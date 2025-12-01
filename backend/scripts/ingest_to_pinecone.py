"""
Pinecone Knowledge Base Ingestion Script (FREE VERSION)
Uses Sentence Transformers for embeddings (no API key needed!)

Usage:
    python scripts/ingest_to_pinecone.py
"""

import json
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables from backend/app/.env
env_path = Path(__file__).parent.parent / "app" / ".env"
load_dotenv(dotenv_path=env_path)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "finstack-knowledge-base")

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not found in environment")

# Initialize clients
pc = Pinecone(api_key=PINECONE_API_KEY)

# Initialize FREE local embedding model
print("Loading embedding model (first time may take a minute to download ~80MB)...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # FREE! Runs locally
print("✅ Embedding model loaded!")

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data"


def generate_embedding(text: str) -> List[float]:
    """Generate embedding using local Sentence Transformers model (FREE!)."""
    try:
        embedding = embedding_model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    except Exception as e:
        print(f"Error generating embedding: {e}")
        raise


def create_index_if_not_exists():
    """Create Pinecone index if it doesn't exist."""
    existing_indexes = pc.list_indexes().names()

    if PINECONE_INDEX_NAME not in existing_indexes:
        print(f"Creating index '{PINECONE_INDEX_NAME}'...")
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=384,  # all-MiniLM-L6-v2 produces 384-dimensional vectors
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        print(f"Index '{PINECONE_INDEX_NAME}' created successfully!")
    else:
        print(f"Index '{PINECONE_INDEX_NAME}' already exists.")


def format_employee_content(emp: Dict[str, Any]) -> str:
    """Format employee data into searchable text."""
    content_parts = [
        f"{emp['name']} is a {emp['title']} in the {emp['department']} department",
        f"Team: {emp.get('team', 'N/A')}",
        f"Based in {emp['location']}",
        f"Email: {emp['email']}, Phone: {emp['phone']}",
        f"Salary: ${emp['salary']:,}",
    ]

    if emp.get('manager_email'):
        content_parts.append(f"Reports to: {emp['manager_email']}")

    if emp.get('equity_annual'):
        content_parts.append(f"Annual equity: ${emp['equity_annual']:,}")

    content_parts.append(f"Performance rating: {emp['performance_rating']}")
    content_parts.append(f"Started: {emp['start_date']}")

    if emp.get('skills'):
        content_parts.append(f"Skills: {', '.join(emp['skills'])}")

    if emp.get('current_project'):
        content_parts.append(f"Current project: {emp['current_project']}")

    return ". ".join(content_parts)


def format_customer_content(cust: Dict[str, Any]) -> str:
    """Format customer data into searchable text."""
    contact = cust.get('primary_contact', {})
    content_parts = [
        f"{cust['company_name']} is a {cust['tier']} customer in the {cust['industry']} industry",
        f"Annual contract value: ${cust['arr']:,}",
        f"Company size: {cust['employee_count']} employees",
        f"Primary contact: {contact.get('name', 'N/A')} ({contact.get('title', 'N/A')})",
        f"Contact email: {contact.get('email', 'N/A')}, Phone: {contact.get('phone', 'N/A')}",
        f"Payment method: {cust.get('payment_method', 'N/A')}",
        f"Contract: {cust['contract_start']} to {cust['contract_end']}",
        f"Support tier: {cust['support_tier']}",
        f"Customer Success Manager: {cust.get('csm', 'N/A')}",
        f"Active users: {cust.get('active_users', 0)}",
    ]

    if cust.get('integrations'):
        content_parts.append(f"Integrations: {', '.join(cust['integrations'])}")

    if cust.get('recent_notes'):
        content_parts.append(f"Notes: {cust['recent_notes']}")

    return ". ".join(content_parts)


def format_financial_content(fin: Dict[str, Any]) -> str:
    """Format financial data into searchable text."""
    content_parts = [f"Financial Record: {fin['record_type']}"]

    if fin['record_type'] == 'quarterly_budget':
        content_parts.extend([
            f"Department: {fin['department']}",
            f"Quarter: {fin['fiscal_quarter']}",
            f"Budget allocated: ${fin['budget_allocated']:,}",
            f"Actual spend: ${fin['actual_spend']:,}",
            f"Utilization: {fin['utilization']}%",
            f"Headcount: {fin.get('headcount', 'N/A')}",
        ])
        if fin.get('breakdown'):
            breakdown_str = ', '.join([f"{k}: ${v:,}" for k, v in fin['breakdown'].items()])
            content_parts.append(f"Breakdown: {breakdown_str}")

    elif fin['record_type'] == 'funding':
        content_parts.extend([
            f"Funding round: {fin['funding_round']}",
            f"Amount: ${fin['amount']:,}",
            f"Date: {fin['date']}",
            f"Lead investor: {fin['lead_investor']}",
            f"Post-money valuation: ${fin['post_money_valuation']:,}",
        ])

    elif fin['record_type'] == 'revenue_forecast':
        content_parts.extend([
            f"Fiscal year: {fin['fiscal_year']}",
            f"Total forecast: ${fin['total_year']:,}",
            f"YoY growth: {fin['yoy_growth']}%",
            f"ARR target end of year: ${fin['arr_target_eoy']:,}",
        ])

    if fin.get('notes'):
        content_parts.append(f"Notes: {fin['notes']}")

    return ". ".join(content_parts)


def format_project_content(proj: Dict[str, Any]) -> str:
    """Format project data into searchable text."""
    content_parts = [
        f"Project: {proj['project_name']}",
        f"Status: {proj['status']}",
        f"Team: {proj['team']}",
        f"Project lead: {proj['lead']}",
        f"Objective: {proj['objective']}",
    ]

    if proj.get('tech_stack'):
        content_parts.append(f"Technology stack: {', '.join(proj['tech_stack'])}")

    if proj.get('target_launch'):
        content_parts.append(f"Target launch: {proj['target_launch']}")

    if proj.get('budget'):
        content_parts.append(f"Budget: ${proj['budget']:,}")

    if proj.get('team_size'):
        content_parts.append(f"Team size: {proj['team_size']} people")

    if proj.get('risks'):
        content_parts.append(f"Risks: {proj['risks']}")

    return ". ".join(content_parts)


def format_knowledge_content(kb: Dict[str, Any]) -> str:
    """Format company knowledge into searchable text."""
    content_parts = [
        f"Topic: {kb['title']}",
        f"Category: {kb['category']}",
        f"Department: {kb['department']}",
        kb['content'],
    ]

    if kb.get('last_updated'):
        content_parts.append(f"Last updated: {kb['last_updated']}")

    return ". ".join(content_parts)


def ingest_employees():
    """Ingest employee data into Pinecone."""
    print("\n📊 Ingesting employee data...")

    with open(DATA_DIR / "employees.json", "r") as f:
        employees = json.load(f)

    index = pc.Index(PINECONE_INDEX_NAME)
    vectors = []

    for emp in employees:
        content = format_employee_content(emp)
        embedding = generate_embedding(content)

        vectors.append({
            "id": emp['id'],
            "values": embedding,
            "metadata": {
                "doc_type": "employee",
                "content": content,
                "name": emp['name'],
                "email": emp['email'],
                "department": emp['department'],
                "title": emp['title'],
                "salary": emp['salary'],
                "location": emp['location'],
                "confidential": True,
                "access_level": "hr_managers_only"
            }
        })

    # Upsert in batches of 100
    for i in range(0, len(vectors), 100):
        batch = vectors[i:i+100]
        index.upsert(vectors=batch)

    print(f"✅ Ingested {len(employees)} employee records")


def ingest_customers():
    """Ingest customer data into Pinecone."""
    print("\n📊 Ingesting customer data...")

    with open(DATA_DIR / "customers.json", "r") as f:
        customers = json.load(f)

    index = pc.Index(PINECONE_INDEX_NAME)
    vectors = []

    for cust in customers:
        content = format_customer_content(cust)
        embedding = generate_embedding(content)

        vectors.append({
            "id": cust['id'],
            "values": embedding,
            "metadata": {
                "doc_type": "customer",
                "content": content,
                "company_name": cust['company_name'],
                "industry": cust['industry'],
                "tier": cust['tier'],
                "arr": cust['arr'],
                "support_tier": cust['support_tier'],
                "pii_included": True,
                "confidential": True,
                "access_level": "sales_cs_only"
            }
        })

    for i in range(0, len(vectors), 100):
        batch = vectors[i:i+100]
        index.upsert(vectors=batch)

    print(f"✅ Ingested {len(customers)} customer records")


def ingest_financials():
    """Ingest financial data into Pinecone."""
    print("\n📊 Ingesting financial data...")

    with open(DATA_DIR / "financial_records.json", "r") as f:
        financials = json.load(f)

    index = pc.Index(PINECONE_INDEX_NAME)
    vectors = []

    for fin in financials:
        content = format_financial_content(fin)
        embedding = generate_embedding(content)

        vectors.append({
            "id": fin['id'],
            "values": embedding,
            "metadata": {
                "doc_type": "financial",
                "content": content,
                "record_type": fin['record_type'],
                "confidential": True,
                "access_level": "finance_exec_only"
            }
        })

    for i in range(0, len(vectors), 100):
        batch = vectors[i:i+100]
        index.upsert(vectors=batch)

    print(f"✅ Ingested {len(financials)} financial records")


def ingest_projects():
    """Ingest project data into Pinecone."""
    print("\n📊 Ingesting project data...")

    with open(DATA_DIR / "projects.json", "r") as f:
        projects = json.load(f)

    index = pc.Index(PINECONE_INDEX_NAME)
    vectors = []

    for proj in projects:
        content = format_project_content(proj)
        embedding = generate_embedding(content)

        vectors.append({
            "id": proj['id'],
            "values": embedding,
            "metadata": {
                "doc_type": "project",
                "content": content,
                "project_name": proj['project_name'],
                "status": proj['status'],
                "team": proj['team'],
                "confidential": False,
                "access_level": "all_employees"
            }
        })

    for i in range(0, len(vectors), 100):
        batch = vectors[i:i+100]
        index.upsert(vectors=batch)

    print(f"✅ Ingested {len(projects)} project records")


def ingest_company_knowledge():
    """Ingest company knowledge into Pinecone."""
    print("\n📊 Ingesting company knowledge...")

    with open(DATA_DIR / "company_knowledge.json", "r") as f:
        knowledge = json.load(f)

    index = pc.Index(PINECONE_INDEX_NAME)
    vectors = []

    for kb in knowledge:
        content = format_knowledge_content(kb)
        embedding = generate_embedding(content)

        # Determine confidentiality based on category
        confidential = kb['category'] in ['security_incident', 'technical']
        access_level = kb.get('access_level', 'all_employees')

        vectors.append({
            "id": kb['id'],
            "values": embedding,
            "metadata": {
                "doc_type": "knowledge",
                "content": content,
                "title": kb['title'],
                "category": kb['category'],
                "department": kb['department'],
                "confidential": confidential,
                "access_level": access_level
            }
        })

    for i in range(0, len(vectors), 100):
        batch = vectors[i:i+100]
        index.upsert(vectors=batch)

    print(f"✅ Ingested {len(knowledge)} knowledge base entries")


def main():
    """Main ingestion function."""
    print("=" * 60)
    print("FinStack Knowledge Base Ingestion")
    print("Using Sentence Transformers - No API key needed!")
    print("=" * 60)

    # Create index if needed
    create_index_if_not_exists()

    # Wait for index to be ready
    print("\nWaiting for index to be ready...")
    import time
    time.sleep(5)

    # Ingest all data
    ingest_employees()
    ingest_customers()
    ingest_financials()
    ingest_projects()
    ingest_company_knowledge()

    # Get stats
    index = pc.Index(PINECONE_INDEX_NAME)
    stats = index.describe_index_stats()

    print("\n" + "=" * 60)
    print(f"✅ Ingestion complete!")
    print(f"Total vectors in index: {stats.total_vector_count}")
    print("=" * 60)

    # Test query
    print("\n🧪 Testing with a sample query...")
    test_query = "What is Sarah Chen's salary?"
    test_embedding = generate_embedding(test_query)
    results = index.query(
        vector=test_embedding,
        top_k=3,
        include_metadata=True
    )

    print(f"\nQuery: '{test_query}'")
    print(f"Top {len(results.matches)} results:")
    for i, match in enumerate(results.matches, 1):
        print(f"\n{i}. Score: {match.score:.4f}")
        print(f"   Type: {match.metadata.get('doc_type')}")
        print(f"   Content: {match.metadata.get('content', '')[:200]}...")


if __name__ == "__main__":
    main()

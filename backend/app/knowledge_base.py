"""
Knowledge Base Service for FinStack (FREE VERSION)
Uses Sentence Transformers for embeddings (no API key needed!)
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Silence tokenizers warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Load environment variables from backend/app/.env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

class KnowledgeBaseService:
    """
    Service for querying the FinStack knowledge base in Pinecone.

    SECURITY NOTE: This is the V1 (insecure) version.
    It has NO access control - any user can query any data!
    """

    def __init__(self):
        """Initialize the knowledge base service."""
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "finstack-knowledge-base")

        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY not found in environment")

        # Initialize Pinecone client
        self.pc = Pinecone(api_key=self.pinecone_api_key)

        # Initialize FREE local embedding model
        print("📚 Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # FREE!
        print("✅ Embedding model loaded!")

        # Get index
        try:
            self.index = self.pc.Index(self.index_name)
        except Exception as e:
            print(f"Warning: Could not connect to Pinecone index '{self.index_name}': {e}")
            self.index = None

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using local Sentence Transformers model (FREE!)."""
        try:
            embedding = self.embedding_model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge base for relevant information.

        Args:
            query: The search query
            top_k: Number of results to return
            filters: Optional metadata filters (e.g., {"doc_type": "employee"})
            user_id: User making the request (NOT USED IN V1 - NO ACCESS CONTROL!)

        Returns:
            List of search results with content and metadata

        VULNERABILITY: No access control! User can query any data.
        VULNERABILITY: Returns sensitive metadata (salary, access_level, etc.)
        """
        if not self.index:
            return [{
                "content": "Knowledge base not available. Please run the ingestion script first.",
                "score": 0.0,
                "metadata": {}
            }]

        # Generate embedding for query
        print(f"🔍 Searching for: '{query}'")
        query_embedding = self.generate_embedding(query)

        # VULNERABILITY: No filtering based on user permissions!
        # In V2, we would filter by user role/department

        # Query Pinecone
        try:
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filters,  # User could manipulate these filters
                include_metadata=True  # VULNERABILITY: Returns ALL metadata including sensitive fields
            )

            print(f"📊 Found {len(results.matches)} results")
            
            # Format results
            formatted_results = []
            for match in results.matches:
                print(f"  - Score: {match.score:.4f}, ID: {match.id}, Filename: {match.metadata.get('filename', 'N/A')}")
                formatted_results.append({
                    "content": match.metadata.get("content", ""),
                    "score": float(match.score),
                    "metadata": match.metadata,  # VULNERABILITY: Exposes all metadata
                    "id": match.id
                })

            return formatted_results

        except Exception as e:
            print(f"❌ Error querying knowledge base: {e}")
            import traceback
            traceback.print_exc()
            return [{
                "content": f"Error searching knowledge base: {str(e)}",
                "score": 0.0,
                "metadata": {}
            }]

    async def search_employees(
        self,
        query: str,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search specifically for employee information.

        VULNERABILITY: Anyone can search employee data including salaries!
        """
        return await self.search(
            query=query,
            top_k=5,
            filters={"doc_type": "employee"},
            user_id=user_id
        )

    async def search_customers(
        self,
        query: str,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search specifically for customer information.

        VULNERABILITY: Anyone can access customer PII!
        """
        return await self.search(
            query=query,
            top_k=5,
            filters={"doc_type": "customer"},
            user_id=user_id
        )

    async def search_financials(
        self,
        query: str,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search specifically for financial information.

        VULNERABILITY: Anyone can access financial data!
        """
        return await self.search(
            query=query,
            top_k=5,
            filters={"doc_type": "financial"},
            user_id=user_id
        )

    async def search_projects(
        self,
        query: str,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for project information."""
        return await self.search(
            query=query,
            top_k=5,
            filters={"doc_type": "project"},
            user_id=user_id
        )

    async def get_context_for_llm(
        self,
        query: str,
        user_id: Optional[str] = None,
        max_results: int = 3
    ) -> str:
        """
        Get formatted context from knowledge base to include in LLM prompt.

        Args:
            query: The user's question
            user_id: User making the request (not used for access control in V1)
            max_results: Maximum number of results to include

        Returns:
            Formatted string with relevant context
        """
        results = await self.search(query=query, top_k=max_results, user_id=user_id)

        if not results or results[0]["score"] < 0.3:
            return "No relevant information found in knowledge base."

        # Format context for LLM
        context_parts = ["Here is relevant information from the knowledge base:\n"]

        for i, result in enumerate(results, 1):
            if result["score"] < 0.3:  # Skip low-confidence results
                break

            context_parts.append(f"\n[Source {i}] (Relevance: {result['score']:.2f})")
            context_parts.append(result["content"])

            # VULNERABILITY: Include metadata that might contain sensitive info
            if result["metadata"].get("access_level"):
                context_parts.append(f"[Access Level: {result['metadata']['access_level']}]")

        return "\n".join(context_parts)

    async def ingest_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> Dict[str, Any]:
        """
        Ingest a document into the knowledge base by chunking and vectorizing it.

        Args:
            content: The text content to ingest
            metadata: Metadata about the document (filename, doc_type, etc.)
            chunk_size: Size of text chunks (in characters)
            chunk_overlap: Overlap between chunks

        Returns:
            Dictionary with ingestion results
        """
        if not self.index:
            raise ValueError("Pinecone index not available")

        print(f"📝 Ingesting document: {metadata.get('filename', 'unknown')}")
        print(f"   Content length: {len(content)} characters")
        
        # Split content into chunks
        chunks = self._chunk_text(content, chunk_size, chunk_overlap)
        print(f"   Created {len(chunks)} chunks")
        
        # Generate embeddings and prepare vectors
        vectors = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{metadata.get('filename', 'doc')}_{uuid.uuid4().hex[:8]}_{i}"
            embedding = self.generate_embedding(chunk)
            
            chunk_metadata = {
                **metadata,
                "content": chunk,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
            
            vectors.append({
                "id": chunk_id,
                "values": embedding,
                "metadata": chunk_metadata
            })

        # Upsert to Pinecone in batches
        batch_size = 100
        total_upserted = 0
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)
            total_upserted += len(batch)
            print(f"   Upserted batch {i//batch_size + 1}: {len(batch)} vectors (total: {total_upserted})")

        print(f"✅ Successfully ingested {metadata.get('filename', 'unknown')}")
        
        return {
            "status": "success",
            "chunks_created": len(chunks),
            "vectors_upserted": len(vectors),
            "filename": metadata.get("filename", "unknown")
        }

    def _chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> List[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundaries
            if end < text_length:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size * 0.5:  # Only break if we're past halfway
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - chunk_overlap

        return [c for c in chunks if c]  # Filter empty chunks


# Global instance (singleton pattern for easy import)
kb_service = KnowledgeBaseService()


# Example usage functions for testing
async def example_usage():
    """Example of how to use the knowledge base service."""
    kb = KnowledgeBaseService()

    # Basic search
    print("=" * 60)
    print("Example 1: Basic search")
    results = await kb.search("What is Sarah Chen's salary?")
    for result in results:
        print(f"\nScore: {result['score']:.4f}")
        print(f"Content: {result['content'][:200]}...")

    # Search employees
    print("\n" + "=" * 60)
    print("Example 2: Search employees")
    results = await kb.search_employees("software engineer")
    print(f"Found {len(results)} employees")

    # Search customers
    print("\n" + "=" * 60)
    print("Example 3: Search customers")
    results = await kb.search_customers("healthcare")
    print(f"Found {len(results)} customers")

    # Get context for LLM
    print("\n" + "=" * 60)
    print("Example 4: Get context for LLM")
    context = await kb.get_context_for_llm("What projects are in progress?")
    print(context)


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())

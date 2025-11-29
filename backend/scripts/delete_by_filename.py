#!/usr/bin/env python3
"""
Quick script to delete all vectors for a specific filename from Pinecone.

To run:

cd backend
python scripts/delete_by_filename.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pinecone import Pinecone

# Load environment variables
env_path = Path(__file__).parent.parent / "app" / ".env"
load_dotenv(dotenv_path=env_path)

# Configuration
FILENAME_TO_DELETE = "Corporate Memo.pdf"  # TODO: Update filename

def main():
    # Initialize Pinecone
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "finstack-knowledge-base")
    
    if not api_key:
        print("❌ PINECONE_API_KEY not found in environment")
        sys.exit(1)
    
    print(f"🔌 Connecting to Pinecone index: {index_name}")
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)
    
    # Query for all vectors with this filename
    print(f"🔍 Searching for vectors with filename: '{FILENAME_TO_DELETE}'")
    
    # Pinecone doesn't support direct metadata-only queries for deletion
    # We need to use delete with filter
    try:
        # Delete by metadata filter
        delete_response = index.delete(
            filter={"filename": {"$eq": FILENAME_TO_DELETE}}
        )
        
        print(f"✅ Deleted all vectors for filename: '{FILENAME_TO_DELETE}'")
        print(f"   Response: {delete_response}")
        
        # Verify deletion
        print("\n⏳ Waiting 2 seconds for deletion to propagate...")
        import time
        time.sleep(2)
        
        # Check index stats
        stats = index.describe_index_stats()
        print(f"\n📊 Index stats after deletion:")
        print(f"   Total vectors: {stats.total_vector_count}")
        
    except Exception as e:
        print(f"❌ Error deleting vectors: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("🗑️  Pinecone Vector Deletion Script")
    print("=" * 60)
    print(f"\nTarget filename: {FILENAME_TO_DELETE}")
    
    confirm = input("\nAre you sure you want to delete these vectors? (yes/no): ")
    if confirm.lower() != "yes":
        print("❌ Cancelled")
        sys.exit(0)
    
    main()
    print("\n✅ Done!")

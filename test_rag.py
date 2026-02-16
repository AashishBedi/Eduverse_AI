"""
Test script for RAG service
Tests the complete RAG pipeline with dummy documents
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag_service import rag_service, initialize_with_dummy_data


def test_rag_pipeline():
    """Test the complete RAG pipeline"""
    
    print("=" * 80)
    print("Testing EduVerse AI RAG Service")
    print("=" * 80)
    
    # Initialize with dummy data
    print("\n📚 Step 1: Initializing RAG service with dummy documents...")
    initialize_with_dummy_data()
    
    # Get stats
    print("\n📊 Step 2: Getting collection statistics...")
    stats = rag_service.get_collection_stats()
    print(f"   Collection: {stats['collection_name']}")
    print(f"   Documents: {stats['document_count']}")
    print(f"   Embedding Model: {stats['embedding_model']}")
    print(f"   LLM Model: {stats['ollama_model']}")
    
    # Test queries
    test_questions = [
        "What is Python?",
        "Explain machine learning",
        "What is FastAPI?",
        "Tell me about REST APIs",
        "What are vector databases used for?"
    ]
    
    print("\n🔍 Step 3: Testing RAG queries...")
    print("=" * 80)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[Query {i}] {question}")
        print("-" * 80)
        
        try:
            result = rag_service.query(question, top_k=2)
            
            print(f"\n📝 Answer:")
            print(f"   {result['answer']}")
            
            print(f"\n📚 Sources ({len(result['sources'])}):")
            for j, source in enumerate(result['sources'], 1):
                print(f"   [{j}] {source['id']} (Score: {source['relevance_score']:.3f})")
                print(f"       {source['text'][:100]}...")
            
            print("\n" + "=" * 80)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print("   Note: Make sure Ollama is running with phi3 model installed")
            print("   Run: ollama pull phi3")
            print("\n" + "=" * 80)
            break
    
    print("\n✅ RAG pipeline test completed!")
    print("=" * 80)


if __name__ == "__main__":
    test_rag_pipeline()

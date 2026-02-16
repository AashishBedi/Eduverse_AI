"""
Test script for unified chat endpoint
Tests mode-aware routing and separation
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.chat_orchestrator import chat_orchestrator, ChatMode
from app.services.rag_service import initialize_with_dummy_data
from app.db.database import SessionLocal
from app.models.timetable import Timetable
from datetime import time


def setup_test_data(db):
    """Setup test data for all modes"""
    
    print("📚 Setting up test data...")
    
    # Initialize RAG with dummy documents
    print("   Initializing RAG service...")
    initialize_with_dummy_data()
    
    # Create sample timetable data
    print("   Creating sample timetable data...")
    db.query(Timetable).filter(Timetable.teacher_uid.like("T%")).delete()
    db.commit()
    
    sample_timetable = [
        Timetable(
            teacher_uid="T001",
            teacher_name="Dr. John Smith",
            subject="Database Systems",
            day="Monday",
            start_time=time(9, 0),
            end_time=time(10, 30),
            classroom="Room 101",
            department="Computer Science"
        ),
        Timetable(
            teacher_uid="T001",
            teacher_name="Dr. John Smith",
            subject="Web Development",
            day="Wednesday",
            start_time=time(14, 0),
            end_time=time(15, 30),
            classroom="Room 102",
            department="Computer Science"
        ),
    ]
    
    for entry in sample_timetable:
        db.add(entry)
    db.commit()
    
    print("✅ Test data ready\n")


def test_unified_chat():
    """Test unified chat endpoint with all modes"""
    
    print("=" * 80)
    print("Testing EduVerse AI Unified Chat Endpoint")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # Setup test data
        setup_test_data(db)
        
        # Get mode information
        print("📋 Available Modes:")
        mode_info = chat_orchestrator.get_mode_info()
        for mode, description in mode_info["descriptions"].items():
            print(f"   • {mode}: {description}")
        print()
        
        # Test cases for each mode
        test_cases = [
            {
                "mode": ChatMode.TIMETABLE,
                "query": "Show me timetable for T001 on Monday",
                "description": "Timetable query (deterministic)"
            },
            {
                "mode": ChatMode.TIMETABLE,
                "query": "What classes does T001 have?",
                "description": "Timetable query (all days)"
            },
            {
                "mode": ChatMode.ADMISSIONS,
                "query": "What is Python?",
                "description": "Admissions query (uses RAG)"
            },
            {
                "mode": ChatMode.GENERAL,
                "query": "Explain FastAPI framework",
                "description": "General query (uses RAG)"
            },
            {
                "mode": ChatMode.REGULATIONS,
                "query": "What is a REST API?",
                "description": "Regulations query (uses RAG)"
            },
            {
                "mode": ChatMode.FEES,
                "query": "What is the tuition fee structure?",
                "description": "Fees query (structured)"
            },
            {
                "mode": ChatMode.FEES,
                "query": "Tell me about payment options",
                "description": "Fees query (RAG fallback)"
            },
        ]
        
        print("🧪 Testing Chat Modes:")
        print("=" * 80)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[Test {i}] {test_case['description']}")
            print(f"Mode: {test_case['mode'].value}")
            print(f"Query: {test_case['query']}")
            print("-" * 80)
            
            try:
                result = chat_orchestrator.chat(
                    mode=test_case["mode"],
                    query=test_case["query"],
                    db=db
                )
                
                print(f"\n✅ Response Type: {result['response_type']}")
                print(f"   LLM Used: {result['metadata']['llm_used']}")
                print(f"   Service: {result['metadata']['service']}")
                
                print(f"\n📝 Answer:")
                # Truncate long answers
                answer = result['answer']
                if len(answer) > 300:
                    print(f"   {answer[:300]}...")
                else:
                    print(f"   {answer}")
                
                if result['sources']:
                    print(f"\n📚 Sources: {len(result['sources'])} documents")
                
                if result['data']:
                    print(f"\n📊 Structured Data: {list(result['data'].keys())}")
                
                print("\n" + "=" * 80)
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("=" * 80)
        
        print("\n✅ All unified chat tests completed!")
        print("=" * 80)
        
        # Summary
        print("\n📊 Test Summary:")
        print(f"   Total modes: {len(mode_info['modes'])}")
        print(f"   RAG modes: {', '.join(mode_info['rag_modes'])}")
        print(f"   Structured modes: {', '.join(mode_info['structured_modes'])}")
        print(f"   Hybrid modes: {', '.join(mode_info['hybrid_modes'])}")
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_unified_chat()

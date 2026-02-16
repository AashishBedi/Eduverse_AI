"""
Test script for Admin Content Management
Tests both file upload and text ingestion endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_text_ingestion():
    """Test direct text ingestion"""
    print("\n" + "="*60)
    print("Testing Text Ingestion Endpoint")
    print("="*60)
    
    # Test data
    test_content = """
    Academic Regulations for Computer Science Department
    
    1. Attendance Requirements:
       - Minimum 75% attendance is mandatory for all courses
       - Students with less than 75% attendance will not be allowed to appear in exams
       - Medical certificates must be submitted within 3 days
    
    2. Examination Rules:
       - Students must carry their ID cards to the examination hall
       - Electronic devices are strictly prohibited
       - Late entry is not permitted after 30 minutes
    
    3. Grading System:
       - A+: 90-100
       - A: 80-89
       - B+: 70-79
       - B: 60-69
       - C: 50-59
       - F: Below 50
    
    4. Academic Integrity:
       - Plagiarism is strictly prohibited
       - Copying in exams will result in immediate failure
       - All assignments must be original work
    """
    
    # Test 1: Valid text ingestion
    print("\n1. Testing valid text ingestion (regulations)...")
    data = {
        "content": test_content,
        "category": "regulations",
        "department": "Computer Science",
        "academic_year": "2024-2025"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/upload/text",
            data=data
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            print(f"   ✓ Success! Created {result['chunks_created']} chunks")
        else:
            print(f"   ✗ Failed: {result.get('detail', 'Unknown error')}")
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
    
    # Test 2: Empty content (should fail)
    print("\n2. Testing empty content (should fail)...")
    data = {
        "content": "",
        "category": "regulations",
        "department": "Computer Science",
        "academic_year": "2024-2025"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/upload/text",
            data=data
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        if response.status_code == 400:
            print(f"   ✓ Correctly rejected: {result.get('detail')}")
        else:
            print(f"   ✗ Should have failed but got: {result}")
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
    
    # Test 3: Timetable category (should fail)
    print("\n3. Testing timetable category (should fail)...")
    data = {
        "content": "Some timetable data",
        "category": "timetable",
        "department": "Computer Science",
        "academic_year": "2024-2025"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/upload/text",
            data=data
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        if response.status_code == 400:
            print(f"   ✓ Correctly rejected: {result.get('detail')}")
        else:
            print(f"   ✗ Should have failed but got: {result}")
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
    
    # Test 4: Invalid category (should fail)
    print("\n4. Testing invalid category (should fail)...")
    data = {
        "content": "Some content",
        "category": "invalid_category",
        "department": "Computer Science",
        "academic_year": "2024-2025"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/upload/text",
            data=data
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        if response.status_code == 400:
            print(f"   ✓ Correctly rejected: {result.get('detail')}")
        else:
            print(f"   ✗ Should have failed but got: {result}")
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")


def test_rag_retrieval():
    """Test if ingested text is retrievable via RAG"""
    print("\n" + "="*60)
    print("Testing RAG Retrieval of Ingested Text")
    print("="*60)
    
    # Wait a moment for indexing
    import time
    time.sleep(2)
    
    # Test query
    print("\n1. Querying for attendance requirements...")
    data = {
        "mode": "regulations",
        "query": "What is the minimum attendance requirement?"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/",
            json=data
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200:
            print(f"   Answer: {result['answer'][:200]}...")
            if result.get('metadata'):
                print(f"   Confidence: {result['metadata'].get('confidence', 'N/A')}")
                print(f"   Max Similarity: {result['metadata'].get('max_similarity', 'N/A')}")
            print("   ✓ Successfully retrieved ingested content!")
        else:
            print(f"   ✗ Failed: {result.get('detail', 'Unknown error')}")
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")


def main():
    print("\n" + "="*60)
    print("Admin Content Management Test Suite")
    print("="*60)
    print("\nMake sure the backend is running on http://localhost:8000")
    print("Press Enter to continue or Ctrl+C to cancel...")
    input()
    
    # Run tests
    test_text_ingestion()
    test_rag_retrieval()
    
    print("\n" + "="*60)
    print("Test Suite Complete!")
    print("="*60)


if __name__ == "__main__":
    main()

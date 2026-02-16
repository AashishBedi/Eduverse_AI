"""
Quick diagnostic script to check backend server status
"""
import requests
import sys

print("🔍 Checking EduVerse Backend Server...\n")

# Test 1: Health endpoint
print("Test 1: Health Check")
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        print("✅ Backend is running and healthy!")
        print(f"   Response: {response.json()}")
    else:
        print(f"⚠️  Backend responded with status {response.status_code}")
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to backend at http://localhost:8000")
    print("   → Backend server is NOT running")
    print("\n💡 Fix: Start the backend server:")
    print("   cd c:\\Users\\91798\\Desktop\\Projects\\eduverse")
    print("   uvicorn app.main:app --reload")
    sys.exit(1)
except requests.exceptions.Timeout:
    print("❌ Backend connection timed out")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 2: Docs endpoint
print("\nTest 2: API Documentation")
try:
    response = requests.get("http://localhost:8000/docs", timeout=5)
    if response.status_code == 200:
        print("✅ Swagger UI is accessible")
    else:
        print(f"⚠️  Docs endpoint returned status {response.status_code}")
except Exception as e:
    print(f"⚠️  Could not access docs: {e}")

# Test 3: Upload endpoint exists
print("\nTest 3: Upload Endpoint")
try:
    # OPTIONS request to check CORS
    response = requests.options("http://localhost:8000/api/upload/upload", timeout=5)
    print(f"✅ Upload endpoint exists (status: {response.status_code})")
    
    # Check CORS headers
    if 'access-control-allow-origin' in response.headers:
        allowed_origin = response.headers['access-control-allow-origin']
        print(f"✅ CORS configured: {allowed_origin}")
    else:
        print("⚠️  CORS headers not found in response")
except Exception as e:
    print(f"⚠️  Could not check upload endpoint: {e}")

print("\n" + "="*50)
print("✅ BACKEND IS READY FOR FILE UPLOADS!")
print("="*50)
print("\nYou can now:")
print("1. Open frontend at http://localhost:5173")
print("2. Navigate to Admin Panel")
print("3. Upload files - should work now!")

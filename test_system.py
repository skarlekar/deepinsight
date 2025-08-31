#!/usr/bin/env python3
"""
DeepInsight System Test Script

This script tests the basic functionality of the DeepInsight system
to ensure all components are working correctly.
"""

import requests
import json
import time
import sys
import os

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_user_registration():
    """Test user registration"""
    print("🔍 Testing user registration...")
    
    user_data = {
        "username": "testuser123",
        "email": "test@example.com",
        "password": "TestPass123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data, timeout=10)
        if response.status_code == 200:
            print("✅ User registration passed")
            return response.json()
        else:
            print(f"❌ User registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ User registration failed: {e}")
        return None

def test_user_login():
    """Test user login"""
    print("🔍 Testing user login...")
    
    login_data = {
        "username": "testuser123",
        "password": "TestPass123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            print("✅ User login passed")
            return response.json()
        else:
            print(f"❌ User login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ User login failed: {e}")
        return None

def test_document_upload(token):
    """Test document upload"""
    print("🔍 Testing document upload...")
    
    # Create a test text file
    test_content = """
    This is a test document for the DeepInsight system.
    
    The document contains information about John Smith who works for Acme Corporation.
    John Smith is a Software Engineer at Acme Corporation.
    The company Acme Corporation is located in New York.
    
    Mary Johnson also works at Acme Corporation as a Project Manager.
    Mary Johnson reports to the CEO of Acme Corporation.
    
    The CEO of Acme Corporation is Robert Brown.
    Robert Brown founded Acme Corporation in 2010.
    """
    
    # Write test file
    test_file_path = "/tmp/test_document.txt"
    with open(test_file_path, "w") as f:
        f.write(test_content)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        with open(test_file_path, "rb") as f:
            files = {"file": ("test_document.txt", f, "text/plain")}
            response = requests.post(
                f"{BASE_URL}/documents/upload",
                files=files,
                headers=headers,
                timeout=30
            )
        
        if response.status_code == 200:
            print("✅ Document upload passed")
            document = response.json()
            print(f"   Document ID: {document['id']}")
            return document
        else:
            print(f"❌ Document upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Document upload failed: {e}")
        return None
    finally:
        # Cleanup
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def test_api_endpoints():
    """Test basic API endpoints without authentication"""
    print("🔍 Testing API endpoints...")
    
    # Test health endpoint
    if not test_health_check():
        return False
    
    print("✅ Basic API endpoints working")
    return True

def main():
    """Run all tests"""
    print("🚀 Starting DeepInsight System Tests")
    print("=" * 50)
    
    # Test 1: Basic API connectivity
    if not test_api_endpoints():
        print("❌ Basic API tests failed. Is the backend running?")
        sys.exit(1)
    
    # Test 2: User registration
    auth_response = test_user_registration()
    if not auth_response:
        print("❌ User registration failed")
        sys.exit(1)
    
    token = auth_response.get("access_token")
    if not token:
        print("❌ No access token received")
        sys.exit(1)
    
    # Test 3: User login
    login_response = test_user_login()
    if not login_response:
        print("❌ User login failed")
        sys.exit(1)
    
    # Test 4: Document upload
    print("\n⚠️  Note: Document upload and AI processing require ANTHROPIC_API_KEY")
    print("If you haven't configured this, the following tests may fail.\n")
    
    document = test_document_upload(token)
    if document:
        print(f"✅ Document uploaded successfully: {document['id']}")
    else:
        print("⚠️  Document upload failed (may require API key configuration)")
    
    print("\n" + "=" * 50)
    print("🎉 Basic system tests completed!")
    print("\nNext steps:")
    print("1. Configure ANTHROPIC_API_KEY in backend/.env")
    print("2. Visit http://localhost:3000 to use the web interface")
    print("3. Upload documents and create ontologies")
    print("4. Run extractions and export to graph databases")
    
    return True

if __name__ == "__main__":
    main()
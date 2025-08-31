#!/usr/bin/env python3
"""
Quick test to verify feature flags are loaded correctly
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_feature_flags():
    """Test if feature flags are working by checking logs"""
    print("🔧 Testing Feature Flag Configuration")
    print("=" * 50)
    
    session = requests.Session()
    
    # Try to register user
    user_data = {
        "username": "flag_test_user",
        "email": "flag_test@example.com", 
        "password": "TestPass123!"
    }
    
    try:
        response = session.post(f"{BASE_URL}/auth/register", json=user_data)
        if response.status_code == 200:
            auth_data = response.json()
            access_token = auth_data["access_token"]
            print(f"✅ Registered user: {auth_data['user']['username']}")
        else:
            # Try login
            login_data = {
                "username": user_data["username"],
                "password": user_data["password"]
            }
            response = session.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                auth_data = response.json()
                access_token = auth_data["access_token"]
                print(f"✅ Logged in: {auth_data['user']['username']}")
            else:
                print("❌ Authentication failed")
                return False
                
        session.headers.update({
            "Authorization": f"Bearer {access_token}"
        })
        
        # Upload a minimal text document to test feature flags
        test_content = "John works for ACME Corp. He flies from IST to JFK on flight AA100."
        
        files = {'file': ('test.txt', test_content.encode(), 'text/plain')}
        response = session.post(f"{BASE_URL}/documents/upload", files=files)
        
        if response.status_code == 200:
            document_data = response.json()
            document_id = document_data["id"]
            print(f"✅ Document uploaded: {document_id}")
            
            # Wait briefly for processing
            import time
            time.sleep(2)
            
            # Create a simple ontology
            ontology_data = {
                "document_id": document_id,
                "name": "Test Ontology",
                "description": "Minimal test ontology"
            }
            
            response = session.post(f"{BASE_URL}/ontologies/", json=ontology_data)
            if response.status_code == 200:
                ontology = response.json()
                ontology_id = ontology["id"]
                print(f"✅ Ontology created: {ontology_id}")
                
                # Wait for ontology processing
                time.sleep(5)
                
                # Try extraction - this should trigger the enhanced pipeline
                extraction_data = {
                    "document_id": document_id,
                    "ontology_id": ontology_id,
                    "chunk_size": 500,
                    "overlap_percentage": 10
                }
                
                response = session.post(f"{BASE_URL}/extractions/", json=extraction_data)
                if response.status_code == 200:
                    extraction = response.json()
                    extraction_id = extraction["id"]
                    print(f"✅ Extraction started: {extraction_id}")
                    print("🔍 Check backend logs for 'Using enhanced extraction pipeline' message")
                    return True
                else:
                    print(f"❌ Extraction failed: {response.status_code}")
                    if response.text:
                        print(f"   Error: {response.text}")
                    return False
            else:
                print(f"❌ Ontology creation failed: {response.status_code}")
                return False
        else:
            print(f"❌ Document upload failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_feature_flags()
    if success:
        print("\n✅ Feature flag test completed - check backend logs!")
    else:
        print("\n❌ Feature flag test failed!")
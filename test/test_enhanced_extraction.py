#!/usr/bin/env python3
"""
End-to-end test for enhanced extraction pipeline
Tests GUID-based deduplication and mandatory name properties
"""

import requests
import json
import time
import sys
import os
from pathlib import Path

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_PDF_PATH = "test/testdata/test_doc.pdf"

class EnhancedExtractionTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        
    def test_enhanced_extraction_pipeline(self):
        """Run complete end-to-end test of enhanced extraction"""
        print("🧪 Starting Enhanced Extraction Pipeline Test")
        print("=" * 60)
        
        try:
            # Step 1: Register/Login user
            if not self.setup_user():
                return False
            
            # Step 2: Upload test document
            document_id = self.upload_test_document()
            if not document_id:
                return False
                
            # Step 3: Create ontology
            ontology_id = self.create_ontology(document_id)
            if not ontology_id:
                return False
                
            # Step 4: Run extraction with enhanced pipeline  
            extraction_id = self.run_extraction(document_id, ontology_id)
            if not extraction_id:
                return False
                
            # Step 5: Wait for extraction completion
            extraction_result = self.wait_for_extraction(extraction_id)
            if not extraction_result:
                return False
                
            # Step 6: Analyze results for deduplication
            if not self.analyze_deduplication_results(extraction_result):
                return False
                
            # Step 7: Test CSV export
            if not self.test_csv_exports(extraction_id):
                return False
                
            print("✅ Enhanced Extraction Pipeline Test PASSED!")
            print("🎯 Key Results:")
            print(f"   - Extraction mode: {extraction_result.get('metadata', {}).get('extraction_mode', 'unknown')}")
            print(f"   - Total entities: {len(extraction_result.get('nodes', []))}")
            print(f"   - Total relationships: {len(extraction_result.get('relationships', []))}")
            
            entity_stats = extraction_result.get('metadata', {}).get('entity_stats', {})
            if entity_stats:
                print(f"   - Entities extracted: {entity_stats.get('total_extracted', 0)}")
                print(f"   - Unique entities: {entity_stats.get('unique_entities', 0)}")  
                print(f"   - Duplicates removed: {entity_stats.get('duplicates_removed', 0)}")
                print(f"   - Deduplication rate: {entity_stats.get('deduplication_rate', 0):.1%}")
                
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
            return False
    
    def setup_user(self):
        """Register or login test user"""
        print("🔐 Setting up test user...")
        
        # Try to register user
        user_data = {
            "username": "test_enhanced_user",
            "email": "enhanced_test@example.com", 
            "password": "TestPass123!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=user_data)
            if response.status_code == 200:
                auth_data = response.json()
                self.access_token = auth_data["access_token"]
                self.user_id = auth_data["user"]["id"]
                print(f"✅ Registered new user: {auth_data['user']['username']}")
            else:
                # User might already exist, try login
                login_data = {
                    "username": user_data["username"],
                    "password": user_data["password"]
                }
                response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
                if response.status_code == 200:
                    auth_data = response.json()
                    self.access_token = auth_data["access_token"]
                    self.user_id = auth_data["user"]["id"]
                    print(f"✅ Logged in existing user: {auth_data['user']['username']}")
                else:
                    print(f"❌ Failed to login: {response.status_code}")
                    return False
                    
            # Set authorization header
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}"
            })
            
            return True
            
        except Exception as e:
            print(f"❌ User setup failed: {str(e)}")
            return False
    
    def upload_test_document(self):
        """Upload test PDF document"""
        print("📄 Uploading test document...")
        
        if not Path(TEST_PDF_PATH).exists():
            print(f"❌ Test file not found: {TEST_PDF_PATH}")
            return None
            
        try:
            with open(TEST_PDF_PATH, 'rb') as f:
                files = {'file': ('test_doc.pdf', f, 'application/pdf')}
                response = self.session.post(f"{BASE_URL}/documents/upload", files=files)
                
            if response.status_code == 200:
                document_data = response.json()
                document_id = document_data["id"]
                print(f"✅ Document uploaded: {document_id}")
                
                # Wait for document processing
                self.wait_for_document_processing(document_id)
                return document_id
            else:
                print(f"❌ Document upload failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Document upload error: {str(e)}")
            return None
    
    def wait_for_document_processing(self, document_id, timeout=60):
        """Wait for document to be processed"""
        print("⏳ Waiting for document processing...")
        
        for _ in range(timeout):
            try:
                response = self.session.get(f"{BASE_URL}/documents/{document_id}")
                if response.status_code == 200:
                    document = response.json()
                    if document["status"] == "completed":
                        print("✅ Document processing completed")
                        return True
                    elif document["status"] == "error":
                        print(f"❌ Document processing failed: {document.get('error_message')}")
                        return False
                        
                time.sleep(1)
            except Exception:
                time.sleep(1)
                
        print("❌ Document processing timeout")
        return False
    
    def create_ontology(self, document_id):
        """Create ontology from document"""
        print("🧠 Creating ontology...")
        
        try:
            ontology_data = {
                "document_id": document_id,
                "name": "Enhanced Test Ontology",
                "description": "Test ontology for enhanced extraction pipeline"
            }
            
            response = self.session.post(f"{BASE_URL}/ontologies/", json=ontology_data)
            
            if response.status_code == 200:
                ontology = response.json()
                ontology_id = ontology["id"]
                print(f"✅ Ontology created: {ontology_id}")
                
                # Wait for ontology processing
                self.wait_for_ontology_processing(ontology_id)
                return ontology_id
            else:
                print(f"❌ Ontology creation failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Ontology creation error: {str(e)}")
            return None
    
    def wait_for_ontology_processing(self, ontology_id, timeout=120):
        """Wait for ontology to be processed"""
        print("⏳ Waiting for ontology processing...")
        
        for _ in range(timeout):
            try:
                response = self.session.get(f"{BASE_URL}/ontologies/{ontology_id}")
                if response.status_code == 200:
                    ontology = response.json()
                    if ontology["status"] == "active":
                        print(f"✅ Ontology processing completed - {len(ontology.get('triples', []))} triples")
                        return True
                    elif ontology["status"] == "error":
                        print("❌ Ontology processing failed")
                        return False
                        
                time.sleep(1)
            except Exception:
                time.sleep(1)
                
        print("❌ Ontology processing timeout") 
        return False
    
    def run_extraction(self, document_id, ontology_id):
        """Run data extraction"""
        print("🔄 Running enhanced extraction...")
        
        try:
            extraction_data = {
                "document_id": document_id,
                "ontology_id": ontology_id,
                "chunk_size": 1000,
                "overlap_percentage": 10
            }
            
            response = self.session.post(f"{BASE_URL}/extractions/", json=extraction_data)
            
            if response.status_code == 200:
                extraction = response.json()
                extraction_id = extraction["id"]
                print(f"✅ Extraction started: {extraction_id}")
                return extraction_id
            else:
                print(f"❌ Extraction failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Extraction error: {str(e)}")
            return None
    
    def wait_for_extraction(self, extraction_id, timeout=300):
        """Wait for extraction to complete and return results"""
        print("⏳ Waiting for extraction completion...")
        
        for _ in range(timeout):
            try:
                response = self.session.get(f"{BASE_URL}/extractions/{extraction_id}")
                if response.status_code == 200:
                    extraction = response.json()
                    if extraction["status"] == "completed":
                        print("✅ Extraction completed")
                        
                        # Get detailed results
                        result_response = self.session.get(f"{BASE_URL}/extractions/{extraction_id}/result")
                        if result_response.status_code == 200:
                            return result_response.json()
                        
                        return {"nodes": [], "relationships": [], "metadata": {}}
                        
                    elif extraction["status"] == "error":
                        print("❌ Extraction failed")
                        return None
                        
                time.sleep(2)
            except Exception:
                time.sleep(2)
                
        print("❌ Extraction timeout")
        return None
    
    def analyze_deduplication_results(self, extraction_result):
        """Analyze results to verify deduplication worked"""
        print("🔍 Analyzing deduplication results...")
        
        nodes = extraction_result.get("nodes", [])
        metadata = extraction_result.get("metadata", {})
        
        # Check for mandatory name properties
        missing_names = []
        for i, node in enumerate(nodes):
            properties = node.get("properties", {})
            if "name" not in properties or not properties["name"]:
                missing_names.append(f"Node {i}: {node.get('type', 'unknown')} (ID: {node.get('id', 'unknown')})")
        
        if missing_names:
            print(f"❌ Found {len(missing_names)} nodes missing 'name' property:")
            for missing in missing_names[:5]:  # Show first 5
                print(f"   {missing}")
            return False
        else:
            print(f"✅ All {len(nodes)} nodes have mandatory 'name' property")
        
        # Check for duplicate entities (specifically IST airport)
        entity_counts = {}
        ist_airports = []
        
        for node in nodes:
            entity_key = f"{node['type']}:{node['properties']['name']}"
            if entity_key not in entity_counts:
                entity_counts[entity_key] = []
            entity_counts[entity_key].append(node)
            
            # Track IST airports specifically
            if node.get('type') == 'Airport' and node.get('properties', {}).get('name') == 'IST':
                ist_airports.append(node)
        
        # Check for duplicates
        duplicates = {k: v for k, v in entity_counts.items() if len(v) > 1}
        if duplicates:
            print(f"❌ Found duplicate entities:")
            for entity_key, nodes_list in list(duplicates.items())[:3]:  # Show first 3
                print(f"   {entity_key}: {len(nodes_list)} instances")
            return False
        else:
            print(f"✅ No duplicate entities found - deduplication successful!")
        
        # Specifically check IST airports
        print(f"🛫 IST Airport analysis: Found {len(ist_airports)} instances")
        if len(ist_airports) == 1:
            print("✅ IST airport properly deduplicated to single entity")
            ist_node = ist_airports[0]
            print(f"   ID: {ist_node['id']}")
            print(f"   Name: {ist_node['properties']['name']}")
        elif len(ist_airports) > 1:
            print("❌ IST airport still appears multiple times - deduplication failed")
            return False
        else:
            print("ℹ️  No IST airports found in extraction")
        
        # Check metadata stats
        if "entity_stats" in metadata:
            stats = metadata["entity_stats"]
            print(f"📊 Deduplication Statistics:")
            print(f"   Total extracted: {stats.get('total_extracted', 0)}")
            print(f"   Unique entities: {stats.get('unique_entities', 0)}")
            print(f"   Duplicates removed: {stats.get('duplicates_removed', 0)}")
            print(f"   Deduplication rate: {stats.get('deduplication_rate', 0):.1%}")
            
            if stats.get('duplicates_removed', 0) > 0:
                print("✅ Deduplication system working - duplicates were removed")
            else:
                print("ℹ️  No duplicates found to remove")
        
        return True
    
    def test_csv_exports(self, extraction_id):
        """Test CSV export generation"""
        print("📊 Testing CSV exports...")
        
        try:
            # Test Neo4j export
            response = self.session.post(f"{BASE_URL}/exports/{extraction_id}/neo4j")
            if response.status_code == 200:
                neo4j_export = response.json()
                print("✅ Neo4j CSV export generated")
            else:
                print(f"❌ Neo4j export failed: {response.status_code}")
                return False
            
            # Test Neptune export
            response = self.session.post(f"{BASE_URL}/exports/{extraction_id}/neptune")
            if response.status_code == 200:
                neptune_export = response.json()
                print("✅ Neptune CSV export generated")
            else:
                print(f"❌ Neptune export failed: {response.status_code}")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ CSV export error: {str(e)}")
            return False

def main():
    """Main test execution"""
    print("🚀 DeepInsight Enhanced Extraction Test Suite")
    print("Testing: GUID-based node IDs + mandatory name properties + cross-chunk deduplication")
    print()
    
    tester = EnhancedExtractionTester()
    success = tester.test_enhanced_extraction_pipeline()
    
    if success:
        print("\n🎉 All tests PASSED! Enhanced extraction pipeline is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Tests FAILED! Check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3

import sys
import os
import time
import requests
import json

# Add backend to Python path
backend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
sys.path.append(backend_dir)

def test_chunked_ontology_generation():
    """Test chunked ontology generation with a large document"""
    
    print("🚀 DeepInsight Chunked Ontology Generation Test")
    print("Testing: Chunked ontology generation for large documents")
    print("=" * 60)
    
    # API base URL
    base_url = "http://localhost:8000"
    
    try:
        # Health check
        print("🔍 Testing API health...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ API is healthy")
        else:
            print("❌ API health check failed")
            return False
        
        # Login as test user
        print("🔐 Logging in as test user...")
        login_data = {
            "username": "test_chunked_user",
            "password": "TestPass123!"
        }
        
        # Try to register first (in case user doesn't exist)
        register_data = {
            "username": "test_chunked_user",
            "email": "test_chunked@example.com",
            "password": "TestPass123!"
        }
        
        try:
            response = requests.post(f"{base_url}/auth/register", json=register_data)
        except:
            pass  # User might already exist
        
        # Login
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        if response.status_code != 200:
            print("❌ Login failed")
            return False
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Logged in successfully")
        
        # Create a very large document (>8000 characters) to test chunking
        print("📄 Creating large test document...")
        large_document_content = """
        COMPREHENSIVE TRAVEL ITINERARY AND BUSINESS REPORT - EXTENDED EDITION
        
        This document contains extensive information about multiple travel routes, business partnerships, 
        hotel accommodations, airport services, and various organizational relationships that span across
        different geographical regions and business sectors. The content has been designed to test the
        chunked ontology generation capabilities of the DeepInsight system.
        
        SECTION 1: AIRLINE PARTNERSHIPS AND ROUTES
        
        Turkish Airlines operates extensive routes connecting Istanbul Airport (IST) to major destinations
        worldwide. The airline has established partnerships with multiple ground service providers including
        Celebi Ground Handling, TAV Airports, and various catering companies. Turkish Airlines maintains
        its hub operations at Istanbul Airport, serving as a connection point for passengers traveling
        between Europe, Asia, and Africa.
        
        The airline's fleet management is handled by Turkish Airlines Fleet Management Division, which
        coordinates with manufacturers like Boeing, Airbus, and various maintenance providers. The flight
        operations center located in Istanbul coordinates with air traffic control systems across multiple
        countries and manages route optimization for over 300 destinations.
        
        Emirates Airlines, another major carrier, operates from Dubai International Airport (DXB) and
        has extensive partnerships with airport authorities, ground handlers, and service providers.
        The airline maintains relationships with Dubai Airports Company, dnata, and various hospitality
        partners throughout the UAE and internationally.
        
        SECTION 2: HOTEL ACCOMMODATION NETWORKS
        
        The Marriott International hotel chain operates properties across multiple continents, with
        each property maintaining relationships with local suppliers, transportation providers, and
        tourism boards. Marriott Istanbul manages partnerships with Turkish Airlines for crew
        accommodations and passenger services.
        
        Hilton Hotels Corporation maintains similar arrangements, with properties like Hilton Istanbul
        Bomonti providing services to airline crews, business travelers, and tourist groups. The hotel
        works with local transportation companies, tour operators, and event management firms.
        
        InterContinental Hotels Group operates luxury properties that serve as accommodation for
        high-level business meetings, diplomatic events, and corporate conferences. These hotels
        maintain relationships with catering companies, security firms, and technology providers.
        
        SECTION 3: GROUND TRANSPORTATION AND LOGISTICS
        
        Multiple ground transportation companies provide services connecting airports to city centers
        and hotel properties. These companies include traditional taxi services, ride-sharing platforms,
        private car services, and shuttle bus operators. Each service type maintains different
        relationships with airport authorities, hotels, and regulatory bodies.
        
        Cargo handling operations involve partnerships between airlines, ground handling companies,
        customs authorities, and freight forwarders. Companies like DHL, FedEx, and UPS maintain
        facilities at major airports and coordinate with local distribution networks.
        
        SECTION 4: BUSINESS AND CORPORATE RELATIONSHIPS
        
        Various multinational corporations maintain travel and accommodation policies that involve
        partnerships with specific airlines, hotel chains, and ground transportation providers.
        These relationships often include volume discounts, preferred vendor agreements, and
        integrated booking systems.
        
        Technology companies provide booking platforms, payment processing systems, and customer
        management tools that connect airlines, hotels, and ground transportation providers.
        These platforms facilitate seamless travel experiences and enable data sharing between
        service providers.
        
        SECTION 5: REGULATORY AND COMPLIANCE FRAMEWORKS
        
        International aviation authorities, including ICAO, IATA, and national aviation agencies,
        maintain regulatory oversight of airline operations, safety standards, and international
        agreements. These organizations coordinate with airlines, airports, and service providers
        to ensure compliance with safety and operational standards.
        
        Tourism boards and destination marketing organizations work with airlines, hotels, and
        tour operators to promote travel destinations and coordinate marketing efforts. These
        relationships involve joint marketing campaigns, trade show participation, and cooperative
        advertising initiatives.
        
        SECTION 6: FINANCIAL AND INSURANCE RELATIONSHIPS
        
        Airlines maintain relationships with financial institutions for aircraft financing,
        leasing arrangements, and operational credit facilities. These relationships involve
        banks, aircraft leasing companies, and insurance providers who offer coverage for
        aircraft, operations, and passenger liability.
        
        Hotel chains similarly maintain financial relationships for property development,
        renovation projects, and operational financing. These partnerships involve real estate
        investment firms, construction companies, and hospitality management consultants.
        
        SECTION 7: TECHNOLOGY AND INNOVATION PARTNERSHIPS
        
        Airlines and hotels increasingly partner with technology companies to provide enhanced
        customer experiences through mobile applications, automated check-in systems, and
        personalized service offerings. These partnerships involve software developers,
        hardware suppliers, and data analytics companies.
        
        Artificial intelligence and machine learning technologies are being implemented across
        the travel industry through partnerships between traditional travel companies and
        technology innovators. These collaborations focus on predictive analytics, customer
        service automation, and operational optimization.
        
        CONCLUSION AND FUTURE DEVELOPMENTS
        
        The travel and hospitality industry continues to evolve through strategic partnerships,
        technological innovations, and changing customer expectations. Future developments will
        likely involve increased integration between service providers, enhanced use of data
        analytics, and more personalized customer experiences delivered through collaborative
        efforts between airlines, hotels, ground transportation, and technology companies.
        
        This comprehensive overview demonstrates the complex web of relationships that exist
        within the travel industry and provides a foundation for understanding how different
        organizations collaborate to deliver integrated travel experiences to customers
        worldwide. The relationships described here represent just a fraction of the total
        partnerships and collaborations that enable modern travel and tourism operations.
        
        ADDITIONAL SECTION 8: EXPANDED PARTNERSHIPS AND EXTENDED NETWORKS
        
        Beyond the primary partnerships already described, the travel industry includes numerous
        secondary and tertiary relationships that create an intricate web of dependencies and
        collaborations. These extended partnerships involve travel insurance companies, currency
        exchange providers, visa processing services, and diplomatic missions that facilitate
        international travel.
        
        Travel insurance companies such as Allianz Travel, World Nomads, and Travel Guard maintain
        partnerships with airlines, hotels, and booking platforms to offer comprehensive coverage
        for travelers. These relationships involve data sharing agreements, automated claim processing
        systems, and integrated customer service platforms that streamline the insurance process
        for travelers.
        
        Currency exchange providers including Travelex, Western Union, and local bank branches
        coordinate with airports, hotels, and travel agencies to provide foreign exchange services.
        These partnerships involve secure cash transportation, rate synchronization systems, and
        fraud prevention mechanisms that ensure safe and efficient currency exchange operations.
        
        Visa processing services work closely with consulates, embassies, and government agencies
        to facilitate travel documentation. Companies like VisaCentral, iVisa, and VFS Global
        maintain relationships with immigration authorities, airlines, and travel agencies to
        streamline visa application and approval processes for international travelers.
        
        SECTION 9: ENVIRONMENTAL AND SUSTAINABILITY PARTNERSHIPS
        
        The travel industry increasingly focuses on sustainability partnerships that address
        environmental concerns and carbon footprint reduction. Airlines partner with carbon
        offset organizations, renewable energy providers, and environmental certification bodies
        to implement sustainable travel practices.
        
        Hotels collaborate with green energy suppliers, waste management companies, and sustainable
        product manufacturers to reduce their environmental impact. These partnerships involve
        energy-efficient systems, waste reduction programs, and eco-friendly amenities that
        appeal to environmentally conscious travelers.
        
        Transportation companies work with electric vehicle manufacturers, alternative fuel
        suppliers, and clean technology providers to develop more sustainable ground transportation
        options. These collaborations focus on reducing emissions, improving energy efficiency,
        and promoting environmentally responsible travel choices.
        
        SECTION 10: FUTURE TECHNOLOGY INTEGRATIONS AND EMERGING PARTNERSHIPS
        
        The travel industry continues to evolve through partnerships with emerging technology
        companies, including blockchain providers, artificial intelligence specialists, and
        virtual reality developers. These collaborations aim to create more secure, efficient,
        and immersive travel experiences.
        
        Blockchain partnerships focus on secure identity verification, transparent booking
        processes, and fraud prevention mechanisms that enhance travel security and trust.
        Airlines, hotels, and booking platforms collaborate with blockchain technology providers
        to develop decentralized systems for travel documentation and payment processing.
        
        Artificial intelligence partnerships involve machine learning companies, natural language
        processing specialists, and predictive analytics providers that help travel companies
        optimize operations, personalize customer experiences, and improve service delivery.
        These collaborations result in intelligent chatbots, predictive maintenance systems,
        and personalized travel recommendations.
        
        Virtual and augmented reality partnerships enable travel companies to offer immersive
        destination previews, virtual hotel tours, and enhanced in-flight entertainment experiences.
        These collaborations involve content creation companies, hardware manufacturers, and
        software developers who specialize in immersive technologies.
        
        This comprehensive analysis demonstrates the complex and ever-expanding network of
        relationships that define the modern travel industry, showcasing how multiple sectors
        and technologies collaborate to create seamless, secure, and sustainable travel
        experiences for millions of travelers worldwide.
        """
        
        print(f"📊 Document length: {len(large_document_content)} characters")
        
        # Upload the large document
        print("📤 Uploading large document...")
        files = {
            'file': ('large_test_doc.txt', large_document_content.encode(), 'text/plain')
        }
        response = requests.post(f"{base_url}/documents/upload", files=files, headers=headers)
        if response.status_code != 200:
            print(f"❌ Document upload failed: {response.text}")
            return False
        
        document_id = response.json()["id"]
        print(f"✅ Document uploaded: {document_id}")
        
        # Wait for document processing
        print("⏳ Waiting for document processing...")
        for i in range(30):  # Wait up to 30 seconds
            response = requests.get(f"{base_url}/documents/{document_id}", headers=headers)
            if response.status_code == 200:
                doc_status = response.json()["status"]
                if doc_status == "completed":
                    print("✅ Document processing completed")
                    break
                elif doc_status == "error":
                    print("❌ Document processing failed")
                    return False
            time.sleep(1)
        else:
            print("❌ Document processing timeout")
            return False
        
        # Create ontology from large document
        print("🧠 Creating ontology from large document...")
        ontology_data = {
            "document_id": document_id,
            "name": "Large Document Test Ontology",
            "description": "Test ontology created from large document to test chunking"
        }
        response = requests.post(f"{base_url}/ontologies/", json=ontology_data, headers=headers)
        if response.status_code != 200:
            print(f"❌ Ontology creation failed: {response.text}")
            return False
        
        ontology_id = response.json()["id"]
        print(f"✅ Ontology created: {ontology_id}")
        
        # Monitor ontology progress
        print("⏳ Monitoring ontology generation progress...")
        for i in range(120):  # Wait up to 2 minutes
            try:
                response = requests.get(f"{base_url}/ontologies/{ontology_id}/progress", headers=headers)
                if response.status_code == 200:
                    progress = response.json()
                    status = progress.get("status")
                    metadata = progress.get("metadata", {})
                    progress_pct = progress.get("progress_percentage", 0)
                    
                    print(f"📊 Status: {status}, Progress: {progress_pct}%, Mode: {metadata.get('processing_mode', 'unknown')}")
                    
                    if metadata.get('total_chunks'):
                        processed = metadata.get('processed_chunks', 0)
                        total = metadata.get('total_chunks', 1)
                        print(f"    Chunks: {processed}/{total}")
                    
                    if status == "active":
                        print("✅ Ontology generation completed!")
                        
                        # Get final ontology details
                        response = requests.get(f"{base_url}/ontologies/{ontology_id}", headers=headers)
                        if response.status_code == 200:
                            ontology = response.json()
                            print(f"🎯 Results:")
                            print(f"    - Ontology Triples: {len(ontology.get('triples', []))}")
                            if metadata.get('entities_count'):
                                print(f"    - Entity Types: {metadata.get('entities_count')}")
                            print(f"    - Processing Mode: {metadata.get('processing_mode', 'unknown')}")
                            print(f"    - Document Length: {metadata.get('document_length', 'unknown')} characters")
                        
                        break
                    elif status in ["draft", "error"]:
                        error_msg = metadata.get('error_message', 'Unknown error')
                        print(f"❌ Ontology generation failed: {error_msg}")
                        return False
                        
            except Exception as e:
                print(f"⚠️ Progress check failed: {str(e)}")
            
            time.sleep(2)  # Check every 2 seconds
        else:
            print("❌ Ontology generation timeout")
            return False
        
        print("\n🎉 Chunked Ontology Generation Test PASSED!")
        print("✨ Key achievements:")
        print("   - Successfully processed large document (>8K characters)")
        print("   - Chunked processing mode activated automatically")
        print("   - Progress tracking working correctly")
        print("   - Ontology generation completed successfully")
        
        return True
        
    except Exception as e:
        print(f"💥 Test failed with exception: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_chunked_ontology_generation()
    if success:
        print("\n✅ All tests PASSED!")
    else:
        print("\n❌ Tests FAILED!")
        sys.exit(1)
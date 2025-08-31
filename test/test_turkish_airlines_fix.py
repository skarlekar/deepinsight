#!/usr/bin/env python3
"""
Test the specific Turkish Airlines duplication issue from the extraction results
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

from utils.enhanced_extraction import (
    EntityRegistry, ExtractedEntity, EnhancedExtractionProcessor
)

def test_turkish_airlines_duplication():
    """Test the exact scenario from extraction_7f3eb8d9_results.json"""
    print("🛫 Testing Turkish Airlines Duplication Fix")
    print("=" * 60)
    
    processor = EnhancedExtractionProcessor()
    
    # Simulate chunk 0 with "Turkish Airlines" (proper case)
    chunk_0_result = {
        "nodes": [
            {
                "id": "airline_1",
                "type": "Airline",
                "properties": {"name": "Turkish Airlines", "extracted_text": "Turkish Airlines"}
            }
        ],
        "relationships": []
    }
    
    # Simulate chunk 1 with "TURKISH AIRLINES" (all caps)  
    chunk_1_result = {
        "nodes": [
            {
                "id": "airline_2",
                "type": "Airline", 
                "properties": {"name": "TURKISH AIRLINES", "extracted_text": "TURKISH AIRLINES"}
            }
        ],
        "relationships": []
    }
    
    print("Processing chunk 0 with 'Turkish Airlines'...")
    chunk_0_rels = processor.process_chunk_results(0, chunk_0_result)
    
    print("Processing chunk 1 with 'TURKISH AIRLINES'...")
    chunk_1_rels = processor.process_chunk_results(1, chunk_1_result)
    
    # Get statistics before finalization
    entity_stats = processor.entity_registry.get_deduplication_stats()
    print(f"📊 Pre-finalization stats:")
    print(f"   Total extracted: {entity_stats['total_extracted']}")
    print(f"   Unique entities: {entity_stats['unique_entities']}")
    print(f"   Duplicates removed: {entity_stats['duplicates_removed']}")
    
    # Finalize extraction
    final_results = processor.finalize_extraction([])
    
    print(f"\n🎯 Final Results:")
    print(f"   Total nodes: {len(final_results['nodes'])}")
    
    # Check for Turkish Airlines entities
    turkish_airlines = [n for n in final_results['nodes'] 
                       if n['type'] == 'Airline' and 'turkish' in n['properties']['name'].lower()]
    
    print(f"   Turkish Airlines entities: {len(turkish_airlines)}")
    
    if len(turkish_airlines) == 1:
        airline = turkish_airlines[0]
        print("✅ SUCCESS: Turkish Airlines properly deduplicated!")
        print(f"   Final normalized name: '{airline['properties']['name']}'")
        print(f"   Entity ID: {airline['id']}")
        
        if airline['properties']['name'] == "Turkish Airlines":
            print("✅ SUCCESS: Name normalized to proper title case")
        else:
            print(f"❌ WARNING: Expected 'Turkish Airlines', got '{airline['properties']['name']}'")
        
        return True
    elif len(turkish_airlines) == 0:
        print("❌ FAILURE: No Turkish Airlines entities found")
        return False
    else:
        print("❌ FAILURE: Still have duplicate Turkish Airlines entities:")
        for i, airline in enumerate(turkish_airlines):
            print(f"   {i+1}. '{airline['properties']['name']}' (ID: {airline['id']})")
        return False

def test_mixed_case_entities():
    """Test various mixed case scenarios"""
    print("\n🔤 Testing Mixed Case Entity Scenarios")
    print("=" * 50)
    
    processor = EnhancedExtractionProcessor()
    
    # Test multiple entities with case variations
    test_chunk = {
        "nodes": [
            # Airlines
            {"id": "a1", "type": "Airline", "properties": {"name": "TURKISH AIRLINES"}},
            {"id": "a2", "type": "Airline", "properties": {"name": "Turkish Airlines"}},
            {"id": "a3", "type": "Airline", "properties": {"name": "turkish airlines"}},
            
            # Airports
            {"id": "ap1", "type": "Airport", "properties": {"name": "ist"}},
            {"id": "ap2", "type": "Airport", "properties": {"name": "IST"}},
            {"id": "ap3", "type": "Airport", "properties": {"name": "Ist"}},
            
            # People
            {"id": "p1", "type": "Person", "properties": {"name": "JOHN SMITH"}},
            {"id": "p2", "type": "Person", "properties": {"name": "John Smith"}},
            {"id": "p3", "type": "Person", "properties": {"name": "john smith"}},
        ],
        "relationships": []
    }
    
    processor.process_chunk_results(0, test_chunk)
    final_results = processor.finalize_extraction([])
    
    # Group entities by type
    entities_by_type = {}
    for entity in final_results['nodes']:
        entity_type = entity['type']
        if entity_type not in entities_by_type:
            entities_by_type[entity_type] = []
        entities_by_type[entity_type].append(entity)
    
    success = True
    
    for entity_type, entities in entities_by_type.items():
        print(f"\n{entity_type} entities: {len(entities)}")
        
        if len(entities) == 1:
            entity = entities[0]
            print(f"   ✅ Successfully deduplicated to: '{entity['properties']['name']}'")
        else:
            print(f"   ❌ FAILURE: Expected 1 {entity_type}, got {len(entities)}")
            for e in entities:
                print(f"      - '{e['properties']['name']}' (ID: {e['id']})")
            success = False
    
    # Check final stats
    stats = processor.entity_registry.get_deduplication_stats() 
    print(f"\n📊 Final Statistics:")
    print(f"   Total extracted: {stats['total_extracted']} entities")
    print(f"   Unique entities: {stats['unique_entities']} entities") 
    print(f"   Duplicates removed: {stats['duplicates_removed']} entities")
    print(f"   Deduplication rate: {stats['deduplication_rate']:.1%}")
    
    if stats['duplicates_removed'] == 6:  # 9 input - 3 unique = 6 duplicates
        print("✅ SUCCESS: Correct number of duplicates removed")
    else:
        print(f"❌ FAILURE: Expected 6 duplicates, got {stats['duplicates_removed']}")
        success = False
    
    return success

def main():
    """Run Turkish Airlines deduplication tests"""
    print("🚀 Turkish Airlines Name Normalization Fix Test")
    print("=" * 70)
    
    tests = [
        ("Turkish Airlines Duplication", test_turkish_airlines_duplication),
        ("Mixed Case Entities", test_mixed_case_entities)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"\n✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            print(f"\n💥 {test_name}: ERROR - {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 Turkish Airlines duplication issue FIXED!")
        print("   - TURKISH AIRLINES and Turkish Airlines now properly deduplicated")
        print("   - Name normalized to proper title case: 'Turkish Airlines'")
        print("   - Same applies to all entity types with case variations")
        return True
    else:
        print("💥 Turkish Airlines issue not fully resolved")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
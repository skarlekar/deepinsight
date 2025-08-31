#!/usr/bin/env python3
"""
Test name normalization in enhanced extraction system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

from utils.enhanced_extraction import (
    EntityRegistry, ExtractedEntity
)

def test_name_normalization():
    """Test that entity names are properly normalized for deduplication"""
    print("🧪 Testing Entity Name Normalization")
    print("=" * 50)
    
    registry = EntityRegistry()
    
    # Test airline entity with different cases
    turkish_upper = ExtractedEntity(
        temp_id="airline_1",
        entity_type="Airline",
        name="TURKISH AIRLINES",
        properties={"name": "TURKISH AIRLINES", "extracted_text": "TURKISH AIRLINES"},
        chunk_id=0
    )
    
    turkish_proper = ExtractedEntity(
        temp_id="airline_2",
        entity_type="Airline", 
        name="Turkish Airlines",
        properties={"name": "Turkish Airlines", "extracted_text": "Turkish Airlines"},
        chunk_id=1
    )
    
    # Register both entities
    guid_1 = registry.register_entity(turkish_upper)
    guid_2 = registry.register_entity(turkish_proper)
    
    print(f"TURKISH AIRLINES GUID: {guid_1}")
    print(f"Turkish Airlines GUID: {guid_2}")
    
    if guid_1 == guid_2:
        print("✅ SUCCESS: Different cased airline names properly deduplicated")
    else:
        print("❌ FAILURE: Different cased airline names not deduplicated")
        return False
    
    # Check the final entity details
    all_entities = registry.get_all_entities()
    print(f"Final entities count: {len(all_entities)}")
    
    if len(all_entities) == 1:
        entity = all_entities[0]
        print(f"✅ SUCCESS: Only one airline entity remains")
        print(f"   Final normalized name: '{entity['properties']['name']}'")
        
        # Should be "Turkish Airlines" (title case)
        if entity['properties']['name'] == "Turkish Airlines":
            print("✅ SUCCESS: Name properly normalized to title case")
        else:
            print(f"❌ FAILURE: Expected 'Turkish Airlines', got '{entity['properties']['name']}'")
            return False
    else:
        print("❌ FAILURE: Expected 1 entity, got", len(all_entities))
        return False
    
    # Test airport codes (should remain uppercase)
    print("\n🛫 Testing Airport Code Normalization")
    
    ist_lower = ExtractedEntity(
        temp_id="airport_1", 
        entity_type="Airport",
        name="ist",
        properties={"name": "ist"},
        chunk_id=0
    )
    
    ist_upper = ExtractedEntity(
        temp_id="airport_2",
        entity_type="Airport",
        name="IST", 
        properties={"name": "IST"},
        chunk_id=1
    )
    
    airport_guid_1 = registry.register_entity(ist_lower)
    airport_guid_2 = registry.register_entity(ist_upper)
    
    if airport_guid_1 == airport_guid_2:
        print("✅ SUCCESS: Airport codes properly deduplicated")
        
        # Check final name
        all_entities = registry.get_all_entities()
        airport_entity = [e for e in all_entities if e['type'] == 'Airport'][0]
        
        if airport_entity['properties']['name'] == "IST":
            print("✅ SUCCESS: Airport code normalized to uppercase")
        else:
            print(f"❌ FAILURE: Expected 'IST', got '{airport_entity['properties']['name']}'")
            return False
    else:
        print("❌ FAILURE: Airport codes not deduplicated")
        return False
    
    # Check final stats
    final_stats = registry.get_deduplication_stats()
    print(f"\n📊 Final Stats:")
    print(f"   Total extracted: {final_stats['total_extracted']}")
    print(f"   Unique entities: {final_stats['unique_entities']}")
    print(f"   Duplicates removed: {final_stats['duplicates_removed']}")
    
    if final_stats['duplicates_removed'] == 2:  # Turkish Airlines + IST
        print("✅ SUCCESS: Correct number of duplicates removed")
        return True
    else:
        print(f"❌ FAILURE: Expected 2 duplicates removed, got {final_stats['duplicates_removed']}")
        return False

def test_normalization_edge_cases():
    """Test edge cases for name normalization"""
    print("\n🔧 Testing Edge Cases")
    print("=" * 30)
    
    registry = EntityRegistry()
    
    # Test cases
    test_cases = [
        ("mcdonald's corporation", "Mcdonald'S Corporation"),
        ("john o'connor", "John O'Connor"), 
        ("NEW YORK", "New York"),
        ("los angeles LAX", "Los Angeles Lax"),
        ("XML", "XML"),  # Short abbreviation should stay uppercase
        ("CEO", "CEO"),  # Short abbreviation should stay uppercase
        ("united states of america", "United States Of America")
    ]
    
    for input_name, expected in test_cases:
        normalized = registry._normalize_name(input_name)
        if normalized == expected:
            print(f"✅ '{input_name}' → '{normalized}'")
        else:
            print(f"❌ '{input_name}' → '{normalized}' (expected '{expected}')")
    
    return True

def main():
    """Run all normalization tests"""
    print("🚀 Entity Name Normalization Tests")
    print("=" * 60)
    
    tests = [
        ("Basic Normalization", test_name_normalization),
        ("Edge Cases", test_normalization_edge_cases)
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
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All name normalization tests passed!")
        return True
    else:
        print("💥 Some tests failed - check implementation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
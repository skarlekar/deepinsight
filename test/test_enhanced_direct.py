#!/usr/bin/env python3
"""
Direct test of enhanced extraction components without API calls
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

from utils.enhanced_extraction import (
    EntityRegistry, RelationshipResolver, EnhancedExtractionProcessor,
    ExtractedEntity, ExtractedRelationship
)

def test_entity_registry():
    """Test EntityRegistry deduplication logic"""
    print("🧪 Testing Entity Registry Deduplication")
    print("=" * 50)
    
    registry = EntityRegistry()
    
    # Create duplicate IST airports from different chunks
    ist_chunk_0 = ExtractedEntity(
        temp_id="airport_1",
        entity_type="Airport",
        name="IST",
        properties={"name": "IST", "city": "Istanbul"},
        chunk_id=0
    )
    
    ist_chunk_1 = ExtractedEntity(
        temp_id="airport_2", 
        entity_type="Airport",
        name="IST",
        properties={"name": "IST", "city": "Istanbul", "country": "Turkey"},
        chunk_id=1
    )
    
    # Register both entities
    guid_1 = registry.register_entity(ist_chunk_0)
    guid_2 = registry.register_entity(ist_chunk_1)
    
    print(f"First IST registration: {guid_1}")
    print(f"Second IST registration: {guid_2}")
    
    if guid_1 == guid_2:
        print("✅ SUCCESS: IST airport properly deduplicated - same GUID returned")
    else:
        print("❌ FAILURE: IST airport not deduplicated - different GUIDs")
        return False
    
    # Test stats
    stats = registry.get_deduplication_stats()
    print(f"📊 Stats: {stats['total_extracted']} extracted, {stats['unique_entities']} unique, {stats['duplicates_removed']} duplicates removed")
    
    if stats['duplicates_removed'] == 1:
        print("✅ SUCCESS: Deduplication stats correct")
    else:
        print("❌ FAILURE: Expected 1 duplicate removed, got", stats['duplicates_removed'])
        return False
    
    # Test all entities
    all_entities = registry.get_all_entities()
    print(f"Final entities count: {len(all_entities)}")
    
    if len(all_entities) == 1:
        print("✅ SUCCESS: Only one unique IST entity in final results")
        print(f"   Entity: {all_entities[0]}")
        
        # Check name property
        if all_entities[0]['properties'].get('name') == 'IST':
            print("✅ SUCCESS: Entity has correct name property")
        else:
            print("❌ FAILURE: Entity missing or incorrect name property")
            return False
    else:
        print("❌ FAILURE: Expected 1 entity, got", len(all_entities))
        return False
    
    return True

def test_relationship_resolver():
    """Test RelationshipResolver cross-chunk mapping"""
    print("\n🔗 Testing Relationship Resolver")
    print("=" * 50)
    
    registry = EntityRegistry()
    
    # Create entities
    person = ExtractedEntity(
        temp_id="person_1",
        entity_type="Person", 
        name="John Smith",
        properties={"name": "John Smith"},
        chunk_id=0
    )
    
    airport = ExtractedEntity(
        temp_id="airport_1",
        entity_type="Airport",
        name="IST", 
        properties={"name": "IST"},
        chunk_id=1  # Different chunk
    )
    
    # Register entities
    person_guid = registry.register_entity(person)
    airport_guid = registry.register_entity(airport)
    
    print(f"Person GUID: {person_guid}")
    print(f"Airport GUID: {airport_guid}")
    
    # Create relationship between entities from different chunks
    relationship = ExtractedRelationship(
        temp_id="rel_1",
        relationship_type="TRAVELS_TO",
        source_temp_id="person_1",  # chunk 0 temp ID
        target_temp_id="airport_1", # chunk 1 temp ID
        properties={},
        chunk_id=0  # Relationship found in chunk 0
    )
    
    # Resolve relationship
    resolver = RelationshipResolver(registry)
    resolved_rels = resolver.resolve_relationships([relationship])
    
    print(f"Resolved relationships: {len(resolved_rels)}")
    
    if len(resolved_rels) == 1:
        rel = resolved_rels[0]
        print(f"✅ SUCCESS: Relationship resolved")
        print(f"   Source: {rel['source_id']} (should be {person_guid})")
        print(f"   Target: {rel['target_id']} (should be {airport_guid})")
        
        if rel['source_id'] == person_guid and rel['target_id'] == airport_guid:
            print("✅ SUCCESS: Relationship IDs correctly mapped to GUIDs")
            return True
        else:
            print("❌ FAILURE: Relationship IDs not correctly mapped")
            return False
    else:
        print("❌ FAILURE: Expected 1 resolved relationship")
        return False

def test_enhanced_processor():
    """Test complete EnhancedExtractionProcessor workflow"""
    print("\n🔄 Testing Enhanced Extraction Processor")
    print("=" * 50)
    
    processor = EnhancedExtractionProcessor()
    
    # Simulate chunk 0 results
    chunk_0_result = {
        "nodes": [
            {
                "id": "person_1",
                "type": "Person",
                "properties": {"name": "John Smith", "age": "30"}
            },
            {
                "id": "airport_1", 
                "type": "Airport",
                "properties": {"name": "IST", "city": "Istanbul"}
            }
        ],
        "relationships": [
            {
                "id": "rel_1",
                "type": "TRAVELS_TO",
                "source_id": "person_1",
                "target_id": "airport_1",
                "properties": {}
            }
        ]
    }
    
    # Simulate chunk 1 results (with duplicate IST)
    chunk_1_result = {
        "nodes": [
            {
                "id": "airport_2",  # Different temp ID
                "type": "Airport", 
                "properties": {"name": "IST", "country": "Turkey"}  # Same name - should deduplicate
            },
            {
                "id": "flight_1",
                "type": "Flight",
                "properties": {"name": "AA100", "number": "AA100"}
            }
        ],
        "relationships": [
            {
                "id": "rel_2", 
                "type": "DEPARTS_FROM",
                "source_id": "flight_1",
                "target_id": "airport_2",  # Reference to duplicate IST
                "properties": {}
            }
        ]
    }
    
    # Process chunks
    print("Processing chunk 0...")
    chunk_0_rels = processor.process_chunk_results(0, chunk_0_result)
    
    print("Processing chunk 1...")  
    chunk_1_rels = processor.process_chunk_results(1, chunk_1_result)
    
    # Combine all relationships
    all_relationships = chunk_0_rels + chunk_1_rels
    
    # Finalize extraction
    print("Finalizing extraction...")
    final_results = processor.finalize_extraction(all_relationships)
    
    print(f"Final results:")
    print(f"  Nodes: {len(final_results['nodes'])}")
    print(f"  Relationships: {len(final_results['relationships'])}")
    
    # Check for deduplication
    ist_nodes = [n for n in final_results['nodes'] if n['properties'].get('name') == 'IST']
    print(f"  IST airports: {len(ist_nodes)}")
    
    if len(ist_nodes) == 1:
        print("✅ SUCCESS: IST airport properly deduplicated")
        print(f"     IST node: {ist_nodes[0]}")
    else:
        print("❌ FAILURE: IST airport not properly deduplicated")
        return False
    
    # Check metadata
    stats = final_results['metadata']['entity_stats']
    print(f"📊 Entity Stats: {stats}")
    
    if stats['duplicates_removed'] > 0:
        print("✅ SUCCESS: Deduplication occurred")
    else:
        print("❌ FAILURE: No deduplication detected")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Enhanced Extraction Component Tests")
    print("=" * 60)
    
    tests = [
        ("Entity Registry", test_entity_registry),
        ("Relationship Resolver", test_relationship_resolver), 
        ("Enhanced Processor", test_enhanced_processor)
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
        print("🎉 All enhanced extraction components working correctly!")
        return True
    else:
        print("💥 Some tests failed - check implementation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
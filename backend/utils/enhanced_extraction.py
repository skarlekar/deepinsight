"""
Enhanced extraction system with Entity Registry and Relationship Resolver
for GUID-based node IDs and mandatory name properties.
"""
import uuid
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ExtractedEntity:
    """Represents an extracted entity with its properties"""
    temp_id: str  # AI-generated temporary ID
    entity_type: str
    name: str
    properties: Dict[str, Any]
    source_location: Optional[str] = None
    chunk_id: Optional[int] = None

@dataclass
class ExtractedRelationship:
    """Represents an extracted relationship"""
    temp_id: str
    relationship_type: str
    source_temp_id: str
    target_temp_id: str
    properties: Dict[str, Any]
    source_location: Optional[str] = None
    chunk_id: Optional[int] = None

class EntityRegistry:
    """
    Registry for managing unique entities across document chunks.
    Implements GUID-based deduplication using entity type + normalized name combination.
    """
    
    def __init__(self):
        self.entities: Dict[Tuple[str, str], str] = {}  # {(type, normalized_name): guid}
        self.ai_id_mapping: Dict[str, str] = {}  # {temp_id_with_chunk: final_guid}
        self.entity_details: Dict[str, ExtractedEntity] = {}  # {guid: entity_details}
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize entity name to consistent format for deduplication.
        Converts to title case for proper nouns (organizations, people, places).
        """
        if not name:
            return name
        
        # Basic normalization: strip whitespace and convert to title case
        normalized = name.strip()
        
        # For entities that are likely proper nouns, use title case
        # This converts "TURKISH AIRLINES" -> "Turkish Airlines"
        # and keeps "Turkish Airlines" as "Turkish Airlines"
        normalized = normalized.title()
        
        # Handle common abbreviations and codes that should remain uppercase
        # Airport codes, airline codes, etc.
        if len(normalized) <= 4 and normalized.isalpha():
            normalized = normalized.upper()
        
        return normalized
        
    def register_entity(self, entity: ExtractedEntity) -> str:
        """
        Register an entity and return its consistent GUID.
        If entity already exists (same type + normalized name), return existing GUID.
        """
        if not entity.name:
            raise ValueError(f"Entity {entity.temp_id} missing mandatory 'name' property")
        
        # Normalize the name for consistent deduplication
        normalized_name = self._normalize_name(entity.name)
        
        # Create unique key using type and normalized name
        entity_key = (entity.entity_type, normalized_name)
        
        # Check if entity already exists
        if entity_key in self.entities:
            existing_guid = self.entities[entity_key]
            # Update mapping for this temp_id
            temp_key = f"chunk_{entity.chunk_id}_{entity.temp_id}"
            self.ai_id_mapping[temp_key] = existing_guid
            
            # Merge properties if needed (keep most complete version)
            existing_entity = self.entity_details[existing_guid]
            if len(entity.properties) > len(existing_entity.properties):
                # Update entity with normalized name
                entity.name = normalized_name
                entity.properties['name'] = normalized_name
                self.entity_details[existing_guid] = entity
                self.entity_details[existing_guid].temp_id = existing_guid  # Use GUID as final ID
            
            logger.info(f"Reused existing entity {existing_guid} for {entity_key}")
            return existing_guid
        else:
            # Create new GUID for new entity
            new_guid = str(uuid.uuid4())
            self.entities[entity_key] = new_guid
            
            # Update mapping
            temp_key = f"chunk_{entity.chunk_id}_{entity.temp_id}"
            self.ai_id_mapping[temp_key] = new_guid
            
            # Store entity details with GUID as final ID and normalized name
            entity.name = normalized_name
            entity.properties['name'] = normalized_name
            entity.temp_id = new_guid
            self.entity_details[new_guid] = entity
            
            logger.info(f"Created new entity {new_guid} for {entity_key}")
            return new_guid
    
    def resolve_temp_id(self, chunk_id: int, temp_id: str) -> Optional[str]:
        """Resolve a temporary AI-generated ID to its final GUID"""
        temp_key = f"chunk_{chunk_id}_{temp_id}"
        return self.ai_id_mapping.get(temp_key)
    
    def get_all_entities(self) -> List[Dict[str, Any]]:
        """Get all unique entities as JSON-serializable dicts"""
        entities = []
        for guid, entity in self.entity_details.items():
            entities.append({
                "id": guid,
                "type": entity.entity_type,
                "properties": entity.properties,
                "source_location": entity.source_location
            })
        return entities
    
    def get_entity_count(self) -> int:
        """Get total number of unique entities"""
        return len(self.entity_details)
    
    def get_deduplication_stats(self) -> Dict[str, Any]:
        """Get statistics about deduplication"""
        total_temp_ids = len(self.ai_id_mapping)
        unique_entities = len(self.entity_details)
        duplicates_removed = total_temp_ids - unique_entities
        
        return {
            "total_extracted": total_temp_ids,
            "unique_entities": unique_entities,
            "duplicates_removed": duplicates_removed,
            "deduplication_rate": duplicates_removed / total_temp_ids if total_temp_ids > 0 else 0
        }

class RelationshipResolver:
    """
    Resolves relationships between entities across document chunks using EntityRegistry.
    """
    
    def __init__(self, entity_registry: EntityRegistry):
        self.entity_registry = entity_registry
        self.resolved_relationships: List[Dict[str, Any]] = []
        self.orphaned_relationships: List[ExtractedRelationship] = []
    
    def resolve_relationships(self, all_relationships: List[ExtractedRelationship]) -> List[Dict[str, Any]]:
        """
        Resolve all relationships using entity registry to map temp IDs to GUIDs.
        """
        resolved_relationships = []
        orphaned_relationships = []
        
        for rel in all_relationships:
            # Resolve source and target entity GUIDs - try all chunks since entities may be in different chunks
            source_guid = self._resolve_temp_id_any_chunk(rel.source_temp_id)
            target_guid = self._resolve_temp_id_any_chunk(rel.target_temp_id)
            
            if source_guid and target_guid:
                # Successfully resolved relationship
                resolved_rel = {
                    "id": str(uuid.uuid4()),
                    "type": rel.relationship_type,
                    "source_id": source_guid,
                    "target_id": target_guid,
                    "properties": rel.properties,
                    "source_location": rel.source_location
                }
                resolved_relationships.append(resolved_rel)
                logger.debug(f"Resolved relationship {rel.temp_id}: {source_guid} -> {target_guid}")
            else:
                # Orphaned relationship - couldn't resolve entities
                orphaned_relationships.append(rel)
                logger.warning(f"Orphaned relationship {rel.temp_id}: source={rel.source_temp_id} target={rel.target_temp_id}")
        
        self.resolved_relationships = resolved_relationships
        self.orphaned_relationships = orphaned_relationships
        
        logger.info(f"Resolved {len(resolved_relationships)} relationships, {len(orphaned_relationships)} orphaned")
        return resolved_relationships
    
    def _resolve_temp_id_any_chunk(self, temp_id: str) -> Optional[str]:
        """
        Resolve temp_id by searching across all chunks since entities can be found in different chunks
        """
        # Check all possible chunk mappings for this temp_id
        for temp_key, guid in self.entity_registry.ai_id_mapping.items():
            if temp_key.endswith(f"_{temp_id}"):  # Match temp_id regardless of chunk
                return guid
        return None
    
    def get_relationship_stats(self) -> Dict[str, Any]:
        """Get statistics about relationship resolution"""
        total_relationships = len(self.resolved_relationships) + len(self.orphaned_relationships)
        
        return {
            "total_relationships": total_relationships,
            "resolved_relationships": len(self.resolved_relationships),
            "orphaned_relationships": len(self.orphaned_relationships),
            "resolution_rate": len(self.resolved_relationships) / total_relationships if total_relationships > 0 else 0
        }

class EnhancedExtractionProcessor:
    """
    Main processor that orchestrates enhanced extraction with EntityRegistry and RelationshipResolver.
    """
    
    def __init__(self):
        self.entity_registry = EntityRegistry()
        self.relationship_resolver = RelationshipResolver(self.entity_registry)
        
    def process_chunk_results(self, chunk_id: int, chunk_result: Dict[str, Any]) -> None:
        """
        Process results from a single chunk extraction.
        """
        # Process entities
        nodes = chunk_result.get("nodes", [])
        for node_data in nodes:
            # Validate name property
            if "name" not in node_data.get("properties", {}):
                logger.error(f"Node {node_data.get('id')} missing mandatory 'name' property")
                continue
            
            entity = ExtractedEntity(
                temp_id=node_data["id"],
                entity_type=node_data["type"],
                name=node_data["properties"]["name"],
                properties=node_data["properties"],
                source_location=node_data.get("source_location"),
                chunk_id=chunk_id
            )
            
            # Register entity and get GUID
            self.entity_registry.register_entity(entity)
        
        # Process relationships (store for later resolution)
        relationships = chunk_result.get("relationships", [])
        extracted_relationships = []
        
        for rel_data in relationships:
            relationship = ExtractedRelationship(
                temp_id=rel_data["id"],
                relationship_type=rel_data["type"],
                source_temp_id=rel_data["source_id"],
                target_temp_id=rel_data["target_id"],
                properties=rel_data.get("properties", {}),
                source_location=rel_data.get("source_location"),
                chunk_id=chunk_id
            )
            extracted_relationships.append(relationship)
        
        return extracted_relationships
    
    def finalize_extraction(self, all_relationships: List[ExtractedRelationship]) -> Dict[str, Any]:
        """
        Finalize the extraction by resolving all relationships and returning final results.
        """
        # Resolve all relationships
        resolved_relationships = self.relationship_resolver.resolve_relationships(all_relationships)
        
        # Get final entities
        final_entities = self.entity_registry.get_all_entities()
        
        # Compile statistics
        entity_stats = self.entity_registry.get_deduplication_stats()
        relationship_stats = self.relationship_resolver.get_relationship_stats()
        
        return {
            "nodes": final_entities,
            "relationships": resolved_relationships,
            "metadata": {
                "extraction_mode": "enhanced",
                "entity_stats": entity_stats,
                "relationship_stats": relationship_stats,
                "total_unique_entities": len(final_entities),
                "total_resolved_relationships": len(resolved_relationships)
            }
        }

def validate_name_properties(nodes: List[Dict[str, Any]]) -> List[str]:
    """
    Validate that all nodes have mandatory 'name' property.
    Returns list of validation errors.
    """
    errors = []
    
    for i, node in enumerate(nodes):
        node_id = node.get("id", f"node_{i}")
        properties = node.get("properties", {})
        
        if "name" not in properties:
            errors.append(f"Node {node_id} of type {node.get('type')} missing mandatory 'name' property")
        elif not properties["name"]:
            errors.append(f"Node {node_id} has empty 'name' property")
    
    return errors
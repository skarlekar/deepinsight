# DeepInsight LangGraph Agent Implementation Specifications
# Complete agent workflow definitions for ontology creation and data extraction

from langgraph import StateGraph, END
from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel
from anthropic import Anthropic
import json
import re
from datetime import datetime

# ============================================================================
# State Definitions for Agent Workflows
# ============================================================================

class OntologyCreationState(TypedDict):
    """State for ontology creation workflow"""
    # Input data
    document_text: str
    document_id: str
    user_id: str
    chunk_size: int
    overlap_percentage: int
    
    # Processing state
    document_chunks: List[str]
    chunk_metadata: List[Dict[str, Any]]
    current_chunk_index: int
    
    # Extraction results
    extracted_entities: List[Dict[str, Any]]
    extracted_relationships: List[Dict[str, Any]]
    raw_extractions: List[Dict[str, Any]]  # Per-chunk results
    
    # Final output
    ontology_triples: List[Dict[str, Any]]
    
    # Status tracking
    processing_complete: bool
    deduplication_complete: bool
    error_message: Optional[str]
    progress_percentage: int

class DataExtractionState(TypedDict):
    """State for data extraction workflow"""
    # Input data
    document_text: str
    document_id: str
    ontology_schema: Dict[str, Any]
    user_id: str
    extraction_id: str
    chunk_size: int
    overlap_percentage: int
    
    # Processing state
    document_chunks: List[str]
    chunk_metadata: List[Dict[str, Any]]
    current_chunk_index: int
    
    # Extraction results
    extracted_nodes: List[Dict[str, Any]]
    extracted_edges: List[Dict[str, Any]]
    raw_extractions: List[Dict[str, Any]]  # Per-chunk results
    
    # Post-processing
    processed_nodes: List[Dict[str, Any]]
    processed_edges: List[Dict[str, Any]]
    
    # Status tracking
    processing_complete: bool
    deduplication_complete: bool
    error_message: Optional[str]
    progress_percentage: int

# ============================================================================
# LLM Prompt Templates
# ============================================================================

ONTOLOGY_ENTITY_EXTRACTION_PROMPT = """
You are an expert knowledge engineer tasked with extracting entities from document text to create an ontology.

TASK: Analyze the following text chunk and extract ALL distinct entity types that appear in the content.

RULES:
1. Extract only the TYPES of entities, not specific instances
2. Use singular form (e.g., "Person" not "People" or "Persons")
3. Be specific but not overly granular (e.g., "Employee" rather than just "Person" if the context is professional)
4. Include type variations (common synonyms or alternative names)
5. Specify the primitive data type for each entity

PRIMITIVE TYPES:
- string: Text values (names, titles, descriptions)
- integer: Whole numbers (counts, IDs, ages)
- float: Decimal numbers (prices, percentages, measurements)
- boolean: True/false values (flags, status indicators)

TEXT CHUNK:
{text_chunk}

Respond with a JSON array of entity definitions:
[
  {{
    "entity_type": "Person",
    "type_variations": ["Individual", "Employee", "Staff Member"],
    "primitive_type": "string",
    "examples": ["John Smith", "CEO", "Manager"]
  }}
]

Focus on accuracy and completeness. Extract ALL entity types present in the text.
"""

ONTOLOGY_RELATIONSHIP_EXTRACTION_PROMPT = """
You are an expert knowledge engineer tasked with extracting relationship types from document text to create an ontology.

TASK: Analyze the following text chunk and extract ALL types of relationships between entities.

RULES:
1. Extract only the TYPES of relationships, not specific instances
2. Use descriptive relationship names (e.g., "works_for", "manages", "located_in")
3. Include relationship variations (different ways to express the same relationship)
4. Focus on meaningful connections, not trivial associations
5. Use snake_case for relationship names

TEXT CHUNK:
{text_chunk}

ENTITIES ALREADY IDENTIFIED:
{entity_types}

Respond with a JSON array of relationship definitions:
[
  {{
    "relationship_type": "works_for",
    "type_variations": ["employed_by", "works_at", "is_employed_by"],
    "typical_subject_types": ["Person", "Employee"],
    "typical_object_types": ["Organization", "Company"]
  }}
]

Focus on relationships that connect the identified entity types.
"""

ONTOLOGY_TRIPLE_GENERATION_PROMPT = """
You are an expert knowledge engineer creating ontology triples from extracted entities and relationships.

TASK: Create meaningful subject-predicate-object triples that represent the knowledge structure of the document domain.

ENTITIES:
{entities}

RELATIONSHIPS:
{relationships}

RULES:
1. Create triples that make semantic sense: subject-relationship-object
2. Ensure subject and object are entity types, relationship connects them meaningfully
3. Each triple should represent a fundamental relationship in the domain
4. Avoid redundant or overly similar triples
5. Focus on the most important and frequent relationship patterns

Respond with a JSON array of ontology triples:
[
  {{
    "subject": {{
      "entity_type": "Person",
      "type_variations": ["Employee", "Individual"],
      "primitive_type": "string"
    }},
    "relationship": {{
      "relationship_type": "works_for",
      "type_variations": ["employed_by", "works_at"]
    }},
    "object": {{
      "entity_type": "Organization",
      "type_variations": ["Company", "Employer"],
      "primitive_type": "string"
    }}
  }}
]
"""

DATA_EXTRACTION_PROMPT = """
You are an expert data extraction specialist. Extract specific entity instances and their relationships from the text using the provided ontology schema.

ONTOLOGY SCHEMA:
{ontology_schema}

TEXT CHUNK:
{text_chunk}

CHUNK LOCATION: {chunk_location}

TASK: Extract actual entity instances and relationships that match the ontology schema.

RULES:
1. Extract SPECIFIC instances, not types (e.g., "John Smith" not "Person")
2. Only extract entities that match the ontology entity types
3. Only extract relationships that match the ontology relationship types
4. Include the source location for each extracted item
5. Ensure relationships connect valid entity instances
6. Be precise with data types (convert numbers to appropriate types)

Respond with JSON in this exact format:
{{
  "nodes": [
    {{
      "id": "unique_node_id",
      "type": "entity_type_from_ontology",
      "properties": {{
        "name": "actual_value",
        "other_property": "value"
      }},
      "source_location": "page X, paragraph Y" or "line Z"
    }}
  ],
  "relationships": [
    {{
      "id": "unique_relationship_id",
      "type": "relationship_type_from_ontology",
      "source_id": "source_node_id",
      "target_id": "target_node_id",
      "properties": {{}},
      "source_location": "page X, paragraph Y" or "line Z"
    }}
  ]
}}

Be thorough but precise. Only extract what is clearly present in the text.
"""

DEDUPLICATION_PROMPT = """
You are an expert data curator tasked with deduplicating extracted entities and relationships.

EXTRACTED DATA:
{extracted_data}

TASK: Remove duplicates and merge similar entities/relationships while preserving all unique information.

RULES FOR ENTITY DEDUPLICATION:
1. Merge entities with identical names (case-insensitive)
2. Merge entities that are clearly the same (e.g., "John Smith" and "Mr. Smith" in same context)
3. Consolidate properties from merged entities
4. Keep the most complete entity record
5. Update all relationship references to merged entities

RULES FOR RELATIONSHIP DEDUPLICATION:
1. Remove exact duplicates (same type, source, target)
2. Merge relationships with different source locations but same semantic meaning
3. Consolidate properties from merged relationships

Respond with deduplicated JSON in the same format as input.
"""

# ============================================================================
# Agent Node Functions
# ============================================================================

class LLMService:
    """Service for interacting with Claude Sonnet 4"""
    
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        self.max_tokens = 4000
        self.temperature = 0.1
    
    async def generate_response(self, prompt: str) -> str:
        """Generate response from Claude"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"LLM generation failed: {str(e)}")

class DocumentChunker:
    """Service for chunking documents with overlap"""
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap_percentage: int = 10) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks with metadata"""
        overlap_size = int(chunk_size * overlap_percentage / 100)
        chunks = []
        start = 0
        chunk_id = 0
        
        # Split into paragraphs first for better context preservation
        paragraphs = text.split('\n\n')
        current_text = ""
        current_paragraph = 0
        
        for paragraph in paragraphs:
            if len(current_text + paragraph) > chunk_size and current_text:
                # Create chunk
                chunks.append({
                    "chunk_id": f"chunk_{chunk_id:04d}",
                    "text": current_text.strip(),
                    "start_char": start,
                    "end_char": start + len(current_text),
                    "paragraph_start": current_paragraph - current_text.count('\n\n'),
                    "paragraph_end": current_paragraph
                })
                
                # Prepare next chunk with overlap
                if overlap_size > 0:
                    overlap_text = current_text[-overlap_size:]
                    current_text = overlap_text + paragraph
                    start = start + len(current_text) - overlap_size
                else:
                    current_text = paragraph
                    start = start + len(current_text)
                
                chunk_id += 1
                current_paragraph += 1
            else:
                current_text += "\n\n" + paragraph if current_text else paragraph
                current_paragraph += 1
        
        # Add final chunk
        if current_text:
            chunks.append({
                "chunk_id": f"chunk_{chunk_id:04d}",
                "text": current_text.strip(),
                "start_char": start,
                "end_char": start + len(current_text),
                "paragraph_start": current_paragraph - current_text.count('\n\n'),
                "paragraph_end": current_paragraph
            })
        
        return chunks

# ============================================================================
# Ontology Creation Agent Functions
# ============================================================================

def chunk_document_node(state: OntologyCreationState) -> OntologyCreationState:
    """Chunk document with overlap for processing"""
    try:
        chunks_data = DocumentChunker.chunk_text(
            text=state["document_text"],
            chunk_size=state["chunk_size"],
            overlap_percentage=state["overlap_percentage"]
        )
        
        state["document_chunks"] = [chunk["text"] for chunk in chunks_data]
        state["chunk_metadata"] = chunks_data
        state["current_chunk_index"] = 0
        state["progress_percentage"] = 10
        
    except Exception as e:
        state["error_message"] = f"Document chunking failed: {str(e)}"
    
    return state

def extract_entities_node(state: OntologyCreationState) -> OntologyCreationState:
    """Extract entities from all chunks using Claude"""
    try:
        llm_service = LLMService(api_key=os.getenv("ANTHROPIC_API_KEY"))
        all_entities = []
        
        for i, chunk in enumerate(state["document_chunks"]):
            prompt = ONTOLOGY_ENTITY_EXTRACTION_PROMPT.format(text_chunk=chunk)
            response = llm_service.generate_response(prompt)
            
            try:
                entities = json.loads(response)
                all_entities.extend(entities)
            except json.JSONDecodeError:
                # Extract JSON from response if wrapped in markdown
                json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
                if json_match:
                    entities = json.loads(json_match.group(1))
                    all_entities.extend(entities)
                else:
                    raise ValueError("Invalid JSON response from LLM")
            
            # Update progress
            progress = 20 + (30 * (i + 1) // len(state["document_chunks"]))
            state["progress_percentage"] = progress
        
        state["extracted_entities"] = all_entities
        state["progress_percentage"] = 50
        
    except Exception as e:
        state["error_message"] = f"Entity extraction failed: {str(e)}"
    
    return state

def extract_relationships_node(state: OntologyCreationState) -> OntologyCreationState:
    """Extract relationships from all chunks using Claude"""
    try:
        llm_service = LLMService(api_key=os.getenv("ANTHROPIC_API_KEY"))
        all_relationships = []
        
        # Prepare entity types for context
        entity_types = [entity["entity_type"] for entity in state["extracted_entities"]]
        entity_context = json.dumps(entity_types, indent=2)
        
        for i, chunk in enumerate(state["document_chunks"]):
            prompt = ONTOLOGY_RELATIONSHIP_EXTRACTION_PROMPT.format(
                text_chunk=chunk,
                entity_types=entity_context
            )
            response = llm_service.generate_response(prompt)
            
            try:
                relationships = json.loads(response)
                all_relationships.extend(relationships)
            except json.JSONDecodeError:
                json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
                if json_match:
                    relationships = json.loads(json_match.group(1))
                    all_relationships.extend(relationships)
                else:
                    raise ValueError("Invalid JSON response from LLM")
            
            # Update progress
            progress = 50 + (20 * (i + 1) // len(state["document_chunks"]))
            state["progress_percentage"] = progress
        
        state["extracted_relationships"] = all_relationships
        state["progress_percentage"] = 70
        
    except Exception as e:
        state["error_message"] = f"Relationship extraction failed: {str(e)}"
    
    return state

def deduplicate_ontology_node(state: OntologyCreationState) -> OntologyCreationState:
    """Deduplicate extracted entities and relationships"""
    try:
        # Deduplicate entities by type name
        unique_entities = {}
        for entity in state["extracted_entities"]:
            entity_type = entity["entity_type"].lower()
            if entity_type not in unique_entities:
                unique_entities[entity_type] = entity
            else:
                # Merge type variations
                existing_variations = set(unique_entities[entity_type].get("type_variations", []))
                new_variations = set(entity.get("type_variations", []))
                unique_entities[entity_type]["type_variations"] = list(existing_variations | new_variations)
        
        # Deduplicate relationships by type name
        unique_relationships = {}
        for relationship in state["extracted_relationships"]:
            rel_type = relationship["relationship_type"].lower()
            if rel_type not in unique_relationships:
                unique_relationships[rel_type] = relationship
            else:
                # Merge type variations
                existing_variations = set(unique_relationships[rel_type].get("type_variations", []))
                new_variations = set(relationship.get("type_variations", []))
                unique_relationships[rel_type]["type_variations"] = list(existing_variations | new_variations)
        
        state["extracted_entities"] = list(unique_entities.values())
        state["extracted_relationships"] = list(unique_relationships.values())
        state["deduplication_complete"] = True
        state["progress_percentage"] = 80
        
    except Exception as e:
        state["error_message"] = f"Deduplication failed: {str(e)}"
    
    return state

def create_ontology_triples_node(state: OntologyCreationState) -> OntologyCreationState:
    """Create final ontology triple structure"""
    try:
        llm_service = LLMService(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        entities_json = json.dumps(state["extracted_entities"], indent=2)
        relationships_json = json.dumps(state["extracted_relationships"], indent=2)
        
        prompt = ONTOLOGY_TRIPLE_GENERATION_PROMPT.format(
            entities=entities_json,
            relationships=relationships_json
        )
        
        response = llm_service.generate_response(prompt)
        
        try:
            triples = json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                triples = json.loads(json_match.group(1))
            else:
                raise ValueError("Invalid JSON response from LLM")
        
        state["ontology_triples"] = triples
        state["processing_complete"] = True
        state["progress_percentage"] = 100
        
    except Exception as e:
        state["error_message"] = f"Triple creation failed: {str(e)}"
    
    return state

# ============================================================================
# Data Extraction Agent Functions
# ============================================================================

def chunk_document_extraction_node(state: DataExtractionState) -> DataExtractionState:
    """Chunk document for data extraction"""
    try:
        chunks_data = DocumentChunker.chunk_text(
            text=state["document_text"],
            chunk_size=state["chunk_size"],
            overlap_percentage=state["overlap_percentage"]
        )
        
        state["document_chunks"] = [chunk["text"] for chunk in chunks_data]
        state["chunk_metadata"] = chunks_data
        state["current_chunk_index"] = 0
        state["progress_percentage"] = 10
        
    except Exception as e:
        state["error_message"] = f"Document chunking failed: {str(e)}"
    
    return state

def extract_data_node(state: DataExtractionState) -> DataExtractionState:
    """Extract actual data using ontology schema"""
    try:
        llm_service = LLMService(api_key=os.getenv("ANTHROPIC_API_KEY"))
        all_nodes = []
        all_edges = []
        
        ontology_json = json.dumps(state["ontology_schema"], indent=2)
        
        for i, chunk in enumerate(state["document_chunks"]):
            chunk_metadata = state["chunk_metadata"][i]
            location = f"chunk {i+1}, paragraphs {chunk_metadata['paragraph_start']}-{chunk_metadata['paragraph_end']}"
            
            prompt = DATA_EXTRACTION_PROMPT.format(
                ontology_schema=ontology_json,
                text_chunk=chunk,
                chunk_location=location
            )
            
            response = llm_service.generate_response(prompt)
            
            try:
                extraction_result = json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
                if json_match:
                    extraction_result = json.loads(json_match.group(1))
                else:
                    continue  # Skip this chunk if parsing fails
            
            # Add chunk-specific IDs to avoid conflicts
            for node in extraction_result.get("nodes", []):
                node["id"] = f"chunk_{i}_{node['id']}"
                all_nodes.append(node)
            
            for edge in extraction_result.get("relationships", []):
                edge["id"] = f"chunk_{i}_{edge['id']}"
                edge["source_id"] = f"chunk_{i}_{edge['source_id']}"
                edge["target_id"] = f"chunk_{i}_{edge['target_id']}"
                all_edges.append(edge)
            
            # Update progress
            progress = 10 + (70 * (i + 1) // len(state["document_chunks"]))
            state["progress_percentage"] = progress
        
        state["extracted_nodes"] = all_nodes
        state["extracted_edges"] = all_edges
        state["progress_percentage"] = 80
        
    except Exception as e:
        state["error_message"] = f"Data extraction failed: {str(e)}"
    
    return state

def deduplicate_data_node(state: DataExtractionState) -> DataExtractionState:
    """Deduplicate extracted nodes and edges"""
    try:
        # Deduplicate nodes by name and type
        unique_nodes = {}
        node_id_mapping = {}
        
        for node in state["extracted_nodes"]:
            node_key = f"{node['type']}_{node['properties'].get('name', '')}"
            if node_key not in unique_nodes:
                new_id = f"node_{len(unique_nodes):04d}"
                unique_nodes[node_key] = {
                    **node,
                    "id": new_id
                }
                node_id_mapping[node["id"]] = new_id
            else:
                # Merge properties and source locations
                existing_node = unique_nodes[node_key]
                node_id_mapping[node["id"]] = existing_node["id"]
                
                # Merge properties
                for key, value in node["properties"].items():
                    if key not in existing_node["properties"]:
                        existing_node["properties"][key] = value
                
                # Merge source locations
                existing_location = existing_node.get("source_location", "")
                new_location = node.get("source_location", "")
                if new_location and new_location not in existing_location:
                    combined_location = f"{existing_location}, {new_location}" if existing_location else new_location
                    existing_node["source_location"] = combined_location
        
        # Deduplicate edges and update node references
        unique_edges = {}
        for edge in state["extracted_edges"]:
            new_source_id = node_id_mapping.get(edge["source_id"], edge["source_id"])
            new_target_id = node_id_mapping.get(edge["target_id"], edge["target_id"])
            
            edge_key = f"{edge['type']}_{new_source_id}_{new_target_id}"
            if edge_key not in unique_edges:
                unique_edges[edge_key] = {
                    **edge,
                    "id": f"edge_{len(unique_edges):04d}",
                    "source_id": new_source_id,
                    "target_id": new_target_id
                }
            else:
                # Merge source locations
                existing_edge = unique_edges[edge_key]
                existing_location = existing_edge.get("source_location", "")
                new_location = edge.get("source_location", "")
                if new_location and new_location not in existing_location:
                    combined_location = f"{existing_location}, {new_location}" if existing_location else new_location
                    existing_edge["source_location"] = combined_location
        
        state["processed_nodes"] = list(unique_nodes.values())
        state["processed_edges"] = list(unique_edges.values())
        state["deduplication_complete"] = True
        state["processing_complete"] = True
        state["progress_percentage"] = 100
        
    except Exception as e:
        state["error_message"] = f"Data deduplication failed: {str(e)}"
    
    return state

# ============================================================================
# Workflow Graph Definitions
# ============================================================================

def create_ontology_creation_graph() -> StateGraph:
    """Create the ontology creation workflow graph"""
    graph = StateGraph(OntologyCreationState)
    
    # Add nodes
    graph.add_node("chunk_document", chunk_document_node)
    graph.add_node("extract_entities", extract_entities_node)
    graph.add_node("extract_relationships", extract_relationships_node)
    graph.add_node("deduplicate", deduplicate_ontology_node)
    graph.add_node("create_triples", create_ontology_triples_node)
    
    # Define edges (workflow flow)
    graph.add_edge("chunk_document", "extract_entities")
    graph.add_edge("extract_entities", "extract_relationships")
    graph.add_edge("extract_relationships", "deduplicate")
    graph.add_edge("deduplicate", "create_triples")
    graph.add_edge("create_triples", END)
    
    # Set entry point
    graph.set_entry_point("chunk_document")
    
    return graph

def create_data_extraction_graph() -> StateGraph:
    """Create the data extraction workflow graph"""
    graph = StateGraph(DataExtractionState)
    
    # Add nodes
    graph.add_node("chunk_document", chunk_document_extraction_node)
    graph.add_node("extract_data", extract_data_node)
    graph.add_node("deduplicate_data", deduplicate_data_node)
    
    # Define edges
    graph.add_edge("chunk_document", "extract_data")
    graph.add_edge("extract_data", "deduplicate_data")
    graph.add_edge("deduplicate_data", END)
    
    # Set entry point
    graph.set_entry_point("chunk_document")
    
    return graph

# ============================================================================
# Workflow Execution Functions
# ============================================================================

async def execute_ontology_creation(
    document_text: str,
    document_id: str,
    user_id: str,
    chunk_size: int = 1000,
    overlap_percentage: int = 10
) -> Dict[str, Any]:
    """Execute ontology creation workflow"""
    
    # Initialize state
    initial_state: OntologyCreationState = {
        "document_text": document_text,
        "document_id": document_id,
        "user_id": user_id,
        "chunk_size": chunk_size,
        "overlap_percentage": overlap_percentage,
        "document_chunks": [],
        "chunk_metadata": [],
        "current_chunk_index": 0,
        "extracted_entities": [],
        "extracted_relationships": [],
        "raw_extractions": [],
        "ontology_triples": [],
        "processing_complete": False,
        "deduplication_complete": False,
        "error_message": None,
        "progress_percentage": 0
    }
    
    # Create and execute workflow
    workflow = create_ontology_creation_graph()
    compiled_workflow = workflow.compile()
    
    try:
        final_state = compiled_workflow.invoke(initial_state)
        return {
            "success": True,
            "ontology_triples": final_state["ontology_triples"],
            "entities_count": len(final_state["extracted_entities"]),
            "relationships_count": len(final_state["extracted_relationships"]),
            "triples_count": len(final_state["ontology_triples"]),
            "processing_complete": final_state["processing_complete"],
            "error_message": final_state["error_message"]
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": str(e),
            "ontology_triples": [],
            "processing_complete": False
        }

async def execute_data_extraction(
    document_text: str,
    document_id: str,
    ontology_schema: Dict[str, Any],
    user_id: str,
    extraction_id: str,
    chunk_size: int = 1000,
    overlap_percentage: int = 10
) -> Dict[str, Any]:
    """Execute data extraction workflow"""
    
    # Initialize state
    initial_state: DataExtractionState = {
        "document_text": document_text,
        "document_id": document_id,
        "ontology_schema": ontology_schema,
        "user_id": user_id,
        "extraction_id": extraction_id,
        "chunk_size": chunk_size,
        "overlap_percentage": overlap_percentage,
        "document_chunks": [],
        "chunk_metadata": [],
        "current_chunk_index": 0,
        "extracted_nodes": [],
        "extracted_edges": [],
        "raw_extractions": [],
        "processed_nodes": [],
        "processed_edges": [],
        "processing_complete": False,
        "deduplication_complete": False,
        "error_message": None,
        "progress_percentage": 0
    }
    
    # Create and execute workflow
    workflow = create_data_extraction_graph()
    compiled_workflow = workflow.compile()
    
    try:
        final_state = compiled_workflow.invoke(initial_state)
        return {
            "success": True,
            "nodes": final_state["processed_nodes"],
            "edges": final_state["processed_edges"],
            "nodes_count": len(final_state["processed_nodes"]),
            "relationships_count": len(final_state["processed_edges"]),
            "processing_complete": final_state["processing_complete"],
            "error_message": final_state["error_message"]
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": str(e),
            "nodes": [],
            "edges": [],
            "processing_complete": False
        }

# Import statements at the top of the file
import os
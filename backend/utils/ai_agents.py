from typing import Dict, Any, List, TypedDict
import json
from anthropic import Anthropic
from config import get_settings
import logging

settings = get_settings()
client = Anthropic(api_key=settings.anthropic_api_key)

logger = logging.getLogger(__name__)

# State definitions for LangGraph-like processing
class OntologyCreationState(TypedDict):
    document_text: str
    document_id: str
    user_id: str
    extracted_entities: List[Dict[str, Any]]
    ontology_triples: List[Dict[str, Any]]
    ontology_name: str
    ontology_description: str
    status: str
    error_message: str

class DataExtractionState(TypedDict):
    document_text: str
    document_id: str
    user_id: str
    ontology_triples: List[Dict[str, Any]]
    extracted_nodes: List[Dict[str, Any]]
    extracted_relationships: List[Dict[str, Any]]
    chunk_metadata: Dict[str, Any]
    status: str
    error_message: str

class OntologyCreationAgent:
    """Agent for creating ontologies from document content"""
    
    ENTITY_EXTRACTION_PROMPT = """
    Analyze the following document text and extract key entities that would be useful for creating a knowledge graph ontology.

    Document Text:
    {document_text}

    Extract entities following these guidelines:
    1. Identify concrete nouns, proper nouns, and important concepts
    2. Group similar entities under common types
    3. Focus on entities that are likely to have relationships with other entities
    4. Provide variations of each entity type (synonyms, alternate forms)

    Return a JSON array of entities in this format:
    [
        {
            "entity_type": "Person",
            "type_variations": ["Individual", "Employee", "Researcher"],
            "primitive_type": "string"
        },
        {
            "entity_type": "Organization", 
            "type_variations": ["Company", "Institution", "Corporation"],
            "primitive_type": "string"
        }
    ]

    Focus on quality over quantity - extract 5-15 meaningful entity types.
    """

    ONTOLOGY_CREATION_PROMPT = """
    Based on the extracted entities, create an ontology of meaningful relationships between them.

    Extracted Entities:
    {entities}

    Document Context:
    {document_text}

    Create relationship triples that represent how these entities relate to each other in the document context.

    Return a JSON array of ontology triples in this format:
    [
        {
            "subject": {
                "entity_type": "Person",
                "type_variations": ["Individual", "Employee"],
                "primitive_type": "string"
            },
            "relationship": {
                "relationship_type": "works_for",
                "type_variations": ["is_employed_by", "employed_at"]
            },
            "object": {
                "entity_type": "Organization",
                "type_variations": ["Company", "Employer"],
                "primitive_type": "string"
            }
        }
    ]

    Create 3-10 meaningful relationship triples that capture the key relationships in the document.
    """

    def extract_entities(self, state: OntologyCreationState) -> OntologyCreationState:
        """Extract entities from document text"""
        try:
            prompt = self.ENTITY_EXTRACTION_PROMPT.format(
                document_text=state["document_text"][:8000]  # Limit for token constraints
            )
            
            response = client.messages.create(
                model=settings.llm_model,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse JSON response
            entities_text = response.content[0].text
            entities = json.loads(entities_text)
            
            state["extracted_entities"] = entities
            state["status"] = "entities_extracted"
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            state["status"] = "error"
            state["error_message"] = f"Entity extraction failed: {str(e)}"
        
        return state

    def create_ontology_triples(self, state: OntologyCreationState) -> OntologyCreationState:
        """Create ontology triples from extracted entities"""
        try:
            prompt = self.ONTOLOGY_CREATION_PROMPT.format(
                entities=json.dumps(state["extracted_entities"], indent=2),
                document_text=state["document_text"][:4000]  # Smaller context for this step
            )
            
            response = client.messages.create(
                model=settings.llm_model,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse JSON response
            triples_text = response.content[0].text
            triples = json.loads(triples_text)
            
            state["ontology_triples"] = triples
            state["status"] = "ontology_created"
            
        except Exception as e:
            logger.error(f"Ontology creation failed: {str(e)}")
            state["status"] = "error"
            state["error_message"] = f"Ontology creation failed: {str(e)}"
        
        return state

    def process(self, document_text: str, document_id: str, user_id: str) -> OntologyCreationState:
        """Main processing pipeline"""
        state = OntologyCreationState(
            document_text=document_text,
            document_id=document_id,
            user_id=user_id,
            extracted_entities=[],
            ontology_triples=[],
            ontology_name=f"Ontology for document {document_id}",
            ontology_description="Auto-generated ontology from document content",
            status="starting",
            error_message=""
        )
        
        # Step 1: Extract entities
        state = self.extract_entities(state)
        if state["status"] == "error":
            return state
        
        # Step 2: Create ontology triples
        state = self.create_ontology_triples(state)
        
        return state

class DataExtractionAgent:
    """Agent for extracting structured data using ontology"""
    
    DATA_EXTRACTION_PROMPT = """
    Extract structured data from the following text chunk using the provided ontology.

    Text Chunk:
    {text_chunk}

    Ontology Triples:
    {ontology_triples}

    Instructions:
    1. Find instances of the entities defined in the ontology within the text
    2. Extract relationships between these entities as specified in the ontology
    3. Assign unique IDs to each extracted entity instance
    4. Include source location information (character positions)

    Return JSON in this format:
    {
        "nodes": [
            {
                "id": "person_1",
                "type": "Person",
                "properties": {
                    "name": "John Smith",
                    "extracted_text": "John Smith"
                },
                "source_location": "char_100_110"
            }
        ],
        "relationships": [
            {
                "id": "rel_1",
                "type": "works_for",
                "source_id": "person_1",
                "target_id": "org_1",
                "properties": {},
                "source_location": "char_100_150"
            }
        ]
    }

    Only extract entities and relationships that are explicitly mentioned or clearly implied in the text.
    """

    def extract_from_chunk(self, state: DataExtractionState) -> DataExtractionState:
        """Extract data from a single text chunk"""
        try:
            prompt = self.DATA_EXTRACTION_PROMPT.format(
                text_chunk=state["document_text"],
                ontology_triples=json.dumps(state["ontology_triples"], indent=2)
            )
            
            response = client.messages.create(
                model=settings.llm_model,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse JSON response
            extraction_text = response.content[0].text
            extraction_result = json.loads(extraction_text)
            
            state["extracted_nodes"] = extraction_result.get("nodes", [])
            state["extracted_relationships"] = extraction_result.get("relationships", [])
            state["status"] = "extraction_completed"
            
        except Exception as e:
            logger.error(f"Data extraction failed: {str(e)}")
            state["status"] = "error"
            state["error_message"] = f"Data extraction failed: {str(e)}"
        
        return state

    def process(self, document_text: str, ontology_triples: List[Dict], document_id: str, user_id: str) -> DataExtractionState:
        """Main processing pipeline"""
        state = DataExtractionState(
            document_text=document_text,
            document_id=document_id,
            user_id=user_id,
            ontology_triples=ontology_triples,
            extracted_nodes=[],
            extracted_relationships=[],
            chunk_metadata={},
            status="starting",
            error_message=""
        )
        
        # Extract data from chunk
        state = self.extract_from_chunk(state)
        
        return state

# Factory functions for easy access
def create_ontology_from_document(document_text: str, document_id: str, user_id: str) -> OntologyCreationState:
    """Create ontology from document using AI agent"""
    agent = OntologyCreationAgent()
    return agent.process(document_text, document_id, user_id)

def extract_data_with_ontology(document_text: str, ontology_triples: List[Dict], document_id: str, user_id: str) -> DataExtractionState:
    """Extract structured data using ontology"""
    agent = DataExtractionAgent()
    return agent.process(document_text, ontology_triples, document_id, user_id)
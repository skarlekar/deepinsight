from typing import Dict, Any, List, TypedDict
import json
import time
import asyncio
from anthropic import Anthropic
from config import get_settings
import logging

settings = get_settings()

logger = logging.getLogger(__name__)

def retry_anthropic_call(func, max_retries=3, base_delay=1):
    """Retry Anthropic API calls with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            error_str = str(e)
            if "overloaded" in error_str.lower() or "429" in error_str or "529" in error_str:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"[RETRY] API overloaded, waiting {delay}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(delay)
                    continue
                else:
                    print(f"[RETRY] Max retries reached, failing with: {error_str}")
                    raise
            else:
                # Non-retryable error, fail immediately
                raise

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

    {additional_instructions_section}

    Return a JSON array of entities in this format:
    [
        {{
            "entity_type": "Person",
            "type_variations": ["Individual", "Employee", "Researcher"],
            "primitive_type": "string"
        }},
        {{
            "entity_type": "Organization", 
            "type_variations": ["Company", "Institution", "Corporation"],
            "primitive_type": "string"
        }}
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

    {additional_instructions_section}

    Return a JSON array of ontology triples in this format:
    [
        {{
            "subject": {{
                "entity_type": "Person",
                "type_variations": ["Individual", "Employee"],
                "primitive_type": "string"
            }},
            "relationship": {{
                "relationship_type": "works_for",
                "type_variations": ["is_employed_by", "employed_at"]
            }},
            "object": {{
                "entity_type": "Organization",
                "type_variations": ["Company", "Employer"],
                "primitive_type": "string"
            }}
        }}
    ]

    Create 3-10 meaningful relationship triples that capture the key relationships in the document.
    """

    def extract_entities(self, state: OntologyCreationState, additional_instructions: str = None) -> OntologyCreationState:
        """Extract entities from document text"""
        try:
            # Prepare additional instructions section
            additional_instructions_section = ""
            if additional_instructions:
                additional_instructions_section = f"Additional User Instructions:\n{additional_instructions}\n"
            
            prompt = self.ENTITY_EXTRACTION_PROMPT.format(
                document_text=state["document_text"][:8000],  # Limit for token constraints
                additional_instructions_section=additional_instructions_section
            )
            
            # Log the prompt for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[ONTOLOGY] Entity extraction prompt (first 500 chars):\n{prompt[:500]}...")
            if additional_instructions:
                logger.info(f"[ONTOLOGY] Additional instructions in entity extraction: {additional_instructions}")
            
            client = Anthropic(api_key=settings.anthropic_api_key)
            response = client.messages.create(
                model=settings.llm_model,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            # Parse JSON response
            entities_text = response.content[0].text.strip()
            
            # Extract JSON from response if it's wrapped in markdown or other text
            if "```json" in entities_text:
                json_start = entities_text.find("```json") + 7
                json_end = entities_text.find("```", json_start)
                entities_text = entities_text[json_start:json_end].strip()
            elif "```" in entities_text:
                json_start = entities_text.find("```") + 3
                json_end = entities_text.find("```", json_start)
                entities_text = entities_text[json_start:json_end].strip()
            else:
                # Find JSON array in the text - look for the first complete JSON array
                json_start = entities_text.find("[")
                if json_start != -1:
                    # Find the matching closing bracket by counting brackets
                    bracket_count = 0
                    json_end = json_start
                    for i, char in enumerate(entities_text[json_start:]):
                        if char == '[':
                            bracket_count += 1
                        elif char == ']':
                            bracket_count -= 1
                            if bracket_count == 0:
                                json_end = json_start + i + 1
                                break
                    
                    if json_end > json_start:
                        entities_text = entities_text[json_start:json_end]
            
            entities = json.loads(entities_text)
            
            state["extracted_entities"] = entities
            state["status"] = "entities_extracted"
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            state["status"] = "error"
            state["error_message"] = f"Entity extraction failed: {str(e)}"
        
        return state

    def create_ontology_triples(self, state: OntologyCreationState, additional_instructions: str = None) -> OntologyCreationState:
        """Create ontology triples from extracted entities"""
        try:
            # Prepare additional instructions section
            additional_instructions_section = ""
            if additional_instructions:
                additional_instructions_section = f"Additional User Instructions:\n{additional_instructions}\n"
            
            prompt = self.ONTOLOGY_CREATION_PROMPT.format(
                entities=json.dumps(state["extracted_entities"], indent=2),
                document_text=state["document_text"][:4000],  # Smaller context for this step
                additional_instructions_section=additional_instructions_section
            )
            
            # Log the prompt for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[ONTOLOGY] Triple creation prompt (first 500 chars):\n{prompt[:500]}...")
            if additional_instructions:
                logger.info(f"[ONTOLOGY] Additional instructions in triple creation: {additional_instructions}")
            
            client = Anthropic(api_key=settings.anthropic_api_key)
            response = client.messages.create(
                model=settings.llm_model,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse JSON response
            triples_text = response.content[0].text.strip()
            
            # Extract JSON from response if it's wrapped in markdown or other text
            if "```json" in triples_text:
                json_start = triples_text.find("```json") + 7
                json_end = triples_text.find("```", json_start)
                triples_text = triples_text[json_start:json_end].strip()
            elif "```" in triples_text:
                json_start = triples_text.find("```") + 3
                json_end = triples_text.find("```", json_start)
                triples_text = triples_text[json_start:json_end].strip()
            else:
                # Find JSON array in the text - look for the first complete JSON array
                json_start = triples_text.find("[")
                if json_start != -1:
                    # Find the matching closing bracket by counting brackets
                    bracket_count = 0
                    json_end = json_start
                    for i, char in enumerate(triples_text[json_start:]):
                        if char == '[':
                            bracket_count += 1
                        elif char == ']':
                            bracket_count -= 1
                            if bracket_count == 0:
                                json_end = json_start + i + 1
                                break
                    
                    if json_end > json_start:
                        triples_text = triples_text[json_start:json_end]
            
            triples = json.loads(triples_text)
            
            state["ontology_triples"] = triples
            state["status"] = "ontology_created"
            
        except Exception as e:
            logger.error(f"Ontology creation failed: {str(e)}")
            state["status"] = "error"
            state["error_message"] = f"Ontology creation failed: {str(e)}"
        
        return state

    def process_chunked_ontology(self, document_text: str, document_id: str, user_id: str, 
                                chunk_size: int = 6000, overlap_percentage: int = 20,
                                db_session=None, ontology_id: str = None, 
                                additional_instructions: str = None) -> OntologyCreationState:
        """Chunked ontology generation for large documents"""
        from utils.file_processor import chunk_text
        
        state = OntologyCreationState(
            document_text=document_text,
            document_id=document_id,
            user_id=user_id,
            extracted_entities=[],
            ontology_triples=[],
            ontology_name=f"Ontology for document {document_id}",
            ontology_description="Auto-generated chunked ontology from document content",
            status="starting",
            error_message=""
        )
        
        try:
            # Step 1: Chunk the document
            chunks = chunk_text(document_text, chunk_size, overlap_percentage)
            print(f"[ONTOLOGY] Processing {len(chunks)} chunks for ontology generation")
            
            all_entities = []
            
            # Step 2: Extract entities from each chunk
            for i, chunk in enumerate(chunks):
                print(f"[ONTOLOGY] Processing chunk {i+1}/{len(chunks)}")
                
                chunk_state = OntologyCreationState(
                    document_text=chunk["text"],
                    document_id=document_id,
                    user_id=user_id,
                    extracted_entities=[],
                    ontology_triples=[],
                    ontology_name=state["ontology_name"],
                    ontology_description=state["ontology_description"],
                    status="starting",
                    error_message=""
                )
                
                # Extract entities from this chunk
                chunk_state = self.extract_entities(chunk_state, additional_instructions)
                
                # Update chunk progress in database if available
                if db_session and ontology_id:
                    try:
                        from database import Ontology
                        ontology = db_session.query(Ontology).filter(Ontology.id == ontology_id).first()
                        if ontology and ontology.ontology_metadata:
                            metadata = ontology.ontology_metadata.copy()
                            if "chunk_progress" in metadata and i < len(metadata["chunk_progress"]):
                                if chunk_state["status"] == "error":
                                    metadata["chunk_progress"][i] = {"status": "error"}
                                    print(f"[ONTOLOGY] Error in chunk {i+1}: {chunk_state['error_message']}")
                                else:
                                    metadata["chunk_progress"][i] = {"status": "completed"}
                                    print(f"[ONTOLOGY] Extracted {len(chunk_state['extracted_entities'])} entity types from chunk {i+1}")
                                
                                metadata["processed_chunks"] = i + 1
                                ontology.ontology_metadata = metadata
                                db_session.commit()
                    except Exception as e:
                        print(f"[ONTOLOGY] Warning: Could not update chunk progress: {str(e)}")
                
                if chunk_state["status"] == "error":
                    continue
                
                # Collect all entities
                all_entities.extend(chunk_state["extracted_entities"])
            
            # Step 3: Deduplicate entities
            unique_entities = self._deduplicate_entities(all_entities)
            print(f"[ONTOLOGY] Deduplicated to {len(unique_entities)} unique entity types")
            
            state["extracted_entities"] = unique_entities
            state["status"] = "entities_extracted"
            
            # Step 4: Create ontology triples from unique entities
            state = self.create_ontology_triples(state, additional_instructions)
            
            return state
            
        except Exception as e:
            logger.error(f"Chunked ontology creation failed: {str(e)}")
            state["status"] = "error"
            state["error_message"] = f"Chunked ontology creation failed: {str(e)}"
            return state

    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate entities by entity_type"""
        unique_entities = {}
        
        for entity in entities:
            entity_type = entity.get("entity_type")
            if entity_type not in unique_entities:
                unique_entities[entity_type] = entity
            else:
                # Merge type_variations from duplicate entities
                existing_variations = set(unique_entities[entity_type].get("type_variations", []))
                new_variations = set(entity.get("type_variations", []))
                merged_variations = list(existing_variations.union(new_variations))
                unique_entities[entity_type]["type_variations"] = merged_variations
        
        return list(unique_entities.values())

    def process(self, document_text: str, document_id: str, user_id: str, additional_instructions: str = None) -> OntologyCreationState:
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
        state = self.extract_entities(state, additional_instructions)
        if state["status"] == "error":
            return state
        
        # Step 2: Create ontology triples
        state = self.create_ontology_triples(state, additional_instructions)
        
        return state

class DataExtractionAgent:
    """Agent for extracting structured data using ontology"""
    

    DATA_EXTRACTION_PROMPT_ENHANCED = """
    Extract structured data from the following text chunk using the provided ontology.

    Text Chunk:
    {text_chunk}

    Ontology Triples:
    {ontology_triples}

    {additional_instructions_section}

    Instructions:
    1. Find instances of the entities defined in the ontology within the text
    2. Extract relationships between these entities as specified in the ontology
    3. Assign unique IDs to each extracted entity instance (use simple sequential IDs like "person_1", "airport_1")
    4. Include source location information (character positions)
    5. **MANDATORY: Every node MUST have a 'name' property for entity deduplication**
       - For Airport entities: name must be the airport code (e.g., "IST", "BOM", "IAD")
       - For Person entities: name must be the full person name (e.g., "John Smith")
       - For Organization/Company entities: name must be the organization name
       - For Hotel entities: name must be the hotel name
       - For Location entities: name must be the location/address
       - The name property will be used to deduplicate identical entities across document chunks

    Return JSON with GUARANTEED name property for every node:
    {{
        "nodes": [
            {{
                "id": "airport_1",
                "type": "Airport",
                "properties": {{
                    "name": "IST",
                    "code": "IST",
                    "extracted_text": "IST"
                }},
                "source_location": "char_100_103"
            }},
            {{
                "id": "person_1", 
                "type": "Person",
                "properties": {{
                    "name": "John Smith",
                    "extracted_text": "John Smith"
                }},
                "source_location": "char_200_210"
            }}
        ],
        "relationships": [
            {{
                "id": "rel_1",
                "type": "works_for",
                "source_id": "person_1",
                "target_id": "org_1",
                "properties": {{}},
                "source_location": "char_100_150"
            }}
        ]
    }}

    CRITICAL: Every entity node must have a 'name' property - this is mandatory for deduplication.
    Only extract entities and relationships that are explicitly mentioned or clearly implied in the text.
    """

    def extract_from_chunk(self, state: DataExtractionState, additional_instructions: str = None) -> DataExtractionState:
        """Extract data from a single text chunk"""
        try:
            # Prepare additional instructions section
            additional_instructions_section = ""
            if additional_instructions:
                additional_instructions_section = f"Additional User Instructions:\n{additional_instructions}\n"
                print(f"[EXTRACTION] Using additional instructions in prompt: {additional_instructions[:100]}...")
            else:
                print(f"[EXTRACTION] No additional instructions provided for extraction")
            
            # Use enhanced prompt with mandatory name property requirements
            prompt = self.DATA_EXTRACTION_PROMPT_ENHANCED.format(
                text_chunk=state["document_text"],
                ontology_triples=json.dumps(state["ontology_triples"], indent=2),
                additional_instructions_section=additional_instructions_section
            )
            
            # Log the full prompt for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[EXTRACTION] Full prompt being sent to LLM:\n{prompt[:500]}...")
            if additional_instructions:
                logger.info(f"[EXTRACTION] Additional instructions in prompt: {additional_instructions}")
            
            from config import get_settings
            settings = get_settings()
            client = Anthropic(api_key=settings.anthropic_api_key)
            
            def make_api_call():
                return client.messages.create(
                    model=settings.llm_model,
                    max_tokens=settings.llm_max_tokens,
                    temperature=settings.llm_temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
            
            response = retry_anthropic_call(make_api_call, max_retries=3, base_delay=2)
            
            # Parse JSON response
            extraction_text = response.content[0].text.strip()
            
            # Extract JSON from response if it's wrapped in markdown or other text
            if "```json" in extraction_text:
                json_start = extraction_text.find("```json") + 7
                json_end = extraction_text.find("```", json_start)
                extraction_text = extraction_text[json_start:json_end].strip()
            elif "```" in extraction_text:
                json_start = extraction_text.find("```") + 3
                json_end = extraction_text.find("```", json_start)
                extraction_text = extraction_text[json_start:json_end].strip()
            
            # Find JSON object in the text
            json_start = extraction_text.find("{")
            json_end = extraction_text.rfind("}") + 1
            if json_start != -1 and json_end != 0:
                extraction_text = extraction_text[json_start:json_end]
            
            extraction_result = json.loads(extraction_text)
            
            state["extracted_nodes"] = extraction_result.get("nodes", [])
            state["extracted_relationships"] = extraction_result.get("relationships", [])
            state["status"] = "extraction_completed"
            
        except Exception as e:
            logger.error(f"Data extraction failed: {str(e)}")
            state["status"] = "error"
            state["error_message"] = f"Data extraction failed: {str(e)}"
        
        return state

    def process(self, document_text: str, ontology_triples: List[Dict], document_id: str, user_id: str, additional_instructions: str = None) -> DataExtractionState:
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
        state = self.extract_from_chunk(state, additional_instructions)
        
        return state

# Factory functions for easy access
def create_ontology_from_document(document_text: str, document_id: str, user_id: str) -> OntologyCreationState:
    """Create ontology from document using AI agent"""
    from config import get_settings
    settings = get_settings()
    
    agent = OntologyCreationAgent()
    
    # Use chunked processing for large documents (>8K chars)
    if len(document_text) > 8000:
        print(f"[ONTOLOGY] Using chunked processing for large document ({len(document_text)} chars)")
        return agent.process_chunked_ontology(document_text, document_id, user_id)
    else:
        print(f"[ONTOLOGY] Using standard processing for document ({len(document_text)} chars)")
        return agent.process(document_text, document_id, user_id)

def create_chunked_ontology_from_document(document_text: str, document_id: str, user_id: str, 
                                        chunk_size: int = 6000, overlap_percentage: int = 20) -> OntologyCreationState:
    """Create ontology from document using chunked processing (for testing/manual use)"""
    agent = OntologyCreationAgent()
    return agent.process_chunked_ontology(document_text, document_id, user_id, chunk_size, overlap_percentage)

def extract_data_with_ontology(document_text: str, ontology_triples: List[Dict], document_id: str, user_id: str, additional_instructions: str = None) -> DataExtractionState:
    """Extract structured data using ontology"""
    agent = DataExtractionAgent()
    return agent.process(document_text, ontology_triples, document_id, user_id, additional_instructions)
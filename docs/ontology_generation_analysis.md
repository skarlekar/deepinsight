# DeepInsight Ontology Generation & Document Chunking Analysis

**Report Date:** August 31, 2025  
**Analyzed Components:** Ontology Creation, Document Chunking, Data Extraction Pipeline  
**Focus:** Chunking strategy, deduplication mechanisms, and processing workflow  

---

## Executive Summary

After comprehensive code analysis, **the ontology generation process does NOT use document chunking**. The ontology is created from the complete document text as a single unit. However, **the data extraction process DOES use chunking** with sophisticated deduplication mechanisms to handle entity overlaps across chunks.

This creates a fundamental architectural difference between ontology creation (whole document) and data extraction (chunked document) that affects the system's scalability and consistency.

---

## Detailed Analysis

### 1. Ontology Generation Process

#### 1.1 Current Implementation
**Location:** `backend/ontologies/routes.py` and `backend/utils/ai_agents.py`

```python
# Ontology creation uses the COMPLETE document text
def process_ontology_creation(ontology_id: str, document_text: str, user_id: str, db: Session):
    # Process with AI agent - ENTIRE document at once
    result = create_ontology_from_document(document_text, ontology.document_id, user_id)
```

#### 1.2 Processing Steps
1. **Document Upload** → Text extracted as single unit
2. **Entity Extraction** → AI analyzes entire document (truncated to 8000 chars for token limits)
3. **Ontology Creation** → AI creates triples from all extracted entities
4. **Storage** → Complete ontology stored as JSON

#### 1.3 Key Characteristics
- ✅ **No Chunking:** Processes entire document as one piece
- ⚠️ **Token Limitations:** Truncates to 8000 characters for Claude API limits
- ✅ **Consistency:** Single AI pass ensures coherent entity relationships
- ❌ **Scalability:** Cannot handle very large documents effectively

### 2. Document Chunking Implementation

#### 2.1 Chunking Strategy
**Location:** `backend/utils/file_processor.py`

```python
def chunk_text(text: str, chunk_size: int = 1000, overlap_percentage: int = 10) -> List[Dict[str, Any]]:
    """Split text into overlapping chunks"""
    overlap_size = int(chunk_size * overlap_percentage / 100)
    # Creates overlapping chunks with configurable size and overlap
```

#### 2.2 Chunking Parameters
- **Default Chunk Size:** 1000 characters
- **Default Overlap:** 10% (100 characters)
- **Overlap Purpose:** Preserve context across chunk boundaries
- **Chunk Metadata:** Includes start/end positions, size, and chunk ID

#### 2.3 Usage Context
**Chunking is ONLY used during data extraction, NOT ontology creation**

### 3. Data Extraction Process (Uses Chunking)

#### 3.1 Extraction Pipeline
**Location:** `backend/extractions/routes.py`

```python
# 1. Document is chunked
chunks = chunk_text(document_text, chunk_size, overlap_percentage)

# 2. Each chunk processed separately
for i, chunk in enumerate(chunks):
    result = extract_data_with_ontology(
        chunk["text"],  # Individual chunk
        ontology_triples,
        extraction.document_id,
        user_id
    )
```

#### 3.2 Two Processing Modes

##### Legacy Mode (Original)
- **Entity IDs:** Prefixed with chunk number (`chunk_0_person_1`)
- **Deduplication:** Basic name-based deduplication after processing
- **Issues:** Duplicate entities across chunks (like Turkish Airlines case)

##### Enhanced Mode (New)
- **Entity Registry:** GUID-based deduplication with name normalization
- **Relationship Resolver:** Cross-chunk relationship mapping
- **Deduplication:** Real-time during processing with entity type + normalized name

### 4. Deduplication Mechanisms

#### 4.1 Legacy Deduplication
```python
# Simple deduplication after all chunks processed
unique_nodes = {}
for node in all_nodes:
    node_key = f"{node['type']}:{node.get('properties', {}).get('name', node['id'])}"
    if node_key not in unique_nodes:
        unique_nodes[node_key] = node
```

**Limitations:**
- No cross-chunk relationship integrity
- Case-sensitive name matching
- Chunk-prefixed IDs create artificial duplicates

#### 4.2 Enhanced Deduplication
```python
class EntityRegistry:
    def register_entity(self, entity: ExtractedEntity) -> str:
        # Normalize name for consistent deduplication
        normalized_name = self._normalize_name(entity.name)
        entity_key = (entity.entity_type, normalized_name)
        
        # Return existing GUID or create new one
        if entity_key in self.entities:
            return self.entities[entity_key]  # Deduplicated!
```

**Advantages:**
- Real-time deduplication during processing
- Case-insensitive name normalization
- Cross-chunk relationship integrity maintained
- GUID-based entity identification

---

## Critical Findings

### 1. Architectural Inconsistency

| Process | Chunking Strategy | Implications |
|---------|------------------|--------------|
| **Ontology Creation** | No chunking (full document) | Limited to ~8K characters, consistent entity view |
| **Data Extraction** | Chunking with overlap | Scalable for large documents, potential entity duplication |

### 2. Token Limitations Impact

#### Ontology Creation
- **Limit:** 8000 characters (Claude API constraint)
- **Truncation:** Large documents lose content in ontology
- **Risk:** Incomplete ontologies for comprehensive documents

#### Data Extraction
- **Advantage:** No size limits due to chunking
- **Challenge:** Entity consistency across chunks
- **Solution:** Enhanced deduplication pipeline

### 3. Deduplication Evolution

The system has evolved from basic post-processing deduplication to sophisticated real-time deduplication:

#### Before (Legacy)
```json
{
  "nodes": [
    {"id": "chunk_0_airline_1", "properties": {"name": "TURKISH AIRLINES"}},
    {"id": "chunk_1_airline_2", "properties": {"name": "Turkish Airlines"}}
  ]
}
```

#### After (Enhanced)
```json
{
  "nodes": [
    {"id": "a1b2c3-uuid", "properties": {"name": "Turkish Airlines"}}
  ],
  "metadata": {
    "entity_stats": {
      "total_extracted": 2,
      "unique_entities": 1,
      "duplicates_removed": 1
    }
  }
}
```

---

## Recommendations

### 1. Immediate Actions

#### 1.1 Ontology Generation Enhancement
**Problem:** 8K character limitation affects large documents

**Solution:** Implement chunked ontology generation
```python
def create_chunked_ontology(document_text: str, chunk_size: int = 6000):
    chunks = chunk_text(document_text, chunk_size, overlap_percentage=20)
    
    # Extract entities from each chunk
    all_entities = []
    for chunk in chunks:
        chunk_entities = extract_entities_from_chunk(chunk["text"])
        all_entities.extend(chunk_entities)
    
    # Deduplicate and create relationships
    unique_entities = deduplicate_entities(all_entities)
    ontology_triples = create_relationships(unique_entities, document_text)
    
    return ontology_triples
```

#### 1.2 Consistency Alignment
**Problem:** Different processing strategies for ontology vs extraction

**Solution:** Align both processes to use similar chunking and deduplication strategies

### 2. Long-term Improvements

#### 2.1 Adaptive Chunking
- **Context-aware chunking:** Break at sentence/paragraph boundaries
- **Semantic chunking:** Use NLP to identify logical sections
- **Dynamic sizing:** Adjust chunk size based on document structure

#### 2.2 Progressive Ontology Building
- **Incremental creation:** Build ontology progressively from chunks
- **Relationship validation:** Cross-validate relationships across chunks
- **Iterative refinement:** Allow ontology updates as more chunks are processed

#### 2.3 Performance Optimization
- **Parallel processing:** Process chunks concurrently
- **Caching:** Cache entity recognition results
- **Streaming:** Process large documents in streams

---

## Implementation Priority

### High Priority
1. **Fix Turkish Airlines duplicate issue** ✅ (Already implemented)
2. **Enable enhanced extraction by default** (Change feature flags)
3. **Implement chunked ontology generation** (Address 8K limit)

### Medium Priority
1. **Context-aware chunking** (Improve chunk boundaries)
2. **Progressive ontology building** (Handle very large documents)
3. **Performance monitoring** (Track deduplication effectiveness)

### Low Priority
1. **Semantic chunking** (Advanced NLP-based chunking)
2. **Adaptive chunk sizing** (Dynamic optimization)
3. **Real-time ontology updates** (Live refinement)

---

## Conclusion

The DeepInsight system uses a **hybrid approach** where ontology generation processes entire documents while data extraction uses chunking with sophisticated deduplication. The recent enhanced extraction pipeline successfully addresses the entity duplication issues (like Turkish Airlines appearing twice) through GUID-based entity management and name normalization.

The main architectural improvement needed is implementing chunked ontology generation to remove the 8K character limitation and ensure consistency between the two processing pipelines.

**Current Status:** Enhanced extraction pipeline working correctly with proper deduplication ✅  
**Next Phase:** Implement chunked ontology generation for scalability 🔄
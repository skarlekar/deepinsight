# DeepInsight CSV Export Format Specifications
# Complete Neo4j and Neptune CSV export implementations

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import csv
import io
from datetime import datetime
import re
import json

# ============================================================================
# Data Classes for Export
# ============================================================================

class GraphNode:
    """Represents a graph node for export"""
    
    def __init__(self, id: str, type: str, properties: Dict[str, Any], source_location: Optional[str] = None):
        self.id = self._sanitize_id(id)
        self.type = type
        self.properties = properties or {}
        self.source_location = source_location
    
    @staticmethod
    def _sanitize_id(node_id: str) -> str:
        """Sanitize node ID for database compatibility"""
        # Remove special characters and spaces, replace with underscores
        sanitized = re.sub(r'[^\w\-]', '_', str(node_id))
        # Ensure ID starts with letter or underscore
        if sanitized and sanitized[0].isdigit():
            sanitized = f"node_{sanitized}"
        return sanitized or "unknown_node"

class GraphEdge:
    """Represents a graph edge for export"""
    
    def __init__(self, id: str, type: str, source_id: str, target_id: str, 
                 properties: Dict[str, Any] = None, source_location: Optional[str] = None):
        self.id = self._sanitize_id(id)
        self.type = type
        self.source_id = GraphNode._sanitize_id(source_id)
        self.target_id = GraphNode._sanitize_id(target_id)
        self.properties = properties or {}
        self.source_location = source_location
    
    @staticmethod
    def _sanitize_id(edge_id: str) -> str:
        """Sanitize edge ID for database compatibility"""
        sanitized = re.sub(r'[^\w\-]', '_', str(edge_id))
        if sanitized and sanitized[0].isdigit():
            sanitized = f"edge_{sanitized}"
        return sanitized or "unknown_edge"

# ============================================================================
# Base Export Class
# ============================================================================

class BaseGraphExporter(ABC):
    """Abstract base class for graph data exporters"""
    
    @abstractmethod
    def export_nodes(self, nodes: List[GraphNode], output_path: Path) -> str:
        """Export nodes to CSV format"""
        pass
    
    @abstractmethod
    def export_edges(self, edges: List[GraphEdge], output_path: Path) -> str:
        """Export edges to CSV format"""
        pass
    
    def export_graph(self, nodes: List[GraphNode], edges: List[GraphEdge], 
                    output_dir: Path, filename_prefix: str = "graph") -> Dict[str, str]:
        """Export complete graph to CSV files"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export nodes
        nodes_file = output_dir / f"{filename_prefix}_nodes.csv"
        nodes_path = self.export_nodes(nodes, nodes_file)
        
        # Export edges  
        edges_file = output_dir / f"{filename_prefix}_edges.csv"
        edges_path = self.export_edges(edges, edges_file)
        
        return {
            "nodes_csv": nodes_path,
            "edges_csv": edges_path
        }
    
    @staticmethod
    def _escape_csv_value(value: Any) -> str:
        """Escape value for CSV output"""
        if value is None:
            return ""
        
        str_value = str(value)
        
        # Escape double quotes by doubling them
        if '"' in str_value:
            str_value = str_value.replace('"', '""')
        
        # Quote values that contain commas, quotes, or newlines
        if ',' in str_value or '"' in str_value or '\n' in str_value or '\r' in str_value:
            str_value = f'"{str_value}"'
        
        return str_value
    
    @staticmethod
    def _serialize_properties(properties: Dict[str, Any]) -> Dict[str, str]:
        """Serialize properties to string values for CSV"""
        serialized = {}
        
        for key, value in properties.items():
            if isinstance(value, (dict, list)):
                # Serialize complex objects as JSON
                serialized[key] = json.dumps(value)
            elif isinstance(value, bool):
                # Convert boolean to string
                serialized[key] = "true" if value else "false"
            elif value is None:
                serialized[key] = ""
            else:
                serialized[key] = str(value)
        
        return serialized

# ============================================================================
# Neo4j CSV Exporter
# ============================================================================

class Neo4jExporter(BaseGraphExporter):
    """Export graph data to Neo4j CSV format"""
    
    def export_nodes(self, nodes: List[GraphNode], output_path: Path) -> str:
        """
        Export nodes to Neo4j CSV format
        
        Format: nodeId:ID,name,type,:LABEL
        Example: person1,John Doe,string,Person
        """
        if not nodes:
            # Create empty file with headers
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['nodeId:ID', ':LABEL'])
            return str(output_path)
        
        # Collect all unique property keys
        all_property_keys = set()
        for node in nodes:
            serialized_props = self._serialize_properties(node.properties)
            all_property_keys.update(serialized_props.keys())
        
        # Sort property keys for consistent output
        property_keys = sorted(all_property_keys)
        
        # Create header row
        headers = ['nodeId:ID'] + property_keys + ['source_location', ':LABEL']
        
        # Write CSV file
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for node in nodes:
                serialized_props = self._serialize_properties(node.properties)
                row = [node.id]
                
                # Add property values in same order as headers
                for prop_key in property_keys:
                    row.append(serialized_props.get(prop_key, ''))
                
                # Add source location and label
                row.append(node.source_location or '')
                row.append(node.type)
                
                writer.writerow(row)
        
        return str(output_path)
    
    def export_edges(self, edges: List[GraphEdge], output_path: Path) -> str:
        """
        Export edges to Neo4j CSV format
        
        Format: :START_ID,:END_ID,:TYPE,properties...,source_location
        Example: person1,org1,WORKS_FOR,"page 1, line 15"
        """
        if not edges:
            # Create empty file with headers
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([':START_ID', ':END_ID', ':TYPE'])
            return str(output_path)
        
        # Collect all unique property keys
        all_property_keys = set()
        for edge in edges:
            serialized_props = self._serialize_properties(edge.properties)
            all_property_keys.update(serialized_props.keys())
        
        # Sort property keys for consistent output
        property_keys = sorted(all_property_keys)
        
        # Create header row
        headers = [':START_ID', ':END_ID', ':TYPE'] + property_keys + ['source_location']
        
        # Write CSV file
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for edge in edges:
                serialized_props = self._serialize_properties(edge.properties)
                row = [edge.source_id, edge.target_id, edge.type.upper()]
                
                # Add property values in same order as headers
                for prop_key in property_keys:
                    row.append(serialized_props.get(prop_key, ''))
                
                # Add source location
                row.append(edge.source_location or '')
                
                writer.writerow(row)
        
        return str(output_path)
    
    def generate_import_script(self, nodes_csv_path: str, edges_csv_path: str) -> str:
        """Generate Neo4j import script"""
        script = f"""
// Neo4j Import Script for DeepInsight Data
// Generated on {datetime.now().isoformat()}

// Import nodes
LOAD CSV WITH HEADERS FROM 'file:///{nodes_csv_path}' AS row
CREATE (n)
SET n = row, n.nodeId = row.`nodeId:ID`
SET n:`{"{"}row.`:LABEL`{"}"}`;

// Create index on nodeId for faster lookups
CREATE INDEX nodeId_index IF NOT EXISTS FOR (n) ON (n.nodeId);

// Import relationships
LOAD CSV WITH HEADERS FROM 'file:///{edges_csv_path}' AS row
MATCH (source {{nodeId: row.`:START_ID`}})
MATCH (target {{nodeId: row.`:END_ID`}})
CALL apoc.create.relationship(source, row.`:TYPE`, row, target) YIELD rel
RETURN count(rel);

// Verify import
MATCH (n) RETURN labels(n) as Labels, count(n) as NodeCount;
MATCH ()-[r]->() RETURN type(r) as RelationshipType, count(r) as RelationshipCount;
"""
        return script.strip()

# ============================================================================
# Neptune CSV Exporter  
# ============================================================================

class NeptuneExporter(BaseGraphExporter):
    """Export graph data to AWS Neptune CSV format"""
    
    def export_nodes(self, nodes: List[GraphNode], output_path: Path) -> str:
        """
        Export nodes to Neptune CSV format
        
        Format: ~id,~label,property1,property2,...
        Example: person1,Person,John Doe,string
        """
        if not nodes:
            # Create empty file with headers
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['~id', '~label'])
            return str(output_path)
        
        # Collect all unique property keys
        all_property_keys = set()
        for node in nodes:
            serialized_props = self._serialize_properties(node.properties)
            all_property_keys.update(serialized_props.keys())
        
        # Sort property keys for consistent output
        property_keys = sorted(all_property_keys)
        
        # Create header row
        headers = ['~id', '~label'] + property_keys + ['source_location']
        
        # Write CSV file
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for node in nodes:
                serialized_props = self._serialize_properties(node.properties)
                row = [node.id, node.type]
                
                # Add property values in same order as headers
                for prop_key in property_keys:
                    row.append(serialized_props.get(prop_key, ''))
                
                # Add source location
                row.append(node.source_location or '')
                
                writer.writerow(row)
        
        return str(output_path)
    
    def export_edges(self, edges: List[GraphEdge], output_path: Path) -> str:
        """
        Export edges to Neptune CSV format
        
        Format: ~id,~from,~to,~label,property1,property2,...
        Example: rel1,person1,org1,works_for,"page 1, line 15"
        """
        if not edges:
            # Create empty file with headers
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['~id', '~from', '~to', '~label'])
            return str(output_path)
        
        # Collect all unique property keys
        all_property_keys = set()
        for edge in edges:
            serialized_props = self._serialize_properties(edge.properties)
            all_property_keys.update(serialized_props.keys())
        
        # Sort property keys for consistent output
        property_keys = sorted(all_property_keys)
        
        # Create header row
        headers = ['~id', '~from', '~to', '~label'] + property_keys + ['source_location']
        
        # Write CSV file
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for edge in edges:
                serialized_props = self._serialize_properties(edge.properties)
                row = [edge.id, edge.source_id, edge.target_id, edge.type.lower()]
                
                # Add property values in same order as headers
                for prop_key in property_keys:
                    row.append(serialized_props.get(prop_key, ''))
                
                # Add source location
                row.append(edge.source_location or '')
                
                writer.writerow(row)
        
        return str(output_path)
    
    def generate_bulk_loader_manifest(self, vertices_csv_path: str, edges_csv_path: str, 
                                    s3_bucket: str = None) -> Dict[str, Any]:
        """Generate Neptune bulk loader manifest"""
        
        base_uri = f"s3://{s3_bucket}/" if s3_bucket else "file:///"
        
        manifest = {
            "version": "v2.0",
            "allowEmptyStrings": True,
            "includeHeaders": True,
            "format": "csv",
            "loadId": f"deepinsight_load_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "sources": [
                {
                    "source": f"{base_uri}{vertices_csv_path}",
                    "format": "csv",
                    "type": "vertices",
                    "headers": True
                },
                {
                    "source": f"{base_uri}{edges_csv_path}",
                    "format": "csv", 
                    "type": "edges",
                    "headers": True
                }
            ]
        }
        
        return manifest

# ============================================================================
# Data Transformation Functions
# ============================================================================

def transform_extraction_results_to_graph_data(
    extraction_results: Dict[str, Any]
) -> Tuple[List[GraphNode], List[GraphEdge]]:
    """
    Transform LLM extraction results to graph data format
    
    Args:
        extraction_results: Dictionary containing 'nodes' and 'relationships' lists
        
    Returns:
        Tuple of (nodes, edges) ready for export
    """
    nodes = []
    edges = []
    
    # Process nodes
    for node_data in extraction_results.get('nodes', []):
        node = GraphNode(
            id=node_data.get('id', ''),
            type=node_data.get('type', 'Unknown'),
            properties=node_data.get('properties', {}),
            source_location=node_data.get('source_location')
        )
        nodes.append(node)
    
    # Process relationships/edges
    for edge_data in extraction_results.get('relationships', []):
        edge = GraphEdge(
            id=edge_data.get('id', ''),
            type=edge_data.get('type', 'RELATED'),
            source_id=edge_data.get('source_id', ''),
            target_id=edge_data.get('target_id', ''),
            properties=edge_data.get('properties', {}),
            source_location=edge_data.get('source_location')
        )
        edges.append(edge)
    
    return nodes, edges

def validate_graph_data(nodes: List[GraphNode], edges: List[GraphEdge]) -> List[str]:
    """
    Validate graph data for export
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Check for empty data
    if not nodes and not edges:
        errors.append("No nodes or edges to export")
        return errors
    
    # Collect node IDs
    node_ids = {node.id for node in nodes}
    
    # Validate nodes
    for i, node in enumerate(nodes):
        if not node.id:
            errors.append(f"Node {i} has empty ID")
        if not node.type:
            errors.append(f"Node {i} ({node.id}) has empty type")
    
    # Validate edges
    for i, edge in enumerate(edges):
        if not edge.id:
            errors.append(f"Edge {i} has empty ID")
        if not edge.type:
            errors.append(f"Edge {i} ({edge.id}) has empty type")
        if not edge.source_id:
            errors.append(f"Edge {i} ({edge.id}) has empty source_id")
        if not edge.target_id:
            errors.append(f"Edge {i} ({edge.id}) has empty target_id")
        
        # Check if referenced nodes exist
        if edge.source_id and edge.source_id not in node_ids:
            errors.append(f"Edge {i} ({edge.id}) references non-existent source node: {edge.source_id}")
        if edge.target_id and edge.target_id not in node_ids:
            errors.append(f"Edge {i} ({edge.id}) references non-existent target node: {edge.target_id}")
    
    return errors

# ============================================================================
# Export Factory
# ============================================================================

class GraphExportFactory:
    """Factory for creating graph exporters"""
    
    _exporters = {
        'neo4j': Neo4jExporter,
        'neptune': NeptuneExporter
    }
    
    @classmethod
    def create_exporter(cls, format_type: str) -> BaseGraphExporter:
        """Create exporter for specified format"""
        format_type = format_type.lower()
        
        if format_type not in cls._exporters:
            raise ValueError(f"Unsupported export format: {format_type}. "
                           f"Supported formats: {list(cls._exporters.keys())}")
        
        return cls._exporters[format_type]()
    
    @classmethod
    def export_extraction_results(cls, 
                                 extraction_results: Dict[str, Any],
                                 output_dir: Path,
                                 formats: List[str] = None,
                                 filename_prefix: str = "extraction") -> Dict[str, Dict[str, str]]:
        """
        Export extraction results to multiple formats
        
        Args:
            extraction_results: LLM extraction results
            output_dir: Output directory
            formats: List of formats to export to (default: ['neo4j', 'neptune'])
            filename_prefix: Prefix for output files
            
        Returns:
            Dictionary mapping format names to file paths
        """
        if formats is None:
            formats = ['neo4j', 'neptune']
        
        # Transform data
        nodes, edges = transform_extraction_results_to_graph_data(extraction_results)
        
        # Validate data
        validation_errors = validate_graph_data(nodes, edges)
        if validation_errors:
            raise ValueError(f"Graph data validation failed: {'; '.join(validation_errors)}")
        
        # Export to each format
        results = {}
        
        for format_type in formats:
            try:
                exporter = cls.create_exporter(format_type)
                format_output_dir = output_dir / format_type
                
                export_files = exporter.export_graph(
                    nodes=nodes,
                    edges=edges,
                    output_dir=format_output_dir,
                    filename_prefix=filename_prefix
                )
                
                results[format_type] = export_files
                
            except Exception as e:
                raise Exception(f"Export to {format_type} failed: {str(e)}")
        
        return results

# ============================================================================
# Utility Functions
# ============================================================================

def get_supported_export_formats() -> List[str]:
    """Get list of supported export formats"""
    return list(GraphExportFactory._exporters.keys())

def estimate_csv_size(nodes: List[GraphNode], edges: List[GraphEdge]) -> Dict[str, int]:
    """Estimate CSV file sizes in bytes"""
    # Rough estimation based on data
    avg_node_size = 200  # bytes per node row
    avg_edge_size = 150  # bytes per edge row
    
    return {
        "nodes_csv_bytes": len(nodes) * avg_node_size,
        "edges_csv_bytes": len(edges) * avg_edge_size,
        "total_bytes": (len(nodes) * avg_node_size) + (len(edges) * avg_edge_size)
    }

def create_export_summary(nodes: List[GraphNode], edges: List[GraphEdge]) -> Dict[str, Any]:
    """Create summary statistics of exported data"""
    # Count node types
    node_types = {}
    for node in nodes:
        node_types[node.type] = node_types.get(node.type, 0) + 1
    
    # Count edge types  
    edge_types = {}
    for edge in edges:
        edge_types[edge.type] = edge_types.get(edge.type, 0) + 1
    
    return {
        "export_timestamp": datetime.now().isoformat(),
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "node_types": node_types,
        "edge_types": edge_types,
        "has_source_locations": any(node.source_location for node in nodes) or 
                               any(edge.source_location for edge in edges)
    }
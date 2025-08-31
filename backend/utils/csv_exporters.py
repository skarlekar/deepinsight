from abc import ABC, abstractmethod
from pathlib import Path
import csv
import uuid
from typing import List, Dict, Any
from datetime import datetime, timedelta

class GraphNode:
    def __init__(self, id: str, type: str, properties: Dict[str, Any], source_location: str = None):
        self.id = id
        self.type = type
        self.properties = properties
        self.source_location = source_location

class GraphRelationship:
    def __init__(self, id: str, type: str, source_id: str, target_id: str, 
                 properties: Dict[str, Any] = None, source_location: str = None):
        self.id = id
        self.type = type
        self.source_id = source_id
        self.target_id = target_id
        self.properties = properties or {}
        self.source_location = source_location

class BaseGraphExporter(ABC):
    @abstractmethod
    def export_nodes(self, nodes: List[GraphNode], output_path: Path) -> str:
        pass
    
    @abstractmethod
    def export_relationships(self, relationships: List[GraphRelationship], output_path: Path) -> str:
        pass

class Neo4jExporter(BaseGraphExporter):
    """Export graph data in Neo4j CSV format"""
    
    def export_nodes(self, nodes: List[GraphNode], output_path: Path) -> str:
        """Export nodes in Neo4j format: nodeId:ID,name,type,:LABEL"""
        filename = f"neo4j_nodes_{uuid.uuid4().hex[:8]}.csv"
        file_path = output_path / filename
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                'nodeId:ID', 'name', 'type', 'properties', 'source_location', ':LABEL'
            ])
            
            # Write nodes
            for node in nodes:
                name = node.properties.get('name', node.id)
                properties_str = self._serialize_properties(node.properties)
                
                writer.writerow([
                    node.id,
                    name,
                    node.type,
                    properties_str,
                    node.source_location or '',
                    node.type  # Neo4j label
                ])
        
        return str(file_path)
    
    def export_relationships(self, relationships: List[GraphRelationship], output_path: Path) -> str:
        """Export relationships in Neo4j format: :START_ID,:END_ID,:TYPE,properties"""
        filename = f"neo4j_relationships_{uuid.uuid4().hex[:8]}.csv"
        file_path = output_path / filename
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                ':START_ID', ':END_ID', ':TYPE', 'properties', 'source_location'
            ])
            
            # Write relationships
            for rel in relationships:
                properties_str = self._serialize_properties(rel.properties)
                
                writer.writerow([
                    rel.source_id,
                    rel.target_id,
                    rel.type,
                    properties_str,
                    rel.source_location or ''
                ])
        
        return str(file_path)
    
    def _serialize_properties(self, properties: Dict[str, Any]) -> str:
        """Serialize properties to JSON string"""
        if not properties:
            return ''
        
        # Simple JSON serialization
        import json
        try:
            return json.dumps(properties)
        except (TypeError, ValueError):
            return str(properties)

class NeptuneExporter(BaseGraphExporter):
    """Export graph data in AWS Neptune CSV format"""
    
    def export_nodes(self, nodes: List[GraphNode], output_path: Path) -> str:
        """Export vertices in Neptune format: ~id,~label,name,type,properties"""
        filename = f"neptune_vertices_{uuid.uuid4().hex[:8]}.csv"
        file_path = output_path / filename
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                '~id', '~label', 'name:String', 'type:String', 
                'properties:String', 'source_location:String'
            ])
            
            # Write vertices
            for node in nodes:
                name = node.properties.get('name', node.id)
                properties_str = self._serialize_properties(node.properties)
                
                writer.writerow([
                    node.id,
                    node.type,
                    name,
                    node.type,
                    properties_str,
                    node.source_location or ''
                ])
        
        return str(file_path)
    
    def export_relationships(self, relationships: List[GraphRelationship], output_path: Path) -> str:
        """Export edges in Neptune format: ~id,~from,~to,~label,properties"""
        filename = f"neptune_edges_{uuid.uuid4().hex[:8]}.csv"
        file_path = output_path / filename
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                '~id', '~from', '~to', '~label', 
                'properties:String', 'source_location:String'
            ])
            
            # Write edges
            for rel in relationships:
                properties_str = self._serialize_properties(rel.properties)
                
                writer.writerow([
                    rel.id,
                    rel.source_id,
                    rel.target_id,
                    rel.type,
                    properties_str,
                    rel.source_location or ''
                ])
        
        return str(file_path)
    
    def _serialize_properties(self, properties: Dict[str, Any]) -> str:
        """Serialize properties to JSON string"""
        if not properties:
            return ''
        
        import json
        try:
            return json.dumps(properties)
        except (TypeError, ValueError):
            return str(properties)

class ExportManager:
    """Manages graph data exports"""
    
    def __init__(self, export_directory: str):
        self.export_directory = Path(export_directory)
        self.export_directory.mkdir(parents=True, exist_ok=True)
    
    def export_for_neo4j(self, nodes_data: List[Dict], relationships_data: List[Dict]) -> Dict[str, str]:
        """Export data in Neo4j format"""
        # Convert data to graph objects
        nodes = [
            GraphNode(
                id=node['id'],
                type=node['type'],
                properties=node.get('properties', {}),
                source_location=node.get('source_location')
            )
            for node in nodes_data
        ]
        
        relationships = [
            GraphRelationship(
                id=rel['id'],
                type=rel['type'],
                source_id=rel['source_id'],
                target_id=rel['target_id'],
                properties=rel.get('properties', {}),
                source_location=rel.get('source_location')
            )
            for rel in relationships_data
        ]
        
        # Export using Neo4j exporter
        exporter = Neo4jExporter()
        nodes_file = exporter.export_nodes(nodes, self.export_directory)
        relationships_file = exporter.export_relationships(relationships, self.export_directory)
        
        return {
            'nodes_csv_url': self._get_download_url(nodes_file),
            'relationships_csv_url': self._get_download_url(relationships_file)
        }
    
    def export_for_neptune(self, nodes_data: List[Dict], relationships_data: List[Dict]) -> Dict[str, str]:
        """Export data in Neptune format"""
        # Convert data to graph objects
        nodes = [
            GraphNode(
                id=node['id'],
                type=node['type'],
                properties=node.get('properties', {}),
                source_location=node.get('source_location')
            )
            for node in nodes_data
        ]
        
        relationships = [
            GraphRelationship(
                id=rel['id'],
                type=rel['type'],
                source_id=rel['source_id'],
                target_id=rel['target_id'],
                properties=rel.get('properties', {}),
                source_location=rel.get('source_location')
            )
            for rel in relationships_data
        ]
        
        # Export using Neptune exporter
        exporter = NeptuneExporter()
        vertices_file = exporter.export_nodes(nodes, self.export_directory)
        edges_file = exporter.export_relationships(relationships, self.export_directory)
        
        return {
            'vertices_csv_url': self._get_download_url(vertices_file),
            'edges_csv_url': self._get_download_url(edges_file)
        }
    
    def _get_download_url(self, file_path: str) -> str:
        """Generate download URL for exported file"""
        filename = Path(file_path).name
        return f"/exports/download/{filename}"
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up old export files"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        for file_path in self.export_directory.glob("*.csv"):
            try:
                if datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff_time:
                    file_path.unlink()
            except (OSError, ValueError):
                continue  # Skip files that can't be processed

# Factory function
def get_export_manager(export_directory: str) -> ExportManager:
    """Get configured export manager instance"""
    return ExportManager(export_directory)
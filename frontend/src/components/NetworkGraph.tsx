import React, { useEffect, useRef, useState } from 'react';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import { Box, Paper, Typography, IconButton, Tooltip } from '@mui/material';
import { OpenInNew } from '@mui/icons-material';
import { ExtractionNode, ExtractionRelationship } from '../types';

interface NetworkGraphProps {
  nodes: ExtractionNode[];
  relationships: ExtractionRelationship[];
  height?: number;
}

export const NetworkGraph: React.FC<NetworkGraphProps> = ({ 
  nodes, 
  relationships, 
  height = 400 
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const [tooltipContent, setTooltipContent] = useState<string>('');
  const [tooltipPosition, setTooltipPosition] = useState<{x: number, y: number} | null>(null);


  // Transform nodes data for vis.js
  const transformNodes = (nodeList: ExtractionNode[]) => {
    return nodeList.map(node => {
      // Get display label - try multiple properties
      let label = '';
      if (node.properties?.name) {
        label = node.properties.name;
      } else if (node.properties?.extracted_text) {
        label = node.properties.extracted_text;
      } else if (node.properties?.code) {
        label = node.properties.code;
      } else if (node.properties?.value) {
        label = node.properties.value;
      } else {
        label = node.type || 'Unknown';
      }

      // Ensure label is a string and not too long
      const displayLabel = String(label).trim();
      const shortLabel = displayLabel.length > 15 ? displayLabel.substring(0, 15) + '...' : displayLabel;

      // Determine color based on node type
      const getNodeColor = (type: string): string => {
        const colors: { [key: string]: string } = {
          'Person': '#4CAF50',      // Green
          'Organization': '#2196F3', // Blue  
          'Company': '#2196F3',     // Blue
          'Location': '#FF9800',    // Orange
          'Place': '#FF9800',       // Orange
          'Airport': '#9C27B0',     // Purple
          'Airline': '#F44336',     // Red
          'Date': '#795548',        // Brown
          'Money': '#4CAF50',       // Green
          'Number': '#607D8B',      // Blue Grey
          'default': '#9E9E9E'      // Grey
        };
        return colors[type] || colors.default;
      };

      // Create comprehensive tooltip - using plain text for better compatibility
      const createTooltip = (nodeData: ExtractionNode) => {
        const parts = [];
        parts.push(`Type: ${nodeData.type}`);
        parts.push(`ID: ${nodeData.id.substring(0, 12)}...`);
        
        if (displayLabel && displayLabel !== nodeData.type) {
          parts.push(`Name: ${displayLabel}`);
        }
        
        if (nodeData.source_location) {
          parts.push(`Source: ${nodeData.source_location}`);
        }
        
        if (nodeData.properties && Object.keys(nodeData.properties).length > 0) {
          parts.push('Properties:');
          const propEntries = Object.entries(nodeData.properties).slice(0, 3);
          propEntries.forEach(([key, value]) => {
            const val = String(value).substring(0, 30);
            parts.push(`  ${key}: ${val}${val.length >= 30 ? '...' : ''}`);
          });
        }
        
        return parts.join('\n');
      };

      return {
        id: node.id,
        label: shortLabel || node.type,
        color: {
          background: getNodeColor(node.type),
          border: '#2B2B2B',
          highlight: {
            background: getNodeColor(node.type),
            border: '#000000'
          },
          hover: {
            background: getNodeColor(node.type),
            border: '#000000'
          }
        },
        title: createTooltip(node),
        shape: 'dot',
        size: 20,
        font: {
          color: '#ffffff',
          size: 12,
          face: 'Arial',
          strokeWidth: 2,
          strokeColor: '#000000'
        }
      };
    });
  };

  // Transform relationships data for vis.js  
  const transformEdges = (relationshipList: ExtractionRelationship[]) => {
    return relationshipList.map(rel => {
      // Create comprehensive tooltip for edges - using plain text for better compatibility
      const createEdgeTooltip = (relationship: ExtractionRelationship) => {
        const parts = [];
        parts.push(`Relationship: ${relationship.type}`);
        parts.push(`From: ${relationship.source_id.substring(0, 12)}...`);
        parts.push(`To: ${relationship.target_id.substring(0, 12)}...`);
        
        if (relationship.source_location) {
          parts.push(`Source: ${relationship.source_location}`);
        }
        
        if (relationship.properties && Object.keys(relationship.properties).length > 0) {
          parts.push('Properties:');
          const propEntries = Object.entries(relationship.properties).slice(0, 3);
          propEntries.forEach(([key, value]) => {
            const val = String(value).substring(0, 30);
            parts.push(`  ${key}: ${val}${val.length >= 30 ? '...' : ''}`);
          });
        }
        
        return parts.join('\n');
      };

      return {
        id: rel.id,
        from: rel.source_id,
        to: rel.target_id,
        label: rel.type,
        title: createEdgeTooltip(rel),
        color: {
          color: '#848484',
          highlight: '#2B2B2B',
          hover: '#2B2B2B'
        },
        width: 2,
        arrows: {
          to: { enabled: true, scaleFactor: 0.8, type: 'arrow' }
        },
        font: {
          size: 10,
          color: '#2B2B2B',
          strokeWidth: 1,
          strokeColor: '#ffffff'
        }
      };
    });
  };

  useEffect(() => {
    if (!containerRef.current || nodes.length === 0) return;

    // Create custom tooltip functions inside useEffect
    const createCustomTooltipLocal = (nodeData: ExtractionNode) => {
      const parts = [];
      parts.push(`Type: ${nodeData.type}`);
      parts.push(`ID: ${nodeData.id.substring(0, 12)}...`);
      
      if (nodeData.properties) {
        // Try to get a meaningful name/label
        const nameProps = ['name', 'extracted_text', 'code', 'value'];
        const nameField = nameProps.find(prop => nodeData.properties[prop]);
        if (nameField && nodeData.properties[nameField] !== nodeData.type) {
          parts.push(`Name: ${String(nodeData.properties[nameField]).substring(0, 30)}`);
        }
        
        if (nodeData.source_location) {
          parts.push(`Source: ${nodeData.source_location}`);
        }
        
        // Show properties
        parts.push('Properties:');
        Object.entries(nodeData.properties).slice(0, 3).forEach(([key, value]) => {
          const val = String(value).substring(0, 30);
          parts.push(`  ${key}: ${val}${val.length >= 30 ? '...' : ''}`);
        });
      }
      
      return parts.join('\n');
    };

    const createCustomEdgeTooltipLocal = (relationship: ExtractionRelationship) => {
      const parts = [];
      parts.push(`Relationship: ${relationship.type}`);
      parts.push(`From: ${relationship.source_id.substring(0, 12)}...`);
      parts.push(`To: ${relationship.target_id.substring(0, 12)}...`);
      
      if (relationship.source_location) {
        parts.push(`Source: ${relationship.source_location}`);
      }
      
      if (relationship.properties && Object.keys(relationship.properties).length > 0) {
        parts.push('Properties:');
        Object.entries(relationship.properties).slice(0, 3).forEach(([key, value]) => {
          const val = String(value).substring(0, 30);
          parts.push(`  ${key}: ${val}${val.length >= 30 ? '...' : ''}`);
        });
      }
      
      return parts.join('\n');
    };

    // Debug logging
    console.log('NetworkGraph - Raw nodes:', nodes);
    console.log('NetworkGraph - Raw relationships:', relationships);

    // Debug specific node properties
    if (nodes.length > 0) {
      console.log('First node properties:', nodes[0].properties);
      console.log('First node structure:', {
        id: nodes[0].id,
        type: nodes[0].type,
        properties: nodes[0].properties,
        source_location: nodes[0].source_location
      });
    }

    // Prepare data
    const transformedNodes = transformNodes(nodes);
    const transformedEdges = transformEdges(relationships);
    
    console.log('NetworkGraph - Transformed nodes:', transformedNodes);
    console.log('NetworkGraph - Transformed edges:', transformedEdges);

    // Debug first transformed node
    if (transformedNodes.length > 0) {
      console.log('First transformed node tooltip:', transformedNodes[0].title);
    }

    const visNodes = new DataSet(transformedNodes);
    const visEdges = new DataSet(transformedEdges);

    const data = {
      nodes: visNodes,
      edges: visEdges
    };

    // Configure network options
    const options = {
      layout: {
        improvedLayout: true,
        hierarchical: false
      },
      physics: {
        enabled: true,
        stabilization: { iterations: 100 },
        barnesHut: {
          gravitationalConstant: -2000,
          centralGravity: 0.3,
          springLength: 95,
          springConstant: 0.04,
          damping: 0.09,
          avoidOverlap: 0.1
        }
      },
      interaction: {
        hover: true,
        hoverConnectedEdges: true,
        selectConnectedEdges: false,
        tooltipDelay: 100,
        hideEdgesOnDrag: false,
        hideEdgesOnZoom: false,
        zoomView: true,
        dragView: true,
        dragNodes: true,
        multiselect: false,
        navigationButtons: false
      },
      nodes: {
        borderWidth: 2,
        borderWidthSelected: 3,
        chosen: {
          node: true,
          label: false
        },
        font: { 
          color: '#ffffff',
          size: 12,
          face: 'Arial',
          strokeWidth: 2,
          strokeColor: '#000000'
        },
        labelHighlightBold: true,
        shape: 'dot',
        size: 20
      },
      edges: {
        arrows: {
          to: { 
            enabled: true, 
            scaleFactor: 0.8,
            type: 'arrow'
          }
        },
        color: {
          color: '#848484',
          highlight: '#2B2B2B',
          hover: '#2B2B2B'
        },
        chosen: {
          edge: true,
          label: false
        },
        font: { 
          size: 10,
          color: '#2B2B2B',
          strokeWidth: 1,
          strokeColor: '#ffffff'
        },
        smooth: {
          enabled: true,
          type: 'dynamic',
          roundness: 0.5
        },
        width: 2
      },
      configure: {
        enabled: false
      },
      height: `${height}px`,
      width: '100%',
      autoResize: true,
      clickToUse: false
    };

    // Create network with type assertion to avoid TypeScript issues
    networkRef.current = new Network(containerRef.current, data, options as any);

    // Add event listeners
    networkRef.current.on('selectNode', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = visNodes.get(nodeId);
        console.log('Selected node:', node);
      }
    });

    networkRef.current.on('selectEdge', (params) => {
      if (params.edges.length > 0) {
        const edgeId = params.edges[0];
        const edge = visEdges.get(edgeId);
        console.log('Selected edge:', edge);
      }
    });

    // Add hover event listeners with custom tooltip
    networkRef.current.on('hoverNode', (params) => {
      console.log('Hovering over node:', params.node);
      const rawNode = nodes.find(n => n.id === params.node);
      if (rawNode) {
        console.log('Found raw node:', rawNode);
        const tooltipText = createCustomTooltipLocal(rawNode);
        setTooltipContent(tooltipText);
        setTooltipPosition({x: params.pointer.DOM.x, y: params.pointer.DOM.y});
      }
    });

    networkRef.current.on('hoverEdge', (params) => {
      console.log('Hovering over edge:', params.edge);
      const rawEdge = relationships.find(r => r.id === params.edge);
      if (rawEdge) {
        console.log('Found raw edge:', rawEdge);
        const tooltipText = createCustomEdgeTooltipLocal(rawEdge);
        setTooltipContent(tooltipText);
        setTooltipPosition({x: params.pointer.DOM.x, y: params.pointer.DOM.y});
      }
    });

    // Hide tooltip when not hovering
    networkRef.current.on('blurNode', () => {
      setTooltipPosition(null);
      setTooltipContent('');
    });

    networkRef.current.on('blurEdge', () => {
      setTooltipPosition(null);
      setTooltipContent('');
    });

    // Cleanup function
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [nodes, relationships, height]);

  if (nodes.length === 0) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography color="text.secondary">
          No nodes available for visualization
        </Typography>
      </Paper>
    );
  }

  const handleOpenFullscreen = () => {
    // Create a URL with the graph data as query parameters
    const graphData = {
      nodes: nodes,
      relationships: relationships
    };
    
    // Encode the data to pass it via URL
    const encodedData = encodeURIComponent(JSON.stringify(graphData));
    const fullscreenUrl = `/network-fullscreen?data=${encodedData}`;
    
    // Open in new tab
    window.open(fullscreenUrl, '_blank');
  };

  return (
    <Box sx={{ mb: 3, position: 'relative' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          Network Visualization
        </Typography>
        <Tooltip title="Open in fullscreen">
          <IconButton 
            size="small" 
            onClick={handleOpenFullscreen}
            sx={{ ml: 1 }}
          >
            <OpenInNew fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
      <Paper 
        sx={{ 
          p: 1,
          height: height + 20,
          overflow: 'hidden',
          border: '1px solid #e0e0e0'
        }}
      >
        <div 
          ref={containerRef} 
          style={{ 
            width: '100%', 
            height: `${height}px`,
            backgroundColor: '#fafafa'
          }} 
        />
      </Paper>
      
      {/* Custom tooltip overlay */}
      {tooltipPosition && tooltipContent && (
        <Box
          sx={{
            position: 'absolute',
            left: tooltipPosition.x + 10,
            top: tooltipPosition.y - 10,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            color: 'white',
            padding: 1,
            borderRadius: 1,
            fontSize: '12px',
            maxWidth: 300,
            whiteSpace: 'pre-line',
            pointerEvents: 'none',
            zIndex: 1000,
            fontFamily: 'monospace'
          }}
        >
          {tooltipContent}
        </Box>
      )}
      
      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
        Click and drag to explore. Hover over nodes and edges for details.
      </Typography>
    </Box>
  );
};
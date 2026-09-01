// frontend/src/components/SupplyChainGraph.tsx
import { useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

// Color coding for different node types
const nodeColors: Record<string, string> = {
  Country: '#4CAF50',
  Port: '#2196F3',
  Warehouse: '#FF9800',
  Manufacturer: '#9C27B0',
  Supplier: '#F44336',
  Product: '#607D8B',
};

interface GraphData {
  nodes: { id: string; labels: string[]; properties: any }[];
  links: { source: string; target: string; type: string }[];
}

interface Props {
  data: GraphData | null;
  onNodeClick: (nodeId: string) => void;
}

export default function SupplyChainGraph({ data, onNodeClick }: Props) {
  const { initialNodes, initialEdges } = useMemo(() => {
    if (!data) return { initialNodes: [], initialEdges: [] };

    const rfNodes = data.nodes.map((n, index) => {
      const label = n.labels[0] || 'Default';
      
      // Grid layout optimized for ~35-100 nodes
      const col = index % 7; 
      const row = Math.floor(index / 7);
      
      // Determine border color based on risk
      let borderColor = 'rgba(255,255,255,0.3)';
      let boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
      
      if (n.properties.risk === 'HIGH') {
        borderColor = '#dc2626'; // Red
        boxShadow = '0 0 0 3px rgba(220, 38, 38, 0.3), 0 4px 12px rgba(0,0,0,0.15)';
      } else if (n.properties.risk === 'MEDIUM') {
        borderColor = '#ea580c'; // Orange
        boxShadow = '0 0 0 3px rgba(234, 88, 12, 0.3), 0 4px 12px rgba(0,0,0,0.15)';
      }

      return {
        id: n.id,
        data: { 
          label: n.properties.name || label,
        },
        style: {
          background: nodeColors[label] || '#999',
          color: '#fff',
          border: `3px solid ${borderColor}`,
          borderRadius: '12px',
          padding: '12px 16px',
          fontWeight: 600,
          fontSize: '13px',
          width: 140,
          textAlign: 'center' as const,
          boxShadow: boxShadow,
          transition: 'all 0.3s ease',
        },
        position: { x: col * 220, y: row * 180 },
      };
    });

    const rfEdges = data.links.map((l, index) => ({
      id: `e-${index}`,
      source: l.source,
      target: l.target,
      label: l.type,
      animated: true,
      style: { 
        stroke: '#888',
        strokeWidth: 2
      },
      labelStyle: {
        fontSize: 11,
        fontWeight: 600
      }
    }));

    return { initialNodes: rfNodes, initialEdges: rfEdges };
  }, [data]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  const onNodeClickHandler = useCallback(
    (event: React.MouseEvent, node: any) => {
      onNodeClick(node.id);
    },
    [onNodeClick]
  );

  if (!data) return <div>Loading graph...</div>;

  return (
    <div style={{ 
      width: '100%', 
      height: '100%',
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0
    }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClickHandler}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        style={{ background: '#fafafa' }}
      >
        <Background color="#ddd" gap={20} />
        <Controls />
        <MiniMap 
          nodeColor={(node) => {
            const bgColor = node.style?.background as string;
            return bgColor || '#999';
          }}
          maskColor="rgba(0,0,0,0.1)"
        />
      </ReactFlow>
    </div>
  );
}
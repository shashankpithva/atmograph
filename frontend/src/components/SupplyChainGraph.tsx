// frontend/src/components/SupplyChainGraph.tsx
import { useCallback, useMemo, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const nodeColors: Record<string, string> = {
  Country: '#4CAF50',
  Port: '#2196F3',
  Warehouse: '#FF9800',
  Manufacturer: '#9C27B0',
  Supplier: '#F44336',
  Product: '#607D8B',
};

interface GraphData {
  nodes: { 
    id: string; 
    label?: string; 
    labels?: string[]; 
    name?: string;
    risk_level?: string;
    risk_score?: number;
    predicted_delay?: number;
    predicted_delay_30d?: number;
    predicted_delay_60d?: number;
    predicted_delay_90d?: number;
    properties: any; 
  }[];
  links: { source: string; target: string; type: string }[];
}

type Horizon = 'base' | '30d' | '60d' | '90d';

interface Props {
  data: GraphData | null;
  onNodeClick: (nodeId: string) => void;
  selectedHorizon: Horizon;
}

export default function SupplyChainGraph({ data, onNodeClick, selectedHorizon }: Props) {
  // 1. Calculate the derived nodes and edges based on data and selectedHorizon
  const { initialNodes, initialEdges } = useMemo(() => {
    if (!data) return { initialNodes: [], initialEdges: [] };

    const rfNodes = data.nodes.map((n, index) => {
      const label = n.label || (n.labels && n.labels[0]) || 'Default';
      const col = index % 7; 
      const row = Math.floor(index / 7);
      
      const riskLevel = n.risk_level || n.properties?.risk || 'LOW';
      let borderColor = 'rgba(255,255,255,0.3)';
      let boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
      
      if (riskLevel === 'HIGH') {
        borderColor = '#dc2626';
        boxShadow = '0 0 0 3px rgba(220, 38, 38, 0.3), 0 4px 12px rgba(0,0,0,0.15)';
      } else if (riskLevel === 'MEDIUM') {
        borderColor = '#ea580c';
        boxShadow = '0 0 0 3px rgba(234, 88, 12, 0.3), 0 4px 12px rgba(0,0,0,0.15)';
      }

      const nodeName = n.name || n.properties?.name || label;
      
      // Select delay based on horizon
      let delay = n.predicted_delay;
      if (selectedHorizon === '30d') delay = n.predicted_delay_30d;
      else if (selectedHorizon === '60d') delay = n.predicted_delay_60d;
      else if (selectedHorizon === '90d') delay = n.predicted_delay_90d;

      const horizonLabel = selectedHorizon === 'base' ? '' : ` (${selectedHorizon})`;
      
      const displayLabel = (delay !== null && delay !== undefined && delay > 0) 
        ? `${nodeName}\n⚠️ ${delay}h delay${horizonLabel}` 
        : nodeName;

      return {
        id: n.id,
        data: { label: displayLabel },
        style: {
          background: nodeColors[label] || '#999',
          color: '#fff',
          border: `3px solid ${borderColor}`,
          borderRadius: '12px',
          padding: '12px 16px',
          fontWeight: 600,
          fontSize: '13px',
          width: 170, // Slightly wider to accommodate horizon text
          textAlign: 'center' as const,
          whiteSpace: 'pre-wrap',
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
      style: { stroke: '#888', strokeWidth: 2 },
      labelStyle: { fontSize: 11, fontWeight: 600 }
    }));

    return { initialNodes: rfNodes, initialEdges: rfEdges };
  }, [data, selectedHorizon]);

  // 2. Initialize React Flow state (start empty)
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // 3. CRITICAL FIX: Sync React Flow state whenever the derived data changes
  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const onNodeClickHandler = useCallback(
    (event: React.MouseEvent, node: any) => {
      onNodeClick(node.id);
    },
    [onNodeClick]
  );

  if (!data) return <div style={{ padding: '20px' }}>Loading graph...</div>;

  return (
    <div style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}>
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
// frontend/src/App.tsx
import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import SupplyChainGraph from './components/SupplyChainGraph';
import NodeDetails from './components/NodeDetails';
import NewsAnalyzer from './components/NewsAnalyzer';

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

function App() {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedHorizon, setSelectedHorizon] = useState<Horizon>('base');
  const wsRef = useRef<WebSocket | null>(null);

  // 1. Initial Graph Fetch
  useEffect(() => {
    fetchGraph();
  }, []);

  // 2. WebSocket Connection Setup
  useEffect(() => {
    let isMounted = true;

    const connectWebSocket = () => {
      wsRef.current = new WebSocket('ws://127.0.0.1:8000/ws');

      wsRef.current.onopen = () => {
        if (isMounted) console.log('✅ WebSocket Connected to AtmoGraph Backend');
      };

      wsRef.current.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'graph_update' && isMounted) {
            console.log('🔄 Real-time graph update received via WebSocket');
            setGraphData(msg.data);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onclose = () => {
        if (isMounted) {
          console.log('❌ WebSocket Disconnected. Attempting silent reconnect in 5s...');
          setTimeout(() => {
            if (isMounted) connectWebSocket();
          }, 5000);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error observed:', error);
      };
    };

    connectWebSocket();

    return () => {
      isMounted = false;
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const fetchGraph = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/graph');
      setGraphData(response.data);
    } catch (error) {
      console.error("Error fetching graph:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleNodeClick = async (nodeId: string) => {
    try {
      const response = await axios.get(`http://127.0.0.1:8000/nodes/${nodeId}`);
      setSelectedNode(response.data);
    } catch (error) {
      console.error("Error fetching node details:", error);
    }
  };

  const horizonOptions: { value: Horizon; label: string }[] = [
    { value: 'base', label: 'Current' },
    { value: '30d', label: '30 Days' },
    { value: '60d', label: '60 Days' },
    { value: '90d', label: '90 Days' },
  ];

  return (
    <div style={{ 
      width: '100vw', 
      height: '100vh', 
      display: 'flex', 
      flexDirection: 'column',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      background: '#f5f5f5',
      margin: 0,
      padding: 0,
      overflow: 'hidden'
    }}>
      {/* Header */}
      <header style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        padding: '15px 30px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center', // Centers the timeline control
        position: 'relative' // Allows absolute positioning for the title
      }}>
        {/* Title - Absolutely positioned to the left */}
        <div style={{ position: 'absolute', left: '30px' }}>
          <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 600 }}>AtmoGraph</h1>
          <p style={{ margin: '4px 0 0 0', opacity: 0.9, fontSize: '13px' }}>Supply Chain Network Visualization</p>
        </div>

        {/* Timeline Control - Perfectly centered, won't overlap with right sidebar */}
        <div style={{
          background: 'rgba(255,255,255,0.15)',
          borderRadius: '8px',
          padding: '4px',
          display: 'flex',
          gap: '4px'
        }}>
          {horizonOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setSelectedHorizon(opt.value)}
              style={{
                background: selectedHorizon === opt.value ? 'white' : 'transparent',
                color: selectedHorizon === opt.value ? '#764ba2' : 'white',
                border: 'none',
                borderRadius: '6px',
                padding: '6px 14px',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </header>

      {/* Main Content */}
      <main style={{ flex: 1, position: 'relative', width: '100%', minHeight: 0 }}>
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', fontSize: '18px', color: '#666' }}>
            Loading Supply Chain Graph...
          </div>
        ) : (
          <SupplyChainGraph 
            data={graphData} 
            onNodeClick={handleNodeClick} 
            selectedHorizon={selectedHorizon}
          />
        )}
        
        {/* News Analyzer - Top Left (Draggable) */}
        <NewsAnalyzer 
          onAnalysisComplete={() => console.log('Analysis complete, awaiting WS update...')}
          onAllRisksCleared={() => {
            fetchGraph();
            setSelectedNode(null);
          }}
        />
      </main>

      {/* Node Details Panel - Top Right */}
      <NodeDetails 
        node={selectedNode} 
        onClose={() => setSelectedNode(null)}
        onRiskCleared={() => {
          fetchGraph();
          setSelectedNode(null);
        }}
        selectedHorizon={selectedHorizon}
      />
    </div>
  );
}

export default App;
// frontend/src/App.tsx
import { useState, useEffect } from 'react';
import axios from 'axios';
import SupplyChainGraph from './components/SupplyChainGraph';
import NodeDetails from './components/NodeDetails';
import NewsAnalyzer from './components/NewsAnalyzer';

interface GraphData {
  nodes: { id: string; labels: string[]; properties: any }[];
  links: { source: string; target: string; type: string }[];
}

function App() {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGraph();
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

  const refreshGraph = () => {
    setLoading(true);
    axios.get('http://127.0.0.1:8000/graph')
      .then(res => setGraphData(res.data))
      .finally(() => setLoading(false));
  };

  const handleNodeClick = async (nodeId: string) => {
    try {
      const response = await axios.get(`http://127.0.0.1:8000/nodes/${nodeId}`);
      setSelectedNode(response.data);
    } catch (error) {
      console.error("Error fetching node details:", error);
    }
  };

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
        padding: '20px 30px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        flexShrink: 0
      }}>
        <h1 style={{ margin: 0, fontSize: '28px', fontWeight: 600 }}>
          AtmoGraph
        </h1>
        <p style={{ margin: '5px 0 0 0', opacity: 0.9, fontSize: '14px' }}>
          Supply Chain Network Visualization
        </p>
      </header>

      {/* Main Content */}
      <main style={{ 
        flex: 1,
        position: 'relative',
        width: '100%',
        minHeight: 0
      }}>
        {loading ? (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            height: '100%',
            fontSize: '18px',
            color: '#666'
          }}>
            Loading Supply Chain Graph...
          </div>
        ) : (
          <SupplyChainGraph data={graphData} onNodeClick={handleNodeClick} />
        )}
        
        {/* News Analyzer - Top Left */}
        <NewsAnalyzer 
          onAnalysisComplete={refreshGraph}
          onAllRisksCleared={() => {
            refreshGraph();
            setSelectedNode(null);
          }}
        />
      </main>

      {/* Node Details Panel - Top Right */}
      <NodeDetails 
        node={selectedNode} 
        onClose={() => setSelectedNode(null)}
        onRiskCleared={() => {
          refreshGraph();
          setSelectedNode(null);
        }}
      />
    </div>
  );
}

export default App;
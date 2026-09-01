// frontend/src/components/NodeDetails.tsx
import axios from 'axios';

interface NodeData {
  id: string;
  labels: string[];
  properties: any;
}

interface Props {
  node: NodeData | null;
  onClose: () => void;
  onRiskCleared: () => void;
}

export default function NodeDetails({ node, onClose, onRiskCleared }: Props) {
  if (!node) return null;

  const isRisky = node.properties.risk === 'HIGH' || node.properties.risk === 'MEDIUM';

  const labelColor = node.labels[0] === 'Country' ? '#4CAF50' :
                     node.labels[0] === 'Port' ? '#2196F3' :
                     node.labels[0] === 'Warehouse' ? '#FF9800' :
                     node.labels[0] === 'Manufacturer' ? '#9C27B0' :
                     node.labels[0] === 'Supplier' ? '#F44336' :
                     node.labels[0] === 'Product' ? '#607D8B' : '#999';

  const handleClearRisk = async () => {
    try {
      await axios.post(`http://127.0.0.1:8000/nodes/${node.id}/clear-risk`);
      onRiskCleared();
    } catch (error) {
      console.error("Failed to clear risk:", error);
      alert("Failed to clear risk. Please try again.");
    }
  };

  return (
    <div style={{
      position: 'absolute',
      top: '20px',
      right: '20px',
      width: '350px',
      maxHeight: 'calc(100vh - 150px)',
      background: 'white',
      borderRadius: '12px',
      boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
      overflow: 'hidden',
      zIndex: 100
    }}>
      {/* Header with color accent */}
      <div style={{
        background: labelColor,
        color: 'white',
        padding: '20px',
        position: 'relative'
      }}>
        <button 
          onClick={onClose} 
          style={{ 
            position: 'absolute',
            top: '15px',
            right: '15px',
            cursor: 'pointer', 
            background: 'rgba(255,255,255,0.2)', 
            border: 'none', 
            color: 'white',
            fontSize: '20px',
            width: '30px',
            height: '30px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'background 0.2s'
          }}
          onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.3)'}
          onMouseOut={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.2)'}
        >
          ×
        </button>
        <h3 style={{ margin: 0, fontSize: '20px', fontWeight: 600 }}>
          {node.properties.name || 'Unknown'}
        </h3>
        <p style={{ margin: '8px 0 0 0', opacity: 0.9, fontSize: '13px' }}>
          {node.labels.join(', ')}
        </p>

        {/* Risk Badge */}
        {node.properties.risk && (
          <div style={{
            marginTop: '12px',
            padding: '8px 12px',
            background: node.properties.risk === 'HIGH' ? 'rgba(220, 38, 38, 0.2)' : 
                        node.properties.risk === 'MEDIUM' ? 'rgba(234, 88, 12, 0.2)' : 'rgba(22, 163, 74, 0.2)',
            color: node.properties.risk === 'HIGH' ? '#fca5a5' : 
                   node.properties.risk === 'MEDIUM' ? '#fdba74' : '#86efac',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: 700,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <span>RISK LEVEL</span>
            <span>{node.properties.risk} ({node.properties.risk_score})</span>
          </div>
        )}
      </div>

      {/* Properties */}
      <div style={{ padding: '20px', overflowY: 'auto', maxHeight: 'calc(100vh - 250px)' }}>
        {/* Clear Risk Button - only shown for risky nodes */}
        {isRisky && (
          <button
            onClick={handleClearRisk}
            style={{
              width: '100%',
              padding: '12px',
              background: 'white',
              color: '#dc2626',
              border: '2px solid #dc2626',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: 600,
              cursor: 'pointer',
              marginBottom: '15px',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = '#dc2626';
              e.currentTarget.style.color = 'white';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = 'white';
              e.currentTarget.style.color = '#dc2626';
            }}
          >
            🧹 Clear Risk for This Node
          </button>
        )}

        <h4 style={{ 
          margin: '0 0 15px 0', 
          fontSize: '14px', 
          fontWeight: 600,
          color: '#666',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          Properties
        </h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {Object.entries(node.properties).map(([key, value]) => (
            <div key={key} style={{
              padding: '12px',
              background: '#f8f9fa',
              borderRadius: '8px',
              borderLeft: `3px solid ${labelColor}`
            }}>
              <div style={{ 
                fontSize: '12px', 
                color: '#666', 
                fontWeight: 600,
                textTransform: 'uppercase',
                marginBottom: '4px'
              }}>
                {key}
              </div>
              <div style={{ fontSize: '15px', color: '#333', fontWeight: 500 }}>
                {String(value)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
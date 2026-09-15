// frontend/src/components/NewsAnalyzer.tsx
import { useState, useRef, useEffect } from 'react';
import axios from 'axios';

interface Props {
  onAnalysisComplete: () => void;
  onAllRisksCleared: () => void;
}

export default function NewsAnalyzer({ onAnalysisComplete, onAllRisksCleared }: Props) {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  
  // New states for draggable and minimize features
  const [isMinimized, setIsMinimized] = useState(false);
  const [position, setPosition] = useState({ x: 20, y: 20 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef({ x: 0, y: 0, posX: 0, posY: 0 });

  const handleMouseDown = (e: React.MouseEvent) => {
    // Only allow dragging from the header
    setIsDragging(true);
    dragStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      posX: position.x,
      posY: position.y,
    };
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        const deltaX = e.clientX - dragStartRef.current.x;
        const deltaY = e.clientY - dragStartRef.current.y;
        setPosition({
          x: dragStartRef.current.posX + deltaX,
          y: dragStartRef.current.posY + deltaY,
        });
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  const handleAnalyze = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await axios.post('http://127.0.0.1:8000/analyze-news', { text });
      setResult(response.data);
      onAnalysisComplete();
    } catch (err) {
      setError('Failed to analyze news. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleClearAllRisks = async () => {
    const confirmed = window.confirm(
      'Are you sure you want to clear ALL risk levels from every node? This action cannot be undone.'
    );
    if (!confirmed) return;

    setClearing(true);
    try {
      await axios.post('http://127.0.0.1:8000/clear-all-risks');
      setResult(null);
      setText('');
      onAllRisksCleared();
    } catch (err) {
      console.error("Failed to clear all risks:", err);
      alert("Failed to clear all risks. Please try again.");
    } finally {
      setClearing(false);
    }
  };

  return (
    <div style={{
      position: 'absolute',
      top: 0,
      left: 0,
      transform: `translate(${position.x}px, ${position.y}px)`,
      width: '350px',
      background: 'white',
      borderRadius: '12px',
      boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
      zIndex: 100,
      overflow: 'hidden',
      transition: isDragging ? 'none' : 'box-shadow 0.2s',
    }}>
      {/* Draggable Header */}
      <div 
        onMouseDown={handleMouseDown}
        style={{ 
          padding: '15px 20px', 
          borderBottom: isMinimized ? 'none' : '1px solid #eee',
          cursor: isDragging ? 'grabbing' : 'grab',
          userSelect: 'none',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: isDragging ? '#f9fafb' : 'white',
          transition: 'background 0.2s'
        }}
      >
        <div>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#333' }}>
            📰 News Risk Analyzer
          </h3>
          {!isMinimized && (
            <p style={{ margin: '5px 0 0 0', fontSize: '13px', color: '#666' }}>
              Paste a news snippet to detect disruptions.
            </p>
          )}
        </div>
        <button 
          onClick={(e) => {
            e.stopPropagation(); // Prevent triggering drag start
            setIsMinimized(!isMinimized);
          }}
          style={{
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            fontSize: '18px',
            color: '#666',
            padding: '0 5px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '30px',
            height: '30px',
            borderRadius: '6px',
            transition: 'background 0.2s'
          }}
          onMouseOver={(e) => e.currentTarget.style.background = '#f3f4f6'}
          onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
          title={isMinimized ? "Maximize" : "Minimize"}
        >
          {isMinimized ? '➕' : '➖'}
        </button>
      </div>

      {/* Collapsible Body */}
      {!isMinimized && (
        <div style={{ padding: '20px' }}>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="e.g., Workers at the Port of Rotterdam announced a three-week strike causing massive delays."
            style={{
              width: '100%',
              height: '100px',
              padding: '12px',
              borderRadius: '8px',
              border: '1px solid #ddd',
              fontSize: '14px',
              resize: 'none',
              fontFamily: 'inherit',
              boxSizing: 'border-box'
            }}
          />
          <button
            onClick={handleAnalyze}
            disabled={loading || !text.trim()}
            style={{
              width: '100%',
              marginTop: '12px',
              padding: '12px',
              background: loading ? '#ccc' : '#667eea',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'background 0.2s'
            }}
          >
            {loading ? 'Analyzing...' : 'Analyze News'}
          </button>

          <button
            onClick={handleClearAllRisks}
            disabled={clearing}
            style={{
              width: '100%',
              marginTop: '8px',
              padding: '10px',
              background: 'white',
              color: '#dc2626',
              border: '2px solid #dc2626',
              borderRadius: '8px',
              fontSize: '13px',
              fontWeight: 600,
              cursor: clearing ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => {
              if (!clearing) {
                e.currentTarget.style.background = '#dc2626';
                e.currentTarget.style.color = 'white';
              }
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = 'white';
              e.currentTarget.style.color = '#dc2626';
            }}
          >
            {clearing ? 'Clearing...' : '🧹 Clear All Risks'}
          </button>

          {error && <p style={{ color: 'red', fontSize: '13px', marginTop: '10px' }}>{error}</p>}

          {result && (
            <div style={{ marginTop: '15px', paddingTop: '15px', borderTop: '1px solid #eee' }}>
              <div style={{ marginBottom: '10px' }}>
                <strong style={{ fontSize: '13px', color: '#666' }}>Disruptions Found:</strong>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
                  {result.detected_disruptions.length > 0 ? (
                    result.detected_disruptions.map((d: string, i: number) => (
                      <span key={i} style={{
                        background: '#fee2e2',
                        color: '#991b1b',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: 600
                      }}>
                        {d.toUpperCase()}
                      </span>
                    ))
                  ) : (
                    <span style={{ fontSize: '13px', color: '#16a34a' }}>None detected ✅</span>
                  )}
                </div>
              </div>

              {result.risk_changes.length > 0 && (
                <div>
                  <strong style={{ fontSize: '13px', color: '#666' }}>Nodes Updated:</strong>
                  <ul style={{ margin: '6px 0 0 0', paddingLeft: '20px', fontSize: '13px', color: '#333' }}>
                    {result.risk_changes.map((change: any, i: number) => (
                      <li key={i}>
                        <strong>{change.node_name}</strong> → Risk: 
                        <span style={{ 
                          color: change.new_risk === 'HIGH' ? '#dc2626' : '#ea580c',
                          fontWeight: 600,
                          marginLeft: '4px'
                        }}>
                          {change.new_risk} ({change.new_risk_score})
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
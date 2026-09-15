# AtmoGraph: Supply Chain Risk Visualization

AtmoGraph is a full-stack Machine Learning application designed to visualize supply chain networks, detect real-world disruptions using Natural Language Processing (NLP), and predict multi-horizon delay cascades using a Graph Convolutional Network (GCN).

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, Neo4j (Graph Database), spaCy (NLP)
- **Machine Learning**: PyTorch, PyTorch Geometric (PyG)
- **Frontend**: React, TypeScript, Vite, React Flow (`@xyflow/react`), Axios
- **Testing**: `pytest`
- **Infrastructure**: Docker (Neo4j)

## ✨ Key Features

- **Interactive Graph Visualization**: Drag, pan, and zoom through a 35+ node supply chain network (Countries, Ports, Warehouses, Manufacturers, Suppliers, Products) with risk-based color coding.
- **NLP Disruption Detection**: Paste news snippets to automatically extract entities and detect disruption keywords (e.g., "strike", "fire", "shutdown") using spaCy.
- **GNN Delay Prediction**: A 2-layer Graph Convolutional Network predicts delay cascades based on node features (type, degree, current risk) and graph topology.
- **Multi-Horizon Timeline**: Dynamically switch between Current, 30-Day, 60-Day, and 90-Day predicted delay projections directly in the UI.
- **Real-Time WebSocket Updates**: The frontend instantly updates with new risk levels and GNN predictions the moment a news article is analyzed, without requiring a page refresh.
- **Draggable & Minimizable UI**: The News Analyzer panel can be dragged anywhere on the screen and minimized to keep the workspace clean.
- **Automated Testing**: Comprehensive `pytest` suite for risk logic and mocked GNN data loading.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+ and npm
- Docker (for running Neo4j)

### 1. Database Setup (Neo4j)
Start a local Neo4j instance using Docker:
```bash
docker run -d \
  --name neo4j-atmograph \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
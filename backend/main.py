# backend/main.py
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import get_db
from nlp_engine import analyze_text
from risk_engine import match_entities_in_neo4j, calculate_risk, update_node_risk_in_neo4j
from run_inference import run_inference_and_update_neo4j

app = FastAPI(title="AtmoGraph API")

# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ WebSocket client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"❌ WebSocket client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to WebSocket: {e}")

manager = ConnectionManager()

# Define the request body structure for our POST endpoint
class NewsRequest(BaseModel):
    text: str

# --- Helper to fetch graph data (reused by /graph and WebSocket broadcasts) ---
def get_graph_data():
    db = get_db()
    nodes_query = """
    MATCH (n)
    RETURN elementId(n) AS id, 
           labels(n)[0] AS label, 
           n.name AS name,
           n.risk_level AS risk_level,
           n.risk_score AS risk_score,
           n.predicted_delay AS predicted_delay,
           n.predicted_delay_30d AS predicted_delay_30d,
           n.predicted_delay_60d AS predicted_delay_60d,
           n.predicted_delay_90d AS predicted_delay_90d,
           properties(n) AS properties
    """
    rels_query = """
    MATCH (a)-[r]->(b)
    RETURN elementId(a) AS source, elementId(b) AS target, type(r) AS type
    """
    nodes = []
    links = []
    with db.session() as session:
        result_nodes = session.run(nodes_query)
        for record in result_nodes:
            nodes.append({
                "id": str(record["id"]),
                "label": record["label"],
                "name": record["name"],
                "risk_level": record["risk_level"],
                "risk_score": record["risk_score"],
                "predicted_delay": record["predicted_delay"],
                "predicted_delay_30d": record["predicted_delay_30d"],
                "predicted_delay_60d": record["predicted_delay_60d"],
                "predicted_delay_90d": record["predicted_delay_90d"],
                "properties": record["properties"]
            })
        result_rels = session.run(rels_query)
        for record in result_rels:
            links.append({
                "source": str(record["source"]),
                "target": str(record["target"]),
                "type": record["type"]
            })
    return {"nodes": nodes, "links": links}

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "AtmoGraph backend is running"}

@app.get("/graph")
def get_graph():
    """Fetches all nodes and relationships for the graph visualization."""
    return get_graph_data()

@app.get("/nodes/{node_id}")
def get_node(node_id: str):
    """Fetches details for a specific node by its ID."""
    db = get_db()
    query = """
    MATCH (n)
    WHERE elementId(n) = $node_id
    RETURN elementId(n) AS id, 
           labels(n)[0] AS label, 
           n.name AS name,
           n.risk_level AS risk_level,
           n.risk_score AS risk_score,
           n.predicted_delay AS predicted_delay,
           n.predicted_delay_30d AS predicted_delay_30d,
           n.predicted_delay_60d AS predicted_delay_60d,
           n.predicted_delay_90d AS predicted_delay_90d,
           properties(n) AS properties
    """
    with db.session() as session:
        result = session.run(query, node_id=node_id)
        record = result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Node not found")

        return {
            "id": str(record["id"]),
            "label": record["label"],
            "name": record["name"],
            "risk_level": record["risk_level"],
            "risk_score": record["risk_score"],
            "predicted_delay": record["predicted_delay"],
            "predicted_delay_30d": record["predicted_delay_30d"],
            "predicted_delay_60d": record["predicted_delay_60d"],
            "predicted_delay_90d": record["predicted_delay_90d"],
            "properties": record["properties"]
        }

@app.get("/test-nlp")
def test_nlp(text: str):
    """Temporary endpoint to test the NLP engine."""
    return analyze_text(text)

@app.post("/analyze-news")
async def analyze_news(request: NewsRequest, background_tasks: BackgroundTasks):
    """
    Full pipeline: NLP -> Entity Matching -> Risk Calculation -> Neo4j Update
    Triggers GNN inference and WebSocket broadcast in the background.
    """
    # 1. Run NLP to extract entities and disruptions
    nlp_result = analyze_text(request.text)
    
    # 2. Match extracted entities with Neo4j nodes
    matched_nodes = match_entities_in_neo4j(nlp_result["entities"])
    
    # 3. Calculate risk based on disruptions
    risk_level, risk_score = calculate_risk(nlp_result["disruptions"])
    
    # 4. Update Neo4j and track changes (only if disruptions were found)
    risk_changes = []
    if nlp_result["disruptions"]:
        for node in matched_nodes:
            node_id_str = str(node["id"])
            update_node_risk_in_neo4j(node_id_str, risk_level, risk_score)
            risk_changes.append({
                "node_id": node_id_str,
                "node_name": node["properties"].get("name"),
                "new_risk": risk_level,
                "new_risk_score": risk_score
            })
            
    # 5. Trigger GNN Inference and WebSocket Broadcast in the background
    background_tasks.add_task(run_inference_and_broadcast)
            
    # 6. Return the immediate NLP analysis results to the frontend
    return {
        "extracted_entities": nlp_result["entities"],
        "detected_disruptions": nlp_result["disruptions"],
        "matched_nodes": matched_nodes,
        "risk_changes": risk_changes
    }

async def run_inference_and_broadcast():
    """Background task: Runs the GNN inference and broadcasts the updated graph to all WebSocket clients."""
    print("🔄 [Background Task] Running GNN inference...")
    run_inference_and_update_neo4j() # Synchronous call is fine for our small graph
    
    print("📡 [Background Task] Broadcasting updated graph via WebSocket...")
    updated_graph = get_graph_data()
    await manager.broadcast({
        "type": "graph_update", 
        "data": updated_graph
    })

@app.post("/nodes/{node_id}/clear-risk")
def clear_node_risk(node_id: str):
    """Clear the risk properties of a specific node."""
    db = get_db()
    query = """
    MATCH (n)
    WHERE elementId(n) = $node_id
    SET n.risk_level = 'LOW', n.risk_score = 0.1
    RETURN n.name AS name
    """
    with db.session() as session:
        result = session.run(query, node_id=node_id)
        record = result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Node not found")
        return {"status": "ok", "node_name": record["name"]}

@app.post("/clear-all-risks")
def clear_all_risks():
    """Reset all nodes to LOW risk."""
    db = get_db()
    query = """
    MATCH (n)
    SET n.risk_level = 'LOW', n.risk_score = 0.1
    RETURN count(n) AS count
    """
    with db.session() as session:
        result = session.run(query)
        record = result.single()
        return {"status": "ok", "nodes_reset": record["count"]}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive. Listen for client messages (e.g., pings).
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
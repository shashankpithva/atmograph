# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import get_db
from nlp_engine import analyze_text
from risk_engine import match_entities_in_neo4j, calculate_risk, update_node_risk_in_neo4j

app = FastAPI(title="AtmoGraph API")

# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the request body structure for our POST endpoint
class NewsRequest(BaseModel):
    text: str


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "AtmoGraph backend is running"}


@app.get("/graph")
def get_graph():
    """Fetches all nodes and relationships for the graph visualization."""
    db = get_db()

    nodes_query = """
    MATCH (n)
    RETURN id(n) AS id, labels(n) AS labels, properties(n) AS properties
    """

    rels_query = """
    MATCH (a)-[r]->(b)
    RETURN id(a) AS source, id(b) AS target, type(r) AS type
    """

    nodes = []
    links = []

    with db.session() as session:
        result_nodes = session.run(nodes_query)
        for record in result_nodes:
            nodes.append({
                "id": str(record["id"]),
                "labels": record["labels"],
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


@app.get("/nodes/{node_id}")
def get_node(node_id: int):
    """Fetches details for a specific node by its ID."""
    db = get_db()
    query = """
    MATCH (n)
    WHERE id(n) = $node_id
    RETURN id(n) AS id, labels(n) AS labels, properties(n) AS properties
    """

    with db.session() as session:
        result = session.run(query, node_id=node_id)
        record = result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Node not found")

        return {
            "id": str(record["id"]),
            "labels": record["labels"],
            "properties": record["properties"]
        }


@app.get("/test-nlp")
def test_nlp(text: str):
    """Temporary endpoint to test the NLP engine."""
    return analyze_text(text)


@app.post("/analyze-news")
def analyze_news(request: NewsRequest):
    """
    Full pipeline: NLP -> Entity Matching -> Risk Calculation -> Neo4j Update
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
            node_id = int(node["id"])
            update_node_risk_in_neo4j(node_id, risk_level, risk_score)
            risk_changes.append({
                "node_id": node["id"],
                "node_name": node["properties"].get("name"),
                "new_risk": risk_level,
                "new_risk_score": risk_score
            })
            
    # 5. Return the complete analysis
    return {
        "extracted_entities": nlp_result["entities"],
        "detected_disruptions": nlp_result["disruptions"],
        "matched_nodes": matched_nodes,
        "risk_changes": risk_changes
    }


@app.post("/nodes/{node_id}/clear-risk")
def clear_node_risk(node_id: int):
    """Clear the risk properties of a specific node."""
    db = get_db()
    query = """
    MATCH (n)
    WHERE id(n) = $node_id
    SET n.risk = 'LOW', n.risk_score = 0.1
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
    SET n.risk = 'LOW', n.risk_score = 0.1
    RETURN count(n) AS count
    """
    with db.session() as session:
        result = session.run(query)
        record = result.single()
        return {"status": "ok", "nodes_reset": record["count"]}
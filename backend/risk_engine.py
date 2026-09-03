# backend/risk_engine.py
from database import get_db

def normalize_entity(entity_text: str) -> str:
    """Normalize entity text for matching (lowercase, strip whitespace, remove articles)."""
    text = entity_text.strip().lower()
    articles = ['the ', 'a ', 'an ']
    for article in articles:
        if text.startswith(article):
            text = text[len(article):]
    return text

def match_entities_in_neo4j(entities: list[dict]) -> list[dict]:
    """Find matching nodes in Neo4j based on extracted entities."""
    db = get_db()
    matched_nodes = []
    
    with db.session() as session:
        for ent in entities:
            normalized_name = normalize_entity(ent['text'])
            
            # Try exact match first
            query = """
            MATCH (n)
            WHERE toLower(n.name) = $name
            RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS properties
            """
            result = session.run(query, name=normalized_name)
            records = list(result)
            
            # If no exact match, try partial match
            if not records:
                query = """
                MATCH (n)
                WHERE toLower(n.name) CONTAINS $name OR $name CONTAINS toLower(n.name)
                RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS properties
                LIMIT 1
                """
                result = session.run(query, name=normalized_name)
                records = list(result)
            
            for record in records:
                matched_nodes.append({
                    "id": str(record["id"]),
                    "labels": record["labels"],
                    "properties": record["properties"],
                    "matched_entity": ent['text']
                })
                
    return matched_nodes

def calculate_risk(disruptions: list[str]) -> tuple[str, float]:
    """Calculate risk level and score based on detected disruptions."""
    if not disruptions:
        return "LOW", 0.1
        
    num_disruptions = len(disruptions)
    if num_disruptions == 1:
        return "MEDIUM", 0.5
    elif num_disruptions == 2:
        return "HIGH", 0.8
    else:
        return "HIGH", 0.95

def update_node_risk_in_neo4j(node_id: str, risk_level: str, risk_score: float):
    """Update the risk properties of a node in Neo4j."""
    db = get_db()
    # Updated to use elementId and n.risk_level for schema consistency
    query = """
    MATCH (n)
    WHERE elementId(n) = $node_id
    SET n.risk_level = $risk_level, n.risk_score = $risk_score
    """
    with db.session() as session:
        session.run(query, node_id=node_id, risk_level=risk_level, risk_score=risk_score)
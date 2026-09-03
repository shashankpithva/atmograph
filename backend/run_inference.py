# backend/run_inference.py
import torch
import datetime
from gnn_data_loader import load_graph_from_neo4j
from gnn_models import GCNModel
from database import get_db

def run_inference_and_update_neo4j():
    print("Loading graph data...")
    data = load_graph_from_neo4j()
    
    in_channels = data.num_node_features
    hidden_channels = 16
    
    # 1. Load the trained GCN model
    print("Loading trained GCN model...")
    model = GCNModel(in_channels, hidden_channels)
    # weights_only=True is a security best practice in PyTorch 2.x
    model.load_state_dict(torch.load("models/gcn_model.pth", map_location=torch.device('cpu'), weights_only=True))
    model.eval()
    
    # 2. Run predictions
    print("Running predictions...")
    with torch.no_grad():
        predictions = model(data.x, data.edge_index)
        
    predicted_delays = predictions.numpy()
    
    # 3. Map predictions to risk_score and risk_level
    results = []
    current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    for i in range(data.num_nodes):
        delay = float(predicted_delays[i])
        delay = max(0.0, delay) # Ensure non-negative delay
        
        # Calculate risk score (0.0 to 1.0), capping at 72 hours for normalization
        risk_score = min(delay / 72.0, 1.0)
        
        # Determine risk level based on delay hours
        if delay < 24.0:
            risk_level = "LOW"
        elif delay < 48.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
            
        neo_id = data.idx_to_neo_id[i]
        results.append({
            "neo_id": neo_id,
            "predicted_delay": round(delay, 2),
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "timestamp": current_time
        })
        
    # 4. Update Neo4j
    print("Updating Neo4j with predictions...")
    driver = get_db()
    
    # Note: Using 'prediction_timestamp' to avoid overwriting any existing 'timestamp' 
    # properties from Week 2's news analysis, while fulfilling the requirement.
    update_query = """
    MATCH (n)
    WHERE elementId(n) = $neo_id
    SET n.predicted_delay = $predicted_delay,
        n.risk_score = $risk_score,
        n.risk_level = $risk_level,
        n.prediction_timestamp = $timestamp
    """
    
    with driver.session() as session:
        for res in results:
            session.run(update_query, res)
            
    print(f"✅ Successfully updated {len(results)} nodes in Neo4j!")
    
    # Print a few examples
    print("\nSample Predictions:")
    for res in results[:3]:
        print(f"  Node {res['neo_id']}: Delay={res['predicted_delay']}h, Risk={res['risk_level']} ({res['risk_score']})")

if __name__ == "__main__":
    run_inference_and_update_neo4j()
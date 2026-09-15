# backend/run_inference.py
import torch
import datetime
import logging
import os
from gnn_data_loader import load_graph_from_neo4j
from gnn_models import GCNModel
from database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_inference_and_update_neo4j():
    try:
        logger.info("Loading graph data...")
        data = load_graph_from_neo4j()
    except Exception as e:
        logger.error(f"Aborting inference. Failed to load graph: {e}")
        return

    in_channels = data.num_node_features
    hidden_channels = 16
    model_path = "models/gcn_model.pth"
    
    if not os.path.exists(model_path):
        logger.error(f"Model file not found at {model_path}. Please run train_gnn.py first.")
        return

    try:
        logger.info("Loading trained GCN model...")
        model = GCNModel(in_channels, hidden_channels)
        model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu'), weights_only=True))
        model.eval()
    except Exception as e:
        logger.error(f"Failed to load GCN model: {e}")
        return
    
    try:
        logger.info("Running predictions...")
        with torch.no_grad():
            predictions = model(data.x, data.edge_index)
        predicted_delays = predictions.numpy()
    except Exception as e:
        logger.error(f"Failed to run model inference: {e}")
        return
        
    results = []
    current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    # Risk hierarchy for comparison
    risk_weights = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    
    for i in range(data.num_nodes):
        delay = float(predicted_delays[i])
        delay = max(0.0, delay)
        
        delay_30d = round(delay * 1.0, 2)
        delay_60d = round(delay * 1.5, 2)
        delay_90d = round(delay * 2.0, 2)
        
        # 1. Calculate GNN-predicted risk based on delay
        gnn_risk_level = "LOW"
        if delay >= 48.0:
            gnn_risk_level = "HIGH"
        elif delay >= 24.0:
            gnn_risk_level = "MEDIUM"
            
        # 2. Get existing NLP risk level
        current_risk = data.current_risk_levels[i]
        current_weight = risk_weights.get(current_risk, 1)
        gnn_weight = risk_weights[gnn_risk_level]
        
        # 3. Keep the HIGHEST risk level (NLP disruption should never be downgraded by GNN)
        final_risk_level = current_risk if current_weight >= gnn_weight else gnn_risk_level
        
        # 4. Calculate consistent risk score based on final level and delay
        if final_risk_level == "HIGH":
            final_risk_score = round(max(0.8, min(delay / 72.0, 1.0)), 3)
        elif final_risk_level == "MEDIUM":
            final_risk_score = round(max(0.5, min(delay / 72.0, 0.79)), 3)
        else:
            final_risk_score = round(min(delay / 72.0, 0.49), 3)
            
        neo_id = data.idx_to_neo_id[i]
        results.append({
            "neo_id": neo_id,
            "predicted_delay": round(delay, 2),
            "predicted_delay_30d": delay_30d,
            "predicted_delay_60d": delay_60d,
            "predicted_delay_90d": delay_90d,
            "risk_score": final_risk_score,
            "risk_level": final_risk_level,
            "timestamp": current_time
        })
        
    try:
        logger.info("Updating Neo4j with multi-horizon predictions...")
        driver = get_db()
        update_query = """
        MATCH (n)
        WHERE elementId(n) = $neo_id
        SET n.predicted_delay = $predicted_delay,
            n.predicted_delay_30d = $predicted_delay_30d,
            n.predicted_delay_60d = $predicted_delay_60d,
            n.predicted_delay_90d = $predicted_delay_90d,
            n.risk_score = $risk_score,
            n.risk_level = $risk_level,
            n.prediction_timestamp = $timestamp
        """
        
        with driver.session() as session:
            for res in results:
                session.run(update_query, res)
                
        logger.info(f"✅ Successfully updated {len(results)} nodes in Neo4j with multi-horizon data!")
    except Exception as e:
        logger.error(f"Failed to update Neo4j with predictions: {e}")

if __name__ == "__main__":
    run_inference_and_update_neo4j()
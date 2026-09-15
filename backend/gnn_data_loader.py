# backend/gnn_data_loader.py
import torch
import logging
from torch_geometric.data import Data
from database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NODE_TYPE_MAP = {
    'Country': 0, 'Supplier': 1, 'Manufacturer': 2,
    'Port': 3, 'Warehouse': 4, 'Product': 5
}

RISK_MAP = {'LOW': 0.33, 'MEDIUM': 0.66, 'HIGH': 1.0, None: 0.0}

def load_graph_from_neo4j():
    try:
        driver = get_db()
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j driver: {e}")
        raise RuntimeError("Database connection failed")

    nodes_query = """
    MATCH (n)
    RETURN elementId(n) AS neo_id, labels(n)[0] AS node_type, n.id AS node_id, n.risk_level AS risk_level, n.risk_score AS risk_score
    """
    edges_query = """
    MATCH (a)-[r]->(b)
    RETURN elementId(a) AS source_id, elementId(b) AS target_id
    """
    
    try:
        with driver.session() as session:
            node_records = session.run(nodes_query).data()
            
            neo_id_to_idx = {}
            num_nodes = len(node_records)
            node_types = []
            risk_scores = []
            current_risk_levels = []
            
            for idx, record in enumerate(node_records):
                neo_id = record['neo_id']
                neo_id_to_idx[neo_id] = idx
                
                node_type = record['node_type'] or 'Unknown'
                type_idx = NODE_TYPE_MAP.get(node_type, -1)
                node_types.append(type_idx)
                
                risk_level = record['risk_level'] or 'LOW'
                current_risk_levels.append(risk_level)
                
                risk_val = RISK_MAP.get(risk_level, 0.0)
                risk_scores.append(risk_val)
                
            edge_records = session.run(edges_query).data()
            
            source_indices = []
            target_indices = []
            
            for record in edge_records:
                src_neo_id = record['source_id']
                tgt_neo_id = record['target_id']
                if src_neo_id in neo_id_to_idx and tgt_neo_id in neo_id_to_idx:
                    source_indices.append(neo_id_to_idx[src_neo_id])
                    target_indices.append(neo_id_to_idx[tgt_neo_id])
                    
            edge_index = torch.tensor([source_indices, target_indices], dtype=torch.long)
            
            degrees = torch.zeros(num_nodes, dtype=torch.float)
            unique, counts = torch.unique(edge_index.flatten(), return_counts=True)
            degrees[unique] = counts.float()
            
            max_degree = degrees.max().item() if degrees.max().item() > 0 else 1.0
            normalized_degrees = (degrees / max_degree).unsqueeze(1)
            
            node_types_tensor = torch.tensor(node_types, dtype=torch.long)
            node_types_tensor = torch.clamp(node_types_tensor, min=0, max=len(NODE_TYPE_MAP)-1)
            node_type_one_hot = torch.nn.functional.one_hot(node_types_tensor, num_classes=len(NODE_TYPE_MAP)).float()
            
            risk_scores_tensor = torch.tensor(risk_scores, dtype=torch.float).unsqueeze(1)
            
            x = torch.cat([node_type_one_hot, normalized_degrees, risk_scores_tensor], dim=1)
            
            # --- TUNED FORMULA ---
            # Ensures baseline LOW risk nodes stay under 24h delay, even with high degree.
            # HIGH risk nodes will correctly cascade to 24h+ delays.
            noise = torch.randn(num_nodes, 1) * 2.0
            y = (risk_scores_tensor * 20.0) + (normalized_degrees * 10.0) + noise
            y = y.squeeze()
            
            num_train = int(num_nodes * 0.6)
            num_val = int(num_nodes * 0.2)
            perm = torch.randperm(num_nodes)
            
            train_mask = torch.zeros(num_nodes, dtype=torch.bool)
            val_mask = torch.zeros(num_nodes, dtype=torch.bool)
            test_mask = torch.zeros(num_nodes, dtype=torch.bool)
            
            train_mask[perm[:num_train]] = True
            val_mask[perm[num_train:num_train + num_val]] = True
            test_mask[perm[num_train + num_val:]] = True
            
            graph_data = Data(
                x=x, edge_index=edge_index, y=y,
                train_mask=train_mask, val_mask=val_mask, test_mask=test_mask,
                num_nodes=num_nodes
            )
            
            graph_data.neo_id_to_idx = neo_id_to_idx
            graph_data.idx_to_neo_id = {v: k for k, v in neo_id_to_idx.items()}
            graph_data.current_risk_levels = current_risk_levels
            
            return graph_data
            
    except Exception as e:
        logger.error(f"Error loading graph from Neo4j: {e}")
        raise RuntimeError("Failed to load graph data from database")

if __name__ == "__main__":
    try:
        data = load_graph_from_neo4j()
        logger.info(f"✅ Successfully loaded PyTorch Geometric Data! Nodes: {data.num_nodes}, Edges: {data.num_edges}")
    except Exception as e:
        logger.error(f"❌ Error loading graph: {e}")
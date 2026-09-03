# backend/gnn_data_loader.py
import torch
from torch_geometric.data import Data
from database import get_db

# Mapping for node types (based on Week 1 mock nodes)
NODE_TYPE_MAP = {
    'Country': 0,
    'Supplier': 1,
    'Manufacturer': 2,
    'Port': 3,
    'Warehouse': 4,
    'Product': 5
}

# Mapping for risk levels to numeric values
RISK_MAP = {
    'LOW': 0.33,
    'MEDIUM': 0.66,
    'HIGH': 1.0,
    None: 0.0
}

def load_graph_from_neo4j():
    driver = get_db()
    
    # 1. Fetch all nodes
    nodes_query = """
    MATCH (n)
    RETURN elementId(n) AS neo_id, 
           labels(n)[0] AS node_type, 
           n.id AS node_id,
           n.risk_level AS risk_level,
           n.risk_score AS risk_score
    """
    
    # 2. Fetch all relationships
    edges_query = """
    MATCH (a)-[r]->(b)
    RETURN elementId(a) AS source_id, elementId(b) AS target_id
    """
    
    with driver.session() as session:
        # Execute node query
        node_records = session.run(nodes_query).data()
        
        # Build mapping from neo_id to local tensor index (0 to N-1)
        neo_id_to_idx = {}
        num_nodes = len(node_records)
        
        # Initialize feature lists
        node_types = []
        risk_scores = []
        
        for idx, record in enumerate(node_records):
            neo_id = record['neo_id']
            neo_id_to_idx[neo_id] = idx
            
            # Feature 1: Node type (integer encoded, will be one-hot encoded later)
            node_type = record['node_type'] or 'Unknown'
            type_idx = NODE_TYPE_MAP.get(node_type, -1)
            node_types.append(type_idx)
            
            # Feature 2: Current risk (float)
            risk_level = record['risk_level']
            risk_val = RISK_MAP.get(risk_level, 0.0)
            risk_scores.append(risk_val)
            
        # Execute edge query
        edge_records = session.run(edges_query).data()
        
        # Build edge_index (2 x E tensor)
        source_indices = []
        target_indices = []
        
        for record in edge_records:
            src_neo_id = record['source_id']
            tgt_neo_id = record['target_id']
            
            if src_neo_id in neo_id_to_idx and tgt_neo_id in neo_id_to_idx:
                source_indices.append(neo_id_to_idx[src_neo_id])
                target_indices.append(neo_id_to_idx[tgt_neo_id])
                
        edge_index = torch.tensor([source_indices, target_indices], dtype=torch.long)
        
        # Feature 3: Degree/connectivity (normalized)
        degrees = torch.zeros(num_nodes, dtype=torch.float)
        unique, counts = torch.unique(edge_index.flatten(), return_counts=True)
        degrees[unique] = counts.float()
        
        # Normalize degrees (simple max normalization, avoid div by zero)
        max_degree = degrees.max().item() if degrees.max().item() > 0 else 1.0
        normalized_degrees = (degrees / max_degree).unsqueeze(1)
        
        # Encode node types as one-hot
        node_types_tensor = torch.tensor(node_types, dtype=torch.long)
        node_types_tensor = torch.clamp(node_types_tensor, min=0, max=len(NODE_TYPE_MAP)-1)
        node_type_one_hot = torch.nn.functional.one_hot(node_types_tensor, num_classes=len(NODE_TYPE_MAP)).float()
        
        # Risk scores tensor
        risk_scores_tensor = torch.tensor(risk_scores, dtype=torch.float).unsqueeze(1)
        
        # Combine features: [One-Hot Type (6) + Normalized Degree (1) + Risk Score (1)] = 8 dimensions
        x = torch.cat([node_type_one_hot, normalized_degrees, risk_scores_tensor], dim=1)
        
        # --- NEW: Create Prediction Target (y) ---
        # downstream_delay (in hours) is modeled as a function of risk and degree + noise
        # This provides a learnable, deterministic signal for the GNN.
        noise = torch.randn(num_nodes, 1) * 2.0  # Small noise (std=2)
        y = (risk_scores_tensor * 48.0) + (normalized_degrees * 24.0) + noise
        y = y.squeeze() # Make it 1D tensor of shape [num_nodes]
        
        # --- NEW: Train/Val/Test Splits ---
        # For 35 nodes: ~60% train (21), ~20% val (7), ~20% test (7)
        num_train = int(num_nodes * 0.6)
        num_val = int(num_nodes * 0.2)
        
        # Create a random permutation of node indices
        perm = torch.randperm(num_nodes)
        
        train_mask = torch.zeros(num_nodes, dtype=torch.bool)
        val_mask = torch.zeros(num_nodes, dtype=torch.bool)
        test_mask = torch.zeros(num_nodes, dtype=torch.bool)
        
        train_mask[perm[:num_train]] = True
        val_mask[perm[num_train:num_train + num_val]] = True
        test_mask[perm[num_train + num_val:]] = True
        
        # Create PyTorch Geometric Data object
        graph_data = Data(
            x=x, 
            edge_index=edge_index, 
            y=y,
            train_mask=train_mask,
            val_mask=val_mask,
            test_mask=test_mask,
            num_nodes=num_nodes
        )
        
        # Attach metadata for later use (e.g., mapping back to Neo4j)
        graph_data.neo_id_to_idx = neo_id_to_idx
        graph_data.idx_to_neo_id = {v: k for k, v in neo_id_to_idx.items()}
        
        return graph_data

if __name__ == "__main__":
    print("Loading graph from Neo4j...")
    try:
        data = load_graph_from_neo4j()
        print("\n✅ Successfully loaded PyTorch Geometric Data!")
        print(f"Number of nodes: {data.num_nodes}")
        print(f"Number of edges: {data.num_edges}")
        print(f"Node feature dimensions (x): {data.x.shape}")
        print(f"Target variable (y) shape: {data.y.shape}")
        print(f"Train/Val/Test split: {data.train_mask.sum().item()} / {data.val_mask.sum().item()} / {data.test_mask.sum().item()}")
        print("\nSample node features (first 2 nodes):\n", data.x[:2])
        print("Sample targets (first 2 nodes):\n", data.y[:2])
    except Exception as e:
        print(f"❌ Error loading graph: {e}")
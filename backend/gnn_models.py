# backend/gnn_models.py
import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv

class BaselineMLP(torch.nn.Module):
    """
    Baseline Multi-Layer Perceptron.
    Ignores graph structure (edges) and only uses node features (x).
    """
    def __init__(self, in_channels, hidden_channels):
        super().__init__()
        self.lin1 = torch.nn.Linear(in_channels, hidden_channels)
        self.lin2 = torch.nn.Linear(hidden_channels, 1)

    def forward(self, x):
        # x shape: [num_nodes, in_channels]
        x = F.relu(self.lin1(x))
        x = F.dropout(x, p=0.5, training=self.training) # Dropout for regularization
        x = self.lin2(x)
        return x.squeeze() # Output shape: [num_nodes]

class GCNModel(torch.nn.Module):
    """
    2-Layer Graph Convolutional Network (GCN).
    Leverages graph structure (edge_index) to aggregate neighbor information.
    """
    def __init__(self, in_channels, hidden_channels):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, hidden_channels)
        self.lin = torch.nn.Linear(hidden_channels, 1)

    def forward(self, x, edge_index):
        # x shape: [num_nodes, in_channels]
        # edge_index shape: [2, num_edges]
        
        # First GCN layer
        x = self.conv1(x, edge_index).relu()
        x = F.dropout(x, p=0.5, training=self.training)
        
        # Second GCN layer
        x = self.conv2(x, edge_index).relu()
        x = F.dropout(x, p=0.5, training=self.training)
        
        # Final linear layer for regression output
        x = self.lin(x)
        return x.squeeze() # Output shape: [num_nodes]

if __name__ == "__main__":
    from gnn_data_loader import load_graph_from_neo4j
    
    print("Loading graph data to test models...")
    data = load_graph_from_neo4j()
    
    in_channels = data.num_node_features
    hidden_channels = 16
    
    # 1. Test Baseline MLP
    print("\n--- Testing Baseline MLP ---")
    mlp_model = BaselineMLP(in_channels, hidden_channels)
    mlp_out = mlp_model(data.x)
    print(f"MLP Input shape: {data.x.shape}")
    print(f"MLP Output shape: {mlp_out.shape}")
    print(f"MLP Sample predictions: {mlp_out[:3].detach().numpy()}")
    
    # 2. Test GCN Model
    print("\n--- Testing GCN Model ---")
    gcn_model = GCNModel(in_channels, hidden_channels)
    gcn_out = gcn_model(data.x, data.edge_index)
    print(f"GCN Input shape (x): {data.x.shape}")
    print(f"GCN Input shape (edge_index): {data.edge_index.shape}")
    print(f"GCN Output shape: {gcn_out.shape}")
    print(f"GCN Sample predictions: {gcn_out[:3].detach().numpy()}")
    
    print("\n✅ Both models initialized and forward passes successful!")
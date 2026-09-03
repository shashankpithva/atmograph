# backend/train_gnn.py
import os
import torch
import torch.nn.functional as F
from gnn_data_loader import load_graph_from_neo4j
from gnn_models import BaselineMLP, GCNModel

# --- Custom Metrics (to avoid scikit-learn dependency) ---
def mae(pred, true):
    return torch.abs(pred - true).mean().item()

def rmse(pred, true):
    return torch.sqrt(((pred - true) ** 2).mean()).item()

def r2(pred, true):
    ss_res = ((true - pred) ** 2).sum().item()
    ss_tot = ((true - true.mean()) ** 2).sum().item()
    return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

# --- Training Function ---
def train_model(model, data, model_name, epochs=200, lr=0.01, weight_decay=5e-4):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    criterion = torch.nn.MSELoss()
    
    best_val_loss = float('inf')
    best_model_state = None
    
    print(f"\n🚀 Training {model_name}...")
    
    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()
        
        # Forward pass (GCN needs edge_index, MLP does not)
        if isinstance(model, GCNModel):
            out = model(data.x, data.edge_index)
        else:
            out = model(data.x)
            
        # Calculate loss ONLY on training nodes
        loss = criterion(out[data.train_mask], data.y[data.train_mask])
        loss.backward()
        optimizer.step()
        
        # Validation phase every 20 epochs
        if epoch % 20 == 0:
            model.eval()
            with torch.no_grad():
                if isinstance(model, GCNModel):
                    val_out = model(data.x, data.edge_index)
                else:
                    val_out = model(data.x)
                    
                val_loss = criterion(val_out[data.val_mask], data.y[data.val_mask]).item()
                
                # Save best model state based on validation loss
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_model_state = {k: v.clone() for k, v in model.state_dict().items()}
                    
    # Restore the best model weights
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
        
    print(f"✅ {model_name} training complete. Best Val Loss: {best_val_loss:.4f}")
    return model

# --- Evaluation Function ---
def evaluate_model(model, data, model_name):
    model.eval()
    with torch.no_grad():
        if isinstance(model, GCNModel):
            pred = model(data.x, data.edge_index)
        else:
            pred = model(data.x)
            
        true = data.y
        mask = data.test_mask
        
        pred_masked = pred[mask]
        true_masked = true[mask]
        
        mae_val = mae(pred_masked, true_masked)
        rmse_val = rmse(pred_masked, true_masked)
        r2_val = r2(pred_masked, true_masked)
        
        print(f"\n📊 {model_name} Test Metrics:")
        print(f"   MAE  (Mean Absolute Error): {mae_val:.4f} hours")
        print(f"   RMSE (Root Mean Sq Error):  {rmse_val:.4f} hours")
        print(f"   R²   (Coefficient Det.):    {r2_val:.4f}")
        
        return mae_val, rmse_val, r2_val

# --- Main Execution ---
if __name__ == "__main__":
    print("Loading graph data for training...")
    data = load_graph_from_neo4j()
    
    in_channels = data.num_node_features
    hidden_channels = 16
    
    # Ensure models directory exists
    os.makedirs("models", exist_ok=True)
    
    # 1. Train and Evaluate Baseline MLP
    mlp_model = BaselineMLP(in_channels, hidden_channels)
    mlp_model = train_model(mlp_model, data, "Baseline MLP")
    evaluate_model(mlp_model, data, "Baseline MLP")
    torch.save(mlp_model.state_dict(), "models/baseline_mlp.pth")
    print("💾 Saved Baseline MLP to models/baseline_mlp.pth")
    
    # 2. Train and Evaluate GCN Model
    gcn_model = GCNModel(in_channels, hidden_channels)
    gcn_model = train_model(gcn_model, data, "GCN Model")
    evaluate_model(gcn_model, data, "GCN Model")
    torch.save(gcn_model.state_dict(), "models/gcn_model.pth")
    print("💾 Saved GCN Model to models/gcn_model.pth")
    
    print("\n🎉 All models trained and saved successfully!")
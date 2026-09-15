# backend/tests/test_gnn_data_loader.py
import pytest
from unittest.mock import patch, MagicMock
import torch
from gnn_data_loader import load_graph_from_neo4j, NODE_TYPE_MAP, RISK_MAP

class TestLoadGraphFromNeo4j:
    @patch('gnn_data_loader.get_db')
    def test_load_graph_with_mock_data(self, mock_get_db):
        """Test loading graph with mocked Neo4j data."""
        # Setup mock driver and session
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_get_db.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock node data (10 nodes for clean 60/20/20 split)
        mock_node_records = [
            {'neo_id': f'node{i}', 'node_type': 'Country' if i % 2 == 0 else 'Port', 'node_id': i, 'risk_level': 'LOW', 'risk_score': 0.33}
            for i in range(10)
        ]
        
        # Mock edge data
        mock_edge_records = [
            {'source_id': f'node{i}', 'target_id': f'node{i+1}'}
            for i in range(9)
        ]
        
        # Configure mock session.run() to return different results based on query
        def mock_run(query, **kwargs):
            mock_result = MagicMock()
            if 'MATCH (n)' in query:
                mock_result.data.return_value = mock_node_records
            elif 'MATCH (a)-[r]->(b)' in query:
                mock_result.data.return_value = mock_edge_records
            return mock_result
        
        mock_session.run.side_effect = mock_run
        
        # Execute the function
        data = load_graph_from_neo4j()
        
        # Assertions
        assert data.num_nodes == 10
        assert data.num_edges == 9
        assert data.x.shape == (10, 8)  # 10 nodes, 8 features (6 one-hot + 1 degree + 1 risk)
        assert data.edge_index.shape == (2, 9)  # 9 edges, 2 rows (source, target)
        assert data.y.shape == (10,)  # 10 target values
        
        # Check train/val/test masks (60% = 6, 20% = 2, 20% = 2)
        assert data.train_mask.sum().item() == 6
        assert data.val_mask.sum().item() == 2
        assert data.test_mask.sum().item() == 2
        
        # Check metadata
        assert 'node0' in data.idx_to_neo_id.values()
        assert 'node9' in data.idx_to_neo_id.values()

    @patch('gnn_data_loader.get_db')
    def test_load_graph_handles_missing_risk_level(self, mock_get_db):
        """Test that missing risk_level defaults to 0.0."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_get_db.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock node data with None risk_level
        mock_node_records = [
            {'neo_id': 'node1', 'node_type': 'Country', 'node_id': 1, 'risk_level': None, 'risk_score': None},
        ]
        
        mock_edge_records = []
        
        def mock_run(query, **kwargs):
            mock_result = MagicMock()
            if 'MATCH (n)' in query:
                mock_result.data.return_value = mock_node_records
            elif 'MATCH (a)-[r]->(b)' in query:
                mock_result.data.return_value = mock_edge_records
            return mock_result
        
        mock_session.run.side_effect = mock_run
        
        data = load_graph_from_neo4j()
        
        # Check that risk score is 0.0 (from RISK_MAP[None])
        assert data.x[0, -1].item() == 0.0  # Last feature is risk score

    @patch('gnn_data_loader.get_db')
    def test_load_graph_handles_unknown_node_type(self, mock_get_db):
        """Test that unknown node types are clamped to valid range."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_get_db.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        mock_node_records = [
            {'neo_id': 'node1', 'node_type': 'UnknownType', 'node_id': 1, 'risk_level': 'LOW', 'risk_score': 0.33},
        ]
        
        mock_edge_records = []
        
        def mock_run(query, **kwargs):
            mock_result = MagicMock()
            if 'MATCH (n)' in query:
                mock_result.data.return_value = mock_node_records
            elif 'MATCH (a)-[r]->(b)' in query:
                mock_result.data.return_value = mock_edge_records
            return mock_result
        
        mock_session.run.side_effect = mock_run
        
        # Should not raise an error
        data = load_graph_from_neo4j()
        assert data.num_nodes == 1

    @patch('gnn_data_loader.get_db')
    def test_load_graph_raises_error_on_db_failure(self, mock_get_db):
        """Test that database connection failure raises RuntimeError."""
        mock_get_db.side_effect = Exception("Connection failed")
        
        with pytest.raises(RuntimeError, match="Database connection failed"):
            load_graph_from_neo4j()
# backend/tests/conftest.py
import sys
import os
import pytest
from unittest.mock import MagicMock

# Add the backend directory to sys.path so tests can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver for testing without a live database."""
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    return mock_driver, mock_session
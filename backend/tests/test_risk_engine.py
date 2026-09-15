# backend/tests/test_risk_engine.py
import pytest
from risk_engine import calculate_risk

class TestCalculateRisk:
    def test_no_disruptions_returns_low_risk(self):
        """Test that no disruptions results in LOW risk."""
        risk_level, risk_score = calculate_risk([])
        assert risk_level == "LOW"
        assert risk_score == 0.1

    def test_single_disruption_returns_medium_risk(self):
        """Test that one disruption results in MEDIUM risk."""
        risk_level, risk_score = calculate_risk(["strike"])
        assert risk_level == "MEDIUM"
        assert risk_score == 0.5

    def test_two_disruptions_returns_high_risk(self):
        """Test that two disruptions results in HIGH risk."""
        risk_level, risk_score = calculate_risk(["strike", "fire"])
        assert risk_level == "HIGH"
        assert risk_score == 0.8

    def test_three_or_more_disruptions_returns_high_risk(self):
        """Test that three or more disruptions results in HIGH risk with higher score."""
        risk_level, risk_score = calculate_risk(["strike", "fire", "flood"])
        assert risk_level == "HIGH"
        assert risk_score == 0.95

    def test_many_disruptions_returns_high_risk(self):
        """Test that many disruptions still results in HIGH risk."""
        disruptions = ["strike", "fire", "flood", "earthquake", "pandemic"]
        risk_level, risk_score = calculate_risk(disruptions)
        assert risk_level == "HIGH"
        assert risk_score == 0.95
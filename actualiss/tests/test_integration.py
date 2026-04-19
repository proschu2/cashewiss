"""
Integration tests for actualiss Docker workflow.

Tests the complete workflow: upload → process → import.
"""

import pytest
import requests
import time
import csv
import tempfile
import os
from pathlib import Path
from io import StringIO


class TestActualissIntegration:
    """Test the actualiss integration with Actual Budget."""

    @pytest.fixture(scope="class")
    def actual_budget_base_url(self):
        """Base URL for Actual Budget service."""
        return "http://localhost:5006"

    @pytest.fixture(scope="class")
    def actualiss_base_url(self):
        """Base URL for actualiss service."""
        return "http://localhost:8501"

    @pytest.fixture(scope="class")
    def wait_for_services(self, actual_budget_base_url, actualiss_base_url):
        """Wait for both services to be healthy."""
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{actual_budget_base_url}/health", timeout=5)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)
        else:
            raise Exception("Actual Budget service did not become healthy")

        for attempt in range(max_attempts):
            try:
                response = requests.get(
                    f"{actualiss_base_url}/_stcore/health", timeout=5
                )
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)
        else:
            raise Exception("actualiss service did not become healthy")

    @pytest.fixture
    def sample_transaction_data(self):
        """Create sample transaction data for testing."""
        csv_data = """Date,Amount,Category,Title,Note,Account
23/03/2025 00:00,-50,Groceries,Fruits and Vegetables,Paid with cash,Sanzio
24/03/2025 00:00,-25,DINING,Restaurant Dinner,Family dinner,Sanzio
25/03/2025 00:00,-100,SHOPPING,Clothing Store,New clothes,Sanzio
"""
        return csv_data

    def test_actual_budget_health(self, actual_budget_base_url, wait_for_services):
        """Test that Actual Budget service is healthy."""
        response = requests.get(f"{actual_budget_base_url}/health")
        assert response.status_code == 200

    def test_actualiss_health(self, actualiss_base_url, wait_for_services):
        """Test that actualiss service is healthy."""
        response = requests.get(f"{actualiss_base_url}/_stcore/health")
        assert response.status_code == 200

    def test_upload_endpoint_exists(self, actualiss_base_url, wait_for_services):
        """Test that upload endpoint exists."""
        response = requests.get(f"{actualiss_base_url}/")
        assert response.status_code == 200
        assert "file upload" in response.text.lower()

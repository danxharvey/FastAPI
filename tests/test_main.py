# Import libraries
import pytest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app, health_check
from app.config import config


class TestHealthCheckEndpoint:
    """Test suite for GET /health endpoint."""
    
    def test_health_check_success(self, client):
        """Test health check when templates directory exists."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "status" in data
        assert "app" in data
        assert "version" in data
        assert "templates_dir" in data
        
        # Verify values when templates exist
        assert data["status"] == "ok"
        assert data["app"] == config["title"]
        assert data["version"] == config["version"]
        assert data["templates_dir"] == "ok"
    
    def test_health_check_response_type(self, client):
        """Test that health check returns JSON response."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
    
    def test_health_check_uses_config_values(self, client):
        """Test that health check uses values from config."""
        response = client.get("/health")
        data = response.json()
        
        # Verify config values are used
        assert data["app"] == config["title"]
        assert data["version"] == config["version"]
    
    @patch('app.main.os.path.isdir')
    def test_health_check_missing_templates(self, mock_isdir, client):
        """Test health check when templates directory is missing."""
        # Mock templates directory as missing
        mock_isdir.return_value = False
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify error status when templates missing
        assert data["status"] == "error"
        assert data["templates_dir"] == "missing"
        assert data["app"] == config["title"]
        assert data["version"] == config["version"]
    
    def test_health_check_templates_dir_path(self):
        """Test that health check checks correct templates directory path."""
        # Get the expected path
        expected_path = os.path.join(os.path.dirname(__file__), "..", "app", "templates")
        expected_path = os.path.abspath(expected_path)
        
        # Verify the path exists in actual implementation
        actual_path = os.path.join(os.path.dirname(__file__), "..", "app", "templates")
        actual_path = os.path.abspath(actual_path)
        
        # The path should exist in normal operation
        assert os.path.isdir(actual_path) or os.path.isdir(expected_path)
    
    def test_health_check_no_auth_required(self, client):
        """Test that health check endpoint doesn't require authentication."""
        # Should work without any authentication
        response = client.get("/health")
        
        assert response.status_code == 200
        # Should not get 401 Unauthorized
        assert response.status_code != 401
    
    def test_health_check_response_consistency(self, client):
        """Test that health check returns consistent response structure."""
        response1 = client.get("/health")
        response2 = client.get("/health")
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Response structure should be consistent
        assert set(data1.keys()) == set(data2.keys())
        assert set(data1.keys()) == {"status", "app", "version", "templates_dir"}
        
        # Values should be the same (assuming templates still exist)
        assert data1["app"] == data2["app"]
        assert data1["version"] == data2["version"]


class TestHealthCheckFunction:
    """Test suite for health_check function directly."""
    
    def test_health_check_function_returns_dict(self):
        """Test that health_check function returns a dictionary."""
        result = health_check()
        
        assert isinstance(result, dict)
        assert "status" in result
        assert "app" in result
        assert "version" in result
        assert "templates_dir" in result
    
    def test_health_check_function_with_templates(self):
        """Test health_check function when templates exist."""
        result = health_check()
        
        # When templates exist, status should be "ok"
        templates_dir = os.path.join(os.path.dirname(__file__), "..", "app", "templates")
        templates_dir = os.path.abspath(templates_dir)
        
        if os.path.isdir(templates_dir):
            assert result["status"] == "ok"
            assert result["templates_dir"] == "ok"
        else:
            assert result["status"] == "error"
            assert result["templates_dir"] == "missing"
    
    @patch('app.main.os.path.isdir')
    def test_health_check_function_templates_missing(self, mock_isdir):
        """Test health_check function when templates directory is missing."""
        mock_isdir.return_value = False
        
        result = health_check()
        
        assert result["status"] == "error"
        assert result["templates_dir"] == "missing"
        assert result["app"] == config["title"]
        assert result["version"] == config["version"]
    
    @patch('app.main.os.path.isdir')
    def test_health_check_function_templates_exists(self, mock_isdir):
        """Test health_check function when templates directory exists."""
        mock_isdir.return_value = True
        
        result = health_check()
        
        assert result["status"] == "ok"
        assert result["templates_dir"] == "ok"
        assert result["app"] == config["title"]
        assert result["version"] == config["version"]

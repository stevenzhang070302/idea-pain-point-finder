#!/usr/bin/env python3
"""
Test suite for Phase 3 Backend API
Tests all FastAPI endpoints and database functionality
"""

import pytest
import requests
import json
import time
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Test configuration
API_BASE = "http://localhost:8000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpass123"
TEST_TOPIC = "test developers"

class TestBackendAPI:
    """Test suite for Backend API functionality"""
    
    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        cls.test_user_id = None
        cls.test_search_id = None
        cls.test_alert_id = None
        cls.analysis_id = None
        
    def test_00_health_check(self):
        """Test API health check endpoint"""
        print("\n🔍 Testing API health check...")
        try:
            response = requests.get(f"{API_BASE}/")
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Reddit Pain Finder API v3.0"
            assert data["phase"] == "3"
            assert "Interactive Dashboard" in data["features"]
            print("✅ Health check passed")
        except requests.exceptions.ConnectionError:
            pytest.fail("❌ Backend server is not running. Please start the backend first.")
    
    def test_01_user_registration(self):
        """Test user registration"""
        print("\n🔍 Testing user registration...")
        
        payload = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        
        response = requests.post(f"{API_BASE}/auth/register", json=payload)
        
        # Handle case where user already exists
        if response.status_code == 400:
            print("⚠️ User already exists, continuing with existing user")
            return
            
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert data["message"] == "User registered successfully"
        TestBackendAPI.test_user_id = data["user_id"]
        print(f"✅ User registered with ID: {TestBackendAPI.test_user_id}")
    
    def test_02_user_login(self):
        """Test user login"""
        print("\n🔍 Testing user login...")
        
        payload = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        
        response = requests.post(f"{API_BASE}/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert data["message"] == "Login successful"
        TestBackendAPI.test_user_id = data["user_id"]
        print(f"✅ User logged in with ID: {TestBackendAPI.test_user_id}")
    
    def test_03_invalid_login(self):
        """Test invalid login credentials"""
        print("\n🔍 Testing invalid login...")
        
        payload = {
            "email": TEST_USER_EMAIL,
            "password": "wrongpassword"
        }
        
        response = requests.post(f"{API_BASE}/auth/login", json=payload)
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Invalid credentials"
        print("✅ Invalid login properly rejected")
    
    def test_04_start_analysis(self):
        """Test starting a pain point analysis"""
        print("\n🔍 Testing analysis start...")
        
        payload = {
            "topic": TEST_TOPIC,
            "save_results": True
        }
        
        response = requests.post(f"{API_BASE}/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["topic"] == TEST_TOPIC
        assert data["status"] in ["processing", "completed"]
        TestBackendAPI.analysis_id = data["id"]
        print(f"✅ Analysis started with ID: {TestBackendAPI.analysis_id}")
        print(f"   Status: {data['status']}")
    
    def test_05_get_analysis_status(self):
        """Test getting analysis status"""
        print("\n🔍 Testing analysis status check...")
        
        if not TestBackendAPI.analysis_id:
            pytest.skip("No analysis ID available")
        
        # Wait a bit for processing
        time.sleep(2)
        
        response = requests.get(f"{API_BASE}/analyze/{TestBackendAPI.analysis_id}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        print(f"✅ Analysis status: {data['status']}")
        
        if data["status"] == "completed":
            assert "results" in data
            results = data["results"]
            assert "clusters" in results
            assert "analysis_summary" in results
            print(f"   Found {len(results['clusters'])} clusters")
    
    def test_06_save_search(self):
        """Test saving a search"""
        print("\n🔍 Testing save search...")
        
        if not TestBackendAPI.test_user_id:
            pytest.skip("No user ID available")
        
        payload = {
            "user_id": TestBackendAPI.test_user_id,
            "topic": TEST_TOPIC,
            "keywords": "test keywords"
        }
        
        response = requests.post(f"{API_BASE}/searches", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["message"] == "Search saved successfully"
        TestBackendAPI.test_search_id = data["id"]
        print(f"✅ Search saved with ID: {TestBackendAPI.test_search_id}")
    
    def test_07_get_user_searches(self):
        """Test getting user's saved searches"""
        print("\n🔍 Testing get user searches...")
        
        if not TestBackendAPI.test_user_id:
            pytest.skip("No user ID available")
        
        response = requests.get(f"{API_BASE}/searches/{TestBackendAPI.test_user_id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            search = data[0]
            assert "id" in search
            assert "topic" in search
            assert search["topic"] == TEST_TOPIC
            print(f"✅ Found {len(data)} saved searches")
        else:
            print("⚠️ No saved searches found")
    
    def test_08_create_alert_subscription(self):
        """Test creating an alert subscription"""
        print("\n🔍 Testing alert subscription creation...")
        
        if not TestBackendAPI.test_user_id or not TestBackendAPI.test_search_id:
            pytest.skip("No user ID or search ID available")
        
        payload = {
            "user_id": TestBackendAPI.test_user_id,
            "search_id": TestBackendAPI.test_search_id,
            "email": TEST_USER_EMAIL,
            "frequency": "weekly",
            "min_desperation_score": 7
        }
        
        response = requests.post(f"{API_BASE}/alerts", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["message"] == "Alert subscription created successfully"
        TestBackendAPI.test_alert_id = data["id"]
        print(f"✅ Alert subscription created with ID: {TestBackendAPI.test_alert_id}")
    
    def test_09_get_user_alerts(self):
        """Test getting user's alert subscriptions"""
        print("\n🔍 Testing get user alerts...")
        
        if not TestBackendAPI.test_user_id:
            pytest.skip("No user ID available")
        
        response = requests.get(f"{API_BASE}/alerts/{TestBackendAPI.test_user_id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            alert = data[0]
            assert "id" in alert
            assert "email" in alert
            assert alert["email"] == TEST_USER_EMAIL
            print(f"✅ Found {len(data)} alert subscriptions")
        else:
            print("⚠️ No alert subscriptions found")
    
    def test_10_csv_export(self):
        """Test CSV export functionality"""
        print("\n🔍 Testing CSV export...")
        
        if not TestBackendAPI.analysis_id:
            pytest.skip("No analysis ID available")
        
        response = requests.get(f"{API_BASE}/topics/{TestBackendAPI.analysis_id}/export.csv")
        
        if response.status_code == 404:
            print("⚠️ Analysis results not found, skipping CSV export test")
            return
            
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        
        # Check CSV content
        csv_content = response.content.decode('utf-8')
        lines = csv_content.split('\n')
        assert len(lines) >= 2  # At least header + one data row
        
        # Check header
        header = lines[0]
        expected_columns = ['Cluster ID', 'Topic', 'Problem Category', 'Frequency']
        for col in expected_columns:
            assert col in header
        
        print("✅ CSV export successful")
        print(f"   Exported {len(lines)-2} data rows")

def run_backend_tests():
    """Run all backend tests"""
    print("🚀 Starting Phase 3 Backend API Tests")
    print("="*50)
    
    # Check if backend is running
    try:
        response = requests.get(f"{API_BASE}/", timeout=5)
        if response.status_code != 200:
            print("❌ Backend server is not responding correctly")
            return False
    except requests.exceptions.RequestException:
        print("❌ Backend server is not running!")
        print("   Please start the backend first: cd backend && python backend.py")
        return False
    
    # Run tests
    test_class = TestBackendAPI()
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    test_methods.sort()
    
    passed = 0
    failed = 0
    
    for method_name in test_methods:
        try:
            method = getattr(test_class, method_name)
            method()
            passed += 1
        except Exception as e:
            print(f"❌ {method_name} failed: {str(e)}")
            failed += 1
    
    print("\n" + "="*50)
    print(f"🏁 Backend Tests Complete: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All backend tests passed!")
        return True
    else:
        print("⚠️ Some backend tests failed")
        return False

if __name__ == "__main__":
    success = run_backend_tests()
    sys.exit(0 if success else 1) 
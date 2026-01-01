"""
Backend API Tests for Faithful Threads Design Management
Tests: Design CRUD operations, Design filtering by category, Admin design upload
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@faithfulthreads.com"
ADMIN_PASSWORD = "admin123"


class TestDesignAPI:
    """Design endpoint tests for the 3-step purchase flow"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Admin authentication failed")
    
    def test_get_designs_empty_or_list(self):
        """Test GET /api/designs returns list (may be empty initially)"""
        response = requests.get(f"{BASE_URL}/api/designs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_designs_filter_by_apparel_category(self):
        """Test GET /api/designs?category=apparel filters correctly"""
        response = requests.get(f"{BASE_URL}/api/designs?category=apparel")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned designs should be apparel category
        for design in data:
            assert design["category"] == "apparel"
    
    def test_get_designs_filter_by_hats_category(self):
        """Test GET /api/designs?category=hats filters correctly"""
        response = requests.get(f"{BASE_URL}/api/designs?category=hats")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned designs should be hats category
        for design in data:
            assert design["category"] == "hats"
    
    def test_create_design_authenticated(self, auth_token):
        """Test POST /api/admin/designs creates a new design"""
        design_data = {
            "name": "TEST_Faith Over Fear Cross",
            "category": "apparel",
            "image_url": "https://via.placeholder.com/300x300?text=Test+Design"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/designs",
            json=design_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "design_id" in data
        assert data["name"] == design_data["name"]
        assert data["category"] == design_data["category"]
        assert data["image_url"] == design_data["image_url"]
        assert "created_at" in data
        
        # Store design_id for cleanup
        self.__class__.created_design_id = data["design_id"]
    
    def test_create_design_unauthenticated(self):
        """Test POST /api/admin/designs without auth returns 401"""
        design_data = {
            "name": "Unauthorized Design",
            "category": "apparel",
            "image_url": "https://via.placeholder.com/300"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/designs", json=design_data)
        assert response.status_code == 401
    
    def test_get_single_design(self, auth_token):
        """Test GET /api/designs/{design_id} returns single design"""
        # First create a design
        design_data = {
            "name": "TEST_Single Design Test",
            "category": "hats",
            "image_url": "https://via.placeholder.com/300x300?text=Hat+Design"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/designs",
            json=design_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert create_response.status_code == 200
        design_id = create_response.json()["design_id"]
        
        # Get the design
        response = requests.get(f"{BASE_URL}/api/designs/{design_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["design_id"] == design_id
        assert data["name"] == design_data["name"]
        assert data["category"] == design_data["category"]
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/admin/designs/{design_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
    
    def test_get_nonexistent_design(self):
        """Test GET /api/designs/{design_id} with invalid ID returns 404"""
        response = requests.get(f"{BASE_URL}/api/designs/nonexistent_design_id")
        assert response.status_code == 404
    
    def test_delete_design_authenticated(self, auth_token):
        """Test DELETE /api/admin/designs/{design_id} deletes design"""
        # First create a design to delete
        design_data = {
            "name": "TEST_Design To Delete",
            "category": "apparel",
            "image_url": "https://via.placeholder.com/300"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/designs",
            json=design_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert create_response.status_code == 200
        design_id = create_response.json()["design_id"]
        
        # Delete the design
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/designs/{design_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert delete_response.status_code == 200
        
        # Verify design is deleted
        get_response = requests.get(f"{BASE_URL}/api/designs/{design_id}")
        assert get_response.status_code == 404
    
    def test_delete_design_unauthenticated(self, auth_token):
        """Test DELETE /api/admin/designs without auth returns 401"""
        # First create a design
        design_data = {
            "name": "TEST_Design For Unauth Delete",
            "category": "apparel",
            "image_url": "https://via.placeholder.com/300"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/designs",
            json=design_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        design_id = create_response.json()["design_id"]
        
        # Try to delete without auth
        delete_response = requests.delete(f"{BASE_URL}/api/admin/designs/{design_id}")
        assert delete_response.status_code == 401
        
        # Cleanup with auth
        requests.delete(
            f"{BASE_URL}/api/admin/designs/{design_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
    
    def test_delete_nonexistent_design(self, auth_token):
        """Test DELETE /api/admin/designs with invalid ID returns 404"""
        response = requests.delete(
            f"{BASE_URL}/api/admin/designs/nonexistent_design_id",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404
    
    def test_update_design_authenticated(self, auth_token):
        """Test PUT /api/admin/designs/{design_id} updates design"""
        # First create a design
        design_data = {
            "name": "TEST_Design To Update",
            "category": "apparel",
            "image_url": "https://via.placeholder.com/300"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/designs",
            json=design_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert create_response.status_code == 200
        design_id = create_response.json()["design_id"]
        
        # Update the design
        update_data = {
            "name": "TEST_Updated Design Name",
            "category": "hats",
            "image_url": "https://via.placeholder.com/400"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/admin/designs/{design_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert update_response.status_code == 200
        data = update_response.json()
        
        assert data["name"] == update_data["name"]
        assert data["category"] == update_data["category"]
        assert data["image_url"] == update_data["image_url"]
        
        # Verify update persisted
        get_response = requests.get(f"{BASE_URL}/api/designs/{design_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == update_data["name"]
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/admin/designs/{design_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
    
    def test_admin_get_designs(self, auth_token):
        """Test GET /api/admin/designs returns all designs for admin"""
        response = requests.get(
            f"{BASE_URL}/api/admin/designs",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_admin_get_designs_unauthenticated(self):
        """Test GET /api/admin/designs without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/admin/designs")
        assert response.status_code == 401


class TestProductForDesignFlow:
    """Test product endpoint for design flow"""
    
    def test_get_product_for_design_flow(self):
        """Test fetching product prod_9f6e866cdfef for design flow testing"""
        response = requests.get(f"{BASE_URL}/api/products/prod_9f6e866cdfef")
        # Product may or may not exist, just verify API works
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "product_id" in data
            assert "category" in data
            assert "colors" in data
            assert "sizes" in data
    
    def test_get_tshirt_product_for_apparel_design(self):
        """Test fetching a T-shirt product for apparel design flow"""
        response = requests.get(f"{BASE_URL}/api/products?category=tshirts")
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            product = data[0]
            assert product["category"] == "tshirts"
            # T-shirts should use apparel designs
    
    def test_get_hat_product_for_hat_design(self):
        """Test fetching a hat product for hat design flow"""
        response = requests.get(f"{BASE_URL}/api/products?category=hats")
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            product = data[0]
            assert product["category"] == "hats"
            # Hats should use hat designs


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Admin authentication failed")
    
    def test_cleanup_test_designs(self, auth_token):
        """Cleanup any TEST_ prefixed designs"""
        response = requests.get(
            f"{BASE_URL}/api/admin/designs",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        if response.status_code == 200:
            designs = response.json()
            for design in designs:
                if design["name"].startswith("TEST_"):
                    requests.delete(
                        f"{BASE_URL}/api/admin/designs/{design['design_id']}",
                        headers={"Authorization": f"Bearer {auth_token}"}
                    )
        
        # This test always passes - it's just for cleanup
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

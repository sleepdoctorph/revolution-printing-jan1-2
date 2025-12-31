"""
Backend API Tests for Faithful Threads E-commerce Platform
Tests: Authentication, Products, Admin Stats, Category Filtering
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@faithfulthreads.com"
ADMIN_PASSWORD = "admin123"


class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_health_endpoint(self):
        """Test API health endpoint returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_root_endpoint(self):
        """Test API root endpoint returns version info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Faithful Threads" in data["message"]


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "user" in data
        assert data["token_type"] == "bearer"
        
        # Validate user data
        user = data["user"]
        assert user["email"] == ADMIN_EMAIL
        assert user["is_admin"] == True
        assert "user_id" in user
        assert "name" in user
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_login_invalid_email_format(self):
        """Test login with invalid email format returns 422"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "not-an-email",
            "password": "password123"
        })
        assert response.status_code == 422


class TestProducts:
    """Product endpoint tests"""
    
    def test_get_all_products(self):
        """Test fetching all products returns 33 products"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        data = response.json()
        
        # Verify total count (12 original + 1 existing Gildan + 20 new Gildan)
        assert len(data) == 33
        
        # Verify product structure
        product = data[0]
        assert "product_id" in product
        assert "name" in product
        assert "description" in product
        assert "price" in product
        assert "category" in product
        assert "images" in product
        assert "colors" in product
        assert "sizes" in product
        assert "brand" in product
        assert "is_blank" in product
        assert "stock" in product
        assert "featured" in product
    
    def test_filter_products_by_category_tshirts(self):
        """Test filtering products by T-Shirts category"""
        response = requests.get(f"{BASE_URL}/api/products?category=tshirts")
        assert response.status_code == 200
        data = response.json()
        
        # Should have 24 t-shirts (3 original + 1 test + 20 Gildan)
        assert len(data) == 24
        
        # Verify all products are t-shirts
        for product in data:
            assert product["category"] == "tshirts"
    
    def test_filter_products_by_category_hoodies(self):
        """Test filtering products by Hoodies category"""
        response = requests.get(f"{BASE_URL}/api/products?category=hoodies")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        for product in data:
            assert product["category"] == "hoodies"
    
    def test_filter_products_by_category_hats(self):
        """Test filtering products by Hats category"""
        response = requests.get(f"{BASE_URL}/api/products?category=hats")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        for product in data:
            assert product["category"] == "hats"
    
    def test_filter_products_by_category_mugs(self):
        """Test filtering products by Mugs category"""
        response = requests.get(f"{BASE_URL}/api/products?category=mugs")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        for product in data:
            assert product["category"] == "mugs"
    
    def test_filter_blank_products(self):
        """Test filtering blank products"""
        response = requests.get(f"{BASE_URL}/api/products?is_blank=true")
        assert response.status_code == 200
        data = response.json()
        
        # All returned products should be blank
        for product in data:
            assert product["is_blank"] == True
    
    def test_get_single_product(self):
        """Test fetching a single product by ID"""
        # First get all products to get a valid ID
        all_response = requests.get(f"{BASE_URL}/api/products")
        products = all_response.json()
        product_id = products[0]["product_id"]
        
        # Fetch single product
        response = requests.get(f"{BASE_URL}/api/products/{product_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["product_id"] == product_id
        assert "name" in data
        assert "price" in data
    
    def test_get_nonexistent_product(self):
        """Test fetching non-existent product returns 404"""
        response = requests.get(f"{BASE_URL}/api/products/nonexistent_id")
        assert response.status_code == 404


class TestAdminStats:
    """Admin statistics endpoint tests"""
    
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
    
    def test_admin_stats_authenticated(self, auth_token):
        """Test admin stats endpoint with valid authentication"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify stats structure
        assert "total_products" in data
        assert "total_orders" in data
        assert "total_customers" in data
        assert "pending_orders" in data
        assert "total_revenue" in data
        
        # Verify product count
        assert data["total_products"] == 33
        
        # Verify data types
        assert isinstance(data["total_products"], int)
        assert isinstance(data["total_orders"], int)
        assert isinstance(data["total_customers"], int)
        assert isinstance(data["pending_orders"], int)
        assert isinstance(data["total_revenue"], (int, float))
    
    def test_admin_stats_unauthenticated(self):
        """Test admin stats endpoint without authentication returns 401"""
        response = requests.get(f"{BASE_URL}/api/admin/stats")
        assert response.status_code == 401


class TestAdminOrders:
    """Admin orders endpoint tests"""
    
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
    
    def test_admin_orders_authenticated(self, auth_token):
        """Test admin orders endpoint with valid authentication"""
        response = requests.get(
            f"{BASE_URL}/api/admin/orders",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should be a list
        assert isinstance(data, list)
        
        # If orders exist, verify structure
        if len(data) > 0:
            order = data[0]
            assert "order_id" in order
            assert "user_id" in order
            assert "items" in order
            assert "total_amount" in order
            assert "status" in order
    
    def test_admin_orders_unauthenticated(self):
        """Test admin orders endpoint without authentication returns 401"""
        response = requests.get(f"{BASE_URL}/api/admin/orders")
        assert response.status_code == 401


class TestAdminCustomers:
    """Admin customers endpoint tests"""
    
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
    
    def test_admin_customers_authenticated(self, auth_token):
        """Test admin customers endpoint with valid authentication"""
        response = requests.get(
            f"{BASE_URL}/api/admin/customers",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should be a list
        assert isinstance(data, list)
        
        # If customers exist, verify structure (no password field)
        if len(data) > 0:
            customer = data[0]
            assert "user_id" in customer
            assert "email" in customer
            assert "password" not in customer  # Password should not be exposed


class TestPaymentConfig:
    """Payment configuration endpoint tests"""
    
    def test_payment_config(self):
        """Test payment config endpoint returns Square configuration"""
        response = requests.get(f"{BASE_URL}/api/payments/config")
        assert response.status_code == 200
        data = response.json()
        
        # Verify config structure
        assert "applicationId" in data
        assert "locationId" in data
        assert "environment" in data


class TestContactForm:
    """Contact form endpoint tests"""
    
    def test_submit_contact_form(self):
        """Test submitting contact form"""
        response = requests.post(f"{BASE_URL}/api/contact", json={
            "name": "TEST_Contact User",
            "email": "test@example.com",
            "subject": "Test Subject",
            "message": "This is a test message"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "contact_id" in data
    
    def test_submit_contact_form_invalid_email(self):
        """Test submitting contact form with invalid email"""
        response = requests.post(f"{BASE_URL}/api/contact", json={
            "name": "Test User",
            "email": "invalid-email",
            "subject": "Test Subject",
            "message": "This is a test message"
        })
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

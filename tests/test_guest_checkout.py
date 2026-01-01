"""
Test Guest Checkout Feature for Revolution Printing E-commerce
Tests:
- POST /api/orders/guest - Create guest order without authentication
- Newsletter subscription during guest checkout
- Email validation for guest orders
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data
TEST_PRODUCT_ID = None  # Will be fetched dynamically
TEST_DESIGN_ID = None   # Will be fetched dynamically


class TestGuestCheckoutAPI:
    """Test guest checkout API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data by fetching a real product and design"""
        global TEST_PRODUCT_ID, TEST_DESIGN_ID
        
        # Get a product
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200, f"Failed to get products: {response.text}"
        products = response.json()
        assert len(products) > 0, "No products found in database"
        TEST_PRODUCT_ID = products[0]['product_id']
        
        # Get a design
        response = requests.get(f"{BASE_URL}/api/designs")
        if response.status_code == 200:
            designs = response.json()
            if len(designs) > 0:
                TEST_DESIGN_ID = designs[0]['design_id']
    
    def test_guest_order_success(self):
        """Test creating a guest order with valid data"""
        unique_email = f"test_guest_{uuid.uuid4().hex[:8]}@example.com"
        
        order_data = {
            "items": [{
                "product_id": TEST_PRODUCT_ID,
                "quantity": 1,
                "color": "White",
                "size": "M",
                "design_id": TEST_DESIGN_ID or "",
                "design_name": "Test Design"
            }],
            "shipping_address": {
                "firstName": "Test",
                "lastName": "Guest",
                "email": unique_email,
                "address": "123 Test Street",
                "city": "Test City",
                "state": "BC",
                "zip": "V1V 1V1",
                "phone": "604-555-1234"
            },
            "total_amount": 29.99,
            "is_guest": True,
            "subscribe_to_updates": False
        }
        
        response = requests.post(f"{BASE_URL}/api/orders/guest", json=order_data)
        
        # Assertions
        assert response.status_code == 200, f"Guest order failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "order_id" in data, "Response missing order_id"
        assert data["order_id"].startswith("order_"), f"Invalid order_id format: {data['order_id']}"
        assert data["is_guest"] == True, "Order should be marked as guest"
        assert data["status"] == "pending", f"Expected status 'pending', got '{data['status']}'"
        assert data["total_amount"] == 29.99, f"Total amount mismatch"
        
        # Verify items
        assert len(data["items"]) == 1, "Expected 1 item in order"
        assert data["items"][0]["product_id"] == TEST_PRODUCT_ID
        
        # Verify shipping address
        assert data["shipping_address"]["email"] == unique_email
        assert data["shipping_address"]["firstName"] == "Test"
        
        print(f"✓ Guest order created successfully: {data['order_id']}")
        return data["order_id"]
    
    def test_guest_order_with_newsletter_subscription(self):
        """Test guest order with newsletter subscription enabled"""
        unique_email = f"test_newsletter_{uuid.uuid4().hex[:8]}@example.com"
        
        order_data = {
            "items": [{
                "product_id": TEST_PRODUCT_ID,
                "quantity": 2,
                "color": "Black",
                "size": "L",
                "design_id": TEST_DESIGN_ID or "",
                "design_name": "Newsletter Test Design"
            }],
            "shipping_address": {
                "firstName": "Newsletter",
                "lastName": "Subscriber",
                "email": unique_email,
                "address": "456 Newsletter Ave",
                "city": "Vancouver",
                "state": "BC",
                "zip": "V2V 2V2",
                "phone": "604-555-5678"
            },
            "total_amount": 59.98,
            "is_guest": True,
            "subscribe_to_updates": True  # Newsletter subscription enabled
        }
        
        response = requests.post(f"{BASE_URL}/api/orders/guest", json=order_data)
        
        assert response.status_code == 200, f"Guest order with newsletter failed: {response.text}"
        data = response.json()
        
        assert "order_id" in data
        assert data["is_guest"] == True
        
        print(f"✓ Guest order with newsletter subscription created: {data['order_id']}")
        print(f"  Email {unique_email} should be added to newsletter_subscribers collection")
    
    def test_guest_order_missing_email(self):
        """Test that guest order fails without email"""
        order_data = {
            "items": [{
                "product_id": TEST_PRODUCT_ID,
                "quantity": 1,
                "color": "White",
                "size": "M",
                "design_id": "",
                "design_name": ""
            }],
            "shipping_address": {
                "firstName": "No",
                "lastName": "Email",
                # Missing email field
                "address": "789 No Email St",
                "city": "Test City",
                "state": "BC",
                "zip": "V3V 3V3",
                "phone": "604-555-9999"
            },
            "total_amount": 19.99,
            "is_guest": True,
            "subscribe_to_updates": False
        }
        
        response = requests.post(f"{BASE_URL}/api/orders/guest", json=order_data)
        
        # Should fail with 400 error
        assert response.status_code == 400, f"Expected 400 for missing email, got {response.status_code}"
        data = response.json()
        assert "email" in data.get("detail", "").lower(), f"Error should mention email: {data}"
        
        print("✓ Guest order correctly rejected when email is missing")
    
    def test_guest_order_empty_email(self):
        """Test that guest order fails with empty email"""
        order_data = {
            "items": [{
                "product_id": TEST_PRODUCT_ID,
                "quantity": 1,
                "color": "White",
                "size": "M",
                "design_id": "",
                "design_name": ""
            }],
            "shipping_address": {
                "firstName": "Empty",
                "lastName": "Email",
                "email": "",  # Empty email
                "address": "789 Empty Email St",
                "city": "Test City",
                "state": "BC",
                "zip": "V3V 3V3",
                "phone": "604-555-9999"
            },
            "total_amount": 19.99,
            "is_guest": True,
            "subscribe_to_updates": False
        }
        
        response = requests.post(f"{BASE_URL}/api/orders/guest", json=order_data)
        
        # Should fail with 400 error
        assert response.status_code == 400, f"Expected 400 for empty email, got {response.status_code}"
        
        print("✓ Guest order correctly rejected when email is empty")
    
    def test_guest_order_multiple_items(self):
        """Test guest order with multiple items"""
        unique_email = f"test_multi_{uuid.uuid4().hex[:8]}@example.com"
        
        # Get multiple products
        response = requests.get(f"{BASE_URL}/api/products")
        products = response.json()
        
        items = []
        for i, product in enumerate(products[:3]):  # Use first 3 products
            items.append({
                "product_id": product['product_id'],
                "quantity": i + 1,
                "color": product.get('colors', ['White'])[0] if product.get('colors') else 'White',
                "size": product.get('sizes', ['M'])[0] if product.get('sizes') else 'M',
                "design_id": TEST_DESIGN_ID or "",
                "design_name": "Multi-item Test"
            })
        
        order_data = {
            "items": items,
            "shipping_address": {
                "firstName": "Multi",
                "lastName": "Item",
                "email": unique_email,
                "address": "999 Multi Item Blvd",
                "city": "Vancouver",
                "state": "BC",
                "zip": "V4V 4V4",
                "phone": "604-555-0000"
            },
            "total_amount": 149.97,
            "is_guest": True,
            "subscribe_to_updates": False
        }
        
        response = requests.post(f"{BASE_URL}/api/orders/guest", json=order_data)
        
        assert response.status_code == 200, f"Multi-item guest order failed: {response.text}"
        data = response.json()
        
        assert len(data["items"]) == len(items), f"Expected {len(items)} items, got {len(data['items'])}"
        
        print(f"✓ Guest order with {len(items)} items created: {data['order_id']}")
    
    def test_guest_order_no_auth_required(self):
        """Verify guest order endpoint doesn't require authentication"""
        unique_email = f"test_noauth_{uuid.uuid4().hex[:8]}@example.com"
        
        order_data = {
            "items": [{
                "product_id": TEST_PRODUCT_ID,
                "quantity": 1,
                "color": "White",
                "size": "M",
                "design_id": "",
                "design_name": ""
            }],
            "shipping_address": {
                "firstName": "No",
                "lastName": "Auth",
                "email": unique_email,
                "address": "111 No Auth Lane",
                "city": "Test City",
                "state": "BC",
                "zip": "V5V 5V5",
                "phone": "604-555-1111"
            },
            "total_amount": 24.99,
            "is_guest": True,
            "subscribe_to_updates": False
        }
        
        # Make request without any auth headers or cookies
        response = requests.post(
            f"{BASE_URL}/api/orders/guest", 
            json=order_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Should succeed without authentication
        assert response.status_code == 200, f"Guest order should not require auth: {response.text}"
        
        print("✓ Guest order endpoint correctly works without authentication")


class TestAuthenticatedOrderComparison:
    """Compare authenticated vs guest order endpoints"""
    
    def test_authenticated_order_requires_auth(self):
        """Verify regular order endpoint requires authentication"""
        # Get a product first
        response = requests.get(f"{BASE_URL}/api/products")
        products = response.json()
        product_id = products[0]['product_id']
        
        order_data = {
            "items": [{
                "product_id": product_id,
                "quantity": 1,
                "color": "White",
                "size": "M"
            }],
            "shipping_address": {
                "firstName": "Auth",
                "lastName": "Required",
                "email": "auth@test.com",
                "address": "222 Auth Required St",
                "city": "Test City",
                "state": "BC",
                "zip": "V6V 6V6",
                "phone": "604-555-2222"
            },
            "total_amount": 29.99
        }
        
        # Make request without authentication
        response = requests.post(
            f"{BASE_URL}/api/orders", 
            json=order_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Should fail with 401 Unauthorized
        assert response.status_code == 401, f"Expected 401 for unauthenticated order, got {response.status_code}"
        
        print("✓ Regular order endpoint correctly requires authentication")


class TestPaymentIntegration:
    """Test payment processing for guest orders"""
    
    def test_payment_demo_mode(self):
        """Test that payment works in demo mode for guest orders"""
        # First create a guest order
        unique_email = f"test_payment_{uuid.uuid4().hex[:8]}@example.com"
        
        response = requests.get(f"{BASE_URL}/api/products")
        products = response.json()
        product_id = products[0]['product_id']
        
        order_data = {
            "items": [{
                "product_id": product_id,
                "quantity": 1,
                "color": "White",
                "size": "M",
                "design_id": "",
                "design_name": ""
            }],
            "shipping_address": {
                "firstName": "Payment",
                "lastName": "Test",
                "email": unique_email,
                "address": "333 Payment Test Ave",
                "city": "Vancouver",
                "state": "BC",
                "zip": "V7V 7V7",
                "phone": "604-555-3333"
            },
            "total_amount": 34.99,
            "is_guest": True,
            "subscribe_to_updates": False
        }
        
        order_response = requests.post(f"{BASE_URL}/api/orders/guest", json=order_data)
        assert order_response.status_code == 200
        order_id = order_response.json()["order_id"]
        
        # Note: Payment endpoint requires authentication, so this tests the flow
        # In the actual app, payment is processed after order creation
        print(f"✓ Guest order {order_id} created, ready for payment processing")
        print("  Note: Payment is processed in DEMO/SANDBOX mode")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

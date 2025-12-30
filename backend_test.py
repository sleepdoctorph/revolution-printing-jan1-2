import requests
import sys
import json
from datetime import datetime

class FaithfulThreadsAPITester:
    def __init__(self, base_url="https://faithful-threads.preview.emergentagent.com"):
        self.base_url = base_url
        self.user_session = requests.Session()
        self.admin_session = requests.Session()
        self.admin_token = None
        self.user_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, use_cookies=True):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)

        try:
            # Use session for cookie-based auth or individual request for token-based
            if use_cookies:
                if method == 'GET':
                    response = self.session.get(url, headers=test_headers)
                elif method == 'POST':
                    response = self.session.post(url, json=data, headers=test_headers)
                elif method == 'PUT':
                    response = self.session.put(url, json=data, headers=test_headers)
                elif method == 'DELETE':
                    response = self.session.delete(url, headers=test_headers)
            else:
                if method == 'GET':
                    response = requests.get(url, headers=test_headers)
                elif method == 'POST':
                    response = requests.post(url, json=data, headers=test_headers)
                elif method == 'PUT':
                    response = requests.put(url, json=data, headers=test_headers)
                elif method == 'DELETE':
                    response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            if not success:
                details += f", Expected: {expected_status}"
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Response: {response.text[:100]}"

            self.log_test(name, success, details)
            return success, response.json() if success and response.content else {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test basic health endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        self.run_test("API Root", "GET", "", 200)
        self.run_test("Health Check", "GET", "health", 200)

    def test_seed_database(self):
        """Test database seeding"""
        print("\n🔍 Testing Database Seeding...")
        self.run_test("Seed Database", "POST", "seed", 200)

    def test_user_registration(self):
        """Test user registration"""
        print("\n🔍 Testing User Registration...")
        test_user_data = {
            "name": "Test User",
            "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "User Registration", 
            "POST", 
            "auth/register", 
            200, 
            test_user_data
        )
        
        if success and 'access_token' in response:
            self.user_token = response['access_token']
            return test_user_data
        return None

    def test_admin_login(self):
        """Test admin login"""
        print("\n🔍 Testing Admin Login...")
        admin_data = {
            "email": "admin@faithfulthreads.com",
            "password": "admin123"
        }
        
        success, response = self.run_test(
            "Admin Login", 
            "POST", 
            "auth/login", 
            200, 
            admin_data
        )
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            return True
        return False

    def test_user_login(self, user_data):
        """Test user login"""
        print("\n🔍 Testing User Login...")
        if not user_data:
            self.log_test("User Login", False, "No user data available")
            return False
            
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        success, response = self.run_test(
            "User Login", 
            "POST", 
            "auth/login", 
            200, 
            login_data
        )
        
        if success and 'access_token' in response:
            self.user_token = response['access_token']
            return True
        return False

    def test_auth_me(self):
        """Test getting current user info"""
        print("\n🔍 Testing Auth Me Endpoint...")
        if not self.user_token:
            self.log_test("Get Current User", False, "No user token available")
            return
            
        self.run_test("Get Current User", "GET", "auth/me", 200)

    def test_products_endpoints(self):
        """Test product-related endpoints"""
        print("\n🔍 Testing Product Endpoints...")
        
        # Get all products
        self.run_test("Get All Products", "GET", "products", 200)
        
        # Get products by category
        self.run_test("Get T-Shirts", "GET", "products?category=tshirts", 200)
        self.run_test("Get Featured Products", "GET", "products?featured=true", 200)
        self.run_test("Get Blank Products", "GET", "products?is_blank=true", 200)
        
        # Get specific product (we'll use a known product ID from seeded data)
        success, products = self.run_test("Get Products for ID Test", "GET", "products", 200)
        if success and products:
            product_id = products[0]['product_id']
            self.run_test("Get Single Product", "GET", f"products/{product_id}", 200)
        else:
            self.log_test("Get Single Product", False, "No products available for testing")

    def test_admin_products(self):
        """Test admin product management"""
        print("\n🔍 Testing Admin Product Management...")
        
        if not self.admin_token:
            self.log_test("Admin Product Tests", False, "No admin token available")
            return None
            
        # Use session cookies for admin requests since the backend uses cookie-based auth
        # Create a new product
        new_product = {
            "name": "Test Product",
            "description": "A test product for API testing",
            "price": 19.99,
            "category": "tshirts",
            "images": ["https://example.com/test.jpg"],
            "colors": ["Black", "White"],
            "sizes": ["S", "M", "L"],
            "brand": "Test Brand",
            "is_blank": False,
            "stock": 50,
            "featured": False
        }
        
        success, response = self.run_test(
            "Create Product", 
            "POST", 
            "admin/products", 
            200, 
            new_product
        )
        
        if success and 'product_id' in response:
            product_id = response['product_id']
            
            # Update the product
            update_data = {"name": "Updated Test Product", "price": 24.99}
            self.run_test(
                "Update Product", 
                "PUT", 
                f"admin/products/{product_id}", 
                200, 
                update_data
            )
            
            # Delete the product
            self.run_test(
                "Delete Product", 
                "DELETE", 
                f"admin/products/{product_id}", 
                200
            )
            
            return product_id
        
        return None

    def test_orders(self):
        """Test order creation and management"""
        print("\n🔍 Testing Order Management...")
        
        if not self.user_token:
            self.log_test("Order Tests", False, "No user token available")
            return None
            
        # Get products first
        success, products = self.run_test("Get Products for Order", "GET", "products", 200)
        if not success or not products:
            self.log_test("Create Order", False, "No products available")
            return None
            
        # Create an order
        order_data = {
            "items": [{
                "product_id": products[0]['product_id'],
                "quantity": 2,
                "color": "Black",
                "size": "M"
            }],
            "shipping_address": {
                "firstName": "Test",
                "lastName": "User",
                "address": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "zip": "12345",
                "phone": "555-0123"
            },
            "total_amount": 59.98
        }
        
        success, response = self.run_test(
            "Create Order", 
            "POST", 
            "orders", 
            200, 
            order_data
        )
        
        if success and 'order_id' in response:
            order_id = response['order_id']
            
            # Get user orders
            self.run_test("Get User Orders", "GET", "orders", 200)
            
            return order_id
        
        return None

    def test_admin_orders(self, order_id):
        """Test admin order management"""
        print("\n🔍 Testing Admin Order Management...")
        
        if not self.admin_token:
            self.log_test("Admin Order Tests", False, "No admin token available")
            return
            
        # Get all orders
        self.run_test("Get All Orders", "GET", "admin/orders", 200)
        
        # Update order status
        if order_id:
            self.run_test(
                "Update Order Status", 
                "PUT", 
                f"admin/orders/{order_id}/status", 
                200, 
                "shipped"
            )

    def test_payment(self, order_id):
        """Test payment processing"""
        print("\n🔍 Testing Payment Processing...")
        
        if not self.user_token or not order_id:
            self.log_test("Payment Test", False, "No user token or order ID available")
            return
            
        # Test payment config
        self.run_test("Get Payment Config", "GET", "payments/config", 200)
        
        # Process payment (demo mode) - expect this to work in demo mode
        payment_data = {
            "source_id": "demo_payment_token",
            "order_id": order_id,
            "amount": 5998  # $59.98 in cents
        }
        
        # Payment might fail due to Square library issues, so we'll test but not fail the whole suite
        success, response = self.run_test(
            "Process Payment", 
            "POST", 
            "payments/create", 
            200, 
            payment_data
        )
        
        if not success:
            print("  ⚠️  Payment processing failed - likely due to Square library configuration")
            print("  ⚠️  This is expected in demo mode without proper Square setup")

    def test_contact_form(self):
        """Test contact form submission"""
        print("\n🔍 Testing Contact Form...")
        
        contact_data = {
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Test Message",
            "message": "This is a test message from the API test suite."
        }
        
        self.run_test("Submit Contact Form", "POST", "contact", 200, contact_data)

    def test_admin_stats(self):
        """Test admin statistics"""
        print("\n🔍 Testing Admin Statistics...")
        
        if not self.admin_token:
            self.log_test("Admin Stats", False, "No admin token available")
            return
            
        self.run_test("Get Admin Stats", "GET", "admin/stats", 200)
        self.run_test("Get Customers", "GET", "admin/customers", 200)
        self.run_test("Get Contacts", "GET", "admin/contacts", 200)

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Faithful Threads API Tests...")
        print(f"Testing against: {self.base_url}")
        
        # Basic health checks
        self.test_health_check()
        
        # Seed database
        self.test_seed_database()
        
        # Authentication tests
        user_data = self.test_user_registration()
        admin_success = self.test_admin_login()
        user_login_success = self.test_user_login(user_data)
        
        if user_login_success:
            self.test_auth_me()
        
        # Product tests
        self.test_products_endpoints()
        
        if admin_success:
            self.test_admin_products()
            
        # Order tests
        order_id = None
        if user_login_success:
            order_id = self.test_orders()
            
        if admin_success and order_id:
            self.test_admin_orders(order_id)
            
        # Payment tests
        if order_id:
            self.test_payment(order_id)
            
        # Contact form
        self.test_contact_form()
        
        # Admin stats
        if admin_success:
            self.test_admin_stats()
        
        # Print summary
        print(f"\n📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed < self.tests_run:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = FaithfulThreadsAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
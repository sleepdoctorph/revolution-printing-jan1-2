from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Settings
SECRET_KEY = os.environ.get('JWT_SECRET', 'faithful-threads-secret-key-2025')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Square Settings
SQUARE_ACCESS_TOKEN = os.environ.get('SQUARE_ACCESS_TOKEN', '')
SQUARE_LOCATION_ID = os.environ.get('SQUARE_LOCATION_ID', '')
SQUARE_ENVIRONMENT = os.environ.get('SQUARE_ENVIRONMENT', 'sandbox')

app = FastAPI(title="Faithful Threads API")
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ======================== MODELS ========================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    is_admin: bool = False
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    category: str  # tshirts, hoodies, hats, mugs
    images: List[str] = []
    colors: List[str] = []
    sizes: List[str] = []
    brand: str = ""
    is_blank: bool = False
    stock: int = 0
    featured: bool = False

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    images: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    sizes: Optional[List[str]] = None
    brand: Optional[str] = None
    is_blank: Optional[bool] = None
    stock: Optional[int] = None
    featured: Optional[bool] = None

class ProductResponse(BaseModel):
    product_id: str
    name: str
    description: str
    price: float
    category: str
    images: List[str]
    colors: List[str]
    sizes: List[str]
    brand: str
    is_blank: bool
    stock: int
    featured: bool
    created_at: datetime

class CartItem(BaseModel):
    product_id: str
    quantity: int
    color: str = ""
    size: str = ""

class OrderCreate(BaseModel):
    items: List[CartItem]
    shipping_address: dict
    total_amount: float

class OrderResponse(BaseModel):
    order_id: str
    user_id: str
    items: List[dict]
    shipping_address: dict
    total_amount: float
    status: str
    payment_id: Optional[str] = None
    created_at: datetime

class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

class PaymentRequest(BaseModel):
    source_id: str
    order_id: str
    amount: int  # in cents

# ======================== HELPER FUNCTIONS ========================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(request: Request) -> dict:
    # Check cookie first
    token = request.cookies.get("session_token")
    
    # Fallback to Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if it's a session token from Google OAuth
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if session:
        expires_at = session.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Session expired")
        
        user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    
    # Try JWT token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(request: Request) -> dict:
    user = await get_current_user(request)
    if not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# ======================== AUTH ROUTES ========================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate, response: Response):
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "password": hash_password(user_data.password),
        "picture": None,
        "is_admin": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    token = create_access_token({"sub": user_id})
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=60*60*24*7
    )
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            user_id=user_id,
            email=user_data.email,
            name=user_data.name,
            is_admin=False,
            created_at=datetime.fromisoformat(user_doc["created_at"])
        )
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin, response: Response):
    user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if not user or not verify_password(user_data.password, user.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token({"sub": user["user_id"]})
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=60*60*24*7
    )
    
    created_at = user.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            user_id=user["user_id"],
            email=user["email"],
            name=user["name"],
            picture=user.get("picture"),
            is_admin=user.get("is_admin", False),
            created_at=created_at
        )
    )

@api_router.get("/auth/session")
async def get_session_data(request: Request, response: Response):
    """Handle Google OAuth session callback"""
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    # Fetch user data from Emergent Auth
    async with httpx.AsyncClient() as client:
        auth_response = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        
        if auth_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        auth_data = auth_response.json()
    
    # Check if user exists
    existing = await db.users.find_one({"email": auth_data["email"]}, {"_id": 0})
    
    if existing:
        user_id = existing["user_id"]
        # Update user info
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "name": auth_data.get("name", existing.get("name")),
                "picture": auth_data.get("picture")
            }}
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user_doc = {
            "user_id": user_id,
            "email": auth_data["email"],
            "name": auth_data.get("name", ""),
            "picture": auth_data.get("picture"),
            "is_admin": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
    
    # Store session
    session_token = auth_data.get("session_token", str(uuid.uuid4()))
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=60*60*24*7
    )
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    created_at = user.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    return {
        "user_id": user_id,
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture"),
        "is_admin": user.get("is_admin", False),
        "session_token": session_token
    }

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    created_at = user.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    return UserResponse(
        user_id=user["user_id"],
        email=user["email"],
        name=user["name"],
        picture=user.get("picture"),
        is_admin=user.get("is_admin", False),
        created_at=created_at
    )

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out successfully"}

# ======================== PRODUCT ROUTES ========================

@api_router.get("/products", response_model=List[ProductResponse])
async def get_products(
    category: Optional[str] = None,
    is_blank: Optional[bool] = None,
    featured: Optional[bool] = None
):
    query = {}
    if category:
        query["category"] = category
    if is_blank is not None:
        query["is_blank"] = is_blank
    if featured is not None:
        query["featured"] = featured
    
    products = await db.products.find(query, {"_id": 0}).to_list(1000)
    
    result = []
    for p in products:
        created_at = p.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        result.append(ProductResponse(
            product_id=p["product_id"],
            name=p["name"],
            description=p["description"],
            price=p["price"],
            category=p["category"],
            images=p.get("images", []),
            colors=p.get("colors", []),
            sizes=p.get("sizes", []),
            brand=p.get("brand", ""),
            is_blank=p.get("is_blank", False),
            stock=p.get("stock", 0),
            featured=p.get("featured", False),
            created_at=created_at
        ))
    
    return result

@api_router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    product = await db.products.find_one({"product_id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    created_at = product.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    return ProductResponse(
        product_id=product["product_id"],
        name=product["name"],
        description=product["description"],
        price=product["price"],
        category=product["category"],
        images=product.get("images", []),
        colors=product.get("colors", []),
        sizes=product.get("sizes", []),
        brand=product.get("brand", ""),
        is_blank=product.get("is_blank", False),
        stock=product.get("stock", 0),
        featured=product.get("featured", False),
        created_at=created_at
    )

@api_router.post("/admin/products", response_model=ProductResponse)
async def create_product(product: ProductCreate, user: dict = Depends(get_admin_user)):
    product_id = f"prod_{uuid.uuid4().hex[:12]}"
    product_doc = {
        "product_id": product_id,
        **product.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.products.insert_one(product_doc)
    
    return ProductResponse(
        product_id=product_id,
        **product.model_dump(),
        created_at=datetime.now(timezone.utc)
    )

@api_router.put("/admin/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, product: ProductUpdate, user: dict = Depends(get_admin_user)):
    existing = await db.products.find_one({"product_id": product_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = {k: v for k, v in product.model_dump().items() if v is not None}
    if update_data:
        await db.products.update_one({"product_id": product_id}, {"$set": update_data})
    
    updated = await db.products.find_one({"product_id": product_id}, {"_id": 0})
    created_at = updated.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    return ProductResponse(
        product_id=updated["product_id"],
        name=updated["name"],
        description=updated["description"],
        price=updated["price"],
        category=updated["category"],
        images=updated.get("images", []),
        colors=updated.get("colors", []),
        sizes=updated.get("sizes", []),
        brand=updated.get("brand", ""),
        is_blank=updated.get("is_blank", False),
        stock=updated.get("stock", 0),
        featured=updated.get("featured", False),
        created_at=created_at
    )

@api_router.delete("/admin/products/{product_id}")
async def delete_product(product_id: str, user: dict = Depends(get_admin_user)):
    result = await db.products.delete_one({"product_id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}

# ======================== ORDER ROUTES ========================

@api_router.post("/orders", response_model=OrderResponse)
async def create_order(order: OrderCreate, user: dict = Depends(get_current_user)):
    order_id = f"order_{uuid.uuid4().hex[:12]}"
    
    # Build order items with product details
    items_with_details = []
    for item in order.items:
        product = await db.products.find_one({"product_id": item.product_id}, {"_id": 0})
        if product:
            items_with_details.append({
                "product_id": item.product_id,
                "product_name": product["name"],
                "price": product["price"],
                "quantity": item.quantity,
                "color": item.color,
                "size": item.size,
                "image": product.get("images", [""])[0] if product.get("images") else ""
            })
    
    order_doc = {
        "order_id": order_id,
        "user_id": user["user_id"],
        "items": items_with_details,
        "shipping_address": order.shipping_address,
        "total_amount": order.total_amount,
        "status": "pending",
        "payment_id": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.orders.insert_one(order_doc)
    
    return OrderResponse(
        order_id=order_id,
        user_id=user["user_id"],
        items=items_with_details,
        shipping_address=order.shipping_address,
        total_amount=order.total_amount,
        status="pending",
        created_at=datetime.now(timezone.utc)
    )

@api_router.get("/orders", response_model=List[OrderResponse])
async def get_user_orders(user: dict = Depends(get_current_user)):
    orders = await db.orders.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(100)
    
    result = []
    for o in orders:
        created_at = o.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        result.append(OrderResponse(
            order_id=o["order_id"],
            user_id=o["user_id"],
            items=o["items"],
            shipping_address=o["shipping_address"],
            total_amount=o["total_amount"],
            status=o["status"],
            payment_id=o.get("payment_id"),
            created_at=created_at
        ))
    
    return result

@api_router.get("/admin/orders", response_model=List[OrderResponse])
async def get_all_orders(user: dict = Depends(get_admin_user)):
    orders = await db.orders.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    result = []
    for o in orders:
        created_at = o.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        result.append(OrderResponse(
            order_id=o["order_id"],
            user_id=o["user_id"],
            items=o["items"],
            shipping_address=o["shipping_address"],
            total_amount=o["total_amount"],
            status=o["status"],
            payment_id=o.get("payment_id"),
            created_at=created_at
        ))
    
    return result

@api_router.put("/admin/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str, user: dict = Depends(get_admin_user)):
    result = await db.orders.update_one(
        {"order_id": order_id},
        {"$set": {"status": status}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order status updated"}

# ======================== PAYMENT ROUTES ========================

@api_router.post("/payments/create")
async def create_payment(payment: PaymentRequest, user: dict = Depends(get_current_user)):
    """Process payment through Square"""
    from square.client import Client
    
    if not SQUARE_ACCESS_TOKEN:
        # Mock payment for demo without Square credentials
        payment_id = f"pay_{uuid.uuid4().hex[:12]}"
        await db.orders.update_one(
            {"order_id": payment.order_id},
            {"$set": {"status": "paid", "payment_id": payment_id}}
        )
        return {"success": True, "payment_id": payment_id, "message": "Payment processed (demo mode)"}
    
    try:
        square_client = Client(
            access_token=SQUARE_ACCESS_TOKEN,
            environment=SQUARE_ENVIRONMENT
        )
        
        result = square_client.payments.create_payment(
            body={
                "source_id": payment.source_id,
                "idempotency_key": str(uuid.uuid4()),
                "amount_money": {
                    "amount": payment.amount,
                    "currency": "USD"
                },
                "location_id": SQUARE_LOCATION_ID
            }
        )
        
        if result.is_success():
            payment_id = result.body["payment"]["id"]
            await db.orders.update_one(
                {"order_id": payment.order_id},
                {"$set": {"status": "paid", "payment_id": payment_id}}
            )
            return {"success": True, "payment_id": payment_id}
        else:
            raise HTTPException(status_code=400, detail=str(result.errors))
    
    except Exception as e:
        logger.error(f"Payment error: {str(e)}")
        raise HTTPException(status_code=500, detail="Payment processing failed")

@api_router.get("/payments/config")
async def get_payment_config():
    """Get Square payment configuration for frontend"""
    return {
        "applicationId": os.environ.get('SQUARE_APP_ID', ''),
        "locationId": SQUARE_LOCATION_ID,
        "environment": SQUARE_ENVIRONMENT
    }

# ======================== ADMIN ROUTES ========================

@api_router.get("/admin/customers")
async def get_customers(user: dict = Depends(get_admin_user)):
    customers = await db.users.find({"is_admin": {"$ne": True}}, {"_id": 0, "password": 0}).to_list(1000)
    return customers

@api_router.get("/admin/stats")
async def get_admin_stats(user: dict = Depends(get_admin_user)):
    total_products = await db.products.count_documents({})
    total_orders = await db.orders.count_documents({})
    total_customers = await db.users.count_documents({"is_admin": {"$ne": True}})
    pending_orders = await db.orders.count_documents({"status": "pending"})
    
    # Calculate revenue
    orders = await db.orders.find({"status": {"$in": ["paid", "shipped", "delivered"]}}, {"_id": 0}).to_list(1000)
    total_revenue = sum(o.get("total_amount", 0) for o in orders)
    
    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "pending_orders": pending_orders,
        "total_revenue": total_revenue
    }

# ======================== CONTACT ROUTES ========================

@api_router.post("/contact")
async def submit_contact(message: ContactMessage):
    contact_id = f"contact_{uuid.uuid4().hex[:12]}"
    contact_doc = {
        "contact_id": contact_id,
        **message.model_dump(),
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.contacts.insert_one(contact_doc)
    return {"message": "Message sent successfully", "contact_id": contact_id}

@api_router.get("/admin/contacts")
async def get_contacts(user: dict = Depends(get_admin_user)):
    contacts = await db.contacts.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return contacts

# ======================== SEED DATA ========================

@api_router.post("/seed")
async def seed_database():
    """Seed initial product data"""
    # Check if already seeded
    count = await db.products.count_documents({})
    if count > 0:
        return {"message": "Database already seeded"}
    
    products = [
        # T-Shirts
        {
            "product_id": f"prod_{uuid.uuid4().hex[:12]}",
            "name": "Faith Over Fear Tee",
            "description": "A bold statement of faith with modern typography. Perfect for everyday wear.",
            "price": 29.99,
            "category": "tshirts",
            "images": ["https://images.pexels.com/photos/9594086/pexels-photo-9594086.jpeg"],
            "colors": ["Black", "White", "Navy", "Heather Gray"],
            "sizes": ["S", "M", "L", "XL", "2XL"],
            "brand": "Faithful Threads",
            "is_blank": False,
            "stock": 100,
            "featured": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "product_id": f"prod_{uuid.uuid4().hex[:12]}",
            "name": "Blessed Beyond Measure",
            "description": "Scripture-inspired design celebrating God's blessings.",
            "price": 27.99,
            "category": "tshirts",
            "images": ["https://images.pexels.com/photos/7598248/pexels-photo-7598248.jpeg"],
            "colors": ["White", "Sand", "Light Blue"],
            "sizes": ["S", "M", "L", "XL"],
            "brand": "Faithful Threads",
            "is_blank": False,
            "stock": 75,
            "featured": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        # Hoodies
        {
            "product_id": f"prod_{uuid.uuid4().hex[:12]}",
            "name": "He Is Risen Hoodie",
            "description": "Celebrate the resurrection with this cozy premium hoodie.",
            "price": 54.99,
            "category": "hoodies",
            "images": ["https://images.pexels.com/photos/8217415/pexels-photo-8217415.jpeg"],
            "colors": ["Black", "Charcoal", "Forest Green"],
            "sizes": ["S", "M", "L", "XL", "2XL"],
            "brand": "Faithful Threads",
            "is_blank": False,
            "stock": 50,
            "featured": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "product_id": f"prod_{uuid.uuid4().hex[:12]}",
            "name": "Grace Upon Grace Hoodie",
            "description": "John 1:16 inspired design on premium cotton blend.",
            "price": 52.99,
            "category": "hoodies",
            "images": ["https://images.pexels.com/photos/9594086/pexels-photo-9594086.jpeg"],
            "colors": ["Navy", "Burgundy", "Cream"],
            "sizes": ["S", "M", "L", "XL"],
            "brand": "Faithful Threads",
            "is_blank": False,
            "stock": 40,
            "featured": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        # Hats
        {
            "product_id": f"prod_{uuid.uuid4().hex[:12]}",
            "name": "Cross Embroidered Cap",
            "description": "Classic dad cap with elegant embroidered cross.",
            "price": 24.99,
            "category": "hats",
            "images": ["https://images.pexels.com/photos/15437441/pexels-photo-15437441.jpeg"],
            "colors": ["Black", "White", "Khaki", "Navy"],
            "sizes": ["One Size"],
            "brand": "Faithful Threads",
            "is_blank": False,
            "stock": 80,
            "featured": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "product_id": f"prod_{uuid.uuid4().hex[:12]}",
            "name": "WWJD Trucker Hat",
            "description": "Retro trucker style with classic WWJD message.",
            "price": 22.99,
            "category": "hats",
            "images": ["https://images.pexels.com/photos/26886471/pexels-photo-26886471.jpeg"],
            "colors": ["Black/White", "Navy/White", "Red/White"],
            "sizes": ["One Size"],
            "brand": "Faithful Threads",
            "is_blank": False,
            "stock": 60,
            "featured": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        # Mugs
        {
            "product_id": f"prod_{uuid.uuid4().hex[:12]}",
            "name": "Morning Devotion Mug",
            "description": "Start your day with Scripture. Psalm 5:3 design.",
            "price": 16.99,
            "category": "mugs",
            "images": ["https://images.pexels.com/photos/6801212/pexels-photo-6801212.jpeg"],
            "colors": ["White", "Black"],
            "sizes": ["11oz", "15oz"],
            "brand": "Faithful Threads",
            "is_blank": False,
            "stock": 120,
            "featured": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "product_id": f"prod_{uuid.uuid4().hex[:12]}",
            "name": "Be Still Ceramic Mug",
            "description": "Psalm 46:10 reminder for your daily quiet time.",
            "price": 18.99,
            "category": "mugs",
            "images": ["https://images.pexels.com/photos/6801175/pexels-photo-6801175.jpeg"],
            "colors": ["White", "Cream"],
            "sizes": ["11oz", "15oz"],
            "brand": "Faithful Threads",
            "is_blank": False,
            "stock": 100,
            "featured": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        # Blanks
        {
            "product_id": f"prod_{uuid.uuid4().hex[:12]}",
            "name": "Premium Cotton Tee (Blank)",
            "description": "High-quality blank tee ready for custom designs.",
            "price": 12.99,
            "category": "tshirts",
            "images": ["https://images.pexels.com/photos/9594086/pexels-photo-9594086.jpeg"],
            "colors": ["White", "Black", "Navy", "Red", "Gray"],
            "sizes": ["S", "M", "L", "XL", "2XL", "3XL"],
            "brand": "Gildan",
            "is_blank": True,
            "stock": 500,
            "featured": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "product_id": f"prod_{uuid.uuid4().hex[:12]}",
            "name": "Heavyweight Hoodie (Blank)",
            "description": "Premium blank hoodie for custom printing.",
            "price": 32.99,
            "category": "hoodies",
            "images": ["https://images.pexels.com/photos/8217415/pexels-photo-8217415.jpeg"],
            "colors": ["Black", "Navy", "Gray", "White"],
            "sizes": ["S", "M", "L", "XL", "2XL"],
            "brand": "Hanes",
            "is_blank": True,
            "stock": 200,
            "featured": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "product_id": f"prod_{uuid.uuid4().hex[:12]}",
            "name": "Classic Dad Cap (Blank)",
            "description": "Unstructured blank cap for embroidery or printing.",
            "price": 8.99,
            "category": "hats",
            "images": ["https://images.pexels.com/photos/15437441/pexels-photo-15437441.jpeg"],
            "colors": ["Black", "White", "Navy", "Khaki", "Red"],
            "sizes": ["One Size"],
            "brand": "Yupoong",
            "is_blank": True,
            "stock": 300,
            "featured": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "product_id": f"prod_{uuid.uuid4().hex[:12]}",
            "name": "Ceramic Mug (Blank)",
            "description": "Sublimation-ready blank ceramic mug.",
            "price": 5.99,
            "category": "mugs",
            "images": ["https://images.pexels.com/photos/6801212/pexels-photo-6801212.jpeg"],
            "colors": ["White"],
            "sizes": ["11oz", "15oz"],
            "brand": "Generic",
            "is_blank": True,
            "stock": 400,
            "featured": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.products.insert_many(products)
    
    # Create admin user
    admin_exists = await db.users.find_one({"email": "admin@faithfulthreads.com"})
    if not admin_exists:
        admin_doc = {
            "user_id": f"user_{uuid.uuid4().hex[:12]}",
            "email": "admin@faithfulthreads.com",
            "name": "Admin",
            "password": hash_password("admin123"),
            "is_admin": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(admin_doc)
    
    return {"message": "Database seeded successfully"}

# ======================== HEALTH CHECK ========================

@api_router.get("/")
async def root():
    return {"message": "Faithful Threads API", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include router and add middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

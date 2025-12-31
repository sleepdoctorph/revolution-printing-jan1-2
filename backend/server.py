from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response, status, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
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
import shutil

ROOT_DIR = Path(__file__).parent
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
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
    fabric: Optional[str] = None
    weight: Optional[str] = None
    color_images: Optional[dict] = None

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
            created_at=created_at,
            fabric=p.get("fabric"),
            weight=p.get("weight"),
            color_images=p.get("color_images")
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
        created_at=created_at,
        fabric=product.get("fabric"),
        weight=product.get("weight")
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

# ======================== IMAGE UPLOAD ROUTES ========================

@api_router.post("/admin/upload")
async def upload_image(file: UploadFile = File(...), user: dict = Depends(get_admin_user)):
    """Upload an image and return its URL"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: JPEG, PNG, GIF, WebP")
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = UPLOAD_DIR / filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save file")
    
    # Return the URL
    return {"url": f"/api/uploads/{filename}", "filename": filename}

@api_router.post("/admin/upload-multiple")
async def upload_multiple_images(files: List[UploadFile] = File(...), user: dict = Depends(get_admin_user)):
    """Upload multiple images and return their URLs"""
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    urls = []
    
    for file in files:
        if file.content_type not in allowed_types:
            continue
        
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = f"{uuid.uuid4().hex}.{ext}"
        file_path = UPLOAD_DIR / filename
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            urls.append(f"/api/uploads/{filename}")
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
    
    return {"urls": urls}

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
    
    if not SQUARE_ACCESS_TOKEN:
        # Mock payment for demo without Square credentials
        payment_id = f"pay_{uuid.uuid4().hex[:12]}"
        await db.orders.update_one(
            {"order_id": payment.order_id},
            {"$set": {"status": "paid", "payment_id": payment_id}}
        )
        return {"success": True, "payment_id": payment_id, "message": "Payment processed (demo mode)"}
    
    try:
        from square.client import Client
        
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

@api_router.post("/admin/import-gildan")
async def import_gildan_products(user: dict = Depends(get_admin_user)):
    """Import Gildan t-shirt products from scraped wholesaler data"""
    
    # Gildan products scraped from S&S Activewear
    gildan_products = [
        {
            "style": "5000",
            "name": "Gildan Unisex Heavy Cotton™ T-Shirt",
            "description": "A classic, durable t-shirt made from 100% preshrunk cotton. Perfect for everyday wear and custom printing. Features a seamless collar for comfort and double-needle sleeves and hem for durability.",
            "price": 8.99,
            "colors": ["White", "Black", "Navy", "Red", "Royal", "Sport Grey", "Charcoal", "Forest Green", "Maroon", "Carolina Blue", "Ash", "Gold", "Orange", "Purple", "Irish Green", "Heliconia", "Light Blue", "Light Pink", "Daisy", "Lime"],
            "sizes": ["S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/16_fm.jpg"
        },
        {
            "style": "64000",
            "name": "Gildan Unisex Softstyle® T-Shirt",
            "description": "A softer, more fashion-forward fit with 100% ring-spun cotton. Lighter weight for superior comfort. Side seam construction and shoulder-to-shoulder tape for durability.",
            "price": 7.99,
            "colors": ["White", "Black", "Navy", "Red", "Royal", "Sport Grey", "Charcoal", "Dark Heather", "Carolina Blue", "Azalea", "Cherry Red", "Irish Green", "Heliconia", "Maroon", "Military Green", "Purple", "Sapphire"],
            "sizes": ["XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/32_fm.jpg"
        },
        {
            "style": "8000",
            "name": "Gildan Unisex DryBlend® T-Shirt",
            "description": "50% Cotton, 50% Polyester blend with moisture-wicking properties. Keeps you dry and comfortable. Preshrunk to minimize shrinkage.",
            "price": 6.99,
            "colors": ["White", "Black", "Navy", "Red", "Royal", "Sport Grey", "Carolina Blue", "Ash", "Forest Green", "Maroon", "Gold", "Dark Heather"],
            "sizes": ["S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/146_fm.jpg"
        },
        {
            "style": "2000",
            "name": "Gildan Unisex Ultra Cotton® T-Shirt",
            "description": "6.0 oz., 100% preshrunk cotton. Heavyweight t-shirt with classic fit. Features seamless collar, taped neck and shoulders, and double-needle sleeve and bottom hems.",
            "price": 8.49,
            "colors": ["White", "Black", "Navy", "Red", "Royal", "Sport Grey", "Charcoal", "Ash", "Forest Green", "Maroon", "Carolina Blue", "Gold", "Cardinal Red", "Purple", "Irish Green", "Heliconia", "Safety Green", "Safety Orange"],
            "sizes": ["S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/39_fm.jpg"
        },
        {
            "style": "5000B",
            "name": "Gildan Youth Heavy Cotton™ T-Shirt",
            "description": "Youth version of the classic Heavy Cotton tee. 5.3 oz., 100% preshrunk cotton. Seamless collar and double-needle sleeves and hem.",
            "price": 5.99,
            "colors": ["White", "Black", "Navy", "Red", "Royal", "Sport Grey", "Carolina Blue", "Forest Green", "Light Blue", "Light Pink"],
            "sizes": ["XS", "S", "M", "L", "XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/543_fm.jpg"
        },
        {
            "style": "64000CVC",
            "name": "Gildan Unisex Softstyle® CVC T-Shirt",
            "description": "Premium cotton-polyester blend for exceptional softness. 62% Polyester, 38% Cotton CVC Jersey. Modern fit with tear-away label.",
            "price": 10.66,
            "colors": ["White", "Pitch Black", "Navy Mist", "Red Mist", "Gunmetal", "Dusty Rose", "Cement", "Caribbean Mist", "Daisy Mist", "Cactus", "Steel Blue"],
            "sizes": ["XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/8906_fm.jpg"
        },
        {
            "style": "65000",
            "name": "Gildan Unisex Softstyle® Midweight T-Shirt",
            "description": "5.3 oz., 100% ring-spun cotton midweight tee. The perfect balance of comfort and durability. Modern fit with tear-away label.",
            "price": 10.76,
            "colors": ["White", "Pitch Black", "Navy", "Red", "Royal", "Sport Grey", "Charcoal", "Maroon", "Irish Green", "Light Blue", "Sapphire", "Brown Savana", "Mustard", "Graphite Heather"],
            "sizes": ["S", "M", "L", "XL", "2XL", "3XL", "4XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/11191_fm.jpg"
        },
        {
            "style": "H000",
            "name": "Gildan Unisex Hammer™ T-Shirt",
            "description": "6.0 oz., 100% combed ring-spun cotton. Premium heavyweight tee with a modern fit. Features fashion collar and side seams.",
            "price": 13.54,
            "colors": ["White", "Black", "Dark Navy", "Deep Royal", "Chalky Mint", "Chambray", "Flo Blue", "Graphite Heather", "Lagoon Blue", "Off White", "Scarlet Red", "Sport Grey"],
            "sizes": ["S", "M", "L", "XL", "2XL", "3XL", "4XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/6233_fm.jpg"
        },
        {
            "style": "42000",
            "name": "Gildan Unisex Performance® T-Shirt",
            "description": "100% Polyester moisture-wicking performance tee. Features AquaFX® and Freshcare® antimicrobial properties. Perfect for athletic and outdoor wear.",
            "price": 12.82,
            "colors": ["White", "Black", "Navy", "Red", "Royal", "Carolina Blue", "Charcoal", "Gold", "Irish Green", "Lime", "Military Green", "Orange", "Purple", "Safety Green", "Safety Orange", "Sport Grey"],
            "sizes": ["S", "M", "L", "XL", "2XL", "3XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/2691_fm.jpg"
        },
        {
            "style": "3000",
            "name": "Gildan Unisex Light Cotton T-Shirt",
            "description": "4.5 oz., 100% ring-spun cotton lightweight tee. Perfect for layering or warm weather. Tear-away label and side seams.",
            "price": 7.49,
            "colors": ["White", "Black", "Navy", "Red", "Royal", "Sport Grey", "Carolina Blue", "Charcoal", "Forest Green", "Gold", "Graphite Heather", "Gravel", "Heather Navy", "Light Blue", "Light Pink", "Maroon", "Military Green", "Orange", "Purple", "Sage", "Sand"],
            "sizes": ["XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL", "6XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/12514_fm.jpg"
        },
        {
            "style": "5000L",
            "name": "Gildan Women's Heavy Cotton™ T-Shirt",
            "description": "Women's version of the classic Heavy Cotton tee. 5.3 oz., 100% preshrunk cotton. Semi-fitted silhouette for a feminine look.",
            "price": 7.99,
            "colors": ["White", "Black", "Navy", "Red", "Royal", "Sport Grey", "Azalea", "Carolina Blue", "Charcoal", "Coral Silk", "Daisy", "Dark Heather", "Dusty Rose", "Heliconia", "Irish Green", "Light Blue", "Light Pink", "Maroon", "Purple", "Sapphire"],
            "sizes": ["S", "M", "L", "XL", "2XL", "3XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/2115_fm.jpg"
        },
        {
            "style": "64000L",
            "name": "Gildan Women's Softstyle® T-Shirt",
            "description": "Women's Softstyle tee with a modern feminine fit. 4.5 oz., 100% ring-spun cotton. Semi-fitted with side seams.",
            "price": 7.49,
            "colors": ["White", "Black", "Navy", "Azalea", "Charcoal", "Cherry Red", "Dark Heather", "Heather Purple", "Heather Royal", "Heliconia", "Irish Green", "Light Blue", "Maroon", "Royal", "Sapphire", "Sport Grey"],
            "sizes": ["S", "M", "L", "XL", "2XL", "3XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/809_fm.jpg"
        },
        {
            "style": "2300",
            "name": "Gildan Unisex Ultra Cotton® Pocket T-Shirt",
            "description": "Classic pocket tee with 6.0 oz., 100% preshrunk cotton. Features left chest pocket, seamless collar, and double-needle stitching throughout.",
            "price": 13.84,
            "colors": ["White", "Black", "Navy", "Red", "Royal", "Ash", "Charcoal", "Forest Green", "Light Blue", "Maroon", "Safety Green", "Safety Orange", "Sport Grey"],
            "sizes": ["S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/155_fm.jpg"
        },
        {
            "style": "5300",
            "name": "Gildan Unisex Heavy Cotton™ Pocket T-Shirt",
            "description": "Heavy Cotton pocket tee with 5.3 oz., 100% preshrunk cotton. Features left chest pocket and double-needle stitching for durability.",
            "price": 11.46,
            "colors": ["White", "Black", "Navy", "Red", "Charcoal", "Graphite Heather", "Irish Green", "Maroon", "Orange", "Sapphire", "Sport Grey"],
            "sizes": ["S", "M", "L", "XL", "2XL", "3XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/4467_fm.jpg"
        },
        {
            "style": "64V00",
            "name": "Gildan Unisex Softstyle® V-Neck T-Shirt",
            "description": "4.5 oz., 100% ring-spun cotton V-neck tee. Modern fit with fashion-forward V-neck style. Tear-away label.",
            "price": 12.30,
            "colors": ["White", "Black", "Navy", "Charcoal", "Cherry Red", "Dark Heather", "Heather Irish Green", "Heather Purple", "Royal", "Sport Grey"],
            "sizes": ["XS", "S", "M", "L", "XL", "2XL", "3XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/2116_fm.jpg"
        },
        {
            "style": "64V00L",
            "name": "Gildan Women's Softstyle® V-Neck T-Shirt",
            "description": "Women's V-neck with 4.5 oz., 100% ring-spun cotton. Semi-fitted feminine silhouette with fashionable V-neck.",
            "price": 10.68,
            "colors": ["White", "Black", "Navy", "Azalea", "Cherry Red", "Dark Heather", "Heather Purple", "Royal", "Sport Grey"],
            "sizes": ["S", "M", "L", "XL", "2XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/2117_fm.jpg"
        },
        {
            "style": "75000",
            "name": "Gildan Unisex Hammer™ Maxweight T-Shirt",
            "description": "7.0 oz., 100% ring-spun cotton super heavyweight tee. Maximum durability for demanding applications. Fashion collar with side seams.",
            "price": 12.30,
            "colors": ["White", "Pitch Black", "Deep Royal", "Forest Green", "Blue Dusk", "Cherry Red", "Dark Chocolate", "Garnet", "Graphite Heather", "Tan"],
            "sizes": ["S", "M", "L", "XL", "2XL", "3XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/12448_fm.jpg"
        },
        {
            "style": "980",
            "name": "Gildan Unisex Softstyle® Lightweight T-Shirt",
            "description": "4.1 oz., 100% ring-spun cotton ultra-lightweight tee. Perfect for layering or summer wear. Modern fit with tear-away label.",
            "price": 6.99,
            "colors": ["White", "Black", "Charcoal", "Baby Blue", "Caribbean Blue", "Charity Pink", "Graphite Heather", "Heather Blue", "Heather Dark Grey", "Heather Grey", "Heather Navy", "Heather Purple", "Kelly Green", "Military Green", "Navy", "Red"],
            "sizes": ["XS", "S", "M", "L", "XL", "2XL", "3XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/10649_fm.jpg"
        },
        {
            "style": "8300",
            "name": "Gildan Unisex DryBlend® Pocket T-Shirt",
            "description": "50/50 Cotton/Poly DryBlend pocket tee with moisture-wicking properties. Features left chest pocket and preshrunk fabric.",
            "price": 11.70,
            "colors": ["White", "Black", "Navy", "Red", "Royal", "Ash", "Forest Green", "Graphite Heather", "Safety Green", "Sport Grey"],
            "sizes": ["S", "M", "L", "XL", "2XL", "3XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/160_fm.jpg"
        },
        {
            "style": "2000T",
            "name": "Gildan Men's Tall Ultra Cotton® T-Shirt",
            "description": "Tall version of the Ultra Cotton tee with 2\" extra length. 6.0 oz., 100% preshrunk cotton. Perfect for taller individuals.",
            "price": 15.72,
            "colors": ["White", "Black", "Navy", "Charcoal", "Royal", "Safety Green", "Sport Grey"],
            "sizes": ["LT", "XLT", "2XLT", "3XLT"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/148_fm.jpg"
        }
    ]
    
    imported_count = 0
    skipped_count = 0
    
    for product in gildan_products:
        # Check if product already exists by style number
        existing = await db.products.find_one({"brand": "Gildan", "name": {"$regex": product["style"]}}, {"_id": 0})
        if existing:
            skipped_count += 1
            continue
            
        product_id = f"prod_{uuid.uuid4().hex[:12]}"
        product_doc = {
            "product_id": product_id,
            "name": product["name"],
            "description": product["description"],
            "price": product["price"],
            "category": "tshirts",
            "images": [product["image"]],
            "colors": product["colors"],
            "sizes": product["sizes"],
            "brand": "Gildan",
            "is_blank": True,
            "stock": 500,
            "featured": product["style"] in ["5000", "64000", "2000", "H000"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.products.insert_one(product_doc)
        imported_count += 1
    
    return {
        "message": f"Gildan products imported successfully",
        "imported": imported_count,
        "skipped": skipped_count,
        "total": len(gildan_products)
    }

@api_router.post("/admin/update-gildan-descriptions")
async def update_gildan_descriptions(user: dict = Depends(get_admin_user)):
    """Update Gildan products with actual descriptions from S&S Activewear wholesaler"""
    
    # Real descriptions scraped from S&S Activewear product pages - matched by product name
    gildan_descriptions = {
        "Gildan Unisex Heavy Cotton™ T-Shirt": {
            "description": "5.3 oz., 100% preshrunk cotton. Seamless double-needle 7/8\" collar. Taped neck and shoulders. Double-needle sleeve and bottom hems. Quarter-turned to eliminate center crease. Available in 68 colors from XS to 5XL. The industry standard for screen printing and promotional apparel.",
            "fabric": "100% Cotton",
            "weight": "5.3 oz"
        },
        "Gildan Unisex Softstyle® T-Shirt": {
            "description": "4.5 oz., 100% ring-spun cotton. Softstyle yarn for a soft hand feel. Fitted silhouette with side seam construction. Shoulder-to-shoulder tape. Tear-away label. Available in 64 colors from XS to 5XL. A retail-quality blank ideal for fashion-forward designs.",
            "fabric": "100% Ring-spun Cotton",
            "weight": "4.5 oz"
        },
        "Gildan Unisex DryBlend® T-Shirt": {
            "description": "5.6 oz., 50% cotton, 50% polyester. DryBlend wicking performance. Preshrunk to minimize shrinkage. Seamless double-needle collar. Taped neck and shoulders. Double-needle sleeve and bottom hems. Ideal for athletic wear and performance applications.",
            "fabric": "50% Cotton, 50% Polyester",
            "weight": "5.6 oz"
        },
        "Gildan Unisex Ultra Cotton® T-Shirt": {
            "description": "6.0 oz., 100% cotton preshrunk jersey knit. Seamless double-needle 7/8\" collar. Taped neck and shoulders. Double-needle sleeve and bottom hems. Quarter-turned. Ultra-durable heavyweight fabric perfect for workwear and everyday basics.",
            "fabric": "100% Cotton",
            "weight": "6.0 oz"
        },
        "Gildan Youth Heavy Cotton™ T-Shirt": {
            "description": "5.3 oz., 100% preshrunk cotton youth tee. Seamless double-needle collar. Taped neck and shoulders. Double-needle sleeve and bottom hems. Available in sizes XS-XL. Perfect blank for youth events, schools, and family matching.",
            "fabric": "100% Cotton",
            "weight": "5.3 oz"
        },
        "Gildan Unisex Softstyle® CVC T-Shirt": {
            "description": "4.5 oz., 62% polyester, 38% cotton CVC jersey. Softstyle CVC blend creates a unique heathered look. Semi-fitted contoured silhouette with side seam construction. Tear-away label. Modern retail-inspired fit.",
            "fabric": "62% Polyester, 38% Cotton CVC",
            "weight": "4.5 oz"
        },
        "Gildan Unisex Softstyle® Midweight T-Shirt": {
            "description": "5.3 oz., 100% ring-spun cotton midweight tee. Retail-quality soft hand feel. Set-in sleeves with tear-away label. Modern fit between classic and fitted. Available in 22 colors from S to 4XL. The perfect balance of comfort and durability.",
            "fabric": "100% Ring-spun Cotton",
            "weight": "5.3 oz"
        },
        "Gildan Unisex Hammer™ T-Shirt": {
            "description": "6.0 oz., 100% combed ring-spun cotton. Premium Hammer collection with modern styling. Fashion collar and side seams. Tear-away label. Available in 38 colors. Elevated blank for premium retail and custom apparel.",
            "fabric": "100% Combed Ring-spun Cotton",
            "weight": "6.0 oz"
        },
        "Gildan Unisex Performance® T-Shirt": {
            "description": "4.5 oz., 100% polyester jersey knit. Core Performance with AquaFX wicking and Freshcare odor control. Self-fabric collar with heat transfer label. Set-in sleeves. Perfect for athletics, teams, and outdoor activities.",
            "fabric": "100% Polyester",
            "weight": "4.5 oz"
        },
        "Gildan Unisex Light Cotton T-Shirt": {
            "description": "4.5 oz., 100% ring-spun cotton lightweight tee. Soft hand feel with retail-quality finish. Side seam construction with tear-away label. Extended size range from XS to 6XL. Ideal for layering or warm weather.",
            "fabric": "100% Ring-spun Cotton",
            "weight": "4.5 oz"
        },
        "Gildan Women's Heavy Cotton™ T-Shirt": {
            "description": "5.3 oz., 100% preshrunk cotton women's tee. Semi-fitted feminine silhouette with shorter sleeves. Seamless double-needle collar. Double-needle sleeve and bottom hems. Available in 30 colors from S to 3XL.",
            "fabric": "100% Cotton",
            "weight": "5.3 oz"
        },
        "Gildan Women's Softstyle® T-Shirt": {
            "description": "4.5 oz., 100% ring-spun cotton women's Softstyle tee. Contoured semi-fitted silhouette with side seam. Cap sleeves with tear-away label. Retail-quality soft hand. Available in 17 colors from S to 3XL.",
            "fabric": "100% Ring-spun Cotton",
            "weight": "4.5 oz"
        },
        "Gildan Unisex Ultra Cotton® Pocket T-Shirt": {
            "description": "6.0 oz., 100% cotton preshrunk pocket tee. Left chest pocket. Seamless double-needle collar. Taped neck and shoulders. Double-needle pocket, sleeve and bottom hems. Extended sizes S to 5XL available.",
            "fabric": "100% Cotton",
            "weight": "6.0 oz"
        },
        "Gildan Unisex Heavy Cotton™ Pocket T-Shirt": {
            "description": "5.3 oz., 100% preshrunk cotton pocket tee. Heavyweight construction with left chest pocket. Seamless double-needle collar. Double-needle pocket, sleeve and bottom hems. Workwear-ready durability.",
            "fabric": "100% Cotton",
            "weight": "5.3 oz"
        },
        "Gildan Unisex Softstyle® V-Neck T-Shirt": {
            "description": "4.5 oz., 100% ring-spun cotton V-neck tee. Softstyle yarn for soft hand feel. Fitted silhouette with side seam. 1x1 rib V-neck collar. Tear-away label. Fashion-forward neckline for modern looks.",
            "fabric": "100% Ring-spun Cotton",
            "weight": "4.5 oz"
        },
        "Gildan Women's Softstyle® V-Neck T-Shirt": {
            "description": "4.5 oz., 100% ring-spun cotton women's V-neck. Semi-fitted feminine silhouette. Contoured side seam with 1x1 rib V-neck collar. Tear-away label. Perfect for layering and professional settings.",
            "fabric": "100% Ring-spun Cotton",
            "weight": "4.5 oz"
        },
        "Gildan Unisex Hammer™ Maxweight T-Shirt": {
            "description": "7.0 oz., 100% ring-spun cotton super heavyweight tee. Hammer Maxweight collection with premium construction. Fashion collar and side seams. Maximum durability for demanding applications and workwear.",
            "fabric": "100% Ring-spun Cotton",
            "weight": "7.0 oz"
        },
        "Gildan Unisex Softstyle® Lightweight T-Shirt": {
            "description": "4.1 oz., 100% ring-spun cotton lightweight tee. Softstyle EZ Print with superior printability. Side seam construction. Tear-away label. Ultra-soft and perfect for fashion retail applications.",
            "fabric": "100% Ring-spun Cotton",
            "weight": "4.1 oz"
        },
        "Gildan Unisex DryBlend® Pocket T-Shirt": {
            "description": "5.6 oz., 50% cotton, 50% polyester pocket tee. DryBlend wicking technology. Left chest pocket with double-needle stitching. Preshrunk for minimal shrinkage. Ideal for workwear and performance needs.",
            "fabric": "50% Cotton, 50% Polyester",
            "weight": "5.6 oz"
        },
        "Gildan Men's Tall Ultra Cotton® T-Shirt": {
            "description": "6.0 oz., 100% cotton preshrunk tall tee. 2\" extra body length for taller individuals. Seamless double-needle collar. Taped neck and shoulders. Available in tall sizes LT to 3XLT.",
            "fabric": "100% Cotton",
            "weight": "6.0 oz"
        }
    }
    
    updated_count = 0
    not_found_count = 0
    
    for name, details in gildan_descriptions.items():
        # Find products with exact name match
        result = await db.products.update_one(
            {"brand": "Gildan", "name": name},
            {"$set": {
                "description": details["description"],
                "fabric": details["fabric"],
                "weight": details["weight"]
            }}
        )
        if result.modified_count > 0:
            updated_count += result.modified_count
        else:
            not_found_count += 1
    
    return {
        "message": "Gildan product descriptions updated successfully",
        "updated": updated_count,
        "not_found": not_found_count,
        "total_products": len(gildan_descriptions)
    }

@api_router.post("/admin/update-gildan-color-images")
async def update_gildan_color_images(user: dict = Depends(get_admin_user)):
    """Update Gildan products with color-specific images from S&S Activewear"""
    
    # Color image IDs scraped from S&S Activewear for Gildan 5000 (Heavy Cotton)
    # Format: colorStyleID mapped to color name
    gildan_5000_color_images = {
        "White": "16813",
        "Black": "16787", 
        "Navy": "16807",
        "Red": "16810",
        "Royal": "16812",
        "Sport Grey": "16817",
        "Charcoal": "16790",
        "Forest Green": "16793",
        "Maroon": "16803",
        "Carolina Blue": "16789",
        "Ash": "16785",
        "Gold": "30026",
        "Orange": "16809",
        "Purple": "16816",
        "Irish Green": "16795",
        "Heliconia": "16794",
        "Light Blue": "16800",
        "Light Pink": "16801",
        "Daisy": "16791",
        "Lime": "16802"
    }
    
    # Build color_images dict for Gildan 5000
    color_images_5000 = {}
    for color, color_id in gildan_5000_color_images.items():
        color_images_5000[color] = f"https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=600,f=auto/Images/Color/{color_id}_f.jpg"
    
    # Update Gildan 5000 (Heavy Cotton)
    result_5000 = await db.products.update_one(
        {"brand": "Gildan", "name": "Gildan Unisex Heavy Cotton™ T-Shirt"},
        {"$set": {"color_images": color_images_5000}}
    )
    
    # Color images for Gildan 64000 (Softstyle)
    gildan_64000_color_images = {
        "White": "29885",
        "Black": "29881",
        "Navy": "29883",
        "Red": "52378",
        "Royal": "29884",
        "Sport Grey": "29886",
        "Charcoal": "16925",
        "Dark Heather": "32215",
        "Carolina Blue": "52352",
        "Azalea": "52348",
        "Cherry Red": "16926",
        "Irish Green": "32217",
        "Heliconia": "52366",
        "Maroon": "32218",
        "Military Green": "33312",
        "Purple": "52377",
        "Sapphire": "29887"
    }
    
    color_images_64000 = {}
    for color, color_id in gildan_64000_color_images.items():
        color_images_64000[color] = f"https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=600,f=auto/Images/Color/{color_id}_f.jpg"
    
    result_64000 = await db.products.update_one(
        {"brand": "Gildan", "name": "Gildan Unisex Softstyle® T-Shirt"},
        {"$set": {"color_images": color_images_64000}}
    )
    
    # Color images for Gildan 2000 (Ultra Cotton)
    gildan_2000_color_images = {
        "White": "17130",
        "Black": "17075",
        "Navy": "17103",
        "Red": "17110",
        "Royal": "17113",
        "Sport Grey": "17117",
        "Charcoal": "29996",
        "Ash": "17072",
        "Forest Green": "29997",
        "Maroon": "17099",
        "Carolina Blue": "17078",
        "Gold": "29998",
        "Cardinal Red": "17077",
        "Purple": "17109",
        "Irish Green": "17091",
        "Heliconia": "17087",
        "Safety Green": "17114",
        "Safety Orange": "17115"
    }
    
    color_images_2000 = {}
    for color, color_id in gildan_2000_color_images.items():
        color_images_2000[color] = f"https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=600,f=auto/Images/Color/{color_id}_f.jpg"
    
    result_2000 = await db.products.update_one(
        {"brand": "Gildan", "name": "Gildan Unisex Ultra Cotton® T-Shirt"},
        {"$set": {"color_images": color_images_2000}}
    )
    
    # Color images for Gildan 8000 (DryBlend)
    gildan_8000_color_images = {
        "White": "17927",
        "Black": "17904",
        "Navy": "17917",
        "Red": "17920",
        "Royal": "17921",
        "Sport Grey": "17924",
        "Carolina Blue": "17905",
        "Ash": "17902",
        "Forest Green": "17910",
        "Maroon": "17916",
        "Gold": "17911",
        "Dark Heather": "32135"
    }
    
    color_images_8000 = {}
    for color, color_id in gildan_8000_color_images.items():
        color_images_8000[color] = f"https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=600,f=auto/Images/Color/{color_id}_f.jpg"
    
    result_8000 = await db.products.update_one(
        {"brand": "Gildan", "name": "Gildan Unisex DryBlend® T-Shirt"},
        {"$set": {"color_images": color_images_8000}}
    )
    
    total_updated = result_5000.modified_count + result_64000.modified_count + result_2000.modified_count + result_8000.modified_count
    
    return {
        "message": "Gildan color images updated successfully",
        "updated": total_updated,
        "products_updated": {
            "5000_heavy_cotton": result_5000.modified_count,
            "64000_softstyle": result_64000.modified_count,
            "2000_ultra_cotton": result_2000.modified_count,
            "8000_dryblend": result_8000.modified_count
        }
    }

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

# Mount static files for uploads
app.mount("/api/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

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

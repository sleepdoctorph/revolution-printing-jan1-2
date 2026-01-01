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
import resend

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

# Resend Email Settings
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
resend.api_key = RESEND_API_KEY

app = FastAPI(title="Revolution Printing API")
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

class DesignCreate(BaseModel):
    name: str
    category: str  # "apparel" (for tshirts, hoodies, mugs) or "hats"
    image_url: str = ""

class DesignResponse(BaseModel):
    design_id: str
    name: str
    category: str
    image_url: str
    created_at: datetime

class CartItemWithDesign(BaseModel):
    product_id: str
    quantity: int
    color: str = ""
    size: str = ""
    design_id: str = ""
    design_name: str = ""
    design_image: str = ""

class OrderCreateWithDesign(BaseModel):
    items: List[CartItemWithDesign]
    shipping_address: dict
    total_amount: float

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

async def send_order_confirmation_email(order_data: dict, customer_email: str, customer_name: str):
    """Send order confirmation email to customer"""
    if not RESEND_API_KEY:
        logger.warning("Resend API key not configured, skipping email")
        return False
    
    try:
        # Build items HTML
        items_html = ""
        for item in order_data.get("items", []):
            design_info = f"<br><small>Design: {item.get('design_name', 'N/A')}</small>" if item.get('design_name') else ""
            items_html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #eee;">
                    <strong>{item.get('product_name', 'Product')}</strong><br>
                    <small style="color: #666;">Color: {item.get('color', 'N/A')} | Size: {item.get('size', 'N/A')}</small>
                    {design_info}
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: center;">{item.get('quantity', 1)}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right;">${item.get('price', 0):.2f}</td>
            </tr>
            """
        
        shipping = order_data.get("shipping_address", {})
        shipping_html = f"""
            {shipping.get('firstName', '')} {shipping.get('lastName', '')}<br>
            {shipping.get('address', '')}<br>
            {shipping.get('city', '')}, {shipping.get('state', '')} {shipping.get('zip', '')}<br>
            {shipping.get('phone', '')}
        """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Order Confirmation</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; padding: 20px 0; border-bottom: 3px solid #E53E3E;">
                <h1 style="color: #E53E3E; margin: 0;">Revolution Printing</h1>
                <p style="color: #666; font-style: italic; margin: 5px 0;">Inspired by Scripture. Designed for Life.</p>
            </div>
            
            <div style="padding: 30px 0;">
                <h2 style="color: #333;">Thank You for Your Order! 🙏</h2>
                <p>Dear {customer_name},</p>
                <p>Thank you for choosing Revolution Printing! We're blessed to have you as part of our faith community. Your order has been received and we're getting it ready for you.</p>
                
                <div style="background: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #E53E3E;">Order Details</h3>
                    <p><strong>Order ID:</strong> {order_data.get('order_id', 'N/A')}</p>
                    <p><strong>Order Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
                </div>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <thead>
                        <tr style="background: #E53E3E; color: white;">
                            <th style="padding: 12px; text-align: left;">Item</th>
                            <th style="padding: 12px; text-align: center;">Qty</th>
                            <th style="padding: 12px; text-align: right;">Price</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                    <tfoot>
                        <tr>
                            <td colspan="2" style="padding: 12px; text-align: right;"><strong>Total:</strong></td>
                            <td style="padding: 12px; text-align: right; font-size: 18px; color: #E53E3E;"><strong>${order_data.get('total_amount', 0):.2f}</strong></td>
                        </tr>
                    </tfoot>
                </table>
                
                <div style="background: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #E53E3E;">Shipping Address</h3>
                    <p style="margin: 0;">{shipping_html}</p>
                </div>
                
                <div style="background: #FFF5F5; padding: 20px; border-radius: 8px; border-left: 4px solid #E53E3E; margin: 20px 0;">
                    <p style="margin: 0; font-style: italic;">"For I know the plans I have for you," declares the Lord, "plans to prosper you and not to harm you, plans to give you hope and a future." - Jeremiah 29:11</p>
                </div>
                
                <p>If you have any questions about your order, please don't hesitate to reach out to us at <a href="mailto:myrevolutionprinting@gmail.com" style="color: #E53E3E;">myrevolutionprinting@gmail.com</a></p>
                
                <p>God bless,<br><strong>The Revolution Printing Team</strong></p>
            </div>
            
            <div style="text-align: center; padding: 20px 0; border-top: 1px solid #eee; color: #666; font-size: 12px;">
                <p>© {datetime.now().year} Revolution Printing. All rights reserved.</p>
                <p>Inspired by Scripture. Designed for Life.</p>
            </div>
        </body>
        </html>
        """
        
        params = {
            "from": "Revolution Printing <onboarding@resend.dev>",
            "to": [customer_email],
            "subject": f"Order Confirmed! Thank you for your purchase #{order_data.get('order_id', '')}",
            "html": html_content
        }
        
        email = resend.Emails.send(params)
        logger.info(f"Order confirmation email sent to {customer_email}, email_id: {email.get('id')}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send order confirmation email: {str(e)}")
        return False

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
        weight=product.get("weight"),
        color_images=product.get("color_images")
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

# ======================== DESIGN ROUTES ========================

@api_router.get("/designs", response_model=List[DesignResponse])
async def get_designs(category: Optional[str] = None):
    """Get all designs, optionally filtered by category (apparel or hats)"""
    query = {}
    if category:
        query["category"] = category
    
    designs = await db.designs.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    result = []
    for d in designs:
        created_at = d.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        result.append(DesignResponse(
            design_id=d["design_id"],
            name=d["name"],
            category=d["category"],
            image_url=d.get("image_url", ""),
            created_at=created_at
        ))
    return result

@api_router.get("/designs/{design_id}", response_model=DesignResponse)
async def get_design(design_id: str):
    """Get a single design by ID"""
    design = await db.designs.find_one({"design_id": design_id}, {"_id": 0})
    if not design:
        raise HTTPException(status_code=404, detail="Design not found")
    
    created_at = design.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    return DesignResponse(
        design_id=design["design_id"],
        name=design["name"],
        category=design["category"],
        image_url=design.get("image_url", ""),
        created_at=created_at
    )

@api_router.post("/admin/designs", response_model=DesignResponse)
async def create_design(design: DesignCreate, user: dict = Depends(get_admin_user)):
    """Create a new design (admin only)"""
    design_id = f"design_{uuid.uuid4().hex[:12]}"
    
    design_doc = {
        "design_id": design_id,
        "name": design.name,
        "category": design.category,  # "apparel" or "hats"
        "image_url": design.image_url,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.designs.insert_one(design_doc)
    
    return DesignResponse(
        design_id=design_id,
        name=design.name,
        category=design.category,
        image_url=design.image_url,
        created_at=datetime.now(timezone.utc)
    )

@api_router.put("/admin/designs/{design_id}", response_model=DesignResponse)
async def update_design(design_id: str, design: DesignCreate, user: dict = Depends(get_admin_user)):
    """Update a design (admin only)"""
    existing = await db.designs.find_one({"design_id": design_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Design not found")
    
    update_data = {
        "name": design.name,
        "category": design.category,
        "image_url": design.image_url
    }
    
    await db.designs.update_one({"design_id": design_id}, {"$set": update_data})
    
    created_at = existing.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    return DesignResponse(
        design_id=design_id,
        name=design.name,
        category=design.category,
        image_url=design.image_url,
        created_at=created_at
    )

@api_router.delete("/admin/designs/{design_id}")
async def delete_design(design_id: str, user: dict = Depends(get_admin_user)):
    """Delete a design (admin only)"""
    result = await db.designs.delete_one({"design_id": design_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Design not found")
    return {"message": "Design deleted successfully"}

@api_router.post("/admin/designs/upload")
async def upload_design_image(
    file: UploadFile = File(...),
    user: dict = Depends(get_admin_user)
):
    """Upload a design image file"""
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, WebP, GIF allowed.")
    
    # Create designs upload directory
    designs_dir = UPLOAD_DIR / "designs"
    designs_dir.mkdir(exist_ok=True)
    
    ext = file.filename.split(".")[-1] if "." in file.filename else "png"
    filename = f"design_{uuid.uuid4().hex[:12]}.{ext}"
    file_path = designs_dir / filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"url": f"/api/uploads/designs/{filename}"}
    except Exception as e:
        logger.error(f"Design upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Upload failed")

@api_router.get("/admin/designs", response_model=List[DesignResponse])
async def get_admin_designs(user: dict = Depends(get_admin_user)):
    """Get all designs for admin management"""
    designs = await db.designs.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    result = []
    for d in designs:
        created_at = d.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        result.append(DesignResponse(
            design_id=d["design_id"],
            name=d["name"],
            category=d["category"],
            image_url=d.get("image_url", ""),
            created_at=created_at
        ))
    return result

# ======================== SEED DATA ========================

@api_router.post("/admin/update-all-gildan-color-images")
async def update_all_gildan_color_images(user: dict = Depends(get_admin_user)):
    """Update ALL Gildan products with color-specific images from S&S Activewear"""
    
    # Product color mappings extracted from S&S Activewear
    product_color_mappings = {
        # Gildan 5000B - Youth Heavy Cotton
        "Gildan Youth Heavy Cotton™ T-Shirt": {
            "White": "21029", "Black": "21005", "Aquatic": "114534", "Ash": "21003", "Azalea": "21004",
            "Blue Dusk": "66834", "Cardinal": "21006", "Carolina Blue": "21007", "Charcoal": "21008",
            "Cobalt": "40568", "Coral Silk": "37348", "Daisy": "21009", "Dark Heather": "40573",
            "Dusty Rose": "114536", "Electric Green": "37350", "Forest Green": "21011", "Garnet": "32229",
            "Gold": "21012", "Graphite Heather": "46153", "Heather Navy": "32235", "Heather Red": "78839",
            "Heather Sapphire": "78832", "Heliconia": "32230", "Indigo Blue": "21013", "Irish Green": "21014",
            "Kiwi": "21015", "Light Blue": "21016", "Light Pink": "21017", "Lime": "21018", "Maroon": "27882",
            "Military Green": "33351", "Mint Green": "40569", "Natural": "21019", "Navy": "21020",
            "Neon Blue": "42453", "Neon Green": "42454", "Off White": "66835", "Orange": "21021",
            "Purple": "21022", "Red": "27883", "Royal": "21023", "Safety Green": "40574",
            "Safety Orange": "40575", "Safety Pink": "42452", "Sand": "21024", "Sapphire": "21025",
            "Sky": "29962", "Sport Grey": "21026", "Tennessee Orange": "32232", "Tropical Blue": "37351",
            "Violet": "21028"
        },
        # Gildan 5000L - Women's Heavy Cotton
        "Gildan Women's Heavy Cotton™ T-Shirt": {
            "White": "33429", "Black": "33413", "Aquatic": "114524", "Azalea": "33412",
            "Blue Dusk": "114532", "Carolina Blue": "37386", "Charcoal": "33414", "Coral Silk": "33432",
            "Daisy": "37387", "Dark Heather": "40578", "Dusty Rose": "114526", "Heather Sapphire": "33417",
            "Heliconia": "33419", "Irish Green": "33430", "Light Blue": "33420", "Light Pink": "37389",
            "Maroon": "33422", "Navy": "33423", "Off White": "114529", "Orange": "33424",
            "Purple": "33425", "Red": "33426", "Royal": "33427", "Sapphire": "33431",
            "Sport Grey": "33428", "Tropical Blue": "37393", "Violet": "37394"
        },
        # Gildan H000 - Hammer T-Shirt
        "Gildan Unisex Hammer™ T-Shirt": {
            "White": "66670", "Black": "66651", "Chambray": "66674", "Dark Navy": "66663",
            "Deep Royal": "66666", "Graphite Heather": "66655", "Off White": "107649",
            "Scarlet Red": "66667", "Seafoam": "66678", "Sport Grey": "66668"
        },
        # Gildan 64000L - Women's Softstyle
        "Gildan Women's Softstyle® T-Shirt": {
            "White": "17263", "Black": "17243", "Azalea": "17241", "Charcoal": "17244",
            "Cherry Red": "17245", "Dark Heather": "17246", "Heather Purple": "52381",
            "Heather Royal": "32236", "Heliconia": "17251", "Irish Green": "17252",
            "Light Blue": "33443", "Maroon": "17256", "Navy": "17257", "Royal": "17260",
            "Sapphire": "17261", "Sport Grey": "17262"
        },
        # Gildan 64V00 - V-Neck
        "Gildan Unisex Softstyle® V-Neck T-Shirt": {
            "White": "17273", "Black": "17267", "Charcoal": "33466", "Cherry Red": "17268",
            "Dark Heather": "17269", "Heather Irish Green": "33464", "Heather Purple": "33465",
            "Navy": "52389", "Royal": "17272", "Sport Grey": "33468"
        },
        # Gildan 64V00L - Women's V-Neck
        "Gildan Women's Softstyle® V-Neck T-Shirt": {
            "White": "17283", "Black": "17278", "Azalea": "17276", "Cherry Red": "17279",
            "Dark Heather": "17280", "Heather Purple": "52390", "Navy": "52391",
            "Royal": "17282", "Sport Grey": "33471"
        },
        # Gildan 2300 - Ultra Cotton Pocket
        "Gildan Unisex Ultra Cotton® Pocket T-Shirt": {
            "White": "17175", "Black": "17168", "Ash": "17167", "Charcoal": "17169",
            "Forest Green": "17170", "Light Blue": "17171", "Maroon": "17172",
            "Navy": "17173", "Red": "17174", "Royal": "52303", "Safety Green": "30018",
            "Safety Orange": "30019", "Sport Grey": "30020"
        },
        # Gildan 5300 - Heavy Cotton Pocket
        "Gildan Unisex Heavy Cotton™ Pocket T-Shirt": {
            "White": "33742", "Black": "33681", "Charcoal": "33686", "Graphite Heather": "33697",
            "Irish Green": "33707", "Maroon": "33713", "Navy": "33718", "Orange": "33722",
            "Red": "33724", "Sapphire": "33731", "Sport Grey": "33733"
        },
        # Gildan 8300 - DryBlend Pocket
        "Gildan Unisex DryBlend® Pocket T-Shirt": {
            "White": "17964", "Black": "17958", "Ash": "17956", "Forest Green": "17959",
            "Graphite Heather": "46076", "Navy": "17960", "Red": "17961", "Royal": "17962",
            "Safety Green": "17963", "Sport Grey": "30021"
        },
        # Gildan 42000 - Performance
        "Gildan Unisex Performance® T-Shirt": {
            "White": "17363", "Black": "17351", "Carolina Blue": "17352", "Charcoal": "17353",
            "Gold": "17354", "Irish Green": "17355", "Lime": "17356", "Maroon": "17357",
            "Military Green": "33345", "Navy": "17358", "Orange": "17359", "Purple": "17360",
            "Red": "17361", "Royal": "17362", "Safety Green": "30010", "Safety Orange": "30011"
        },
        # Gildan 64000CVC - Softstyle CVC
        "Gildan Unisex Softstyle® CVC T-Shirt": {
            "White": "30043", "Pitch Black": "30042", "Navy Mist": "30040", "Red Mist": "30044",
            "Gunmetal": "30039", "Dusty Rose": "66770", "Cement": "66768", "Caribbean Mist": "66767",
            "Daisy Mist": "66769", "Cactus": "66766", "Steel Blue": "66771"
        },
        # Gildan 65000 - Softstyle Midweight
        "Gildan Unisex Softstyle® Midweight T-Shirt": {
            "White": "91103", "Pitch Black": "91101", "Navy": "91099", "Red": "91102",
            "Royal": "91104", "Sport Grey": "91105", "Charcoal": "91096", "Maroon": "91098",
            "Irish Green": "91097", "Light Blue": "91109", "Sapphire": "91106",
            "Brown Savana": "91107", "Mustard": "91100", "Graphite Heather": "91108"
        },
        # Gildan 75000 - Hammer Maxweight
        "Gildan Unisex Hammer™ Maxweight T-Shirt": {
            "White": "33660", "Pitch Black": "35158", "Deep Royal": "33658", "Forest Green": "33641",
            "Blue Dusk": "35154", "Cherry Red": "35153", "Dark Chocolate": "35157",
            "Garnet": "35156", "Graphite Heather": "33650", "Tan": "35155"
        },
        # Gildan 980 - Softstyle Lightweight
        "Gildan Unisex Softstyle® Lightweight T-Shirt": {
            "White": "75177", "Black": "75165", "Charcoal": "75166", "Baby Blue": "75164",
            "Caribbean Blue": "52347", "Charity Pink": "75175", "Graphite Heather": "75168",
            "Heather Blue": "75169", "Heather Dark Grey": "75170", "Heather Grey": "75171",
            "Heather Navy": "75172", "Heather Purple": "75173", "Kelly Green": "75174",
            "Military Green": "75176", "Navy": "52376", "Red": "52379"
        },
        # Gildan 3000 - Light Cotton
        "Gildan Unisex Light Cotton T-Shirt": {
            "White": "101285", "Black": "101271", "Navy": "101279", "Red": "101282",
            "Royal": "101283", "Sport Grey": "101284", "Carolina Blue": "101273",
            "Charcoal": "101274", "Forest Green": "101275", "Gold": "101276",
            "Graphite Heather": "101277", "Gravel": "101278", "Heather Navy": "101288",
            "Light Blue": "101289", "Light Pink": "101290", "Maroon": "101291",
            "Military Green": "101292", "Orange": "101293", "Purple": "101294",
            "Sage": "101280", "Sand": "101281"
        },
        # Gildan 2000T - Men's Tall Ultra Cotton
        "Gildan Men's Tall Ultra Cotton® T-Shirt": {
            "White": "17145", "Black": "17139", "Charcoal": "17140", "Navy": "17142",
            "Royal": "17143", "Safety Green": "17144", "Sport Grey": "17146"
        }
    }
    
    updated_count = 0
    products_updated = []
    
    for product_name, color_ids in product_color_mappings.items():
        # Build color_images dict
        color_images = {}
        colors_list = []
        for color, color_id in color_ids.items():
            color_images[color] = f"https://cdn.ssactivewear.com/Images/Color/{color_id}_f_fm.jpg"
            colors_list.append(color)
        
        # Update the product
        result = await db.products.update_one(
            {"brand": "Gildan", "name": product_name},
            {"$set": {
                "color_images": color_images,
                "colors": colors_list
            }}
        )
        
        if result.modified_count > 0:
            updated_count += 1
            products_updated.append(product_name)
    
    return {
        "message": "All Gildan products updated with color images",
        "total_updated": updated_count,
        "products_updated": products_updated
    }

@api_router.post("/admin/update-gildan-all-colors")
async def update_gildan_all_colors(user: dict = Depends(get_admin_user)):
    """Update Gildan products with ALL colors from S&S Activewear wholesaler"""
    
    # Complete color list for Gildan 5000 - 75 colors from S&S Activewear
    gildan_5000_all_colors = [
        "White", "Black", "Antique Cherry Red", "Antique Irish Green", "Antique Jade Dome",
        "Antique Orange", "Antique Sapphire", "Aquatic", "Ash", "Azalea", "Berry", "Blackberry",
        "Blue Dusk", "Brown Savana", "Cardinal", "Carolina Blue", "Charcoal", "Cobalt",
        "Coral Silk", "Cornsilk", "Daisy", "Dark Chocolate", "Dark Heather", "Dusty Rose",
        "Electric Green", "Forest Green", "Garnet", "Gold", "Graphite Heather", "Gravel",
        "Heather Military Green", "Heather Navy", "Heather Radiant Orchid", "Heather Red",
        "Heather Sapphire", "Heliconia", "Ice Grey", "Indigo Blue", "Irish Green", "Kiwi",
        "Light Blue", "Light Pink", "Lilac", "Lime", "Maroon", "Midnight", "Military Green",
        "Mint Green", "Natural", "Navy", "Neon Blue", "Neon Green", "Off White", "Old Gold",
        "Orange", "Purple", "Red", "Royal", "Russet", "Safety Green", "Safety Orange",
        "Safety Pink", "Sand", "Sapphire", "Sky", "Sport Grey", "Sunset", "Tangerine",
        "Tennessee Orange", "Texas Orange", "Tropical Blue", "Turf Green", "Tweed", "Violet",
        "Yellow Haze"
    ]
    
    # Color image IDs for ALL Gildan 5000 colors
    gildan_5000_color_ids = {
        "White": "16813", "Black": "16787", "Antique Cherry Red": "33476", "Antique Irish Green": "33477",
        "Antique Jade Dome": "33496", "Antique Orange": "33499", "Antique Sapphire": "33483",
        "Aquatic": "114510", "Ash": "16785", "Azalea": "16786", "Berry": "33485", "Blackberry": "33481",
        "Blue Dusk": "114522", "Brown Savana": "33488", "Cardinal": "16788", "Carolina Blue": "16789",
        "Charcoal": "16790", "Cobalt": "40523", "Coral Silk": "33479", "Cornsilk": "42437",
        "Daisy": "16791", "Dark Chocolate": "30025", "Dark Heather": "40520", "Dusty Rose": "114512",
        "Electric Green": "37317", "Forest Green": "16793", "Garnet": "32126", "Gold": "30026",
        "Graphite Heather": "46045", "Gravel": "33486", "Heather Military Green": "33475",
        "Heather Navy": "68108", "Heather Radiant Orchid": "52325", "Heather Red": "33487",
        "Heather Sapphire": "33474", "Heliconia": "32127", "Ice Grey": "37312", "Indigo Blue": "16795",
        "Irish Green": "30027", "Kiwi": "30028", "Light Blue": "16798", "Light Pink": "30029",
        "Lilac": "37313", "Lime": "30030", "Maroon": "27238", "Midnight": "37314",
        "Military Green": "30031", "Mint Green": "40519", "Natural": "16802", "Navy": "16803",
        "Neon Blue": "42440", "Neon Green": "42441", "Off White": "114519", "Old Gold": "32128",
        "Orange": "16804", "Purple": "30032", "Red": "27239", "Royal": "16806", "Russet": "33482",
        "Safety Green": "40521", "Safety Orange": "40522", "Safety Pink": "42438", "Sand": "16807",
        "Sapphire": "16808", "Sky": "16809", "Sport Grey": "16810", "Sunset": "37315",
        "Tangerine": "16811", "Tennessee Orange": "32129", "Texas Orange": "42439",
        "Tropical Blue": "37316", "Turf Green": "33495", "Tweed": "33480", "Violet": "16812",
        "Yellow Haze": "16814"
    }
    
    # Build color_images dict
    color_images = {}
    for color, color_id in gildan_5000_color_ids.items():
        color_images[color] = f"https://cdn.ssactivewear.com/Images/Color/{color_id}_f_fm.jpg"
    
    # Update Gildan 5000
    result_5000 = await db.products.update_one(
        {"brand": "Gildan", "name": "Gildan Unisex Heavy Cotton™ T-Shirt"},
        {"$set": {
            "colors": gildan_5000_all_colors,
            "color_images": color_images
        }}
    )
    
    # Complete color list for Gildan 64000 Softstyle - 64 colors
    gildan_64000_all_colors = [
        "White", "Black", "Antique Cherry Red", "Antique Irish Green", "Antique Sapphire",
        "Azalea", "Berry", "Cardinal", "Carolina Blue", "Charcoal", "Cherry Red", "Cobalt",
        "Coral Silk", "Cornsilk", "Daisy", "Dark Heather", "Dark Navy", "Dusty Rose",
        "Graphite Heather", "Gravel", "Heather Irish Green", "Heather Maroon", "Heather Military Green",
        "Heather Navy", "Heather Orange", "Heather Purple", "Heather Red", "Heather Royal",
        "Heather Sapphire", "Heliconia", "Indigo Blue", "Irish Green", "Kelly Green", "Light Blue",
        "Light Pink", "Lilac", "Lime", "Maroon", "Midnight", "Midnight Navy", "Military Green",
        "Mint Green", "Natural", "Navy", "Neon Blue", "Neon Green", "Old Gold", "Orange",
        "Paragon", "Purple", "Red", "Royal", "Russet", "Sand", "Sapphire", "Sport Grey",
        "Tangerine", "Teal", "Tennessee Orange", "Tropical Blue", "Turf Green", "Violet",
        "White Mist", "Yellow Haze"
    ]
    
    result_64000 = await db.products.update_one(
        {"brand": "Gildan", "name": "Gildan Unisex Softstyle® T-Shirt"},
        {"$set": {"colors": gildan_64000_all_colors}}
    )
    
    return {
        "message": "Gildan products updated with all colors",
        "gildan_5000_colors": len(gildan_5000_all_colors),
        "gildan_5000_updated": result_5000.modified_count,
        "gildan_64000_colors": len(gildan_64000_all_colors),
        "gildan_64000_updated": result_64000.modified_count
    }

@api_router.post("/admin/import-hats")
async def import_hats(user: dict = Depends(get_admin_user)):
    """Import YP Classics, Richardson, and Flexfit hats from S&S Activewear"""
    
    hats = [
        # YP Classics
        {
            "style": "6606",
            "name": "YP Classics Retro Trucker Cap",
            "description": "Classic trucker cap with structured front panels and mesh back. Adjustable plastic snapback closure. Pre-curved visor. Mid-profile fit. Perfect for custom embroidery and printing.",
            "price": 15.92,
            "colors": ["White", "Black", "Black/White", "Brown/Khaki", "Caramel", "Charcoal", "Charcoal/Black", "Charcoal/Navy", "Heather Grey", "Kelly Green", "Khaki", "Loden", "Maroon", "Navy", "Navy/White", "Neon Green", "Neon Orange", "Neon Pink", "Orange", "Pink", "Purple", "Red", "Red/White", "Royal", "Royal/White", "Silver", "Texas Orange"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/3783_fm.jpg",
            "brand": "YP Classics"
        },
        {
            "style": "6506",
            "name": "YP Classics Five-Panel Retro Trucker Cap",
            "description": "Five-panel trucker cap with foam front and mesh back. Adjustable snapback closure. Flat bill with slight pre-curve. High-profile crown. Retro styling perfect for screen printing.",
            "price": 16.38,
            "colors": ["White", "Black", "Black/White", "Brown/Khaki", "Charcoal", "Charcoal/White", "Heather/Black", "Heather/White", "Khaki", "Navy", "Navy/White", "Red", "Royal"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/5768_fm.jpg",
            "brand": "YP Classics"
        },
        {
            "style": "6089M",
            "name": "YP Classics Premium Flat Bill Snapback Cap",
            "description": "Premium snapback cap with flat bill. Structured six-panel design. Green undervisor. Adjustable plastic snap closure. High-profile crown. Perfect for embroidery.",
            "price": 17.62,
            "colors": ["White", "Black", "Black/Camo", "Black/Purple", "Black/Red", "Black/Silver", "Camo/Black", "Dark Grey", "Dark Heather", "Dark Navy", "Heather Grey", "Kelly Green", "Khaki", "Maroon", "Navy", "Orange", "Purple", "Red", "Royal", "Silver", "Spruce", "Vegas Gold"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/2293_fm.jpg",
            "brand": "YP Classics"
        },
        {
            "style": "6006",
            "name": "YP Classics Five-Panel Classic Trucker Cap",
            "description": "Classic five-panel trucker with foam front and mesh back. Adjustable snapback closure. Pre-curved visor. Mid-profile crown. Versatile style for custom decoration.",
            "price": 16.84,
            "colors": ["White", "Black", "Black/White", "Brown/White", "Charcoal", "Charcoal/Black", "Charcoal/White", "Heather/Black", "Heather/White", "Kelly/White", "Khaki", "Maroon/White", "Navy", "Navy/White", "Neon Green", "Neon Orange", "Neon Pink", "Orange/White", "Red", "Red/White", "Royal", "Royal/White"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/2523_fm.jpg",
            "brand": "YP Classics"
        },
        {
            "style": "6245CM",
            "name": "YP Classics Classic Dad Hat",
            "description": "Unstructured low-profile dad hat. 100% cotton chino twill. Adjustable buckle strap closure with grommet. Pre-curved visor. Relaxed fit. Perfect for casual embroidery.",
            "price": 19.88,
            "colors": ["White", "Black", "Cranberry", "Dark Grey", "Green Camo", "Khaki", "Light Blue", "Navy", "Orange", "Pink", "Spruce", "Stone"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/4338_fm.jpg",
            "brand": "YP Classics"
        },
        {
            "style": "6789M",
            "name": "YP Classics Premium Curved Bill Snapback Cap",
            "description": "Premium snapback with pre-curved visor. Structured six-panel design. Matching undervisor. Adjustable plastic snap closure. Mid-profile crown.",
            "price": 21.38,
            "colors": ["White", "Black", "Dark Grey", "Heather Grey", "Navy", "Red", "Royal"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/6812_fm.jpg",
            "brand": "YP Classics"
        },
        # Richardson
        {
            "style": "112",
            "name": "Richardson Snapback Trucker Cap",
            "description": "The #1 selling trucker cap. Structured mid-profile design with pre-curved visor. Mesh back panels for breathability. Adjustable plastic snapback closure. Perfect for embroidery and patches.",
            "price": 21.10,
            "colors": ["White", "Black", "Black/Charcoal", "Black/Gold", "Black/White", "Brown/Khaki", "Carmel/Black", "Charcoal/Black", "Charcoal/White", "Dark Green", "Forest Camo", "Grey/Black", "Heather Grey/Black", "Heather Grey/White", "Khaki/Brown", "Loden/Black", "Maroon/Black", "Maroon/White", "Navy", "Navy/White", "Orange/Black", "Orange/White", "Pink/White", "Red", "Red/Black", "Red/White", "Royal", "Royal/White", "Split Black/White", "Texas Orange", "Vegas Gold"],
            "sizes": ["OSFM"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/4332_fm.jpg",
            "brand": "Richardson"
        },
        {
            "style": "115",
            "name": "Richardson Low Pro Trucker Cap",
            "description": "Low-profile trucker with unstructured front. Pre-curved visor. Mesh back panels. Adjustable plastic snapback. Relaxed fit for comfortable all-day wear.",
            "price": 21.56,
            "colors": ["Black", "Black/Charcoal", "Charcoal/Black", "Heather Grey/Black", "Heather Grey/Birch", "Heather Grey/Light Blue", "Khaki/Loden", "Loden/Black", "Navy", "Navy/White"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/5769_fm.jpg",
            "brand": "Richardson"
        },
        {
            "style": "112FP",
            "name": "Richardson Five-Panel Trucker Cap",
            "description": "Five-panel trucker cap with structured front. Mesh back panels. Adjustable plastic snapback closure. Pre-curved visor. Modern styling with classic trucker functionality.",
            "price": 21.10,
            "colors": ["Army Olive Green/Tan", "Black/White", "Charcoal/Black", "Charcoal/White", "Heather Grey/Black", "Navy/White", "Ombre Blue/Navy"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/7614_fm.jpg",
            "brand": "Richardson"
        },
        {
            "style": "110",
            "name": "Richardson R-Flex Trucker Cap",
            "description": "FlexFit technology trucker cap. Structured front with mesh back. Stretch-to-fit comfort. Pre-curved visor. Available in S/M and L/XL sizes.",
            "price": 25.28,
            "colors": ["Black", "Black/White", "Charcoal/Black", "Heather Grey/Black", "Heather Grey/Navy", "Heather Grey/White", "Loden/Black", "Navy", "Royal/White"],
            "sizes": ["S/M", "L/XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/6367_fm.jpg",
            "brand": "Richardson"
        },
        {
            "style": "312",
            "name": "Richardson Twill Back Trucker Cap",
            "description": "Trucker cap with twill back panels instead of mesh. Structured front. Adjustable plastic snapback closure. Pre-curved visor. Unique alternative to traditional mesh truckers.",
            "price": 22.00,
            "colors": ["Black/Charcoal", "Black/White", "Charcoal/Black", "Heather Grey/Black", "Loden/Black", "Navy/White", "Royal/White"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/6850_fm.jpg",
            "brand": "Richardson"
        },
        {
            "style": "112Y",
            "name": "Richardson Youth Trucker Snapback Cap",
            "description": "Youth-sized version of the classic 112 trucker. Structured front with mesh back. Adjustable plastic snapback. Pre-curved visor. Perfect for young fans.",
            "price": 20.84,
            "colors": ["Black", "Heather Grey/Black", "Heather Grey/White", "Navy"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/9254_fm.jpg",
            "brand": "Richardson"
        },
        # Flexfit
        {
            "style": "6277",
            "name": "Flexfit Cotton Blend Cap",
            "description": "The original Flexfit cap. 63% polyester, 34% cotton, 3% spandex blend. Structured mid-profile design. Pre-curved visor. Stretch-to-fit comfort. Silver undervisor. The industry standard for fitted caps.",
            "price": 21.14,
            "colors": ["White", "Black", "Brown", "Carolina Blue", "Coyote Brown", "Dark Grey", "Dark Navy", "Grey", "Khaki", "Maroon", "Navy", "Olive", "Red", "Royal Blue", "Silver", "Spruce", "Texas Orange", "True Navy", "Vegas Gold"],
            "sizes": ["S/M", "L/XL", "XL/2XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/467_fm.jpg",
            "brand": "Flexfit"
        },
        {
            "style": "110M",
            "name": "Flexfit 110® Mesh-Back Cap",
            "description": "Flexfit 110 technology with mesh back panels. Adjustable snapback closure. Structured front. Pre-curved visor. Combines Flexfit comfort with trucker style.",
            "price": 22.04,
            "colors": ["White", "Black", "Black/White", "Brown/Khaki", "Caramel/Khaki", "Charcoal", "Charcoal/Black", "Charcoal/White", "Coyote Brown/Black", "Coyote Brown/Khaki", "Heather Grey/Black", "Heather Grey/White", "Khaki", "Maroon/White", "Navy", "Navy/White", "Red/White", "Royal/White"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/8128_fm.jpg",
            "brand": "Flexfit"
        },
        {
            "style": "110F",
            "name": "Flexfit 110® Snapback Cap",
            "description": "Flexfit 110 adjustable technology. Structured six-panel design. Pre-curved visor. Adjustable snapback closure. Combines Flexfit comfort with snapback adjustability.",
            "price": 28.96,
            "colors": ["White", "Black", "Black/Grey", "Black/Red", "Black/Teal", "Dark Grey", "Heather Grey", "Navy"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/2998_fm.jpg",
            "brand": "Flexfit"
        },
        {
            "style": "180",
            "name": "Flexfit Delta® Seamless Cap",
            "description": "Premium Delta technology with seamless construction. 95% polyester, 5% elastane. Moisture-wicking and quick-dry performance. Stretch-to-fit comfort. Laser-cut ventilation holes.",
            "price": 33.82,
            "colors": ["White", "Black", "Dark Grey", "Navy", "Red", "Silver"],
            "sizes": ["S/M", "L/XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/3755_fm.jpg",
            "brand": "Flexfit"
        },
        {
            "style": "6511",
            "name": "Flexfit Trucker Cap",
            "description": "Classic trucker style with Flexfit stretch-to-fit technology. Structured front with mesh back. Pre-curved visor. Available in one size fits most.",
            "price": 20.86,
            "colors": ["Black", "Black/White", "Caramel/Black", "Charcoal", "Charcoal/Black", "Navy", "Navy/White", "Red", "Royal", "Royal/White"],
            "sizes": ["One Size"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/1682_fm.jpg",
            "brand": "Flexfit"
        },
        {
            "style": "6477",
            "name": "Flexfit Wool-Blend Cap",
            "description": "Premium wool-blend construction. 83% acrylic, 15% wool, 2% spandex. Structured mid-profile design. Pre-curved visor. Stretch-to-fit comfort with classic wool look.",
            "price": 27.00,
            "colors": ["Black", "Brown", "Dark Heather", "Dark Navy", "Grey", "Heather Grey", "Maroon", "Navy", "Red"],
            "sizes": ["S/M", "L/XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/484_fm.jpg",
            "brand": "Flexfit"
        },
        {
            "style": "5001",
            "name": "Flexfit V-Flexfit® Cotton Twill Cap",
            "description": "100% cotton twill construction. V-Flexfit technology for extra stretch comfort. Structured mid-profile design. Pre-curved visor. Classic cotton cap with modern fit.",
            "price": 22.78,
            "colors": ["White", "Black", "Dark Grey", "Grey", "Navy", "Red", "Royal Blue"],
            "sizes": ["S/M", "L/XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/455_fm.jpg",
            "brand": "Flexfit"
        },
        {
            "style": "6597",
            "name": "Flexfit Cool & Dry Sport Cap",
            "description": "100% polyester moisture-wicking performance fabric. Cool & Dry technology keeps you comfortable. Structured mid-profile design. Pre-curved visor. Perfect for athletic wear.",
            "price": 25.24,
            "colors": ["White", "Black", "Grey", "Navy", "Royal Blue"],
            "sizes": ["S/M", "L/XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/2982_fm.jpg",
            "brand": "Flexfit"
        },
        {
            "style": "6110NU",
            "name": "Flexfit NU® Adjustable Cap",
            "description": "NU technology with adjustable fit. Structured six-panel design. Pre-curved visor. Hook and loop closure. Combines premium Flexfit construction with adjustability.",
            "price": 27.28,
            "colors": ["White", "Black", "Dark Grey", "Navy"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/11269_fm.jpg",
            "brand": "Flexfit"
        }
    ]
    
    imported_count = 0
    skipped_count = 0
    
    for hat in hats:
        # Check if product already exists
        existing = await db.products.find_one({"brand": hat["brand"], "name": hat["name"]}, {"_id": 0})
        if existing:
            skipped_count += 1
            continue
            
        product_id = f"prod_{uuid.uuid4().hex[:12]}"
        product_doc = {
            "product_id": product_id,
            "name": hat["name"],
            "description": hat["description"],
            "price": hat["price"],
            "category": "hats",
            "images": [hat["image"]],
            "colors": hat["colors"],
            "sizes": hat["sizes"],
            "brand": hat["brand"],
            "is_blank": True,
            "stock": 500,
            "featured": hat["style"] in ["112", "6277", "6606"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.products.insert_one(product_doc)
        imported_count += 1
    
    return {
        "message": "Hats imported successfully",
        "imported": imported_count,
        "skipped": skipped_count,
        "total": len(hats)
    }

@api_router.post("/admin/import-gildan-hoodies")
async def import_gildan_hoodies(user: dict = Depends(get_admin_user)):
    """Import Gildan hoodie products from S&S Activewear wholesaler data"""
    
    gildan_hoodies = [
        {
            "style": "18500",
            "name": "Gildan Unisex Heavy Blend™ Hooded Sweatshirt",
            "description": "8.0 oz., 50% cotton, 50% polyester preshrunk fleece. Air jet yarn for softer feel and reduced pilling. Double-lined hood with matching drawcord. Pouch pocket. Double-needle stitching throughout. 1x1 athletic rib with spandex. Quarter-turned to eliminate center crease. The classic hoodie for screen printing and embroidery.",
            "price": 32.04,
            "colors": ["White", "Black", "Antique Cherry Red", "Antique Sapphire", "Ash", "Azalea", "Cardinal Red", "Carolina Blue", "Charcoal", "Cherry Red", "Dark Chocolate", "Dark Heather", "Forest Green", "Gold", "Graphite Heather", "Gravel", "Heliconia", "Indigo Blue", "Irish Green", "Light Blue", "Light Pink", "Maroon", "Military Green", "Navy", "Orange", "Purple", "Red", "Royal", "Safety Green", "Safety Orange", "Sand", "Sapphire", "Sport Grey", "Tennessee Orange", "Texas Orange", "Vegas Gold", "Violet", "White", "Yellow Haze"],
            "sizes": ["XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/395_fm.jpg",
            "fabric": "50% Cotton, 50% Polyester",
            "weight": "8.0 oz"
        },
        {
            "style": "18600",
            "name": "Gildan Unisex Heavy Blend™ Full-Zip Hooded Sweatshirt",
            "description": "8.0 oz., 50% cotton, 50% polyester preshrunk fleece. Air jet yarn for softer feel and reduced pilling. Double-lined hood with matching drawcord. Full-zip with YKK zipper. Split pouch pocket. Double-needle stitching throughout. 1x1 athletic rib with spandex.",
            "price": 47.02,
            "colors": ["White", "Black", "Ash", "Cardinal Red", "Carolina Blue", "Dark Chocolate", "Dark Heather", "Forest Green", "Graphite Heather", "Irish Green", "Maroon", "Military Green", "Navy", "Purple", "Red", "Royal", "Sport Grey"],
            "sizes": ["S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/415_fm.jpg",
            "fabric": "50% Cotton, 50% Polyester",
            "weight": "8.0 oz"
        },
        {
            "style": "18500B",
            "name": "Gildan Youth Heavy Blend™ Hooded Sweatshirt",
            "description": "8.0 oz., 50% cotton, 50% polyester preshrunk fleece. Youth version of the classic Heavy Blend hoodie. Air jet yarn for softer feel. Double-lined hood with matching drawcord. Pouch pocket. Double-needle stitching. 1x1 athletic rib with spandex.",
            "price": 33.00,
            "colors": ["White", "Black", "Carolina Blue", "Charcoal", "Dark Heather", "Forest Green", "Gold", "Graphite Heather", "Heliconia", "Irish Green", "Light Pink", "Maroon", "Navy", "Purple", "Red", "Royal", "Sport Grey"],
            "sizes": ["XS", "S", "M", "L", "XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/557_fm.jpg",
            "fabric": "50% Cotton, 50% Polyester",
            "weight": "8.0 oz"
        },
        {
            "style": "SF500",
            "name": "Gildan Unisex Softstyle® Midweight Hooded Sweatshirt",
            "description": "8.5 oz., 80% ring-spun cotton, 20% polyester midweight fleece. Retail-quality Softstyle hoodie with superior softness. Jersey-lined hood. Flat drawcord. Pouch pocket. Tear-away label. Modern fit with side seams.",
            "price": 34.28,
            "colors": ["White", "Black", "Aquatic", "Ash", "Blue Dusk", "Brown Savana", "Cardinal", "Carolina Blue", "Charcoal", "Cobalt", "Cocoa", "Dark Heather", "Dusty Rose", "Forest Green", "Graphite Heather", "Irish Green", "Light Pink", "Maroon", "Military Green", "Natural", "Navy", "Orchid", "Pistachio", "Purple", "Red", "Royal", "Sand", "Sapphire", "Sport Grey", "Stone Blue", "Tangerine", "Vegas Gold", "White"],
            "sizes": ["S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/9352_fm.jpg",
            "fabric": "80% Ring-spun Cotton, 20% Polyester",
            "weight": "8.5 oz"
        },
        {
            "style": "19500",
            "name": "Gildan Unisex Hammer™ Maxweight Hooded Sweatshirt",
            "description": "10.0 oz., 100% ring-spun cotton face fleece. Premium Hammer collection super heavyweight hoodie. 100% cotton face for superior printability. Jersey-lined hood. Flat drawcord. Pouch pocket. Tear-away label. Maximum warmth and durability.",
            "price": 45.46,
            "colors": ["Blue Dusk", "Cherry Red", "Deep Royal", "Garnet", "Gravel", "Off White", "Olive", "Pitch Black", "Tan"],
            "sizes": ["S", "M", "L", "XL", "2XL", "3XL", "4XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/12449_fm.jpg",
            "fabric": "100% Ring-spun Cotton Face",
            "weight": "10.0 oz"
        },
        {
            "style": "12500",
            "name": "Gildan Unisex DryBlend® Hooded Sweatshirt",
            "description": "9.0 oz., 50% cotton, 50% DryBlend polyester preshrunk fleece. Moisture-wicking DryBlend technology. Air jet yarn for softer feel. Double-lined hood with matching drawcord. Pouch pocket. Double-needle stitching. 1x1 athletic rib with spandex.",
            "price": 45.30,
            "colors": ["White", "Black", "Ash", "Charcoal", "Forest Green", "Maroon", "Navy", "Red", "Royal", "Safety Green", "Safety Orange", "Sport Grey"],
            "sizes": ["S", "M", "L", "XL", "2XL", "3XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/423_fm.jpg",
            "fabric": "50% Cotton, 50% Polyester DryBlend",
            "weight": "9.0 oz"
        },
        {
            "style": "18600B",
            "name": "Gildan Youth Heavy Blend™ Full-Zip Hooded Sweatshirt",
            "description": "8.0 oz., 50% cotton, 50% polyester preshrunk fleece. Youth full-zip hoodie. Air jet yarn for softer feel. Double-lined hood with matching drawcord. Full YKK zipper. Split pouch pocket. Double-needle stitching. 1x1 athletic rib with spandex.",
            "price": 39.74,
            "colors": ["Black", "Navy", "Red", "Royal", "Sport Grey"],
            "sizes": ["XS", "S", "M", "L", "XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/562_fm.jpg",
            "fabric": "50% Cotton, 50% Polyester",
            "weight": "8.0 oz"
        },
        {
            "style": "SF500B",
            "name": "Gildan Youth Softstyle® Midweight Hooded Sweatshirt",
            "description": "8.5 oz., 80% ring-spun cotton, 20% polyester midweight fleece. Youth Softstyle hoodie with retail-quality softness. Jersey-lined hood. Flat drawcord. Pouch pocket. Tear-away label. Modern fit.",
            "price": 30.54,
            "colors": ["White", "Black", "Daisy", "Dark Heather", "Forest Green", "Light Pink", "Maroon", "Military Green", "Navy", "Pink Lemonade", "Red", "Royal", "Sand", "Sport Grey", "Stone Blue"],
            "sizes": ["XS", "S", "M", "L", "XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/11668_fm.jpg",
            "fabric": "80% Ring-spun Cotton, 20% Polyester",
            "weight": "8.5 oz"
        }
    ]
    
    imported_count = 0
    skipped_count = 0
    
    for hoodie in gildan_hoodies:
        # Check if product already exists
        existing = await db.products.find_one({"brand": "Gildan", "name": hoodie["name"]}, {"_id": 0})
        if existing:
            skipped_count += 1
            continue
            
        product_id = f"prod_{uuid.uuid4().hex[:12]}"
        product_doc = {
            "product_id": product_id,
            "name": hoodie["name"],
            "description": hoodie["description"],
            "price": hoodie["price"],
            "category": "hoodies",
            "images": [hoodie["image"]],
            "colors": hoodie["colors"],
            "sizes": hoodie["sizes"],
            "brand": "Gildan",
            "is_blank": True,
            "stock": 500,
            "featured": hoodie["style"] in ["18500", "SF500"],
            "fabric": hoodie["fabric"],
            "weight": hoodie["weight"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.products.insert_one(product_doc)
        imported_count += 1
    
    return {
        "message": "Gildan hoodies imported successfully",
        "imported": imported_count,
        "skipped": skipped_count,
        "total": len(gildan_hoodies)
    }

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
        color_images_5000[color] = f"https://cdn.ssactivewear.com/Images/Color/{color_id}_f_fm.jpg"
    
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
        color_images_64000[color] = f"https://cdn.ssactivewear.com/Images/Color/{color_id}_f_fm.jpg"
    
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
        color_images_2000[color] = f"https://cdn.ssactivewear.com/Images/Color/{color_id}_f_fm.jpg"
    
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
        color_images_8000[color] = f"https://cdn.ssactivewear.com/Images/Color/{color_id}_f_fm.jpg"
    
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


@api_router.post("/admin/import-hats")
async def import_hats(user: dict = Depends(get_admin_user)):
    """Import hat products from YP Classics, Richardson, and Flexfit brands"""
    
    hats_data = [
        # YP Classics (16 products)
        {
            "style": "6606",
            "name": "YP Classics Retro Trucker Cap",
            "description": "Classic retro trucker cap with foam front and mesh back. Snapback closure for adjustable fit. Six-panel construction with structured crown. Pre-curved visor. Perfect for custom embroidery and screen printing.",
            "price": 15.92,
            "brand": "YP Classics",
            "colors": ["White", "Black", "Black/White", "Black/White/Black", "Brown/Khaki", "Caramel", "Caramel/Black", "Charcoal", "Charcoal/Black", "Charcoal/Navy", "Charcoal/Neon Green", "Heather Grey", "Kelly/White", "Khaki", "Maroon/White", "Navy", "Navy/White", "Navy/White/Navy", "Olive", "Orange", "Purple", "Red", "Red/Black", "Red/White", "Red/White/Red", "Royal", "Royal/White", "Royal/White/Royal", "Silver", "Texas Orange", "Teal", "Vegas Gold", "White/Black", "White/Maroon", "White/Navy", "White/Red", "White/Royal", "Yellow", "Charcoal/White", "Heather/Black", "Kelly", "Light Pink", "Loden", "Pink", "Red/White/Black", "Royal/White/Black"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/3783_fm.jpg",
            "fabric": "Cotton/Polyester Mesh",
            "weight": "N/A"
        },
        {
            "style": "6506",
            "name": "YP Classics Five-Panel Retro Trucker Cap",
            "description": "Five-panel retro trucker cap with foam front and mesh back. Snapback closure. Structured crown with flat brim. Modern streetwear silhouette. Great for embroidery and patches.",
            "price": 16.38,
            "brand": "YP Classics",
            "colors": ["White", "Black", "Black/White", "Brown/Khaki", "Charcoal", "Charcoal/White", "Heather/Black", "Heather/White", "Khaki", "Navy", "Navy/White", "Red/White", "Royal/White"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/5768_fm.jpg",
            "fabric": "Cotton/Polyester Mesh",
            "weight": "N/A"
        },
        {
            "style": "6089M",
            "name": "YP Classics Premium Flat Bill Snapback Cap",
            "description": "Premium snapback with flat bill visor. Structured six-panel design with classic fit. Green undervisor. Plastic snap closure. Pro-style cap perfect for embroidery and sublimation.",
            "price": 17.62,
            "brand": "YP Classics",
            "colors": ["White", "Black", "Black/Camo", "Black/Purple", "Black/Red", "Black/Silver", "Camo/Black", "Dark Grey", "Dark Heather", "Dark Heather/Black", "Dark Navy", "Gold", "Heather Grey", "Kelly", "Khaki", "Maroon", "Navy", "Navy/White", "Purple", "Red", "Royal", "Sport Grey"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/2293_fm.jpg",
            "fabric": "80% Acrylic, 20% Wool",
            "weight": "N/A"
        },
        {
            "style": "6006",
            "name": "YP Classics Five-Panel Classic Trucker Cap",
            "description": "Classic five-panel trucker cap with foam front and mesh back. Snapback closure. Structured crown. Pre-curved visor. Timeless trucker style for casual and promotional wear.",
            "price": 16.84,
            "brand": "YP Classics",
            "colors": ["White", "Black", "Black/White", "Black/White/Black", "Brown/White", "Charcoal", "Charcoal/Black", "Charcoal/White", "Heather/Black", "Heather/White", "Kelly/White/Kelly", "Khaki/White", "Maroon/White", "Navy", "Navy/White", "Navy/White/Navy", "Purple/White", "Red/White", "Red/White/Red", "Royal", "Royal/White"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/2523_fm.jpg",
            "fabric": "Cotton/Polyester Mesh",
            "weight": "N/A"
        },
        {
            "style": "6245CM",
            "name": "YP Classics Classic Dad Hat",
            "description": "Unstructured low-profile dad hat with pre-curved visor. Cotton twill construction. Slide buckle closure with grommet. Soft crown for comfortable all-day wear. Classic relaxed style.",
            "price": 19.88,
            "brand": "YP Classics",
            "colors": ["White", "Black", "Cranberry", "Dark Grey", "Green Camo", "Khaki", "Light Blue", "Navy", "Orange", "Pink", "Spruce", "Stone"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/4338_fm.jpg",
            "fabric": "100% Cotton",
            "weight": "N/A"
        },
        {
            "style": "6789M",
            "name": "YP Classics Premium Curved Bill Snapback Cap",
            "description": "Premium snapback cap with pre-curved visor. Structured six-panel design. Plastic snap closure. Grey undervisor. Professional look for corporate and team apparel.",
            "price": 21.38,
            "brand": "YP Classics",
            "colors": ["White", "Black", "Dark Grey", "Heather Grey", "Navy", "Red", "Royal"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/6812_fm.jpg",
            "fabric": "80% Acrylic, 20% Wool",
            "weight": "N/A"
        },
        {
            "style": "6389",
            "name": "YP Classics CVC Snapback Cap",
            "description": "CVC cotton/polyester blend snapback cap. Six-panel structured design with pre-curved visor. Plastic snap closure. Soft-touch fabric for comfort. Modern casual style.",
            "price": 13.50,
            "brand": "YP Classics",
            "colors": ["White", "Black", "Charcoal", "Dark Heather Grey", "Navy"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/10422_fm.jpg",
            "fabric": "Cotton/Polyester CVC",
            "weight": "N/A"
        },
        {
            "style": "6601",
            "name": "YP Classics Elite Cap",
            "description": "Elite performance cap with structured crown. Pre-curved visor with snapback closure. Six-panel construction. Athletic style suitable for sports and casual wear.",
            "price": 16.82,
            "brand": "YP Classics",
            "colors": ["Black", "Black/White", "Charcoal", "Charcoal/Black", "Heather/Black", "Heather/White", "Moss Green/Khaki", "Navy", "Navy/White"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/11758_fm.jpg",
            "fabric": "Polyester",
            "weight": "N/A"
        },
        {
            "style": "6007",
            "name": "YP Classics Five-Panel Cotton Twill Snapback Cap",
            "description": "Five-panel cotton twill snapback. Structured crown with flat visor. Plastic snap closure. Clean minimal design. Perfect canvas for embroidery.",
            "price": 18.38,
            "brand": "YP Classics",
            "colors": ["White", "Black", "Black/Red", "Navy", "Royal Blue"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/2522_fm.jpg",
            "fabric": "100% Cotton Twill",
            "weight": "N/A"
        },
        {
            "style": "5089M",
            "name": "YP Classics Premium Five-Panel Snapback Cap",
            "description": "Premium five-panel snapback with structured crown. Flat bill visor. Plastic snap closure. Green undervisor. Streetwear-inspired design.",
            "price": 21.58,
            "brand": "YP Classics",
            "colors": ["White", "Black", "Dark Grey", "Heather Grey", "Navy", "Royal"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/3782_fm.jpg",
            "fabric": "80% Acrylic, 20% Wool",
            "weight": "N/A"
        },
        {
            "style": "5789M",
            "name": "YP Classics Premium Five-Panel Curved Bill Snapback Cap",
            "description": "Premium five-panel snapback with curved visor. Structured crown. Plastic snap closure. Modern profile. Great for custom branding.",
            "price": 21.38,
            "brand": "YP Classics",
            "colors": ["Black", "Heather Grey", "Navy"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/8160_fm.jpg",
            "fabric": "80% Acrylic, 20% Wool",
            "weight": "N/A"
        },
        {
            "style": "6245PT",
            "name": "YP Classics Peached Cotton Twill Dad Hat",
            "description": "Peached cotton twill dad hat with soft hand feel. Unstructured low-profile crown. Pre-curved visor. Slide buckle closure. Washed vintage look.",
            "price": 19.84,
            "brand": "YP Classics",
            "colors": ["White", "Black", "Light Grey", "Loden"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/5646_fm.jpg",
            "fabric": "100% Cotton Twill",
            "weight": "N/A"
        },
        {
            "style": "6245EC",
            "name": "YP Classics EcoWash Dad Hat",
            "description": "Eco-friendly dad hat with washed finish. Unstructured low-profile design. Pre-curved visor. Slide buckle closure. Sustainable style choice.",
            "price": 20.94,
            "brand": "YP Classics",
            "colors": ["Black", "Navy", "Oak"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/9271_fm.jpg",
            "fabric": "100% Cotton",
            "weight": "N/A"
        },
        {
            "style": "6502",
            "name": "YP Classics Lightly-Structured Five-Panel Snapback Cap",
            "description": "Lightly-structured five-panel cap. Pre-curved visor with snapback closure. Mid-profile crown. Versatile everyday style.",
            "price": 15.52,
            "brand": "YP Classics",
            "colors": ["Black", "Charcoal", "Navy"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/5766_fm.jpg",
            "fabric": "Cotton/Polyester",
            "weight": "N/A"
        },
        
        # Richardson (11 products)
        {
            "style": "112",
            "name": "Richardson Snapback Trucker Cap",
            "description": "The most popular trucker cap in the industry. Structured mid-profile with pre-curved visor. Mesh back with snapback closure. 112 is the go-to trucker for custom embroidery and screen printing.",
            "price": 21.10,
            "brand": "Richardson",
            "colors": ["White", "Black", "Black/Charcoal", "Black/Gold", "Black/Vegas Gold", "Black/White", "Black/White/Heather Grey", "Black/White/Red", "Brown/Khaki", "Carmel/Black", "Charcoal/Black", "Charcoal/White", "Heather Grey/Black", "Heather Grey/Light Grey", "Heather Grey/White", "Kelly/White", "Khaki/White", "Loden/Black", "Maroon/White", "Navy", "Navy/White", "Orange/White", "Pink/White", "Purple/White", "Red/White", "Royal/White", "Split Charcoal/White", "Sport Grey", "Texas Orange/White", "Vegas Gold", "White/Black", "White/Charcoal", "White/Columbia Blue", "White/Dark Green", "White/Maroon", "White/Navy", "White/Red", "White/Royal", "Army Olive Green", "Cardinal/White", "Charcoal/Navy", "Columbia Blue/White", "Dark Green/White", "Hot Pink/White", "Khaki/Burgundy", "Khaki/Coffee", "Red/Black/White", "Red/White/Blue"],
            "sizes": ["OSFM"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/4332_fm.jpg",
            "fabric": "Cotton/Polyester Mesh",
            "weight": "N/A"
        },
        {
            "style": "112FP",
            "name": "Richardson Five-Panel Trucker Cap",
            "description": "Five-panel version of the iconic 112 trucker. Structured crown with mesh back. Pre-curved visor. Snapback closure. Modern streetwear appeal.",
            "price": 21.10,
            "brand": "Richardson",
            "colors": ["Army Olive Green/Tan", "Black/White", "Charcoal/Black", "Charcoal/White", "Heather Grey/Black", "Navy/White", "Ombre Blue/Navy"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/7614_fm.jpg",
            "fabric": "Cotton/Polyester Mesh",
            "weight": "N/A"
        },
        {
            "style": "110",
            "name": "Richardson R-Flex Trucker Cap",
            "description": "Fitted trucker cap with stretch mesh back. Structured crown with pre-curved visor. R-Flex fitted comfort. Premium trucker style.",
            "price": 25.28,
            "brand": "Richardson",
            "colors": ["Black", "Black/White", "Charcoal/Black", "Heather Grey/Black", "Heather Grey/Navy", "Heather Grey/White", "Loden/Black", "Navy", "Royal/White"],
            "sizes": ["S/M", "L/XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/6367_fm.jpg",
            "fabric": "Cotton/Spandex Mesh",
            "weight": "N/A"
        },
        {
            "style": "112Y",
            "name": "Richardson Youth Trucker Snapback Cap",
            "description": "Youth-sized version of the classic 112 trucker. Structured crown with mesh back. Snapback closure sized for kids. Same quality construction.",
            "price": 20.84,
            "brand": "Richardson",
            "colors": ["Black", "Heather Grey/Black", "Heather Grey/White", "Navy"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/9254_fm.jpg",
            "fabric": "Cotton/Polyester Mesh",
            "weight": "N/A"
        },
        {
            "style": "312",
            "name": "Richardson Twill Back Trucker Cap",
            "description": "Trucker cap with solid twill back instead of mesh. Structured crown with pre-curved visor. Snapback closure. Unique solid-back trucker style.",
            "price": 22.00,
            "brand": "Richardson",
            "colors": ["Black/Charcoal", "Black/White", "Charcoal/Black", "Heather Grey/Black", "Loden/Black", "Navy/White", "Royal/White"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/6850_fm.jpg",
            "fabric": "Cotton Twill",
            "weight": "N/A"
        },
        {
            "style": "632",
            "name": "Richardson Laser Perf R-Flex Cap",
            "description": "Performance cap with laser perforated panels for breathability. R-Flex fitted construction. Pre-curved visor. Athletic performance style.",
            "price": 29.00,
            "brand": "Richardson",
            "colors": ["Black", "Charcoal"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/15653_fm.jpg",
            "fabric": "Polyester Performance",
            "weight": "N/A"
        },
        
        # Flexfit (18 products)
        {
            "style": "6277",
            "name": "Flexfit Cotton Blend Cap",
            "description": "The original Flexfit cap. 6-panel structured mid-profile with pre-curved visor. Patented Flexfit technology for comfortable stretch fit. The industry standard for fitted caps.",
            "price": 21.14,
            "brand": "Flexfit",
            "colors": ["White", "Black", "Brown", "Carolina Blue", "Coyote Brown", "Dark Grey", "Dark Navy", "Grey", "Khaki", "Kryptek Typhon", "Maroon", "Navy", "Olive Drab", "Purple", "Red", "Royal", "Silver", "Spruce", "Texas Orange", "True Navy", "Vegas Gold"],
            "sizes": ["S/M", "L/XL", "XL/2XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/467_fm.jpg",
            "fabric": "63% Polyester, 34% Cotton, 3% Spandex",
            "weight": "N/A"
        },
        {
            "style": "110M",
            "name": "Flexfit 110 Mesh-Back Cap",
            "description": "Flexfit 110 with mesh back panels. Adjustable snapback with Flexfit comfort. Structured crown with pre-curved visor. Breathable mesh for warm weather.",
            "price": 22.04,
            "brand": "Flexfit",
            "colors": ["White", "Black", "Black/White", "Brown/Khaki", "Caramel/Khaki", "Charcoal", "Charcoal/Black", "Charcoal/White", "Coyote Brown/Black", "Coyote Brown/Khaki", "Heather Grey/Black", "Heather Grey/White", "Khaki/Brown", "Loden/Black", "Maroon/White", "Navy", "Navy/White", "Red/White", "Royal/White", "Silver/Black"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/8128_fm.jpg",
            "fabric": "Cotton/Polyester Mesh",
            "weight": "N/A"
        },
        {
            "style": "110F",
            "name": "Flexfit 110 Snapback Cap",
            "description": "Flexfit 110 flat bill snapback. Structured crown with flat visor. Adjustable snapback with Flexfit technology. Pro style with premium fit.",
            "price": 28.96,
            "brand": "Flexfit",
            "colors": ["White", "Black", "Dark Navy", "Heather Grey", "Khaki", "Maroon", "Navy", "Royal"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/2998_fm.jpg",
            "fabric": "83% Acrylic, 15% Wool, 2% Spandex",
            "weight": "N/A"
        },
        {
            "style": "6511",
            "name": "Flexfit Trucker Cap",
            "description": "Flexfit trucker with mesh back. Structured crown with pre-curved visor. Flexfit fitted comfort without snapback. Classic trucker meets Flexfit technology.",
            "price": 20.86,
            "brand": "Flexfit",
            "colors": ["Black", "Black/White", "Caramel/Black", "Charcoal", "Charcoal/Black", "Navy", "Navy/White", "Navy/White/Navy", "Red", "Royal", "Royal/White"],
            "sizes": ["One Size"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/1682_fm.jpg",
            "fabric": "Cotton/Polyester Mesh",
            "weight": "N/A"
        },
        {
            "style": "6477",
            "name": "Flexfit Wool-Blend Cap",
            "description": "Premium wool-blend Flexfit cap. Structured mid-profile with pre-curved visor. Flexfit fitted technology. Elevated material for sophisticated style.",
            "price": 27.00,
            "brand": "Flexfit",
            "colors": ["Black", "Brown", "Dark Heather", "Dark Navy", "Grey", "Heather Grey", "Maroon", "Navy", "Red"],
            "sizes": ["S/M", "L/XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/484_fm.jpg",
            "fabric": "98% Polyester, 2% Spandex",
            "weight": "N/A"
        },
        {
            "style": "110P",
            "name": "Flexfit 110 Cool & Dry Mini-Piqué Cap",
            "description": "Performance piqué fabric with Cool & Dry technology. Flexfit 110 adjustable construction. Moisture-wicking for athletic wear. Structured crown.",
            "price": 25.52,
            "brand": "Flexfit",
            "colors": ["White", "Black", "Navy", "Royal Blue", "Silver"],
            "sizes": ["Adjustable"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/3750_fm.jpg",
            "fabric": "100% Polyester Mini-Piqué",
            "weight": "N/A"
        },
        {
            "style": "6597",
            "name": "Flexfit Cool & Dry Sport Cap",
            "description": "Cool & Dry performance fabric Flexfit cap. Moisture-wicking and quick-drying. Structured crown with pre-curved visor. Ideal for sports and outdoor activities.",
            "price": 25.24,
            "brand": "Flexfit",
            "colors": ["White", "Black", "Grey", "Navy", "Royal Blue"],
            "sizes": ["S/M", "L/XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/2982_fm.jpg",
            "fabric": "100% Polyester Cool & Dry",
            "weight": "N/A"
        },
        {
            "style": "6533",
            "name": "Flexfit Ultrafiber Mesh Cap",
            "description": "Ultrafiber cap with mesh side panels. Flexfit fitted construction. Structured crown with pre-curved visor. Enhanced breathability.",
            "price": 25.08,
            "brand": "Flexfit",
            "colors": ["Black", "Dark Grey", "Navy", "Royal Blue"],
            "sizes": ["S/M", "L/XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/2170_fm.jpg",
            "fabric": "Polyester Ultrafiber/Mesh",
            "weight": "N/A"
        },
        {
            "style": "6580",
            "name": "Flexfit Pro-Formance Cap",
            "description": "Pro-Formance athletic cap with Flexfit technology. Structured performance crown. Pre-curved visor. Professional sports styling.",
            "price": 25.36,
            "brand": "Flexfit",
            "colors": ["Black", "Dark Navy", "Grey"],
            "sizes": ["S/M", "L/XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/1330_fm.jpg",
            "fabric": "100% Polyester Pro-Formance",
            "weight": "N/A"
        },
        {
            "style": "6277Y",
            "name": "Flexfit Youth Cotton Blend Cap",
            "description": "Youth-sized version of the classic 6277 Flexfit. Same quality construction in kid-friendly sizes. Structured crown with pre-curved visor.",
            "price": 24.42,
            "brand": "Flexfit",
            "colors": ["Black", "Navy"],
            "sizes": ["One Size"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/9359_fm.jpg",
            "fabric": "63% Polyester, 34% Cotton, 3% Spandex",
            "weight": "N/A"
        },
        {
            "style": "6297F",
            "name": "Flexfit Pro-Baseball On Field Cap",
            "description": "Pro-style baseball cap designed for on-field performance. Flexfit fitted technology. Structured crown. Official baseball cap construction.",
            "price": 22.80,
            "brand": "Flexfit",
            "colors": ["Red"],
            "sizes": ["S/M", "L/XL"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/2462_fm.jpg",
            "fabric": "100% Polyester",
            "weight": "N/A"
        },
        {
            "style": "6311",
            "name": "Flexfit Mélange Trucker Cap",
            "description": "Mélange heathered fabric trucker with mesh back. Flexfit adjustable snapback. Modern heathered look. Pre-curved visor.",
            "price": 21.32,
            "brand": "Flexfit",
            "colors": ["Heather Grey/Red", "Heather Grey/Royal"],
            "sizes": ["One Size"],
            "image": "https://cdn.ssactivewear.com/cdn-cgi/image/quality=80,w=400,f=auto/Images/Style/4303_fm.jpg",
            "fabric": "Polyester Mélange/Mesh",
            "weight": "N/A"
        }
    ]
    
    imported_count = 0
    skipped_count = 0
    
    for hat in hats_data:
        # Check if product already exists
        existing = await db.products.find_one({"brand": hat["brand"], "name": hat["name"]}, {"_id": 0})
        if existing:
            skipped_count += 1
            continue
            
        product_id = f"prod_{uuid.uuid4().hex[:12]}"
        product_doc = {
            "product_id": product_id,
            "name": hat["name"],
            "description": hat["description"],
            "price": hat["price"],
            "category": "hats",
            "images": [hat["image"]],
            "colors": hat["colors"],
            "sizes": hat["sizes"],
            "brand": hat["brand"],
            "is_blank": True,
            "stock": 300,
            "featured": hat["style"] in ["6277", "112", "6606"],  # Feature popular styles
            "fabric": hat["fabric"],
            "weight": hat["weight"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.products.insert_one(product_doc)
        imported_count += 1
    
    return {
        "message": "Hats imported successfully",
        "imported": imported_count,
        "skipped": skipped_count,
        "total": len(hats_data),
        "brands": ["YP Classics", "Richardson", "Flexfit"]
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
    return {"message": "Revolution Printing API", "version": "1.0.0"}

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

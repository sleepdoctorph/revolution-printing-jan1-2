import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ChevronLeft, Check, ShoppingBag, Minus, Plus } from 'lucide-react';
import { Button } from '../components/ui/button';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Color name to hex mapping
const colorMap = {
  'white': '#FFFFFF',
  'black': '#000000',
  'navy': '#001F3F',
  'red': '#DC2626',
  'royal': '#4169E1',
  'sport grey': '#8B8B8B',
  'charcoal': '#36454F',
  'forest green': '#228B22',
  'maroon': '#800000',
  'carolina blue': '#56A0D3',
  'ash': '#B2BEB5',
  'gold': '#FFD700',
  'orange': '#FF6600',
  'purple': '#800080',
  'irish green': '#009A44',
  'heliconia': '#E4007C',
  'light blue': '#ADD8E6',
  'light pink': '#FFB6C1',
  'khaki': '#C3B091',
  'brown': '#8B4513',
  'heather grey': '#9E9E9E',
  'dark grey': '#4A4A4A',
  'dark heather': '#4A4A4A',
  'coyote brown': '#8B6914',
};

const getColorHex = (colorName) => {
  if (!colorName) return '#CCCCCC';
  const key = colorName.toLowerCase().split('/')[0].trim();
  return colorMap[key] || '#CCCCCC';
};

const ReviewOrderPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { addItem } = useCart();
  const { user } = useAuth();
  
  const [quantity, setQuantity] = useState(location.state?.quantity || 1);

  // Get data from navigation state
  const { product, selectedColor, selectedSize, design, printPlacement } = location.state || {};

  // If no data, redirect back to shop
  if (!product || !design) {
    navigate('/shop');
    return null;
  }

  const handleAddToCart = () => {
    addItem(product, quantity, selectedColor, selectedSize, design, printPlacement);
    toast.success('Added to cart!');
    navigate('/shop');
  };

  const handleCheckout = () => {
    if (!user) {
      toast.error('Please sign in to checkout');
      navigate('/login', { state: { from: '/review-order' } });
      return;
    }
    addItem(product, quantity, selectedColor, selectedSize, design, printPlacement);
    navigate('/checkout');
  };

  const totalPrice = product.price * quantity;
  const colorHex = getColorHex(selectedColor);
  const placementLabel = printPlacement === 'left-chest' ? 'Left Chest' : printPlacement === 'back' ? 'Back' : 'Front';

  return (
    <div className="min-h-screen bg-background py-8" data-testid="review-order-page">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Progress Steps */}
        <div className="flex items-center justify-center mb-8">
          <div className="flex items-center">
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary text-white font-bold">
              <Check className="w-5 h-5" />
            </div>
            <span className="ml-2 text-sm font-medium text-muted-foreground">Product</span>
          </div>
          <div className="w-16 h-1 bg-primary mx-2" />
          <div className="flex items-center">
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary text-white font-bold">
              <Check className="w-5 h-5" />
            </div>
            <span className="ml-2 text-sm font-medium text-muted-foreground">Design</span>
          </div>
          <div className="w-16 h-1 bg-primary mx-2" />
          <div className="flex items-center">
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary text-white font-bold">
              3
            </div>
            <span className="ml-2 text-sm font-bold">Review & Pay</span>
          </div>
        </div>

        {/* Back Button */}
        <Button
          variant="ghost"
          onClick={() => navigate(-1)}
          className="mb-6"
          data-testid="back-button"
        >
          <ChevronLeft className="h-5 w-5 mr-1" />
          Back to Design Selection
        </Button>

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="font-heading text-3xl md:text-4xl font-bold mb-2">
            Review Your Order
          </h1>
          <p className="text-muted-foreground">
            Here&apos;s a preview of your custom product
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-12">
          {/* Mockup Preview */}
          <div className="space-y-4">
            <div 
              className="aspect-square rounded-xl border-2 border-black overflow-hidden shadow-brutal-lg relative"
              style={{ backgroundColor: colorHex }}
            >
              {/* Product Base Image */}
              <img
                src={product.images?.[0] || 'https://via.placeholder.com/600'}
                alt={product.name}
                className="w-full h-full object-cover mix-blend-multiply"
              />
              
              {/* Design Overlay */}
              {design.image_url && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <img
                    src={design.image_url.startsWith('/') ? `${API_URL}${design.image_url}` : design.image_url}
                    alt={design.name}
                    className="max-w-[40%] max-h-[40%] object-contain drop-shadow-lg"
                    style={{
                      marginTop: product.category === 'hats' ? '-10%' : '0',
                    }}
                  />
                </div>
              )}
            </div>

            {/* Design Preview Thumbnail */}
            <div className="flex items-center gap-4 p-4 bg-card border-2 border-black rounded-xl shadow-brutal">
              <div className="w-16 h-16 rounded-lg border-2 border-black overflow-hidden bg-white">
                {design.image_url ? (
                  <img
                    src={design.image_url.startsWith('/') ? `${API_URL}${design.image_url}` : design.image_url}
                    alt={design.name}
                    className="w-full h-full object-contain p-1"
                  />
                ) : (
                  <div className="w-full h-full bg-muted" />
                )}
              </div>
              <div>
                <p className="font-bold">{design.name}</p>
                <p className="text-sm text-muted-foreground">Selected Design</p>
              </div>
            </div>
          </div>

          {/* Order Details */}
          <div className="space-y-6">
            {/* Product Info */}
            <div className="bg-card border-2 border-black rounded-xl p-6 shadow-brutal">
              <h2 className="font-heading text-2xl font-bold mb-4">Order Summary</h2>
              
              <div className="space-y-4">
                {/* Product */}
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-bold">{product.name}</p>
                    <p className="text-sm text-muted-foreground">{product.brand}</p>
                  </div>
                  <p className="font-bold">${product.price.toFixed(2)}</p>
                </div>

                <div className="border-t pt-4 space-y-2">
                  {/* Color */}
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Color</span>
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-5 h-5 rounded-full border-2 border-gray-300"
                        style={{ backgroundColor: colorHex }}
                      />
                      <span className="font-medium">{selectedColor}</span>
                    </div>
                  </div>

                  {/* Size */}
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Size</span>
                    <span className="font-medium">{selectedSize}</span>
                  </div>

                  {/* Design */}
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Design</span>
                    <span className="font-medium">{design.name}</span>
                  </div>

                  {/* Print Placement */}
                  {product.category !== 'mugs' && (
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Print Placement</span>
                      <span className="font-medium">{placementLabel}</span>
                    </div>
                  )}
                </div>

                {/* Quantity */}
                <div className="border-t pt-4">
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Quantity</span>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => setQuantity(Math.max(1, quantity - 1))}
                        disabled={quantity <= 1}
                        className="h-8 w-8 border-2 border-black"
                      >
                        <Minus className="h-4 w-4" />
                      </Button>
                      <span className="w-8 text-center font-bold">{quantity}</span>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => setQuantity(quantity + 1)}
                        className="h-8 w-8 border-2 border-black"
                      >
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Total */}
                <div className="border-t pt-4">
                  <div className="flex justify-between items-center">
                    <span className="text-lg font-bold">Total</span>
                    <span className="text-2xl font-bold text-primary">${totalPrice.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-3">
              <Button
                onClick={handleCheckout}
                className="w-full bg-primary text-white border-2 border-black shadow-brutal hover-lift h-14 text-lg"
                data-testid="checkout-button"
              >
                Proceed to Checkout
              </Button>

              <Button
                onClick={handleAddToCart}
                variant="outline"
                className="w-full border-2 border-black shadow-brutal hover-lift h-14 text-lg"
                data-testid="add-to-cart-button"
              >
                <ShoppingBag className="h-5 w-5 mr-2" />
                Add to Cart & Continue Shopping
              </Button>
            </div>

            {/* Info Note */}
            <p className="text-sm text-muted-foreground text-center">
              Price includes the design. Free shipping on orders over $50.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReviewOrderPage;

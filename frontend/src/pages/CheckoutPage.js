import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { CreditCard, Truck, ShieldCheck, Loader2, CheckCircle, Mail, AlertTriangle } from 'lucide-react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Separator } from '../components/ui/separator';
import { Checkbox } from '../components/ui/checkbox';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const CheckoutPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { items, totalPrice, clearCart } = useCart();
  const { user, isAuthenticated } = useAuth();
  
  // Check if this is guest checkout
  const isGuestCheckout = location.state?.guestCheckout || !isAuthenticated;
  
  const [loading, setLoading] = useState(false);
  const [orderComplete, setOrderComplete] = useState(false);
  const [orderId, setOrderId] = useState('');
  const [subscribeToUpdates, setSubscribeToUpdates] = useState(false);
  
  // Custom order confirmation checkboxes
  const [confirmations, setConfirmations] = useState({
    printReady: false,
    noDesignService: false,
    spellingResponsibility: false,
    sizeAdjustment: false,
    turnaround: false,
    shippingFees: false,
    designedProducts: false,
    designedShipping: false
  });
  
  const [shippingInfo, setShippingInfo] = useState({
    firstName: user?.name?.split(' ')[0] || '',
    lastName: user?.name?.split(' ').slice(1).join(' ') || '',
    email: user?.email || '',
    address: '',
    city: '',
    state: '',
    zip: '',
    phone: '',
    country: 'CA'
  });

  // Calculate shipping based on ChitChats rates
  // In-house designs: Free shipping for orders $75+ (Canada only)
  // Custom orders: Always charged shipping
  const calculateShipping = () => {
    // Check if order contains custom designs (no design_id means custom/blank)
    const hasCustomOrder = items.some(item => !item.design_id || item.design_name?.toLowerCase().includes('custom'));
    const hasInHouseDesign = items.some(item => item.design_id && !item.design_name?.toLowerCase().includes('custom'));
    
    // Count items by type for weight estimation
    let hasHeavyItem = items.some(item => 
      item.name?.toLowerCase().includes('hoodie') || 
      item.name?.toLowerCase().includes('sweatshirt')
    );
    let hasMug = items.some(item => 
      item.name?.toLowerCase().includes('mug')
    );
    
    const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);
    
    // Calculate base shipping rate
    const getBaseRate = () => {
      if (shippingInfo.country === 'CA') {
        if (hasHeavyItem || hasMug) return 9.99;
        if (itemCount >= 3) return 11.99;
        return 6.99;
      } else {
        // USA shipping
        if (hasHeavyItem || hasMug) return 14.99;
        if (itemCount >= 3) return 16.99;
        return 9.99;
      }
    };
    
    const baseRate = getBaseRate();
    
    // Custom orders: Always charge shipping (no free shipping)
    if (hasCustomOrder && !hasInHouseDesign) {
      return baseRate;
    }
    
    // Mixed order (custom + in-house): Always charge shipping
    if (hasCustomOrder && hasInHouseDesign) {
      return baseRate;
    }
    
    // In-house designs only: Free shipping over $75 (Canada only)
    if (shippingInfo.country === 'CA' && totalPrice >= 75) {
      return 0;
    }
    
    return baseRate;
  };

  // Check if order qualifies for free shipping message
  const isCustomOrder = items.some(item => !item.design_id || item.design_name?.toLowerCase().includes('custom'));
  const canGetFreeShipping = !isCustomOrder && shippingInfo.country === 'CA';

  // Check if all required confirmations are checked
  const allConfirmationsChecked = isCustomOrder
    ? (confirmations.printReady && confirmations.noDesignService && confirmations.spellingResponsibility && confirmations.turnaround && confirmations.shippingFees)
    : (confirmations.designedProducts && confirmations.designedShipping);

  const shipping = calculateShipping();
  const taxRate = shippingInfo.country === 'CA' ? 0.13 : 0.08; // 13% HST for Canada, 8% for USA
  const tax = totalPrice * taxRate;
  const finalTotal = totalPrice + shipping + tax;

  const handleInputChange = (e) => {
    setShippingInfo({ ...shippingInfo, [e.target.name]: e.target.value });
  };

  const handleCheckout = async (e) => {
    e.preventDefault();
    
    // Validate required fields for guest checkout
    if (isGuestCheckout && !shippingInfo.email) {
      toast.error('Please enter your email address');
      return;
    }

    setLoading(true);

    try {
      // For guest checkout, create a guest order
      const orderData = {
        items: items.map(item => ({
          product_id: item.product_id,
          quantity: item.quantity,
          color: item.color,
          size: item.size,
          design_id: item.design_id || '',
          design_name: item.design_name || ''
        })),
        shipping_address: {
          firstName: shippingInfo.firstName,
          lastName: shippingInfo.lastName,
          email: shippingInfo.email,
          address: shippingInfo.address,
          city: shippingInfo.city,
          state: shippingInfo.state,
          zip: shippingInfo.zip,
          phone: shippingInfo.phone
        },
        total_amount: finalTotal,
        is_guest: isGuestCheckout,
        subscribe_to_updates: subscribeToUpdates
      };

      let orderResponse;
      
      if (isGuestCheckout) {
        // Guest order endpoint (no auth required)
        orderResponse = await axios.post(`${API_URL}/api/orders/guest`, orderData);
      } else {
        // Authenticated order
        orderResponse = await axios.post(`${API_URL}/api/orders`, orderData, { withCredentials: true });
      }

      const newOrderId = orderResponse.data.order_id;

      // Process payment (demo mode)
      await axios.post(`${API_URL}/api/payments/create`, {
        source_id: 'demo_payment_token',
        order_id: newOrderId,
        amount: Math.round(finalTotal * 100)
      });

      setOrderId(newOrderId);
      setOrderComplete(true);
      clearCart();
      toast.success('Order placed successfully!');
    } catch (error) {
      console.error('Checkout error:', error);
      toast.error(error.response?.data?.detail || 'Checkout failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (orderComplete) {
    return (
      <div className="min-h-screen bg-background py-12" data-testid="order-complete">
        <div className="max-w-lg mx-auto px-4 text-center">
          <div className="bg-white border-2 border-black rounded-xl shadow-brutal-lg p-8">
            <CheckCircle className="h-16 w-16 text-accent mx-auto mb-4" />
            <h1 className="font-heading text-3xl font-bold mb-2">Order Confirmed!</h1>
            <p className="text-muted-foreground mb-4">
              Thank you for your purchase. Your order has been placed successfully.
              {isGuestCheckout && " A confirmation email has been sent to your email address."}
            </p>
            <p className="font-medium mb-6">
              Order ID: <span className="text-primary">{orderId}</span>
            </p>
            
            {subscribeToUpdates && (
              <div className="bg-accent/10 border border-accent/20 rounded-lg p-4 mb-6">
                <Mail className="h-6 w-6 text-accent mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">
                  You&apos;re subscribed! We&apos;ll send you updates on new products and exclusive promotions.
                </p>
              </div>
            )}
            
            <div className="space-y-3">
              {!isGuestCheckout && (
                <Button
                  onClick={() => navigate('/orders')}
                  className="w-full bg-primary text-white border-2 border-black shadow-brutal hover-lift"
                >
                  View My Orders
                </Button>
              )}
              <Button
                onClick={() => navigate('/shop')}
                variant="outline"
                className="w-full border-2 border-black"
              >
                Continue Shopping
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="min-h-screen bg-background py-12">
        <div className="max-w-lg mx-auto px-4 text-center">
          <h1 className="font-heading text-3xl font-bold mb-4">Your cart is empty</h1>
          <Button onClick={() => navigate('/shop')} className="bg-primary text-white border-2 border-black shadow-brutal hover-lift">
            Start Shopping
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-8" data-testid="checkout-page">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="font-heading text-4xl font-bold mb-2">Checkout</h1>
        {isGuestCheckout && (
          <p className="text-muted-foreground mb-8">
            Checking out as guest. <button onClick={() => navigate('/login')} className="text-primary underline">Sign in</button> to save your order history.
          </p>
        )}

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Checkout Form */}
          <div className="lg:col-span-2">
            <form onSubmit={handleCheckout} className="space-y-8">
              {/* Shipping Info */}
              <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
                <div className="flex items-center gap-2 mb-6">
                  <Truck className="h-5 w-5 text-primary" />
                  <h2 className="font-heading text-xl font-bold">Shipping Information</h2>
                </div>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">First Name</Label>
                    <Input
                      id="firstName"
                      name="firstName"
                      value={shippingInfo.firstName}
                      onChange={handleInputChange}
                      className="border-2 border-black h-12"
                      required
                      data-testid="shipping-first-name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">Last Name</Label>
                    <Input
                      id="lastName"
                      name="lastName"
                      value={shippingInfo.lastName}
                      onChange={handleInputChange}
                      className="border-2 border-black h-12"
                      required
                      data-testid="shipping-last-name"
                    />
                  </div>
                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      name="email"
                      type="email"
                      value={shippingInfo.email}
                      onChange={handleInputChange}
                      className="border-2 border-black h-12"
                      required
                      data-testid="shipping-email"
                    />
                    <p className="text-xs text-muted-foreground">Order confirmation will be sent to this email</p>
                  </div>
                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="address">Address</Label>
                    <Input
                      id="address"
                      name="address"
                      value={shippingInfo.address}
                      onChange={handleInputChange}
                      className="border-2 border-black h-12"
                      required
                      data-testid="shipping-address"
                    />
                  </div>
                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="country">Country</Label>
                    <select
                      id="country"
                      name="country"
                      value={shippingInfo.country}
                      onChange={handleInputChange}
                      className="w-full border-2 border-black h-12 rounded-md px-3 bg-white"
                      required
                      data-testid="shipping-country"
                    >
                      <option value="CA">Canada 🇨🇦</option>
                      <option value="US">United States 🇺🇸</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="city">City</Label>
                    <Input
                      id="city"
                      name="city"
                      value={shippingInfo.city}
                      onChange={handleInputChange}
                      className="border-2 border-black h-12"
                      required
                      data-testid="shipping-city"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="state">{shippingInfo.country === 'CA' ? 'Province' : 'State'}</Label>
                    <Input
                      id="state"
                      name="state"
                      value={shippingInfo.state}
                      onChange={handleInputChange}
                      className="border-2 border-black h-12"
                      placeholder={shippingInfo.country === 'CA' ? 'ON, BC, AB...' : 'CA, NY, TX...'}
                      required
                      data-testid="shipping-state"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="zip">{shippingInfo.country === 'CA' ? 'Postal Code' : 'ZIP Code'}</Label>
                    <Input
                      id="zip"
                      name="zip"
                      value={shippingInfo.zip}
                      onChange={handleInputChange}
                      className="border-2 border-black h-12"
                      placeholder={shippingInfo.country === 'CA' ? 'A1A 1A1' : '12345'}
                      required
                      data-testid="shipping-zip"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone</Label>
                    <Input
                      id="phone"
                      name="phone"
                      value={shippingInfo.phone}
                      onChange={handleInputChange}
                      className="border-2 border-black h-12"
                      required
                      data-testid="shipping-phone"
                    />
                  </div>
                </div>
              </div>

              {/* Newsletter Signup for Guest/All Customers */}
              <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Mail className="h-5 w-5 text-primary" />
                  <h2 className="font-heading text-xl font-bold">Stay Updated</h2>
                </div>
                <div className="flex items-start space-x-3">
                  <Checkbox
                    id="subscribe"
                    checked={subscribeToUpdates}
                    onCheckedChange={(checked) => setSubscribeToUpdates(checked)}
                    className="mt-1"
                    data-testid="subscribe-checkbox"
                  />
                  <label htmlFor="subscribe" className="text-sm text-muted-foreground leading-relaxed cursor-pointer">
                    Yes! Sign me up for email updates on new products, exclusive designs, and special promotions from Revolution Printing.
                  </label>
                </div>
              </div>

              {/* Order Confirmation - Custom Orders */}
              {isCustomOrder && (
                <div className="bg-yellow-50 border-2 border-yellow-400 rounded-xl shadow-brutal p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <AlertTriangle className="h-5 w-5 text-yellow-600" />
                    <h2 className="font-heading text-xl font-bold text-yellow-800">Custom Order Confirmation</h2>
                  </div>
                  <p className="text-sm text-yellow-700 mb-4">
                    Please review and confirm before placing your custom order:
                  </p>
                  <div className="space-y-3">
                    <div className="flex items-start space-x-3">
                      <Checkbox
                        id="printReady"
                        checked={confirmations.printReady}
                        onCheckedChange={(checked) => setConfirmations({...confirmations, printReady: checked})}
                        className="mt-1"
                      />
                      <label htmlFor="printReady" className="text-sm text-yellow-800 cursor-pointer">
                        I understand that custom orders require print-ready, high-resolution artwork suitable for apparel or drinkware printing.
                      </label>
                    </div>
                    <div className="flex items-start space-x-3">
                      <Checkbox
                        id="noDesignService"
                        checked={confirmations.noDesignService}
                        onCheckedChange={(checked) => setConfirmations({...confirmations, noDesignService: checked})}
                        className="mt-1"
                      />
                      <label htmlFor="noDesignService" className="text-sm text-yellow-800 cursor-pointer">
                        I understand that Revolution Printing does not provide custom design services and will print my artwork exactly as submitted.
                      </label>
                    </div>
                    <div className="flex items-start space-x-3">
                      <Checkbox
                        id="spellingResponsibility"
                        checked={confirmations.spellingResponsibility}
                        onCheckedChange={(checked) => setConfirmations({...confirmations, spellingResponsibility: checked})}
                        className="mt-1"
                      />
                      <label htmlFor="spellingResponsibility" className="text-sm text-yellow-800 cursor-pointer">
                        I understand that spelling, layout, and design accuracy are my responsibility, and errors will not be corrected.
                      </label>
                    </div>
                    <div className="flex items-start space-x-3">
                      <Checkbox
                        id="turnaround"
                        checked={confirmations.turnaround}
                        onCheckedChange={(checked) => setConfirmations({...confirmations, turnaround: checked})}
                        className="mt-1"
                      />
                      <label htmlFor="turnaround" className="text-sm text-yellow-800 cursor-pointer">
                        I understand that custom order turnaround time is 3–10 business days, depending on printing method.
                      </label>
                    </div>
                    <div className="flex items-start space-x-3">
                      <Checkbox
                        id="shippingFees"
                        checked={confirmations.shippingFees}
                        onCheckedChange={(checked) => setConfirmations({...confirmations, shippingFees: checked})}
                        className="mt-1"
                      />
                      <label htmlFor="shippingFees" className="text-sm text-yellow-800 cursor-pointer">
                        I understand that shipping fees always apply to custom orders, regardless of order total.
                      </label>
                    </div>
                  </div>
                  <p className="text-xs text-yellow-700 mt-4 pt-4 border-t border-yellow-300">
                    <Link to="/printing-info" className="underline font-medium">View full printing & ordering information →</Link>
                  </p>
                </div>
              )}

              {/* Order Confirmation - Designed Products */}
              {!isCustomOrder && (
                <div className="bg-green-50 border-2 border-green-400 rounded-xl shadow-brutal p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    <h2 className="font-heading text-xl font-bold text-green-800">Order Confirmation</h2>
                  </div>
                  <div className="space-y-3">
                    <div className="flex items-start space-x-3">
                      <Checkbox
                        id="designedProducts"
                        checked={confirmations.designedProducts}
                        onCheckedChange={(checked) => setConfirmations({...confirmations, designedProducts: checked})}
                        className="mt-1"
                      />
                      <label htmlFor="designedProducts" className="text-sm text-green-800 cursor-pointer">
                        I understand that designed products are not customizable and are sold as shown.
                      </label>
                    </div>
                    <div className="flex items-start space-x-3">
                      <Checkbox
                        id="designedShipping"
                        checked={confirmations.designedShipping}
                        onCheckedChange={(checked) => setConfirmations({...confirmations, designedShipping: checked})}
                        className="mt-1"
                      />
                      <label htmlFor="designedShipping" className="text-sm text-green-800 cursor-pointer">
                        I understand that designed products ship within 24 hours and qualify for free shipping on orders $75+ (Canada).
                      </label>
                    </div>
                  </div>
                </div>
              )}

              {/* Payment Info */}
              <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
                <div className="flex items-center gap-2 mb-6">
                  <CreditCard className="h-5 w-5 text-primary" />
                  <h2 className="font-heading text-xl font-bold">Payment</h2>
                </div>
                <div className="bg-accent/10 border border-accent/20 rounded-lg p-4 text-center">
                  <ShieldCheck className="h-8 w-8 text-accent mx-auto mb-2" />
                  <p className="font-medium text-accent">Demo Mode</p>
                  <p className="text-sm text-muted-foreground">
                    Payment is processed in demo mode. No real charges will be made.
                  </p>
                </div>
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-primary text-white border-2 border-black shadow-brutal hover-lift h-14 text-lg"
                data-testid="place-order-button"
              >
                {loading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  `Place Order • $${finalTotal.toFixed(2)}`
                )}
              </Button>
            </form>
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6 sticky top-24">
              <h2 className="font-heading text-xl font-bold mb-4">Order Summary</h2>
              
              <div className="space-y-4 mb-6">
                {items.map((item) => (
                  <div key={`${item.product_id}-${item.color}-${item.size}-${item.design_id || ''}`} className="flex gap-3">
                    <div className="w-16 h-16 rounded-lg border-2 border-black overflow-hidden bg-muted flex-shrink-0">
                      <img src={item.image || 'https://via.placeholder.com/64'} alt={item.name} className="w-full h-full object-cover" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm line-clamp-1">{item.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {item.color && item.color}{item.color && item.size && ' / '}{item.size && item.size}
                      </p>
                      {item.design_name && (
                        <p className="text-xs text-primary">Design: {item.design_name}</p>
                      )}
                      <p className="text-sm">Qty: {item.quantity}</p>
                    </div>
                    <p className="font-medium">${(item.price * item.quantity).toFixed(2)}</p>
                  </div>
                ))}
              </div>

              <Separator className="my-4" />

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Subtotal</span>
                  <span>${totalPrice.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">
                    Shipping ({shippingInfo.country === 'CA' ? '🇨🇦 Canada' : '🇺🇸 USA'})
                  </span>
                  <span>{shipping === 0 ? 'Free' : `$${shipping.toFixed(2)}`}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">
                    Tax ({shippingInfo.country === 'CA' ? 'HST 13%' : 'Sales Tax 8%'})
                  </span>
                  <span>${tax.toFixed(2)}</span>
                </div>
              </div>

              <Separator className="my-4" />

              <div className="flex justify-between font-bold text-lg">
                <span>Total ({shippingInfo.country === 'CA' ? 'CAD' : 'USD'})</span>
                <span className="text-primary">${finalTotal.toFixed(2)}</span>
              </div>

              {shipping > 0 && canGetFreeShipping && totalPrice < 75 && (
                <p className="text-xs text-muted-foreground mt-4 text-center">
                  Add ${(75 - totalPrice).toFixed(2)} more for free shipping in Canada!
                </p>
              )}
              
              {isCustomOrder && (
                <p className="text-xs text-muted-foreground mt-4 text-center">
                  Custom orders include a shipping fee.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CheckoutPage;

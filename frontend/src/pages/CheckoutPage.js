import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CreditCard, Truck, ShieldCheck, Loader2, CheckCircle } from 'lucide-react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Separator } from '../components/ui/separator';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const CheckoutPage = () => {
  const navigate = useNavigate();
  const { items, totalPrice, clearCart } = useCart();
  const { user, isAuthenticated } = useAuth();
  
  const [loading, setLoading] = useState(false);
  const [orderComplete, setOrderComplete] = useState(false);
  const [orderId, setOrderId] = useState('');
  
  const [shippingInfo, setShippingInfo] = useState({
    firstName: user?.name?.split(' ')[0] || '',
    lastName: user?.name?.split(' ').slice(1).join(' ') || '',
    email: user?.email || '',
    address: '',
    city: '',
    state: '',
    zip: '',
    phone: ''
  });

  const shipping = totalPrice >= 50 ? 0 : 5.99;
  const tax = totalPrice * 0.08;
  const finalTotal = totalPrice + shipping + tax;

  const handleInputChange = (e) => {
    setShippingInfo({ ...shippingInfo, [e.target.name]: e.target.value });
  };

  const handleCheckout = async (e) => {
    e.preventDefault();
    
    if (!isAuthenticated) {
      navigate('/login', { state: { from: { pathname: '/checkout' } } });
      return;
    }

    setLoading(true);

    try {
      // Create order
      const orderResponse = await axios.post(`${API_URL}/api/orders`, {
        items: items.map(item => ({
          product_id: item.product_id,
          quantity: item.quantity,
          color: item.color,
          size: item.size
        })),
        shipping_address: {
          firstName: shippingInfo.firstName,
          lastName: shippingInfo.lastName,
          address: shippingInfo.address,
          city: shippingInfo.city,
          state: shippingInfo.state,
          zip: shippingInfo.zip,
          phone: shippingInfo.phone
        },
        total_amount: finalTotal
      }, { withCredentials: true });

      const newOrderId = orderResponse.data.order_id;

      // Process payment (demo mode)
      await axios.post(`${API_URL}/api/payments/create`, {
        source_id: 'demo_payment_token',
        order_id: newOrderId,
        amount: Math.round(finalTotal * 100) // cents
      }, { withCredentials: true });

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
            </p>
            <p className="font-medium mb-6">
              Order ID: <span className="text-primary">{orderId}</span>
            </p>
            <div className="space-y-3">
              <Button
                onClick={() => navigate('/orders')}
                className="w-full bg-primary text-white border-2 border-black shadow-brutal hover-lift"
              >
                View My Orders
              </Button>
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
        <h1 className="font-heading text-4xl font-bold mb-8">Checkout</h1>

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
                    <Label htmlFor="state">State</Label>
                    <Input
                      id="state"
                      name="state"
                      value={shippingInfo.state}
                      onChange={handleInputChange}
                      className="border-2 border-black h-12"
                      required
                      data-testid="shipping-state"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="zip">ZIP Code</Label>
                    <Input
                      id="zip"
                      name="zip"
                      value={shippingInfo.zip}
                      onChange={handleInputChange}
                      className="border-2 border-black h-12"
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
                disabled={loading || !isAuthenticated}
                className="w-full bg-primary text-white border-2 border-black shadow-brutal hover-lift h-14 text-lg"
                data-testid="place-order-button"
              >
                {loading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : !isAuthenticated ? (
                  'Sign in to checkout'
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
                  <div key={`${item.product_id}-${item.color}-${item.size}`} className="flex gap-3">
                    <div className="w-16 h-16 rounded-lg border-2 border-black overflow-hidden bg-muted flex-shrink-0">
                      <img src={item.image || 'https://via.placeholder.com/64'} alt={item.name} className="w-full h-full object-cover" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm line-clamp-1">{item.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {item.color && item.color}{item.color && item.size && ' / '}{item.size && item.size}
                      </p>
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
                  <span className="text-muted-foreground">Shipping</span>
                  <span>{shipping === 0 ? 'Free' : `$${shipping.toFixed(2)}`}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Tax</span>
                  <span>${tax.toFixed(2)}</span>
                </div>
              </div>

              <Separator className="my-4" />

              <div className="flex justify-between font-bold text-lg">
                <span>Total</span>
                <span className="text-primary">${finalTotal.toFixed(2)}</span>
              </div>

              {totalPrice < 50 && (
                <p className="text-xs text-muted-foreground mt-4 text-center">
                  Add ${(50 - totalPrice).toFixed(2)} more for free shipping!
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

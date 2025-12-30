import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Package, ChevronRight, ShoppingBag } from 'lucide-react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { useAuth } from '../context/AuthContext';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const OrdersPage = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: { pathname: '/orders' } } });
      return;
    }

    const fetchOrders = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/orders`, { withCredentials: true });
        setOrders(response.data);
      } catch (error) {
        console.error('Error fetching orders:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchOrders();
  }, [isAuthenticated, navigate]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'paid': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'shipped': return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'delivered': return 'bg-green-100 text-green-800 border-green-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background py-12">
        <div className="max-w-4xl mx-auto px-4">
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
                <div className="h-6 bg-muted animate-pulse rounded w-1/4 mb-4" />
                <div className="h-4 bg-muted animate-pulse rounded w-1/2" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-12" data-testid="orders-page">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="font-heading text-4xl font-bold mb-8">My Orders</h1>

        {orders.length === 0 ? (
          <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-12 text-center">
            <ShoppingBag className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <h2 className="font-heading text-2xl font-bold mb-2">No orders yet</h2>
            <p className="text-muted-foreground mb-6">Start shopping to see your orders here!</p>
            <Button
              onClick={() => navigate('/shop')}
              className="bg-primary text-white border-2 border-black shadow-brutal hover-lift"
            >
              Browse Products
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {orders.map((order) => (
              <div
                key={order.order_id}
                className="bg-white border-2 border-black rounded-xl shadow-brutal p-6"
                data-testid={`order-${order.order_id}`}
              >
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Order ID</p>
                    <p className="font-mono font-medium">{order.order_id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Date</p>
                    <p className="font-medium">
                      {new Date(order.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total</p>
                    <p className="font-bold text-primary">${order.total_amount.toFixed(2)}</p>
                  </div>
                  <Badge className={`${getStatusColor(order.status)} border capitalize`}>
                    {order.status}
                  </Badge>
                </div>

                <div className="flex items-center gap-4 overflow-x-auto pb-2">
                  {order.items.map((item, index) => (
                    <div key={index} className="flex-shrink-0">
                      <div className="w-16 h-16 rounded-lg border-2 border-black overflow-hidden bg-muted">
                        <img
                          src={item.image || 'https://via.placeholder.com/64'}
                          alt={item.product_name}
                          className="w-full h-full object-cover"
                        />
                      </div>
                    </div>
                  ))}
                  <div className="flex items-center text-muted-foreground">
                    <span className="text-sm">{order.items.length} item(s)</span>
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default OrdersPage;

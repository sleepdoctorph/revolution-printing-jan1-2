import React, { useEffect, useState } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import { Package, ShoppingCart, Users, DollarSign, TrendingUp, Clock, ArrowRight } from 'lucide-react';
import axios from 'axios';
import { Button } from '../../components/ui/button';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const AdminDashboard = () => {
  const { stats } = useOutletContext() || {};
  const [recentOrders, setRecentOrders] = useState([]);

  useEffect(() => {
    const fetchRecentOrders = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/admin/orders`, { withCredentials: true });
        setRecentOrders(response.data.slice(0, 5));
      } catch (error) {
        console.error('Error fetching orders:', error);
      }
    };
    fetchRecentOrders();
  }, []);

  const statCards = [
    { name: 'Total Products', value: stats?.total_products || 0, icon: Package, color: 'text-primary' },
    { name: 'Total Orders', value: stats?.total_orders || 0, icon: ShoppingCart, color: 'text-secondary' },
    { name: 'Total Customers', value: stats?.total_customers || 0, icon: Users, color: 'text-accent' },
    { name: 'Revenue', value: `$${stats?.total_revenue?.toFixed(2) || '0.00'}`, icon: DollarSign, color: 'text-chart-4' },
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'paid': return 'bg-blue-100 text-blue-800';
      case 'shipped': return 'bg-purple-100 text-purple-800';
      case 'delivered': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div data-testid="admin-dashboard">
      <div className="mb-8">
        <h1 className="font-heading text-3xl font-bold mb-2">Dashboard</h1>
        <p className="text-muted-foreground">Welcome back! Here's what's happening with your store.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((stat) => (
          <div key={stat.name} className="bg-white border-2 border-black rounded-xl p-6 shadow-brutal">
            <div className="flex items-center justify-between mb-4">
              <stat.icon className={`h-8 w-8 ${stat.color}`} />
              <TrendingUp className="h-4 w-4 text-accent" />
            </div>
            <p className="text-2xl font-bold mb-1">{stat.value}</p>
            <p className="text-sm text-muted-foreground">{stat.name}</p>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Recent Orders */}
        <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-heading text-xl font-bold">Recent Orders</h2>
            <Button asChild variant="ghost" size="sm">
              <Link to="/admin/orders">
                View All
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
          
          {recentOrders.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No orders yet</p>
          ) : (
            <div className="space-y-4">
              {recentOrders.map((order) => (
                <div key={order.order_id} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                  <div>
                    <p className="font-medium text-sm">{order.order_id}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(order.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold">${order.total_amount.toFixed(2)}</p>
                    <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(order.status)}`}>
                      {order.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
          <h2 className="font-heading text-xl font-bold mb-6">Quick Actions</h2>
          <div className="grid grid-cols-2 gap-4">
            <Button asChild className="h-24 flex-col bg-primary text-white border-2 border-black shadow-brutal hover-lift">
              <Link to="/admin/products/new">
                <Package className="h-6 w-6 mb-2" />
                Add Product
              </Link>
            </Button>
            <Button asChild variant="outline" className="h-24 flex-col border-2 border-black shadow-brutal hover-lift">
              <Link to="/admin/orders">
                <ShoppingCart className="h-6 w-6 mb-2" />
                View Orders
              </Link>
            </Button>
            <Button asChild variant="outline" className="h-24 flex-col border-2 border-black shadow-brutal hover-lift">
              <Link to="/admin/customers">
                <Users className="h-6 w-6 mb-2" />
                Customers
              </Link>
            </Button>
            <Button asChild variant="outline" className="h-24 flex-col border-2 border-black shadow-brutal hover-lift">
              <Link to="/admin/contacts">
                <Clock className="h-6 w-6 mb-2" />
                Messages
              </Link>
            </Button>
          </div>
        </div>

        {/* Pending Orders Alert */}
        {stats?.pending_orders > 0 && (
          <div className="lg:col-span-2 bg-yellow-50 border-2 border-yellow-400 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Clock className="h-8 w-8 text-yellow-600" />
                <div>
                  <p className="font-heading font-bold text-lg">Pending Orders</p>
                  <p className="text-muted-foreground">
                    You have {stats.pending_orders} order(s) waiting to be processed
                  </p>
                </div>
              </div>
              <Button asChild className="bg-yellow-600 text-white border-2 border-black shadow-brutal hover-lift">
                <Link to="/admin/orders">Review Orders</Link>
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;

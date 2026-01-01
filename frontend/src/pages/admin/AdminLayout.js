import React, { useEffect, useState } from 'react';
import { Link, useNavigate, Outlet, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, Package, ShoppingCart, Users, Inbox, Palette,
  ChevronRight, Menu, X 
} from 'lucide-react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/AuthContext';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const AdminLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAdmin, loading } = useAuth();
  const [stats, setStats] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (!loading && !isAdmin) {
      navigate('/');
    }
  }, [isAdmin, loading, navigate]);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/admin/stats`, { withCredentials: true });
        setStats(response.data);
      } catch (error) {
        console.error('Error fetching stats:', error);
      }
    };
    if (isAdmin) {
      fetchStats();
    }
  }, [isAdmin]);

  const navItems = [
    { name: 'Dashboard', href: '/admin', icon: LayoutDashboard },
    { name: 'Products', href: '/admin/products', icon: Package },
    { name: 'Designs', href: '/admin/designs', icon: Palette },
    { name: 'Orders', href: '/admin/orders', icon: ShoppingCart },
    { name: 'Customers', href: '/admin/customers', icon: Users },
    { name: 'Messages', href: '/admin/contacts', icon: Inbox },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!isAdmin) return null;

  return (
    <div className="min-h-screen bg-muted" data-testid="admin-layout">
      {/* Mobile Header */}
      <div className="lg:hidden bg-foreground text-background p-4 flex items-center justify-between">
        <h1 className="font-heading text-xl font-bold text-primary">Admin Panel</h1>
        <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!sidebarOpen)}>
          {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </Button>
      </div>

      <div className="flex">
        {/* Sidebar */}
        <aside className={`
          fixed lg:sticky top-0 left-0 z-40 h-screen w-64 bg-foreground text-background
          transform transition-transform duration-300 lg:translate-x-0
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        `}>
          <div className="p-6 border-b border-muted-foreground/20">
            <Link to="/">
              <img 
                src="https://customer-assets.emergentagent.com/job_faithapparel/artifacts/odi1used_logo%201.png" 
                alt="Revolution Printing" 
                className="h-10 object-contain"
              />
            </Link>
            <p className="text-sm text-muted-foreground mt-1">Admin Panel</p>
          </div>

          <nav className="p-4 space-y-2">
            {navItems.map((item) => {
              const isActive = location.pathname === item.href || 
                (item.href !== '/admin' && location.pathname.startsWith(item.href));
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`
                    flex items-center gap-3 px-4 py-3 rounded-lg transition-colors
                    ${isActive 
                      ? 'bg-primary text-white' 
                      : 'hover:bg-muted-foreground/10'
                    }
                  `}
                  data-testid={`admin-nav-${item.name.toLowerCase()}`}
                >
                  <item.icon className="h-5 w-5" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Quick Stats */}
          {stats && (
            <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-muted-foreground/20">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="bg-muted-foreground/10 rounded-lg p-2 text-center">
                  <p className="font-bold text-primary">{stats.total_orders}</p>
                  <p className="text-xs text-muted-foreground">Orders</p>
                </div>
                <div className="bg-muted-foreground/10 rounded-lg p-2 text-center">
                  <p className="font-bold text-primary">${stats.total_revenue?.toFixed(0) || 0}</p>
                  <p className="text-xs text-muted-foreground">Revenue</p>
                </div>
              </div>
            </div>
          )}
        </aside>

        {/* Overlay for mobile */}
        {sidebarOpen && (
          <div 
            className="fixed inset-0 bg-black/50 z-30 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main Content */}
        <main className="flex-1 p-6 lg:p-8 min-h-screen">
          <Outlet context={{ stats }} />
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;

import React, { useEffect, useState } from 'react';
import { Search, Mail, Calendar, DollarSign, ShoppingBag, Download, Users, UserCheck, Eye, X, Package } from 'lucide-react';
import axios from 'axios';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const AdminCustomers = () => {
  const [customers, setCustomers] = useState([]);
  const [subscribers, setSubscribers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all'); // all, registered, guest, newsletter
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [customersRes, subscribersRes] = await Promise.all([
          axios.get(`${API_URL}/api/admin/customers`, { withCredentials: true }),
          axios.get(`${API_URL}/api/admin/newsletter-subscribers`, { withCredentials: true })
        ]);
        setCustomers(customersRes.data);
        setSubscribers(subscribersRes.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleExport = async () => {
    setExporting(true);
    try {
      const response = await axios.get(`${API_URL}/api/admin/crm/export`, { withCredentials: true });
      const data = response.data;
      
      // Convert to CSV
      const headers = ['Name', 'Email', 'Phone', 'Total Orders', 'Total Spent', 'Joined Date', 'Last Order', 'Source'];
      const csvContent = [
        headers.join(','),
        ...data.map(row => [
          `"${row.name || ''}"`,
          `"${row.email || ''}"`,
          `"${row.phone || ''}"`,
          row.total_orders,
          row.total_spent,
          `"${row.joined_date || ''}"`,
          `"${row.last_order_date || ''}"`,
          `"${row.source || ''}"`
        ].join(','))
      ].join('\n');
      
      // Download file
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `revolution-printing-customers-${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      
      toast.success(`Exported ${data.length} contacts!`);
    } catch (error) {
      console.error('Error exporting:', error);
      toast.error('Failed to export data');
    } finally {
      setExporting(false);
    }
  };

  const filteredCustomers = customers.filter(c => {
    const matchesSearch = 
      c.name?.toLowerCase().includes(search.toLowerCase()) ||
      c.email?.toLowerCase().includes(search.toLowerCase());
    
    if (!matchesSearch) return false;
    
    if (filter === 'registered') return !c.is_guest;
    if (filter === 'guest') return c.is_guest;
    return true;
  });

  const stats = {
    total: customers.length,
    registered: customers.filter(c => !c.is_guest).length,
    guests: customers.filter(c => c.is_guest).length,
    subscribers: subscribers.length,
    totalRevenue: customers.reduce((sum, c) => sum + (c.total_spent || 0), 0)
  };

  return (
    <div data-testid="admin-customers">
      <div className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="font-heading text-3xl font-bold mb-2">Customer CRM</h1>
          <p className="text-muted-foreground">Manage customers, view order history, and export data</p>
        </div>
        <Button 
          onClick={handleExport} 
          disabled={exporting}
          className="bg-accent text-white border-2 border-black shadow-brutal"
        >
          <Download className="h-4 w-4 mr-2" />
          {exporting ? 'Exporting...' : 'Export CSV'}
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <div className="bg-white border-2 border-black rounded-xl p-4 shadow-brutal">
          <Users className="h-6 w-6 text-primary mb-2" />
          <p className="text-2xl font-bold">{stats.total}</p>
          <p className="text-xs text-muted-foreground">Total Customers</p>
        </div>
        <div className="bg-white border-2 border-black rounded-xl p-4 shadow-brutal">
          <UserCheck className="h-6 w-6 text-accent mb-2" />
          <p className="text-2xl font-bold">{stats.registered}</p>
          <p className="text-xs text-muted-foreground">Registered</p>
        </div>
        <div className="bg-white border-2 border-black rounded-xl p-4 shadow-brutal">
          <ShoppingBag className="h-6 w-6 text-secondary mb-2" />
          <p className="text-2xl font-bold">{stats.guests}</p>
          <p className="text-xs text-muted-foreground">Guest Checkouts</p>
        </div>
        <div className="bg-white border-2 border-black rounded-xl p-4 shadow-brutal">
          <Mail className="h-6 w-6 text-chart-4 mb-2" />
          <p className="text-2xl font-bold">{stats.subscribers}</p>
          <p className="text-xs text-muted-foreground">Newsletter Subs</p>
        </div>
        <div className="bg-white border-2 border-black rounded-xl p-4 shadow-brutal">
          <DollarSign className="h-6 w-6 text-green-600 mb-2" />
          <p className="text-2xl font-bold">${stats.totalRevenue.toFixed(2)}</p>
          <p className="text-xs text-muted-foreground">Total Revenue</p>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
          <Input
            placeholder="Search by name or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10 border-2 border-black"
          />
        </div>
        <div className="flex gap-2">
          {['all', 'registered', 'guest'].map((f) => (
            <Button
              key={f}
              variant={filter === f ? 'default' : 'outline'}
              onClick={() => setFilter(f)}
              className={`border-2 border-black ${filter === f ? 'bg-primary text-white' : ''}`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </Button>
          ))}
        </div>
      </div>

      {/* Customers Table */}
      {loading ? (
        <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-8">
          <div className="animate-pulse space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-muted rounded" />
            ))}
          </div>
        </div>
      ) : filteredCustomers.length === 0 ? (
        <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-8 text-center text-muted-foreground">
          No customers found
        </div>
      ) : (
        <div className="bg-white border-2 border-black rounded-xl shadow-brutal overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-muted">
                <tr>
                  <th className="text-left p-4 font-heading">Customer</th>
                  <th className="text-left p-4 font-heading hidden md:table-cell">Email</th>
                  <th className="text-center p-4 font-heading">Orders</th>
                  <th className="text-right p-4 font-heading">Total Spent</th>
                  <th className="text-center p-4 font-heading">Type</th>
                  <th className="text-center p-4 font-heading">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredCustomers.map((customer) => (
                  <tr key={customer.user_id || customer.email} className="border-t border-gray-200 hover:bg-muted/50">
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <Avatar className="h-10 w-10 border-2 border-black">
                          <AvatarImage src={customer.picture} />
                          <AvatarFallback className="bg-primary text-white font-bold">
                            {customer.name?.charAt(0) || 'U'}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium">{customer.name || 'Unknown'}</p>
                          <p className="text-xs text-muted-foreground md:hidden">{customer.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="p-4 hidden md:table-cell text-muted-foreground">{customer.email}</td>
                    <td className="p-4 text-center font-bold">{customer.total_orders || 0}</td>
                    <td className="p-4 text-right font-bold text-green-600">${(customer.total_spent || 0).toFixed(2)}</td>
                    <td className="p-4 text-center">
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        customer.is_guest 
                          ? 'bg-yellow-100 text-yellow-800' 
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {customer.is_guest ? 'Guest' : 'Registered'}
                      </span>
                    </td>
                    <td className="p-4 text-center">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setSelectedCustomer(customer)}
                        className="border-2 border-black"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Newsletter Subscribers Section */}
      {subscribers.length > 0 && (
        <div className="mt-8">
          <h2 className="font-heading text-xl font-bold mb-4">Newsletter Subscribers</h2>
          <div className="bg-white border-2 border-black rounded-xl shadow-brutal overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted">
                  <tr>
                    <th className="text-left p-4 font-heading">Name</th>
                    <th className="text-left p-4 font-heading">Email</th>
                    <th className="text-left p-4 font-heading">Source</th>
                    <th className="text-left p-4 font-heading">Subscribed</th>
                  </tr>
                </thead>
                <tbody>
                  {subscribers.map((sub, i) => (
                    <tr key={i} className="border-t border-gray-200 hover:bg-muted/50">
                      <td className="p-4 font-medium">{sub.name || '-'}</td>
                      <td className="p-4 text-muted-foreground">{sub.email}</td>
                      <td className="p-4">
                        <span className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-800">
                          {sub.source || 'website'}
                        </span>
                      </td>
                      <td className="p-4 text-muted-foreground">
                        {sub.subscribed_at ? new Date(sub.subscribed_at).toLocaleDateString() : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Customer Detail Modal */}
      {selectedCustomer && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white border-2 border-black rounded-xl shadow-brutal max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-heading text-2xl font-bold">Customer Details</h2>
                <Button variant="ghost" size="sm" onClick={() => setSelectedCustomer(null)}>
                  <X className="h-5 w-5" />
                </Button>
              </div>
              
              {/* Customer Info */}
              <div className="flex items-center gap-4 mb-6 p-4 bg-muted rounded-lg">
                <Avatar className="h-16 w-16 border-2 border-black">
                  <AvatarImage src={selectedCustomer.picture} />
                  <AvatarFallback className="bg-primary text-white font-bold text-xl">
                    {selectedCustomer.name?.charAt(0) || 'U'}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-heading text-xl font-bold">{selectedCustomer.name || 'Unknown'}</p>
                  <p className="text-muted-foreground">{selectedCustomer.email}</p>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    selectedCustomer.is_guest 
                      ? 'bg-yellow-100 text-yellow-800' 
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {selectedCustomer.is_guest ? 'Guest Customer' : 'Registered Customer'}
                  </span>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="text-center p-4 bg-muted rounded-lg">
                  <p className="text-2xl font-bold">{selectedCustomer.total_orders || 0}</p>
                  <p className="text-xs text-muted-foreground">Total Orders</p>
                </div>
                <div className="text-center p-4 bg-muted rounded-lg">
                  <p className="text-2xl font-bold text-green-600">${(selectedCustomer.total_spent || 0).toFixed(2)}</p>
                  <p className="text-xs text-muted-foreground">Total Spent</p>
                </div>
                <div className="text-center p-4 bg-muted rounded-lg">
                  <p className="text-2xl font-bold">{selectedCustomer.created_at ? new Date(selectedCustomer.created_at).toLocaleDateString() : '-'}</p>
                  <p className="text-xs text-muted-foreground">Customer Since</p>
                </div>
              </div>

              {/* Order History */}
              <h3 className="font-heading font-bold mb-4">Order History</h3>
              {selectedCustomer.orders?.length > 0 ? (
                <div className="space-y-3">
                  {selectedCustomer.orders.map((order) => (
                    <div key={order.order_id} className="p-4 border-2 border-gray-200 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-mono text-sm">{order.order_id}</span>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          order.status === 'delivered' ? 'bg-green-100 text-green-800' :
                          order.status === 'shipped' ? 'bg-blue-100 text-blue-800' :
                          order.status === 'paid' ? 'bg-purple-100 text-purple-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {order.status}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">
                          {order.created_at ? new Date(order.created_at).toLocaleDateString() : '-'}
                        </span>
                        <span className="font-bold">${(order.total_amount || 0).toFixed(2)}</span>
                      </div>
                      {order.items && (
                        <div className="mt-2 pt-2 border-t border-gray-100">
                          <p className="text-xs text-muted-foreground">
                            {order.items.map(i => i.product_name || i.name).join(', ')}
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-center py-4">No orders yet</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminCustomers;

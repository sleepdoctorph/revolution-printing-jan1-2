import React, { useEffect, useState } from 'react';
import { Search, Mail, Calendar } from 'lucide-react';
import axios from 'axios';
import { Input } from '../../components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '../../components/ui/avatar';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const AdminCustomers = () => {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    const fetchCustomers = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/admin/customers`, { withCredentials: true });
        setCustomers(response.data);
      } catch (error) {
        console.error('Error fetching customers:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchCustomers();
  }, []);

  const filteredCustomers = customers.filter(c =>
    c.name?.toLowerCase().includes(search.toLowerCase()) ||
    c.email?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div data-testid="admin-customers">
      <div className="mb-8">
        <h1 className="font-heading text-3xl font-bold mb-2">Customers</h1>
        <p className="text-muted-foreground">View and manage your customers</p>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
        <Input
          placeholder="Search customers..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10 border-2 border-black max-w-md"
        />
      </div>

      {/* Customers Grid */}
      {loading ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
              <div className="h-20 bg-muted animate-pulse rounded" />
            </div>
          ))}
        </div>
      ) : filteredCustomers.length === 0 ? (
        <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-8 text-center text-muted-foreground">
          No customers found
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCustomers.map((customer) => (
            <div
              key={customer.user_id}
              className="bg-white border-2 border-black rounded-xl shadow-brutal p-6"
            >
              <div className="flex items-center gap-4 mb-4">
                <Avatar className="h-12 w-12 border-2 border-black">
                  <AvatarImage src={customer.picture} />
                  <AvatarFallback className="bg-primary text-white font-bold">
                    {customer.name?.charAt(0) || 'U'}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-heading font-bold">{customer.name || 'Unknown'}</p>
                  <p className="text-sm text-muted-foreground">{customer.user_id}</p>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Mail className="h-4 w-4" />
                  {customer.email}
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  Joined {new Date(customer.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminCustomers;

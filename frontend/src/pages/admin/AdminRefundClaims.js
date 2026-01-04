import React, { useEffect, useState } from 'react';
import { Search, Send, Eye, X, Clock, CheckCircle, XCircle, AlertTriangle, Mail } from 'lucide-react';
import axios from 'axios';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const AdminRefundClaims = () => {
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [sendFormModal, setSendFormModal] = useState(false);
  const [sendFormData, setSendFormData] = useState({ email: '', order_id: '', customer_name: '' });
  const [sending, setSending] = useState(false);

  useEffect(() => {
    fetchClaims();
  }, []);

  const fetchClaims = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/admin/refund-claims`, { withCredentials: true });
      setClaims(response.data);
    } catch (error) {
      console.error('Error fetching claims:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateClaim = async (claimId, updates) => {
    try {
      await axios.put(`${API_URL}/api/admin/refund-claims/${claimId}`, updates, { withCredentials: true });
      toast.success('Claim updated successfully');
      fetchClaims();
      setSelectedClaim(null);
    } catch (error) {
      console.error('Error updating claim:', error);
      toast.error('Failed to update claim');
    }
  };

  const handleSendRefundForm = async () => {
    if (!sendFormData.email) {
      toast.error('Email is required');
      return;
    }
    
    setSending(true);
    try {
      await axios.post(`${API_URL}/api/admin/send-refund-form`, sendFormData, { withCredentials: true });
      toast.success(`Refund form sent to ${sendFormData.email}`);
      setSendFormModal(false);
      setSendFormData({ email: '', order_id: '', customer_name: '' });
    } catch (error) {
      console.error('Error sending form:', error);
      toast.error('Failed to send refund form');
    } finally {
      setSending(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'approved': return 'bg-green-100 text-green-800 border-green-300';
      case 'denied': return 'bg-red-100 text-red-800 border-red-300';
      case 'resolved': return 'bg-blue-100 text-blue-800 border-blue-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return <Clock className="h-4 w-4" />;
      case 'approved': return <CheckCircle className="h-4 w-4" />;
      case 'denied': return <XCircle className="h-4 w-4" />;
      case 'resolved': return <CheckCircle className="h-4 w-4" />;
      default: return <AlertTriangle className="h-4 w-4" />;
    }
  };

  const filteredClaims = claims.filter(claim => {
    const matchesSearch = 
      claim.claim_id?.toLowerCase().includes(search.toLowerCase()) ||
      claim.order_id?.toLowerCase().includes(search.toLowerCase()) ||
      claim.email?.toLowerCase().includes(search.toLowerCase()) ||
      claim.name?.toLowerCase().includes(search.toLowerCase());
    
    if (!matchesSearch) return false;
    if (statusFilter === 'all') return true;
    return claim.status === statusFilter;
  });

  return (
    <div data-testid="admin-refund-claims">
      <div className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="font-heading text-3xl font-bold mb-2">Refund Claims</h1>
          <p className="text-muted-foreground">Manage customer refund requests</p>
        </div>
        <Button 
          onClick={() => setSendFormModal(true)}
          className="bg-primary text-white border-2 border-black shadow-brutal"
        >
          <Mail className="h-4 w-4 mr-2" />
          Send Refund Form
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white border-2 border-black rounded-xl p-4 shadow-brutal">
          <p className="text-2xl font-bold">{claims.length}</p>
          <p className="text-xs text-muted-foreground">Total Claims</p>
        </div>
        <div className="bg-yellow-50 border-2 border-yellow-400 rounded-xl p-4">
          <p className="text-2xl font-bold text-yellow-800">{claims.filter(c => c.status === 'pending').length}</p>
          <p className="text-xs text-yellow-700">Pending</p>
        </div>
        <div className="bg-green-50 border-2 border-green-400 rounded-xl p-4">
          <p className="text-2xl font-bold text-green-800">{claims.filter(c => c.status === 'approved').length}</p>
          <p className="text-xs text-green-700">Approved</p>
        </div>
        <div className="bg-red-50 border-2 border-red-400 rounded-xl p-4">
          <p className="text-2xl font-bold text-red-800">{claims.filter(c => c.status === 'denied').length}</p>
          <p className="text-xs text-red-700">Denied</p>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
          <Input
            placeholder="Search by claim ID, order ID, email, or name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10 border-2 border-black"
          />
        </div>
        <div className="flex gap-2">
          {['all', 'pending', 'approved', 'denied', 'resolved'].map((status) => (
            <Button
              key={status}
              variant={statusFilter === status ? 'default' : 'outline'}
              onClick={() => setStatusFilter(status)}
              className={`border-2 border-black ${statusFilter === status ? 'bg-primary text-white' : ''}`}
              size="sm"
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </Button>
          ))}
        </div>
      </div>

      {/* Claims Table */}
      {loading ? (
        <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-8">
          <div className="animate-pulse space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-muted rounded" />
            ))}
          </div>
        </div>
      ) : filteredClaims.length === 0 ? (
        <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-8 text-center text-muted-foreground">
          No refund claims found
        </div>
      ) : (
        <div className="bg-white border-2 border-black rounded-xl shadow-brutal overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-muted">
                <tr>
                  <th className="text-left p-4 font-heading">Claim ID</th>
                  <th className="text-left p-4 font-heading">Order</th>
                  <th className="text-left p-4 font-heading hidden md:table-cell">Customer</th>
                  <th className="text-left p-4 font-heading">Issue</th>
                  <th className="text-center p-4 font-heading">Status</th>
                  <th className="text-left p-4 font-heading hidden md:table-cell">Date</th>
                  <th className="text-center p-4 font-heading">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredClaims.map((claim) => (
                  <tr key={claim.claim_id} className="border-t border-gray-200 hover:bg-muted/50">
                    <td className="p-4 font-mono text-sm">{claim.claim_id}</td>
                    <td className="p-4 font-mono text-sm">{claim.order_id}</td>
                    <td className="p-4 hidden md:table-cell">
                      <div>
                        <p className="font-medium">{claim.name}</p>
                        <p className="text-xs text-muted-foreground">{claim.email}</p>
                      </div>
                    </td>
                    <td className="p-4 text-sm">{claim.issue_type?.replace(/_/g, ' ')}</td>
                    <td className="p-4 text-center">
                      <span className={`inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full border ${getStatusColor(claim.status)}`}>
                        {getStatusIcon(claim.status)}
                        {claim.status}
                      </span>
                    </td>
                    <td className="p-4 hidden md:table-cell text-sm text-muted-foreground">
                      {claim.created_at ? new Date(claim.created_at).toLocaleDateString() : '-'}
                    </td>
                    <td className="p-4 text-center">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setSelectedClaim(claim)}
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

      {/* Send Refund Form Modal */}
      {sendFormModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white border-2 border-black rounded-xl shadow-brutal max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-heading text-xl font-bold">Send Refund Form</h2>
                <Button variant="ghost" size="sm" onClick={() => setSendFormModal(false)}>
                  <X className="h-5 w-5" />
                </Button>
              </div>
              
              <p className="text-sm text-muted-foreground mb-4">
                Send a refund claim form link to a customer. The form will be pre-filled with their information.
              </p>
              
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Customer Email *</label>
                  <Input
                    type="email"
                    value={sendFormData.email}
                    onChange={(e) => setSendFormData({...sendFormData, email: e.target.value})}
                    placeholder="customer@email.com"
                    className="border-2 border-black"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Order ID (optional)</label>
                  <Input
                    value={sendFormData.order_id}
                    onChange={(e) => setSendFormData({...sendFormData, order_id: e.target.value})}
                    placeholder="order_abc123"
                    className="border-2 border-black"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Customer Name (optional)</label>
                  <Input
                    value={sendFormData.customer_name}
                    onChange={(e) => setSendFormData({...sendFormData, customer_name: e.target.value})}
                    placeholder="John Doe"
                    className="border-2 border-black"
                  />
                </div>
              </div>
              
              <div className="flex gap-3 mt-6">
                <Button variant="outline" onClick={() => setSendFormModal(false)} className="flex-1 border-2 border-black">
                  Cancel
                </Button>
                <Button 
                  onClick={handleSendRefundForm} 
                  disabled={sending || !sendFormData.email}
                  className="flex-1 bg-primary text-white border-2 border-black"
                >
                  {sending ? 'Sending...' : 'Send Form'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Claim Detail Modal */}
      {selectedClaim && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white border-2 border-black rounded-xl shadow-brutal max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-heading text-2xl font-bold">Claim Details</h2>
                <Button variant="ghost" size="sm" onClick={() => setSelectedClaim(null)}>
                  <X className="h-5 w-5" />
                </Button>
              </div>
              
              {/* Claim Info */}
              <div className="grid md:grid-cols-2 gap-4 mb-6">
                <div className="bg-muted rounded-lg p-4">
                  <p className="text-xs text-muted-foreground">Claim ID</p>
                  <p className="font-mono font-bold">{selectedClaim.claim_id}</p>
                </div>
                <div className="bg-muted rounded-lg p-4">
                  <p className="text-xs text-muted-foreground">Order ID</p>
                  <p className="font-mono font-bold">{selectedClaim.order_id}</p>
                </div>
                <div className="bg-muted rounded-lg p-4">
                  <p className="text-xs text-muted-foreground">Customer</p>
                  <p className="font-bold">{selectedClaim.name}</p>
                  <p className="text-sm text-muted-foreground">{selectedClaim.email}</p>
                  {selectedClaim.phone && <p className="text-sm text-muted-foreground">{selectedClaim.phone}</p>}
                </div>
                <div className="bg-muted rounded-lg p-4">
                  <p className="text-xs text-muted-foreground">Issue Type</p>
                  <p className="font-bold">{selectedClaim.issue_type?.replace(/_/g, ' ')}</p>
                </div>
              </div>

              {/* Description */}
              <div className="mb-6">
                <h3 className="font-heading font-bold mb-2">Description</h3>
                <p className="bg-muted rounded-lg p-4 text-sm">{selectedClaim.description}</p>
              </div>

              {/* Photos */}
              <div className="mb-6">
                <h3 className="font-heading font-bold mb-2">Photo Evidence</h3>
                <div className="bg-muted rounded-lg p-4">
                  <p className="text-sm break-all">{selectedClaim.photo_urls}</p>
                </div>
              </div>

              {/* Status Update */}
              <div className="mb-6">
                <h3 className="font-heading font-bold mb-2">Update Status</h3>
                <div className="flex gap-2">
                  {['pending', 'approved', 'denied', 'resolved'].map((status) => (
                    <Button
                      key={status}
                      variant={selectedClaim.status === status ? 'default' : 'outline'}
                      onClick={() => handleUpdateClaim(selectedClaim.claim_id, { status })}
                      className={`border-2 border-black ${selectedClaim.status === status ? 'bg-primary text-white' : ''}`}
                      size="sm"
                    >
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Admin Notes */}
              <div className="mb-6">
                <h3 className="font-heading font-bold mb-2">Admin Notes</h3>
                <Textarea
                  defaultValue={selectedClaim.admin_notes || ''}
                  placeholder="Add internal notes about this claim..."
                  className="border-2 border-black min-h-[100px]"
                  onBlur={(e) => {
                    if (e.target.value !== selectedClaim.admin_notes) {
                      handleUpdateClaim(selectedClaim.claim_id, { admin_notes: e.target.value });
                    }
                  }}
                />
              </div>

              {/* Resolution */}
              <div>
                <h3 className="font-heading font-bold mb-2">Resolution (sent to customer)</h3>
                <Textarea
                  defaultValue={selectedClaim.resolution || ''}
                  placeholder="Enter resolution message to send to customer..."
                  className="border-2 border-black min-h-[100px]"
                  onBlur={(e) => {
                    if (e.target.value !== selectedClaim.resolution) {
                      handleUpdateClaim(selectedClaim.claim_id, { resolution: e.target.value });
                    }
                  }}
                />
              </div>

              <div className="flex justify-end mt-6">
                <Button onClick={() => setSelectedClaim(null)} className="border-2 border-black">
                  Close
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminRefundClaims;

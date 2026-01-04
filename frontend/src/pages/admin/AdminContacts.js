import React, { useEffect, useState } from 'react';
import { Mail, Calendar, MessageSquare, Reply, Send, X, Loader2 } from 'lucide-react';
import axios from 'axios';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Helper to get token from either storage
const getToken = () => localStorage.getItem('token') || sessionStorage.getItem('token');

const AdminContacts = () => {
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [replyingTo, setReplyingTo] = useState(null);
  const [replyMessage, setReplyMessage] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    const fetchContacts = async () => {
      try {
        const token = getToken();
        const response = await axios.get(`${API_URL}/api/admin/contacts`, { 
          headers: { Authorization: `Bearer ${token}` },
          withCredentials: true 
        });
        setContacts(response.data);
      } catch (error) {
        console.error('Error fetching contacts:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchContacts();
  }, []);

  const handleReply = async (contact) => {
    if (!replyMessage.trim()) {
      toast.error('Please enter a reply message');
      return;
    }

    setSending(true);
    try {
      const token = getToken();
      await axios.post(
        `${API_URL}/api/admin/contacts/${contact.contact_id}/reply`,
        { message: replyMessage },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(`Reply sent to ${contact.email}`);
      setReplyingTo(null);
      setReplyMessage('');
      
      // Mark as read
      setContacts(contacts.map(c => 
        c.contact_id === contact.contact_id ? { ...c, read: true } : c
      ));
    } catch (error) {
      console.error('Error sending reply:', error);
      toast.error('Failed to send reply');
    } finally {
      setSending(false);
    }
  };

  return (
    <div data-testid="admin-contacts">
      <div className="mb-8">
        <h1 className="font-heading text-3xl font-bold mb-2">Messages</h1>
        <p className="text-muted-foreground">Customer inquiries and messages</p>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
              <div className="h-24 bg-muted animate-pulse rounded" />
            </div>
          ))}
        </div>
      ) : contacts.length === 0 ? (
        <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-8 text-center">
          <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">No messages yet</p>
        </div>
      ) : (
        <div className="space-y-4">
          {contacts.map((contact) => (
            <div
              key={contact.contact_id}
              className="bg-white border-2 border-black rounded-xl shadow-brutal p-6"
            >
              <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-heading font-bold text-lg">{contact.subject}</h3>
                    {!contact.read && (
                      <Badge className="bg-secondary text-white">New</Badge>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Mail className="h-4 w-4" />
                      {contact.name} ({contact.email})
                    </span>
                    <span className="flex items-center gap-1">
                      <Calendar className="h-4 w-4" />
                      {new Date(contact.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <Button
                  onClick={() => {
                    setReplyingTo(replyingTo === contact.contact_id ? null : contact.contact_id);
                    setReplyMessage('');
                  }}
                  variant="outline"
                  className="border-2 border-black shadow-brutal hover-lift"
                  data-testid={`reply-btn-${contact.contact_id}`}
                >
                  <Reply className="h-4 w-4 mr-2" />
                  Reply
                </Button>
              </div>
              
              <p className="text-foreground bg-muted p-4 rounded-lg mb-4">
                {contact.message}
              </p>

              {/* Reply Form */}
              {replyingTo === contact.contact_id && (
                <div className="border-t-2 border-dashed border-muted pt-4 mt-4 animate-fade-in">
                  <div className="flex items-center gap-2 mb-3">
                    <Reply className="h-4 w-4 text-primary" />
                    <span className="font-medium">Reply to {contact.name}</span>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 ml-auto"
                      onClick={() => setReplyingTo(null)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                  <Textarea
                    value={replyMessage}
                    onChange={(e) => setReplyMessage(e.target.value)}
                    placeholder="Type your reply here..."
                    className="border-2 border-black mb-3 min-h-[120px]"
                    data-testid={`reply-textarea-${contact.contact_id}`}
                  />
                  <div className="flex gap-2">
                    <Button
                      onClick={() => handleReply(contact)}
                      disabled={sending || !replyMessage.trim()}
                      className="bg-primary text-white border-2 border-black shadow-brutal hover-lift"
                      data-testid={`send-reply-btn-${contact.contact_id}`}
                    >
                      {sending ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Send className="h-4 w-4 mr-2" />
                      )}
                      Send Reply
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => setReplyingTo(null)}
                      className="border-2 border-black"
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminContacts;

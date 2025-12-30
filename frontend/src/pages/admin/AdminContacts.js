import React, { useEffect, useState } from 'react';
import { Mail, Calendar, MessageSquare } from 'lucide-react';
import axios from 'axios';
import { Badge } from '@/components/ui/badge';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const AdminContacts = () => {
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchContacts = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/admin/contacts`, { withCredentials: true });
        setContacts(response.data);
      } catch (error) {
        console.error('Error fetching contacts:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchContacts();
  }, []);

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
              </div>
              <p className="text-foreground bg-muted p-4 rounded-lg">
                {contact.message}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminContacts;

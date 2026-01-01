import React, { useState } from 'react';
import { Mail, Phone, MapPin, Send, Loader2, CheckCircle } from 'lucide-react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const ContactPage = () => {
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [form, setForm] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API_URL}/api/contact`, form);
      setSent(true);
      toast.success('Message sent successfully!');
    } catch (error) {
      toast.error('Failed to send message. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <div className="min-h-screen bg-background py-20">
        <div className="max-w-lg mx-auto px-4 text-center">
          <div className="bg-white border-2 border-black rounded-xl shadow-brutal-lg p-8">
            <CheckCircle className="h-16 w-16 text-accent mx-auto mb-4" />
            <h1 className="font-heading text-3xl font-bold mb-2">Message Sent!</h1>
            <p className="text-muted-foreground mb-6">
              Thank you for reaching out. We'll get back to you within 24-48 hours.
            </p>
            <Button
              onClick={() => {
                setSent(false);
                setForm({ name: '', email: '', subject: '', message: '' });
              }}
              className="bg-primary text-white border-2 border-black shadow-brutal hover-lift"
            >
              Send Another Message
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-12" data-testid="contact-page">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="font-heading text-4xl md:text-5xl font-bold mb-4">Get in Touch</h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Have questions about our products? Want to collaborate? We'd love to hear from you!
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-12">
          {/* Contact Info */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
              <Mail className="h-8 w-8 text-primary mb-3" />
              <h3 className="font-heading font-bold text-lg mb-1">Email</h3>
              <p className="text-muted-foreground">hello@revolutionprinting.com</p>
            </div>
            <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
              <Phone className="h-8 w-8 text-primary mb-3" />
              <h3 className="font-heading font-bold text-lg mb-1">Phone</h3>
              <p className="text-muted-foreground">(555) 123-4567</p>
            </div>
            <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
              <MapPin className="h-8 w-8 text-primary mb-3" />
              <h3 className="font-heading font-bold text-lg mb-1">Address</h3>
              <p className="text-muted-foreground">
                123 Faith Street<br />
                Grace City, GC 12345
              </p>
            </div>
          </div>

          {/* Contact Form */}
          <div className="lg:col-span-2">
            <form onSubmit={handleSubmit} className="bg-white border-2 border-black rounded-xl shadow-brutal p-8">
              <h2 className="font-heading text-2xl font-bold mb-6">Send us a Message</h2>
              
              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Your Name</Label>
                  <Input
                    id="name"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="border-2 border-black h-12"
                    placeholder="John Doe"
                    required
                    data-testid="contact-name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    className="border-2 border-black h-12"
                    placeholder="you@example.com"
                    required
                    data-testid="contact-email"
                  />
                </div>
              </div>

              <div className="space-y-2 mb-4">
                <Label htmlFor="subject">Subject</Label>
                <Input
                  id="subject"
                  value={form.subject}
                  onChange={(e) => setForm({ ...form, subject: e.target.value })}
                  className="border-2 border-black h-12"
                  placeholder="How can we help?"
                  required
                  data-testid="contact-subject"
                />
              </div>

              <div className="space-y-2 mb-6">
                <Label htmlFor="message">Message</Label>
                <Textarea
                  id="message"
                  value={form.message}
                  onChange={(e) => setForm({ ...form, message: e.target.value })}
                  className="border-2 border-black min-h-[150px]"
                  placeholder="Tell us more..."
                  required
                  data-testid="contact-message"
                />
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-primary text-white border-2 border-black shadow-brutal hover-lift h-12"
                data-testid="contact-submit"
              >
                {loading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <>
                    Send Message
                    <Send className="ml-2 h-5 w-5" />
                  </>
                )}
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContactPage;

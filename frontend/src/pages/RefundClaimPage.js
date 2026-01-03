import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Upload, AlertTriangle, CheckCircle, Camera, Send } from 'lucide-react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Checkbox } from '../components/ui/checkbox';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const RefundClaimPage = () => {
  const [searchParams] = useSearchParams();
  const orderIdFromUrl = searchParams.get('order') || '';
  const emailFromUrl = searchParams.get('email') || '';

  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    orderId: orderIdFromUrl,
    email: emailFromUrl,
    name: '',
    phone: '',
    issueType: '',
    description: '',
    photoUrls: '',
    acknowledgePrinterDefect: false,
    acknowledgeNoArtworkRefund: false,
    acknowledge48Hours: false
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.acknowledgePrinterDefect || !formData.acknowledgeNoArtworkRefund || !formData.acknowledge48Hours) {
      toast.error('Please acknowledge all policy statements');
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API_URL}/api/refund-claims`, formData);
      setSubmitted(true);
      toast.success('Refund claim submitted successfully');
    } catch (error) {
      console.error('Error submitting claim:', error);
      toast.error('Failed to submit claim. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-background py-12">
        <div className="container mx-auto px-4 max-w-2xl">
          <div className="bg-green-50 border-2 border-green-400 rounded-xl shadow-brutal p-8 text-center">
            <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-4" />
            <h1 className="font-heading text-3xl font-bold text-green-800 mb-4">Claim Submitted</h1>
            <p className="text-green-700 mb-4">
              Thank you for submitting your refund claim. Our team will review your request within 2-3 business days.
            </p>
            <p className="text-sm text-green-600">
              You will receive an email confirmation at <strong>{formData.email}</strong>
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-12">
      <div className="container mx-auto px-4 max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="font-heading text-3xl md:text-4xl font-bold mb-2">Refund Claim Form</h1>
          <p className="text-muted-foreground">Revolution Printing</p>
        </div>

        {/* Important Notice */}
        <div className="bg-yellow-50 border-2 border-yellow-400 rounded-xl p-6 mb-8">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-6 w-6 text-yellow-600 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-heading font-bold text-yellow-800 mb-2">Important: Before You Submit</h3>
              <ul className="text-sm text-yellow-700 space-y-1">
                <li>• Refunds are only issued for <strong>printer-caused defects</strong></li>
                <li>• Claims must be submitted within <strong>48 hours</strong> of delivery</li>
                <li>• Clear photos of the defect are <strong>required</strong></li>
                <li>• Artwork errors, spelling mistakes, and color variations are <strong>not eligible</strong></li>
              </ul>
            </div>
          </div>
        </div>

        {/* Claim Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
            <h2 className="font-heading text-xl font-bold mb-6">Order Information</h2>
            
            <div className="grid md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="orderId">Order ID *</Label>
                <Input
                  id="orderId"
                  name="orderId"
                  value={formData.orderId}
                  onChange={handleChange}
                  placeholder="e.g., order_abc123"
                  className="border-2 border-black"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email Address *</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="your@email.com"
                  className="border-2 border-black"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Full Name *</Label>
                <Input
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Your full name"
                  className="border-2 border-black"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number</Label>
                <Input
                  id="phone"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder="(optional)"
                  className="border-2 border-black"
                />
              </div>
            </div>
          </div>

          <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
            <h2 className="font-heading text-xl font-bold mb-6">Issue Details</h2>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="issueType">Type of Issue *</Label>
                <select
                  id="issueType"
                  name="issueType"
                  value={formData.issueType}
                  onChange={handleChange}
                  className="w-full border-2 border-black h-12 rounded-md px-3 bg-white"
                  required
                >
                  <option value="">Select issue type...</option>
                  <option value="printing_error">Printing Error (misalignment, smudging)</option>
                  <option value="wrong_product">Wrong Product Received</option>
                  <option value="wrong_size">Wrong Size Received</option>
                  <option value="wrong_color">Wrong Color Received</option>
                  <option value="manufacturing_defect">Manufacturing Defect (tears, holes)</option>
                  <option value="missing_item">Missing Item from Order</option>
                  <option value="damaged_shipping">Damaged During Shipping</option>
                  <option value="other">Other (describe below)</option>
                </select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Detailed Description *</Label>
                <Textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  placeholder="Please describe the issue in detail. Include what you expected vs. what you received."
                  className="border-2 border-black min-h-[120px]"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="photoUrls" className="flex items-center gap-2">
                  <Camera className="h-4 w-4" />
                  Photo Evidence (Required) *
                </Label>
                <Textarea
                  id="photoUrls"
                  name="photoUrls"
                  value={formData.photoUrls}
                  onChange={handleChange}
                  placeholder="Please upload your photos to a service like Google Drive, Dropbox, or Imgur and paste the link(s) here. Include multiple angles if possible."
                  className="border-2 border-black min-h-[80px]"
                  required
                />
                <p className="text-xs text-muted-foreground">
                  Tip: Use Google Drive, Dropbox, or Imgur to share photos. Make sure links are publicly accessible.
                </p>
              </div>
            </div>
          </div>

          {/* Policy Acknowledgments */}
          <div className="bg-red-50 border-2 border-red-300 rounded-xl shadow-brutal p-6">
            <h2 className="font-heading text-xl font-bold text-red-800 mb-4">Policy Acknowledgment</h2>
            <p className="text-sm text-red-700 mb-4">Please confirm you understand our refund policy:</p>
            
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <Checkbox
                  id="acknowledgePrinterDefect"
                  checked={formData.acknowledgePrinterDefect}
                  onCheckedChange={(checked) => setFormData({...formData, acknowledgePrinterDefect: checked})}
                  className="mt-1"
                />
                <label htmlFor="acknowledgePrinterDefect" className="text-sm text-red-800 cursor-pointer">
                  I understand that refunds are only issued for printer-caused defects (printing errors, wrong products, manufacturing defects).
                </label>
              </div>
              
              <div className="flex items-start space-x-3">
                <Checkbox
                  id="acknowledgeNoArtworkRefund"
                  checked={formData.acknowledgeNoArtworkRefund}
                  onCheckedChange={(checked) => setFormData({...formData, acknowledgeNoArtworkRefund: checked})}
                  className="mt-1"
                />
                <label htmlFor="acknowledgeNoArtworkRefund" className="text-sm text-red-800 cursor-pointer">
                  I understand that errors in customer-supplied artwork (spelling, design, layout, color expectations) are NOT eligible for refunds.
                </label>
              </div>
              
              <div className="flex items-start space-x-3">
                <Checkbox
                  id="acknowledge48Hours"
                  checked={formData.acknowledge48Hours}
                  onCheckedChange={(checked) => setFormData({...formData, acknowledge48Hours: checked})}
                  className="mt-1"
                />
                <label htmlFor="acknowledge48Hours" className="text-sm text-red-800 cursor-pointer">
                  I confirm that I am submitting this claim within 48 hours of receiving my order.
                </label>
              </div>
            </div>
          </div>

          <Button
            type="submit"
            disabled={loading || !formData.acknowledgePrinterDefect || !formData.acknowledgeNoArtworkRefund || !formData.acknowledge48Hours}
            className="w-full bg-primary text-white border-2 border-black shadow-brutal hover-lift h-14 text-lg disabled:opacity-50"
          >
            {loading ? (
              'Submitting...'
            ) : (
              <>
                <Send className="h-5 w-5 mr-2" />
                Submit Refund Claim
              </>
            )}
          </Button>
        </form>

        {/* Footer Note */}
        <p className="text-center text-sm text-muted-foreground mt-8">
          Questions? Contact us at <a href="mailto:myrevolutionprinting@gmail.com" className="text-primary underline">myrevolutionprinting@gmail.com</a>
        </p>
      </div>
    </div>
  );
};

export default RefundClaimPage;

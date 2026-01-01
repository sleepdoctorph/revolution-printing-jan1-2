import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ChevronLeft, Check, Palette } from 'lucide-react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const DesignSelectionPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [designs, setDesigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDesign, setSelectedDesign] = useState(null);

  // Get product data from navigation state
  const { product, selectedColor, selectedSize, quantity } = location.state || {};

  useEffect(() => {
    // If no product data, redirect back to shop
    if (!product) {
      navigate('/shop');
      return;
    }

    const fetchDesigns = async () => {
      try {
        // Determine design category based on product category
        const designCategory = product.category === 'hats' ? 'hats' : 'apparel';
        const response = await axios.get(`${API_URL}/api/designs?category=${designCategory}`);
        setDesigns(response.data);
      } catch (error) {
        console.error('Error fetching designs:', error);
        toast.error('Failed to load designs');
      } finally {
        setLoading(false);
      }
    };

    fetchDesigns();
  }, [product, navigate]);

  const handleContinue = () => {
    if (!selectedDesign) {
      toast.error('Please select a design to continue');
      return;
    }

    // Navigate to review/mockup page (Step 3)
    navigate('/review-order', {
      state: {
        product,
        selectedColor,
        selectedSize,
        quantity,
        design: selectedDesign
      }
    });
  };

  if (!product) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background py-8" data-testid="design-selection-page">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Progress Steps */}
        <div className="flex items-center justify-center mb-8">
          <div className="flex items-center">
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary text-white font-bold">
              <Check className="w-5 h-5" />
            </div>
            <span className="ml-2 text-sm font-medium text-muted-foreground">Product</span>
          </div>
          <div className="w-16 h-1 bg-primary mx-2" />
          <div className="flex items-center">
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary text-white font-bold">
              2
            </div>
            <span className="ml-2 text-sm font-bold">Choose Design</span>
          </div>
          <div className="w-16 h-1 bg-muted mx-2" />
          <div className="flex items-center">
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-muted text-muted-foreground font-bold">
              3
            </div>
            <span className="ml-2 text-sm text-muted-foreground">Review & Pay</span>
          </div>
        </div>

        {/* Back Button */}
        <Button
          variant="ghost"
          onClick={() => navigate(-1)}
          className="mb-6"
          data-testid="back-button"
        >
          <ChevronLeft className="h-5 w-5 mr-1" />
          Back to Product
        </Button>

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="font-heading text-3xl md:text-4xl font-bold mb-2">
            Choose Your Design
          </h1>
          <p className="text-muted-foreground">
            Select a design to apply to your {product.name}
          </p>
        </div>

        {/* Selected Product Summary */}
        <div className="bg-card border-2 border-black rounded-xl p-4 mb-8 shadow-brutal">
          <div className="flex items-center gap-4">
            <img
              src={product.images?.[0] || 'https://via.placeholder.com/100'}
              alt={product.name}
              className="w-20 h-20 object-cover rounded-lg border-2 border-black"
            />
            <div className="flex-1">
              <h3 className="font-bold text-lg">{product.name}</h3>
              <p className="text-sm text-muted-foreground">
                {selectedColor} / {selectedSize} / Qty: {quantity}
              </p>
              <p className="text-primary font-bold">${product.price.toFixed(2)}</p>
            </div>
          </div>
        </div>

        {/* Designs Grid */}
        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="aspect-square bg-muted animate-pulse rounded-xl" />
            ))}
          </div>
        ) : designs.length === 0 ? (
          <div className="text-center py-16 bg-card border-2 border-dashed border-muted rounded-xl">
            <Palette className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
            <h3 className="font-heading text-xl font-bold mb-2">No Designs Available Yet</h3>
            <p className="text-muted-foreground mb-4">
              Designs for {product.category === 'hats' ? 'hats' : 'apparel'} will be uploaded soon.
            </p>
            <p className="text-sm text-muted-foreground">
              Please check back later or contact us for custom designs.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {designs.map((design) => (
              <button
                key={design.design_id}
                type="button"
                onClick={() => setSelectedDesign(design)}
                className={`relative aspect-square rounded-xl border-2 overflow-hidden transition-all ${
                  selectedDesign?.design_id === design.design_id
                    ? 'border-primary ring-4 ring-primary/30 scale-105 shadow-brutal-lg'
                    : 'border-black hover:border-primary hover:scale-102 shadow-brutal'
                }`}
                data-testid={`design-${design.design_id}`}
              >
                {design.image_url ? (
                  <img
                    src={design.image_url.startsWith('/') ? `${API_URL}${design.image_url}` : design.image_url}
                    alt={design.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full bg-muted flex items-center justify-center">
                    <Palette className="w-12 h-12 text-muted-foreground" />
                  </div>
                )}
                
                {/* Selection Indicator */}
                {selectedDesign?.design_id === design.design_id && (
                  <div className="absolute top-2 right-2 w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                    <Check className="w-5 h-5 text-white" />
                  </div>
                )}
                
                {/* Design Name */}
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3">
                  <p className="text-white font-bold text-sm truncate">{design.name}</p>
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Continue Button */}
        {designs.length > 0 && (
          <div className="mt-8 flex justify-center">
            <Button
              onClick={handleContinue}
              disabled={!selectedDesign}
              className="bg-primary text-white border-2 border-black shadow-brutal hover-lift h-14 px-12 text-lg"
              data-testid="continue-to-review-button"
            >
              Continue to Review
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default DesignSelectionPage;

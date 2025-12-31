import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Minus, Plus, ShoppingBag, ChevronLeft, Truck, Shield, RotateCcw } from 'lucide-react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { useCart } from '../context/CartContext';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Color name to hex mapping for apparel colors
const colorMap = {
  'white': '#FFFFFF',
  'black': '#000000',
  'navy': '#001F3F',
  'red': '#DC2626',
  'royal': '#4169E1',
  'sport grey': '#8B8B8B',
  'charcoal': '#36454F',
  'forest green': '#228B22',
  'maroon': '#800000',
  'carolina blue': '#56A0D3',
  'ash': '#B2BEB5',
  'gold': '#FFD700',
  'orange': '#FF6600',
  'purple': '#800080',
  'irish green': '#009A44',
  'heliconia': '#E4007C',
  'light blue': '#ADD8E6',
  'light pink': '#FFB6C1',
  'daisy': '#FFD54F',
  'lime': '#32CD32',
  'azalea': '#F19CBB',
  'cherry red': '#DE3163',
  'military green': '#4B5320',
  'sapphire': '#0F52BA',
  'dark heather': '#4A4A4A',
  'cardinal red': '#C41E3A',
  'cardinal': '#C41E3A',
  'safety green': '#78FF00',
  'safety orange': '#FF6700',
  'safety pink': '#FF69B4',
  'graphite heather': '#5C5C5C',
  'gravel': '#6E6E6E',
  'brown savana': '#8B4513',
  'sand': '#C2B280',
  'coral silk': '#FF7F50',
  'dusty rose': '#DCAE96',
  'antique cherry red': '#CD5C5C',
  'antique irish green': '#3CB371',
  'antique jade dome': '#00A86B',
  'antique orange': '#FF7538',
  'antique sapphire': '#2F5DA6',
  'heather navy': '#4A5568',
  'heather red': '#E57373',
  'heather purple': '#9370DB',
  'heather royal': '#6495ED',
  'heather military green': '#6B8E23',
  'heather maroon': '#8B3A3A',
  'heather orange': '#FF8C69',
  'heather irish green': '#66CDAA',
  'heather sapphire': '#6A8DC2',
  'heather radiant orchid': '#B163A3',
  'pitch black': '#0D0D0D',
  'navy mist': '#7B8FA1',
  'red mist': '#D4A5A5',
  'gunmetal': '#536267',
  'cement': '#A9A9A9',
  'caribbean mist': '#6FB7B7',
  'daisy mist': '#F5E6AB',
  'cactus': '#5D8A66',
  'steel blue': '#4682B4',
  'dark navy': '#1C2841',
  'deep royal': '#002366',
  'chalky mint': '#98FF98',
  'chambray': '#A4C8D9',
  'flo blue': '#00A3E0',
  'lagoon blue': '#4682B4',
  'off white': '#FAF9F6',
  'scarlet red': '#FF2400',
  'blue dusk': '#6699CC',
  'garnet': '#733635',
  'dark chocolate': '#3D1C00',
  'tan': '#D2B48C',
  'baby blue': '#89CFF0',
  'caribbean blue': '#1AC1DD',
  'charity pink': '#FF69B4',
  'heather blue': '#7B9FC4',
  'heather dark grey': '#5A5A5A',
  'heather grey': '#9E9E9E',
  'kelly green': '#4CBB17',
  'mustard': '#FFDB58',
  'sage': '#9CAF88',
  'violet': '#8B00FF',
  'aquatic': '#00CED1',
  'berry': '#8E4585',
  'blackberry': '#4A2C2A',
  'cobalt': '#0047AB',
  'cornsilk': '#FFF8DC',
  'electric green': '#00FF00',
  'ice grey': '#D0D0D0',
  'indigo blue': '#4B0082',
  'kiwi': '#8EE53F',
  'lilac': '#C8A2C8',
  'midnight': '#191970',
  'midnight navy': '#003366',
  'mint green': '#98FF98',
  'natural': '#F5F5DC',
  'neon blue': '#1B03A3',
  'neon green': '#39FF14',
  'old gold': '#CFB53B',
  'russet': '#80461B',
  'sky': '#87CEEB',
  'sunset': '#FAD6A5',
  'tangerine': '#FF9966',
  'tennessee orange': '#FF8200',
  'texas orange': '#BF5700',
  'tropical blue': '#00BFFF',
  'turf green': '#3D9140',
  'tweed': '#8B8589',
  'yellow haze': '#F0E68C',
  'paragon': '#6B5B95',
  'teal': '#008080',
  'white mist': '#F5F5F5'
};

// Get hex color from color name
const getColorHex = (colorName) => {
  const key = colorName.toLowerCase().trim();
  return colorMap[key] || '#CCCCCC';
};

const ProductDetailPage = () => {
  const { productId } = useParams();
  const navigate = useNavigate();
  const { addItem } = useCart();
  
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedColor, setSelectedColor] = useState('');
  const [selectedSize, setSelectedSize] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [selectedImage, setSelectedImage] = useState(0);

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/products/${productId}`);
        setProduct(response.data);
        if (response.data.colors?.length > 0) {
          setSelectedColor(response.data.colors[0]);
        }
        if (response.data.sizes?.length > 0) {
          setSelectedSize(response.data.sizes[0]);
        }
      } catch (error) {
        console.error('Error fetching product:', error);
        navigate('/shop');
      } finally {
        setLoading(false);
      }
    };
    fetchProduct();
  }, [productId, navigate]);

  const handleAddToCart = () => {
    if (product) {
      addItem(product, quantity, selectedColor, selectedSize);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12">
            <div className="aspect-square bg-muted animate-pulse rounded-xl" />
            <div className="space-y-4">
              <div className="h-8 bg-muted animate-pulse rounded w-1/4" />
              <div className="h-12 bg-muted animate-pulse rounded w-3/4" />
              <div className="h-24 bg-muted animate-pulse rounded" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!product) return null;

  return (
    <div className="min-h-screen bg-background py-8" data-testid="product-detail-page">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Back Button */}
        <Button
          variant="ghost"
          onClick={() => navigate(-1)}
          className="mb-6"
          data-testid="back-button"
        >
          <ChevronLeft className="h-5 w-5 mr-1" />
          Back to Shop
        </Button>

        <div className="grid lg:grid-cols-2 gap-12">
          {/* Images */}
          <div className="space-y-4">
            <div className="aspect-square rounded-xl border-2 border-black overflow-hidden shadow-brutal-lg bg-white">
              <img
                src={product.images?.[selectedImage] || 'https://via.placeholder.com/600'}
                alt={product.name}
                className="w-full h-full object-cover"
              />
            </div>
            {product.images?.length > 1 && (
              <div className="flex gap-4">
                {product.images.map((image, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => setSelectedImage(index)}
                    className={`w-20 h-20 rounded-lg border-2 overflow-hidden transition-all ${
                      selectedImage === index 
                        ? 'border-primary shadow-brutal-sm' 
                        : 'border-black hover:border-primary'
                    }`}
                  >
                    <img src={image} alt="" className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Product Info */}
          <div className="space-y-6">
            <div>
              <p className="text-sm text-muted-foreground uppercase tracking-wide mb-1">
                {product.brand || 'Faithful Threads'}
              </p>
              <h1 className="font-heading text-3xl md:text-4xl font-bold mb-2">
                {product.name}
              </h1>
              <div className="flex items-center gap-4">
                <span className="font-bold text-3xl text-primary">
                  ${product.price.toFixed(2)}
                </span>
                {product.is_blank && (
                  <span className="bg-accent text-white text-xs font-bold px-3 py-1 rounded-full">
                    Blank
                  </span>
                )}
              </div>
            </div>

            <p className="text-muted-foreground text-lg leading-relaxed">
              {product.description}
            </p>

            {/* Color Selection */}
            {product.colors?.length > 0 && (
              <div>
                <label className="font-heading font-bold text-sm mb-2 block">
                  Color: <span className="font-normal">{selectedColor}</span>
                </label>
                <div className="flex flex-wrap gap-2">
                  {product.colors.map((color) => {
                    const hexColor = getColorHex(color);
                    const isLight = hexColor === '#FFFFFF' || hexColor === '#FAF9F6' || hexColor === '#B2BEB5';
                    return (
                      <button
                        key={color}
                        type="button"
                        onClick={() => setSelectedColor(color)}
                        className={`w-8 h-8 rounded-full transition-all ${
                          selectedColor === color
                            ? 'ring-2 ring-primary ring-offset-2 scale-110'
                            : 'hover:scale-110'
                        } ${isLight ? 'border-2 border-gray-300' : 'border border-gray-200'}`}
                        style={{ backgroundColor: hexColor }}
                        title={color}
                        data-testid={`color-${color.toLowerCase().replace(/\s+/g, '-')}`}
                      />
                    );
                  })}
                </div>
                {product.colors.length > 10 && (
                  <p className="text-xs text-muted-foreground mt-2">
                    {product.colors.length} colors available
                  </p>
                )}
              </div>
            )}

            {/* Size Selection */}
            {product.sizes?.length > 0 && (
              <div>
                <label className="font-heading font-bold text-sm mb-2 block">
                  Size
                </label>
                <Select value={selectedSize} onValueChange={setSelectedSize}>
                  <SelectTrigger className="w-full border-2 border-black h-12" data-testid="size-select">
                    <SelectValue placeholder="Select size" />
                  </SelectTrigger>
                  <SelectContent>
                    {product.sizes.map((size) => (
                      <SelectItem key={size} value={size}>{size}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Quantity */}
            <div>
              <label className="font-heading font-bold text-sm mb-2 block">
                Quantity
              </label>
              <div className="flex items-center gap-4">
                <div className="flex items-center border-2 border-black rounded-lg">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    disabled={quantity <= 1}
                    className="h-12 w-12"
                  >
                    <Minus className="h-4 w-4" />
                  </Button>
                  <span className="w-12 text-center font-bold text-lg">{quantity}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setQuantity(quantity + 1)}
                    className="h-12 w-12"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                <span className="text-muted-foreground">
                  {product.stock > 0 ? `${product.stock} in stock` : 'Out of stock'}
                </span>
              </div>
            </div>

            {/* Add to Cart */}
            <Button
              onClick={handleAddToCart}
              disabled={product.stock === 0}
              className="w-full bg-primary text-white border-2 border-black shadow-brutal hover-lift h-14 text-lg"
              data-testid="add-to-cart-button"
            >
              <ShoppingBag className="h-5 w-5 mr-2" />
              Add to Cart
            </Button>

            {/* Features */}
            <div className="grid grid-cols-3 gap-4 pt-6 border-t">
              <div className="text-center">
                <Truck className="h-6 w-6 mx-auto text-primary mb-2" />
                <p className="text-xs text-muted-foreground">Free shipping over $50</p>
              </div>
              <div className="text-center">
                <Shield className="h-6 w-6 mx-auto text-primary mb-2" />
                <p className="text-xs text-muted-foreground">Quality guaranteed</p>
              </div>
              <div className="text-center">
                <RotateCcw className="h-6 w-6 mx-auto text-primary mb-2" />
                <p className="text-xs text-muted-foreground">Easy returns</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDetailPage;

import React from 'react';
import { Link } from 'react-router-dom';
import { ShoppingBag } from 'lucide-react';
import { Button } from '../components/ui/button';
import { useCart } from '../context/CartContext';

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
  'white mist': '#F5F5F5',
  // Hoodie specific colors
  'iris': '#5A4FCF',
  'metro blue': '#4169E1',
  'oceana': '#4F94CD',
  'orchid': '#DA70D6',
  'pistachio': '#93C572',
  'stone blue': '#89A4B8',
  'vegas gold': '#C5B358',
  'khaki': '#C3B091',
  'cocoa': '#875F42',
  'olive': '#808000',
  'pink lemonade': '#FFB6C1'
};

const getColorHex = (colorName) => {
  const key = colorName.toLowerCase().trim();
  return colorMap[key] || '#CCCCCC';
};

const ProductCard = ({ product }) => {
  const { addItem } = useCart();
  
  const handleQuickAdd = (e) => {
    e.preventDefault();
    e.stopPropagation();
    addItem(product, 1, product.colors?.[0] || '', product.sizes?.[0] || '');
  };

  return (
    <Link
      to={`/product/${product.product_id}`}
      className="group block"
      data-testid={`product-card-${product.product_id}`}
    >
      <div className="bg-white border-2 border-black rounded-xl overflow-hidden shadow-brutal transition-all duration-300 hover:shadow-brutal-lg hover:-translate-y-1">
        {/* Image */}
        <div className="relative aspect-square overflow-hidden bg-muted">
          <img
            src={product.images?.[0] || 'https://via.placeholder.com/400'}
            alt={product.name}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
          {product.featured && (
            <span className="absolute top-3 left-3 bg-primary text-white text-xs font-bold px-3 py-1 rounded-full border border-black">
              Featured
            </span>
          )}
          {product.is_blank && (
            <span className="absolute top-3 right-3 bg-accent text-white text-xs font-bold px-3 py-1 rounded-full border border-black">
              Blank
            </span>
          )}
          {/* Quick Add Button */}
          <Button
            onClick={handleQuickAdd}
            className="absolute bottom-3 right-3 bg-primary text-white border-2 border-black shadow-brutal-sm opacity-0 group-hover:opacity-100 transition-opacity"
            size="icon"
            data-testid={`quick-add-${product.product_id}`}
          >
            <ShoppingBag className="h-4 w-4" />
          </Button>
        </div>
        
        {/* Content */}
        <div className="p-4">
          <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
            {product.brand || 'Revolution Printing'}
          </p>
          <h3 className="font-heading font-bold text-lg text-foreground mb-2 line-clamp-1">
            {product.name}
          </h3>
          <div className="flex items-center justify-between">
            <span className="font-bold text-xl text-primary">
              ${product.price.toFixed(2)}
            </span>
            {product.colors?.length > 0 && (
              <div className="flex gap-1">
                {product.colors.slice(0, 4).map((color, i) => {
                  const hexColor = getColorHex(color);
                  const isLight = hexColor === '#FFFFFF' || hexColor === '#FAF9F6' || hexColor === '#B2BEB5' || hexColor === '#F5F5DC';
                  return (
                    <span
                      key={i}
                      className={`w-4 h-4 rounded-full ${isLight ? 'border-2 border-gray-300' : 'border border-black'}`}
                      style={{ backgroundColor: hexColor }}
                      title={color}
                    />
                  );
                })}
                {product.colors.length > 4 && (
                  <span className="text-xs text-muted-foreground">
                    +{product.colors.length - 4}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
};

export default ProductCard;

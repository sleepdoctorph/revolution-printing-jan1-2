import React from 'react';
import { Link } from 'react-router-dom';
import { ShoppingBag } from 'lucide-react';
import { Button } from '../components/ui/button';
import { useCart } from '../context/CartContext';

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
            {product.brand || 'Faithful Threads'}
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
                {product.colors.slice(0, 4).map((color, i) => (
                  <span
                    key={i}
                    className="w-4 h-4 rounded-full border border-black"
                    style={{ backgroundColor: color.toLowerCase() }}
                    title={color}
                  />
                ))}
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

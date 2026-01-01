import React from 'react';
import { X, Plus, Minus, ShoppingBag, Palette } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '../components/ui/sheet';
import { Button } from '../components/ui/button';
import { ScrollArea } from '../components/ui/scroll-area';
import { Separator } from '../components/ui/separator';
import { useCart } from '../context/CartContext';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const CartDrawer = () => {
  const { items, isOpen, setIsOpen, removeItem, updateQuantity, totalPrice, totalItems } = useCart();
  const navigate = useNavigate();

  const handleCheckout = () => {
    setIsOpen(false);
    navigate('/checkout');
  };

  return (
    <Sheet open={isOpen} onOpenChange={setIsOpen}>
      <SheetContent className="border-l-2 border-black flex flex-col w-full sm:max-w-md" data-testid="cart-drawer">
        <SheetHeader>
          <SheetTitle className="font-heading text-xl flex items-center gap-2">
            <ShoppingBag className="h-5 w-5" />
            Your Cart ({totalItems})
          </SheetTitle>
        </SheetHeader>

        {items.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
            <ShoppingBag className="h-16 w-16 text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">Your cart is empty</p>
            <p className="text-muted-foreground text-sm mb-4">
              Add some faithful threads to get started!
            </p>
            <Button
              onClick={() => {
                setIsOpen(false);
                navigate('/shop');
              }}
              className="bg-primary text-white border-2 border-black shadow-brutal hover-lift"
            >
              Start Shopping
            </Button>
          </div>
        ) : (
          <>
            <ScrollArea className="flex-1 -mx-6 px-6">
              <div className="space-y-4 py-4">
                {items.map((item, index) => (
                  <div
                    key={`${item.product_id}-${item.color}-${item.size}-${item.design_id || 'no-design'}`}
                    className="flex gap-4 animate-fade-in"
                    style={{ animationDelay: `${index * 50}ms` }}
                    data-testid={`cart-item-${item.product_id}`}
                  >
                    {/* Image */}
                    <div className="w-20 h-20 rounded-lg border-2 border-black overflow-hidden bg-muted flex-shrink-0 relative">
                      <img
                        src={item.image || 'https://via.placeholder.com/80'}
                        alt={item.name}
                        className="w-full h-full object-cover"
                      />
                      {/* Design overlay indicator */}
                      {item.design_image && (
                        <div className="absolute bottom-1 right-1 w-6 h-6 bg-white rounded-full border border-black p-0.5">
                          <Palette className="w-full h-full text-primary" />
                        </div>
                      )}
                    </div>

                    {/* Details */}
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-sm line-clamp-1">{item.name}</h4>
                      <p className="text-xs text-muted-foreground">
                        {item.color && `${item.color}`}
                        {item.color && item.size && ' / '}
                        {item.size && `${item.size}`}
                      </p>
                      {item.design_name && (
                        <p className="text-xs text-primary font-medium mt-0.5">
                          Design: {item.design_name}
                        </p>
                      )}
                      <p className="font-bold text-primary mt-1">
                        ${item.price.toFixed(2)}
                      </p>
                    </div>

                    {/* Quantity Controls */}
                    <div className="flex flex-col items-end gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={() => removeItem(item.product_id, item.color, item.size, item.design_id)}
                        data-testid={`remove-item-${item.product_id}`}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                      <div className="flex items-center gap-2 border-2 border-black rounded-lg">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => updateQuantity(item.product_id, item.color, item.size, item.quantity - 1, item.design_id)}
                        >
                          <Minus className="h-3 w-3" />
                        </Button>
                        <span className="w-6 text-center text-sm font-medium">
                          {item.quantity}
                        </span>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => updateQuantity(item.product_id, item.color, item.size, item.quantity + 1, item.design_id)}
                        >
                          <Plus className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>

            <div className="border-t-2 border-black pt-4 space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Subtotal</span>
                <span className="font-bold text-lg">${totalPrice.toFixed(2)}</span>
              </div>
              <p className="text-xs text-muted-foreground text-center">
                Shipping & taxes calculated at checkout
              </p>
              <Button
                onClick={handleCheckout}
                className="w-full bg-primary text-white border-2 border-black shadow-brutal hover-lift h-12 text-lg"
                data-testid="checkout-button"
              >
                Checkout
              </Button>
              <Button
                variant="outline"
                onClick={() => setIsOpen(false)}
                className="w-full border-2 border-black"
              >
                Continue Shopping
              </Button>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
};

export default CartDrawer;

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const CartContext = createContext(null);

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within CartProvider');
  }
  return context;
};

export const CartProvider = ({ children }) => {
  const [items, setItems] = useState(() => {
    const saved = localStorage.getItem('cart');
    return saved ? JSON.parse(saved) : [];
  });
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem('cart', JSON.stringify(items));
  }, [items]);

  const addItem = useCallback((product, quantity = 1, color = '', size = '', design = null) => {
    setItems(prev => {
      const existingIndex = prev.findIndex(
        item => item.product_id === product.product_id && 
                item.color === color && 
                item.size === size &&
                item.design_id === (design?.design_id || '')
      );

      if (existingIndex > -1) {
        const updated = [...prev];
        updated[existingIndex].quantity += quantity;
        return updated;
      }

      return [...prev, {
        product_id: product.product_id,
        name: product.name,
        price: product.price,
        image: product.images?.[0] || '',
        color,
        size,
        quantity,
        design_id: design?.design_id || '',
        design_name: design?.name || '',
        design_image: design?.image_url || ''
      }];
    });
    setIsOpen(true);
  }, []);

  const removeItem = useCallback((productId, color, size, designId = '') => {
    setItems(prev => prev.filter(
      item => !(item.product_id === productId && item.color === color && item.size === size && item.design_id === designId)
    ));
  }, []);

  const updateQuantity = useCallback((productId, color, size, quantity, designId = '') => {
    if (quantity <= 0) {
      removeItem(productId, color, size, designId);
      return;
    }
    
    setItems(prev => prev.map(item => {
      if (item.product_id === productId && item.color === color && item.size === size && item.design_id === designId) {
        return { ...item, quantity };
      }
      return item;
    }));
  }, [removeItem]);

  const clearCart = useCallback(() => {
    setItems([]);
  }, []);

  const totalItems = items.reduce((sum, item) => sum + item.quantity, 0);
  const totalPrice = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);

  const value = {
    items,
    isOpen,
    setIsOpen,
    addItem,
    removeItem,
    updateQuantity,
    clearCart,
    totalItems,
    totalPrice
  };

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
};

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShoppingCart, User, Menu, X, LogOut, Settings } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '../components/ui/sheet';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';

// Sparkle component
const SparkleEffect = ({ x, y, onComplete }) => {
  React.useEffect(() => {
    const timer = setTimeout(onComplete, 1200);
    return () => clearTimeout(timer);
  }, [onComplete]);

  const sparkles = Array.from({ length: 16 }, (_, i) => {
    const angle = (i / 16) * Math.PI * 2;
    const distance = 40 + Math.random() * 50;
    return {
      id: i,
      x: Math.cos(angle) * distance,
      y: Math.sin(angle) * distance,
      delay: Math.random() * 0.3,
      size: 14 + Math.random() * 10,
    };
  });

  return (
    <div 
      className="fixed pointer-events-none z-[9999]"
      style={{ left: x, top: y }}
    >
      {sparkles.map((sparkle) => (
        <div
          key={sparkle.id}
          className="absolute text-yellow-400"
          style={{
            left: sparkle.x,
            top: sparkle.y,
            fontSize: sparkle.size,
            animation: `sparkle-burst 1s ease-out forwards`,
            animationDelay: `${sparkle.delay}s`,
          }}
        >
          ✦
        </div>
      ))}
    </div>
  );
};

const Navbar = () => {
  const { user, logout, isAdmin } = useAuth();
  const { totalItems, setIsOpen: setCartOpen } = useCart();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [sparkle, setSparkle] = useState(null);
  const [glowingLink, setGlowingLink] = useState(null);

  const navLinks = [
    { name: 'Home', href: '/', isCategory: false },
    { name: 'Shop', href: '/shop', isCategory: false },
    { name: 'T-Shirts', href: '/shop?category=tshirts', isCategory: true },
    { name: 'Hoodies', href: '/shop?category=hoodies', isCategory: true },
    { name: 'Hats', href: '/shop?category=hats', isCategory: true },
    { name: 'Mugs', href: '/shop?category=mugs', isCategory: true },
    { name: 'About', href: '/about', isCategory: false },
    { name: 'Contact', href: '/contact', isCategory: false },
  ];

  const handleCategoryClick = (e, link) => {
    if (link.isCategory) {
      e.preventDefault();
      
      const rect = e.currentTarget.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      
      setGlowingLink(link.name);
      setSparkle({ x: centerX, y: centerY, href: link.href });
      
      setTimeout(() => {
        setGlowingLink(null);
        setSparkle(null);
        navigate(link.href);
      }, 1200);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <nav className="sticky top-0 z-50 bg-background border-b-2 border-black">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2" data-testid="logo">
            <img 
              src="https://customer-assets.emergentagent.com/job_faithapparel/artifacts/odi1used_logo%201.png" 
              alt="Revolution Printing" 
              className="h-12 object-contain"
            />
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-6">
            {navLinks.map((link) => (
              <Link
                key={link.name}
                to={link.href}
                onClick={(e) => handleCategoryClick(e, link)}
                className={`text-foreground hover:text-primary font-medium transition-all duration-200 px-2 py-1 rounded-lg ${
                  glowingLink === link.name 
                    ? 'text-primary scale-110 shadow-[0_0_20px_rgba(217,119,6,0.8)] bg-primary/10' 
                    : ''
                }`}
                data-testid={`nav-${link.name.toLowerCase().replace(' ', '-')}`}
              >
                {link.name}
              </Link>
            ))}
          </div>

          {/* Sparkle Effect */}
          {sparkle && (
            <SparkleEffect 
              x={sparkle.x} 
              y={sparkle.y} 
              onComplete={() => setSparkle(null)} 
            />
          )}

          {/* Right Side Actions */}
          <div className="flex items-center gap-4">
            {/* Cart Button */}
            <Button
              variant="outline"
              size="icon"
              className="relative border-2 border-black shadow-brutal hover-lift"
              onClick={() => setCartOpen(true)}
              data-testid="cart-button"
            >
              <ShoppingCart className="h-5 w-5" />
              {totalItems > 0 && (
                <span className="absolute -top-2 -right-2 bg-secondary text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center border border-black">
                  {totalItems}
                </span>
              )}
            </Button>

            {/* User Menu */}
            {user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    size="icon"
                    className="border-2 border-black shadow-brutal hover-lift"
                    data-testid="user-menu-button"
                  >
                    <User className="h-5 w-5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="border-2 border-black shadow-brutal">
                  <div className="px-2 py-1.5">
                    <p className="text-sm font-medium">{user.name}</p>
                    <p className="text-xs text-muted-foreground">{user.email}</p>
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => navigate('/orders')} data-testid="my-orders-link">
                    My Orders
                  </DropdownMenuItem>
                  {isAdmin && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => navigate('/admin')} data-testid="admin-link">
                        <Settings className="mr-2 h-4 w-4" />
                        Admin Dashboard
                      </DropdownMenuItem>
                    </>
                  )}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} data-testid="logout-button">
                    <LogOut className="mr-2 h-4 w-4" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Button
                onClick={() => navigate('/login')}
                className="bg-primary text-white border-2 border-black shadow-brutal hover-lift"
                data-testid="login-button"
              >
                Sign In
              </Button>
            )}

            {/* Mobile Menu */}
            <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
              <SheetTrigger asChild className="md:hidden">
                <Button variant="outline" size="icon" className="border-2 border-black">
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="border-l-2 border-black">
                <div className="flex flex-col gap-4 mt-8">
                  {navLinks.map((link) => (
                    <Link
                      key={link.name}
                      to={link.href}
                      onClick={() => setMobileOpen(false)}
                      className="text-lg font-medium hover:text-primary"
                    >
                      {link.name}
                    </Link>
                  ))}
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;

import React from 'react';
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

const Navbar = () => {
  const { user, logout, isAdmin } = useAuth();
  const { totalItems, setIsOpen: setCartOpen } = useCart();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = React.useState(false);

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

  const createSparkles = (e) => {
    const rect = e.target.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    // Create sparkle container
    const container = document.createElement('div');
    container.className = 'sparkle-container';
    container.style.left = `${centerX}px`;
    container.style.top = `${centerY}px`;
    document.body.appendChild(container);
    
    // Create multiple sparkles
    for (let i = 0; i < 12; i++) {
      const sparkle = document.createElement('div');
      sparkle.className = 'sparkle';
      const angle = (i / 12) * Math.PI * 2;
      const distance = 30 + Math.random() * 40;
      sparkle.style.left = `${Math.cos(angle) * distance}px`;
      sparkle.style.top = `${Math.sin(angle) * distance}px`;
      sparkle.style.animationDelay = `${Math.random() * 0.2}s`;
      container.appendChild(sparkle);
    }
    
    // Remove container after animation
    setTimeout(() => container.remove(), 800);
  };

  const handleCategoryClick = (e, link) => {
    if (link.isCategory) {
      e.preventDefault();
      e.target.classList.add('nav-link-sparkle');
      createSparkles(e);
      
      setTimeout(() => {
        e.target.classList.remove('nav-link-sparkle');
        navigate(link.href);
      }, 500);
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
                className="text-foreground hover:text-primary font-medium transition-colors"
                data-testid={`nav-${link.name.toLowerCase().replace(' ', '-')}`}
              >
                {link.name}
              </Link>
            ))}
          </div>

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

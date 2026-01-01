import React from 'react';
import { Link } from 'react-router-dom';
import { Facebook, Instagram, Twitter, Mail, MapPin, Phone } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="bg-foreground text-background mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1">
            <h3 className="font-heading text-2xl font-bold text-primary mb-4">Revolution Printing</h3>
            <p className="text-muted-foreground text-sm mb-4">
              Spreading faith through fashion. Quality Christian apparel for the whole family.
            </p>
            <div className="flex gap-4">
              <a href="#" className="text-muted-foreground hover:text-primary transition-colors">
                <Facebook className="h-5 w-5" />
              </a>
              <a href="#" className="text-muted-foreground hover:text-primary transition-colors">
                <Instagram className="h-5 w-5" />
              </a>
              <a href="#" className="text-muted-foreground hover:text-primary transition-colors">
                <Twitter className="h-5 w-5" />
              </a>
            </div>
          </div>

          {/* Shop */}
          <div>
            <h4 className="font-heading font-bold text-lg mb-4">Shop</h4>
            <ul className="space-y-2">
              <li>
                <Link to="/shop?category=tshirts" className="text-muted-foreground hover:text-primary text-sm transition-colors">
                  T-Shirts
                </Link>
              </li>
              <li>
                <Link to="/shop?category=hoodies" className="text-muted-foreground hover:text-primary text-sm transition-colors">
                  Hoodies
                </Link>
              </li>
              <li>
                <Link to="/shop?category=hats" className="text-muted-foreground hover:text-primary text-sm transition-colors">
                  Hats
                </Link>
              </li>
              <li>
                <Link to="/shop?category=mugs" className="text-muted-foreground hover:text-primary text-sm transition-colors">
                  Mugs
                </Link>
              </li>
              <li>
                <Link to="/shop?blanks=true" className="text-muted-foreground hover:text-primary text-sm transition-colors">
                  Blank Products
                </Link>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="font-heading font-bold text-lg mb-4">Company</h4>
            <ul className="space-y-2">
              <li>
                <Link to="/about" className="text-muted-foreground hover:text-primary text-sm transition-colors">
                  About Us
                </Link>
              </li>
              <li>
                <Link to="/contact" className="text-muted-foreground hover:text-primary text-sm transition-colors">
                  Contact
                </Link>
              </li>
              <li>
                <Link to="/faq" className="text-muted-foreground hover:text-primary text-sm transition-colors">
                  FAQ
                </Link>
              </li>
              <li>
                <Link to="/shipping" className="text-muted-foreground hover:text-primary text-sm transition-colors">
                  Shipping Policy
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="font-heading font-bold text-lg mb-4">Contact</h4>
            <ul className="space-y-3">
              <li className="flex items-center gap-2 text-muted-foreground text-sm">
                <Mail className="h-4 w-4 text-primary" />
                hello@revolutionprinting.com
              </li>
              <li className="flex items-center gap-2 text-muted-foreground text-sm">
                <Phone className="h-4 w-4 text-primary" />
                (555) 123-4567
              </li>
              <li className="flex items-start gap-2 text-muted-foreground text-sm">
                <MapPin className="h-4 w-4 text-primary mt-0.5" />
                123 Faith Street<br />
                Grace City, GC 12345
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-muted-foreground/20 mt-8 pt-8 text-center">
          <p className="text-muted-foreground text-sm">
            © {new Date().getFullYear()} Revolution Printing. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;

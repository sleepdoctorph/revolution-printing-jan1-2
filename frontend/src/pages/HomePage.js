import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Star, Truck, Shield, Heart } from 'lucide-react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import ProductCard from '../components/ProductCard';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const HomePage = () => {
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        // Seed database first
        await axios.post(`${API_URL}/api/seed`);
        
        // Fetch featured products
        const response = await axios.get(`${API_URL}/api/products?featured=true`);
        setFeaturedProducts(response.data.slice(0, 8));
      } catch (error) {
        console.error('Error fetching products:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchProducts();
  }, []);

  const categories = [
    { name: 'T-Shirts', slug: 'tshirts', image: 'https://customer-assets.emergentagent.com/job_faithapparel/artifacts/yimlwpen_image.png', color: 'bg-primary' },
    { name: 'Hoodies', slug: 'hoodies', image: 'https://images.pexels.com/photos/8217415/pexels-photo-8217415.jpeg', color: 'bg-secondary' },
    { name: 'Hats', slug: 'hats', image: 'https://customer-assets.emergentagent.com/job_faithapparel/artifacts/sts99fzr_hat%20category.png', color: 'bg-accent' },
    { name: 'Mugs', slug: 'mugs', image: 'https://customer-assets.emergentagent.com/job_faithapparel/artifacts/v6zpunbr_mug%20category.png', color: 'bg-chart-4' },
  ];

  return (
    <div className="min-h-screen" data-testid="home-page">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-background py-20 lg:py-32">
        <div className="absolute inset-0 hero-overlay" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="animate-fade-in">
              <h1 className="font-heading text-5xl md:text-7xl font-extrabold tracking-tight leading-none mb-6">
                Inspired by Scripture.{' '}
                <span className="text-primary">Designed</span>
                {' '}for Life.
              </h1>
              <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-lg">
                Premium Christian apparel that makes a statement. T-shirts, hoodies, hats, and mugs designed to inspire and spread the message of faith.
              </p>
              <div className="flex flex-wrap gap-4">
                <Button
                  asChild
                  className="bg-primary text-white border-2 border-black shadow-brutal hover-lift h-12 px-8 text-lg"
                >
                  <Link to="/shop" data-testid="shop-now-btn">
                    Shop Now
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Link>
                </Button>
                <Button
                  asChild
                  variant="outline"
                  className="border-2 border-black shadow-brutal hover-lift h-12 px-8 text-lg"
                >
                  <Link to="/about">Our Story</Link>
                </Button>
              </div>
            </div>
            <div className="relative animate-fade-in" style={{ animationDelay: '200ms' }}>
              <img
                src="https://customer-assets.emergentagent.com/job_faithapparel/artifacts/ayjfal3q_webpage%20image.png"
                alt="Revolution Printing - Jesus Is My Rock shirt, Faith Over Fear hat, Saved By Grace mug"
                className="rounded-xl border-2 border-black shadow-brutal-lg w-full h-auto object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-12 bg-foreground text-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div className="flex flex-col items-center">
              <Truck className="h-8 w-8 text-primary mb-3" />
              <h3 className="font-heading font-bold text-lg">Free Shipping</h3>
              <p className="text-muted-foreground text-sm">On orders over $50</p>
            </div>
            <div className="flex flex-col items-center">
              <Shield className="h-8 w-8 text-primary mb-3" />
              <h3 className="font-heading font-bold text-lg">Quality Guaranteed</h3>
              <p className="text-muted-foreground text-sm">Premium materials only</p>
            </div>
            <div className="flex flex-col items-center">
              <Heart className="h-8 w-8 text-primary mb-3" />
              <h3 className="font-heading font-bold text-lg">Made with Love</h3>
              <p className="text-muted-foreground text-sm">Faith in every stitch</p>
            </div>
          </div>
        </div>
      </section>

      {/* Shop by Category */}
      <section className="py-20 bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="font-heading text-3xl md:text-5xl font-bold mb-4">Shop by Category</h2>
            <p className="text-muted-foreground text-lg">Find your perfect faithful thread</p>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {categories.map((category, index) => (
              <Link
                key={category.slug}
                to={`/shop?category=${category.slug}`}
                className="group relative overflow-hidden rounded-xl border-2 border-black shadow-brutal hover:shadow-brutal-lg transition-all hover:-translate-y-1 animate-fade-in"
                style={{ animationDelay: `${index * 100}ms` }}
                data-testid={`category-${category.slug}`}
              >
                <div className="aspect-[3/4] bg-muted">
                  <img
                    src={category.image}
                    alt={category.name}
                    className="w-full h-full object-contain transition-transform duration-500 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
                  <div className="absolute bottom-0 left-0 right-0 p-4">
                    <h3 className="font-heading text-xl font-bold text-white">{category.name}</h3>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Products */}
      <section className="py-20 bg-muted">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-end mb-12">
            <div>
              <h2 className="font-heading text-3xl md:text-5xl font-bold mb-4">Featured Products</h2>
              <p className="text-muted-foreground text-lg">Our most loved designs</p>
            </div>
            <Button asChild variant="outline" className="border-2 border-black shadow-brutal hover-lift">
              <Link to="/shop">View All</Link>
            </Button>
          </div>
          
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="bg-white border-2 border-black rounded-xl overflow-hidden shadow-brutal">
                  <div className="aspect-square bg-muted animate-pulse" />
                  <div className="p-4 space-y-2">
                    <div className="h-4 bg-muted animate-pulse rounded" />
                    <div className="h-6 bg-muted animate-pulse rounded w-3/4" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {featuredProducts.map((product, index) => (
                <div key={product.product_id} className="animate-fade-in" style={{ animationDelay: `${index * 100}ms` }}>
                  <ProductCard product={product} />
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20 bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="font-heading text-3xl md:text-5xl font-bold mb-4">What Our Customers Say</h2>
            <p className="text-muted-foreground text-lg">Spreading faith one thread at a time</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { name: 'Sarah M.', text: 'The quality is amazing! I get compliments on my Faith Over Fear tee everywhere I go.', rating: 5 },
              { name: 'James L.', text: 'Fast shipping and the hoodie is so comfortable. Perfect for spreading the message!', rating: 5 },
              { name: 'Grace K.', text: 'Love supporting a faith-based business. The mug is my daily reminder to stay blessed.', rating: 5 },
            ].map((testimonial, index) => (
              <div
                key={index}
                className="bg-white border-2 border-black rounded-xl p-6 shadow-brutal testimonial-card animate-fade-in"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="flex gap-1 mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <Star key={i} className="h-5 w-5 fill-primary text-primary" />
                  ))}
                </div>
                <p className="text-foreground mb-4">{testimonial.text}</p>
                <p className="font-heading font-bold text-primary">{testimonial.name}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-primary text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="font-heading text-3xl md:text-5xl font-bold mb-6">
            Ready to Wear Your Faith?
          </h2>
          <p className="text-xl mb-8 opacity-90 max-w-2xl mx-auto">
            Join thousands of believers who proudly display their faith through quality Christian apparel.
          </p>
          <Button
            asChild
            className="bg-white text-primary border-2 border-black shadow-brutal hover-lift h-12 px-8 text-lg"
          >
            <Link to="/shop">Browse Collection</Link>
          </Button>
        </div>
      </section>
    </div>
  );
};

export default HomePage;

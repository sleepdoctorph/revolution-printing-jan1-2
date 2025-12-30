import React from 'react';
import { Link } from 'react-router-dom';
import { Heart, Users, Target, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/button';

const AboutPage = () => {
  return (
    <div className="min-h-screen bg-background" data-testid="about-page">
      {/* Hero */}
      <section className="py-20 lg:py-32 bg-foreground text-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <span className="inline-block bg-primary/10 text-primary font-medium px-4 py-2 rounded-full text-sm mb-6">
              Our Story
            </span>
            <h1 className="font-heading text-5xl md:text-7xl font-extrabold tracking-tight leading-none mb-6">
              Faith Woven Into Every Thread
            </h1>
            <p className="text-xl text-muted-foreground">
              We believe that what you wear is an extension of who you are. That's why we created Faithful Threads - to help believers express their faith boldly through quality apparel.
            </p>
          </div>
        </div>
      </section>

      {/* Mission */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <img
                src="https://images.unsplash.com/photo-1712701083828-f692860260c0?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwxfHxoYXBweSUyMGRpdmVyc2UlMjBmcmllbmRzJTIwbGF1Z2hpbmclMjBvdXRkb29ycyUyMHN1bnNldHxlbnwwfHx8fDE3NjcxMjc2ODV8MA&ixlib=rb-4.1.0&q=85"
                alt="Community"
                className="rounded-xl border-2 border-black shadow-brutal-lg w-full h-96 object-cover"
              />
            </div>
            <div>
              <h2 className="font-heading text-3xl md:text-5xl font-bold mb-6">Our Mission</h2>
              <p className="text-lg text-muted-foreground mb-6">
                Faithful Threads was born from a simple idea: fashion can be a powerful tool for spreading faith. Every t-shirt, hoodie, hat, and mug we create is designed with purpose - to spark conversations, inspire hope, and remind wearers and onlookers alike of God's love.
              </p>
              <p className="text-lg text-muted-foreground">
                We're committed to using premium materials and ethical manufacturing practices, ensuring that our products are as righteous as the message they carry.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-20 bg-muted">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="font-heading text-3xl md:text-5xl font-bold mb-4">Our Values</h2>
            <p className="text-muted-foreground text-lg">What guides everything we do</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white border-2 border-black rounded-xl p-8 shadow-brutal text-center">
              <Heart className="h-12 w-12 text-secondary mx-auto mb-4" />
              <h3 className="font-heading text-xl font-bold mb-2">Faith First</h3>
              <p className="text-muted-foreground">
                Every design starts with prayer and purpose. We create apparel that glorifies God and encourages fellow believers.
              </p>
            </div>
            <div className="bg-white border-2 border-black rounded-xl p-8 shadow-brutal text-center">
              <Target className="h-12 w-12 text-primary mx-auto mb-4" />
              <h3 className="font-heading text-xl font-bold mb-2">Quality Always</h3>
              <p className="text-muted-foreground">
                We never compromise on quality. Our products are made to last, just like the message of faith they carry.
              </p>
            </div>
            <div className="bg-white border-2 border-black rounded-xl p-8 shadow-brutal text-center">
              <Users className="h-12 w-12 text-accent mx-auto mb-4" />
              <h3 className="font-heading text-xl font-bold mb-2">Community Driven</h3>
              <p className="text-muted-foreground">
                We're building more than a brand - we're building a community of believers who wear their faith proudly.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-20 bg-primary text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <p className="font-heading text-5xl font-bold mb-2">10K+</p>
              <p className="text-white/80">Happy Customers</p>
            </div>
            <div>
              <p className="font-heading text-5xl font-bold mb-2">50+</p>
              <p className="text-white/80">Unique Designs</p>
            </div>
            <div>
              <p className="font-heading text-5xl font-bold mb-2">4.9</p>
              <p className="text-white/80">Average Rating</p>
            </div>
            <div>
              <p className="font-heading text-5xl font-bold mb-2">100%</p>
              <p className="text-white/80">Faith-Driven</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="font-heading text-3xl md:text-5xl font-bold mb-6">
            Ready to Wear Your Faith?
          </h2>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Join our community of believers and start expressing your faith through quality Christian apparel.
          </p>
          <Button
            asChild
            className="bg-primary text-white border-2 border-black shadow-brutal hover-lift h-12 px-8 text-lg"
          >
            <Link to="/shop">
              Shop Now
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
          </Button>
        </div>
      </section>
    </div>
  );
};

export default AboutPage;

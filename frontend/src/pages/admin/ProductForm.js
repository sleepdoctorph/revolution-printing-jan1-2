import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ChevronLeft, Loader2, Plus, X } from 'lucide-react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const ProductForm = () => {
  const navigate = useNavigate();
  const { productId } = useParams();
  const isEditing = !!productId;

  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(isEditing);
  const [form, setForm] = useState({
    name: '',
    description: '',
    price: '',
    category: 'tshirts',
    images: [''],
    colors: [''],
    sizes: [''],
    brand: '',
    is_blank: false,
    stock: '',
    featured: false
  });

  useEffect(() => {
    if (isEditing) {
      const fetchProduct = async () => {
        try {
          const response = await axios.get(`${API_URL}/api/products/${productId}`);
          const product = response.data;
          setForm({
            name: product.name,
            description: product.description,
            price: product.price.toString(),
            category: product.category,
            images: product.images.length > 0 ? product.images : [''],
            colors: product.colors.length > 0 ? product.colors : [''],
            sizes: product.sizes.length > 0 ? product.sizes : [''],
            brand: product.brand,
            is_blank: product.is_blank,
            stock: product.stock.toString(),
            featured: product.featured
          });
        } catch (error) {
          toast.error('Failed to load product');
          navigate('/admin/products');
        } finally {
          setFetching(false);
        }
      };
      fetchProduct();
    }
  }, [productId, isEditing, navigate]);

  const handleArrayChange = (field, index, value) => {
    const newArray = [...form[field]];
    newArray[index] = value;
    setForm({ ...form, [field]: newArray });
  };

  const addArrayItem = (field) => {
    setForm({ ...form, [field]: [...form[field], ''] });
  };

  const removeArrayItem = (field, index) => {
    if (form[field].length > 1) {
      const newArray = form[field].filter((_, i) => i !== index);
      setForm({ ...form, [field]: newArray });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const productData = {
      ...form,
      price: parseFloat(form.price),
      stock: parseInt(form.stock),
      images: form.images.filter(Boolean),
      colors: form.colors.filter(Boolean),
      sizes: form.sizes.filter(Boolean)
    };

    try {
      if (isEditing) {
        await axios.put(`${API_URL}/api/admin/products/${productId}`, productData, { withCredentials: true });
        toast.success('Product updated successfully');
      } else {
        await axios.post(`${API_URL}/api/admin/products`, productData, { withCredentials: true });
        toast.success('Product created successfully');
      }
      navigate('/admin/products');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save product');
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div data-testid="product-form">
      <Button
        variant="ghost"
        onClick={() => navigate('/admin/products')}
        className="mb-6"
      >
        <ChevronLeft className="h-5 w-5 mr-1" />
        Back to Products
      </Button>

      <div className="mb-8">
        <h1 className="font-heading text-3xl font-bold mb-2">
          {isEditing ? 'Edit Product' : 'Add New Product'}
        </h1>
        <p className="text-muted-foreground">
          {isEditing ? 'Update product information' : 'Add a new product to your catalog'}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
          <h2 className="font-heading text-xl font-bold mb-6">Basic Information</h2>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="name">Product Name</Label>
              <Input
                id="name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="border-2 border-black"
                required
                data-testid="product-name-input"
              />
            </div>

            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                className="border-2 border-black min-h-[100px]"
                required
                data-testid="product-description-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="price">Price ($)</Label>
              <Input
                id="price"
                type="number"
                step="0.01"
                min="0"
                value={form.price}
                onChange={(e) => setForm({ ...form, price: e.target.value })}
                className="border-2 border-black"
                required
                data-testid="product-price-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
                <SelectTrigger className="border-2 border-black" data-testid="product-category-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="tshirts">T-Shirts</SelectItem>
                  <SelectItem value="hoodies">Hoodies</SelectItem>
                  <SelectItem value="hats">Hats</SelectItem>
                  <SelectItem value="mugs">Mugs</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="brand">Brand</Label>
              <Input
                id="brand"
                value={form.brand}
                onChange={(e) => setForm({ ...form, brand: e.target.value })}
                className="border-2 border-black"
                data-testid="product-brand-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="stock">Stock</Label>
              <Input
                id="stock"
                type="number"
                min="0"
                value={form.stock}
                onChange={(e) => setForm({ ...form, stock: e.target.value })}
                className="border-2 border-black"
                required
                data-testid="product-stock-input"
              />
            </div>

            <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
              <div>
                <Label htmlFor="is_blank">Blank Product</Label>
                <p className="text-sm text-muted-foreground">This is a blank for customization</p>
              </div>
              <Switch
                id="is_blank"
                checked={form.is_blank}
                onCheckedChange={(v) => setForm({ ...form, is_blank: v })}
                data-testid="product-blank-switch"
              />
            </div>

            <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
              <div>
                <Label htmlFor="featured">Featured Product</Label>
                <p className="text-sm text-muted-foreground">Show on homepage</p>
              </div>
              <Switch
                id="featured"
                checked={form.featured}
                onCheckedChange={(v) => setForm({ ...form, featured: v })}
                data-testid="product-featured-switch"
              />
            </div>
          </div>
        </div>

        {/* Images */}
        <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
          <h2 className="font-heading text-xl font-bold mb-6">Images</h2>
          <div className="space-y-3">
            {form.images.map((image, index) => (
              <div key={index} className="flex gap-2">
                <Input
                  value={image}
                  onChange={(e) => handleArrayChange('images', index, e.target.value)}
                  placeholder="Image URL"
                  className="border-2 border-black"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => removeArrayItem('images', index)}
                  disabled={form.images.length === 1}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
            <Button type="button" variant="outline" onClick={() => addArrayItem('images')} className="border-2 border-black">
              <Plus className="h-4 w-4 mr-2" />
              Add Image
            </Button>
          </div>
        </div>

        {/* Colors & Sizes */}
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
            <h2 className="font-heading text-xl font-bold mb-6">Colors</h2>
            <div className="space-y-3">
              {form.colors.map((color, index) => (
                <div key={index} className="flex gap-2">
                  <Input
                    value={color}
                    onChange={(e) => handleArrayChange('colors', index, e.target.value)}
                    placeholder="Color name"
                    className="border-2 border-black"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => removeArrayItem('colors', index)}
                    disabled={form.colors.length === 1}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              <Button type="button" variant="outline" onClick={() => addArrayItem('colors')} className="border-2 border-black">
                <Plus className="h-4 w-4 mr-2" />
                Add Color
              </Button>
            </div>
          </div>

          <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
            <h2 className="font-heading text-xl font-bold mb-6">Sizes</h2>
            <div className="space-y-3">
              {form.sizes.map((size, index) => (
                <div key={index} className="flex gap-2">
                  <Input
                    value={size}
                    onChange={(e) => handleArrayChange('sizes', index, e.target.value)}
                    placeholder="Size"
                    className="border-2 border-black"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => removeArrayItem('sizes', index)}
                    disabled={form.sizes.length === 1}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              <Button type="button" variant="outline" onClick={() => addArrayItem('sizes')} className="border-2 border-black">
                <Plus className="h-4 w-4 mr-2" />
                Add Size
              </Button>
            </div>
          </div>
        </div>

        <div className="flex gap-4">
          <Button
            type="submit"
            disabled={loading}
            className="bg-primary text-white border-2 border-black shadow-brutal hover-lift px-8"
            data-testid="save-product-btn"
          >
            {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : (isEditing ? 'Update Product' : 'Create Product')}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/products')}
            className="border-2 border-black"
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
};

export default ProductForm;

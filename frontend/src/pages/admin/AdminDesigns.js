import React, { useState, useEffect, useCallback } from 'react';
import { Plus, Trash2, Upload, Palette, Image as ImageIcon } from 'lucide-react';
import axios from 'axios';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { toast } from 'sonner';
import { useAuth } from '../../context/AuthContext';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Create axios instance with credentials for cookie-based auth
const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: true
});

// Helper to get token and build headers
const getAuthHeaders = () => {
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
};

const AdminDesigns = () => {
  const { user } = useAuth();
  const [designs, setDesigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [uploading, setUploading] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    category: 'apparel',
    image_url: ''
  });

  const fetchDesigns = useCallback(async () => {
    try {
      const response = await apiClient.get('/api/admin/designs', {
        headers: getAuthHeaders()
      });
      setDesigns(response.data);
    } catch (error) {
      console.error('Error fetching designs:', error);
      toast.error('Failed to load designs');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDesigns();
  }, [fetchDesigns]);

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Invalid file type. Only JPEG, PNG, WebP, GIF allowed.');
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File too large. Maximum size is 10MB.');
      return;
    }

    setUploading(true);
    const uploadFormData = new FormData();
    uploadFormData.append('file', file);

    try {
      const response = await apiClient.post('/api/admin/designs/upload', uploadFormData, {
        headers: getAuthHeaders()
      });
      setFormData(prev => ({ ...prev, image_url: response.data.url }));
      toast.success('Image uploaded successfully');
    } catch (error) {
      console.error('Upload error:', error.response?.data || error);
      const errorMsg = error.response?.data?.detail || 'Failed to upload image';
      toast.error(errorMsg);
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      toast.error('Please enter a design name');
      return;
    }
    if (!formData.image_url) {
      toast.error('Please upload a design image');
      return;
    }

    try {
      await apiClient.post('/api/admin/designs', formData, {
        headers: getAuthHeaders()
      });
      toast.success('Design created successfully');
      setFormData({ name: '', category: 'apparel', image_url: '' });
      setShowForm(false);
      fetchDesigns();
    } catch (error) {
      console.error('Error creating design:', error);
      toast.error('Failed to create design');
    }
  };

  const handleDelete = async (designId) => {
    if (!window.confirm('Are you sure you want to delete this design?')) return;

    try {
      await apiClient.delete(`/api/admin/designs/${designId}`, {
        headers: getAuthHeaders()
      });
      toast.success('Design deleted successfully');
      fetchDesigns();
    } catch (error) {
      console.error('Error deleting design:', error);
      toast.error('Failed to delete design');
    }
  };

  const apparelDesigns = designs.filter(d => d.category === 'apparel');
  const hatDesigns = designs.filter(d => d.category === 'hats');

  return (
    <div className="space-y-6" data-testid="admin-designs-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-3xl font-bold">Designs</h1>
          <p className="text-muted-foreground">
            Manage designs that customers can apply to products
          </p>
        </div>
        <Button
          onClick={() => setShowForm(!showForm)}
          className="bg-primary text-white border-2 border-black shadow-brutal hover-lift"
          data-testid="add-design-button"
        >
          <Plus className="h-5 w-5 mr-2" />
          Add Design
        </Button>
      </div>

      {/* Add Design Form */}
      {showForm && (
        <div className="bg-card border-2 border-black rounded-xl p-6 shadow-brutal">
          <h2 className="font-heading text-xl font-bold mb-4">Add New Design</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Design Name</label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., Faith Over Fear Cross"
                className="border-2 border-black"
                data-testid="design-name-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Category</label>
              <Select
                value={formData.category}
                onValueChange={(value) => setFormData(prev => ({ ...prev, category: value }))}
              >
                <SelectTrigger className="border-2 border-black" data-testid="design-category-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="apparel">Apparel (T-Shirts, Hoodies, Mugs)</SelectItem>
                  <SelectItem value="hats">Hats Only</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground mt-1">
                Apparel designs work for T-shirts, Hoodies, and Mugs. Hat designs are separate.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Design Image</label>
              <div className="flex items-center gap-4">
                {formData.image_url ? (
                  <div className="relative w-32 h-32 border-2 border-black rounded-lg overflow-hidden bg-white">
                    <img
                      src={formData.image_url.startsWith('/') ? `${API_URL}${formData.image_url}` : formData.image_url}
                      alt="Design preview"
                      className="w-full h-full object-contain p-2"
                    />
                    <button
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, image_url: '' }))}
                      className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                ) : (
                  <label className="flex flex-col items-center justify-center w-32 h-32 border-2 border-dashed border-black rounded-lg cursor-pointer hover:bg-muted/50 transition-colors">
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageUpload}
                      className="hidden"
                      disabled={uploading}
                    />
                    {uploading ? (
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
                    ) : (
                      <>
                        <Upload className="h-8 w-8 text-muted-foreground mb-2" />
                        <span className="text-xs text-muted-foreground">Upload Image</span>
                      </>
                    )}
                  </label>
                )}
                <div className="text-sm text-muted-foreground">
                  <p>Upload a PNG or JPG image.</p>
                  <p>Transparent PNG recommended for best results.</p>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <Button
                type="submit"
                className="bg-primary text-white border-2 border-black shadow-brutal"
                disabled={uploading}
                data-testid="save-design-button"
              >
                Save Design
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowForm(false);
                  setFormData({ name: '', category: 'apparel', image_url: '' });
                }}
                className="border-2 border-black"
              >
                Cancel
              </Button>
            </div>
          </form>
        </div>
      )}

      {/* Designs Grid */}
      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="aspect-square bg-muted animate-pulse rounded-xl" />
          ))}
        </div>
      ) : designs.length === 0 ? (
        <div className="text-center py-16 bg-card border-2 border-dashed border-muted rounded-xl">
          <Palette className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
          <h3 className="font-heading text-xl font-bold mb-2">No Designs Yet</h3>
          <p className="text-muted-foreground mb-4">
            Upload your first design to get started
          </p>
          <Button
            onClick={() => setShowForm(true)}
            className="bg-primary text-white border-2 border-black shadow-brutal"
          >
            <Plus className="h-5 w-5 mr-2" />
            Add Your First Design
          </Button>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Apparel Designs */}
          <div>
            <h2 className="font-heading text-xl font-bold mb-4 flex items-center gap-2">
              <ImageIcon className="h-5 w-5" />
              Apparel Designs ({apparelDesigns.length})
              <span className="text-sm font-normal text-muted-foreground">
                (T-Shirts, Hoodies, Mugs)
              </span>
            </h2>
            {apparelDesigns.length === 0 ? (
              <p className="text-muted-foreground text-sm">No apparel designs yet</p>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {apparelDesigns.map((design) => (
                  <div
                    key={design.design_id}
                    className="relative aspect-square border-2 border-black rounded-xl overflow-hidden bg-white shadow-brutal group"
                  >
                    {design.image_url ? (
                      <img
                        src={design.image_url.startsWith('/') ? `${API_URL}${design.image_url}` : design.image_url}
                        alt={design.name}
                        className="w-full h-full object-contain p-2"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-muted">
                        <Palette className="h-12 w-12 text-muted-foreground" />
                      </div>
                    )}
                    
                    {/* Overlay with name and delete */}
                    <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center p-2">
                      <p className="text-white font-bold text-sm text-center mb-2 truncate w-full">
                        {design.name}
                      </p>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDelete(design.design_id)}
                        className="bg-red-500 hover:bg-red-600"
                        data-testid={`delete-design-${design.design_id}`}
                      >
                        <Trash2 className="h-4 w-4 mr-1" />
                        Delete
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Hat Designs */}
          <div>
            <h2 className="font-heading text-xl font-bold mb-4 flex items-center gap-2">
              <ImageIcon className="h-5 w-5" />
              Hat Designs ({hatDesigns.length})
              <span className="text-sm font-normal text-muted-foreground">
                (Hats Only)
              </span>
            </h2>
            {hatDesigns.length === 0 ? (
              <p className="text-muted-foreground text-sm">No hat designs yet</p>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {hatDesigns.map((design) => (
                  <div
                    key={design.design_id}
                    className="relative aspect-square border-2 border-black rounded-xl overflow-hidden bg-white shadow-brutal group"
                  >
                    {design.image_url ? (
                      <img
                        src={design.image_url.startsWith('/') ? `${API_URL}${design.image_url}` : design.image_url}
                        alt={design.name}
                        className="w-full h-full object-contain p-2"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-muted">
                        <Palette className="h-12 w-12 text-muted-foreground" />
                      </div>
                    )}
                    
                    {/* Overlay with name and delete */}
                    <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center p-2">
                      <p className="text-white font-bold text-sm text-center mb-2 truncate w-full">
                        {design.name}
                      </p>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDelete(design.design_id)}
                        className="bg-red-500 hover:bg-red-600"
                        data-testid={`delete-design-${design.design_id}`}
                      >
                        <Trash2 className="h-4 w-4 mr-1" />
                        Delete
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDesigns;

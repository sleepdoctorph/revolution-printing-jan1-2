import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Helper to get token from either storage
  const getStoredToken = () => {
    return localStorage.getItem('token') || sessionStorage.getItem('token');
  };

  const checkAuth = useCallback(async () => {
    try {
      // First try to use stored token for Bearer auth
      const storedToken = getStoredToken();
      const headers = storedToken ? { Authorization: `Bearer ${storedToken}` } : {};
      
      const response = await axios.get(`${API_URL}/api/auth/me`, {
        withCredentials: true,
        headers
      });
      setUser(response.data);
    } catch (error) {
      setUser(null);
      // Clear invalid tokens
      localStorage.removeItem('token');
      sessionStorage.removeItem('token');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async (email, password, rememberMe = true) => {
    const response = await axios.post(`${API_URL}/api/auth/login`, 
      { email, password },
      { withCredentials: true }
    );
    // Store token based on remember me preference
    if (response.data.access_token) {
      // Clear both storages first
      localStorage.removeItem('token');
      sessionStorage.removeItem('token');
      
      if (rememberMe) {
        // Persistent storage - survives browser close
        localStorage.setItem('token', response.data.access_token);
      } else {
        // Session storage - cleared when browser closes
        sessionStorage.setItem('token', response.data.access_token);
      }
    }
    setUser(response.data.user);
    return response.data;
  };

  const register = async (email, password, name) => {
    const response = await axios.post(`${API_URL}/api/auth/register`,
      { email, password, name },
      { withCredentials: true }
    );
    // Store token in localStorage for admin pages that use Bearer auth
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
    }
    setUser(response.data.user);
    return response.data;
  };

  const loginWithGoogle = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + '/auth/callback';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const handleGoogleCallback = async (sessionId) => {
    const response = await axios.get(`${API_URL}/api/auth/session`, {
      headers: { 'X-Session-ID': sessionId },
      withCredentials: true
    });
    
    // Store the session token for Bearer auth (used by admin pages)
    if (response.data.session_token) {
      localStorage.setItem('token', response.data.session_token);
    }
    
    setUser(response.data);
    return response.data;
  };

  const logout = async () => {
    try {
      await axios.post(`${API_URL}/api/auth/logout`, {}, { withCredentials: true });
    } catch (error) {
      console.error('Logout error:', error);
    }
    // Clear token from both storages
    localStorage.removeItem('token');
    sessionStorage.removeItem('token');
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    loginWithGoogle,
    handleGoogleCallback,
    checkAuth,
    isAuthenticated: !!user,
    isAdmin: user?.is_admin || false
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

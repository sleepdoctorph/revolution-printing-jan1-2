import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

const AuthCallbackPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { handleGoogleCallback } = useAuth();
  const hasProcessed = useRef(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Prevent double processing in StrictMode
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processCallback = async () => {
      try {
        // Extract session_id from URL fragment
        const hash = location.hash;
        const sessionIdMatch = hash.match(/session_id=([^&]+)/);
        
        if (!sessionIdMatch) {
          setError('No session ID found');
          setTimeout(() => navigate('/login'), 2000);
          return;
        }

        const sessionId = sessionIdMatch[1];
        
        // Exchange session_id for user data
        const user = await handleGoogleCallback(sessionId);
        
        toast.success(`Welcome, ${user.name}!`);
        navigate('/', { replace: true, state: { user } });
      } catch (error) {
        console.error('Auth callback error:', error);
        setError('Authentication failed');
        toast.error('Failed to complete login');
        setTimeout(() => navigate('/login'), 2000);
      }
    };

    processCallback();
  }, [location.hash, handleGoogleCallback, navigate]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center" data-testid="auth-callback-page">
      <div className="text-center">
        {error ? (
          <>
            <p className="text-destructive text-lg mb-2">{error}</p>
            <p className="text-muted-foreground">Redirecting to login...</p>
          </>
        ) : (
          <>
            <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
            <p className="text-lg font-medium">Completing sign in...</p>
            <p className="text-muted-foreground">Please wait</p>
          </>
        )}
      </div>
    </div>
  );
};

export default AuthCallbackPage;

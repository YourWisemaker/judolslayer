'use client';

import { useState, useEffect } from 'react';
import { UserIcon, ArrowRightOnRectangleIcon, ArrowLeftOnRectangleIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface User {
  channel_id: string;
  channel_title: string;
  thumbnail_url?: string;
  authenticated: boolean;
}

interface AuthStatusProps {
  onAuthChange?: (authenticated: boolean) => void;
}

export function AuthStatus({ onAuthChange }: AuthStatusProps) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [loggingIn, setLoggingIn] = useState(false);

  const checkAuthStatus = async () => {
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';
      const response = await fetch(`${API_BASE_URL}/api/auth/status`, {
        credentials: 'include'
      });
      const data = await response.json();
      
      if (data.authenticated && data.user) {
        setUser(data.user);
        onAuthChange?.(true);
      } else {
        setUser(null);
        onAuthChange?.(false);
      }
    } catch (error) {
      console.error('Auth status check failed:', error);
      setUser(null);
      onAuthChange?.(false);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    try {
      setLoggingIn(true);
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';
      const response = await fetch(`${API_BASE_URL}/api/auth/login`);
      const data = await response.json();
      
      if (data.auth_url) {
        // Open OAuth URL in a popup window
        const popup = window.open(
          data.auth_url,
          'oauth',
          'width=500,height=600,scrollbars=yes,resizable=yes'
        );
        
        // Listen for popup close or success
        const checkClosed = setInterval(() => {
          try {
            if (popup?.closed) {
              clearInterval(checkClosed);
              setLoggingIn(false);
              // Check auth status after popup closes
              setTimeout(checkAuthStatus, 1000);
            }
          } catch (error) {
            // Handle Cross-Origin-Opener-Policy errors
            console.warn('Unable to check popup status due to CORS policy:', error);
            // Fallback: assume popup might be closed after a reasonable time
            clearInterval(checkClosed);
            setLoggingIn(false);
            setTimeout(checkAuthStatus, 2000);
          }
        }, 1000);
        
        // Listen for auth success message
        const messageListener = (event: MessageEvent) => {
          if (event.origin !== window.location.origin) return;
          
          if (event.data.type === 'AUTH_SUCCESS') {
            popup?.close();
            clearInterval(checkClosed);
            clearTimeout(popupTimeout);
            setLoggingIn(false);
            checkAuthStatus();
            toast.success('Successfully authenticated!');
            window.removeEventListener('message', messageListener);
          } else if (event.data.type === 'AUTH_ERROR') {
            popup?.close();
            clearInterval(checkClosed);
            clearTimeout(popupTimeout);
            setLoggingIn(false);
            toast.error('Authentication failed');
            window.removeEventListener('message', messageListener);
          }
        };
        
        window.addEventListener('message', messageListener);
        
        // Add timeout fallback (30 seconds)
        const popupTimeout = setTimeout(() => {
          clearInterval(checkClosed);
          window.removeEventListener('message', messageListener);
          setLoggingIn(false);
          if (popup && !popup.closed) {
            popup.close();
          }
          toast.error('Authentication timed out. Please try again.');
        }, 30000);
      } else {
        toast.error('Failed to initiate authentication');
        setLoggingIn(false);
      }
    } catch (error) {
      console.error('Login failed:', error);
      toast.error('Login failed');
      setLoggingIn(false);
    }
  };

  const handleLogout = async () => {
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';
      const response = await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      });
      
      if (response.ok) {
        setUser(null);
        onAuthChange?.(false);
        toast.success('Logged out successfully');
      } else {
        toast.error('Logout failed');
      }
    } catch (error) {
      console.error('Logout failed:', error);
      toast.error('Logout failed');
    }
  };

  useEffect(() => {
    checkAuthStatus();
    
    // Check for auth success/error in URL params (from OAuth redirect)
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('auth_success')) {
      toast.success('Successfully authenticated!');
      checkAuthStatus();
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (urlParams.get('auth_error')) {
      toast.error('Authentication failed');
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  if (loading) {
    return (
      <div className="flex items-center space-x-2 text-gray-500">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-500"></div>
        <span className="text-sm">Checking auth...</span>
      </div>
    );
  }

  if (user) {
    return (
      <div className="flex items-center space-x-3 p-3 bg-green-50 border border-green-200 rounded-lg">
        <div className="flex items-center space-x-2 flex-1">
          {user.thumbnail_url ? (
            <img 
              src={user.thumbnail_url} 
              alt={user.channel_title}
              className="w-8 h-8 rounded-full"
            />
          ) : (
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              <UserIcon className="w-5 h-5 text-green-600" />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-green-900 truncate">
              {user.channel_title}
            </p>
            <p className="text-xs text-green-600">Authenticated for deletion</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center space-x-1 px-3 py-1 text-sm text-green-700 hover:text-green-900 hover:bg-green-100 rounded transition-colors"
        >
          <ArrowLeftOnRectangleIcon className="w-4 h-4" />
          <span>Logout</span>
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
      <div className="flex items-center space-x-2 flex-1">
        <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
          <UserIcon className="w-5 h-5 text-yellow-600" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-yellow-900">
            Not authenticated
          </p>
          <p className="text-xs text-yellow-600">
            Login required for comment deletion
          </p>
        </div>
      </div>
      <button
        onClick={handleLogin}
        disabled={loggingIn}
        className="flex items-center space-x-1 px-3 py-1 text-sm bg-yellow-600 text-white hover:bg-yellow-700 disabled:bg-yellow-400 rounded transition-colors"
      >
        {loggingIn ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            <span>Logging in...</span>
          </>
        ) : (
          <>
            <ArrowRightOnRectangleIcon className="w-4 h-4" />
            <span>Login</span>
          </>
        )}
      </button>
    </div>
  );
}
'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { createClient } from '@supabase/supabase-js';

interface AuthContextType {
  user: any | null;
  isLoading: boolean;
  signOut: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state from Supabase
  const initializeAuth = useCallback(async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      setUser(session?.user || null);
    } catch (error) {
      console.error('Auth init error:', error);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Refresh session from Supabase
  const refreshSession = useCallback(async () => {
    try {
      const { data: { session } } = await supabase.auth.refreshSession();
      setUser(session?.user || null);
      return session;
    } catch (error) {
      console.error('Session refresh error:', error);
      setUser(null);
      return null;
    }
  }, []);

  // Sign out with proper cleanup
  const signOut = useCallback(async () => {
    try {
      // 1. Clear local state immediately
      setUser(null);
      
      // 2. Sign out from Supabase (clears tokens)
      await supabase.auth.signOut();
      
      // 3. Clear all auth-related storage
      localStorage.removeItem('supabase.auth.token');
      localStorage.removeItem('supabase.auth.refreshToken');
      sessionStorage.clear();
      
      // 4. Broadcast to all tabs
      broadcastAuthChange({ type: 'SIGN_OUT', user: null });
      
      // 5. Redirect to login
      window.location.href = '/login';
    } catch (error) {
      console.error('Sign out error:', error);
      // Force redirect even if error
      window.location.href = '/login';
    }
  }, []);

  // Broadcast auth changes to other tabs
  const broadcastAuthChange = (message: any) => {
    const channel = new BroadcastChannel('auth-channel');
    channel.postMessage(message);
    channel.close();
  };

  // Listen for auth changes from Supabase
  useEffect(() => {
    initializeAuth();

    // Subscribe to auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('Auth state changed:', event);
        
        if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
          setUser(session?.user || null);
          broadcastAuthChange({ type: 'SIGN_IN', user: session?.user });
        } else if (event === 'SIGNED_OUT') {
          setUser(null);
          broadcastAuthChange({ type: 'SIGN_OUT', user: null });
        }
      }
    );

    return () => {
      subscription?.unsubscribe();
    };
  }, [initializeAuth]);

  // Listen for auth changes from other tabs
  useEffect(() => {
    const channel = new BroadcastChannel('auth-channel');
    
    const handleMessage = (event: MessageEvent) => {
      console.log('Auth message from other tab:', event.data);
      
      if (event.data.type === 'SIGN_OUT') {
        setUser(null);
        // Redirect to login
        window.location.href = '/login';
      } else if (event.data.type === 'SIGN_IN') {
        setUser(event.data.user);
      }
    };

    channel.addEventListener('message', handleMessage);
    return () => {
      channel.removeEventListener('message', handleMessage);
      channel.close();
    };
  }, []);

  // Refresh session periodically (every 5 minutes)
  useEffect(() => {
    const interval = setInterval(() => {
      if (user) {
        refreshSession();
      }
    }, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [user, refreshSession]);

  return (
    <AuthContext.Provider value={{ user, isLoading, signOut, refreshSession }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

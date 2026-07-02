import { useEffect, useCallback, useRef } from 'react';
import { createClient } from '@supabase/supabase-js';

/**
 * Hook for syncing auth state across browser tabs
 * Handles:
 * - Cross-tab session synchronization
 * - Automatic sign-out propagation
 * - Token refresh coordination
 */
export function useAuthSync() {
  const supabaseRef = useRef(
    createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    )
  );

  // Listen for storage changes (works across tabs)
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      // Supabase stores auth in localStorage with these keys
      if (
        e.key?.includes('supabase') ||
        e.key?.includes('auth') ||
        e.key === null // null key means storage was cleared
      ) {
        console.log('Auth storage changed in another tab');
        
        // Refresh session to sync state
        supabaseRef.current.auth.refreshSession().catch((err) => {
          console.error('Failed to refresh session:', err);
          // If refresh fails, user is likely logged out
          window.location.href = '/login';
        });
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  // Listen for visibility changes (tab becomes active)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        console.log('Tab became visible, syncing auth state');
        
        // Refresh session when tab becomes visible
        supabaseRef.current.auth.refreshSession().catch((err) => {
          console.error('Failed to refresh session on visibility:', err);
        });
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, []);

  // Broadcast channel for real-time cross-tab communication
  useEffect(() => {
    const channel = new BroadcastChannel('supabase-auth');

    const handleMessage = (event: MessageEvent) => {
      const { type, data } = event.data;

      switch (type) {
        case 'SIGN_OUT':
          console.log('Sign out broadcast received');
          // Clear local auth state
          localStorage.removeItem('supabase.auth.token');
          localStorage.removeItem('supabase.auth.refreshToken');
          sessionStorage.clear();
          // Redirect to login
          window.location.href = '/login';
          break;

        case 'SESSION_REFRESH':
          console.log('Session refresh broadcast received');
          supabaseRef.current.auth.refreshSession();
          break;

        case 'SIGN_IN':
          console.log('Sign in broadcast received');
          // Refresh to get updated session
          supabaseRef.current.auth.refreshSession();
          break;
      }
    };

    channel.addEventListener('message', handleMessage);
    return () => {
      channel.removeEventListener('message', handleMessage);
      channel.close();
    };
  }, []);
}

/**
 * Broadcast auth event to all tabs
 */
export function broadcastAuthEvent(type: 'SIGN_OUT' | 'SIGN_IN' | 'SESSION_REFRESH', data?: any) {
  try {
    const channel = new BroadcastChannel('supabase-auth');
    channel.postMessage({ type, data });
    channel.close();
  } catch (error) {
    console.error('Failed to broadcast auth event:', error);
  }
}

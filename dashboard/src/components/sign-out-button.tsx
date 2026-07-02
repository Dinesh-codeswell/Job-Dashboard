'use client';

import { useState } from 'react';
import { createClient } from '@supabase/supabase-js';
import { broadcastAuthEvent } from '@/lib/use-auth-sync';

export function SignOutButton() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSignOut = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const supabase = createClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
      );

      // 1. Sign out from Supabase (invalidates tokens on server)
      const { error: signOutError } = await supabase.auth.signOut();
      
      if (signOutError) {
        throw signOutError;
      }

      // 2. Clear all local storage
      localStorage.clear();
      sessionStorage.clear();

      // 3. Clear cookies
      document.cookie.split(';').forEach((c) => {
        document.cookie = c
          .replace(/^ +/, '')
          .replace(/=.*/, `=;expires=${new Date().toUTCString()};path=/`);
      });

      // 4. Broadcast to all tabs
      broadcastAuthEvent('SIGN_OUT');

      // 5. Redirect to login
      window.location.href = '/login';
    } catch (err) {
      console.error('Sign out error:', err);
      setError(err instanceof Error ? err.message : 'Failed to sign out');
      
      // Force redirect even on error
      setTimeout(() => {
        window.location.href = '/login';
      }, 1000);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button
      onClick={handleSignOut}
      disabled={isLoading}
      className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
    >
      {isLoading ? 'Signing out...' : 'Sign Out'}
    </button>
  );
}

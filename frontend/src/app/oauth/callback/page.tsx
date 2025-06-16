'use client';

import { useEffect } from 'react';
import { useSearchParams } from 'next/navigation';

export default function OAuthCallbackPage() {
  const searchParams = useSearchParams();

  useEffect(() => {
    const authSuccess = searchParams.get('auth_success');
    const authError = searchParams.get('auth_error');

    if (authSuccess) {
      // Notify parent window of successful authentication
      if (window.opener) {
        window.opener.postMessage(
          { type: 'AUTH_SUCCESS' },
          window.location.origin
        );
        window.close();
      } else {
        // If not in popup, redirect to main page
        window.location.href = '/?auth_success=true';
      }
    } else if (authError) {
      // Notify parent window of authentication error
      if (window.opener) {
        window.opener.postMessage(
          { type: 'AUTH_ERROR', error: authError },
          window.location.origin
        );
        window.close();
      } else {
        // If not in popup, redirect to main page with error
        window.location.href = `/?auth_error=${authError}`;
      }
    } else {
      // No auth parameters, redirect to main page
      window.location.href = '/';
    }
  }, [searchParams]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Processing Authentication
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Please wait while we complete your authentication...
          </p>
        </div>
      </div>
    </div>
  );
}
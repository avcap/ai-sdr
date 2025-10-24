import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { useSession } from 'next-auth/react';
import Head from 'next/head';

export default function GoogleCallback() {
  const router = useRouter();
  const { data: session } = useSession();
  const [status, setStatus] = useState('processing');
  const [message, setMessage] = useState('Processing Google authorization...');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const { code, state } = router.query;
        
        if (!code || !state) {
          setStatus('error');
          setMessage('Missing authorization code or state');
          return;
        }

        if (!session) {
          setStatus('error');
          setMessage('Not authenticated');
          return;
        }

        // Send the authorization code to the backend
        const response = await fetch('/api/auth/google/callback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.accessToken || 'demo_token'}`
          },
          body: JSON.stringify({
            code,
            state
          })
        });

        if (response.ok) {
          const result = await response.json();
          setStatus('success');
          setMessage(`Successfully connected Google account: ${result.google_email}`);
          
          // Redirect to dashboard after 2 seconds
          setTimeout(() => {
            router.push('/dashboard');
          }, 2000);
        } else {
          const error = await response.json();
          setStatus('error');
          setMessage(error.detail || 'Failed to connect Google account');
        }
      } catch (err) {
        console.error('Google callback error:', err);
        setStatus('error');
        setMessage('An error occurred during Google authorization');
      }
    };

    if (router.isReady && session) {
      handleCallback();
    }
  }, [router.isReady, router.query, session]);

  return (
    <>
      <Head>
        <title>Google Authorization - AI SDR</title>
      </Head>
      
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
          {status === 'processing' && (
            <>
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Processing Authorization</h2>
              <p className="text-gray-600">{message}</p>
            </>
          )}
          
          {status === 'success' && (
            <>
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Success!</h2>
              <p className="text-gray-600 mb-4">{message}</p>
              <p className="text-sm text-gray-500">Redirecting to dashboard...</p>
            </>
          )}
          
          {status === 'error' && (
            <>
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Authorization Failed</h2>
              <p className="text-gray-600 mb-4">{message}</p>
              <button
                onClick={() => router.push('/dashboard')}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Return to Dashboard
              </button>
            </>
          )}
        </div>
      </div>
    </>
  );
}

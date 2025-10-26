import { getSession } from 'next-auth/react';

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const session = await getSession({ req });
  
  // For demo purposes, use demo token if no session
  const authToken = session?.accessToken || 'demo_token';

  try {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    
    const response = await fetch(`${backendUrl}/campaign-intelligence/suggestions`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authToken}`,
      }
    });

    if (response.ok) {
      const data = await response.json();
      return res.status(200).json(data);
    } else {
      const error = await response.json();
      return res.status(response.status).json(error);
    }
  } catch (error) {
    console.error('Error fetching campaign suggestions:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}

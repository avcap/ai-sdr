import { getSession } from 'next-auth/react';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const session = await getSession({ req });
  if (!session) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  try {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    
    const response = await fetch(`${backendUrl}/campaign-intelligence/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.accessToken}`,
      },
      body: JSON.stringify(req.body),
    });

    if (response.ok) {
      const data = await response.json();
      return res.status(200).json(data);
    } else {
      const error = await response.json();
      return res.status(response.status).json(error);
    }
  } catch (error) {
    console.error('Error generating campaign suggestions:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}

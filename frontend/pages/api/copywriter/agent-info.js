const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const response = await fetch(`${BACKEND_URL}/copywriter/agent-info`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${req.headers.authorization?.replace('Bearer ', '') || 'demo_token'}`
      }
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.status(200).json(data);
  } catch (error) {
    console.error('Copywriter agent info API error:', error);
    res.status(500).json({ error: 'Failed to get agent info' });
  }
}



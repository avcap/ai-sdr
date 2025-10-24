const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const response = await fetch(`${BACKEND_URL}/copywriter/generate-variations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${req.headers.authorization?.replace('Bearer ', '') || 'demo_token'}`
      },
      body: JSON.stringify(req.body)
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.status(200).json(data);
  } catch (error) {
    console.error('Copywriter generate variations API error:', error);
    res.status(500).json({ error: 'Failed to generate message variations' });
  }
}



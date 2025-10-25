export default async function handler(req, res) {
  const { industry } = req.query;

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  if (!industry) {
    return res.status(400).json({ error: 'Industry parameter is required' });
  }

  try {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    
    const response = await fetch(`${backendUrl}/phase3/market-intelligence/${industry}`, {
      method: 'GET',
      headers: {
        'Authorization': req.headers.authorization || '',
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
    console.error('Error getting market intelligence:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}

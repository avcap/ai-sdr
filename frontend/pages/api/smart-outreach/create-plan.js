export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { leads, campaign_context } = req.body;
    const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

    if (!leads || !Array.isArray(leads)) {
      return res.status(400).json({ error: 'Leads data is required' });
    }

    const response = await fetch(`${BACKEND_URL}/smart-outreach/create-plan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${req.headers.authorization?.replace('Bearer ', '') || 'demo_token'}`
      },
      body: JSON.stringify({
        leads,
        campaign_context
      })
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.status(200).json(data);
  } catch (error) {
    console.error('Smart outreach planning error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}

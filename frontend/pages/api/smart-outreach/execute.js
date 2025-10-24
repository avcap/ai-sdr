export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { outreach_plan, user_preferences } = req.body;
    const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

    if (!outreach_plan) {
      return res.status(400).json({ error: 'Outreach plan is required' });
    }

    const response = await fetch(`${BACKEND_URL}/smart-outreach/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${req.headers.authorization?.replace('Bearer ', '') || 'demo_token'}`
      },
      body: JSON.stringify({
        outreach_plan,
        user_preferences
      })
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.status(200).json(data);
  } catch (error) {
    console.error('Smart outreach execution error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}

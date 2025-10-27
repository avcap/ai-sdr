export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { outreach_plan, campaign_id, user_preferences } = req.body;

    // Forward request to backend
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/smart-outreach/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': req.headers.authorization || 'Bearer demo_token'
      },
      body: JSON.stringify({
        outreach_plan,
        campaign_id,
        user_preferences
      })
    });

    const data = await response.json();

    if (response.ok) {
      return res.status(200).json(data);
    } else {
      return res.status(response.status).json(data);
    }
  } catch (error) {
    console.error('Smart outreach execution error:', error);
    return res.status(500).json({ error: error.message || 'Failed to execute outreach' });
  }
}

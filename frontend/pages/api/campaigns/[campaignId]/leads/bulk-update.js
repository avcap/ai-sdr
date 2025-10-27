export default async function handler(req, res) {
  const { method, query } = req;
  const { campaignId } = query;

  if (method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    
    const response = await fetch(`${backendUrl}/campaigns/${campaignId}/leads/bulk-update`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': req.headers.authorization || 'Bearer demo_token'
      },
      body: JSON.stringify(req.body)
    });

    if (response.ok) {
      const data = await response.json();
      return res.status(200).json(data);
    } else {
      const error = await response.json();
      return res.status(response.status).json(error);
    }
  } catch (error) {
    console.error('Bulk update leads API error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}


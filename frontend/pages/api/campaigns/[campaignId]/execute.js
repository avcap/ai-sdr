export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { campaignId } = req.query;

  try {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/campaigns/${campaignId}/execute`, {
      method: 'POST',
      headers: {
        'Authorization': req.headers.authorization
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
    console.error('Campaign execute API error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}

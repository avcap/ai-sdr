export default async function handler(req, res) {
  const { method } = req;

  try {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    let response;
    
    if (method === 'GET') {
      // Get all campaigns
      response = await fetch(`${backendUrl}/campaigns`, {
        headers: {
          'Authorization': req.headers.authorization
        }
      });
    } else if (method === 'POST') {
      // Create new campaign
      response = await fetch(`${backendUrl}/campaigns`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': req.headers.authorization
        },
        body: JSON.stringify(req.body)
      });
    } else {
      return res.status(405).json({ error: 'Method not allowed' });
    }

    if (response.ok) {
      const data = await response.json();
      return res.status(200).json(data);
    } else {
      const error = await response.json();
      return res.status(response.status).json(error);
    }
  } catch (error) {
    console.error('Campaigns API error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}

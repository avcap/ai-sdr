export default async function handler(req, res) {
  const { method, query } = req;
  const { campaignId } = query;

  try {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    let response;
    
    if (method === 'GET') {
      // Get single campaign
      response = await fetch(`${backendUrl}/campaigns/${campaignId}`, {
        headers: {
          'Authorization': req.headers.authorization || 'Bearer demo_token'
        }
      });
    } else if (method === 'PUT') {
      // Update campaign
      response = await fetch(`${backendUrl}/campaigns/${campaignId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': req.headers.authorization || 'Bearer demo_token'
        },
        body: JSON.stringify(req.body)
      });
    } else if (method === 'DELETE') {
      // Delete campaign
      response = await fetch(`${backendUrl}/campaigns/${campaignId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': req.headers.authorization || 'Bearer demo_token'
        }
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
    console.error('Campaign API error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}


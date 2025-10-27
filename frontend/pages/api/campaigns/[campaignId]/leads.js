export default async function handler(req, res) {
  const { method, query } = req;
  const { campaignId, status, search, page, limit } = query;

  if (method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    
    // Build query params
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (search) params.append('search', search);
    if (page) params.append('page', page);
    if (limit) params.append('limit', limit);
    
    const queryString = params.toString() ? `?${params.toString()}` : '';
    
    const response = await fetch(`${backendUrl}/campaigns/${campaignId}/leads${queryString}`, {
      headers: {
        'Authorization': req.headers.authorization || 'Bearer demo_token'
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
    console.error('Campaign leads API error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}


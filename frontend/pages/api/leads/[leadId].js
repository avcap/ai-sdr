export default async function handler(req, res) {
  const { method, query } = req;
  const { leadId } = query;

  try {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    let response;
    
    if (method === 'GET') {
      // Get single lead
      response = await fetch(`${backendUrl}/leads/${leadId}`, {
        headers: {
          'Authorization': req.headers.authorization || 'Bearer demo_token'
        }
      });
    } else if (method === 'PUT') {
      // Update lead
      response = await fetch(`${backendUrl}/leads/${leadId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': req.headers.authorization || 'Bearer demo_token'
        },
        body: JSON.stringify(req.body)
      });
    } else if (method === 'DELETE') {
      // Delete lead
      response = await fetch(`${backendUrl}/leads/${leadId}`, {
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
    console.error('Lead API error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}


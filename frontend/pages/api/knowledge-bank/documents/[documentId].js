export default async function handler(req, res) {
  const { documentId } = req.query;

  if (req.method !== 'DELETE') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  if (!documentId) {
    return res.status(400).json({ error: 'Document ID is required' });
  }

  try {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    
    const response = await fetch(`${backendUrl}/knowledge-bank/documents/${documentId}`, {
      method: 'DELETE',
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
    console.error('Delete document API error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}

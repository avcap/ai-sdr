import formidable from 'formidable';
import fs from 'fs';

export const config = {
  api: {
    bodyParser: false,
  },
};

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { campaignId } = req.query;

  try {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    
    // Parse the incoming form data
    const form = formidable();
    const [fields, files] = await form.parse(req);
    
    if (!files.file || !files.file[0]) {
      return res.status(400).json({ error: 'No file uploaded' });
    }
    
    const file = files.file[0];
    const fileBuffer = fs.readFileSync(file.filepath);
    
    // Create FormData for backend
    const formData = new FormData();
    const blob = new Blob([fileBuffer], { type: file.mimetype });
    formData.append('file', blob, file.originalFilename);

    const response = await fetch(`${backendUrl}/campaigns/${campaignId}/leads/upload`, {
      method: 'POST',
      headers: {
        'Authorization': req.headers.authorization
      },
      body: formData
    });

    if (response.ok) {
      const data = await response.json();
      return res.status(200).json(data);
    } else {
      const error = await response.json();
      return res.status(response.status).json(error);
    }
  } catch (error) {
    console.error('Lead upload API error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}

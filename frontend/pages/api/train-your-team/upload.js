import formidable from 'formidable';
import fs from 'fs';
import path from 'path';

// Configure API route to handle file uploads
export const config = {
  api: {
    bodyParser: false, // Disable body parsing to handle multipart/form-data
  },
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    
    // Parse the multipart form data
    const form = formidable({
      maxFileSize: 10 * 1024 * 1024, // 10MB limit
      uploadDir: '/tmp',
      keepExtensions: true,
    });

    const [fields, files] = await form.parse(req);
    
    // Get the uploaded files
    const uploadedFiles = Object.values(files).flat();
    const subject = fields.subject?.[0] || 'Untitled Document';
    
    if (uploadedFiles.length === 0) {
      return res.status(400).json({ error: 'No files uploaded' });
    }

    // Create FormData for backend
    const formData = new FormData();
    
    // Add files to FormData
    for (const file of uploadedFiles) {
      const fileBuffer = fs.readFileSync(file.filepath);
      const blob = new Blob([fileBuffer], { type: file.mimetype });
      formData.append('files', blob, file.originalFilename);
    }
    
    // Add subject
    formData.append('subject', subject);
    
    // Send to backend
    const response = await fetch(`${backendUrl}/train-your-team/upload`, {
      method: 'POST',
      headers: {
        'Authorization': req.headers.authorization || '',
      },
      body: formData
    });

    const data = await response.json();
    
    // Clean up temporary files
    for (const file of uploadedFiles) {
      fs.unlinkSync(file.filepath);
    }
    
    if (response.ok) {
      res.status(200).json(data);
    } else {
      res.status(response.status).json(data);
    }
  } catch (error) {
    console.error('Upload files error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}


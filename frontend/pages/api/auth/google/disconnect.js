import { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(req, res) {
  if (req.method !== 'DELETE') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    const response = await fetch('http://localhost:8000/auth/google/disconnect', {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${req.headers.authorization?.replace('Bearer ', '') || 'demo_token'}`
      }
    })

    const data = await response.json()
    
    if (response.ok) {
      res.status(200).json(data)
    } else {
      res.status(response.status).json(data)
    }
  } catch (error) {
    console.error('Google disconnect error:', error)
    res.status(500).json({ error: 'Failed to disconnect Google account' })
  }
}



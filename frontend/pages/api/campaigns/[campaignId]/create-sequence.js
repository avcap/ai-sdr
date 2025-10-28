export default async function handler(req, res) {
  const { campaignId } = req.query
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

  if (req.method === 'POST') {
    try {
      const response = await fetch(`${backendUrl}/campaigns/${campaignId}/create-sequence`, {
        method: 'POST',
        headers: {
          'Authorization': req.headers.authorization || '',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(req.body)
      })

      const data = await response.json()

      if (!response.ok) {
        return res.status(response.status).json(data)
      }

      return res.status(200).json(data)
    } catch (error) {
      console.error('Error creating sequence from campaign:', error)
      return res.status(500).json({ error: 'Failed to create sequence' })
    }
  } else {
    res.setHeader('Allow', ['POST'])
    return res.status(405).json({ error: `Method ${req.method} not allowed` })
  }
}


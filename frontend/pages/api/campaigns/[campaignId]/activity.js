export default async function handler(req, res) {
  const { campaignId } = req.query
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

  if (req.method === 'GET') {
    try {
      const params = new URLSearchParams(req.query)
      params.delete('campaignId') // Remove campaignId from query params
      
      const url = `${backendUrl}/campaigns/${campaignId}/activity${params.toString() ? `?${params.toString()}` : ''}`
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': req.headers.authorization || '',
          'Content-Type': 'application/json'
        }
      })

      const data = await response.json()

      if (!response.ok) {
        return res.status(response.status).json(data)
      }

      return res.status(200).json(data)
    } catch (error) {
      console.error('Error fetching activity:', error)
      return res.status(500).json({ error: 'Failed to fetch activity' })
    }
  } else {
    res.setHeader('Allow', ['GET'])
    return res.status(405).json({ error: `Method ${req.method} not allowed` })
  }
}


export default async function handler(req, res) {
  const { campaignId } = req.query
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

  if (req.method === 'GET') {
    try {
      const params = new URLSearchParams(req.query)
      params.delete('campaignId') // Remove campaignId from query params
      
      const url = `${backendUrl}/campaigns/${campaignId}/export${params.toString() ? `?${params.toString()}` : ''}`
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': req.headers.authorization || ''
        }
      })

      // If CSV, stream the response
      if (req.query.format === 'csv') {
        const text = await response.text()
        res.setHeader('Content-Type', 'text/csv')
        res.setHeader('Content-Disposition', `attachment; filename=campaign_export.csv`)
        return res.status(200).send(text)
      }

      // Otherwise JSON
      const data = await response.json()

      if (!response.ok) {
        return res.status(response.status).json(data)
      }

      return res.status(200).json(data)
    } catch (error) {
      console.error('Error exporting campaign:', error)
      return res.status(500).json({ error: 'Failed to export campaign data' })
    }
  } else {
    res.setHeader('Allow', ['GET'])
    return res.status(405).json({ error: `Method ${req.method} not allowed` })
  }
}


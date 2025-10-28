export default async function handler(req, res) {
  const { sequenceId } = req.query
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

  if (req.method === 'POST') {
    try {
      const response = await fetch(`${backendUrl}/sequences/${sequenceId}/duplicate`, {
        method: 'POST',
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
      console.error('Error duplicating sequence:', error)
      return res.status(500).json({ error: 'Failed to duplicate sequence' })
    }
  } else {
    res.setHeader('Allow', ['POST'])
    return res.status(405).json({ error: `Method ${req.method} not allowed` })
  }
}


export default async function handler(req, res) {
  const { sequenceId } = req.query
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

  if (req.method === 'GET') {
    try {
      const response = await fetch(`${backendUrl}/sequences/${sequenceId}/steps`, {
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
      console.error('Error fetching steps:', error)
      return res.status(500).json({ error: 'Failed to fetch steps' })
    }
  } else if (req.method === 'POST') {
    try {
      const response = await fetch(`${backendUrl}/sequences/${sequenceId}/steps`, {
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
      console.error('Error creating step:', error)
      return res.status(500).json({ error: 'Failed to create step' })
    }
  } else {
    res.setHeader('Allow', ['GET', 'POST'])
    return res.status(405).json({ error: `Method ${req.method} not allowed` })
  }
}


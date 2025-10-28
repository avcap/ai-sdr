export default async function handler(req, res) {
  const { sequenceId } = req.query
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

  const url = `${backendUrl}/sequences/${sequenceId}`

  if (req.method === 'GET') {
    try {
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
      console.error('Error fetching sequence:', error)
      return res.status(500).json({ error: 'Failed to fetch sequence' })
    }
  } else if (req.method === 'PUT') {
    try {
      const response = await fetch(url, {
        method: 'PUT',
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
      console.error('Error updating sequence:', error)
      return res.status(500).json({ error: 'Failed to update sequence' })
    }
  } else if (req.method === 'DELETE') {
    try {
      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          'Authorization': req.headers.authorization || ''
        }
      })

      const data = await response.json()

      if (!response.ok) {
        return res.status(response.status).json(data)
      }

      return res.status(200).json(data)
    } catch (error) {
      console.error('Error deleting sequence:', error)
      return res.status(500).json({ error: 'Failed to delete sequence' })
    }
  } else {
    res.setHeader('Allow', ['GET', 'PUT', 'DELETE'])
    return res.status(405).json({ error: `Method ${req.method} not allowed` })
  }
}


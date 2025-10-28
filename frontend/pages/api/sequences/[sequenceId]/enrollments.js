export default async function handler(req, res) {
  const { sequenceId } = req.query
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

  if (req.method === 'GET') {
    try {
      const response = await fetch(`${backendUrl}/sequences/${sequenceId}/enrollments`, {
        method: 'GET',
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
      console.error('Error getting enrollments:', error)
      return res.status(500).json({ error: 'Failed to get enrollments' })
    }
  }

  res.setHeader('Allow', ['GET'])
  res.status(405).end(`Method ${req.method} Not Allowed`)
}


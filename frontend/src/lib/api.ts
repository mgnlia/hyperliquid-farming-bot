const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function fetchStatus() {
  const res = await fetch(`${API_URL}/api/status`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch status')
  return res.json()
}

export async function fetchPositions() {
  const res = await fetch(`${API_URL}/api/positions`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch positions')
  return res.json()
}

export async function fetchPoints() {
  const res = await fetch(`${API_URL}/api/points`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch points')
  return res.json()
}

export async function fetchFarmEvents() {
  const res = await fetch(`${API_URL}/api/farm-events`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch farm events')
  return res.json()
}

export function getSSEUrl() {
  return `${API_URL}/api/stream`
}

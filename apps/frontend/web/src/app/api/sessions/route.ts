import { NextRequest } from 'next/server'

const API = process.env.API_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  const auth = request.cookies.get('auth-token')?.value || request.headers.get('authorization')
  const res = await fetch(`${API}/api/sessions/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(auth && { Authorization: auth }),
    },
    body: JSON.stringify(await request.json().catch(() => ({}))),
  })
  const data = await res.json()
  return Response.json({ sessionId: data.id, ...data }, { status: res.status })
}

export async function GET(request: NextRequest) {
  const auth = request.cookies.get('auth-token')?.value || request.headers.get('authorization')
  const res = await fetch(`${API}/api/sessions/`, {
    headers: { ...(auth && { Authorization: auth }) },
  })
  return Response.json(await res.json(), { status: res.status })
}

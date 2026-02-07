import { NextRequest } from 'next/server'

const API = process.env.API_URL || 'http://localhost:8000'

export async function GET(
  request: NextRequest,
  { params }: { params: { sessionId: string } }
) {
  const auth = request.cookies.get('auth-token')?.value || request.headers.get('authorization')
  const res = await fetch(`${API}/api/sessions/${params.sessionId}/messages`, {
    headers: { ...(auth && { Authorization: auth }) },
  })
  const messages = await res.json()
  return Response.json({ messages }, { status: res.status })
}

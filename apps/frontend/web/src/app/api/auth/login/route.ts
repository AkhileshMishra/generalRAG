import { NextRequest, NextResponse } from 'next/server'

const API = process.env.API_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  const body = await request.json()
  
  const res = await fetch(`${API}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  const data = await res.json()
  
  if (res.ok && data.token) {
    const response = NextResponse.json(data)
    response.cookies.set('auth-token', data.token, {
      httpOnly: false, // Allow JS access for API calls
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 7, // 7 days
      path: '/',
    })
    return response
  }
  
  return NextResponse.json(data, { status: res.status })
}

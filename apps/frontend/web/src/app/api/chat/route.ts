import { NextRequest } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const auth = request.cookies.get('auth-token')?.value || request.headers.get('authorization')
    
    const response = await fetch(`${process.env.BACKEND_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(auth && { 'Authorization': auth })
      },
      body: JSON.stringify(await request.json())
    })

    return new Response(response.body, {
      status: response.status,
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Transfer-Encoding': 'chunked'
      }
    })
  } catch (error) {
    return Response.json({ error: 'Failed to process request' }, { status: 500 })
  }
}
import { NextRequest } from 'next/server'

const API = process.env.API_URL || 'http://localhost:8000'

export async function GET(request: NextRequest) {
  const auth = request.cookies.get('auth-token')?.value || request.headers.get('authorization')
  
  // For now return empty array - backend doesn't have list endpoint yet
  return Response.json([])
}

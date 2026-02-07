import { NextResponse } from 'next/server'

export async function POST() {
  const response = NextResponse.json({ status: 'logged out' })
  response.cookies.delete('auth-token')
  return response
}

import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth-token')?.value || request.headers.get('authorization')
  const { pathname } = request.nextUrl

  if ((pathname.startsWith('/chat') || pathname.startsWith('/admin')) && !token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/chat/:path*', '/admin/:path*']
}
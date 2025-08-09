import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { jwtVerify, createRemoteJWKSet } from 'jose'

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
const JWKS = createRemoteJWKSet(new URL(apiBase + '/v1/.well-known/jwks.json'))
const AUD = 'loan-manager'
const ISS = 'http://localhost:8000/auth'

// Map of path prefix -> required role(s)
const PROTECTED: Record<string, string[]> = {
  '/loan-products': ['admin', 'user'],
}

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl
  const rule = Object.entries(PROTECTED).find(([prefix]) => pathname.startsWith(prefix))
  if (!rule) return NextResponse.next()

  const cookie = req.cookies.get('access_token')?.value
  if (!cookie) {
    const url = req.nextUrl.clone(); url.pathname = '/login'
    return NextResponse.redirect(url)
  }
  try {
    const { payload } = await jwtVerify(cookie, JWKS, { issuer: ISS, audience: AUD })
    const roles = (payload.roles as string[]) || []
    const needed = rule[1]
    const ok = needed.some(r => roles.includes(r))
    if (!ok) {
      const url = req.nextUrl.clone(); url.pathname = '/login'
      return NextResponse.redirect(url)
    }
    return NextResponse.next()
  } catch {
    const url = req.nextUrl.clone(); url.pathname = '/login'
    return NextResponse.redirect(url)
  }
}

export const config = { matcher: ['/loan-products/:path*'] }



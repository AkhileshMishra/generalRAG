import { NextRequest } from 'next/server'

const API = process.env.API_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  const auth = request.cookies.get('auth-token')?.value || request.headers.get('authorization')
  
  const formData = await request.formData()
  const file = formData.get('files') as File
  
  if (!file) {
    return Response.json({ error: 'No file provided' }, { status: 400 })
  }

  const backendForm = new FormData()
  backendForm.append('file', file)
  backendForm.append('title', file.name)

  const res = await fetch(`${API}/api/admin/upload/`, {
    method: 'POST',
    headers: { ...(auth && { Authorization: auth.startsWith('Bearer ') ? auth : `Bearer ${auth}` }) },
    body: backendForm,
  })

  return Response.json(await res.json(), { status: res.status })
}

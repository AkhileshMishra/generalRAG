'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

export default function NewChatPage() {
  const router = useRouter()
  const [error, setError] = useState(false)

  useEffect(() => {
    fetch('/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
      .then(res => { if (!res.ok) throw new Error(); return res.json() })
      .then(data => router.replace(`/chat/${data.sessionId}`))
      .catch(() => setError(true))
  }, [router])

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="mb-4">Failed to create chat session.</p>
          <button onClick={() => { setError(false); location.reload() }} className="px-4 py-2 bg-blue-600 text-white rounded">
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-center justify-center h-full">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto" />
    </div>
  )
}

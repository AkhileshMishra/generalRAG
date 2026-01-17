'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

export default function NewChatPage() {
  const router = useRouter()
  const [isCreating, setIsCreating] = useState(true)

  useEffect(() => {
    const createSession = async () => {
      try {
        const response = await fetch('/api/sessions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
        
        if (!response.ok) throw new Error('Failed to create session')
        
        const { sessionId } = await response.json()
        router.push(`/chat/${sessionId}`)
      } catch (error) {
        console.error('Error creating session:', error)
        setIsCreating(false)
      }
    }

    createSession()
  }, [router])

  if (isCreating) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Creating new chat session...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-center justify-center h-full">
      <p>Failed to create chat session. Please try again.</p>
    </div>
  )
}
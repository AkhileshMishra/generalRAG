import { useCallback } from 'react'
import { Citation } from '../lib/types'

interface StreamResponse {
  token?: string
  citations?: Citation[]
  done?: boolean
}

export const useChat = () => {
  const sendMessage = useCallback(async function* (sessionId: string, message: string) {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ sessionId, message }),
    })

    if (!response.body) throw new Error('No response body')

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let citations: Citation[] = []

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') return citations

            try {
              const parsed: StreamResponse = JSON.parse(data)
              if (parsed.token) {
                yield parsed.token
              }
              if (parsed.citations) {
                citations = parsed.citations
              }
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }

    return citations
  }, [])

  return { sendMessage }
}
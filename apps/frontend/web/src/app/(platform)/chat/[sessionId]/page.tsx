'use client'

import { useEffect, useState, useCallback } from 'react'
import { MessageList } from '@/components/chat/message-list'
import { ChatInput } from '@/components/chat/chat-input'
import { CitationPanel } from '@/components/chat/citation-panel'
import { Message, Citation } from '@/lib/types'

export default function ChatSessionPage({
  params,
}: {
  params: { sessionId: string }
}) {
  const [messages, setMessages] = useState<Message[]>([])
  const [citations, setCitations] = useState<Citation[]>([])
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    fetch(`/api/sessions/${params.sessionId}/messages`)
      .then(res => res.ok ? res.json() : { messages: [] })
      .then(data => setMessages(data.messages || []))
      .catch(() => {})
  }, [params.sessionId])

  const handleSend = useCallback(async (content: string) => {
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content }
    setMessages(prev => [...prev, userMsg])
    setIsLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content, sessionId: params.sessionId })
      })

      const reader = res.body?.getReader()
      if (!reader) return

      let assistantContent = ''
      const assistantId = (Date.now() + 1).toString()
      let buffer = '' // Buffer for incomplete chunks

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        // Decode with stream: true to handle multi-byte chars across chunks
        const chunk = new TextDecoder().decode(value, { stream: true })
        buffer += chunk

        // Split by newline, keep last incomplete line in buffer
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed || trimmed.startsWith('event:')) continue

          if (trimmed.startsWith('data: ')) {
            try {
              const data = JSON.parse(trimmed.slice(6))
              if (data.text) {
                assistantContent += data.text
                setMessages(prev => {
                  const lastMsg = prev[prev.length - 1]
                  if (lastMsg?.id === assistantId) {
                    return [...prev.slice(0, -1), { ...lastMsg, content: assistantContent }]
                  }
                  return [...prev, { id: assistantId, role: 'assistant', content: assistantContent }]
                })
              }
              if (data.citations) setCitations(data.citations)
            } catch {
              // Incomplete JSON - will be completed in next chunk via buffer
            }
          }
        }
      }

      // Process any remaining buffer content
      if (buffer.trim().startsWith('data: ')) {
        try {
          const data = JSON.parse(buffer.trim().slice(6))
          if (data.citations) setCitations(data.citations)
        } catch {
          // Ignore incomplete final chunk
        }
      }
    } catch (err) {
      console.error('Stream error:', err)
    } finally {
      setIsLoading(false)
    }
  }, [params.sessionId])

  const handleCitationClick = (index: number) => {
    setSelectedIndex(index)
  }

  return (
    <div className="flex h-full">
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto p-4">
          <MessageList 
            messages={messages}
            isLoading={isLoading}
            onCitationClick={handleCitationClick}
          />
        </div>
        <div className="border-t p-4">
          <ChatInput onSend={handleSend} disabled={isLoading} />
        </div>
      </div>
      
      {selectedIndex !== null && (
        <CitationPanel
          citations={citations}
          selectedIndex={selectedIndex}
          onClose={() => setSelectedIndex(null)}
        />
      )}
    </div>
  )
}

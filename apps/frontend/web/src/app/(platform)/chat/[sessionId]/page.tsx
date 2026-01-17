'use client'

import { useEffect, useState } from 'react'
import { useChat } from 'ai/react'
import { MessageList } from '@/components/chat/message-list'
import { ChatInput } from '@/components/chat/chat-input'
import { CitationPanel } from '@/components/chat/citation-panel'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: any[]
}

export default function ChatSessionPage({
  params,
}: {
  params: { sessionId: string }
}) {
  const [messages, setMessages] = useState<Message[]>([])
  const [selectedCitation, setSelectedCitation] = useState(null)
  const [showCitationPanel, setShowCitationPanel] = useState(false)

  const { messages: chatMessages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: '/api/chat',
    body: { sessionId: params.sessionId },
    onFinish: (message) => {
      setMessages(prev => [...prev, message])
    }
  })

  useEffect(() => {
    const fetchMessages = async () => {
      try {
        const response = await fetch(`/api/sessions/${params.sessionId}/messages`)
        if (response.ok) {
          const data = await response.json()
          setMessages(data.messages || [])
        }
      } catch (error) {
        console.error('Error fetching messages:', error)
      }
    }

    fetchMessages()
  }, [params.sessionId])

  const handleCitationClick = (citation: any) => {
    setSelectedCitation(citation)
    setShowCitationPanel(true)
  }

  const allMessages = [...messages, ...chatMessages]

  return (
    <div className="flex h-full">
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto">
          <MessageList 
            messages={allMessages}
            onCitationClick={handleCitationClick}
          />
        </div>
        <div className="border-t p-4">
          <ChatInput
            input={input}
            handleInputChange={handleInputChange}
            handleSubmit={handleSubmit}
            isLoading={isLoading}
          />
        </div>
      </div>
      
      {showCitationPanel && (
        <CitationPanel
          citation={selectedCitation}
          onClose={() => setShowCitationPanel(false)}
        />
      )}
    </div>
  )
}
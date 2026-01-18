import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Message } from '@/lib/types'
import { cn } from '@/lib/utils'

interface MessageBubbleProps {
  message: Message
  onCitationClick: (index: number) => void
}

// Render text with clickable citation badges
function TextWithCitations({ 
  text, 
  onCitationClick 
}: { 
  text: string
  onCitationClick: (index: number) => void 
}) {
  const parts = text.split(/(\[\d+\])/g)
  
  return (
    <>
      {parts.map((part, i) => {
        const match = part.match(/^\[(\d+)\]$/)
        if (match) {
          const index = parseInt(match[1]) - 1
          return (
            <button
              key={i}
              className="inline-flex items-center justify-center w-5 h-5 mx-0.5 text-xs font-medium text-blue-600 bg-blue-100 rounded hover:bg-blue-200"
              onClick={() => onCitationClick(index)}
            >
              {match[1]}
            </button>
          )
        }
        return <React.Fragment key={i}>{part}</React.Fragment>
      })}
    </>
  )
}

export function MessageBubble({ message, onCitationClick }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={cn(
      "flex w-full mb-4",
      isUser ? "justify-end" : "justify-start"
    )}>
      <div className={cn(
        "max-w-[80%] rounded-lg px-4 py-2",
        isUser 
          ? "bg-blue-500 text-white ml-auto" 
          : "bg-gray-100 text-gray-900"
      )}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // Process text nodes to inject citation buttons
            p: ({ children }) => {
              return (
                <p className="mb-2 last:mb-0">
                  {React.Children.map(children, (child) => {
                    if (typeof child === 'string') {
                      return <TextWithCitations text={child} onCitationClick={onCitationClick} />
                    }
                    return child
                  })}
                </p>
              )
            },
            // Handle inline code, strong, em etc. that may contain citations
            strong: ({ children }) => (
              <strong>
                {React.Children.map(children, (child) => {
                  if (typeof child === 'string') {
                    return <TextWithCitations text={child} onCitationClick={onCitationClick} />
                  }
                  return child
                })}
              </strong>
            ),
            em: ({ children }) => (
              <em>
                {React.Children.map(children, (child) => {
                  if (typeof child === 'string') {
                    return <TextWithCitations text={child} onCitationClick={onCitationClick} />
                  }
                  return child
                })}
              </em>
            ),
            li: ({ children }) => (
              <li>
                {React.Children.map(children, (child) => {
                  if (typeof child === 'string') {
                    return <TextWithCitations text={child} onCitationClick={onCitationClick} />
                  }
                  return child
                })}
              </li>
            ),
          }}
        >
          {message.content}
        </ReactMarkdown>
      </div>
    </div>
  )
}

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Message } from '@/lib/types'
import { cn } from '@/lib/utils'

interface MessageBubbleProps {
  message: Message
  onCitationClick: (index: number) => void
}

export function MessageBubble({ message, onCitationClick }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  
  const processContent = (content: string) => {
    return content.replace(/\[(\d+)\]/g, (match, num) => {
      const index = parseInt(num) - 1
      return `<button class="citation-badge" data-citation="${index}">[${num}]</button>`
    })
  }

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
            p: ({ children }) => (
              <div 
                dangerouslySetInnerHTML={{ 
                  __html: processContent(String(children)) 
                }}
                onClick={(e) => {
                  const target = e.target as HTMLElement
                  if (target.classList.contains('citation-badge')) {
                    const index = parseInt(target.dataset.citation || '0')
                    onCitationClick(index)
                  }
                }}
              />
            )
          }}
        >
          {message.content}
        </ReactMarkdown>
      </div>
    </div>
  )
}
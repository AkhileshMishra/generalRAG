import { Citation } from '@/lib/types'
import { cn } from '@/lib/utils'

interface CitationPanelProps {
  citations: Citation[]
  selectedIndex?: number
  onClose: () => void
}

export function CitationPanel({ citations, selectedIndex, onClose }: CitationPanelProps) {
  if (!citations.length) return null

  return (
    <div className="w-80 border-l bg-white h-full flex flex-col">
      <div className="flex items-center justify-between p-4 border-b">
        <h3 className="font-semibold">Citations</h3>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700"
        >
          ×
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {citations.map((citation, index) => (
          <div
            key={citation.id}
            className={cn(
              "border rounded-lg p-3",
              selectedIndex === index && "border-blue-500 bg-blue-50"
            )}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-blue-600">
                [{index + 1}]
              </span>
              <span className="text-xs text-gray-500">
                {citation.documentId}
              </span>
            </div>
            
            <h4 className="font-medium text-sm mb-2">{citation.title}</h4>
            
            <p className="text-sm text-gray-600 mb-2">
              {citation.snippet}
            </p>
            
            {citation.url && (
              <a
                href={citation.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-500 hover:underline"
              >
                View source
              </a>
            )}
            
            <div className="mt-2 p-2 bg-gray-100 rounded text-xs text-gray-500">
              Bbox overlay placeholder
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
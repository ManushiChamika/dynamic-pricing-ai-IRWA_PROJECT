import { useState } from 'react'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible'

interface ThinkingTokensProps {
  thinking: string
}

export function ThinkingTokens({ thinking }: ThinkingTokensProps) {
  const [isOpen, setIsOpen] = useState(false)

  if (!thinking || thinking.trim() === '') {
    return null
  }

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className="my-2">
      <CollapsibleTrigger className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          className={`transform transition-transform ${isOpen ? 'rotate-90' : ''}`}
        >
          <path
            d="M4 2L8 6L4 10"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <span className="font-medium">Thinking tokens</span>
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-2 rounded-md border border-border bg-muted/30 p-3 text-sm">
        <pre className="whitespace-pre-wrap font-mono text-xs">{thinking}</pre>
      </CollapsibleContent>
    </Collapsible>
  )
}



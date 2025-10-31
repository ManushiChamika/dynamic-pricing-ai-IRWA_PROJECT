import React from 'react'
import { Zap } from 'lucide-react'

interface InputEnhancerProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  disabled?: boolean
}

export const InputEnhancer: React.FC<InputEnhancerProps> = ({
  value,
  onChange,
  onSubmit,
  disabled = false,
}) => {
  const charCount = value.trim().length
  const isLongMessage = charCount > 200

  return (
    <div className="relative">
      {isLongMessage && (
        <div className="absolute -top-8 left-0 text-xs text-muted-foreground flex items-center gap-1">
          <Zap className="w-3 h-3" />
          Long message detected - consider breaking it into parts
        </div>
      )}
      <textarea
        className="flex-1 min-h-[80px] rounded-xl border-2 border-indigo-500/20 bg-background/50 backdrop-blur-sm px-4 py-3 text-[0.9375rem] placeholder:text-muted-foreground/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:border-indigo-500 disabled:cursor-not-allowed disabled:opacity-50 resize-none shadow-sm hover:border-indigo-500/30 transition-all duration-200 w-full"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        onKeyDown={(e) => {
          if (!disabled && e.key === 'Enter' && !e.shiftKey && value.trim()) {
            e.preventDefault()
            onSubmit()
          }
        }}
        aria-label="Message input"
        placeholder="Share your thoughts, ask anything..."
      />
      <div className="absolute bottom-3 right-3 text-xs text-muted-foreground">
        {charCount} chars
      </div>
    </div>
  )
}

import React, { useEffect, useState } from 'react'
import { Copy, Check } from 'lucide-react'

interface CodeBlockProps {
  code: string
  language?: string
  className?: string
}

export const CodeBlock: React.FC<CodeBlockProps> = ({ code, language = 'plaintext', className = '' }) => {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      console.error('Failed to copy code')
    }
  }

  return (
    <div className={`relative group my-4 rounded-xl overflow-hidden bg-muted/50 shadow-[0_2px_8px_rgba(0,0,0,0.04)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.2)] border border-border/30 ${className}`}>
      <div className="flex items-center justify-between px-4 py-2.5 bg-muted/70 border-b border-border/20">
        <span className="text-xs font-mono text-muted-foreground/80 uppercase tracking-wider font-medium">
          {language || 'code'}
        </span>
        <button
          onClick={handleCopy}
          className="p-1.5 rounded-md hover:bg-background/50 transition-all duration-200 opacity-0 group-hover:opacity-100"
          title="Copy code"
        >
          {copied ? (
            <Check className="w-4 h-4 text-green-500" />
          ) : (
            <Copy className="w-4 h-4 text-muted-foreground hover:text-foreground transition-colors" />
          )}
        </button>
      </div>
      <pre className="overflow-x-auto p-5 text-[14px] font-mono leading-[1.6]">
        <code className={`language-${language}`}>{code}</code>
      </pre>
    </div>
  )
}

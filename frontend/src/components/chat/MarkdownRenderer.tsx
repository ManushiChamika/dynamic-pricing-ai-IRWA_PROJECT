import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const cleanMarkdownTables = (content: string): string => {
  const lines = content.split('\n')
  const result: string[] = []
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const nextLine = lines[i + 1] || ''
    
    if (line.includes('|') && nextLine.match(/^\s*\|[\s\-:|]*\|\s*$/)) {
      const cells = nextLine.split('|').filter(c => c.trim())
      const cleanedCells = cells.map(cell => {
        const trimmed = cell.trim()
        const dashCount = (trimmed.match(/-/g) || []).length
        
        if (dashCount > 3) {
          const leftColon = trimmed.startsWith(':')
          const rightColon = trimmed.endsWith(':')
          if (leftColon && rightColon) return ':---:'
          if (leftColon) return ':---'
          if (rightColon) return '---:'
          return '---'
        }
        return trimmed
      })
      
      result.push(line)
      result.push('| ' + cleanedCells.join(' | ') + ' |')
      i++
    } else {
      result.push(line)
    }
  }
  
  return result.join('\n')
}

const MARKDOWN_COMPONENTS = {
  h1: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h1 className="text-3xl font-bold my-4 pb-2 border-b border-border/30" {...props}>
      {children}
    </h1>
  ),
  h2: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h2 className="text-2xl font-semibold my-3 pb-1.5 border-b border-border/20" {...props}>
      {children}
    </h2>
  ),
  h3: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h3 className="text-xl font-semibold my-2.5" {...props}>
      {children}
    </h3>
  ),
  h4: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h4 className="text-lg font-semibold my-2" {...props}>
      {children}
    </h4>
  ),
  h5: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h5 className="text-base font-semibold my-1.5" {...props}>
      {children}
    </h5>
  ),
  h6: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h6 className="text-sm font-semibold my-1.5 text-muted-foreground" {...props}>
      {children}
    </h6>
  ),
  p: ({ children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) => (
    <p className="my-2 leading-relaxed" {...props}>
      {children}
    </p>
  ),
  li: ({ children, ...props }: React.LiHTMLAttributes<HTMLLIElement>) => (
    <li className="my-1 leading-relaxed" {...props}>
      {children}
    </li>
  ),
  ul: ({ children, ...props }: React.HTMLAttributes<HTMLUListElement>) => (
    <ul className="list-disc list-inside my-3 space-y-1.5 pl-2" {...props}>
      {children}
    </ul>
  ),
  ol: ({ children, ...props }: React.OlHTMLAttributes<HTMLOListElement>) => (
    <ol className="list-decimal list-inside my-3 space-y-1.5 pl-2" {...props}>
      {children}
    </ol>
  ),
  blockquote: ({ children, ...props }: React.HTMLAttributes<HTMLQuoteElement>) => (
    <blockquote
      className="my-3 pl-4 border-l-4 border-primary/50 text-muted-foreground italic bg-primary/5 py-2 pr-3 rounded-r"
      {...props}
    >
      {children}
    </blockquote>
  ),
  code: ({ children, inline, ...props }: any) => {
    if (inline) {
      return (
        <code
          className="px-1.5 py-0.5 bg-primary/10 text-primary rounded text-sm font-mono"
          {...props}
        >
          {children}
        </code>
      )
    }
    return (
      <code className="font-mono text-sm" {...props}>
        {children}
      </code>
    )
  },
  pre: ({ children, ...props }: React.HTMLAttributes<HTMLPreElement>) => (
    <pre
      className="bg-muted/50 border border-border/50 rounded-lg p-4 my-3 overflow-x-auto"
      {...props}
    >
      {children}
    </pre>
  ),
  table: ({ children, ...props }: React.TableHTMLAttributes<HTMLTableElement>) => (
    <div className="my-3 border border-border/50 rounded-lg overflow-hidden">
      <table className="w-full text-sm" {...props}>
        {children}
      </table>
    </div>
  ),
  thead: ({ children, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) => (
    <thead className="bg-muted/70 border-b border-border/50" {...props}>
      {children}
    </thead>
  ),
  tbody: ({ children, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) => (
    <tbody className="divide-y divide-border/30" {...props}>
      {children}
    </tbody>
  ),
  tr: ({ children, ...props }: React.HTMLAttributes<HTMLTableRowElement>) => (
    <tr className="hover:bg-muted/30 transition-colors" {...props}>
      {children}
    </tr>
  ),
  th: ({ children, ...props }: React.ThHTMLAttributes<HTMLTableHeaderCellElement>) => (
    <th className="px-4 py-2 text-left font-semibold" {...props}>
      {children}
    </th>
  ),
  td: ({ children, ...props }: React.TdHTMLAttributes<HTMLTableDataCellElement>) => (
    <td className="px-4 py-2" {...props}>
      {children}
    </td>
  ),
  a: ({ children, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a
      className="text-primary hover:underline decoration-primary/50 transition-colors"
      {...props}
    >
      {children}
    </a>
  ),
  strong: ({ children, ...props }: React.HTMLAttributes<HTMLElement>) => (
    <strong className="font-semibold text-foreground/90" {...props}>
      {children}
    </strong>
  ),
  em: ({ children, ...props }: React.HTMLAttributes<HTMLElement>) => (
    <em className="italic text-foreground/85" {...props}>
      {children}
    </em>
  ),
  hr: (props: React.HTMLAttributes<HTMLHRElement>) => (
    <hr className="my-4 border-border/30" {...props} />
  ),
}

interface MarkdownRendererProps {
  content: string
  className?: string
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  const cleanedContent = cleanMarkdownTables(content)
  
  return (
    <div className={`max-w-none markdown-renderer ${className}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={MARKDOWN_COMPONENTS}>
        {cleanedContent}
      </ReactMarkdown>
    </div>
  )
}


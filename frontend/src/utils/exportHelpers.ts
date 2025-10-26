export function sanitizeFileName(s: string) {
  if (!s || s.trim() === '') return 'export.txt'
  return s.replace(/[^a-zA-Z0-9._-]/g, '_')
}

export function buildMarkdown(thread: any, messages: any[], includeMeta = false) {
  const lines: string[] = []
  const title = (thread && thread.title) || `Thread ${thread && thread.id ? thread.id : ''}`
  const created = thread && thread.created_at ? thread.created_at : ''
  lines.push(`# ${title}`)
  if (created) lines.push(`_Created: ${created}_`)
  lines.push('')
  lines.push('')
  
  if (!messages || messages.length === 0) {
    lines.push('_No messages in this thread_')
    return lines.join('\n')
  }
  
  for (const m of messages) {
    const role = (m.role || 'user').toString().toUpperCase()
    const ts = m.created_at || ''
    let header = `**${role}**`
    if (ts) header += ` • ${ts}`
    lines.push(header)
    lines.push('')
    
    if (includeMeta) {
      const meta: any = {}
      if (m.model) meta.model = m.model
      if (m.token_in != null) meta.token_in = m.token_in
      if (m.token_out != null) meta.token_out = m.token_out
      if (m.cost_usd != null) meta.cost_usd = m.cost_usd
      if (m.api_calls != null) meta.api_calls = m.api_calls
      if (m.agents) meta.agents = m.agents
      if (m.tools) meta.tools = m.tools
      if (m.metadata) meta.metadata = m.metadata
      
      if (Object.keys(meta).length > 0) {
        try {
          lines.push('```json')
          lines.push(JSON.stringify(meta, null, 2))
          lines.push('```')
          lines.push('')
        } catch (e) {
          console.error('Failed to serialize metadata:', e)
        }
      }
    }
    
    lines.push(m.content || '_No content_')
    lines.push('')
    lines.push('---')
    lines.push('')
  }
  return lines.join('\n')
}

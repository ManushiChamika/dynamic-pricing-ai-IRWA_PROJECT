export function sanitizeFileName(s: string) {
  return (s || '').replace(/[^a-zA-Z0-9._-]/g, '_')
}

export function buildMarkdown(thread: any, messages: any[], includeMeta = false) {
  const lines: string[] = []
  const title = (thread && thread.title) || `Thread ${thread && thread.id ? thread.id : ''}`
  const created = thread && thread.created_at ? thread.created_at : ''
  lines.push(`# ${title}`)
  if (created) lines.push(`_Created: ${created}_`)
  lines.push('')
  for (const m of messages || []) {
    const role = (m.role || 'user').toString().toUpperCase()
    const ts = m.created_at || ''
    let header = `**${role}**`
    if (ts) header += ` • ${ts}`
    lines.push(header)
    if (includeMeta && m.metadata) {
      try {
        lines.push('```json')
        lines.push(JSON.stringify(m.metadata, null, 2))
        lines.push('```')
      } catch (e) {}
    }
    lines.push('')
    lines.push(m.content || '')
    lines.push('\n---\n')
  }
  return lines.join('\n')
}

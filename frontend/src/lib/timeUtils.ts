export function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export function groupThreadsByTime(threads: Array<{ updated_at: string }>): {
  today: number[]
  yesterday: number[]
  thisWeek: number[]
  older: number[]
} {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today.getTime() - 86400000)
  const weekAgo = new Date(today.getTime() - 7 * 86400000)

  const groups: { today: number[]; yesterday: number[]; thisWeek: number[]; older: number[] } = { 
    today: [], 
    yesterday: [], 
    thisWeek: [], 
    older: [] 
  }

  threads.forEach((thread, index) => {
    const threadDate = new Date(thread.updated_at)
    if (threadDate >= today) {
      groups.today.push(index)
    } else if (threadDate >= yesterday) {
      groups.yesterday.push(index)
    } else if (threadDate >= weekAgo) {
      groups.thisWeek.push(index)
    } else {
      groups.older.push(index)
    }
  })

  return groups
}

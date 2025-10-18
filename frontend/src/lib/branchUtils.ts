import type { Message } from '../components/BranchNavigator'

interface BranchInfo {
  hasChildren: boolean
  childCount: number
  children: Message[]
  siblingIndex: number
  siblingCount: number
  siblings: Message[]
}

export function analyzeBranches(messages: Message[], currentMessageId: number): BranchInfo {
  const children = messages.filter((m) => m.parent_id === currentMessageId)
  const current = messages.find((m) => m.id === currentMessageId)
  const siblings = current?.parent_id
    ? messages.filter((m) => m.parent_id === current.parent_id).sort((a, b) => a.id - b.id)
    : []
  const siblingIndex = siblings.findIndex((m) => m.id === currentMessageId)

  return {
    hasChildren: children.length > 1,
    childCount: children.length,
    children: children.sort((a, b) => a.id - b.id),
    siblingIndex: siblingIndex >= 0 ? siblingIndex : 0,
    siblingCount: siblings.length,
    siblings,
  }
}

export function buildConversationPath(
  messages: Message[],
  selectedBranches: Map<number, number> = new Map()
): Message[] {
  if (!messages.length) return []
  const rootMessages = messages.filter((m) => !m.parent_id)
  if (!rootMessages.length) return []
  const root = rootMessages[0]
  const path: Message[] = [root]
  let current = root

  while (true) {
    const children = messages.filter((m) => m.parent_id === current.id)
    if (!children.length) break
    if (children.length === 1) {
      path.push(children[0])
      current = children[0]
      continue
    }
    const branchChoice = selectedBranches.get(current.id)
    if (branchChoice !== undefined) {
      const chosen = messages.find((m) => m.id === branchChoice && m.parent_id === current.id)
      if (chosen) {
        path.push(chosen)
        current = chosen
        continue
      }
    }
    const sorted = children.sort((a, b) => a.id - b.id)
    path.push(sorted[0])
    current = sorted[0]
  }

  return path
}

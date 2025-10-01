import { useMemo } from 'react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./ui/tooltip";

export type Message = {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at?: string;
  parent_id?: number | null;
  [key: string]: any;
};

interface BranchInfo {
  hasChildren: boolean;
  childCount: number;
  children: Message[];
  siblingIndex: number;
  siblingCount: number;
  siblings: Message[];
}

/**
 * Analyze message tree to find branches
 */
export function analyzeBranches(messages: Message[], currentMessageId: number): BranchInfo {
  // Find children of current message
  const children = messages.filter(m => m.parent_id === currentMessageId);
  
  // Find current message
  const current = messages.find(m => m.id === currentMessageId);
  
  // Find siblings (messages with same parent)
  const siblings = current?.parent_id 
    ? messages.filter(m => m.parent_id === current.parent_id).sort((a, b) => a.id - b.id)
    : [];
  
  const siblingIndex = siblings.findIndex(m => m.id === currentMessageId);
  
  return {
    hasChildren: children.length > 1,
    childCount: children.length,
    children: children.sort((a, b) => a.id - b.id),
    siblingIndex: siblingIndex >= 0 ? siblingIndex : 0,
    siblingCount: siblings.length,
    siblings
  };
}

interface BranchNavigatorProps {
  message: Message;
  allMessages: Message[];
  onNavigate: (messageId: number) => void;
}

export function BranchNavigator({ message, allMessages, onNavigate }: BranchNavigatorProps) {
  const branchInfo = useMemo(
    () => analyzeBranches(allMessages, message.id),
    [allMessages, message.id]
  );

  if (!branchInfo.hasChildren && branchInfo.siblingCount <= 1) {
    return null;
  }

  return (
    <div className="flex items-center gap-2 mt-2 p-2 rounded-lg bg-gray-500/10 border border-gray-500/20">
      {/* Show if message has multiple children (branches) */}
      {branchInfo.hasChildren && (
        <div className="flex items-center gap-2">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-1.5 text-xs text-gray-400">
                  <span className="text-yellow-400">🔀</span>
                  <span className="font-medium">{branchInfo.childCount} branches</span>
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs">
                <div className="text-xs space-y-1">
                  <div className="font-semibold">Conversation branches here</div>
                  <div className="text-muted-foreground">
                    This message has {branchInfo.childCount} different continuations.
                    Navigate to the next message to explore branches.
                  </div>
                </div>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          
          <div className="flex gap-1">
            {branchInfo.children.slice(0, 3).map((child, idx) => (
              <TooltipProvider key={child.id}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={() => onNavigate(child.id)}
                      className="px-2 py-1 text-xs rounded bg-gray-600/30 hover:bg-gray-600/50 text-gray-300 transition-colors"
                      aria-label={`Jump to branch ${idx + 1}`}
                    >
                      {child.role === 'user' ? '👤' : '🤖'} #{idx + 1}
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="max-w-xs">
                    <div className="text-xs space-y-1">
                      <div className="font-semibold">Branch #{idx + 1}</div>
                      <div className="text-muted-foreground truncate max-w-[200px]">
                        {child.content.slice(0, 80)}...
                      </div>
                    </div>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            ))}
            {branchInfo.childCount > 3 && (
              <span className="px-2 py-1 text-xs text-gray-400">
                +{branchInfo.childCount - 3} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Show if message has siblings (current message is part of a branch) */}
      {branchInfo.siblingCount > 1 && (
        <div className="flex items-center gap-2 ml-auto">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-1.5 text-xs text-gray-400">
                  <span className="text-blue-400">⸬</span>
                  <span className="font-medium">
                    Branch {branchInfo.siblingIndex + 1}/{branchInfo.siblingCount}
                  </span>
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs">
                <div className="text-xs space-y-1">
                  <div className="font-semibold">Alternative branch</div>
                  <div className="text-muted-foreground">
                    This is branch {branchInfo.siblingIndex + 1} of {branchInfo.siblingCount} alternatives.
                    Use arrows to switch between branches.
                  </div>
                </div>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <div className="flex gap-1">
            <button
              onClick={() => {
                const prevSibling = branchInfo.siblings[branchInfo.siblingIndex - 1];
                if (prevSibling) onNavigate(prevSibling.id);
              }}
              disabled={branchInfo.siblingIndex === 0}
              className="px-2 py-1 text-xs rounded bg-gray-600/30 hover:bg-gray-600/50 disabled:opacity-30 disabled:cursor-not-allowed text-gray-300 transition-colors"
              aria-label="Previous branch"
              title="Previous branch (Ctrl+[)"
            >
              ←
            </button>
            <button
              onClick={() => {
                const nextSibling = branchInfo.siblings[branchInfo.siblingIndex + 1];
                if (nextSibling) onNavigate(nextSibling.id);
              }}
              disabled={branchInfo.siblingIndex === branchInfo.siblingCount - 1}
              className="px-2 py-1 text-xs rounded bg-gray-600/30 hover:bg-gray-600/50 disabled:opacity-30 disabled:cursor-not-allowed text-gray-300 transition-colors"
              aria-label="Next branch"
              title="Next branch (Ctrl+])"
            >
              →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Hook to build a filtered conversation path based on currently selected branches
 */
export function buildConversationPath(
  messages: Message[],
  selectedBranches: Map<number, number> = new Map()
): Message[] {
  if (!messages.length) return [];

  const result: Message[] = [];
  const messageMap = new Map(messages.map(m => [m.id, m]));
  
  // Start with root messages (no parent)
  let current = messages.find(m => !m.parent_id);
  
  while (current) {
    result.push(current);
    
    // Find children
    const children = messages.filter(m => m.parent_id === current?.id).sort((a, b) => a.id - b.id);
    
    if (children.length === 0) {
      break;
    } else if (children.length === 1) {
      // No branch, just continue
      current = children[0];
    } else {
      // Multiple branches - check if we have a selection
      const selectedId = selectedBranches.get(current.id);
      const selected = selectedId ? children.find(c => c.id === selectedId) : null;
      current = selected || children[0]; // Default to first branch
    }
  }
  
  return result;
}

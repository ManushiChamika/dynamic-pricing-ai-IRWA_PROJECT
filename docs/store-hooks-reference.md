# Store Hooks Quick Reference

## Message Store

### State Selectors
```typescript
// Get entire messages array
const messages = useMessages(state => state.messages)

// Get specific streaming state
const streamingActive = useMessages(state => state.streamingActive)
const liveActiveAgent = useMessages(state => state.liveActiveAgent)
const liveTool = useMessages(state => state.liveTool)

// Get all streaming-related state
const { streamingActive, liveActiveAgent, liveTool, liveAgents, turnStats } = useStreamingState()
```

### Actions
```typescript
const { refresh, send, edit, del, branch, fork, stop } = useMessagesActions()
```

## Thread Store

### State Selectors
```typescript
// Get current thread ID
const currentId = useCurrentThread()

// Get threads array
const threads = useThreadList()

// Get both
const { currentId, threads } = useThreads(state => ({ 
  currentId: state.currentId, 
  threads: state.threads 
}))
```

### Actions
```typescript
const { setCurrent, refresh, createThread, deleteThread, renameThread } = useThreadActions()
```

## Settings Store

### State Selectors
```typescript
// Get theme only
const theme = useTheme()

// Get display settings
const { showModel, showTimestamps, showMeta, showThinking } = useDisplaySettings()

// Get app mode settings
const { mode, streaming } = useAppMode()

// Get specific setting
const showThinking = useSettings(state => state.showThinking)
```

### Actions
```typescript
const { set, setSettingsOpen } = useSettingsActions()
```

## Auth Store

### State Selectors
```typescript
// Get token only
const token = useAuthToken()

// Get user only
const user = useAuthUser()

// Get both
const { token, user } = useAuth(state => ({ 
  token: state.token, 
  user: state.user 
}))
```

### Actions
```typescript
const { login, register, logout, fetchMe, setToken } = useAuthActions()
```

## Common Patterns

### Read-Only in Component
```typescript
// When you only need to read state, no actions
function DisplayComponent() {
  const messages = useMessages(state => state.messages)
  const currentId = useCurrentThread()
  
  return <div>{messages.length} messages in thread {currentId}</div>
}
```

### Actions in Event Handlers
```typescript
// When you need actions but not state
function ActionButtons() {
  const { createThread, deleteThread } = useThreadActions()
  
  return (
    <>
      <button onClick={() => createThread()}>New</button>
      <button onClick={() => deleteThread(1)}>Delete</button>
    </>
  )
}
```

### Mixed State and Actions
```typescript
// When you need both
function MessageForm() {
  const currentId = useCurrentThread()
  const streamingActive = useMessages(state => state.streamingActive)
  const { send } = useMessagesActions()
  
  const handleSend = () => {
    if (currentId && !streamingActive) {
      send(currentId, 'Hello', 'user', true)
    }
  }
  
  return <button onClick={handleSend} disabled={streamingActive}>Send</button>
}
```

### One-Time Value Reads
```typescript
// When you need a value once, not reactively
function exportThreads() {
  const threads = useThreads.getState().threads
  console.log('Exporting:', threads)
}
```

### Derived State
```typescript
// Compute derived values in selectors
const hasMessages = useMessages(state => state.messages.length > 0)
const isStreaming = useMessages(state => state.streamingActive && !!state.liveActiveAgent)
```

## Migration Checklist

- [ ] Replace `const {...everything} = useStore()` with selective hooks
- [ ] Use action hooks for methods: `useMessagesActions()`, `useThreadActions()`, etc.
- [ ] Use specific state hooks: `useCurrentThread()`, `useTheme()`, etc.
- [ ] Update component dependencies in useEffect/useCallback hooks
- [ ] Test for reduced re-renders using React DevTools Profiler

## Anti-Patterns to Avoid

❌ **Don't destructure entire store:**
```typescript
const store = useMessages()  // Re-renders on ANY change
```

❌ **Don't mix concerns:**
```typescript
const { messages, send, refresh } = useMessages()  // Mixes state and actions
```

❌ **Don't subscribe to unused state:**
```typescript
const { messages, streamingActive, liveAgent, ... } = useMessages()
// If you only use messages
```

## Performance Tips

1. **Memoize selectors for complex computations:**
```typescript
const expensiveValue = useMessages(state => {
  return state.messages.filter(m => m.role === 'user').length
})
```

2. **Use React.memo for components:**
```typescript
export const MessageView = React.memo(({ message }) => {
  // ...
})
```

3. **Combine related subscriptions:**
```typescript
// Instead of multiple hooks
const { streamingActive, liveAgent, liveTool } = useStreamingState()

// Not
const streamingActive = useMessages(state => state.streamingActive)
const liveAgent = useMessages(state => state.liveActiveAgent)
const liveTool = useMessages(state => state.liveTool)
```

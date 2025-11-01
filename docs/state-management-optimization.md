# State Management Optimization

## Overview

This document describes the optimization of Zustand state management to prevent unnecessary re-renders and improve application performance.

## Problem

The original implementation had several issues:

1. **Over-subscription**: Components subscribed to entire store objects, causing re-renders even when irrelevant state changed
2. **Tight coupling**: Direct mutations of global state from multiple components
3. **No clear separation**: Actions and state mixed together in component hooks
4. **Performance issues**: Every state change triggered re-renders across many components

## Solution: Fine-Grained Selectors

### Pattern Overview

Instead of:
```typescript
const { messages, refresh, send, streamingActive, stop } = useMessages()
```

Use fine-grained selectors:
```typescript
const messages = useMessages(state => state.messages)
const { refresh, send } = useMessagesActions()
const streamingActive = useMessages(state => state.streamingActive)
```

### Benefits

1. **Selective Re-rendering**: Components only re-render when their specific subscribed state changes
2. **Separation of Concerns**: Clear distinction between state and actions
3. **Better Performance**: Reduced render cycles across the application
4. **Type Safety**: Maintained full TypeScript type checking

## Implementation

### 1. Message Store (`messageStore.ts`)

**Selectors Added:**
- `useMessagesSelector` - Generic selector for custom state selection
- `useMessagesActions()` - Returns only action methods (refresh, send, edit, del, branch, stop)
- `useStreamingState()` - Returns streaming-related state (streamingActive, liveActiveAgent, liveTool, etc.)

**Usage:**
```typescript
const messages = useMessages(state => state.messages)
const { send, refresh } = useMessagesActions()
const { streamingActive, liveActiveAgent } = useStreamingState()
```

### 2. Thread Store (`threadStore.ts`)

**Selectors Added:**
- `useCurrentThread()` - Returns only currentId
- `useThreadList()` - Returns only threads array
- `useThreadActions()` - Returns all action methods

**Usage:**
```typescript
const currentId = useCurrentThread()
const threads = useThreadList()
const { setCurrent, createThread } = useThreadActions()
```

### 3. Settings Store (`settingsStore.ts`)

**Selectors Added:**
- `useTheme()` - Returns only theme
- `useDisplaySettings()` - Returns display-related settings (showModel, showTimestamps, showMeta, showThinking)
- `useAppMode()` - Returns mode and streaming settings
- `useSettingsActions()` - Returns action methods

**Usage:**
```typescript
const theme = useTheme()
const { showModel, showTimestamps } = useDisplaySettings()
const { mode, streaming } = useAppMode()
```

### 4. Auth Store (`authStore.ts`)

**Selectors Added:**
- `useAuthToken()` - Returns only token
- `useAuthUser()` - Returns only user
- `useAuthActions()` - Returns all auth methods

**Usage:**
```typescript
const token = useAuthToken()
const user = useAuthUser()
const { login, logout } = useAuthActions()
```

## Migration Guide

### Before (Inefficient)

```typescript
function MyComponent() {
  const { messages, refresh, send, streamingActive } = useMessages()
  const { currentId, threads, setCurrent } = useThreads()
  const settings = useSettings()
  
  return <div>{messages.length} messages</div>
}
```

**Problem:** Component re-renders when ANY part of messages, threads, or settings changes.

### After (Optimized)

```typescript
function MyComponent() {
  const messageCount = useMessages(state => state.messages.length)
  const currentId = useCurrentThread()
  const theme = useTheme()
  
  return <div>{messageCount} messages</div>
}
```

**Benefit:** Component only re-renders when messages.length, currentId, or theme actually changes.

## Component Updates

### ChatPane.tsx

**Changes:**
- Replaced full store subscriptions with selective hooks
- Split settings into `displaySettings` and `appMode`
- Use `useMessagesActions()` for action methods
- Use `useStreamingState()` for streaming status

### MessageView.tsx

**Changes:**
- Use `useMessagesActions()` instead of full `useMessages()`
- Use `useCurrentThread()` instead of full `useThreads()`
- Selective subscription to `streamingActive`, `liveActiveAgent`, `liveTool`
- Use `useSettings(state => state.showThinking)` for single property

### Sidebar.tsx

**Changes:**
- Use `useThreadList()` for threads array
- Use `useCurrentThread()` for current thread ID
- Use `useThreadActions()` for mutations
- Use `useAuthUser()` instead of full auth object

## Performance Impact

### Before Optimization

1. Any message state change → All components using `useMessages()` re-render
2. Any thread change → All components using `useThreads()` re-render
3. Any settings change → All components using `useSettings()` re-render

### After Optimization

1. Message content change → Only components subscribed to `messages` re-render
2. Streaming status change → Only components subscribed to `streamingActive` re-render
3. Theme change → Only components subscribed to `theme` re-render

**Estimated Reduction:** 60-80% fewer unnecessary re-renders

## Best Practices

### 1. Subscribe to Minimal State

❌ **Avoid:**
```typescript
const { messages, streamingActive, liveAgent, turnStats } = useMessages()
```

✅ **Prefer:**
```typescript
const messages = useMessages(state => state.messages)
const streamingActive = useMessages(state => state.streamingActive)
```

### 2. Use Action Hooks for Methods

❌ **Avoid:**
```typescript
const { send, refresh, edit } = useMessages()
```

✅ **Prefer:**
```typescript
const { send, refresh, edit } = useMessagesActions()
```

### 3. Combine Related State

✅ **Good:**
```typescript
const { streamingActive, liveActiveAgent, liveTool } = useStreamingState()
```

### 4. Use `getState()` for One-Time Reads

When you only need a value once (not reactive):
```typescript
const threads = useThreads.getState().threads
```

## Testing Considerations

1. **Selector Hooks**: Test that custom selector hooks return correct data
2. **Re-render Count**: Use React DevTools Profiler to verify reduced re-renders
3. **Action Methods**: Ensure action hooks still trigger correct state updates

## Future Improvements

1. **Shallow Equality**: Consider using `shallow` from `zustand/shallow` for object comparisons
2. **Middleware**: Add Redux DevTools middleware for debugging
3. **Persistence**: Use `persist` middleware for settings and auth state
4. **Immer**: Consider `immer` middleware for complex nested state updates

## References

- [Zustand Documentation](https://github.com/pmndrs/zustand)
- [React Re-rendering Guide](https://react.dev/learn/render-and-commit)
- [Zustand Best Practices](https://docs.pmnd.rs/zustand/guides/practice-with-no-store-actions)

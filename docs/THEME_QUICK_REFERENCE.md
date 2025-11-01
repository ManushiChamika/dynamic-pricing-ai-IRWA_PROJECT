# Global Theme System - Quick Reference

## What Changed?

### Before (Local Theme)
```
Home Page    → Local state
Pricing Page → Local state  
Contact Page → Local state
❌ Not synchronized across pages
❌ Separate toggles per page
```

### After (Global Theme)
```
┌─────────────────────────────────┐
│    ThemeProvider (Root)         │
│  ├─ Home Page                   │
│  ├─ Pricing Page               │
│  ├─ Contact Page               │
│  └─ Chat Page                  │
└─────────────────────────────────┘
      ↓
useTheme() hook
      ↓
 theme: 'dark' | 'light'
 toggleTheme(): void
```

✅ Single source of truth  
✅ All pages share same theme  
✅ Persistent across page navigation  
✅ Persists on page refresh  

## Implementation Files

### New File
- `src/contexts/ThemeContext.tsx` - Theme state & logic

### Updated Files
- `src/main.tsx` - Added ThemeProvider wrapper
- `src/components/Navigation.tsx` - Uses global useTheme()
- `src/pages/LandingPage.tsx` - Uses global useTheme()
- `src/pages/PricingPage.tsx` - Uses global useTheme()
- `src/pages/ContactPage.tsx` - Uses global useTheme()

## How to Use in Components

```tsx
import { useTheme } from '../contexts/ThemeContext'

export function MyComponent() {
  const { theme, toggleTheme } = useTheme()
  
  return (
    <div className={theme === 'dark' ? 'dark-styles' : 'light-styles'}>
      <button onClick={toggleTheme}>
        {theme === 'dark' ? '☀️' : '🌙'}
      </button>
    </div>
  )
}
```

## Theme Values

- `theme === 'dark'` → Dark mode (default)
- `theme === 'light'` → Light mode

## Data Persistence

Saved in `localStorage` as:
```javascript
localStorage.getItem('theme') // 'dark' or 'light'
```

## State Flow

```
Click Toggle Button
    ↓
toggleTheme() invoked
    ↓
theme state updates
    ↓
localStorage updated
    ↓
Document re-renders
    ↓
All pages show new theme
```

## Testing Steps

1. Visit `/` (Home)
2. Click Moon/Sun icon
3. Navigate to `/pricing` → Theme persists ✓
4. Navigate to `/contact` → Theme still there ✓
5. Refresh page → Theme restored ✓

## LocalStorage

```javascript
// Store theme
localStorage.setItem('theme', 'light')

// Retrieve theme
const savedTheme = localStorage.getItem('theme') // 'light'

// Clear theme (resets to default)
localStorage.removeItem('theme')
```

## Benefits

| Feature | Local Theme | Global Theme |
|---------|------------|--------------|
| Same theme everywhere | ❌ | ✅ |
| Persists on refresh | ❌ | ✅ |
| One toggle for all | ❌ | ✅ |
| Easy to extend | ❌ | ✅ |
| Shared state | ❌ | ✅ |

## CSS Class Management

ThemeContext automatically updates:

```javascript
document.documentElement.classList // Contains 'dark' or 'light'
```

This enables global CSS if needed:

```css
html.dark { background: #0F172A; }
html.light { background: white; }
```

---

✨ **Now your entire app has a unified, persistent theme system!**

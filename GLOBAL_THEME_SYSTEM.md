# Global Theme System Implementation

## Overview
Implemented a **global theme system** that allows users to toggle between dark and light mode on any page, and the preference persists across the entire application.

## How It Works

### 1. **Theme Context** (`src/contexts/ThemeContext.tsx`)
- Centralized theme state management using React Context
- Provides `theme` ('dark' or 'light') and `toggleTheme()` function
- Automatically persists theme to localStorage
- Updates document classes for global styling

### 2. **Theme Provider** (in `src/main.tsx`)
- Wraps the entire application
- Makes theme available to all pages and components
- Restores saved theme preference on app load

### 3. **Navigation Component** (updated)
- Uses `useTheme()` hook to access global theme
- Toggle button updates theme globally
- All pages inherit the new theme instantly

### 4. **All Pages** (LandingPage, PricingPage, ContactPage)
- Use `useTheme()` hook to get current theme
- All theme checks updated to use `theme === 'dark'` format
- All pages automatically respond to global theme changes

## Key Features

✅ **Truly Global**: Click toggle on ANY page → applies to ALL pages  
✅ **Persistent**: Theme preference saved to localStorage  
✅ **Automatic Recovery**: Loads saved theme preference on page refresh  
✅ **Real-time Updates**: No page reload needed - instant theme change  
✅ **Complete Coverage**: Works across Home, Pricing, Contact Us, and beyond

## File Structure

```
frontend/src/
├── contexts/
│   └── ThemeContext.tsx          ← New: Global theme state
├── components/
│   └── Navigation.tsx            ← Updated: Uses useTheme hook
├── pages/
│   ├── LandingPage.tsx          ← Updated: Uses useTheme hook
│   ├── PricingPage.tsx          ← Updated: Uses useTheme hook
│   └── ContactPage.tsx          ← Updated: Uses useTheme hook
└── main.tsx                      ← Updated: Wraps app with ThemeProvider
```

## Usage Example

```tsx
import { useTheme } from '../contexts/ThemeContext'

function MyComponent() {
  const { theme, toggleTheme } = useTheme()
  
  return (
    <div className={theme === 'dark' ? 'bg-[#0F172A]' : 'bg-white'}>
      <button onClick={toggleTheme}>
        Switch to {theme === 'dark' ? 'Light' : 'Dark'} Mode
      </button>
    </div>
  )
}
```

## Data Flow

```
User clicks toggle → toggleTheme() called
    ↓
Theme context updated (dark/light)
    ↓
localStorage.setItem('theme', newTheme)
    ↓
Document classes updated
    ↓
All pages re-render with new theme
```

## Testing

To verify it works:

1. Go to Home page (`/`)
2. Click the Moon/Sun icon in navigation
3. Page switches to light/dark mode
4. Navigate to `/pricing` → theme is preserved
5. Navigate to `/contact` → theme is still the same
6. Refresh page → theme persists

## localStorage Structure

```javascript
localStorage.getItem('theme') // returns 'dark' or 'light'
```

On first visit:
- Defaults to 'dark' mode
- Stored in localStorage for future visits

## CSS Classes Applied

The ThemeContext automatically manages:

```javascript
// Dark mode
document.documentElement.classList.add('dark')
document.documentElement.classList.remove('light')

// Light mode
document.documentElement.classList.add('light')
document.documentElement.classList.remove('dark')
```

This allows for global CSS selectors if needed:
```css
:root.dark { /* dark mode styles */ }
:root.light { /* light mode styles */ }
```

## Next Steps / Enhancements

1. **Sync across tabs**: Use storage events to sync theme across browser tabs
2. **System preference detection**: Auto-detect OS dark/light preference
3. **Scheduled switching**: Auto-switch at specific times (e.g., sunset)
4. **More themes**: Extend to support multiple color schemes (ocean, forest, etc.)
5. **Animation**: Add smooth transitions when switching themes

## Troubleshooting

**Theme not persisting?**
- Check browser's localStorage is enabled
- Clear localStorage: `localStorage.clear()` and retry

**Theme not applying?**
- Ensure component imports `useTheme` hook
- Check component is wrapped by app layout with ThemeProvider

**Toggle button not responding?**
- Verify Navigation component is rendering
- Check browser console for errors

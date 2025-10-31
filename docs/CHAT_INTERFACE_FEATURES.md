# Dynamic Pricing AI - Chat Interface Feature Summary

## Overview
Multi-agent LLM-powered dynamic pricing system with an advanced chat interface built using React, TypeScript, and modern UI libraries.

## Core Architecture

### Agents
1. **UIA (User Interaction Agent)** 👤 - Routes requests and ensures safety
2. **POA (Price Optimization Agent)** 🎯 - Main orchestrator for pricing decisions
3. **DCA (Data Collector Agent)** 📊 - Gathers market and competitor data
4. **ANA (Alert & Notification Agent)** 🔔 - Monitors system and sends notifications

### Tech Stack
- **Frontend**: React 18 + TypeScript + Vite
- **State Management**: Zustand
- **Animations**: React Spring + Auto-animate
- **UI Components**: shadcn/ui + Tailwind CSS
- **Charts**: Chart.js
- **Backend**: FastAPI (Python) on port 8000
- **Frontend Dev Server**: Vite on port 5173

## Features Implemented

### ✅ 1. Authentication & User Management
- JWT-based authentication with persistent sessions
- Login/Register functionality
- User profile display in sidebar
- Logout with confirmation dialog
- Token stored in localStorage

### ✅ 2. Thread Management
- **Create/Delete/Rename threads**
- Persistent thread list in sidebar
- Current thread highlighting
- Thread switching with smooth transitions
- Export thread to JSON (Ctrl+Shift+E)
- Import thread from JSON (Ctrl+Shift+I)
- Thread title display with truncation

### ✅ 3. Message System
- **Real-time streaming** via Server-Sent Events (SSE)
- Message editing with branching (creates new conversation path)
- Message deletion with confirmation
- Copy message to clipboard (hover + C or Ctrl+C)
- Edit last user message with ArrowUp when composer is empty
- Message roles: user, assistant, system

### ✅ 4. Conversation Branching
- **Branch Navigator Component** - Shows when messages have multiple children
- Visual indicators for branch points (🔀 icon)
- Navigate between sibling branches with arrow buttons
- Branch counter showing "Branch X/Y"
- Quick jump buttons to explore different branches
- Keyboard shortcuts: Ctrl+[ (prev branch), Ctrl+] (next branch)
- Highlight animation when navigating to messages
- "Branch" button to create alternative conversation paths

### ✅ 5. Agent Visualization
- **AgentBadge Component** with color-coded badges
  - UIA: Blue 👤
  - POA: Purple 🎯
  - DCA: Green 📊
  - ANA: Orange 🔔
- Two variants: `pill` (inline) and `circle` (compact)
- Active agent pulsing animation during streaming
- Tooltips with full agent descriptions
- AgentBadgeGroup for managing multiple agents
- Live agent indicators in header during streaming

### ✅ 6. Conversation Summaries
- **SummaryIndicator Component** - Shows when threads have summaries
- Badge in sidebar thread list (📝 with count)
- Summary button in main chat header
- Modal dialog to view all summaries
- Summary checkpoints with message IDs
- Timestamps for each summary
- Fetches from `/api/threads/{id}/summaries` endpoint

### ✅ 7. Metadata & Analytics
- **MetadataTooltip Component** - Displays message metadata
- Token usage (input/output)
- Cost tracking (USD)
- API call counts
- Model information
- Provider information
- Agent activation counts
- Tool usage statistics
- Timestamps (toggleable)

### ✅ 8. Thinking Tokens
- **ThinkingTokens Component** - Shows AI reasoning process
- Collapsible panel
- Syntax-highlighted code blocks
- Markdown rendering
- Smooth expand/collapse animation
- Toggle via settings

### ✅ 9. Price Visualization
- **PriceChart Component** using Chart.js
- Line chart with price history
- Dark/light theme support
- Displays when `metadata.priceData` is present
- SKU identification
- Responsive sizing

### ✅ 10. Settings Modal
- **SettingsModal Component** with multiple sections
- Theme toggle (dark/light)
- Streaming mode (SSE/polling)
- User mode (user/developer)
- Show thinking tokens toggle
- Show timestamps toggle
- Show model tags toggle
- Show metadata panel toggle
- Persistent settings (synced with backend)
- Keyboard shortcut: Ctrl+,

### ✅ 11. Keyboard Shortcuts
#### General
- `Escape` - Stop streaming
- `Ctrl+,` - Open settings
- `?` - Show help modal

#### Threads
- `Ctrl+N` - New thread
- `Ctrl+Shift+E` - Export thread
- `Ctrl+Shift+I` - Import thread

#### Messaging
- `Enter` - Send message (Shift+Enter for new line)
- `ArrowUp` - Edit last message (when composer empty)

#### Message Actions (hover over message)
- `C` or `Ctrl+C` - Copy message
- `E` - Edit message (user messages only)
- `Delete` - Delete message

#### Branch Navigation
- `Ctrl+[` - Previous branch
- `Ctrl+]` - Next branch

### ✅ 12. UI/UX Enhancements
- **Animations**: Smooth transitions with React Spring
- **Auto-animate**: Lists and dynamic content
- **Toast notifications**: Success/error/info messages
- **Confirmation dialogs**: For destructive actions
- **Prompt modals**: For text input (rename, edit, etc.)
- **Help modal**: Categorized keyboard shortcuts
- **Collapsible sidebar**: Persistent state
- **Hover effects**: Message rows, buttons, badges
- **Scroll behavior**: Auto-scroll to bottom, smooth navigation
- **Loading states**: Spinners, streaming indicators
- **Empty states**: Helpful messages when no content

### ✅ 13. Accessibility
- ARIA labels for all interactive elements
- Role attributes (article, log, status)
- aria-live regions for dynamic content
- aria-busy states during streaming
- Keyboard navigation support
- Focus management in modals

## File Structure

```
frontend/src/
├── components/
│   ├── ui/                    # shadcn/ui components
│   │   ├── alert-dialog.tsx
│   │   ├── button.tsx
│   │   ├── collapsible.tsx
│   │   ├── dialog.tsx
│   │   ├── switch.tsx
│   │   └── tooltip.tsx
│   ├── AgentBadge.tsx         # Agent visualization
│   ├── BranchNavigator.tsx    # Branch navigation & tree
│   ├── MetadataTooltip.tsx    # Message metadata display
│   ├── PriceChart.tsx         # Price data visualization
│   ├── SettingsModal.tsx      # User settings
│   ├── SummaryIndicator.tsx   # Conversation summaries
│   └── ThinkingTokens.tsx     # AI reasoning display
├── lib/
│   ├── conversationExport.ts  # Export/import utilities
│   ├── types.ts               # TypeScript definitions
│   └── utils.ts               # Utility functions
├── pages/
│   ├── AuthPage.tsx           # Login/Register
│   ├── ChatPage.tsx           # Main chat interface
│   └── LandingPage.tsx        # Welcome page
├── App.tsx                    # Main app component
├── main.tsx                   # Entry point
└── styles.css                 # Global styles + Tailwind
```

## API Endpoints Used

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - Login user
- `POST /api/logout` - Logout user
- `GET /api/me` - Get current user info

### Threads
- `GET /api/threads` - List all threads
- `POST /api/threads` - Create new thread
- `PATCH /api/threads/{id}` - Rename thread
- `DELETE /api/threads/{id}` - Delete thread
- `GET /api/threads/{id}/export` - Export thread JSON
- `POST /api/threads/import` - Import thread from JSON
- `GET /api/threads/{id}/summaries` - Get conversation summaries

### Messages
- `GET /api/threads/{id}/messages` - Get all messages in thread
- `POST /api/threads/{id}/messages` - Send new message
- `POST /api/threads/{id}/messages/stream` - Stream response (SSE)
- `PATCH /api/messages/{id}` - Edit message (creates branch)
- `DELETE /api/messages/{id}` - Delete message

### Settings
- `GET /api/settings` - Get user settings
- `POST /api/settings` - Update user settings

## Conversation Branching Details

### How It Works
1. When a user message is edited, a new branch is created
2. The edited message becomes a sibling of the original
3. Both branches share the same parent message
4. BranchNavigator detects and displays:
   - Branch points (messages with multiple children)
   - Sibling relationships (alternative messages)
   - Navigation controls

### Branch Indicators
- **Branch Point** (🔀): Message has multiple children (conversation forks here)
- **Sibling Counter** (⸬): Current branch X of Y alternatives
- **Quick Jump Buttons**: Navigate to specific branches (#1, #2, #3...)
- **Arrow Navigation**: Move between sibling branches

### Navigation Features
- Click branch buttons to jump to specific child messages
- Use arrow buttons to cycle through siblings
- Keyboard shortcuts for quick navigation
- Smooth scroll and highlight animation
- Persistent branch selection per conversation

## Summary System Details

### Backend Integration
- Summaries stored in `ChatSummary` table
- Each summary linked to a thread and message ID
- `upto_message_id` indicates the conversation checkpoint
- Summaries can be generated by agents or manually

### UI Components
- **Badge in Sidebar**: Shows count of summaries per thread
- **Badge in Header**: Quick access for current thread
- **Modal Dialog**: Full summary view with:
  - Checkpoint numbers
  - Message ID references
  - Timestamps
  - Full summary content
  - Scrollable for long histories

### Use Cases
- Quick review of long conversations
- Jump to specific conversation points
- Understand context before resuming
- Track conversation evolution

## Theme System

### Dark Mode (Default)
- Deep blue gradient background
- High contrast text
- Glowing accents
- Indigo primary color

### Light Mode
- Soft white/blue gradient
- Comfortable for bright environments
- Same UI structure
- Toggle via Theme button or Settings

## Development Workflow

### Running the Application
1. **Backend**: `cd backend && uvicorn main:app --reload --port 8000`
2. **Frontend**: `cd frontend && npm run dev`
3. Access: `http://localhost:5173`

### Building for Production
```bash
cd frontend
npm run build
```

### Environment Variables
- Backend uses `.env` file
- Frontend uses `import.meta.env` for Vite
- JWT tokens stored in localStorage

## Testing Checklist

### Core Functionality
- [ ] Sign in/Sign out
- [ ] Create/Delete/Rename threads
- [ ] Send messages and receive responses
- [ ] Edit messages (creates branches)
- [ ] Delete messages
- [ ] Copy messages
- [ ] Branch from any message
- [ ] Branch indicator appears
- [ ] Navigate between branches with arrows
- [ ] Quick jump to specific branches
- [ ] Keyboard shortcuts (Ctrl+[ and Ctrl+])

### Summaries
- [ ] Summary indicator appears in sidebar
- [ ] Click to view summaries modal
- [ ] Multiple summaries displayed correctly
- [ ] Timestamps and message IDs shown

### Agents
- [ ] Agent badges display during streaming
- [ ] Active agent pulses
- [ ] Tooltips show descriptions
- [ ] Multiple agents can be active

### Settings
- [ ] Theme toggle works
- [ ] Settings persist after refresh
- [ ] All toggles affect UI correctly
- [ ] Modal opens with Ctrl+,

### Keyboard Shortcuts
- [ ] Ctrl+N creates new thread
- [ ] Ctrl+Shift+E exports thread
- [ ] Ctrl+Shift+I imports thread
- [ ] Escape stops streaming
- [ ] ArrowUp edits last message
- [ ] Help modal shows all shortcuts

### Charts & Metadata
- [ ] Price charts render when data present
- [ ] Thinking tokens expand/collapse
- [ ] Metadata tooltip shows all info
- [ ] Theme affects chart colors

## Future Enhancements (Not Yet Implemented)

1. **Mobile Responsiveness**
   - Collapsed sidebar on mobile
   - Touch-friendly controls
   - Responsive layout breakpoints

2. **Advanced Branch Visualization**
   - Tree diagram in sidebar
   - Visual branch count indicators
   - Branch naming/tagging

3. **Search & Filtering**
   - Search within threads
   - Filter by agent
   - Filter by date range

4. **Performance Optimization**
   - Virtual scrolling for long threads
   - Lazy loading of old messages
   - Code splitting for faster load

5. **Collaboration Features**
   - Share threads with other users
   - Multi-user real-time editing
   - Comments on messages

6. **Export Options**
   - Export as PDF
   - Export as Markdown
   - Selective export (date range, branches)

## Known Issues

1. Bundle size warning (>500KB) - consider code splitting
2. No mobile optimization yet
3. Summary generation not triggered from UI (backend-only)
4. No visual branch tree in sidebar (only inline indicators)

## Browser Compatibility

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support (ES2020+)
- Mobile: ⚠️ Basic support (needs optimization)

## Dependencies

### Production
- react ^18.3.1
- react-dom ^18.3.1
- zustand ^5.0.2
- @react-spring/web ^9.7.5
- @formkit/auto-animate ^0.8.2
- chart.js ^4.4.8
- react-chartjs-2 ^5.3.0
- @radix-ui components (various)
- tailwindcss ^3.4.20

### Development
- typescript ~5.6.2
- vite ^5.4.20
- @vitejs/plugin-react ^4.3.4
- tailwindcss ^3.4.20
- postcss ^8.4.49

---

**Status**: ✅ Fully Functional
**Last Updated**: January 2025
**Version**: 1.0.0

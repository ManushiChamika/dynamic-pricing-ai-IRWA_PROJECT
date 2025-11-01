# Frontend Tech Decisions

## Research Summary (2024)
Based on comprehensive Reddit r/reactjs and r/webdev community research, our current stack aligns well with 2024 best practices for chat-focused applications.

## Final Recommended Stack

### Core Foundation
- **Framework**: React 18 + TypeScript + Vite
- **Animation**: React Spring + AutoAnimate
- **UI Components**: shadcn/ui + Tailwind CSS + Radix UI

### State Management
- **Global State**: Zustand (optimal for chat apps per community consensus)
- **Server State**: TanStack Query 
- **Form State**: React Hook Form
- **Alternatives Considered**: Redux Toolkit (better for large teams), Jotai (atomic state)

### Real-time Communication (UPDATED)
- **Bidirectional**: Socket.IO (chat messages, user interactions)
- **Unidirectional**: EventSource (real-time price feeds, alerts)
- **Why Both**: EventSource perfect for pricing streams, Socket.IO for chat
- **Alternatives Considered**: Native WebSockets, Pusher, PartyKit

### Data Visualization (UPDATED)
- **Real-time Charts**: Chart.js + react-chartjs-2 (best performance for live data)
- **Analytics Charts**: Recharts (React-native, good for static analysis)
- **Advanced Viz**: D3.js (when needed)
- **Why Hybrid**: Chart.js excels at real-time, Recharts better for complex layouts

### Development Tools
- **Linting**: ESLint + Prettier
- **Testing**: Vitest + Playwright
- **Build**: Vite

## Key Community Insights

### State Management
- Zustand vs Redux becomes similar when using slices/proper structure
- Community strongly prefers Zustand for medium-complexity chat apps
- TanStack Query reduces need for global state by handling server state

### Real-time Architecture
- EventSource recommended for one-way price feeds (lower overhead)
- Socket.IO still dominates for reliability and fallback support
- Hybrid approach (Socket.IO + EventSource) ideal for pricing chat apps

### Chart Libraries
- Chart.js voted #1 for real-time performance in 2024
- Recharts still preferred for React-specific static charts
- Community warns against React chart libraries being "problematic" - Chart.js more reliable

## Context
Chat-focused dynamic pricing AI platform requiring smooth message animations and real-time price updates. Current backend: FastAPI + Python with MCP protocol.

## Key Benefits
- **React Spring**: No re-renders during animations, smooth value interpolations
- **Zustand**: Minimal boilerplate, perfect for chat state management
- **Chart.js**: Superior performance for real-time price chart updates
- **EventSource**: Lightweight, efficient for one-way price data streams
- **shadcn/ui**: Beautiful, accessible components with Tailwind integration
import React, { Suspense, lazy } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from './contexts/ThemeContext.tsx'
import './styles.css'
import { setUnauthorizedHandler } from './lib/apiClient'
import { useToasts } from './stores/toastStore'
import { useAuth } from './stores/authStore'

// Register a global 401 handler
setUnauthorizedHandler(() => {
  try {
    useAuth.getState().setToken(null)
  } catch {
    /* ignore */
  }
  try {
    useToasts.getState().push({ type: 'error', text: 'Session expired. Please sign in again.' })
  } catch {
    /* ignore */
  }
})

const qc = new QueryClient()

const LandingPage = lazy(() =>
  import('./pages/LandingPage').then((m) => ({ default: m.LandingPage }))
)
const AuthPage = lazy(() => import('./pages/AuthPage').then((m) => ({ default: m.AuthPage })))
const ChatPage = lazy(() => import('./pages/ChatPage').then((m) => ({ default: m.ChatPage })))
const PricingPage = lazy(() =>
  import('./pages/PricingPage').then((m) => ({ default: m.PricingPage }))
)
const ContactPage = lazy(() =>
  import('./pages/ContactPage').then((m) => ({ default: m.ContactPage }))
)
const App = lazy(() => import('./App'))

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <QueryClientProvider client={qc}>
        <BrowserRouter>
          <Suspense fallback={<div className="loading">Loading…</div>}>
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/pricing" element={<PricingPage />} />
              <Route path="/contact" element={<ContactPage />} />
              <Route path="/auth" element={<AuthPage />} />
              <Route
                path="/chat"
                element={
                  <ChatPage>
                    <App />
                  </ChatPage>
                }
              />
              <Route
                path="/chat/:threadId"
                element={
                  <ChatPage>
                    <App />
                  </ChatPage>
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  </React.StrictMode>
)

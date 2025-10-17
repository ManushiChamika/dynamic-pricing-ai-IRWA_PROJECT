import React, { useEffect, useState } from 'react'
import { Button } from './ui/button'
import { SummaryIndicator } from './SummaryIndicator'
import { useThreadList, useCurrentThread, useThreadActions } from '../stores/threadStore'
import { useConfirm } from '../stores/confirmStore'
import { useAuthUser, useAuthActions } from '../stores/authStore'
import { useSettings } from '../stores/settingsStore'
import { useToasts } from '../stores/toastStore'

export function Sidebar() {
  const threads = useThreadList()
  const currentId = useCurrentThread()
  const { setCurrent, refresh, createThread } = useThreadActions()
  const [collapsed, setCollapsed] = useState(localStorage.getItem('sidebarCollapsed') === '1')
  const user = useAuthUser()
  const { logout } = useAuthActions()

  useEffect(() => {
    refresh().then(() => {
      const last = Number(localStorage.getItem('lastThreadId') || '')
      if (last) setCurrent(last)
    })
  }, [refresh, setCurrent])

  useEffect(() => {
    document.querySelector('.sidebar')?.classList.toggle('collapsed', collapsed)
  }, [collapsed])

  const handleLogout = async () => {
    useConfirm.getState().openConfirm({
      title: 'Sign out?',
      description: 'You will need to sign in again to access the chat.',
      confirmText: 'Sign Out',
      onConfirm: async () => {
        try {
          await logout()
        } catch {
          /* ignore */
        }
        window.location.href = '/auth'
      },
    })
  }

  return (
    <aside
      className={`${collapsed ? 'w-14' : 'w-[280px]'} border-r border-border p-4 overflow-auto bg-[rgba(17,24,39,0.85)] backdrop-blur-3xl transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]`}
      aria-label="Threads sidebar"
    >
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
          <Button
            variant="ghost"
            size="icon"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            onClick={() =>
              setCollapsed((c) => {
                const n = !c
                localStorage.setItem('sidebarCollapsed', n ? '1' : '0')
                return n
              })
            }
            aria-expanded={!collapsed}
            aria-controls="thread-list"
          >
            {collapsed ? '⮞' : '⮜'}
          </Button>
          <Button onClick={() => createThread()} aria-label="Create new thread" style={{ flex: 1 }}>
            + New Chat
          </Button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', marginBottom: 16 }}>
          <ul id="thread-list" style={{ listStyle: 'none', margin: 0, padding: 0 }}>
            {threads.map((t) => (
              <li
                key={t.id}
                style={{
                  padding: '10px 12px',
                  borderRadius: '12px',
                  background: currentId === t.id ? 'var(--accent-color)' : 'transparent',
                  cursor: 'pointer',
                  marginBottom: '6px',
                  transition: 'all 0.2s ease',
                  color: currentId === t.id ? 'white' : 'var(--fg)',
                  fontWeight: currentId === t.id ? 500 : 400,
                  border: '1px solid',
                  borderColor: currentId === t.id ? 'transparent' : 'transparent',
                }}
                onClick={() => setCurrent(t.id)}
                aria-current={currentId === t.id ? 'true' : undefined}
                onMouseEnter={(e) => {
                  if (currentId !== t.id) {
                    ;(e.currentTarget as HTMLElement).style.background = 'var(--accent-light)'
                    ;(e.currentTarget as HTMLElement).style.borderColor = 'var(--border-color)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (currentId !== t.id) {
                    ;(e.currentTarget as HTMLElement).style.background = 'transparent'
                    ;(e.currentTarget as HTMLElement).style.borderColor = 'transparent'
                  }
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: 8,
                  }}
                >
                  <span
                    style={{
                      flex: 1,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {t.title || `Thread #${t.id}`}
                  </span>
                  <span onClick={(e) => e.stopPropagation()}>
                    <SummaryIndicator threadId={t.id} />
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div
          style={{
            borderTop: '1px solid var(--border-color)',
            paddingTop: 12,
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}
        >
          <Button
            variant="outline"
            onClick={() => useSettings.getState().setSettingsOpen(true)}
            className="flex items-center gap-2"
            aria-label="Open settings"
          >
            <span>⚙️</span>
            <span>Settings</span>
          </Button>

          {user && (
            <div
              style={{
                padding: '10px 12px',
                background: 'var(--panel)',
                border: '1px solid var(--border-color)',
                borderRadius: '12px',
                fontSize: '13px',
              }}
            >
              <div style={{ opacity: 0.7, marginBottom: 4 }}>Signed in as</div>
              <div
                style={{
                  fontWeight: 500,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {user.full_name || user.email}
              </div>
            </div>
          )}

          <Button
            variant="destructive"
            onClick={handleLogout}
            className="flex items-center gap-2"
            aria-label="Sign out"
          >
            <span>🚪</span>
            <span>Sign Out</span>
          </Button>
        </div>
      </div>
    </aside>
  )
}

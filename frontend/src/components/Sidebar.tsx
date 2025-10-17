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
      className={`sidebar ${collapsed ? 'w-14' : 'w-[280px]'} border-r border-border p-[var(--space-4)] overflow-auto bg-[rgba(17,24,39,0.85)] backdrop-blur-3xl transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]`}
      aria-label="Threads sidebar"
    >
      <div className="flex flex-col h-full">
        <div className="flex gap-[var(--space-2)] mb-[var(--space-4)]">
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
          <Button onClick={() => createThread()} aria-label="Create new thread" className="flex-1">
            + New Chat
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto mb-[var(--space-4)]">
          <ul id="thread-list" className="list-none m-0 p-0">
            {threads.map((t) => (
              <li
                key={t.id}
                className="px-3 py-2.5 rounded-lg cursor-pointer mb-1.5 transition-all duration-200 border"
                style={{
                  background: currentId === t.id ? 'var(--accent-color)' : 'transparent',
                  color: currentId === t.id ? 'white' : 'var(--fg)',
                  fontWeight: currentId === t.id ? 500 : 400,
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
                <div className="flex items-center justify-between gap-2">
                  <span className="flex-1 overflow-hidden text-ellipsis whitespace-nowrap text-[var(--font-sm)]">
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

        <div className="border-t border-[var(--border-color)] pt-[var(--space-3)] flex flex-col gap-[var(--space-2)]">
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
            <div className="px-3 py-2.5 bg-[var(--panel)] border border-[var(--border-color)] rounded-lg text-[var(--font-sm)]">
              <div className="opacity-70 mb-1">Signed in as</div>
              <div className="font-medium overflow-hidden text-ellipsis whitespace-nowrap">
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

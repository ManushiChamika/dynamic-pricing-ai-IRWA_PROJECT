import React, { useEffect, useState, useMemo, startTransition } from 'react'
import { Virtuoso } from 'react-virtuoso'
import { Button } from './ui/button'
import { ThreadItem } from './sidebar/ThreadItem'
import {
  useThreadList,
  useCurrentThread,
  useThreadActions,
  useDraftId,
} from '../stores/threadStore'
import { useConfirm } from '../stores/confirmStore'
import { useAuthUser, useAuthActions } from '../stores/authStore'
import { useSettings } from '../stores/settingsStore'
import { useCatalogStore } from '../stores/catalogStore'
import {
  Package,
  Settings,
  LogOut,
  MessageSquarePlus,
  ChevronLeft,
  ChevronRight,
  Home,
} from 'lucide-react'

export function Sidebar() {
  const threads = useThreadList()
  const currentId = useCurrentThread()
  const draftId = useDraftId()
  const { setCurrent, refresh, createDraftThread } = useThreadActions()
  const [collapsed, setCollapsed] = useState(localStorage.getItem('sidebarCollapsed') === '1')
  const user = useAuthUser()
  const { logout } = useAuthActions()

  const allItems = useMemo(() => {
    const items = []
    if (draftId) {
      items.push({ id: draftId, title: 'New Chat (unsaved)', isDraft: true })
    }
    items.push(...threads.map((t) => ({ id: t.id, title: t.title || `Thread #${t.id}`, isDraft: false })))
    return items
  }, [draftId, threads])

  useEffect(() => {
    refresh().then(() => {
      const last = Number(localStorage.getItem('lastThreadId') || '')
      if (last) {
        setCurrent(last)
      } else if (!currentId) {
        createDraftThread()
      }
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
      className={`sidebar ${collapsed ? 'w-14' : 'w-[280px]'} border-r border-border p-[var(--space-4)] overflow-auto bg-[var(--panel)] backdrop-blur-3xl transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]`}
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
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </Button>
          {!collapsed && (
            <Button
              onClick={() => createDraftThread()}
              aria-label="Create new thread"
              className="flex-1"
            >
              <MessageSquarePlus className="w-4 h-4 mr-2" />
              New Chat
            </Button>
          )}
        </div>

        <div className="flex-1 mb-[var(--space-4)]" id="thread-list">
          <Virtuoso
            data={allItems}
            totalCount={allItems.length}
            itemContent={(index, item) => (
              <ThreadItem
                key={item.id}
                id={item.id}
                title={item.title}
                isActive={currentId === item.id}
                isDraft={item.isDraft}
                onSelect={() => startTransition(() => setCurrent(item.id))}
              />
            )}
            style={{ height: '100%' }}
          />
        </div>

        <div className="border-t border-[var(--border-color)] pt-[var(--space-3)] flex flex-col gap-[var(--space-2)]">
          <Button
            variant="outline"
            onClick={() => (window.location.href = '/')}
            className={`flex items-center ${collapsed ? 'justify-center' : 'gap-2'} hover:bg-indigo-500/10 hover:border-indigo-500/30 transition-colors`}
            aria-label="Back to home"
          >
            <Home className="w-4 h-4" />
            {!collapsed && <span>Home</span>}
          </Button>

          <Button
            variant="outline"
            onClick={() => useCatalogStore.getState().setCatalogOpen(true)}
            className={`flex items-center ${collapsed ? 'justify-center' : 'gap-2'} hover:bg-indigo-500/10 hover:border-indigo-500/30 transition-colors`}
            aria-label="Open catalog"
          >
            <Package className="w-4 h-4" />
            {!collapsed && <span>Catalog</span>}
          </Button>

          <Button
            variant="outline"
            onClick={() => useSettings.getState().setSettingsOpen(true)}
            className={`flex items-center ${collapsed ? 'justify-center' : 'gap-2'}`}
            aria-label="Open settings"
          >
            <Settings className="w-4 h-4" />
            {!collapsed && <span>Settings</span>}
          </Button>

          {user && !collapsed && (
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
            className={`flex items-center ${collapsed ? 'justify-center' : 'gap-2'}`}
            aria-label="Sign out"
          >
            <LogOut className="w-4 h-4" />
            {!collapsed && <span>Sign Out</span>}
          </Button>
        </div>
      </div>
    </aside>
  )
}

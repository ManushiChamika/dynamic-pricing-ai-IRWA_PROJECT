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
  Sparkles,
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
      items.push({ id: draftId, title: 'New Chat (unsaved)', isDraft: true, updated_at: '' })
    }
    items.push(
      ...threads.map((t) => ({
        id: t.id,
        title: t.title || 'Untitled',
        isDraft: false,
        updated_at: t.updated_at,
      }))
    )
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
  }, [refresh, setCurrent, createDraftThread, currentId])

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
      className={`sidebar ${collapsed ? 'w-16' : 'w-64'} border-r bg-background overflow-auto transition-all duration-300`}
      aria-label="Threads sidebar"
    >
      <div className="flex flex-col h-full p-3 gap-3">
        <div className="flex gap-2">
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
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
          {!collapsed && (
            <Button
              onClick={() => createDraftThread()}
              aria-label="Create new thread"
              variant="gradient"
              size="lg"
              className="flex-1"
            >
              <Sparkles className="h-5 w-5" />
              <span className="text-[0.9375rem] tracking-wide">New Chat</span>
            </Button>
          )}
        </div>

        <div className="flex-1 -mx-1" id="thread-list">
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
                updatedAt={item.updated_at}
                onSelect={() => startTransition(() => setCurrent(item.id))}
              />
            )}
            style={{ height: '100%', padding: '0 4px' }}
          />
        </div>

        <div className="border-t pt-3 flex flex-col gap-1">
          <Button
            variant="ghost"
            onClick={() => (window.location.href = '/')}
            className={`justify-start ${collapsed ? 'px-2' : ''}`}
            aria-label="Back to home"
          >
            <Home className="h-4 w-4" />
            {!collapsed && <span className="ml-2">Home</span>}
          </Button>

          <Button
            variant="ghost"
            onClick={() => useCatalogStore.getState().setCatalogOpen(true)}
            className={`justify-start ${collapsed ? 'px-2' : ''}`}
            aria-label="Open catalog"
          >
            <Package className="h-4 w-4" />
            {!collapsed && <span className="ml-2">Catalog</span>}
          </Button>

          <Button
            variant="ghost"
            onClick={() => useSettings.getState().setSettingsOpen(true)}
            className={`justify-start ${collapsed ? 'px-2' : ''}`}
            aria-label="Open settings"
          >
            <Settings className="h-4 w-4" />
            {!collapsed && <span className="ml-2">Settings</span>}
          </Button>

          {user && !collapsed && (
            <div className="mt-2 px-3 py-2 bg-muted/50 rounded-lg text-xs">
              <div className="text-muted-foreground mb-1">Signed in as</div>
              <div className="font-medium overflow-hidden text-ellipsis whitespace-nowrap">
                {user.full_name || user.email}
              </div>
            </div>
          )}

          <Button
            variant="ghost"
            onClick={handleLogout}
            className={`justify-start text-destructive hover:text-destructive hover:bg-destructive/10 ${collapsed ? 'px-2' : ''}`}
            aria-label="Sign out"
          >
            <LogOut className="h-4 w-4" />
            {!collapsed && <span className="ml-2">Sign Out</span>}
          </Button>
        </div>
      </div>
    </aside>
  )
}

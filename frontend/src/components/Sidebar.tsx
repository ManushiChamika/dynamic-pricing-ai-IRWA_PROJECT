import React, { useEffect, useMemo, startTransition } from 'react'
import { useNavigate } from 'react-router-dom'
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
import { useSidebar } from '../stores/sidebarStore'
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
  const navigate = useNavigate()
  const threads = useThreadList()
  const currentId = useCurrentThread()
  const draftId = useDraftId()
  const { setCurrent, refresh, createDraftThread } = useThreadActions()
  const { collapsed, toggleCollapsed } = useSidebar()
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
      if (last && !currentId) {
        setCurrent(last)
      } else if (!currentId) {
        createDraftThread()
      }
    })
  }, [refresh, setCurrent, createDraftThread])

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
      className={`sidebar ${collapsed ? 'w-16' : 'w-64'} border-r bg-muted/20 transition-all duration-300 overflow-hidden`}
      aria-label="Threads sidebar"
    >
      <div className={`flex flex-col h-full gap-3 ${collapsed ? 'p-2 items-center' : 'p-3'}`}>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="icon"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            onClick={toggleCollapsed}
            aria-expanded={!collapsed}
            aria-controls="thread-list"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
          {!collapsed && (
            <Button
              onClick={() => {
                navigate('/chat')
                createDraftThread()
              }}
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

        {!collapsed ? (
          <div className="flex-1 -mx-1 border-y py-2 bg-background/50" id="thread-list">
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
                  collapsed={false}
                />
              )}
              style={{ height: '100%', padding: '0 4px' }}
            />
          </div>
        ) : (
          <div className="flex-1 overflow-auto border-y py-2 bg-background/50 flex items-start justify-center" id="thread-list">
            <div className="space-y-1">
              {allItems.map((item) => (
                <ThreadItem
                  key={item.id}
                  id={item.id}
                  title={item.title}
                  isActive={currentId === item.id}
                  isDraft={item.isDraft}
                  updatedAt={item.updated_at}
                  onSelect={() => startTransition(() => setCurrent(item.id))}
                  collapsed={true}
                />
              ))}
            </div>
          </div>
        )}

        <div className="border-t pt-3 flex flex-col gap-1 bg-muted/10 -mx-3 px-3 -mb-3 pb-3">
            <Button
              variant="ghost"
              onClick={() => (window.location.href = '/')}
              className={collapsed ? 'justify-center' : 'justify-start'}
              size={collapsed ? 'icon' : 'default'}
              aria-label="Back to home"
            >
              <Home className="h-4 w-4" />
              {!collapsed && <span className="ml-2">Home</span>}
            </Button>

            <Button
              variant="ghost"
              onClick={() => useCatalogStore.getState().setCatalogOpen(true)}
              className={collapsed ? 'justify-center' : 'justify-start'}
              size={collapsed ? 'icon' : 'default'}
              aria-label="Open catalog"
            >
              <Package className="h-4 w-4" />
              {!collapsed && <span className="ml-2">Catalog</span>}
            </Button>

            <Button
              variant="ghost"
              onClick={() => useSettings.getState().setSettingsOpen(true)}
              className={collapsed ? 'justify-center' : 'justify-start'}
              size={collapsed ? 'icon' : 'default'}
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
              className={collapsed ? 'justify-center text-destructive hover:text-destructive hover:bg-destructive/10' : 'justify-start text-destructive hover:text-destructive hover:bg-destructive/10'}
              size={collapsed ? 'icon' : 'default'}
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

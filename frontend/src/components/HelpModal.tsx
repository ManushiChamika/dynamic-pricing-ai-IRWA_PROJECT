import { Button } from './ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog'
import { useHelp } from '../stores/helpStore'

export function HelpModal() {
  const { open } = useHelp()

  const Row = ({ k, d }: { k: string; d: string }) => (
    <div className="flex justify-between gap-3">
      <code className="opacity-90">{k}</code>
      <span className="opacity-85">{d}</span>
    </div>
  )

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && useHelp.getState().close()}>
      <DialogContent className="sm:max-w-[640px]">
        <DialogHeader>
          <DialogTitle>Keyboard Shortcuts</DialogTitle>
        </DialogHeader>
        <div className="grid gap-2 max-h-[400px] overflow-y-auto py-4">
          <div className="font-semibold mt-2 opacity-90">General</div>
          <Row k="Ctrl+/" d="Open this help" />
          <Row k="Ctrl+," d="Open settings" />
          <Row k="Ctrl+L" d="Toggle theme" />
          <Row k="Ctrl+B" d="Toggle sidebar" />
          <div className="font-semibold mt-2 opacity-90">Threads</div>
          <Row k="Ctrl+N" d="New thread" />
          <Row k="Ctrl+Shift+E" d="Export thread" />
          <Row k="Ctrl+Shift+I" d="Import thread" />
          <div className="font-semibold mt-2 opacity-90">Messaging</div>
          <Row k="Ctrl+K" d="Focus composer" />
          <Row k="Ctrl+Shift+K" d="Clear composer" />
          <Row k="Ctrl+Enter" d="Send message" />
          <Row k="Escape" d="Stop streaming" />
          <Row k="Up Arrow (empty input)" d="Edit last message" />
          <div className="font-semibold mt-2 opacity-90">Message Actions</div>
          <Row k="Hover + C / Ctrl+C" d="Copy message" />
          <Row k="Hover + E" d="Edit (user msgs)" />
          <Row k="Hover + Delete" d="Delete message" />
        </div>
        <DialogFooter>
          <Button onClick={() => useHelp.getState().close()}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

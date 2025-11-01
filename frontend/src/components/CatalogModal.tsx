import React from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog'
import { CatalogUpload } from './CatalogUpload'
import { Package } from 'lucide-react'

interface CatalogModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CatalogModal({ open, onOpenChange }: CatalogModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-3xl max-h-[85vh] overflow-y-auto" aria-label="Product catalog modal" data-testid="catalog-modal">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600">
              <Package className="w-5 h-5 text-white" />
            </div>
            <div>
              <DialogTitle className="text-xl">Product Catalog</DialogTitle>
              <DialogDescription className="mt-1">
                Upload and manage your product inventory
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <div className="mt-2">
          <CatalogUpload />
        </div>
      </DialogContent>
    </Dialog>
  )
}

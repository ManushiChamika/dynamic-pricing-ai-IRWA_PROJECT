import React from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog'
import { CatalogUpload } from './CatalogUpload'

interface CatalogModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CatalogModal({ open, onOpenChange }: CatalogModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Product Catalog Management</DialogTitle>
          <DialogDescription>
            Upload and manage your product catalog
          </DialogDescription>
        </DialogHeader>
        <CatalogUpload />
      </DialogContent>
    </Dialog>
  )
}

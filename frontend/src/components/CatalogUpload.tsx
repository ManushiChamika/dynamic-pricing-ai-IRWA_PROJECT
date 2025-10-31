import React, { useState, useRef } from 'react'
import { Button } from './ui/button'
import { useAuthToken } from '../stores/authStore'
import {
  Upload,
  FileText,
  X,
  CheckCircle2,
  AlertCircle,
  Loader2,
  File,
  Package,
  Trash2,
} from 'lucide-react'

interface UploadResponse {
  success: boolean
  filename: string
  rows_processed: number
  rows_inserted: number
  owner_id: string
}

export function CatalogUpload() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState<UploadResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [deleting, setDeleting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const token = useAuthToken()

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0]
      if (droppedFile.name.endsWith('.csv') || droppedFile.name.endsWith('.json')) {
        setFile(droppedFile)
        setError(null)
        setSuccess(null)
      } else {
        setError('Please upload a CSV or JSON file')
      }
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
      setSuccess(null)
    }
  }

  const handleUpload = async () => {
    if (!file || !token) {
      setError('No file selected or user not authenticated')
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)
    setUploadProgress(0)

    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => Math.min(prev + 10, 90))
    }, 150)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`/api/catalog/upload?token=${encodeURIComponent(token)}`, {
        method: 'POST',
        body: formData,
      })

      clearInterval(progressInterval)
      setUploadProgress(100)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Upload failed')
      }

      const data: UploadResponse = await response.json()
      setSuccess(data)
      setFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      window.dispatchEvent(new Event('catalog-updated'))
    } catch (err) {
      clearInterval(progressInterval)
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setLoading(false)
      setTimeout(() => setUploadProgress(0), 1000)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / 1024 / 1024).toFixed(2) + ' MB'
  }

  const handleDeleteAll = async () => {
    if (!token) {
      setError('User not authenticated')
      return
    }

    if (
      !window.confirm('Are you sure you want to delete all products? This action cannot be undone.')
    ) {
      return
    }

    setDeleting(true)
    setError(null)
    setSuccess(null)

    try {
      const response = await fetch(`/api/catalog/products?token=${encodeURIComponent(token)}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Delete failed')
      }

      const data = await response.json()
      setSuccess({
        success: true,
        filename: 'Catalog cleared',
        rows_processed: data.rows_affected,
        rows_inserted: 0,
        owner_id: '',
      })
      window.dispatchEvent(new Event('catalog-updated'))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed')
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`
          relative overflow-hidden rounded-lg border-2 border-dashed transition-all
          ${
            dragActive
              ? 'border-primary bg-accent'
              : 'border-border hover:border-muted-foreground/50 bg-muted/20'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.json"
          onChange={handleFileChange}
          className="hidden"
          disabled={loading}
        />

        <div className="p-12 text-center">
          <div
            className={`
            mx-auto w-20 h-20 rounded-full flex items-center justify-center mb-6 transition-all
            ${dragActive ? 'bg-primary/20' : 'bg-muted'}
          `}
          >
            <Upload
              className={`w-10 h-10 ${dragActive ? 'text-primary' : 'text-muted-foreground'}`}
            />
          </div>

          <h3 className="text-lg font-semibold mb-2">
            {dragActive ? 'Drop your file here' : 'Upload Product Catalog'}
          </h3>

          <p className="text-sm text-muted-foreground mb-6">
            {dragActive ? 'Release to upload' : 'Drag and drop your file, or click to browse'}
          </p>

          <Button type="button" onClick={() => fileInputRef.current?.click()} disabled={loading}>
            <FileText className="w-4 h-4 mr-2" />
            Choose File
          </Button>

          <p className="text-xs text-muted-foreground mt-4">CSV or JSON • Max 50MB</p>
        </div>
      </div>

      {file && (
        <div className="p-5 rounded-lg border bg-muted/30 transition-all">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-primary/10">
              <File className="w-6 h-6 text-primary" />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate">{file.name}</p>
                  <p className="text-xs text-muted-foreground mt-1">{formatFileSize(file.size)}</p>
                </div>

                <button
                  onClick={() => {
                    setFile(null)
                    if (fileInputRef.current) fileInputRef.current.value = ''
                  }}
                  disabled={loading}
                  className="p-1 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {loading && (
                <div className="mt-4">
                  <div className="h-1.5 rounded-full overflow-hidden bg-muted">
                    <div
                      className="h-full bg-primary transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Uploading... {uploadProgress}%
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-lg border border-destructive/50 bg-destructive/10 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-destructive shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-destructive">Upload Failed</p>
            <p className="text-sm text-destructive/90 mt-1">{error}</p>
          </div>
        </div>
      )}

      {success && (
        <div className="p-4 rounded-lg border border-green-500/50 bg-green-500/10 flex items-start gap-3">
          <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-green-700 dark:text-green-400">
              Upload Successful!
            </p>
            <p className="text-sm text-green-600 dark:text-green-500 mt-1">{success.filename}</p>
            <div className="flex items-center gap-4 mt-2 text-xs text-green-600 dark:text-green-500">
              <span>Processed: {success.rows_processed}</span>
              <span>•</span>
              <span>Inserted: {success.rows_inserted}</span>
            </div>
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <Button onClick={handleUpload} disabled={!file || loading || deleting} className="flex-1">
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <Upload className="w-4 h-4 mr-2" />
              Upload Catalog
            </>
          )}
        </Button>
        <Button onClick={handleDeleteAll} disabled={loading || deleting} variant="destructive">
          {deleting ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Deleting...
            </>
          ) : (
            <>
              <Trash2 className="w-4 h-4 mr-2" />
              Clear All
            </>
          )}
        </Button>
      </div>

      <div className="p-5 rounded-lg border bg-muted/20">
        <div className="flex items-start gap-3 mb-4">
          <Package className="w-5 h-5 text-primary" />
          <div>
            <h3 className="font-medium text-sm mb-1">Required Format</h3>
            <p className="text-xs text-muted-foreground">
              Your CSV/JSON file must include these columns:
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mt-4">
          {[
            { field: 'sku', desc: 'Unique product ID' },
            { field: 'title', desc: 'Product name' },
            { field: 'currency', desc: 'e.g., USD, EUR' },
            { field: 'current_price', desc: 'Current price' },
            { field: 'cost', desc: 'Product cost' },
            { field: 'stock', desc: 'Available quantity' },
          ].map(({ field, desc }) => (
            <div key={field} className="p-3 rounded-lg bg-muted/30">
              <code className="text-xs font-mono text-primary">{field}</code>
              <p className="text-xs text-muted-foreground mt-1">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}



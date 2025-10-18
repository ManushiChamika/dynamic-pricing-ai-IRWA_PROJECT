import React, { useState, useRef } from 'react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { useAuthToken } from '../stores/authStore'
import { useTheme } from '../stores/settingsStore'

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
  const fileInputRef = useRef<HTMLInputElement>(null)
  const token = useAuthToken()
  const theme = useTheme()

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
      } else {
        setError('Please upload a CSV or JSON file')
      }
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
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

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(
        `/api/catalog/upload?token=${encodeURIComponent(token)}`,
        {
          method: 'POST',
          body: formData
        }
      )

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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`p-6 rounded-lg border ${dragActive ? 'border-blue-500 bg-blue-50 dark:bg-blue-950' : 'border-border'} transition-colors`}>
      <h2 className="text-xl font-semibold mb-4">Upload Product Catalog</h2>

      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`p-8 border-2 border-dashed rounded-lg text-center cursor-pointer transition-all ${
          dragActive
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-950'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.json"
          onChange={handleFileChange}
          className="hidden"
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="text-blue-600 dark:text-blue-400 hover:underline"
        >
          Click to upload
        </button>
        {' or drag and drop'}
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
          CSV or JSON file (max 50MB)
        </p>
      </div>

      {file && (
        <div className="mt-4 p-3 bg-gray-100 dark:bg-gray-800 rounded-lg">
          <p className="text-sm font-medium">Selected file: {file.name}</p>
          <p className="text-xs text-gray-600 dark:text-gray-400">
            Size: {(file.size / 1024 / 1024).toFixed(2)} MB
          </p>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 bg-red-100 dark:bg-red-950 border border-red-400 dark:border-red-600 rounded-lg">
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {success && (
        <div className="mt-4 p-3 bg-green-100 dark:bg-green-950 border border-green-400 dark:border-green-600 rounded-lg">
          <p className="text-sm font-medium text-green-800 dark:text-green-200">
            Successfully uploaded {success.filename}
          </p>
          <p className="text-xs text-green-700 dark:text-green-300 mt-1">
            Processed: {success.rows_processed} rows | Inserted: {success.rows_inserted} rows
          </p>
        </div>
      )}

      <div className="mt-6 flex gap-3">
        <Button
          onClick={handleUpload}
          disabled={!file || loading}
          className="flex-1"
        >
          {loading ? 'Uploading...' : 'Upload Catalog'}
        </Button>
        {file && (
          <Button
            onClick={() => {
              setFile(null)
              if (fileInputRef.current) {
                fileInputRef.current.value = ''
              }
            }}
            variant="outline"
            disabled={loading}
          >
            Clear
          </Button>
        )}
      </div>

      <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
        <h3 className="font-semibold text-sm mb-2">Required CSV/JSON Format:</h3>
        <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
          Your file must contain these columns:
        </p>
        <ul className="text-xs text-gray-600 dark:text-gray-400 list-disc list-inside space-y-1">
          <li><strong>sku</strong> - Product identifier (must be unique)</li>
          <li><strong>title</strong> - Product name</li>
          <li><strong>currency</strong> - Currency code (e.g., USD, EUR)</li>
          <li><strong>current_price</strong> - Current price (number)</li>
          <li><strong>cost</strong> - Product cost (number)</li>
          <li><strong>stock</strong> - Available stock (integer)</li>
        </ul>
      </div>
    </div>
  )
}

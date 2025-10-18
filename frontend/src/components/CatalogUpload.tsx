import React, { useState, useRef } from 'react'
import { Button } from './ui/button'
import { useAuthToken } from '../stores/authStore'
import { useTheme } from '../stores/settingsStore'
import { 
  Upload, 
  FileText, 
  X, 
  CheckCircle2, 
  AlertCircle, 
  Loader2,
  File,
  Package
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
  const fileInputRef = useRef<HTMLInputElement>(null)
  const token = useAuthToken()
  const theme = useTheme()
  const isDark = theme === 'dark'

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
      setUploadProgress(prev => Math.min(prev + 10, 90))
    }, 150)

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

  return (
    <div className="space-y-6">
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`
          relative overflow-hidden rounded-xl border-2 border-dashed transition-all duration-300
          ${dragActive 
            ? 'border-indigo-500 bg-indigo-500/10 scale-[1.02]' 
            : isDark 
              ? 'border-gray-700 hover:border-gray-600 bg-gray-900/50' 
              : 'border-gray-300 hover:border-gray-400 bg-gray-50/50'
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
          <div className={`
            mx-auto w-20 h-20 rounded-full flex items-center justify-center mb-6 transition-all duration-300
            ${dragActive 
              ? 'bg-indigo-500/20 scale-110' 
              : isDark 
                ? 'bg-gray-800' 
                : 'bg-white shadow-sm'
            }
          `}>
            <Upload className={`w-10 h-10 ${dragActive ? 'text-indigo-500' : 'text-gray-400'}`} />
          </div>

          <h3 className="text-lg font-semibold mb-2">
            {dragActive ? 'Drop your file here' : 'Upload Product Catalog'}
          </h3>
          
          <p className={`text-sm mb-6 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            {dragActive ? 'Release to upload' : 'Drag and drop your file, or click to browse'}
          </p>

          <Button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
            className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700"
          >
            <FileText className="w-4 h-4 mr-2" />
            Choose File
          </Button>

          <p className={`text-xs mt-4 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
            CSV or JSON • Max 50MB
          </p>
        </div>
      </div>

      {file && (
        <div className={`
          p-5 rounded-xl border transition-all duration-300 animate-in slide-in-from-top-2
          ${isDark 
            ? 'bg-gray-900/80 border-gray-700' 
            : 'bg-white border-gray-200 shadow-sm'
          }
        `}>
          <div className="flex items-start gap-4">
            <div className={`
              p-3 rounded-lg
              ${isDark ? 'bg-indigo-500/10' : 'bg-indigo-50'}
            `}>
              <File className="w-6 h-6 text-indigo-500" />
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate">{file.name}</p>
                  <p className={`text-xs mt-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                    {formatFileSize(file.size)}
                  </p>
                </div>
                
                <button
                  onClick={() => {
                    setFile(null)
                    if (fileInputRef.current) fileInputRef.current.value = ''
                  }}
                  disabled={loading}
                  className={`
                    p-1 rounded-lg transition-colors
                    ${isDark 
                      ? 'hover:bg-gray-800 text-gray-400 hover:text-gray-200' 
                      : 'hover:bg-gray-100 text-gray-500 hover:text-gray-700'
                    }
                    disabled:opacity-50 disabled:cursor-not-allowed
                  `}
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {loading && (
                <div className="mt-4">
                  <div className={`h-1.5 rounded-full overflow-hidden ${isDark ? 'bg-gray-800' : 'bg-gray-200'}`}>
                    <div 
                      className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 transition-all duration-300 ease-out"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <p className={`text-xs mt-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                    Uploading... {uploadProgress}%
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className={`
          p-4 rounded-xl border flex items-start gap-3 animate-in slide-in-from-top-2
          ${isDark 
            ? 'bg-red-950/50 border-red-900/50' 
            : 'bg-red-50 border-red-200'
          }
        `}>
          <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className={`text-sm font-medium ${isDark ? 'text-red-200' : 'text-red-900'}`}>
              Upload Failed
            </p>
            <p className={`text-sm mt-1 ${isDark ? 'text-red-300' : 'text-red-700'}`}>
              {error}
            </p>
          </div>
        </div>
      )}

      {success && (
        <div className={`
          p-4 rounded-xl border flex items-start gap-3 animate-in slide-in-from-top-2
          ${isDark 
            ? 'bg-green-950/50 border-green-900/50' 
            : 'bg-green-50 border-green-200'
          }
        `}>
          <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className={`text-sm font-medium ${isDark ? 'text-green-200' : 'text-green-900'}`}>
              Upload Successful!
            </p>
            <p className={`text-sm mt-1 ${isDark ? 'text-green-300' : 'text-green-700'}`}>
              {success.filename}
            </p>
            <div className={`flex items-center gap-4 mt-2 text-xs ${isDark ? 'text-green-400' : 'text-green-600'}`}>
              <span>Processed: {success.rows_processed}</span>
              <span>•</span>
              <span>Inserted: {success.rows_inserted}</span>
            </div>
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <Button
          onClick={handleUpload}
          disabled={!file || loading}
          className="flex-1 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50"
        >
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
      </div>

      <div className={`
        p-5 rounded-xl border
        ${isDark 
          ? 'bg-gray-900/50 border-gray-800' 
          : 'bg-gray-50 border-gray-200'
        }
      `}>
        <div className="flex items-start gap-3 mb-4">
          <Package className={`w-5 h-5 ${isDark ? 'text-indigo-400' : 'text-indigo-600'}`} />
          <div>
            <h3 className="font-semibold text-sm mb-1">Required Format</h3>
            <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
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
            <div 
              key={field}
              className={`
                p-3 rounded-lg
                ${isDark ? 'bg-gray-800/50' : 'bg-white'}
              `}
            >
              <code className="text-xs font-mono text-indigo-500">{field}</code>
              <p className={`text-xs mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                {desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

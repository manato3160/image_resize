import { useCallback, useState } from 'react'

interface ImageUploaderProps {
  onFileSelect: (files: File[]) => void
  maxFiles?: number
}

export default function ImageUploader({ onFileSelect, maxFiles = 8 }: ImageUploaderProps) {
  const [isDragging, setIsDragging] = useState(false)

  const handleFiles = useCallback(
    (files: File[]) => {
      const validFiles: File[] = []
      const errors: string[] = []

      // ファイル数チェック
      if (files.length > maxFiles) {
        alert(`画像は最大${maxFiles}枚までアップロードできます`)
        return
      }

      files.forEach((file) => {
        // 画像ファイルかチェック
        if (!file.type.startsWith('image/')) {
          errors.push(`${file.name}: 画像ファイルではありません`)
          return
        }
        
        // ファイルサイズチェック（50MB）
        const maxSize = 50 * 1024 * 1024
        if (file.size > maxSize) {
          errors.push(`${file.name}: ファイルサイズが大きすぎます（最大${maxSize / (1024 * 1024)}MB）`)
          return
        }
        
        if (file.size === 0) {
          errors.push(`${file.name}: 空のファイルです`)
          return
        }
        
        validFiles.push(file)
      })

      if (errors.length > 0) {
        alert(errors.join('\n'))
      }

      if (validFiles.length > 0) {
        onFileSelect(validFiles)
      }
    },
    [onFileSelect, maxFiles]
  )

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)

      const files = Array.from(e.dataTransfer.files)
      if (files.length > 0) {
        handleFiles(files)
      }
    },
    [handleFiles]
  )

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files
      if (files && files.length > 0) {
        handleFiles(Array.from(files))
      }
    },
    [handleFiles]
  )

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors duration-200 ${
        isDragging
          ? 'border-indigo-500 bg-indigo-50'
          : 'border-gray-300 bg-gray-50 hover:border-gray-400'
      }`}
    >
      <div className="space-y-4">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          stroke="currentColor"
          fill="none"
          viewBox="0 0 48 48"
        >
          <path
            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <div>
          <label
            htmlFor="file-upload"
            className="cursor-pointer text-indigo-600 hover:text-indigo-700 font-medium"
          >
            クリックしてファイルを選択
          </label>
          <span className="text-gray-600"> またはドラッグ&ドロップ</span>
        </div>
        <p className="text-sm text-gray-500">
          PNG, JPG, JPEG, WebP 形式に対応（最大{maxFiles}枚まで）
        </p>
        <input
          id="file-upload"
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileInput}
          className="hidden"
        />
      </div>
    </div>
  )
}


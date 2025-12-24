import { useState } from 'react'
import ImageUploader from './components/ImageUploader'
import Preview from './components/Preview'
import { 
  processImage, 
  processMultipleImages, 
  ProcessedImage, 
  ProcessMultipleImagesProgress,
  FileWithMode,
  ResizeMode,
  UpscaleMethod
} from './services/api'

// 後方互換性のために型をエクスポート
export type { ResizeMode, UpscaleMethod }

function App() {
  const [selectedFiles, setSelectedFiles] = useState<FileWithMode[]>([])
  const [upscaleMethod, setUpscaleMethod] = useState<UpscaleMethod>('simple')
  const [processedImageUrl, setProcessedImageUrl] = useState<string | null>(null)
  const [processedImages, setProcessedImages] = useState<ProcessedImage[]>([])
  const [processedZipUrl, setProcessedZipUrl] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState<ProcessMultipleImagesProgress | null>(null)

  const handleFileSelect = async (files: File[]) => {
    // 各ファイルにデフォルトのモード（vertical）とプレビューURLを設定
    const filesWithMode: FileWithMode[] = await Promise.all(
      files.map(async (file) => {
        const previewUrl = URL.createObjectURL(file)
        return {
          file,
          mode: 'vertical' as ResizeMode,
          previewUrl
        }
      })
    )
    setSelectedFiles(filesWithMode)
    setProcessedImageUrl(null)
    setProcessedImages([])
    setProcessedZipUrl(null)
    setError(null)
  }

  const handleModeChange = (index: number, mode: ResizeMode) => {
    setSelectedFiles(prev => 
      prev.map((item, i) => i === index ? { ...item, mode } : item)
    )
  }

  const handleRemoveFile = (index: number) => {
    setSelectedFiles(prev => {
      const newFiles = [...prev]
      URL.revokeObjectURL(newFiles[index].previewUrl)
      newFiles.splice(index, 1)
      return newFiles
    })
  }

  const handleProcess = async () => {
    if (selectedFiles.length === 0) {
      setError('画像を選択してください')
      return
    }

    setIsProcessing(true)
    setError(null)
    setProcessedImageUrl(null)
    setProcessedImages([])
    setProcessedZipUrl(null)
    setProgress(null)

    try {
      if (selectedFiles.length === 1) {
        // 単一画像の場合
        const fileWithMode = selectedFiles[0]
        const imageUrl = await processImage(fileWithMode.file, fileWithMode.mode, upscaleMethod)
        setProcessedImageUrl(imageUrl)
      } else {
        // 複数画像の場合は1枚ずつ処理（各画像のモードに応じて）
        const result = await processMultipleImages(
          selectedFiles, 
          upscaleMethod,
          (progressInfo) => {
            setProgress(progressInfo)
          }
        )
        setProcessedImages(result.images)
        setProcessedZipUrl(result.zip_data)
        
        // エラーがあれば警告を表示
        if (result.errors && result.errors.length > 0) {
          setError(`一部の画像の処理に失敗しました:\n${result.errors.join('\n')}`)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '画像処理に失敗しました')
    } finally {
      setIsProcessing(false)
      setProgress(null)
    }
  }

  const handleDownloadZip = () => {
    if (processedZipUrl) {
      const link = document.createElement('a')
      link.href = processedZipUrl
      link.download = 'processed_images.zip'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-center text-gray-800 mb-8">
          画像リサイズ高解像度化ツール
        </h1>

        <div className="max-w-4xl mx-auto space-y-6">
          {/* 画像アップロード */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-semibold mb-4 text-gray-700">
              1. 画像をアップロード（最大8枚）
            </h2>
            <ImageUploader onFileSelect={handleFileSelect} maxFiles={8} />
          </div>

          {/* 画像リストとモード選択 */}
          {selectedFiles.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-semibold mb-4 text-gray-700">
                2. 各画像のリサイズ方向を選択 ({selectedFiles.length}枚)
              </h2>
              <div className="space-y-4">
                {selectedFiles.map((fileWithMode, idx) => (
                  <div key={idx} className="flex items-center gap-4 p-4 border rounded-lg bg-gray-50">
                    {/* プレビュー */}
                    <div className="flex-shrink-0 w-24 h-24 bg-gray-200 rounded-lg overflow-hidden">
                      <img
                        src={fileWithMode.previewUrl}
                        alt={fileWithMode.file.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    
                    {/* ファイル名 */}
                    <div className="flex-grow min-w-0">
                      <p className="text-sm font-medium text-gray-800 truncate">
                        {fileWithMode.file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {(fileWithMode.file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                    
                    {/* モード選択 */}
                    <div className="flex-shrink-0">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleModeChange(idx, 'vertical')}
                          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                            fileWithMode.mode === 'vertical'
                              ? 'bg-indigo-600 text-white'
                              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                          }`}
                        >
                          縦 (1080×1350)
                        </button>
                        <button
                          onClick={() => handleModeChange(idx, 'horizontal')}
                          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                            fileWithMode.mode === 'horizontal'
                              ? 'bg-indigo-600 text-white'
                              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                          }`}
                        >
                          横 (1350×1080)
                        </button>
                      </div>
                    </div>
                    
                    {/* 削除ボタン */}
                    <button
                      onClick={() => handleRemoveFile(idx)}
                      className="flex-shrink-0 text-red-600 hover:text-red-800 transition-colors"
                      title="削除"
                    >
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* オプション選択（高解像度化のみ） */}
          {selectedFiles.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-semibold mb-4 text-gray-700">
                3. 高解像度化オプション
              </h2>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  高解像度化方法
                </label>
                <div className="flex gap-4">
                  <button
                    onClick={() => setUpscaleMethod('simple')}
                    className={`flex-1 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                      upscaleMethod === 'simple'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    シンプル（高速）
                  </button>
                  <button
                    onClick={() => setUpscaleMethod('ai')}
                    disabled
                    className="flex-1 px-4 py-3 rounded-lg text-sm font-medium bg-gray-100 text-gray-400 cursor-not-allowed"
                  >
                    AI（現在利用不可）
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* 処理ボタン */}
          {selectedFiles.length > 0 && (
            <div className="text-center">
              <button
                onClick={handleProcess}
                disabled={isProcessing}
                className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-bold py-3 px-8 rounded-lg text-lg transition-colors duration-200 shadow-lg"
              >
                {isProcessing ? '処理中...' : `画像を一括処理 (${selectedFiles.length}枚)`}
              </button>
            </div>
          )}

          {/* プログレス表示 */}
          {progress && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="mb-2 flex justify-between items-center">
                <span className="text-sm font-medium text-gray-700">
                  処理中: {progress.filename}
                </span>
                <span className="text-sm font-medium text-indigo-600">
                  {progress.current} / {progress.total}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300"
                  style={{ width: `${(progress.current / progress.total) * 100}%` }}
                ></div>
              </div>
              <div className="mt-2 text-xs text-gray-500 text-center">
                {progress.status === 'processing' && '画像を処理中...'}
                {progress.status === 'completed' && '✓ 完了'}
                {progress.status === 'error' && '✗ エラー'}
              </div>
            </div>
          )}

          {/* エラー表示 */}
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg whitespace-pre-line">
              {error}
            </div>
          )}

          {/* プレビュー - 単一画像 */}
          {processedImageUrl && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-semibold mb-4 text-gray-700">
                4. 処理結果
              </h2>
              <Preview imageUrl={processedImageUrl} />
            </div>
          )}
          
          {/* プレビュー - 複数画像 */}
          {processedImages.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-semibold mb-4 text-gray-700">
                4. 処理結果 ({processedImages.length}枚)
              </h2>
              
              {/* 画像グリッド */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                {processedImages.map((img, idx) => (
                  <div key={idx} className="border rounded-lg p-4 bg-gray-50">
                    <p className="text-sm font-medium text-gray-700 mb-2 truncate">
                      {img.filename}
                    </p>
                    <div className="flex justify-center mb-2">
                      <img
                        src={img.data}
                        alt={`処理済み ${img.filename}`}
                        className="max-w-full h-auto rounded-lg shadow-md"
                      />
                    </div>
                    <a
                      href={img.data}
                      download={img.filename}
                      className="block text-center bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded-lg transition-colors duration-200 text-sm"
                    >
                      ダウンロード
                    </a>
                  </div>
                ))}
              </div>
              
              {/* ZIPダウンロードボタン */}
              <div className="text-center pt-4 border-t">
                <button
                  onClick={handleDownloadZip}
                  className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-6 rounded-lg transition-colors duration-200 shadow-md"
                >
                  すべての画像をZIPでダウンロード
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App


import { useState } from 'react'
import ImageUploader from './components/ImageUploader'
import ResizeOptions from './components/ResizeOptions'
import Preview from './components/Preview'
import { processImage, processMultipleImages, ProcessedImage } from './services/api'

export type ResizeMode = 'vertical' | 'horizontal'
export type UpscaleMethod = 'simple' | 'ai'

function App() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [resizeMode, setResizeMode] = useState<ResizeMode>('vertical')
  const [upscaleMethod, setUpscaleMethod] = useState<UpscaleMethod>('simple')
  const [processedImageUrl, setProcessedImageUrl] = useState<string | null>(null)
  const [processedImages, setProcessedImages] = useState<ProcessedImage[]>([])
  const [processedZipUrl, setProcessedZipUrl] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFileSelect = (files: File[]) => {
    setSelectedFiles(files)
    setProcessedImageUrl(null)
    setProcessedImages([])
    setProcessedZipUrl(null)
    setError(null)
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

    try {
      if (selectedFiles.length === 1) {
        // 単一画像の場合は従来通り
        const imageUrl = await processImage(selectedFiles[0], resizeMode, upscaleMethod)
        setProcessedImageUrl(imageUrl)
      } else {
        // 複数画像の場合はJSONで返す
        const result = await processMultipleImages(selectedFiles, resizeMode, upscaleMethod)
        setProcessedImages(result.images)
        setProcessedZipUrl(result.zip_data)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '画像処理に失敗しました')
    } finally {
      setIsProcessing(false)
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
            {selectedFiles.length > 0 && (
              <div className="mt-4">
                <p className="text-sm font-medium text-gray-700 mb-2">
                  選択されたファイル ({selectedFiles.length}枚):
                </p>
                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                  {selectedFiles.map((file, idx) => (
                    <li key={idx}>{file.name}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* オプション選択 */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-semibold mb-4 text-gray-700">
              2. オプションを選択
            </h2>
            <ResizeOptions
              resizeMode={resizeMode}
              upscaleMethod={upscaleMethod}
              onResizeModeChange={setResizeMode}
              onUpscaleMethodChange={setUpscaleMethod}
            />
          </div>

          {/* 処理ボタン */}
          <div className="text-center">
            <button
              onClick={handleProcess}
              disabled={selectedFiles.length === 0 || isProcessing}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-bold py-3 px-8 rounded-lg text-lg transition-colors duration-200 shadow-lg"
            >
              {isProcessing ? '処理中...' : `画像を処理 (${selectedFiles.length}枚)`}
            </button>
          </div>

          {/* エラー表示 */}
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          {/* プレビュー - 単一画像 */}
          {processedImageUrl && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-semibold mb-4 text-gray-700">
                3. 処理結果
              </h2>
              <Preview imageUrl={processedImageUrl} />
            </div>
          )}
          
          {/* プレビュー - 複数画像 */}
          {processedImages.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-semibold mb-4 text-gray-700">
                3. 処理結果 ({processedImages.length}枚)
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


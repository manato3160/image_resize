import { ResizeMode, UpscaleMethod } from '../App'

interface ResizeOptionsProps {
  resizeMode: ResizeMode
  upscaleMethod: UpscaleMethod
  onResizeModeChange: (mode: ResizeMode) => void
  onUpscaleMethodChange: (method: UpscaleMethod) => void
}

export default function ResizeOptions({
  resizeMode,
  upscaleMethod,
  onResizeModeChange,
  onUpscaleMethodChange,
}: ResizeOptionsProps) {
  return (
    <div className="space-y-6">
      {/* リサイズモード選択 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          リサイズモード
        </label>
        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => onResizeModeChange('vertical')}
            className={`p-4 rounded-lg border-2 transition-all duration-200 ${
              resizeMode === 'vertical'
                ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
            }`}
          >
            <div className="font-semibold mb-1">縦向き</div>
            <div className="text-sm text-gray-600">1080 × 1350px</div>
          </button>
          <button
            onClick={() => onResizeModeChange('horizontal')}
            className={`p-4 rounded-lg border-2 transition-all duration-200 ${
              resizeMode === 'horizontal'
                ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
            }`}
          >
            <div className="font-semibold mb-1">横向き</div>
            <div className="text-sm text-gray-600">1350 × 1080px</div>
          </button>
        </div>
      </div>

      {/* アップスケール方法選択 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          高解像度化方法
        </label>
        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => onUpscaleMethodChange('simple')}
            className={`p-4 rounded-lg border-2 transition-all duration-200 ${
              upscaleMethod === 'simple'
                ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
            }`}
          >
            <div className="font-semibold mb-1">単純リサイズ</div>
            <div className="text-sm text-gray-600">高速処理</div>
          </button>
          <button
            onClick={() => onUpscaleMethodChange('ai')}
            className={`p-4 rounded-lg border-2 transition-all duration-200 ${
              upscaleMethod === 'ai'
                ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
            }`}
          >
            <div className="font-semibold mb-1">AIアップスケール</div>
            <div className="text-sm text-gray-600">高品質（処理時間長）</div>
          </button>
        </div>
      </div>
    </div>
  )
}


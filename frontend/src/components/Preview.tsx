import { useRef } from 'react'

interface PreviewProps {
  imageUrl: string
}

export default function Preview({ imageUrl }: PreviewProps) {
  const linkRef = useRef<HTMLAnchorElement>(null)

  const handleDownload = () => {
    if (linkRef.current) {
      linkRef.current.click()
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-center">
        <img
          src={imageUrl}
          alt="処理済み画像"
          className="max-w-full h-auto rounded-lg shadow-md"
        />
      </div>
      <div className="text-center">
        <a
          ref={linkRef}
          href={imageUrl}
          download="processed_image.jpg"
          className="hidden"
        >
          ダウンロード
        </a>
        <button
          onClick={handleDownload}
          className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-6 rounded-lg transition-colors duration-200 shadow-md"
        >
          画像をダウンロード
        </button>
      </div>
    </div>
  )
}


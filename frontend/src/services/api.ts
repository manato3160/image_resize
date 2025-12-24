import axios from 'axios'
import JSZip from 'jszip'
import { ResizeMode, UpscaleMethod } from '../App'

// Vercel Functionsを使用する場合は、環境変数が設定されていない場合は相対パスを使用
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

// 最大ファイルサイズ: 50MB
const MAX_FILE_SIZE = 50 * 1024 * 1024

export async function processImage(
  file: File,
  mode: ResizeMode,
  upscaleMethod: UpscaleMethod
): Promise<string> {
  // ファイルサイズチェック
  if (file.size > MAX_FILE_SIZE) {
    throw new Error(
      `ファイルサイズが大きすぎます。最大${MAX_FILE_SIZE / (1024 * 1024)}MBまで対応しています。`
    )
  }

  // ファイルタイプチェック
  if (!file.type.startsWith('image/')) {
    throw new Error('画像ファイルを選択してください')
  }

  // ファイルをBase64エンコード
  const fileBase64 = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      // data:image/...;base64, の部分を除去
      const base64 = result.split(',')[1]
      resolve(base64)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })

  // Vercel Functions用のJSON形式で送信
  const requestData = {
    image: fileBase64,
    mode: mode,
    upscale_method: upscaleMethod
  }

  try {
    const response = await axios.post<{ success: boolean; image?: string; error?: string; content_type?: string }>(
      `${API_BASE_URL}/api/process`,
      requestData,
      {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 30000, // 30秒（Vercel Functionsの制限を考慮）
      }
    )

    if (!response.data.success || !response.data.image) {
      throw new Error(response.data.error || '画像処理に失敗しました')
    }

    // Base64データをBlob URLに変換
    const imageUrl = `data:${response.data.content_type || 'image/jpeg'};base64,${response.data.image}`
    return imageUrl
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response) {
        // エラーレスポンスがBlobの場合
        if (error.response.data instanceof Blob) {
          try {
            const errorText = await error.response.data.text()
            const errorData = JSON.parse(errorText)
            throw new Error(errorData.detail || '画像処理に失敗しました')
          } catch {
            throw new Error('画像処理に失敗しました')
          }
        }
        // エラーレスポンスの詳細を取得
        const errorData = error.response.data
        let errorMessage = '画像処理に失敗しました'
        
        // エラーレスポンスがJSONの場合
        if (typeof errorData === 'object' && errorData !== null) {
          // デバッグ情報を含むエラーメッセージを構築
          if (errorData.error) {
            errorMessage = errorData.error
            // デバッグ情報があれば追加
            if (errorData.received_method) {
              errorMessage += ` (受信メソッド: ${errorData.received_method})`
            }
            if (errorData.request_keys) {
              errorMessage += ` (リクエストキー: ${errorData.request_keys.join(', ')})`
            }
          } else if (errorData.detail) {
            errorMessage = errorData.detail
          } else if (errorData.message) {
            errorMessage = errorData.message
          } else {
            errorMessage = `エラー: ${error.response.status} ${error.response.statusText}`
          }
        } else if (typeof errorData === 'string') {
          errorMessage = errorData
        } else {
          errorMessage = `エラー: ${error.response.status} ${error.response.statusText}`
        }
        
        throw new Error(errorMessage)
      } else if (error.request) {
        throw new Error(
          'サーバーに接続できませんでした。APIエンドポイントを確認してください。'
        )
      } else if (error.code === 'ECONNABORTED') {
        throw new Error('リクエストがタイムアウトしました。画像が大きすぎる可能性があります。')
      }
    }
    if (error instanceof Error) {
      throw error
    }
    throw new Error('予期しないエラーが発生しました')
  }
}

export interface ProcessedImage {
  filename: string
  data: string // Base64 data URL
  content_type: string
}

export interface ProcessMultipleImagesResult {
  images: ProcessedImage[]
  zip_data: string // Base64 data URL for ZIP
  zip_filename: string
  errors?: string[] | null
}

export interface ProcessMultipleImagesProgress {
  current: number
  total: number
  filename: string
  status: 'processing' | 'completed' | 'error'
}

/**
 * 複数画像を1枚ずつ順次処理（Vercelの4.5MB制限を回避）
 */
export async function processMultipleImages(
  files: File[],
  mode: ResizeMode,
  upscaleMethod: UpscaleMethod,
  onProgress?: (progress: ProcessMultipleImagesProgress) => void
): Promise<ProcessMultipleImagesResult> {
  // ファイル数チェック
  if (files.length === 0) {
    throw new Error('画像を選択してください')
  }

  if (files.length > 8) {
    throw new Error('画像は最大8枚までアップロードできます')
  }

  // 各ファイルの検証
  const maxSize = 50 * 1024 * 1024
  for (const file of files) {
    if (file.size > maxSize) {
      throw new Error(
        `${file.name}: ファイルサイズが大きすぎます。最大${maxSize / (1024 * 1024)}MBまで対応しています。`
      )
    }

    if (!file.type.startsWith('image/')) {
      throw new Error(`${file.name}: 画像ファイルを選択してください`)
    }
  }

  const processedImages: ProcessedImage[] = []
  const errors: string[] = []

  // 1枚ずつ順次処理（Vercelの4.5MB制限を回避）
  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    
    try {
      // プログレス通知
      if (onProgress) {
        onProgress({
          current: i + 1,
          total: files.length,
          filename: file.name,
          status: 'processing'
        })
      }

      // 画像を処理（既存のprocessImage関数を使用）
      const processedImageUrl = await processImage(file, mode, upscaleMethod)

      processedImages.push({
        filename: file.name,
        data: processedImageUrl,
        content_type: 'image/jpeg'
      })

      // プログレス通知（完了）
      if (onProgress) {
        onProgress({
          current: i + 1,
          total: files.length,
          filename: file.name,
          status: 'completed'
        })
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '不明なエラー'
      errors.push(`${file.name}: ${errorMessage}`)

      // プログレス通知（エラー）
      if (onProgress) {
        onProgress({
          current: i + 1,
          total: files.length,
          filename: file.name,
          status: 'error'
        })
      }
    }
  }

  // すべての画像の処理に失敗した場合
  if (processedImages.length === 0) {
    throw new Error(`すべての画像の処理に失敗しました:\n${errors.join('\n')}`)
  }

  // ZIPファイルを作成（フロントエンドで作成）
  const zip = new JSZip()
  
  for (const img of processedImages) {
    // data:image/jpeg;base64,XXXXX から base64 部分を抽出
    const base64Data = img.data.split(',')[1]
    // Base64をバイナリに変換してZIPに追加
    zip.file(img.filename, base64Data, { base64: true })
  }

  // ZIPをBlobとして生成
  const zipBlob = await zip.generateAsync({ type: 'blob' })
  
  // BlobをBase64 data URLに変換
  const zipBase64 = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      resolve(result)
    }
    reader.onerror = reject
    reader.readAsDataURL(zipBlob)
  })

  return {
    images: processedImages,
    zip_data: zipBase64,
    zip_filename: 'processed_images.zip',
    errors: errors.length > 0 ? errors : null
  }
}


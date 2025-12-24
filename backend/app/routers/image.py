from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import Response, JSONResponse
from typing import Optional, List
from app.services.image_processor import ImageProcessor
import logging
import zipfile
import io
import base64

logger = logging.getLogger(__name__)
router = APIRouter()
processor = ImageProcessor()

# 最大ファイルサイズ: 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024
# 最大画像数: 8枚
MAX_IMAGES = 8

@router.post("/process")
async def process_image(
    file: UploadFile = File(...),
    mode: str = Form("vertical"),  # "vertical" or "horizontal"
    upscale_method: str = Form("simple")  # "simple" or "ai"
):
    """
    画像をリサイズ・アップスケール処理します。
    
    - mode: "vertical" (1080x1350) または "horizontal" (1350x1080)
    - upscale_method: "simple" (単純リサイズ) または "ai" (AIアップスケール)
    """
    # デバッグログ: 受信したパラメータを確認
    logger.info(f"画像処理リクエスト受信: mode={mode}, upscale_method={upscale_method}, filename={file.filename}")
    
    # パラメータ検証
    if mode not in ["vertical", "horizontal"]:
        raise HTTPException(
            status_code=400,
            detail="modeは'vertical'または'horizontal'である必要があります"
        )
    
    if upscale_method not in ["simple", "ai"]:
        raise HTTPException(
            status_code=400,
            detail="upscale_methodは'simple'または'ai'である必要があります"
        )
    
    # ファイルタイプ検証
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="画像ファイルをアップロードしてください"
        )
    
    try:
        # ファイルを読み込み
        contents = await file.read()
        
        # ファイルサイズチェック
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"ファイルサイズが大きすぎます。最大{MAX_FILE_SIZE // (1024 * 1024)}MBまで対応しています。"
            )
        
        if len(contents) == 0:
            raise HTTPException(
                status_code=400,
                detail="空のファイルは処理できません"
            )
        
        # 画像処理
        try:
            processed_image = await processor.process_image(
                image_data=contents,
                mode=mode,
                upscale_method=upscale_method
            )
        except ValueError as e:
            # 画像形式エラーなど
            logger.error(f"画像処理エラー (ValueError): {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"画像の形式が正しくありません: {str(e)}"
            )
        except Exception as e:
            # その他の処理エラー
            logger.error(f"画像処理エラー: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"画像処理中にエラーが発生しました: {str(e)}"
            )
        
        # 元のファイル形式を維持（可能な場合）
        content_type = file.content_type or "image/jpeg"
        
        return Response(
            content=processed_image,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=processed_{file.filename or 'image.jpg'}"
            }
        )
    except HTTPException:
        # HTTPExceptionはそのまま再発生
        raise
    except Exception as e:
        # 予期しないエラー
        logger.error(f"予期しないエラー: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="サーバーエラーが発生しました。しばらく時間をおいて再度お試しください。"
        )

@router.post("/process-multiple")
async def process_multiple_images(
    files: List[UploadFile] = File(...),
    mode: str = Form("vertical"),  # "vertical" or "horizontal"
    upscale_method: str = Form("simple")  # "simple" or "ai"
):
    """
    複数の画像をリサイズ・アップスケール処理します。
    
    - files: 最大8枚の画像ファイル
    - mode: "vertical" (1080x1350) または "horizontal" (1350x1080)
    - upscale_method: "simple" (単純リサイズ) または "ai" (AIアップスケール)
    """
    # デバッグログ: 受信したパラメータを確認
    logger.info(f"複数画像処理リクエスト受信: mode={mode}, upscale_method={upscale_method}, ファイル数={len(files)}")
    
    # パラメータ検証
    if mode not in ["vertical", "horizontal"]:
        raise HTTPException(
            status_code=400,
            detail="modeは'vertical'または'horizontal'である必要があります"
        )
    
    if upscale_method not in ["simple", "ai"]:
        raise HTTPException(
            status_code=400,
            detail="upscale_methodは'simple'または'ai'である必要があります"
        )
    
    # ファイル数チェック
    if len(files) > MAX_IMAGES:
        raise HTTPException(
            status_code=400,
            detail=f"画像は最大{MAX_IMAGES}枚までアップロードできます"
        )
    
    if len(files) == 0:
        raise HTTPException(
            status_code=400,
            detail="画像ファイルをアップロードしてください"
        )
    
    processed_images = []
    errors = []
    
    for idx, file in enumerate(files):
        try:
            # ファイルタイプ検証
            if not file.content_type or not file.content_type.startswith("image/"):
                errors.append(f"{file.filename or f'ファイル{idx+1}'}: 画像ファイルではありません")
                continue
            
            # ファイルを読み込み
            contents = await file.read()
            
            # ファイルサイズチェック
            if len(contents) > MAX_FILE_SIZE:
                errors.append(f"{file.filename or f'ファイル{idx+1}'}: ファイルサイズが大きすぎます（最大{MAX_FILE_SIZE // (1024 * 1024)}MB）")
                continue
            
            if len(contents) == 0:
                errors.append(f"{file.filename or f'ファイル{idx+1}'}: 空のファイルです")
                continue
            
            # 画像処理
            try:
                processed_image = await processor.process_image(
                    image_data=contents,
                    mode=mode,
                    upscale_method=upscale_method
                )
                
                processed_images.append({
                    "filename": file.filename or f"image_{idx+1}.jpg",
                    "data": processed_image,
                    "content_type": file.content_type or "image/jpeg"
                })
            except ValueError as e:
                errors.append(f"{file.filename or f'ファイル{idx+1}'}: {str(e)}")
            except Exception as e:
                logger.error(f"画像処理エラー ({file.filename}): {str(e)}", exc_info=True)
                errors.append(f"{file.filename or f'ファイル{idx+1}'}: 処理に失敗しました")
        except Exception as e:
            logger.error(f"予期しないエラー ({file.filename}): {str(e)}", exc_info=True)
            errors.append(f"{file.filename or f'ファイル{idx+1}'}: エラーが発生しました")
    
    # すべての画像の処理に失敗した場合
    if len(processed_images) == 0:
        error_message = "すべての画像の処理に失敗しました。\n" + "\n".join(errors)
        raise HTTPException(status_code=400, detail=error_message)
    
    # 各画像をBase64エンコードしてJSONで返す（プレビュー用）
    result_images = []
    for img in processed_images:
        # Base64エンコード
        img_base64 = base64.b64encode(img["data"]).decode('utf-8')
        result_images.append({
            "filename": img["filename"],
            "data": f"data:{img['content_type']};base64,{img_base64}",
            "content_type": img["content_type"]
        })
    
    # ZIPファイルも作成（ダウンロード用）
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for img in processed_images:
            zip_file.writestr(img["filename"], img["data"])
    zip_buffer.seek(0)
    zip_base64 = base64.b64encode(zip_buffer.read()).decode('utf-8')
    
    return JSONResponse(content={
        "images": result_images,
        "zip_data": f"data:application/zip;base64,{zip_base64}",
        "zip_filename": "processed_images.zip",
        "errors": errors if errors else None
    })


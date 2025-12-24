from http.server import BaseHTTPRequestHandler
import json
import base64
from io import BytesIO
from PIL import Image
import zipfile

# 規定サイズ
VERTICAL_SIZE = (1080, 1350)  # 幅×高さ
HORIZONTAL_SIZE = (1350, 1080)  # 幅×高さ

def resize_to_target(image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    """画像を指定サイズにリサイズ（余白なし）"""
    target_width, target_height = target_size
    original_width, original_height = image.size
    
    # アスペクト比を計算
    target_aspect = target_width / target_height
    original_aspect = original_width / original_height
    
    if abs(original_aspect - target_aspect) < 0.001:
        return image.resize(target_size, Image.Resampling.LANCZOS)
    
    if original_aspect > target_aspect:
        scale_factor = target_width / original_width
        new_width = target_width
        new_height = int(original_height * scale_factor)
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        if new_height >= target_height:
            crop_top = (new_height - target_height) // 2
            return resized.crop((0, crop_top, target_width, crop_top + target_height))
        else:
            scale_factor = target_height / original_height
            new_height = target_height
            new_width = int(original_width * scale_factor)
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            crop_left = (new_width - target_width) // 2
            return resized.crop((crop_left, 0, crop_left + target_width, target_height))
    else:
        scale_factor = target_height / original_height
        new_height = target_height
        new_width = int(original_width * scale_factor)
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        if new_width >= target_width:
            crop_left = (new_width - target_width) // 2
            return resized.crop((crop_left, 0, crop_left + target_width, target_height))
        else:
            scale_factor = target_width / original_width
            new_width = target_width
            new_height = int(original_height * scale_factor)
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            crop_top = (new_height - target_height) // 2
            return resized.crop((0, crop_top, target_width, crop_top + target_height))

def process_image_sync(image_data: bytes, mode: str) -> bytes:
    """同期的な画像処理（軽量版：Pillowのみ）"""
    image = Image.open(BytesIO(image_data))
    
    if image.mode != "RGB":
        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3] if image.mode == "RGBA" else None)
            image = background
        else:
            image = image.convert("RGB")
    
    target_size = VERTICAL_SIZE if mode == "vertical" else HORIZONTAL_SIZE
    resized_image = resize_to_target(image, target_size)
    
    if resized_image.size != target_size:
        resized_image = resized_image.resize(target_size, Image.Resampling.LANCZOS)
    
    output = BytesIO()
    resized_image.save(output, format="JPEG", quality=95)
    output.seek(0)
    return output.read()

def handler(req):
    """Vercel Serverless Function handler"""
    # CORS preflight リクエストを処理
    if req.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
            'body': ''
        }
    
    if req.method != 'POST':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'success': False, 'error': 'Method not allowed'})
        }
    
    try:
        # リクエストボディを取得
        body = req.body
        if isinstance(body, str):
            data = json.loads(body)
        else:
            data = json.loads(body.decode('utf-8') if isinstance(body, bytes) else body)
        
        # 複数画像データを取得
        images_data = data.get('images', [])
        mode = data.get('mode', 'vertical')
        upscale_method = data.get('upscale_method', 'simple')
        
        processed_images = []
        errors = []
        
        for idx, img_data in enumerate(images_data):
            try:
                image_base64 = img_data.get('image', '')
                filename = img_data.get('filename', f'image_{idx+1}.jpg')
                
                # Base64デコード
                image_data = base64.b64decode(image_base64)
                
                # 画像処理
                processed_image = process_image_sync(image_data, mode)
                
                # Base64エンコード
                result_base64 = base64.b64encode(processed_image).decode('utf-8')
                
                processed_images.append({
                    'filename': filename,
                    'data': f'data:image/jpeg;base64,{result_base64}',
                    'content_type': 'image/jpeg'
                })
            except Exception as e:
                errors.append(f"{img_data.get('filename', f'ファイル{idx+1}')}: {str(e)}")
        
        if len(processed_images) == 0:
            raise Exception("すべての画像の処理に失敗しました")
        
        # ZIPファイルも作成
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for img in processed_images:
                img_bytes = base64.b64decode(img['data'].split(',')[1])
                zip_file.writestr(img['filename'], img_bytes)
        zip_buffer.seek(0)
        zip_base64 = base64.b64encode(zip_buffer.read()).decode('utf-8')
        
        # レスポンス
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': True,
                'images': processed_images,
                'zip_data': f'data:application/zip;base64,{zip_base64}',
                'zip_filename': 'processed_images.zip',
                'errors': errors if errors else None
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

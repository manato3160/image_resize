from PIL import Image
import io
import numpy as np
from typing import Literal, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

class ImageProcessor:
    # 規定サイズ
    VERTICAL_SIZE = (1080, 1350)  # 幅×高さ
    HORIZONTAL_SIZE = (1350, 1080)  # 幅×高さ
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._ai_upscaler: Optional[object] = None
        self._ai_available = False
        self._check_ai_availability()
    
    async def process_image(
        self,
        image_data: bytes,
        mode: Literal["vertical", "horizontal"],
        upscale_method: Literal["simple", "ai"]
    ) -> bytes:
        """
        画像を処理します。
        
        Args:
            image_data: 画像のバイトデータ
            mode: リサイズモード（"vertical" または "horizontal"）
            upscale_method: アップスケール方法（"simple" または "ai"）
        
        Returns:
            処理済み画像のバイトデータ
        """
        # 同期的な処理を非同期で実行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._process_image_sync,
            image_data,
            mode,
            upscale_method
        )
    
    def _process_image_sync(
        self,
        image_data: bytes,
        mode: Literal["vertical", "horizontal"],
        upscale_method: Literal["simple", "ai"]
    ) -> bytes:
        """同期的な画像処理"""
        try:
            # 画像を開く
            image = Image.open(io.BytesIO(image_data))
            
            # 画像が正常に読み込めたか確認
            image.verify()
            
            # verify()は画像を閉じるので、再度開く必要がある
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            raise ValueError(f"画像ファイルを読み込めませんでした: {str(e)}")
        
        # RGBに変換（RGBAやPモードなどに対応）
        try:
            if image.mode != "RGB":
                if image.mode == "RGBA":
                    # 透明部分を白で塗りつぶし
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[3] if image.mode == "RGBA" else None)
                    image = background
                else:
                    image = image.convert("RGB")
        except Exception as e:
            raise ValueError(f"画像の色空間変換に失敗しました: {str(e)}")
        
        # ターゲットサイズを決定
        target_size = self.VERTICAL_SIZE if mode == "vertical" else self.HORIZONTAL_SIZE
        logger.info(f"モード: {mode}, ターゲットサイズ: {target_size}")
        
        # リサイズ
        try:
            resized_image = self._resize_to_target(image, target_size)
            # 確実にターゲットサイズになっているか確認
            if resized_image.size != target_size:
                logger.warning(f"リサイズ後のサイズが期待と異なります: {resized_image.size} != {target_size}。再リサイズします。")
                resized_image = resized_image.resize(target_size, Image.Resampling.LANCZOS)
        except Exception as e:
            raise ValueError(f"画像のリサイズに失敗しました: {str(e)}")
        
        # アップスケール
        try:
            if upscale_method == "ai":
                upscaled_image = self._upscale_ai(resized_image, target_size)
            else:
                upscaled_image = self._upscale_simple(resized_image)
        except Exception as e:
            raise ValueError(f"画像のアップスケールに失敗しました: {str(e)}")
        
        # 最終的に確実にターゲットサイズになっているか確認
        if upscaled_image.size != target_size:
            logger.warning(f"アップスケール後のサイズが期待と異なります: {upscaled_image.size} != {target_size}。再リサイズします。")
            upscaled_image = upscaled_image.resize(target_size, Image.Resampling.LANCZOS)
        
        # バイトデータに変換
        try:
            output = io.BytesIO()
            upscaled_image.save(output, format="JPEG", quality=95)
            output.seek(0)
            return output.read()
        except Exception as e:
            raise ValueError(f"画像の保存に失敗しました: {str(e)}")
    
    def _resize_to_target(self, image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
        """
        画像を指定サイズにリサイズします。
        アスペクト比を維持しつつ、必要に応じてクロップを行います。
        余白を含まないように、確実にターゲットサイズにクロップします。
        最終的に確実にtarget_sizeのサイズになります。
        """
        target_width, target_height = target_size
        original_width, original_height = image.size
        
        logger.info(f"リサイズ開始: 元のサイズ={image.size}, ターゲットサイズ={target_size}")
        
        # アスペクト比を計算
        target_aspect = target_width / target_height
        original_aspect = original_width / original_height
        
        logger.info(f"アスペクト比: 元={original_aspect:.3f}, ターゲット={target_aspect:.3f}")
        
        if abs(original_aspect - target_aspect) < 0.001:
            # アスペクト比がほぼ同じ場合、直接リサイズ
            logger.info("アスペクト比が同じため、直接リサイズします")
            resized = image.resize(target_size, Image.Resampling.LANCZOS)
            return resized
        
        if original_aspect > target_aspect:
            # 元の画像がターゲットより横長 → 幅をターゲット幅に合わせてリサイズし、高さをクロップ
            # 余白を避けるため、ターゲット幅に合わせる
            scale_factor = target_width / original_width
            new_width = target_width
            new_height = int(original_height * scale_factor)
            logger.info(f"横長画像: スケール={scale_factor:.3f}, リサイズサイズ=({new_width}, {new_height})")
            
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 高さがターゲットより大きい場合、中央でクロップ（余白を避ける）
            if new_height >= target_height:
                crop_top = (new_height - target_height) // 2
                cropped = resized.crop((0, crop_top, target_width, crop_top + target_height))
                logger.info(f"高さをクロップ: crop_top={crop_top}, 結果サイズ={cropped.size}")
            else:
                # 高さが足りない場合は、幅を拡大してからクロップ
                logger.warning(f"高さが足りません: {new_height} < {target_height}。再計算します。")
                scale_factor = target_height / original_height
                new_height = target_height
                new_width = int(original_width * scale_factor)
                resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                crop_left = (new_width - target_width) // 2
                cropped = resized.crop((crop_left, 0, crop_left + target_width, target_height))
                logger.info(f"幅をクロップ: crop_left={crop_left}, 結果サイズ={cropped.size}")
        else:
            # 元の画像がターゲットより縦長 → 高さをターゲット高さに合わせてリサイズし、幅をクロップ
            # 余白を避けるため、ターゲット高さに合わせる
            scale_factor = target_height / original_height
            new_height = target_height
            new_width = int(original_width * scale_factor)
            logger.info(f"縦長画像: スケール={scale_factor:.3f}, リサイズサイズ=({new_width}, {new_height})")
            
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 幅がターゲットより大きい場合、中央でクロップ（余白を避ける）
            if new_width >= target_width:
                crop_left = (new_width - target_width) // 2
                cropped = resized.crop((crop_left, 0, crop_left + target_width, target_height))
                logger.info(f"幅をクロップ: crop_left={crop_left}, 結果サイズ={cropped.size}")
            else:
                # 幅が足りない場合は、高さを拡大してからクロップ
                logger.warning(f"幅が足りません: {new_width} < {target_width}。再計算します。")
                scale_factor = target_width / original_width
                new_width = target_width
                new_height = int(original_height * scale_factor)
                resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                crop_top = (new_height - target_height) // 2
                cropped = resized.crop((0, crop_top, target_width, crop_top + target_height))
                logger.info(f"高さをクロップ: crop_top={crop_top}, 結果サイズ={cropped.size}")
        
        logger.info(f"リサイズ完了: 最終サイズ={cropped.size}, ターゲット={target_size}")
        
        # 最終確認 - サイズが一致しない場合はエラー
        if cropped.size != target_size:
            raise ValueError(f"リサイズに失敗しました: 最終サイズ={cropped.size}, ターゲット={target_size}")
        
        return cropped
    
    def _upscale_simple(self, image: Image.Image) -> Image.Image:
        """
        単純なリサイズによるアップスケール（高品質なリサンプリング）
        """
        # 既に規定サイズになっているので、そのまま返す
        # 将来的にさらにアップスケールする場合はここで処理
        return image
    
    def _check_ai_availability(self):
        """AIアップスケーラーの利用可能性をチェック"""
        try:
            import realesrgan
            self._ai_available = True
            logger.info("Real-ESRGANが利用可能です")
        except ImportError:
            self._ai_available = False
            logger.warning("Real-ESRGANがインストールされていません。AIアップスケールは利用できません。")
    
    def _init_ai_upscaler(self):
        """AIアップスケーラーを初期化（遅延初期化）"""
        if not self._ai_available:
            raise ImportError("Real-ESRGANが利用できません")
        
        if self._ai_upscaler is not None:
            return self._ai_upscaler
        
        try:
            from realesrgan import RealESRGANer
            import cv2
            
            # Real-ESRGANのモデルを初期化
            # 一般的な画像用のモデルを使用
            upsampler = RealESRGANer(
                scale=4,  # 4倍アップスケール
                model_path='https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth',
                model=None,  # モデルは自動的にダウンロードされる
                tile=0,
                tile_pad=10,
                pre_pad=0,
                half=False  # CPUの場合はFalse
            )
            
            self._ai_upscaler = upsampler
            logger.info("AIアップスケーラーを初期化しました")
            return upsampler
        except Exception as e:
            logger.error(f"AIアップスケーラーの初期化に失敗しました: {e}")
            self._ai_available = False
            raise
    
    def _upscale_ai(self, image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
        """
        AIベースのアップスケール（Real-ESRGANを使用）
        
        Args:
            image: リサイズ済みの画像
            target_size: 最終的なターゲットサイズ（幅, 高さ）
        """
        if not self._ai_available:
            logger.warning("AIアップスケールが利用できないため、単純リサイズにフォールバックします")
            return self._upscale_simple(image)
        
        try:
            import cv2
            
            # アップスケーラーを初期化
            upsampler = self._init_ai_upscaler()
            
            # PIL画像をnumpy配列に変換
            img_array = np.array(image)
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # アップスケール
            output, _ = upsampler.enhance(img_array, outscale=4)
            
            # BGRからRGBに変換
            output = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
            
            # PIL画像に変換
            upscaled_image = Image.fromarray(output)
            
            # ターゲットサイズに確実にリサイズ（AIアップスケールで大きくなった場合）
            if upscaled_image.size != target_size:
                upscaled_image = upscaled_image.resize(target_size, Image.Resampling.LANCZOS)
            
            return upscaled_image
        except ImportError:
            # Real-ESRGANが利用できない場合は単純リサイズにフォールバック
            logger.warning("Real-ESRGANのインポートに失敗しました。単純リサイズにフォールバックします。")
            self._ai_available = False
            return self._upscale_simple(image)
        except Exception as e:
            # エラーが発生した場合は単純リサイズにフォールバック
            logger.error(f"AIアップスケールエラー: {e}", exc_info=True)
            return self._upscale_simple(image)


# ==================== utils/image_processor.py ====================

from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from django.core.files.base import ContentFile
from django.conf import settings
import io
import os
import math


class ShelfImageProcessor:
    """棚割り画像処理クラス"""
    
    def __init__(self, shelf):
        self.shelf = shelf
        self.cell_width_px = 80   # 1セルの幅（ピクセル）
        self.cell_height_px = 80  # 1セルの高さ（ピクセル）
        self.padding = 10
    
    def generate_shelf_layout_image(self, placements, output_format='PNG', high_resolution=False):
        """棚割りレイアウト画像を生成"""
        
        # 高解像度モード
        scale = 3 if high_resolution else 1
        cell_w = self.cell_width_px * scale
        cell_h = self.cell_height_px * scale
        padding = self.padding * scale
        
        # キャンバスサイズ計算
        canvas_width = self.shelf.columns * cell_w + padding * 2
        canvas_height = self.shelf.rows * cell_h + padding * 2 + 100 * scale  # ヘッダー用余白
        
        # 背景画像作成
        img = Image.new('RGB', (canvas_width, canvas_height), color='#f8f9fa')
        draw = ImageDraw.Draw(img)
        
        # フォント設定
        try:
            title_font = ImageFont.truetype("arial.ttf", 24 * scale)
            product_font = ImageFont.truetype("arial.ttf", 10 * scale)
            small_font = ImageFont.truetype("arial.ttf", 8 * scale)
        except:
            title_font = ImageFont.load_default()
            product_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # タイトル描画
        title = f"{self.shelf.name} - 棚割りレイアウト"
        draw.text((padding, padding), title, fill='#333333', font=title_font)
        
        # 棚情報描画
        info_text = f"{self.shelf.width}×{self.shelf.height}×{self.shelf.depth}cm | {self.shelf.rows}段×{self.shelf.columns}列"
        draw.text((padding, padding + 35 * scale), info_text, fill='#666666', font=product_font)
        
        # グリッド描画
        grid_start_y = padding + 80 * scale
        
        # セルの枠線
        for row in range(self.shelf.rows + 1):
            y = grid_start_y + row * cell_h
            draw.line([(padding, y), (canvas_width - padding, y)], fill='#dee2e6', width=1)
        
        for col in range(self.shelf.columns + 1):
            x = padding + col * cell_w
            draw.line([(x, grid_start_y), (x, grid_start_y + self.shelf.rows * cell_h)], fill='#dee2e6', width=1)
        
        # 座標ラベル
        for col in range(self.shelf.columns):
            x = padding + col * cell_w + cell_w // 2
            draw.text((x - 5 * scale, grid_start_y - 20 * scale), str(col + 1), fill='#6c757d', font=small_font)
        
        for row in range(self.shelf.rows):
            y = grid_start_y + row * cell_h + cell_h // 2
            draw.text((padding - 25 * scale, y - 5 * scale), str(row + 1), fill='#6c757d', font=small_font)
        
        # 商品配置描画
        for placement in placements:
            self._draw_product_placement(img, placement, grid_start_y, cell_w, cell_h, padding, scale, product_font, small_font)
        
        # 凡例描画
        self._draw_legend(img, canvas_width, canvas_height, padding, scale, product_font)
        
        # バイト配列に変換
        buffer = io.BytesIO()
        img.save(buffer, format=output_format, quality=95 if output_format == 'JPEG' else None)
        buffer.seek(0)
        
        return buffer.getvalue()
    
    def _draw_product_placement(self, img, placement, grid_start_y, cell_w, cell_h, padding, scale, product_font, small_font):
        """個別商品配置を描画"""
        draw = ImageDraw.Draw(img)
        
        # 配置位置計算
        x = padding + placement.column * cell_w
        y = grid_start_y + placement.row * cell_h
        width = placement.span_columns * cell_w
        height = placement.span_rows * cell_h
        
        # 商品背景色
        bg_color = '#d4edda' if placement.product.is_own_product else '#fff3cd'
        border_color = '#c3e6cb' if placement.product.is_own_product else '#ffeaa7'
        
        # 背景矩形
        draw.rectangle([x + 2, y + 2, x + width - 2, y + height - 2], 
                      fill=bg_color, outline=border_color, width=2)
        
        # 商品画像の描画
        if placement.product.image:
            try:
                product_img = self._resize_product_image(placement.product.image.path, 
                                                       int(width * 0.6), int(height * 0.4))
                if product_img:
                    img_x = x + (width - product_img.width) // 2
                    img_y = y + 5 * scale
                    img.paste(product_img, (img_x, img_y))
            except Exception as e:
                print(f"商品画像読み込みエラー: {e}")
        
        # 商品名描画
        product_name = placement.product.product_name
        if len(product_name) > 15:
            product_name = product_name[:15] + "..."
        
        text_y = y + height * 0.6
        self._draw_wrapped_text(draw, product_name, x + 5 * scale, text_y, 
                               width - 10 * scale, product_font, '#333333')
        
        # メーカー名
        maker_name = placement.product.maker.name
        if len(maker_name) > 12:
            maker_name = maker_name[:12] + "..."
        
        draw.text((x + 5 * scale, y + height * 0.8), maker_name, 
                 fill='#6c757d', font=small_font)
        
        # フェース数バッジ
        if placement.face_count > 1:
            badge_size = 20 * scale
            badge_x = x + width - badge_size - 5 * scale
            badge_y = y + 5 * scale
            
            draw.ellipse([badge_x, badge_y, badge_x + badge_size, badge_y + badge_size], 
                        fill='#007bff', outline='#0056b3')
            
            # フェース数テキスト
            face_text = str(placement.face_count)
            bbox = draw.textbbox((0, 0), face_text, font=small_font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            text_x = badge_x + (badge_size - text_w) // 2
            text_y = badge_y + (badge_size - text_h) // 2
            draw.text((text_x, text_y), face_text, fill='white', font=small_font)
        
        # サイズ情報
        if placement.span_rows > 1 or placement.span_columns > 1:
            size_text = f"{placement.span_rows}×{placement.span_columns}"
            draw.text((x + 5 * scale, y + height - 20 * scale), size_text, 
                     fill='#495057', font=small_font)
    
    def _resize_product_image(self, image_path, max_width, max_height):
        """商品画像をリサイズ"""
        try:
            with Image.open(image_path) as img:
                # RGBAをRGBに変換
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                
                # サムネイル作成
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                return img.copy()
        except Exception as e:
            print(f"画像リサイズエラー: {e}")
            return None
    
    def _draw_wrapped_text(self, draw, text, x, y, max_width, font, fill):
        """テキストを折り返して描画"""
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    lines.append(word)
        
        if current_line:
            lines.append(current_line)
        
        # 描画
        line_height = 15
        for i, line in enumerate(lines[:2]):  # 最大2行
            draw.text((x, y + i * line_height), line, fill=fill, font=font)
    
    def _draw_legend(self, img, canvas_width, canvas_height, padding, scale, font):
        """凡例を描画"""
        draw = ImageDraw.Draw(img)
        
        legend_y = canvas_height - 40 * scale
        legend_items = [
            ('#d4edda', '自社商品'),
            ('#fff3cd', '競合商品'),
        ]
        
        x_offset = padding
        for color, label in legend_items:
            # 色サンプル
            sample_size = 15 * scale
            draw.rectangle([x_offset, legend_y, x_offset + sample_size, legend_y + sample_size], 
                          fill=color, outline='#333333')
            
            # ラベル
            draw.text((x_offset + sample_size + 5 * scale, legend_y + 2 * scale), 
                     label, fill='#333333', font=font)
            
            x_offset += 120 * scale

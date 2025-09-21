# ==================== shelves/models.py ====================
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from products.models import Product
import math


class Shelf(models.Model):
    """棚マスタ"""
    name = models.CharField('棚名', max_length=100)
    description = models.TextField('説明', blank=True)
    width = models.FloatField('幅(cm)', validators=[MinValueValidator(1)])
    height = models.FloatField('高さ(cm)', validators=[MinValueValidator(1)])
    depth = models.FloatField('奥行(cm)', validators=[MinValueValidator(1)])
    rows = models.IntegerField('段数', validators=[MinValueValidator(1), MaxValueValidator(20)])
    columns = models.IntegerField('列数', validators=[MinValueValidator(1), MaxValueValidator(20)])
    
    # セルサイズ（自動計算または手動設定）
    cell_width = models.FloatField('セル幅(cm)', null=True, blank=True, help_text='空白の場合は自動計算')
    cell_height = models.FloatField('セル高さ(cm)', null=True, blank=True, help_text='空白の場合は自動計算')
    
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='作成者')
    
    class Meta:
        verbose_name = '棚'
        verbose_name_plural = '棚'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def total_cells(self):
        return self.rows * self.columns
    
    @property
    def calculated_cell_width(self):
        """計算されたセル幅（cm）"""
        if self.cell_width:
            return self.cell_width
        return self.width / self.columns
    
    @property
    def calculated_cell_height(self):
        """計算されたセル高さ（cm）"""
        if self.cell_height:
            return self.cell_height
        return self.height / self.rows
    
    def can_place_product(self, product, row, column, face_count=1):
        """商品が配置可能かチェック"""
        if not product.width or not product.height:
            # サイズ情報がない場合は1セルとして扱う
            return self.can_place_cells(row, column, 1, 1)
        
        # 必要なセル数を計算
        required_cells = self.calculate_required_cells(product, face_count)
        
        return self.can_place_cells(
            row, column, 
            required_cells['span_rows'], 
            required_cells['span_columns']
        )
    
    def can_place_cells(self, row, column, span_rows, span_columns):
        """指定されたセル範囲が配置可能かチェック"""
        # 範囲チェック
        if row + span_rows > self.rows or column + span_columns > self.columns:
            return False
        
        # 既存配置との重複チェック
        for r in range(row, row + span_rows):
            for c in range(column, column + span_columns):
                if ShelfPlacement.objects.filter(shelf=self, row=r, column=c).exists():
                    return False
        
        return True
    
    def calculate_required_cells(self, product, face_count=1):
        """商品配置に必要なセル数を計算"""
        if not product.width or not product.height:
            return {'span_rows': 1, 'span_columns': 1}
        
        # フェース分を考慮した実際の占有幅
        total_product_width = product.width * face_count
        
        # 必要セル数を計算（切り上げ）
        span_columns = math.ceil(total_product_width / self.calculated_cell_width)
        span_rows = math.ceil(product.height / self.calculated_cell_height)
        
        # 最低1セルは確保
        span_columns = max(1, span_columns)
        span_rows = max(1, span_rows)
        
        # 棚の範囲を超えないよう制限
        span_columns = min(span_columns, self.columns)
        span_rows = min(span_rows, self.rows)
        
        return {
            'span_rows': span_rows,
            'span_columns': span_columns,
            'fit_ratio_width': min(1.0, total_product_width / (span_columns * self.calculated_cell_width)),
            'fit_ratio_height': min(1.0, product.height / (span_rows * self.calculated_cell_height))
        }


class ShelfPlacement(models.Model):
    """棚配置"""
    shelf = models.ForeignKey(Shelf, on_delete=models.CASCADE, verbose_name='棚')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='商品')
    row = models.IntegerField('段', validators=[MinValueValidator(0)])
    column = models.IntegerField('列', validators=[MinValueValidator(0)])
    face_count = models.IntegerField('フェース数', default=1, validators=[MinValueValidator(1)])
    span_rows = models.IntegerField('占有段数', default=1, validators=[MinValueValidator(1)])
    span_columns = models.IntegerField('占有列数', default=1, validators=[MinValueValidator(1)])
    
    # 表示サイズ制御
    display_width_ratio = models.FloatField('表示幅比率', default=1.0, validators=[MinValueValidator(0.1), MaxValueValidator(2.0)])
    display_height_ratio = models.FloatField('表示高さ比率', default=1.0, validators=[MinValueValidator(0.1), MaxValueValidator(2.0)])
    
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='作成者')
    
    class Meta:
        verbose_name = '棚配置'
        verbose_name_plural = '棚配置'
        # 同じ商品が複数セルにまたがる場合があるため、unique_togetherは削除
        indexes = [
            models.Index(fields=['shelf', 'row', 'column']),
        ]
    
    def __str__(self):
        return f"{self.shelf.name} - {self.product.product_name} ({self.row+1}段{self.column+1}列)"
    
    @property
    def occupied_cells(self):
        """占有しているセルの座標リスト"""
        cells = []
        for r in range(self.row, self.row + self.span_rows):
            for c in range(self.column, self.column + self.span_columns):
                cells.append((r, c))
        return cells
    
    @property
    def total_width_cm(self):
        """実際の占有幅（cm）"""
        return self.product.width * self.face_count if self.product.width else 0
    
    @property
    def total_height_cm(self):
        """実際の占有高さ（cm）"""
        return self.product.height if self.product.height else 0
    
    def save(self, *args, **kwargs):
        # 保存前に必要なセル数を自動計算
        if self.shelf and self.product:
            required = self.shelf.calculate_required_cells(self.product, self.face_count)
            self.span_rows = required['span_rows']
            self.span_columns = required['span_columns']
            self.display_width_ratio = required.get('fit_ratio_width', 1.0)
            self.display_height_ratio = required.get('fit_ratio_height', 1.0)
        
        super().save(*args, **kwargs)
    
    def get_display_style(self):
        """CSS用の表示スタイルを生成"""
        return {
            'grid-row-start': self.row + 1,
            'grid-row-end': self.row + self.span_rows + 1,
            'grid-column-start': self.column + 1,
            'grid-column-end': self.column + self.span_columns + 1,
            'width': f'{self.display_width_ratio * 100}%',
            'height': f'{self.display_height_ratio * 100}%',
        }


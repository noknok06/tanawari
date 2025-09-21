from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from PIL import Image
import os


class Maker(models.Model):
    """メーカーマスタ"""
    name = models.CharField('メーカー名', max_length=100, unique=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='作成者')
    
    class Meta:
        verbose_name = 'メーカー'
        verbose_name_plural = 'メーカー'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Brand(models.Model):
    """ブランドマスタ"""
    maker = models.ForeignKey(Maker, on_delete=models.CASCADE, verbose_name='メーカー')
    name = models.CharField('ブランド名', max_length=100)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='作成者')
    
    class Meta:
        verbose_name = 'ブランド'
        verbose_name_plural = 'ブランド'
        ordering = ['maker__name', 'name']
        unique_together = ['maker', 'name']
    
    def __str__(self):
        return f"{self.maker.name} - {self.name}"


class Category(models.Model):
    """カテゴリマスタ"""
    name = models.CharField('カテゴリ名', max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name='親カテゴリ')
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='作成者')
    
    class Meta:
        verbose_name = 'カテゴリ'
        verbose_name_plural = 'カテゴリ'
        ordering = ['name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Product(models.Model):
    """商品マスタ"""
    product_name = models.CharField('商品名', max_length=200)
    product_code = models.CharField('JANコード', max_length=50, unique=True)
    maker = models.ForeignKey(Maker, on_delete=models.CASCADE, verbose_name='メーカー')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null=True, blank=True, verbose_name='ブランド')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='カテゴリ')
    size = models.CharField('容量・規格', max_length=100, blank=True)
    price = models.DecimalField('価格', max_digits=10, decimal_places=2, null=True, blank=True)
    width = models.FloatField('幅(cm)', null=True, blank=True, validators=[MinValueValidator(0.1)])
    height = models.FloatField('高さ(cm)', null=True, blank=True, validators=[MinValueValidator(0.1)])
    depth = models.FloatField('奥行(cm)', null=True, blank=True, validators=[MinValueValidator(0.1)])
    image = models.ImageField('商品画像', upload_to='products/', null=True, blank=True)
    is_own_product = models.BooleanField('自社商品', default=False)
    is_active = models.BooleanField('有効', default=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='作成者')
    
    class Meta:
        verbose_name = '商品'
        verbose_name_plural = '商品'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.product_name
    
    @property
    def has_size_info(self):
        """サイズ情報が設定されているか"""
        return bool(self.width and self.height)
    
    @property
    def display_size(self):
        """表示用サイズ文字列"""
        if not self.has_size_info:
            return "サイズ未設定"
        
        if self.depth:
            return f"{self.width}×{self.height}×{self.depth}cm"
        else:
            return f"{self.width}×{self.height}cm"
        

class ProductSizeCategory(models.Model):
    """商品サイズカテゴリ"""
    name = models.CharField('カテゴリ名', max_length=50)
    min_width = models.FloatField('最小幅(cm)', validators=[MinValueValidator(0)])
    max_width = models.FloatField('最大幅(cm)', validators=[MinValueValidator(0)])
    min_height = models.FloatField('最小高さ(cm)', validators=[MinValueValidator(0)])
    max_height = models.FloatField('最大高さ(cm)', validators=[MinValueValidator(0)])
    color_code = models.CharField('表示色', max_length=7, default='#007bff')
    icon = models.CharField('アイコン', max_length=50, default='bi-box')
    
    class Meta:
        verbose_name = '商品サイズカテゴリ'
        verbose_name_plural = '商品サイズカテゴリ'
        ordering = ['min_width', 'min_height']
    
    def __str__(self):
        return f"{self.name} ({self.min_width}×{self.min_height}〜{self.max_width}×{self.max_height}cm)"


class Product(models.Model):
    """商品マスタ - サイズ機能強化"""
    product_name = models.CharField('商品名', max_length=200)
    product_code = models.CharField('JANコード', max_length=50, unique=True)
    maker = models.ForeignKey('Maker', on_delete=models.CASCADE, verbose_name='メーカー')
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE, null=True, blank=True, verbose_name='ブランド')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, verbose_name='カテゴリ')
    size = models.CharField('容量・規格', max_length=100, blank=True)
    price = models.DecimalField('価格', max_digits=10, decimal_places=2, null=True, blank=True)
    
    # サイズ情報強化
    width = models.FloatField('幅(cm)', null=True, blank=True, validators=[MinValueValidator(0.1)])
    height = models.FloatField('高さ(cm)', null=True, blank=True, validators=[MinValueValidator(0.1)])
    depth = models.FloatField('奥行(cm)', null=True, blank=True, validators=[MinValueValidator(0.1)])
    
    # 新規追加：サイズ管理
    weight = models.FloatField('重量(g)', null=True, blank=True, validators=[MinValueValidator(0)])
    volume = models.FloatField('体積(ml)', null=True, blank=True, validators=[MinValueValidator(0)])
    size_category = models.ForeignKey(ProductSizeCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='サイズカテゴリ')
    
    # サイズ測定情報
    size_measured_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='measured_products', verbose_name='サイズ測定者')
    size_measured_at = models.DateTimeField('サイズ測定日時', null=True, blank=True)
    size_accuracy = models.CharField('測定精度', max_length=20, choices=[
        ('estimated', '推定値'),
        ('measured', '実測値'),
        ('official', '公式データ'),
    ], default='estimated')
    
    # 画像・表示関連
    image = models.ImageField('商品画像', upload_to='products/', null=True, blank=True)
    image_thumbnail = models.ImageField('サムネイル', upload_to='products/thumbnails/', null=True, blank=True)
    
    # 配置関連設定
    min_face_count = models.IntegerField('最小フェース数', default=1, validators=[MinValueValidator(1)])
    max_face_count = models.IntegerField('最大フェース数', default=10, validators=[MinValueValidator(1)])
    recommended_face_count = models.IntegerField('推奨フェース数', default=1, validators=[MinValueValidator(1)])
    
    # フラグ
    is_own_product = models.BooleanField('自社商品', default=False)
    is_active = models.BooleanField('有効', default=True)
    requires_special_handling = models.BooleanField('特別扱い商品', default=False, help_text='壊れやすい、重い等')
    
    # メタデータ
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='作成者')
    
    class Meta:
        verbose_name = '商品'
        verbose_name_plural = '商品'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['width', 'height']),
            models.Index(fields=['size_category']),
            models.Index(fields=['is_own_product', 'is_active']),
        ]
    
    def __str__(self):
        return self.product_name
    
    def save(self, *args, **kwargs):
        # サイズカテゴリの自動設定
        if self.width and self.height and not self.size_category:
            self.size_category = self.get_size_category()
        
        # サムネイル生成
        if self.image and not self.image_thumbnail:
            self.generate_thumbnail()
        
        super().save(*args, **kwargs)
    
    def get_size_category(self):
        """サイズに基づいてカテゴリを自動判定"""
        if not (self.width and self.height):
            return None
        
        categories = ProductSizeCategory.objects.filter(
            min_width__lte=self.width,
            max_width__gte=self.width,
            min_height__lte=self.height,
            max_height__gte=self.height
        ).first()
        
        return categories
    
    def generate_thumbnail(self):
        """サムネイル画像を生成"""
        if not self.image:
            return
        
        try:
            # PILで画像を開く
            img = Image.open(self.image.path)
            
            # サムネイルサイズ（150x150）
            img.thumbnail((150, 150), Image.Resampling.LANCZOS)
            
            # 保存パスを設定
            thumb_name = f"thumb_{os.path.basename(self.image.name)}"
            thumb_path = os.path.join('products/thumbnails/', thumb_name)
            
            # サムネイルを保存
            full_thumb_path = os.path.join('media', thumb_path)
            os.makedirs(os.path.dirname(full_thumb_path), exist_ok=True)
            img.save(full_thumb_path, format='JPEG', quality=85)
            
            # モデルフィールドに設定
            self.image_thumbnail = thumb_path
            
        except Exception as e:
            print(f"サムネイル生成エラー: {e}")
    
    @property
    def has_size_info(self):
        """サイズ情報が設定されているか"""
        return bool(self.width and self.height)
    
    @property
    def volume_calculated(self):
        """計算された体積（cm³）"""
        if self.width and self.height and self.depth:
            return self.width * self.height * self.depth
        return None
    
    @property
    def display_size(self):
        """表示用サイズ文字列"""
        if not self.has_size_info:
            return "サイズ未設定"
        
        if self.depth:
            return f"{self.width}×{self.height}×{self.depth}cm"
        else:
            return f"{self.width}×{self.height}cm"
    
    @property
    def size_status_color(self):
        """サイズ測定状況の表示色"""
        return {
            'estimated': '#ffc107',  # 黄色
            'measured': '#28a745',   # 緑色
            'official': '#007bff',   # 青色
        }.get(self.size_accuracy, '#6c757d')
    
    def calculate_shelf_compatibility(self, shelf):
        """指定棚との適合性を計算"""
        if not self.has_size_info:
            return {
                'compatible': True,
                'reason': 'サイズ未設定のため1セルとして扱います',
                'required_cells': 1,
                'fit_ratio': 1.0
            }
        
        required_cells = shelf.calculate_required_cells(self)
        max_possible_cells = shelf.rows * shelf.columns
        
        compatible = (
            required_cells['span_rows'] <= shelf.rows and
            required_cells['span_columns'] <= shelf.columns
        )
        
        if not compatible:
            reason = f"商品が大きすぎます（{required_cells['span_rows']}×{required_cells['span_columns']}セル必要）"
        elif required_cells['span_rows'] * required_cells['span_columns'] > max_possible_cells * 0.5:
            reason = "大型商品のため配置位置が制限されます"
        else:
            reason = "配置可能"
        
        return {
            'compatible': compatible,
            'reason': reason,
            'required_cells': required_cells['span_rows'] * required_cells['span_columns'],
            'fit_ratio': min(required_cells.get('fit_ratio_width', 1.0), required_cells.get('fit_ratio_height', 1.0))
        }


class ProductSizeMeasurement(models.Model):
    """商品サイズ測定履歴"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='size_measurements')
    measured_width = models.FloatField('測定幅(cm)', validators=[MinValueValidator(0.1)])
    measured_height = models.FloatField('測定高さ(cm)', validators=[MinValueValidator(0.1)])
    measured_depth = models.FloatField('測定奥行(cm)', null=True, blank=True, validators=[MinValueValidator(0.1)])
    measured_weight = models.FloatField('測定重量(g)', null=True, blank=True, validators=[MinValueValidator(0)])
    
    measurement_method = models.CharField('測定方法', max_length=50, choices=[
        ('ruler', '定規・メジャー'),
        ('caliper', 'ノギス'),
        ('scanner', '3Dスキャナー'),
        ('estimation', '目測'),
        ('package', 'パッケージ表記'),
    ], default='ruler')
    
    accuracy_notes = models.TextField('測定メモ', blank=True)
    measured_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='測定者')
    measured_at = models.DateTimeField('測定日時', auto_now_add=True)
    is_approved = models.BooleanField('承認済み', default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_measurements', verbose_name='承認者')
    
    class Meta:
        verbose_name = '商品サイズ測定'
        verbose_name_plural = '商品サイズ測定'
        ordering = ['-measured_at']
    
    def __str__(self):
        return f"{self.product.product_name} - {self.measured_width}×{self.measured_height}cm"
    
    def apply_to_product(self):
        """測定値を商品マスタに反映"""
        if self.is_approved:
            self.product.width = self.measured_width
            self.product.height = self.measured_height
            self.product.depth = self.measured_depth
            self.product.weight = self.measured_weight
            self.product.size_accuracy = 'measured'
            self.product.size_measured_by = self.measured_by
            self.product.size_measured_at = self.measured_at
            self.product.save()


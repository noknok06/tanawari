from django.db import models
from django.contrib.auth.models import User


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
    width = models.FloatField('幅(cm)', null=True, blank=True)
    height = models.FloatField('高さ(cm)', null=True, blank=True)
    depth = models.FloatField('奥行(cm)', null=True, blank=True)
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
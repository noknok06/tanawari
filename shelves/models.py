from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from products.models import Product


class Shelf(models.Model):
    """棚マスタ"""
    name = models.CharField('棚名', max_length=100)
    description = models.TextField('説明', blank=True)
    width = models.FloatField('幅(cm)', validators=[MinValueValidator(1)])
    height = models.FloatField('高さ(cm)', validators=[MinValueValidator(1)])
    depth = models.FloatField('奥行(cm)', validators=[MinValueValidator(1)])
    rows = models.IntegerField('段数', validators=[MinValueValidator(1), MaxValueValidator(20)])
    columns = models.IntegerField('列数', validators=[MinValueValidator(1), MaxValueValidator(20)])
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


class ShelfPlacement(models.Model):
    """棚配置"""
    shelf = models.ForeignKey(Shelf, on_delete=models.CASCADE, verbose_name='棚')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='商品')
    row = models.IntegerField('段', validators=[MinValueValidator(0)])
    column = models.IntegerField('列', validators=[MinValueValidator(0)])
    face_count = models.IntegerField('フェース数', default=1, validators=[MinValueValidator(1)])
    span_rows = models.IntegerField('占有段数', default=1, validators=[MinValueValidator(1)])
    span_columns = models.IntegerField('占有列数', default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='作成者')
    
    class Meta:
        verbose_name = '棚配置'
        verbose_name_plural = '棚配置'
        unique_together = ['shelf', 'row', 'column']
    
    def __str__(self):
        return f"{self.shelf.name} - {self.product.product_name} ({self.row+1}段{self.column+1}列)"


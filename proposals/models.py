# ==================== proposals/models.py ====================

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from shelves.models import Shelf, ShelfPlacement


class Customer(models.Model):
    """得意先マスタ"""
    name = models.CharField('得意先名', max_length=200)
    contact_person = models.CharField('担当者', max_length=100, blank=True)
    phone = models.CharField('電話番号', max_length=20, blank=True)
    email = models.EmailField('メールアドレス', blank=True)
    address = models.TextField('住所', blank=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='作成者')
    
    class Meta:
        verbose_name = '得意先'
        verbose_name_plural = '得意先'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Proposal(models.Model):
    """提案"""
    STATUS_CHOICES = [
        ('draft', '下書き'),
        ('submitted', '提出済み'),
        ('approved', '承認済み'),
        ('rejected', '却下'),
    ]
    
    title = models.CharField('提案タイトル', max_length=200)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='得意先')
    shelf = models.ForeignKey(Shelf, on_delete=models.CASCADE, verbose_name='棚')
    sales_rep = models.CharField('営業担当', max_length=100, blank=True)
    proposal_date = models.DateField('提案日', default=timezone.now)
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='draft')
    description = models.TextField('提案内容', blank=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='作成者')
    
    class Meta:
        verbose_name = '提案'
        verbose_name_plural = '提案'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.customer.name}"
    
    def get_placement_stats(self):
        """配置統計を取得"""
        placements = ShelfPlacement.objects.filter(shelf=self.shelf)
        total_cells = self.shelf.total_cells
        occupied_cells = placements.count()
        own_products = placements.filter(product__is_own_product=True)
        competitor_products = placements.filter(product__is_own_product=False)
        
        own_faces = sum(p.face_count for p in own_products)
        competitor_faces = sum(p.face_count for p in competitor_products)
        total_faces = own_faces + competitor_faces
        
        return {
            'total_cells': total_cells,
            'occupied_cells': occupied_cells,
            'occupancy_rate': round((occupied_cells / total_cells) * 100, 1) if total_cells > 0 else 0,
            'own_products_count': own_products.count(),
            'competitor_products_count': competitor_products.count(),
            'own_faces': own_faces,
            'competitor_faces': competitor_faces,
            'own_share': round((own_faces / total_faces) * 100, 1) if total_faces > 0 else 0,
        }
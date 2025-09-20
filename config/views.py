# ==================== プロジェクトのメインviews.py（tanaoroshi_project/views.py） ====================

from django.shortcuts import render
from products.models import Product


def index(request):
    """ホーム画面"""
    context = {
        'total_products': Product.objects.filter(is_active=True).count(),
        'own_products': Product.objects.filter(is_active=True, is_own_product=True).count(),
        'competitor_products': Product.objects.filter(is_active=True, is_own_product=False).count(),
        'recent_products': Product.objects.filter(is_active=True).select_related('maker').order_by('-created_at')[:5],
    }
    return render(request, 'index.html', context)


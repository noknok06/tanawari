# ==================== products/urls.py ====================

from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # 商品管理
    path('', views.ProductListView.as_view(), name='product_list'),
    path('add/', views.ProductCreateView.as_view(), name='product_add'),
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    
    # API
    path('api/add-maker/', views.add_maker, name='add_maker'),
    path('api/add-brand/', views.add_brand, name='add_brand'),
    path('api/add-category/', views.add_category, name='add_category'),
    path('api/brands-by-maker/', views.get_brands_by_maker, name='get_brands_by_maker'),
]
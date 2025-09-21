# ==================== shelves/urls.py ====================

from django.urls import path
from . import views

app_name = 'shelves'

urlpatterns = [
    # 棚管理
    path('', views.ShelfListView.as_view(), name='shelf_list'),
    path('add/', views.ShelfCreateView.as_view(), name='shelf_add'),
    path('<int:pk>/', views.shelf_detail, name='shelf_detail'),
    path('<int:pk>/edit/', views.ShelfUpdateView.as_view(), name='shelf_edit'),
    path('<int:pk>/delete/', views.ShelfDeleteView.as_view(), name='shelf_delete'),
    
    # サイズベース棚割り
    path('<int:pk>/size-aware/', views.shelf_detail_with_size, name='shelf_detail_size'),
    
    # 従来の棚割りAPI
    path('api/place-product/', views.place_product, name='place_product'),
    path('api/remove-product/', views.remove_product, name='remove_product'),
    path('api/update-face-count/', views.update_face_count, name='update_face_count'),
    
    # サイズベース棚割りAPI
    path('api/place-product-with-size/', views.place_product_with_size, name='place_product_with_size'),
    path('api/remove-product-with-conflicts/', views.remove_product_with_conflicts, name='remove_product_with_conflicts'),
    path('api/check-placement-possibility/', views.check_placement_possibility, name='check_placement_possibility'),
    path('api/placement-conflicts/', views.get_placement_conflicts, name='get_placement_conflicts'),
    path('api/stats/<int:pk>/', views.get_shelf_statistics, name='shelf_statistics'),
    
    # 配置最適化（将来実装）
    path('api/optimize-layout/<int:pk>/', views.optimize_shelf_layout, name='optimize_layout'),
    path('api/suggest-placement/', views.suggest_optimal_placement, name='suggest_placement'),
]


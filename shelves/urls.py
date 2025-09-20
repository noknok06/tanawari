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
    
    # 棚割りAPI
    path('api/place-product/', views.place_product, name='place_product'),
    path('api/remove-product/', views.remove_product, name='remove_product'),
    path('api/update-face-count/', views.update_face_count, name='update_face_count'),
]

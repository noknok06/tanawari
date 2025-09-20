# ==================== proposals/urls.py ====================

from django.urls import path
from . import views

app_name = 'proposals'

urlpatterns = [
    # 提案管理
    path('', views.ProposalListView.as_view(), name='proposal_list'),
    path('add/', views.ProposalCreateView.as_view(), name='proposal_add'),
    path('<int:pk>/', views.proposal_detail, name='proposal_detail'),
    path('<int:pk>/edit/', views.ProposalUpdateView.as_view(), name='proposal_edit'),
    path('<int:pk>/delete/', views.ProposalDeleteView.as_view(), name='proposal_delete'),
    
    # 出力機能
    path('<int:pk>/export/pdf/', views.export_pdf, name='export_pdf'),
    path('<int:pk>/export/excel/', views.export_excel, name='export_excel'),
]
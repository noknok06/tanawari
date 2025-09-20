# ==================== proposals/views.py ====================

from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.template.loader import render_to_string
from shelves.models import ShelfPlacement

from .models import Proposal, Customer
from .forms import ProposalForm


class ProposalListView(ListView):
    """提案一覧"""
    model = Proposal
    template_name = 'proposal_list.html'
    context_object_name = 'proposals'
    paginate_by = 12

    def get_queryset(self):
        queryset = Proposal.objects.select_related('customer', 'shelf')
        
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        customer = self.request.GET.get('customer')
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(customer__name__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
        
        if customer:
            queryset = queryset.filter(customer_id=customer)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status_choices'] = Proposal.STATUS_CHOICES
        context['selected_status'] = self.request.GET.get('status', '')
        context['customers'] = Customer.objects.all()
        context['selected_customer'] = self.request.GET.get('customer', '')
        return context


class ProposalCreateView(CreateView):
    """提案作成"""
    model = Proposal
    form_class = ProposalForm
    template_name = 'proposal_form.html'
    success_url = reverse_lazy('proposals:proposal_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '提案作成'
        return context

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        messages.success(self.request, '提案を作成しました。')
        return super().form_valid(form)


class ProposalUpdateView(UpdateView):
    """提案編集"""
    model = Proposal
    form_class = ProposalForm
    template_name = 'proposal_form.html'
    success_url = reverse_lazy('proposals:proposal_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '提案編集'
        return context

    def form_valid(self, form):
        messages.success(self.request, '提案を更新しました。')
        return super().form_valid(form)


class ProposalDeleteView(DeleteView):
    """提案削除"""
    model = Proposal
    template_name = 'proposal_confirm_delete.html'
    success_url = reverse_lazy('proposals:proposal_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, '提案を削除しました。')
        return super().delete(request, *args, **kwargs)


def proposal_detail(request, pk):
    """提案詳細"""
    proposal = get_object_or_404(Proposal, pk=pk)
    shelf = proposal.shelf
    
    # 棚配置データを取得
    placements = ShelfPlacement.objects.filter(shelf=shelf).select_related('product', 'product__maker')
    
    # グリッド形式でのデータ構築
    grid = [[None for _ in range(shelf.columns)] for _ in range(shelf.rows)]
    for placement in placements:
        if placement.row < shelf.rows and placement.column < shelf.columns:
            grid[placement.row][placement.column] = placement
    
    # 統計情報
    stats = proposal.get_placement_stats()
    
    context = {
        'proposal': proposal,
        'shelf': shelf,
        'grid': grid,
        'placements': placements,
        'stats': stats,
    }
    return render(request, 'proposal_detail.html', context)


def export_pdf(request, pk):
    """PDF出力"""
    proposal = get_object_or_404(Proposal, pk=pk)
    shelf = proposal.shelf
    
    # 棚配置データを取得
    placements = ShelfPlacement.objects.filter(shelf=shelf).select_related('product', 'product__maker')
    
    # グリッド形式でのデータ構築
    grid = [[None for _ in range(shelf.columns)] for _ in range(shelf.rows)]
    for placement in placements:
        if placement.row < shelf.rows and placement.column < shelf.columns:
            grid[placement.row][placement.column] = placement
    
    # 統計情報
    stats = proposal.get_placement_stats()
    
    context = {
        'proposal': proposal,
        'shelf': shelf,
        'grid': grid,
        'placements': placements,
        'stats': stats,
        'export_date': datetime.now(),
    }
    
    # HTMLテンプレートをレンダリング
    html_string = render_to_string('proposal_pdf.html', context)
    
    # 実際のPDF生成処理（WeasyPrintやReportLabを使用）
    # ここでは簡易版として HTMLResponseを返す
    response = HttpResponse(html_string, content_type='text/html')
    response['Content-Disposition'] = f'attachment; filename="{proposal.title}_提案書.html"'
    return response


def export_excel(request, pk):
    """Excel出力"""
    proposal = get_object_or_404(Proposal, pk=pk)
    shelf = proposal.shelf
    
    # 棚配置データを取得
    placements = ShelfPlacement.objects.filter(shelf=shelf).select_related(
        'product', 'product__maker', 'product__brand', 'product__category'
    )
    
    # 実際のExcel生成処理（openpyxlを使用）
    # ここでは簡易版としてCSV形式で返す
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # ヘッダー
    writer.writerow([
        '位置', '商品名', 'JANコード', 'メーカー', 'ブランド', 
        'カテゴリ', 'フェース数', '区分'
    ])
    
    # データ
    for placement in placements:
        writer.writerow([
            f"{placement.row+1}段{placement.column+1}列",
            placement.product.product_name,
            placement.product.product_code,
            placement.product.maker.name,
            placement.product.brand.name if placement.product.brand else '-',
            placement.product.category.name,
            placement.face_count,
            '自社' if placement.product.is_own_product else '競合'
        ])
    
    output.seek(0)
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{proposal.title}_商品配置一覧.csv"'
    return response

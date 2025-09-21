# ==================== shelves/views.py ====================

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.views.decorators.http import require_POST
from products.models import Product

from .models import Shelf, ShelfPlacement
from .forms import ShelfForm


class ShelfListView(ListView):
    """棚一覧"""
    model = Shelf
    template_name = 'shelf_list.html'
    context_object_name = 'shelves'
    paginate_by = 12

    def get_queryset(self):
        queryset = Shelf.objects.all()
        search = self.request.GET.get('search')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class ShelfCreateView(CreateView):
    """棚作成"""
    model = Shelf
    form_class = ShelfForm
    template_name = 'shelf_form.html'
    success_url = reverse_lazy('shelves:shelf_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '棚作成'
        return context

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        messages.success(self.request, '棚を作成しました。')
        return super().form_valid(form)


class ShelfUpdateView(UpdateView):
    """棚編集"""
    model = Shelf
    form_class = ShelfForm
    template_name = 'shelf_form.html'
    success_url = reverse_lazy('shelves:shelf_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '棚編集'
        return context

    def form_valid(self, form):
        messages.success(self.request, '棚を更新しました。')
        return super().form_valid(form)


class ShelfDeleteView(DeleteView):
    """棚削除"""
    model = Shelf
    template_name = 'shelf_confirm_delete.html'
    success_url = reverse_lazy('shelves:shelf_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, '棚を削除しました。')
        return super().delete(request, *args, **kwargs)


def shelf_detail(request, pk):
    """棚詳細・編集画面"""
    shelf = get_object_or_404(Shelf, pk=pk)
    
    # 棚配置データを取得
    placements = ShelfPlacement.objects.filter(shelf=shelf).select_related('product', 'product__maker')
    
    # グリッド形式でのデータ構築
    grid = [[None for _ in range(shelf.columns)] for _ in range(shelf.rows)]
    for placement in placements:
        if placement.row < shelf.rows and placement.column < shelf.columns:
            grid[placement.row][placement.column] = placement
    
    # 商品一覧を取得
    products = Product.objects.filter(is_active=True).select_related('maker', 'brand', 'category')
    
    # カテゴリ一覧を取得（重複なし）
    from products.models import Category
    categories = Category.objects.filter(product__in=products).distinct().order_by('name')
    
    context = {
        'shelf': shelf,
        'grid': grid,
        'placements': placements,
        'products': products,
        'categories': categories,
    }
    return render(request, 'shelf_detail.html', context)


@require_POST
def place_product(request):
    """商品配置API"""
    try:
        shelf_id = request.POST.get('shelf_id')
        product_id = request.POST.get('product_id')
        row = int(request.POST.get('row'))
        column = int(request.POST.get('column'))
        face_count = int(request.POST.get('face_count', 1))
        span_rows = int(request.POST.get('span_rows', 1))
        span_columns = int(request.POST.get('span_columns', 1))
        
        shelf = get_object_or_404(Shelf, id=shelf_id)
        product = get_object_or_404(Product, id=product_id)
        
        # 配置可能かチェック
        if row >= shelf.rows or column >= shelf.columns:
            return JsonResponse({'success': False, 'error': '配置位置が範囲外です'})
        
        # 既存配置をチェック
        if ShelfPlacement.objects.filter(shelf=shelf, row=row, column=column).exists():
            return JsonResponse({'success': False, 'error': 'この位置には既に商品が配置されています'})
        
        # 配置を作成
        placement = ShelfPlacement.objects.create(
            shelf=shelf,
            product=product,
            row=row,
            column=column,
            face_count=face_count,
            span_rows=span_rows,
            span_columns=span_columns,
            created_by=request.user if request.user.is_authenticated else None
        )
        
        return JsonResponse({
            'success': True,
            'placement': {
                'id': placement.id,
                'product_id': product.id,
                'product_name': product.product_name,
                'maker_name': product.maker.name,
                'is_own_product': product.is_own_product,
                'face_count': placement.face_count,
                'image_url': product.image.url if product.image else None,
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def remove_product(request):
    """商品削除API"""
    try:
        placement_id = request.POST.get('placement_id')
        placement = get_object_or_404(ShelfPlacement, id=placement_id)
        placement.delete()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def update_face_count(request):
    """フェース数更新API"""
    try:
        placement_id = request.POST.get('placement_id')
        face_count = int(request.POST.get('face_count'))
        
        placement = get_object_or_404(ShelfPlacement, id=placement_id)
        placement.face_count = face_count
        placement.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
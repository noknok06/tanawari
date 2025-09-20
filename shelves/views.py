# ==================== products/views.py ====================

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.views.decorators.http import require_POST

from .models import Product, Maker, Brand, Category
from .forms import ProductForm, MakerForm, BrandForm, CategoryForm


class ProductListView(ListView):
    """商品一覧"""
    model = Product
    template_name = 'product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('maker', 'brand', 'category')
        
        # 検索・フィルタ処理
        search = self.request.GET.get('search')
        maker = self.request.GET.get('maker')
        category = self.request.GET.get('category')
        is_own = self.request.GET.get('is_own')
        
        if search:
            queryset = queryset.filter(
                Q(product_name__icontains=search) |
                Q(product_code__icontains=search) |
                Q(maker__name__icontains=search)
            )
        
        if maker:
            queryset = queryset.filter(maker_id=maker)
        
        if category:
            queryset = queryset.filter(category_id=category)
        
        if is_own == 'true':
            queryset = queryset.filter(is_own_product=True)
        elif is_own == 'false':
            queryset = queryset.filter(is_own_product=False)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['makers'] = Maker.objects.all()
        context['categories'] = Category.objects.all()
        context['selected_maker'] = self.request.GET.get('maker', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_is_own'] = self.request.GET.get('is_own', '')
        return context


class ProductCreateView(CreateView):
    """商品作成"""
    model = Product
    form_class = ProductForm
    template_name = 'product_form.html'
    success_url = reverse_lazy('products:product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '商品追加'
        return context

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        messages.success(self.request, '商品を追加しました。')
        return super().form_valid(form)


class ProductUpdateView(UpdateView):
    """商品編集"""
    model = Product
    form_class = ProductForm
    template_name = 'product_form.html'
    success_url = reverse_lazy('products:product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '商品編集'
        return context

    def form_valid(self, form):
        messages.success(self.request, '商品を更新しました。')
        return super().form_valid(form)


class ProductDeleteView(DeleteView):
    """商品削除"""
    model = Product
    template_name = 'product_confirm_delete.html'
    success_url = reverse_lazy('products:product_list')

    def delete(self, request, *args, **kwargs):
        # 論理削除
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save()
        messages.success(request, '商品を削除しました。')
        return redirect(self.success_url)


@require_POST
def add_maker(request):
    """メーカー追加API"""
    form = MakerForm(request.POST)
    if form.is_valid():
        maker = form.save(commit=False)
        if request.user.is_authenticated:
            maker.created_by = request.user
        maker.save()
        
        return JsonResponse({
            'success': True,
            'maker': {
                'id': maker.id,
                'name': maker.name
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        })


@require_POST
def add_brand(request):
    """ブランド追加API"""
    form = BrandForm(request.POST)
    if form.is_valid():
        brand = form.save(commit=False)
        if request.user.is_authenticated:
            brand.created_by = request.user
        brand.save()
        
        return JsonResponse({
            'success': True,
            'brand': {
                'id': brand.id,
                'name': brand.name
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        })


@require_POST
def add_category(request):
    """カテゴリ追加API"""
    form = CategoryForm(request.POST)
    if form.is_valid():
        category = form.save(commit=False)
        if request.user.is_authenticated:
            category.created_by = request.user
        category.save()
        
        return JsonResponse({
            'success': True,
            'category': {
                'id': category.id,
                'name': category.name
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        })


def get_brands_by_maker(request):
    """メーカー別ブランド取得API"""
    maker_id = request.GET.get('maker_id')
    brands = Brand.objects.filter(maker_id=maker_id).values('id', 'name')
    return JsonResponse({'brands': list(brands)})


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
    
    context = {
        'shelf': shelf,
        'grid': grid,
        'placements': placements,
        'products': products,
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

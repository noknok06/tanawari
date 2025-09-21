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
    
@require_POST
def place_product_with_size(request):
    """サイズを考慮した商品配置API"""
    try:
        shelf_id = request.POST.get('shelf_id')
        product_id = request.POST.get('product_id')
        row = int(request.POST.get('row'))
        column = int(request.POST.get('column'))
        face_count = int(request.POST.get('face_count', 1))
        
        shelf = get_object_or_404(Shelf, id=shelf_id)
        product = get_object_or_404(Product, id=product_id)
        
        # 配置可能性をチェック
        if not shelf.can_place_product(product, row, column, face_count):
            return JsonResponse({
                'success': False, 
                'error': '指定位置には配置できません（サイズまたは重複の問題）'
            })
        
        # 必要なセル数を計算
        required_cells = shelf.calculate_required_cells(product, face_count)
        
        with transaction.atomic():
            # 配置を作成
            placement = ShelfPlacement.objects.create(
                shelf=shelf,
                product=product,
                row=row,
                column=column,
                face_count=face_count,
                span_rows=required_cells['span_rows'],
                span_columns=required_cells['span_columns'],
                display_width_ratio=required_cells.get('fit_ratio_width', 1.0),
                display_height_ratio=required_cells.get('fit_ratio_height', 1.0),
                created_by=request.user if request.user.is_authenticated else None
            )
            
            # 占有セルの競合レコードを作成
            for r in range(row, row + required_cells['span_rows']):
                for c in range(column, column + required_cells['span_columns']):
                    PlacementConflict.objects.create(
                        placement=placement,
                        row=r,
                        column=c
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
                'span_rows': placement.span_rows,
                'span_columns': placement.span_columns,
                'display_width_ratio': placement.display_width_ratio,
                'display_height_ratio': placement.display_height_ratio,
                'image_url': product.image.url if product.image else None,
                'size_info': {
                    'product_width': product.width,
                    'product_height': product.height,
                    'total_width_cm': placement.total_width_cm,
                    'cell_width': shelf.calculated_cell_width,
                    'cell_height': shelf.calculated_cell_height,
                }
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def remove_product_with_conflicts(request):
    """競合レコードも含めて商品削除"""
    try:
        placement_id = request.POST.get('placement_id')
        placement = get_object_or_404(ShelfPlacement, id=placement_id)
        
        with transaction.atomic():
            # 競合レコードを削除
            PlacementConflict.objects.filter(placement=placement).delete()
            # 配置を削除
            placement.delete()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def get_placement_conflicts(request):
    """指定位置の配置競合をチェック"""
    shelf_id = request.GET.get('shelf_id')
    row = int(request.GET.get('row', 0))
    column = int(request.GET.get('column', 0))
    
    conflicts = PlacementConflict.objects.filter(
        placement__shelf_id=shelf_id,
        row=row,
        column=column
    ).select_related('placement__product')
    
    conflict_data = []
    for conflict in conflicts:
        conflict_data.append({
            'placement_id': conflict.placement.id,
            'product_name': conflict.placement.product.product_name,
            'product_id': conflict.placement.product.id,
            'is_origin': (conflict.row == conflict.placement.row and 
                         conflict.column == conflict.placement.column)
        })
    
    return JsonResponse({
        'conflicts': conflict_data,
        'has_conflicts': len(conflict_data) > 0
    })


def check_placement_possibility(request):
    """配置可能性をリアルタイムチェック"""
    shelf_id = request.GET.get('shelf_id')
    product_id = request.GET.get('product_id')
    row = int(request.GET.get('row', 0))
    column = int(request.GET.get('column', 0))
    face_count = int(request.GET.get('face_count', 1))
    
    try:
        shelf = get_object_or_404(Shelf, id=shelf_id)
        product = get_object_or_404(Product, id=product_id)
        
        # 必要セル数を計算
        required_cells = shelf.calculate_required_cells(product, face_count)
        
        # 配置可能性をチェック
        can_place = shelf.can_place_product(product, row, column, face_count)
        
        # 範囲外チェック
        exceeds_boundary = (
            row + required_cells['span_rows'] > shelf.rows or
            column + required_cells['span_columns'] > shelf.columns
        )
        
        return JsonResponse({
            'can_place': can_place,
            'required_cells': required_cells,
            'exceeds_boundary': exceeds_boundary,
            'shelf_info': {
                'cell_width': shelf.calculated_cell_width,
                'cell_height': shelf.calculated_cell_height,
                'total_rows': shelf.rows,
                'total_columns': shelf.columns,
            },
            'size_analysis': {
                'fits_perfectly': (
                    required_cells.get('fit_ratio_width', 1.0) >= 0.9 and
                    required_cells.get('fit_ratio_height', 1.0) >= 0.9
                ),
                'oversized': (
                    required_cells.get('fit_ratio_width', 1.0) < 0.7 or
                    required_cells.get('fit_ratio_height', 1.0) < 0.7
                ),
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)})


def shelf_detail_with_size(request, pk):
    """サイズ情報を含む棚詳細画面"""
    shelf = get_object_or_404(Shelf, pk=pk)
    
    # 配置データを取得（競合レコードからグリッドを構築）
    placements = ShelfPlacement.objects.filter(shelf=shelf).select_related(
        'product', 'product__maker'
    )
    
    # グリッドマップを構築（どのセルがどの配置に属するか）
    grid_map = {}
    placement_map = {}
    
    for placement in placements:
        placement_map[placement.id] = placement
        for r in range(placement.row, placement.row + placement.span_rows):
            for c in range(placement.column, placement.column + placement.span_columns):
                grid_map[(r, c)] = placement
    
    # 2次元グリッドを構築
    grid = []
    for row in range(shelf.rows):
        grid_row = []
        for col in range(shelf.columns):
            cell_placement = grid_map.get((row, col))
            grid_row.append({
                'placement': cell_placement,
                'is_origin': (cell_placement and 
                             cell_placement.row == row and 
                             cell_placement.column == col) if cell_placement else False,
                'row': row,
                'column': col,
            })
        grid.append(grid_row)
    
    # 商品一覧を取得
    products = Product.objects.filter(is_active=True).select_related(
        'maker', 'brand', 'category'
    )
    
    # サイズ情報付きの商品データ
    products_with_size = []
    for product in products:
        if product.width and product.height:
            required_cells = shelf.calculate_required_cells(product)
            products_with_size.append({
                'product': product,
                'required_cells': required_cells,
                'size_category': get_size_category(product, shelf),
            })
        else:
            products_with_size.append({
                'product': product,
                'required_cells': {'span_rows': 1, 'span_columns': 1},
                'size_category': 'unknown',
            })
    
    # カテゴリ一覧を取得
    from products.models import Category
    categories = Category.objects.filter(
        product__in=[item['product'] for item in products_with_size]
    ).distinct().order_by('name')
    
    context = {
        'shelf': shelf,
        'grid': grid,
        'placements': placements,
        'products_with_size': products_with_size,
        'categories': categories,
        'shelf_info': {
            'cell_width': shelf.calculated_cell_width,
            'cell_height': shelf.calculated_cell_height,
            'total_cells': shelf.total_cells,
        }
    }
    return render(request, 'shelf_detail_with_size.html', context)


def get_size_category(product, shelf):
    """商品のサイズカテゴリを判定"""
    if not product.width or not product.height:
        return 'unknown'
    
    cell_area = shelf.calculated_cell_width * shelf.calculated_cell_height
    product_area = product.width * product.height
    
    if product_area <= cell_area * 0.5:
        return 'small'
    elif product_area <= cell_area * 2:
        return 'medium'
    else:
        return 'large'


def get_shelf_statistics(request, pk):
    """棚の統計情報を取得（サイズ考慮）"""
    shelf = get_object_or_404(Shelf, pk=pk)
    placements = ShelfPlacement.objects.filter(shelf=shelf).select_related('product')
    
    # 占有セル数の計算
    total_occupied_cells = sum(p.span_rows * p.span_columns for p in placements)
    
    # 商品分類
    own_products = placements.filter(product__is_own_product=True)
    competitor_products = placements.filter(product__is_own_product=False)
    
    # フェース数の計算
    own_faces = sum(p.face_count for p in own_products)
    competitor_faces = sum(p.face_count for p in competitor_products)
    total_faces = own_faces + competitor_faces
    
    # 面積利用率の計算
    total_shelf_area = shelf.width * shelf.height
    used_area = sum(p.total_width_cm * p.total_height_cm for p in placements if p.total_width_cm and p.total_height_cm)
    
    stats = {
        'total_cells': shelf.total_cells,
        'occupied_cells': total_occupied_cells,
        'occupancy_rate': round((total_occupied_cells / shelf.total_cells) * 100, 1),
        'own_products_count': own_products.count(),
        'competitor_products_count': competitor_products.count(),
        'own_faces': own_faces,
        'competitor_faces': competitor_faces,
        'own_share': round((own_faces / total_faces) * 100, 1) if total_faces > 0 else 0,
        'area_utilization': round((used_area / total_shelf_area) * 100, 1) if total_shelf_area > 0 else 0,
        'size_distribution': {
            'small': placements.filter(span_rows=1, span_columns=1).count(),
            'medium': placements.filter(span_rows__lte=2, span_columns__lte=2).exclude(span_rows=1, span_columns=1).count(),
            'large': placements.filter(Q(span_rows__gt=2) | Q(span_columns__gt=2)).count(),
        }
    }
    
    return JsonResponse(stats)    

def optimize_shelf_layout(request, pk):
    """棚レイアウト最適化（将来実装）"""
    shelf = get_object_or_404(Shelf, pk=pk)
    
    # TODO: 最適化アルゴリズムを実装
    # - 商品サイズに基づく最適配置
    # - フェース数の最適化
    # - 自社商品の視認性向上
    
    return JsonResponse({
        'success': True,
        'message': '最適化機能は開発中です',
        'suggestions': [
            '大きな商品を棚の端に配置することを検討してください',
            '自社商品の視認性を高めるため、目線の高さに配置してください',
            'フェース数を調整して売上向上を図ってください'
        ]
    })


def suggest_optimal_placement(request):
    """最適配置提案"""
    shelf_id = request.GET.get('shelf_id')
    product_id = request.GET.get('product_id')
    
    try:
        shelf = get_object_or_404(Shelf, id=shelf_id)
        product = get_object_or_404(Product, id=product_id)
        
        # 配置可能な位置を探索
        suggestions = []
        for row in range(shelf.rows):
            for column in range(shelf.columns):
                if shelf.can_place_product(product, row, column):
                    score = calculate_placement_score(shelf, product, row, column)
                    suggestions.append({
                        'row': row,
                        'column': column,
                        'score': score,
                        'reason': get_placement_reason(shelf, product, row, column, score)
                    })
        
        # スコア順にソート
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        
        return JsonResponse({
            'success': True,
            'suggestions': suggestions[:5],  # 上位5件
            'total_options': len(suggestions)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def calculate_placement_score(shelf, product, row, column):
    """配置スコアを計算"""
    score = 100  # 基本スコア
    
    # 自社商品は目線の高さ（中段）を優遇
    if product.is_own_product:
        middle_row = shelf.rows // 2
        distance_from_middle = abs(row - middle_row)
        score -= distance_from_middle * 10
    
    # 大きな商品は端を優遇
    required_cells = shelf.calculate_required_cells(product)
    if required_cells['span_rows'] > 1 or required_cells['span_columns'] > 1:
        if column == 0 or column + required_cells['span_columns'] == shelf.columns:
            score += 20
    
    # 同じメーカーの商品が近くにあるかチェック
    nearby_same_maker = ShelfPlacement.objects.filter(
        shelf=shelf,
        product__maker=product.maker,
        row__range=(max(0, row-1), min(shelf.rows-1, row+1)),
        column__range=(max(0, column-1), min(shelf.columns-1, column+1))
    ).exists()
    
    if nearby_same_maker:
        score += 15  # ブランド統一感ボーナス
    
    return score


def get_placement_reason(shelf, product, row, column, score):
    """配置理由を生成"""
    reasons = []
    
    if product.is_own_product and abs(row - shelf.rows // 2) <= 1:
        reasons.append('目線の高さで視認性が良い')
    
    required_cells = shelf.calculate_required_cells(product)
    if required_cells['span_rows'] > 1 or required_cells['span_columns'] > 1:
        if column == 0 or column + required_cells['span_columns'] == shelf.columns:
            reasons.append('大型商品に適した端の位置')
    
    if score >= 120:
        reasons.append('最適な配置位置')
    elif score >= 100:
        reasons.append('良好な配置位置')
    else:
        reasons.append('配置可能')
    
    return ' / '.join(reasons) if reasons else '配置可能'
    
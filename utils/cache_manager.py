# ==================== utils/cache_manager.py ====================

from django.core.cache import cache
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import json
import hashlib
from datetime import datetime, timedelta


class ShelfCacheManager:
    """棚割りデータキャッシュ管理"""
    
    CACHE_PREFIX = 'shelf_'
    DEFAULT_TIMEOUT = 3600  # 1時間
    
    @staticmethod
    def get_shelf_cache_key(shelf_id, cache_type='layout'):
        """キャッシュキーを生成"""
        return f"{ShelfCacheManager.CACHE_PREFIX}{cache_type}_{shelf_id}"
    
    @staticmethod
    def get_placement_grid(shelf_id):
        """配置グリッドをキャッシュから取得"""
        cache_key = ShelfCacheManager.get_shelf_cache_key(shelf_id, 'grid')
        grid_data = cache.get(cache_key)
        
        if grid_data is None:
            # キャッシュにない場合は生成
            grid_data = ShelfCacheManager._generate_placement_grid(shelf_id)
            cache.set(cache_key, grid_data, ShelfCacheManager.DEFAULT_TIMEOUT)
        
        return grid_data
    
    @staticmethod
    def _generate_placement_grid(shelf_id):
        """配置グリッドを生成"""
        from shelves.models import Shelf, ShelfPlacement, PlacementConflict
        
        try:
            shelf = Shelf.objects.get(id=shelf_id)
        except Shelf.DoesNotExist:
            return None
        
        # 配置データを効率的に取得
        placements = ShelfPlacement.objects.filter(shelf=shelf).select_related(
            'product', 'product__maker', 'product__brand'
        ).prefetch_related('placementconflict_set')
        
        # グリッドマップを構築
        grid_map = {}
        placement_lookup = {}
        
        for placement in placements:
            placement_lookup[placement.id] = {
                'id': placement.id,
                'product_id': placement.product.id,
                'product_name': placement.product.product_name,
                'maker_name': placement.product.maker.name,
                'is_own_product': placement.product.is_own_product,
                'face_count': placement.face_count,
                'span_rows': placement.span_rows,
                'span_columns': placement.span_columns,
                'row': placement.row,
                'column': placement.column,
                'image_url': placement.product.image.url if placement.product.image else None,
            }
            
            # 占有セルをマッピング
            conflicts = PlacementConflict.objects.filter(placement=placement)
            for conflict in conflicts:
                grid_map[(conflict.row, conflict.column)] = placement.id
        
        # 2次元グリッドを構築
        grid = []
        for row in range(shelf.rows):
            grid_row = []
            for col in range(shelf.columns):
                placement_id = grid_map.get((row, col))
                if placement_id:
                    placement_data = placement_lookup[placement_id].copy()
                    placement_data['is_origin'] = (
                        placement_data['row'] == row and 
                        placement_data['column'] == col
                    )
                else:
                    placement_data = None
                
                grid_row.append({
                    'placement': placement_data,
                    'row': row,
                    'column': col,
                })
            grid.append(grid_row)
        
        return {
            'grid': grid,
            'shelf_info': {
                'id': shelf.id,
                'name': shelf.name,
                'rows': shelf.rows,
                'columns': shelf.columns,
                'cell_width': shelf.calculated_cell_width,
                'cell_height': shelf.calculated_cell_height,
            },
            'generated_at': datetime.now().isoformat(),
        }
    
    @staticmethod
    def get_shelf_statistics(shelf_id):
        """棚統計をキャッシュから取得"""
        cache_key = ShelfCacheManager.get_shelf_cache_key(shelf_id, 'stats')
        stats = cache.get(cache_key)
        
        if stats is None:
            stats = ShelfCacheManager._generate_shelf_statistics(shelf_id)
            cache.set(cache_key, stats, ShelfCacheManager.DEFAULT_TIMEOUT)
        
        return stats
    
    @staticmethod
    def _generate_shelf_statistics(shelf_id):
        """棚統計を生成"""
        from shelves.models import Shelf, ShelfPlacement
        
        try:
            shelf = Shelf.objects.get(id=shelf_id)
        except Shelf.DoesNotExist:
            return None
        
        placements = ShelfPlacement.objects.filter(shelf=shelf).select_related('product')
        
        # 基本統計
        total_occupied_cells = sum(p.span_rows * p.span_columns for p in placements)
        own_products = placements.filter(product__is_own_product=True)
        competitor_products = placements.filter(product__is_own_product=False)
        
        own_faces = sum(p.face_count for p in own_products)
        competitor_faces = sum(p.face_count for p in competitor_products)
        total_faces = own_faces + competitor_faces
        
        # 面積利用率
        total_shelf_area = shelf.width * shelf.height
        used_area = sum(
            p.product.width * p.product.height * p.face_count 
            for p in placements 
            if p.product.width and p.product.height
        )
        
        return {
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
                'large': placements.filter(span_rows__gt=2).count() + placements.filter(span_columns__gt=2).count(),
            },
            'generated_at': datetime.now().isoformat(),
        }
    
    @staticmethod
    def invalidate_shelf_cache(shelf_id):
        """棚のキャッシュを無効化"""
        cache_keys = [
            ShelfCacheManager.get_shelf_cache_key(shelf_id, 'grid'),
            ShelfCacheManager.get_shelf_cache_key(shelf_id, 'stats'),
            ShelfCacheManager.get_shelf_cache_key(shelf_id, 'layout'),
        ]
        
        cache.delete_many(cache_keys)
        print(f"Invalidated cache for shelf {shelf_id}")


# キャッシュ無効化シグナル
@receiver([post_save, post_delete], sender='shelves.ShelfPlacement')
def invalidate_placement_cache(sender, instance, **kwargs):
    """配置変更時にキャッシュを無効化"""
    ShelfCacheManager.invalidate_shelf_cache(instance.shelf.id)


@receiver([post_save, post_delete], sender='shelves.PlacementConflict')
def invalidate_conflict_cache(sender, instance, **kwargs):
    """競合変更時にキャッシュを無効化"""
    ShelfCacheManager.invalidate_shelf_cache(instance.placement.shelf.id)


# ==================== utils/database_optimizer.py ====================

from django.db import connection
from django.core.management.base import BaseCommand


class DatabaseOptimizer:
    """データベース最適化ユーティリティ"""
    
    @staticmethod
    def create_optimized_indexes():
        """最適化されたインデックスを作成"""
        with connection.cursor() as cursor:
            # 棚割り検索用複合インデックス
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_shelf_placement_lookup 
                ON shelves_shelfplacement(shelf_id, row, column, span_rows, span_columns);
            """)
            
            # 商品サイズ検索用インデックス
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_product_size 
                ON products_product(width, height, depth) 
                WHERE width IS NOT NULL AND height IS NOT NULL;
            """)
            
            # 配置競合検索用インデックス
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_placement_conflict_range 
                ON shelves_placementconflict(placement_id, row, column);
            """)
            
            # 商品検索用複合インデックス
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_product_search 
                ON products_product(is_active, is_own_product, category_id, maker_id);
            """)
    
    @staticmethod
    def analyze_query_performance():
        """クエリパフォーマンスを分析"""
        with connection.cursor() as cursor:
            # 遅いクエリを特定
            cursor.execute("""
                SELECT 
                    query,
                    mean_exec_time,
                    calls,
                    total_exec_time
                FROM pg_stat_statements 
                WHERE query LIKE '%shelf%' OR query LIKE '%product%'
                ORDER BY mean_exec_time DESC 
                LIMIT 10;
            """)
            
            return cursor.fetchall()

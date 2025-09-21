# ==================== tests/test_shelf_performance.py ====================

from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.core.cache import cache
from django.db import transaction
from django.contrib.auth.models import User
import time
import json

from products.models import Product, Maker, Category
from shelves.models import Shelf, ShelfPlacement
from utils.cache_manager import ShelfCacheManager


class ShelfPerformanceTest(TransactionTestCase):
    """棚割りパフォーマンステスト"""
    
    def setUp(self):
        # テストデータ作成
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.maker = Maker.objects.create(name='テストメーカー')
        self.category = Category.objects.create(name='テストカテゴリ')
        
        # 大きな棚を作成
        self.shelf = Shelf.objects.create(
            name='大型テスト棚',
            width=200.0,
            height=180.0,
            depth=60.0,
            rows=10,
            columns=20,
            created_by=self.user
        )
        
        # 多数の商品を作成
        self.products = []
        for i in range(100):
            product = Product.objects.create(
                product_name=f'テスト商品{i}',
                product_code=f'TEST{i:06d}',
                maker=self.maker,
                category=self.category,
                width=10.0 + (i % 5) * 2,
                height=15.0 + (i % 3) * 5,
                depth=5.0,
                is_own_product=(i % 3 == 0),
                created_by=self.user
            )
            self.products.append(product)
    
    def test_large_grid_generation_performance(self):
        """大きなグリッド生成のパフォーマンステスト"""
        # 多数の配置を作成
        placements = []
        for i, product in enumerate(self.products[:50]):  # 50商品配置
            row = i // 20
            column = i % 20
            if row < self.shelf.rows and column < self.shelf.columns:
                placement = ShelfPlacement.objects.create(
                    shelf=self.shelf,
                    product=product,
                    row=row,
                    column=column,
                    face_count=1,
                    span_rows=1,
                    span_columns=1,
                    created_by=self.user
                )
                placements.append(placement)
        
        # パフォーマンス測定
        start_time = time.time()
        grid_data = ShelfCacheManager.get_placement_grid(self.shelf.id)
        generation_time = time.time() - start_time
        
        # アサーション
        self.assertIsNotNone(grid_data)
        self.assertEqual(len(grid_data['grid']), self.shelf.rows)
        self.assertEqual(len(grid_data['grid'][0]), self.shelf.columns)
        self.assertLess(generation_time, 2.0, "グリッド生成が2秒以内に完了すること")
        
        print(f"グリッド生成時間: {generation_time:.3f}秒")
    
    def test_cache_effectiveness(self):
        """キャッシュ効果のテスト"""
        # 初回アクセス（キャッシュなし）
        cache.clear()
        start_time = time.time()
        grid_data1 = ShelfCacheManager.get_placement_grid(self.shelf.id)
        first_access_time = time.time() - start_time
        
        # 2回目アクセス（キャッシュあり）
        start_time = time.time()
        grid_data2 = ShelfCacheManager.get_placement_grid(self.shelf.id)
        cached_access_time = time.time() - start_time
        
        # アサーション
        self.assertEqual(grid_data1['shelf_info']['id'], grid_data2['shelf_info']['id'])
        self.assertLess(cached_access_time, first_access_time / 5, "キャッシュアクセスが5倍以上高速であること")
        
        print(f"初回アクセス: {first_access_time:.3f}秒")
        print(f"キャッシュアクセス: {cached_access_time:.3f}秒")
        print(f"高速化倍率: {first_access_time / cached_access_time:.1f}倍")
    
    def test_concurrent_placement_operations(self):
        """並行配置操作のテスト"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def place_products(start_idx, count):
            """商品配置を並行実行"""
            try:
                with transaction.atomic():
                    for i in range(start_idx, start_idx + count):
                        if i < len(self.products):
                            row = i // 20
                            column = i % 20
                            if row < self.shelf.rows and column < self.shelf.columns:
                                ShelfPlacement.objects.create(
                                    shelf=self.shelf,
                                    product=self.products[i],
                                    row=row,
                                    column=column,
                                    face_count=1,
                                    span_rows=1,
                                    span_columns=1,
                                    created_by=self.user
                                )
                results_queue.put(f"Thread {start_idx}: Success")
            except Exception as e:
                results_queue.put(f"Thread {start_idx}: Error - {str(e)}")
        
        # 複数スレッドで配置操作を実行
        threads = []
        thread_count = 4
        products_per_thread = 10
        
        start_time = time.time()
        for i in range(thread_count):
            thread = threading.Thread(
                target=place_products, 
                args=(i * products_per_thread, products_per_thread)
            )
            threads.append(thread)
            thread.start()
        
        # 全スレッドの完了を待機
        for thread in threads:
            thread.join()
        
        concurrent_time = time.time() - start_time
        
        # 結果確認
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        success_count = len([r for r in results if 'Success' in r])
        
        self.assertGreater(success_count, 0, "並行操作で少なくとも1つは成功すること")
        self.assertLess(concurrent_time, 5.0, "並行操作が5秒以内に完了すること")
        
        print(f"並行操作時間: {concurrent_time:.3f}秒")
        print(f"成功したスレッド数: {success_count}/{thread_count}")
    
    def test_memory_usage_optimization(self):
        """メモリ使用量最適化のテスト"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # 初期メモリ使用量
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 大量の配置データを作成
        placements = []
        for i in range(200):  # より多くの配置
            row = i // 20
            column = i % 20
            if row < self.shelf.rows and column < self.shelf.columns:
                placement = ShelfPlacement.objects.create(
                    shelf=self.shelf,
                    product=self.products[i % len(self.products)],
                    row=row,
                    column=column,
                    face_count=1,
                    span_rows=1,
                    span_columns=1,
                    created_by=self.user
                )
                placements.append(placement)
        
        # グリッドデータ生成
        grid_data = ShelfCacheManager.get_placement_grid(self.shelf.id)
        
        # 最終メモリ使用量
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # アサーション
        self.assertIsNotNone(grid_data)
        self.assertLess(memory_increase, 100, "メモリ増加量が100MB以下であること")
        
        print(f"初期メモリ: {initial_memory:.1f}MB")
        print(f"最終メモリ: {final_memory:.1f}MB")
        print(f"メモリ増加: {memory_increase:.1f}MB")


class ShelfSizeAwareTest(TestCase):
    """サイズベース棚割りテスト"""
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.maker = Maker.objects.create(name='テストメーカー')
        self.category = Category.objects.create(name='飲料')
        
        self.shelf = Shelf.objects.create(
            name='テスト棚',
            width=120.0,
            height=180.0,
            depth=60.0,
            rows=6,
            columns=8,
            created_by=self.user
        )
        
        # 異なるサイズの商品を作成
        self.small_product = Product.objects.create(
            product_name='小型商品',
            product_code='SMALL001',
            maker=self.maker,
            category=self.category,
            width=8.0,   # セル幅15cmより小さい
            height=12.0, # セル高さ30cmより小さい
            is_own_product=True,
            created_by=self.user
        )
        
        self.large_product = Product.objects.create(
            product_name='大型商品',
            product_code='LARGE001',
            maker=self.maker,
            category=self.category,
            width=35.0,  # 複数セルを占有
            height=45.0, # 複数セルを占有
            is_own_product=True,
            created_by=self.user
        )
    
    def test_size_calculation(self):
        """サイズ計算のテスト"""
        # 小型商品のセル数計算
        small_required = self.shelf.calculate_required_cells(self.small_product)
        self.assertEqual(small_required['span_rows'], 1)
        self.assertEqual(small_required['span_columns'], 1)
        
        # 大型商品のセル数計算
        large_required = self.shelf.calculate_required_cells(self.large_product)
        self.assertGreater(large_required['span_rows'], 1)
        self.assertGreater(large_required['span_columns'], 1)
    
    def test_placement_possibility(self):
        """配置可能性のテスト"""
        # 小型商品は配置可能
        self.assertTrue(self.shelf.can_place_product(self.small_product, 0, 0))
        
        # 大型商品も適切な位置なら配置可能
        self.assertTrue(self.shelf.can_place_product(self.large_product, 0, 0))
        
        # 棚の範囲外は配置不可
        self.assertFalse(self.shelf.can_place_product(self.large_product, 5, 7))
    
    def test_product_compatibility(self):
        """商品適合性のテスト"""
        small_compat = self.small_product.calculate_shelf_compatibility(self.shelf)
        self.assertTrue(small_compat['compatible'])
        self.assertEqual(small_compat['required_cells'], 1)
        
        large_compat = self.large_product.calculate_shelf_compatibility(self.shelf)
        # 大型商品も配置は可能だが制限があることを確認
        self.assertGreater(large_compat['required_cells'], 1)


# ==================== management/commands/performance_test.py ====================

from django.core.management.base import BaseCommand
from django.test.utils import setup_test_environment, teardown_test_environment
from django.test.runner import DiscoverRunner
from django.conf import settings
import time


class Command(BaseCommand):
    help = 'パフォーマンステストを実行'

    def add_arguments(self, parser):
        parser.add_argument(
            '--iterations',
            type=int,
            default=10,
            help='テスト実行回数'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='詳細ログを出力'
        )

    def handle(self, *args, **options):
        iterations = options['iterations']
        verbose = options['verbose']
        
        self.stdout.write('パフォーマンステストを開始します...')
        
        # テスト環境セットアップ
        setup_test_environment()
        runner = DiscoverRunner(verbosity=2 if verbose else 1)
        
        total_time = 0
        
        for i in range(iterations):
            self.stdout.write(f'実行 {i+1}/{iterations}')
            
            start_time = time.time()
            
            # 特定のテストクラスを実行
            suite = runner.setup_databases()
            result = runner.run_tests(['tests.test_shelf_performance.ShelfPerformanceTest'])
            runner.teardown_databases(suite)
            
            iteration_time = time.time() - start_time
            total_time += iteration_time
            
            if verbose:
                self.stdout.write(f'実行時間: {iteration_time:.2f}秒')
        
        # 結果サマリー
        average_time = total_time / iterations
        self.stdout.write(
            self.style.SUCCESS(
                f'\nパフォーマンステスト完了\n'
                f'総実行時間: {total_time:.2f}秒\n'
                f'平均実行時間: {average_time:.2f}秒\n'
                f'実行回数: {iterations}回'
            )
        )
        
        teardown_test_environment()
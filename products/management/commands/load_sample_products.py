from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from products.models import Maker, Brand, Category, Product
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'サンプル商品データを投入します'

    def handle(self, *args, **options):
        # 既存のメーカー、ブランド、カテゴリを取得
        try:
            # 飲料カテゴリの商品
            beverage_category = Category.objects.get(name='飲料')
            coca_cola_maker = Maker.objects.get(name='コカ・コーラ')
            suntory_maker = Maker.objects.get(name='サントリー')
            
            # 菓子カテゴリの商品
            snack_category = Category.objects.get(name='菓子')
            morinaga_maker = Maker.objects.get(name='森永製菓')
            glico_maker = Maker.objects.get(name='グリコ')
            calbee_maker = Maker.objects.get(name='カルビー')
            
            # 日用品カテゴリの商品
            daily_category = Category.objects.get(name='日用品')
            kao_maker = Maker.objects.get(name='花王')
            lion_maker = Maker.objects.get(name='ライオン')
            
        except (Category.DoesNotExist, Maker.DoesNotExist) as e:
            self.stdout.write(self.style.ERROR(f'必要なカテゴリまたはメーカーが見つかりません: {e}'))
            self.stdout.write('先に load_initial_data コマンドを実行してください')
            return

        # サンプル商品データ
        sample_products = [
            # 飲料（自社商品）
            {
                'product_name': 'コカ・コーラ 500ml',
                'product_code': '4902102072577',
                'maker': coca_cola_maker,
                'category': beverage_category,
                'size': '500ml',
                'price': Decimal('150.00'),
                'width': 6.5,
                'height': 20.5,
                'depth': 6.5,
                'is_own_product': True,
            },
            {
                'product_name': 'ファンタ オレンジ 500ml',
                'product_code': '4902102072584',
                'maker': coca_cola_maker,
                'category': beverage_category,
                'size': '500ml',
                'price': Decimal('150.00'),
                'width': 6.5,
                'height': 20.5,
                'depth': 6.5,
                'is_own_product': True,
            },
            {
                'product_name': 'スプライト 500ml',
                'product_code': '4902102072591',
                'maker': coca_cola_maker,
                'category': beverage_category,
                'size': '500ml',
                'price': Decimal('150.00'),
                'width': 6.5,
                'height': 20.5,
                'depth': 6.5,
                'is_own_product': True,
            },
            
            # 飲料（競合商品）
            {
                'product_name': 'C.C.レモン 500ml',
                'product_code': '4901777245617',
                'maker': suntory_maker,
                'category': beverage_category,
                'size': '500ml',
                'price': Decimal('140.00'),
                'width': 6.5,
                'height': 20.5,
                'depth': 6.5,
                'is_own_product': False,
            },
            {
                'product_name': 'なっちゃん オレンジ 500ml',
                'product_code': '4901777245624',
                'maker': suntory_maker,
                'category': beverage_category,
                'size': '500ml',
                'price': Decimal('140.00'),
                'width': 6.5,
                'height': 20.5,
                'depth': 6.5,
                'is_own_product': False,
            },
            
            # 菓子（自社商品）
            {
                'product_name': 'チョコボール ピーナッツ',
                'product_code': '4902888543210',
                'maker': morinaga_maker,
                'category': snack_category,
                'size': '28g',
                'price': Decimal('120.00'),
                'width': 8.0,
                'height': 12.0,
                'depth': 3.5,
                'is_own_product': True,
            },
            {
                'product_name': 'ハイチュウ ストロベリー',
                'product_code': '4902888543227',
                'maker': morinaga_maker,
                'category': snack_category,
                'size': '12粒',
                'price': Decimal('110.00'),
                'width': 7.5,
                'height': 11.0,
                'depth': 2.0,
                'is_own_product': True,
            },
            
            # 菓子（競合商品）
            {
                'product_name': 'ポッキー チョコレート',
                'product_code': '4901005543211',
                'maker': glico_maker,
                'category': snack_category,
                'size': '2袋',
                'price': Decimal('140.00'),
                'width': 15.5,
                'height': 2.5,
                'depth': 18.0,
                'is_own_product': False,
            },
            {
                'product_name': 'プリッツ サラダ',
                'product_code': '4901005543228',
                'maker': glico_maker,
                'category': snack_category,
                'size': '69g',
                'price': Decimal('130.00'),
                'width': 6.0,
                'height': 19.0,
                'depth': 6.0,
                'is_own_product': False,
            },
            {
                'product_name': 'カルビー ポテトチップス うすしお味',
                'product_code': '4901330543235',
                'maker': calbee_maker,
                'category': snack_category,
                'size': '60g',
                'price': Decimal('150.00'),
                'width': 18.0,
                'height': 23.0,
                'depth': 8.0,
                'is_own_product': False,
            },
            
            # 日用品（競合商品）
            {
                'product_name': 'アタック 洗濯洗剤',
                'product_code': '4901301543242',
                'maker': kao_maker,
                'category': daily_category,
                'size': '1kg',
                'price': Decimal('398.00'),
                'width': 15.0,
                'height': 25.0,
                'depth': 8.0,
                'is_own_product': False,
            },
            {
                'product_name': 'トップ 洗濯洗剤',
                'product_code': '4903301543259',
                'maker': lion_maker,
                'category': daily_category,
                'size': '900g',
                'price': Decimal('368.00'),
                'width': 14.5,
                'height': 24.0,
                'depth': 7.5,
                'is_own_product': False,
            },
        ]
        
        created_count = 0
        
        for product_data in sample_products:
            product, created = Product.objects.get_or_create(
                product_code=product_data['product_code'],
                defaults=product_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'商品 "{product.product_name}" を作成しました')
            else:
                self.stdout.write(f'商品 "{product.product_name}" は既に存在します')
        
        # 追加のランダム商品を生成
        self.create_random_products()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'サンプル商品データの投入が完了しました。新規作成: {created_count}件'
            )
        )

    def create_random_products(self):
        """ランダムな商品を追加作成"""
        try:
            makers = list(Maker.objects.all())
            categories = list(Category.objects.all())
            
            if not makers or not categories:
                return
            
            # 追加の商品名パターン
            product_patterns = [
                ('ドリンク', '飲料'),
                ('スナック', '菓子'),
                ('クッキー', '菓子'),
                ('ジュース', '飲料'),
                ('シャンプー', '日用品'),
                ('石鹸', '日用品'),
                ('チョコレート', '菓子'),
                ('キャンディ', '菓子'),
                ('コーヒー', '飲料'),
                ('お茶', '飲料'),
            ]
            
            additional_count = 0
            
            for i, (product_type, category_name) in enumerate(product_patterns, 1):
                try:
                    category = Category.objects.get(name=category_name)
                    maker = random.choice(makers)
                    
                    product_name = f'{maker.name} {product_type} {i}'
                    product_code = f'490{random.randint(1000, 9999)}{random.randint(100000, 999999)}'
                    
                    # 既存チェック
                    if Product.objects.filter(product_code=product_code).exists():
                        continue
                    
                    product = Product.objects.create(
                        product_name=product_name,
                        product_code=product_code,
                        maker=maker,
                        category=category,
                        size=f'{random.randint(50, 500)}{"ml" if category_name == "飲料" else "g"}',
                        price=Decimal(f'{random.randint(100, 500)}.00'),
                        width=random.uniform(5.0, 20.0),
                        height=random.uniform(10.0, 30.0),
                        depth=random.uniform(3.0, 15.0),
                        is_own_product=random.choice([True, False]),
                    )
                    
                    additional_count += 1
                    
                except Category.DoesNotExist:
                    continue
            
            if additional_count > 0:
                self.stdout.write(f'追加で {additional_count} 件のランダム商品を作成しました')
                
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'ランダム商品の作成中にエラー: {e}'))
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tanaoroshi.models import Maker, Brand, Category, Customer


class Command(BaseCommand):
    help = '初期データを投入します'

    def handle(self, *args, **options):
        # スーパーユーザー作成（開発用）
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin')
            self.stdout.write('スーパーユーザー admin を作成しました')

        # メーカーサンプルデータ
        makers_data = [
            'コカ・コーラ', 'サントリー', 'キリン', 'アサヒ', 'ポッカサッポロ',
            '森永製菓', 'グリコ', 'ロッテ', 'カルビー', '湖池屋',
            '花王', 'ライオン', 'P&G', 'ユニ・チャーム', '資生堂'
        ]
        
        for maker_name in makers_data:
            maker, created = Maker.objects.get_or_create(name=maker_name)
            if created:
                self.stdout.write(f'メーカー {maker_name} を作成しました')

        # カテゴリサンプルデータ
        categories_data = [
            '飲料', '菓子', '日用品', '化粧品', '食品',
            '冷凍食品', 'パン', '酒類', 'たばこ', '雑誌'
        ]
        
        for category_name in categories_data:
            category, created = Category.objects.get_or_create(name=category_name)
            if created:
                self.stdout.write(f'カテゴリ {category_name} を作成しました')

        # 得意先サンプルデータ
        customers_data = [
            'セブン-イレブン', 'ファミリーマート', 'ローソン',
            'イオン', 'イトーヨーカドー', 'ライフ',
            'コスモス薬品', 'マツモトキヨシ', 'ウエルシア'
        ]
        
        for customer_name in customers_data:
            customer, created = Customer.objects.get_or_create(name=customer_name)
            if created:
                self.stdout.write(f'得意先 {customer_name} を作成しました')

        self.stdout.write(self.style.SUCCESS('初期データの投入が完了しました'))
        
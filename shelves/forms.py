from django import forms
from django.core.exceptions import ValidationError
from .models import Shelf, ShelfPlacement
from products.models import Product


class ShelfSizeAwareForm(forms.ModelForm):
    """サイズベース棚フォーム"""
    
    # 自動計算オプション
    auto_calculate_cell_size = forms.BooleanField(
        label='セルサイズを自動計算',
        required=False,
        initial=True,
        help_text='チェックを外すと手動でセルサイズを設定できます'
    )
    
    class Meta:
        model = Shelf
        fields = [
            'name', 'description', 'width', 'height', 'depth', 
            'rows', 'columns', 'cell_width', 'cell_height'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '1'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '1'}),
            'depth': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '1'}),
            'rows': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '20'}),
            'columns': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '20'}),
            'cell_width': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'cell_height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # セルサイズフィールドは初期状態で無効
        self.fields['cell_width'].required = False
        self.fields['cell_height'].required = False
        
        # 既存データがある場合の処理
        if self.instance.pk:
            if self.instance.cell_width or self.instance.cell_height:
                self.fields['auto_calculate_cell_size'].initial = False
    
    def clean(self):
        cleaned_data = super().clean()
        auto_calculate = cleaned_data.get('auto_calculate_cell_size', True)
        width = cleaned_data.get('width')
        height = cleaned_data.get('height')
        rows = cleaned_data.get('rows')
        columns = cleaned_data.get('columns')
        cell_width = cleaned_data.get('cell_width')
        cell_height = cleaned_data.get('cell_height')
        
        if auto_calculate:
            # 自動計算の場合、セルサイズをクリア
            cleaned_data['cell_width'] = None
            cleaned_data['cell_height'] = None
        else:
            # 手動設定の場合、必須チェック
            if not cell_width:
                raise ValidationError({'cell_width': 'セルサイズを手動設定する場合、セル幅は必須です。'})
            if not cell_height:
                raise ValidationError({'cell_height': 'セルサイズを手動設定する場合、セル高さは必須です。'})
            
            # セルサイズの妥当性チェック
            if width and rows and cell_width:
                if cell_width * columns > width:
                    raise ValidationError({
                        'cell_width': f'セル幅が大きすぎます。最大: {width / columns:.1f}cm'
                    })
            
            if height and rows and cell_height:
                if cell_height * rows > height:
                    raise ValidationError({
                        'cell_height': f'セル高さが大きすぎます。最大: {height / rows:.1f}cm'
                    })
        
        return cleaned_data


class ProductPlacementSizeForm(forms.Form):
    """サイズ考慮商品配置フォーム"""
    shelf_id = forms.IntegerField(widget=forms.HiddenInput())
    product_id = forms.IntegerField(widget=forms.HiddenInput())
    row = forms.IntegerField(min_value=0)
    column = forms.IntegerField(min_value=0)
    face_count = forms.IntegerField(min_value=1, initial=1)
    
    # サイズ調整オプション
    force_placement = forms.BooleanField(
        label='サイズが合わなくても強制配置',
        required=False,
        help_text='商品が大きすぎる場合でも配置を試行します'
    )
    
    adjust_size = forms.BooleanField(
        label='商品画像を自動リサイズ',
        required=False,
        initial=True,
        help_text='セルサイズに合わせて商品画像を調整します'
    )
    
    def __init__(self, *args, **kwargs):
        self.shelf = kwargs.pop('shelf', None)
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        
        if self.shelf:
            self.fields['row'].widget.attrs['max'] = self.shelf.rows - 1
            self.fields['column'].widget.attrs['max'] = self.shelf.columns - 1
    
    def clean(self):
        cleaned_data = super().clean()
        shelf_id = cleaned_data.get('shelf_id')
        product_id = cleaned_data.get('product_id')
        row = cleaned_data.get('row')
        column = cleaned_data.get('column')
        face_count = cleaned_data.get('face_count', 1)
        force_placement = cleaned_data.get('force_placement', False)
        
        if shelf_id and product_id and row is not None and column is not None:
            try:
                shelf = Shelf.objects.get(id=shelf_id)
                product = Product.objects.get(id=product_id)
                
                # 配置可能性チェック
                if not force_placement and not shelf.can_place_product(product, row, column, face_count):
                    raise ValidationError(
                        'この位置には配置できません。他の商品と重複するか、棚の範囲を超えています。'
                    )
                
                # 必要セル数を計算して警告
                required_cells = shelf.calculate_required_cells(product, face_count)
                if required_cells['span_rows'] > 3 or required_cells['span_columns'] > 3:
                    self.add_warning(
                        f'この商品は{required_cells["span_rows"]}×{required_cells["span_columns"]}セルを占有します。'
                    )
                
            except (Shelf.DoesNotExist, Product.DoesNotExist):
                raise ValidationError('指定された棚または商品が見つかりません。')
        
        return cleaned_data
    
    def add_warning(self, message):
        """警告メッセージを追加（カスタムメソッド）"""
        if not hasattr(self, '_warnings'):
            self._warnings = []
        self._warnings.append(message)
    
    @property
    def warnings(self):
        """警告メッセージを取得"""
        return getattr(self, '_warnings', [])


class ShelfSearchForm(forms.Form):
    """棚検索フォーム（サイズフィルタ付き）"""
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '棚名、説明'
        })
    )
    
    size_category = forms.ChoiceField(
        choices=[
            ('', 'すべてのサイズ'),
            ('small', '小型棚（〜50cm）'),
            ('medium', '中型棚（50-100cm）'),
            ('large', '大型棚（100cm〜）'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    cell_size_range = forms.ChoiceField(
        choices=[
            ('', 'すべて'),
            ('fine', '細かいセル（〜5cm）'),
            ('normal', '通常セル（5-15cm）'),
            ('large', '大きなセル（15cm〜）'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class PlacementAnalysisForm(forms.Form):
    """配置分析フォーム"""
    shelf = forms.ModelChoiceField(
        queryset=Shelf.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    analysis_type = forms.ChoiceField(
        choices=[
            ('utilization', '利用率分析'),
            ('optimization', '最適化提案'),
            ('conflicts', '競合分析'),
            ('size_distribution', 'サイズ分布'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    include_suggestions = forms.BooleanField(
        label='改善提案を含める',
        required=False,
        initial=True
    )
# shelves/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Shelf, ShelfPlacement
from products.models import Product


class ShelfForm(forms.ModelForm):
    """棚フォーム"""
    
    class Meta:
        model = Shelf
        fields = ['name', 'description', 'width', 'height', 'depth', 'rows', 'columns']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '1'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '1'}),
            'depth': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '1'}),
            'rows': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '20'}),
            'columns': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '20'}),
        }


class ShelfSearchForm(forms.Form):
    """棚検索フォーム"""
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '棚名、説明'
        })
    )


class ShelfPlacementForm(forms.Form):
    """棚配置フォーム"""
    shelf_id = forms.IntegerField(widget=forms.HiddenInput())
    product_id = forms.IntegerField(widget=forms.HiddenInput())
    row = forms.IntegerField(min_value=0)
    column = forms.IntegerField(min_value=0)
    face_count = forms.IntegerField(min_value=1, initial=1)
    span_rows = forms.IntegerField(min_value=1, initial=1)
    span_columns = forms.IntegerField(min_value=1, initial=1)
    
    def clean(self):
        cleaned_data = super().clean()
        shelf_id = cleaned_data.get('shelf_id')
        row = cleaned_data.get('row')
        column = cleaned_data.get('column')
        span_rows = cleaned_data.get('span_rows', 1)
        span_columns = cleaned_data.get('span_columns', 1)
        
        if shelf_id and row is not None and column is not None:
            try:
                shelf = Shelf.objects.get(id=shelf_id)
                
                # 範囲チェック
                if row >= shelf.rows or column >= shelf.columns:
                    raise ValidationError('指定された位置が棚の範囲外です。')
                
                if row + span_rows > shelf.rows or column + span_columns > shelf.columns:
                    raise ValidationError('占有サイズが棚の範囲を超えています。')
                
            except Shelf.DoesNotExist:
                raise ValidationError('指定された棚が見つかりません。')
        
        return cleaned_data
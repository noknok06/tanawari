# products/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Product, Maker, Brand, Category


class ProductForm(forms.ModelForm):
    """商品フォーム"""
    
    class Meta:
        model = Product
        fields = [
            'product_name', 'product_code', 'maker', 'brand', 'category',
            'size', 'price', 'width', 'height', 'depth', 'image', 'is_own_product'
        ]
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'product_code': forms.TextInput(attrs={'class': 'form-control'}),
            'maker': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'size': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'depth': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_own_product': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ブランドのクエリセットを空にしておく（JavaScriptで動的に更新）
        self.fields['brand'].queryset = Brand.objects.none()
        
        if 'maker' in self.data:
            try:
                maker_id = int(self.data.get('maker'))
                self.fields['brand'].queryset = Brand.objects.filter(maker_id=maker_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.maker:
            self.fields['brand'].queryset = self.instance.maker.brand_set.order_by('name')


class MakerForm(forms.ModelForm):
    """メーカーフォーム"""
    
    class Meta:
        model = Maker
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }


class BrandForm(forms.ModelForm):
    """ブランドフォーム"""
    
    class Meta:
        model = Brand
        fields = ['maker', 'name']
        widgets = {
            'maker': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }


class CategoryForm(forms.ModelForm):
    """カテゴリフォーム"""
    
    class Meta:
        model = Category
        fields = ['parent', 'name']
        widgets = {
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }


class ProductSearchForm(forms.Form):
    """商品検索フォーム"""
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '商品名、JANコード、メーカー名'
        })
    )
    maker = forms.ModelChoiceField(
        queryset=Maker.objects.all(),
        required=False,
        empty_label='すべて',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='すべて',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_own = forms.ChoiceField(
        choices=[('', 'すべて'), ('true', '自社商品'), ('false', '競合商品')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
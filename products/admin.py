# products/admin.py
from django.contrib import admin
from .models import Maker, Brand, Category, Product


@admin.register(Maker)
class MakerAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'created_by')
    list_filter = ('created_at',)
    search_fields = ('name',)
    readonly_fields = ('created_at',)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'maker', 'created_at', 'created_by')
    list_filter = ('maker', 'created_at')
    search_fields = ('name', 'maker__name')
    readonly_fields = ('created_at',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'created_at', 'created_by')
    list_filter = ('parent', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'product_code', 'maker', 'brand', 'category', 'is_own_product', 'is_active')
    list_filter = ('maker', 'brand', 'category', 'is_own_product', 'is_active', 'created_at')
    search_fields = ('product_name', 'product_code', 'maker__name')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_own_product', 'is_active')



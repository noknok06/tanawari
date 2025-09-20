# shelves/admin.py
from django.contrib import admin
from .models import Shelf, ShelfPlacement


@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = ('name', 'width', 'height', 'depth', 'rows', 'columns', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ShelfPlacement)
class ShelfPlacementAdmin(admin.ModelAdmin):
    list_display = ('shelf', 'product', 'row', 'column', 'face_count', 'created_at')
    list_filter = ('shelf', 'product__is_own_product', 'created_at')
    search_fields = ('shelf__name', 'product__product_name')
    readonly_fields = ('created_at',)

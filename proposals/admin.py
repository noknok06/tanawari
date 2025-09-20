# proposals/admin.py
from django.contrib import admin
from .models import Customer, Proposal


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'contact_person', 'email')
    readonly_fields = ('created_at',)


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ('title', 'customer', 'shelf', 'status', 'proposal_date', 'created_at')
    list_filter = ('status', 'customer', 'proposal_date', 'created_at')
    search_fields = ('title', 'customer__name', 'shelf__name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'proposal_date'
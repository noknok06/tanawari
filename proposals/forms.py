# ==================== proposals/forms.py ====================

from django import forms
from .models import Proposal, Customer
from shelves.models import Shelf


class ProposalForm(forms.ModelForm):
    """提案フォーム"""
    
    class Meta:
        model = Proposal
        fields = ['title', 'customer', 'shelf', 'sales_rep', 'proposal_date', 'status', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'shelf': forms.Select(attrs={'class': 'form-select'}),
            'sales_rep': forms.TextInput(attrs={'class': 'form-control'}),
            'proposal_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class CustomerForm(forms.ModelForm):
    """得意先フォーム"""
    
    class Meta:
        model = Customer
        fields = ['name', 'contact_person', 'phone', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ProposalSearchForm(forms.Form):
    """提案検索フォーム"""
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '提案タイトル、得意先名'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'すべて')] + Proposal.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        empty_label='すべて',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
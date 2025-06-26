from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum
from django.contrib.auth import get_user_model

# Custom admin site configuration
class GaspackAdminSite(AdminSite):
    site_header = "Gaspack RWA Administration"
    site_title = "Gaspack RWA Admin"
    index_title = "Welcome to Gaspack RWA Administration"
    
    def index(self, request, extra_context=None):
        """
        Custom admin index page with dashboard statistics
        """
        extra_context = extra_context or {}
        
        # Import models here to avoid circular imports
        from assets.models import Asset, Purchase
        from nft_simulator.models import SimulatedNFT
        from payments.models import PaymentLog
        from benefits.models import BenefitRule, UserBenefitClaim
        
        User = get_user_model()
        
        # Dashboard statistics
        stats = {
            'total_users': User.objects.filter(is_deleted=False).count(),
            'total_assets': Asset.objects.filter(is_deleted=False).count(),
            'total_nfts': SimulatedNFT.objects.filter(is_deleted=False).count(),
            'total_purchases': Purchase.objects.filter(is_deleted=False).count(),
            'completed_payments': PaymentLog.objects.filter(status='completed', is_deleted=False).count(),
            'pending_payments': PaymentLog.objects.filter(status='pending', is_deleted=False).count(),
            'active_benefits': BenefitRule.objects.filter(is_active=True, is_deleted=False).count(),
            'pending_claims': UserBenefitClaim.objects.filter(claim_status='pending', is_deleted=False).count(),
        }
        
        # Financial statistics
        try:
            total_revenue = PaymentLog.objects.filter(
                status='completed', is_deleted=False
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            total_asset_value = Asset.objects.filter(
                is_deleted=False
            ).aggregate(
                total=Sum('total_slots') * Sum('price_per_slot')
            )['total'] or 0
        except:
            total_revenue = 0
            total_asset_value = 0
        
        stats.update({
            'total_revenue': total_revenue,
            'total_asset_value': total_asset_value,
        })
        
        extra_context['dashboard_stats'] = stats
        
        return super().index(request, extra_context)

# You can register this custom admin site if needed
# gaspack_admin_site = GaspackAdminSite(name='gaspack_admin')

# Custom admin actions and utilities
def export_to_csv(modeladmin, request, queryset):
    """
    Generic CSV export action for any model
    """
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{modeladmin.model._meta.verbose_name_plural}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    field_names = [field.name for field in modeladmin.model._meta.fields]
    writer.writerow(field_names)
    
    # Write data
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in field_names])
    
    return response

export_to_csv.short_description = "Export selected items to CSV"

# Custom admin mixins
class SoftDeleteAdminMixin:
    """
    Mixin to add soft delete functionality to admin classes
    """
    def get_queryset(self, request):
        # Show all objects including soft-deleted ones
        return self.model.objects.all()
    
    def delete_view(self, request, object_id, extra_context=None):
        """
        Override delete to perform soft delete instead
        """
        obj = self.get_object(request, object_id)
        if obj and hasattr(obj, 'is_deleted'):
            obj.is_deleted = True
            obj.save()
            self.message_user(request, f'{obj} was soft deleted.')
            return self.response_delete(request, obj)
        return super().delete_view(request, object_id, extra_context)

class TimestampAdminMixin:
    """
    Mixin to add common timestamp fields to admin classes
    """
    readonly_fields = ('created_at', 'updated_at')
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if hasattr(self.model, 'created_at'):
            readonly_fields.append('created_at')
        if hasattr(self.model, 'updated_at'):
            readonly_fields.append('updated_at')
        return readonly_fields

# Utility functions for admin displays
def get_status_display(status, status_choices=None):
    """
    Generate colored status display for admin
    """
    colors = {
        'active': '#4caf50',
        'inactive': '#ff9800',
        'pending': '#ff9800',
        'completed': '#4caf50',
        'failed': '#f44336',
        'cancelled': '#9e9e9e',
        'approved': '#4caf50',
        'rejected': '#f44336',
        'processed': '#2196f3',
    }
    
    color = colors.get(status.lower(), '#666')
    display_text = status.replace('_', ' ').title()
    
    if status_choices:
        for choice_value, choice_display in status_choices:
            if choice_value == status:
                display_text = choice_display
                break
    
    return format_html(
        '<span style="color: {}; font-weight: bold;">{}</span>',
        color, display_text
    )

def get_currency_display(amount, currency='IDR'):
    """
    Generate formatted currency display for admin
    """
    amount = float(amount)  # Ensure amount is a proper numeric type
    if currency == 'IDR':
        return format_html(
            '<span style="font-weight: bold; color: #4CAF50;">Rp {:,.0f}</span>',
            amount
        )
    else:
        return format_html(
            '<span style="font-weight: bold; color: #4CAF50;">{} {:,.2f}</span>',
            currency, amount
        )

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count
from .models import PaymentLog


@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = (
        'idrx_transaction_id', 'user_link', 'amount', 'currency',
        'status_display', 'payment_method', 'is_deleted_display', 'created_at'
    )
    list_filter = ('status', 'currency', 'payment_method', 'is_deleted', 'created_at', 'updated_at')
    search_fields = ('idrx_transaction_id', 'user__username', 'user__email', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('id', 'user', 'idrx_transaction_id', 'amount', 'currency')
        }),
        ('Payment Details', {
            'fields': ('status', 'payment_method', 'description')
        }),
        ('Status & Timestamps', {
            'fields': ('is_deleted', 'created_at', 'updated_at')
        }),
    )
    
    def user_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html(
            '<a href="{}" title="{}">{}</a>',
            url, obj.user.email, obj.user.username
        )
    user_link.short_description = 'User'
    
    def status_display(self, obj):
        colors = {
            'pending': '#ff9800',
            'processing': '#2196f3',
            'completed': '#4caf50',
            'failed': '#f44336',
            'cancelled': '#9e9e9e'
        }
        icons = {
            'pending': '⏳',
            'processing': '🔄',
            'completed': '✅',
            'failed': '❌',
            'cancelled': '🚫'
        }
        color = colors.get(obj.status, '#666')
        icon = icons.get(obj.status, '❓')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def is_deleted_display(self, obj):
        if obj.is_deleted:
            return format_html(
                '<span style="color: red; font-weight: bold;">🗑️ Deleted</span>'
            )
        return format_html(
            '<span style="color: green;">✅ Active</span>'
        )
    is_deleted_display.short_description = 'Record Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    actions = [
        'mark_as_completed', 'mark_as_failed', 'mark_as_processing', 
        'mark_as_cancelled', 'soft_delete_payments', 'restore_payments'
    ]
    
    def mark_as_completed(self, request, queryset):
        count = queryset.update(status='completed')
        self.message_user(request, f'{count} payments marked as completed.')
    mark_as_completed.short_description = "Mark selected payments as completed"
    
    def mark_as_failed(self, request, queryset):
        count = queryset.update(status='failed')
        self.message_user(request, f'{count} payments marked as failed.')
    mark_as_failed.short_description = "Mark selected payments as failed"
    
    def mark_as_processing(self, request, queryset):
        count = queryset.update(status='processing')
        self.message_user(request, f'{count} payments marked as processing.')
    mark_as_processing.short_description = "Mark selected payments as processing"
    
    def mark_as_cancelled(self, request, queryset):
        count = queryset.update(status='cancelled')
        self.message_user(request, f'{count} payments marked as cancelled.')
    mark_as_cancelled.short_description = "Mark selected payments as cancelled"
    
    def soft_delete_payments(self, request, queryset):
        count = queryset.update(is_deleted=True)
        self.message_user(request, f'{count} payment logs were soft deleted.')
    soft_delete_payments.short_description = "Soft delete selected payment logs"
    
    def restore_payments(self, request, queryset):
        count = queryset.update(is_deleted=False)
        self.message_user(request, f'{count} payment logs were restored.')
    restore_payments.short_description = "Restore selected payment logs"
    
    def changelist_view(self, request, extra_context=None):
        # Add summary statistics to the changelist
        response = super().changelist_view(request, extra_context=extra_context)
        
        try:
            qs = response.context_data['cl'].queryset
            summary = {
                'total_payments': qs.count(),
                'total_amount': qs.aggregate(total=Sum('amount'))['total'] or 0,
                'completed_payments': qs.filter(status='completed').count(),
                'pending_payments': qs.filter(status='pending').count(),
                'failed_payments': qs.filter(status='failed').count(),
            }
            response.context_data['summary'] = summary
        except (AttributeError, KeyError):
            pass
            
        return response

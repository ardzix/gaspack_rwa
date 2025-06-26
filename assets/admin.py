from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Asset, Purchase


class PurchaseInline(admin.TabularInline):
    model = Purchase
    extra = 0
    readonly_fields = ('id', 'total_amount', 'created_at', 'updated_at')
    fields = ('user', 'slots_purchased', 'total_amount', 'payment_status', 'created_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False)


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'image_preview', 'total_slots', 'price_per_slot', 
        'total_value', 'slots_sold', 'availability_status',
        'is_deleted_display', 'created_at'
    )
    list_filter = ('is_deleted', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'total_value', 'slots_sold', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    inlines = [PurchaseInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'image')
        }),
        ('Financial Details', {
            'fields': ('total_slots', 'price_per_slot', 'total_value')
        }),
        ('Statistics', {
            'fields': ('slots_sold',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_deleted', 'created_at', 'updated_at')
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = 'Preview'
    
    def slots_sold(self, obj):
        sold = Purchase.objects.filter(
            asset=obj, 
            is_deleted=False, 
            payment_status='completed'
        ).aggregate(total=Sum('slots_purchased'))['total'] or 0
        return sold
    slots_sold.short_description = 'Slots Sold'
    
    def availability_status(self, obj):
        sold = self.slots_sold(obj)
        available = obj.total_slots - sold
        percentage = (sold / obj.total_slots) * 100 if obj.total_slots > 0 else 0
        
        if percentage >= 100:
            color = '#f44336'  # Red
            status = 'SOLD OUT'
        elif percentage >= 80:
            color = '#ff9800'  # Orange
            status = f'{available} left'
        else:
            color = '#4caf50'  # Green
            status = f'{available} available'
            
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span><br>'
            '<small>{}% sold</small>',
            color, status, percentage
        )
    availability_status.short_description = 'Availability'
    
    def is_deleted_display(self, obj):
        if obj.is_deleted:
            return format_html(
                '<span style="color: red; font-weight: bold;">🗑️ Deleted</span>'
            )
        return format_html(
            '<span style="color: green;">✅ Active</span>'
        )
    is_deleted_display.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            purchase_count=Count('purchase')
        )
    
    actions = ['soft_delete_assets', 'restore_assets', 'export_asset_report']
    
    def soft_delete_assets(self, request, queryset):
        count = queryset.update(is_deleted=True)
        self.message_user(request, f'{count} assets were soft deleted.')
    soft_delete_assets.short_description = "Soft delete selected assets"
    
    def restore_assets(self, request, queryset):
        count = queryset.update(is_deleted=False)
        self.message_user(request, f'{count} assets were restored.')
    restore_assets.short_description = "Restore selected assets"


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        'id_short', 'user_link', 'asset_link', 'slots_purchased', 
        'total_amount', 'payment_status_display', 'is_deleted_display', 'created_at'
    )
    list_filter = ('payment_status', 'is_deleted', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'asset__name', 'id')
    readonly_fields = ('id', 'total_amount', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Purchase Information', {
            'fields': ('id', 'user', 'asset', 'slots_purchased', 'total_amount')
        }),
        ('Payment Details', {
            'fields': ('payment_status',)
        }),
        ('Status & Timestamps', {
            'fields': ('is_deleted', 'created_at', 'updated_at')
        }),
    )
    
    def id_short(self, obj):
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'ID'
    
    def user_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    
    def asset_link(self, obj):
        url = reverse('admin:assets_asset_change', args=[obj.asset.id])
        return format_html('<a href="{}">{}</a>', url, obj.asset.name)
    asset_link.short_description = 'Asset'
    
    def payment_status_display(self, obj):
        colors = {
            'pending': '#ff9800',
            'completed': '#4caf50',
            'failed': '#f44336',
            'refunded': '#9c27b0'
        }
        color = colors.get(obj.payment_status, '#666')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_payment_status_display()
        )
    payment_status_display.short_description = 'Payment Status'
    
    def is_deleted_display(self, obj):
        if obj.is_deleted:
            return format_html(
                '<span style="color: red; font-weight: bold;">🗑️ Deleted</span>'
            )
        return format_html(
            '<span style="color: green;">✅ Active</span>'
        )
    is_deleted_display.short_description = 'Status'
    
    actions = ['mark_as_completed', 'mark_as_failed', 'soft_delete_purchases', 'restore_purchases']
    
    def mark_as_completed(self, request, queryset):
        count = queryset.update(payment_status='completed')
        self.message_user(request, f'{count} purchases marked as completed.')
    mark_as_completed.short_description = "Mark selected purchases as completed"
    
    def mark_as_failed(self, request, queryset):
        count = queryset.update(payment_status='failed')
        self.message_user(request, f'{count} purchases marked as failed.')
    mark_as_failed.short_description = "Mark selected purchases as failed"
    
    def soft_delete_purchases(self, request, queryset):
        count = queryset.update(is_deleted=True)
        self.message_user(request, f'{count} purchases were soft deleted.')
    soft_delete_purchases.short_description = "Soft delete selected purchases"
    
    def restore_purchases(self, request, queryset):
        count = queryset.update(is_deleted=False)
        self.message_user(request, f'{count} purchases were restored.')
    restore_purchases.short_description = "Restore selected purchases"

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import SimulatedNFT


@admin.register(SimulatedNFT)
class SimulatedNFTAdmin(admin.ModelAdmin):
    list_display = (
        'token_id_short', 'user_link', 'asset_link', 'ownership_percentage_display',
        'slots_owned', 'is_deleted_display', 'created_at'
    )
    list_filter = ('is_deleted', 'created_at', 'updated_at', 'asset')
    search_fields = ('token_id', 'user__username', 'user__email', 'asset__name')
    readonly_fields = ('id', 'token_id', 'ownership_percentage', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('NFT Information', {
            'fields': ('id', 'token_id', 'user', 'asset')
        }),
        ('Ownership Details', {
            'fields': ('slots_owned', 'ownership_percentage')
        }),
        ('Status & Timestamps', {
            'fields': ('is_deleted', 'created_at', 'updated_at')
        }),
    )
    
    def token_id_short(self, obj):
        return obj.token_id[:20] + '...' if len(obj.token_id) > 20 else obj.token_id
    token_id_short.short_description = 'Token ID'
    
    def user_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html(
            '<a href="{}" title="{}">{}</a>',
            url, obj.user.email, obj.user.username
        )
    user_link.short_description = 'Owner'
    
    def asset_link(self, obj):
        url = reverse('admin:assets_asset_change', args=[obj.asset.id])
        return format_html('<a href="{}">{}</a>', url, obj.asset.name)
    asset_link.short_description = 'Asset'
    
    def ownership_percentage_display(self, obj):
        percentage = float(obj.ownership_percentage)
        if percentage >= 50:
            color = '#4caf50'  # Green for majority ownership
            icon = '👑'
        elif percentage >= 25:
            color = '#ff9800'  # Orange for significant ownership
            icon = '💎'
        else:
            color = '#2196f3'  # Blue for regular ownership
            icon = '🎯'
            
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}%</span>',
            color, icon, percentage
        )
    ownership_percentage_display.short_description = 'Ownership %'
    
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
        return super().get_queryset(request).select_related('user', 'asset')
    
    actions = ['soft_delete_nfts', 'restore_nfts', 'recalculate_ownership']
    
    def soft_delete_nfts(self, request, queryset):
        count = queryset.update(is_deleted=True)
        self.message_user(request, f'{count} NFTs were soft deleted.')
    soft_delete_nfts.short_description = "Soft delete selected NFTs"
    
    def restore_nfts(self, request, queryset):
        count = queryset.update(is_deleted=False)
        self.message_user(request, f'{count} NFTs were restored.')
    restore_nfts.short_description = "Restore selected NFTs"
    
    def recalculate_ownership(self, request, queryset):
        count = 0
        for nft in queryset:
            old_percentage = nft.ownership_percentage
            nft.ownership_percentage = (nft.slots_owned / nft.asset.total_slots) * 100
            nft.save()
            count += 1
        self.message_user(request, f'{count} NFT ownership percentages recalculated.')
    recalculate_ownership.short_description = "Recalculate ownership percentages"
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ('user', 'asset')
        return self.readonly_fields

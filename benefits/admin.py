from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import BenefitRule, UserBenefitClaim


class UserBenefitClaimInline(admin.TabularInline):
    model = UserBenefitClaim
    extra = 0
    readonly_fields = ('id', 'claimed_at', 'processed_at', 'created_at', 'updated_at')
    fields = ('user', 'claim_status', 'claimed_at', 'processed_at', 'notes')
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False).select_related('user')


@admin.register(BenefitRule)
class BenefitRuleAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'asset_link', 'benefit_type_display', 'benefit_value',
        'min_nft_required', 'claims_count', 'is_active_display', 'is_deleted_display', 'created_at'
    )
    list_filter = ('benefit_type', 'is_active', 'is_deleted', 'created_at', 'updated_at', 'asset')
    search_fields = ('name', 'description', 'asset__name')
    readonly_fields = ('id', 'claims_count', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    inlines = [UserBenefitClaimInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'asset')
        }),
        ('Benefit Details', {
            'fields': ('benefit_type', 'benefit_value', 'min_nft_required')
        }),
        ('Statistics', {
            'fields': ('claims_count',),
            'classes': ('collapse',)
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'is_deleted', 'created_at', 'updated_at')
        }),
    )
    
    def asset_link(self, obj):
        url = reverse('admin:assets_asset_change', args=[obj.asset.id])
        return format_html('<a href="{}">{}</a>', url, obj.asset.name)
    asset_link.short_description = 'Asset'
    
    def benefit_type_display(self, obj):
        icons = {
            'cashback': '💰',
            'discount': '🏷️',
            'access': '🔑',
            'dividend': '📈',
            'other': '🎁'
        }
        colors = {
            'cashback': '#4caf50',
            'discount': '#ff9800',
            'access': '#2196f3',
            'dividend': '#9c27b0',
            'other': '#607d8b'
        }
        icon = icons.get(obj.benefit_type, '❓')
        color = colors.get(obj.benefit_type, '#666')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_benefit_type_display()
        )
    benefit_type_display.short_description = 'Benefit Type'
    
    def claims_count(self, obj):
        count = UserBenefitClaim.objects.filter(
            benefit_rule=obj, is_deleted=False
        ).count()
        return count
    claims_count.short_description = 'Total Claims'
    
    def is_active_display(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✅ Active</span>'
            )
        return format_html(
            '<span style="color: orange; font-weight: bold;">⏸️ Inactive</span>'
        )
    is_active_display.short_description = 'Active Status'
    
    def is_deleted_display(self, obj):
        if obj.is_deleted:
            return format_html(
                '<span style="color: red; font-weight: bold;">🗑️ Deleted</span>'
            )
        return format_html(
            '<span style="color: green;">✅ Available</span>'
        )
    is_deleted_display.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('asset').annotate(
            claim_count=Count('userbenefitclaim')
        )
    
    actions = ['activate_benefits', 'deactivate_benefits', 'soft_delete_benefits', 'restore_benefits']
    
    def activate_benefits(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} benefit rules were activated.')
    activate_benefits.short_description = "Activate selected benefit rules"
    
    def deactivate_benefits(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} benefit rules were deactivated.')
    deactivate_benefits.short_description = "Deactivate selected benefit rules"
    
    def soft_delete_benefits(self, request, queryset):
        count = queryset.update(is_deleted=True, is_active=False)
        self.message_user(request, f'{count} benefit rules were soft deleted.')
    soft_delete_benefits.short_description = "Soft delete selected benefit rules"
    
    def restore_benefits(self, request, queryset):
        count = queryset.update(is_deleted=False)
        self.message_user(request, f'{count} benefit rules were restored.')
    restore_benefits.short_description = "Restore selected benefit rules"


@admin.register(UserBenefitClaim)
class UserBenefitClaimAdmin(admin.ModelAdmin):
    list_display = (
        'id_short', 'user_link', 'benefit_rule_link', 'claim_status_display',
        'claimed_at', 'processed_at', 'is_deleted_display'
    )
    list_filter = ('claim_status', 'is_deleted', 'claimed_at', 'processed_at', 'benefit_rule__benefit_type')
    search_fields = ('user__username', 'user__email', 'benefit_rule__name', 'notes')
    readonly_fields = ('id', 'claimed_at', 'created_at', 'updated_at')
    ordering = ('-claimed_at',)
    
    fieldsets = (
        ('Claim Information', {
            'fields': ('id', 'user', 'benefit_rule', 'claim_status')
        }),
        ('Processing Details', {
            'fields': ('claimed_at', 'processed_at', 'notes')
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
        return format_html(
            '<a href="{}" title="{}">{}</a>',
            url, obj.user.email, obj.user.username
        )
    user_link.short_description = 'User'
    
    def benefit_rule_link(self, obj):
        url = reverse('admin:benefits_benefitrule_change', args=[obj.benefit_rule.id])
        return format_html('<a href="{}">{}</a>', url, obj.benefit_rule.name)
    benefit_rule_link.short_description = 'Benefit Rule'
    
    def claim_status_display(self, obj):
        colors = {
            'pending': '#ff9800',
            'approved': '#4caf50',
            'rejected': '#f44336',
            'processed': '#2196f3'
        }
        icons = {
            'pending': '⏳',
            'approved': '✅',
            'rejected': '❌',
            'processed': '🎯'
        }
        color = colors.get(obj.claim_status, '#666')
        icon = icons.get(obj.claim_status, '❓')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_claim_status_display()
        )
    claim_status_display.short_description = 'Claim Status'
    
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
        return super().get_queryset(request).select_related('user', 'benefit_rule', 'benefit_rule__asset')
    
    actions = [
        'approve_claims', 'reject_claims', 'mark_as_processed', 
        'soft_delete_claims', 'restore_claims'
    ]
    
    def approve_claims(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(claim_status='approved', processed_at=timezone.now())
        self.message_user(request, f'{count} claims were approved.')
    approve_claims.short_description = "Approve selected claims"
    
    def reject_claims(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(claim_status='rejected', processed_at=timezone.now())
        self.message_user(request, f'{count} claims were rejected.')
    reject_claims.short_description = "Reject selected claims"
    
    def mark_as_processed(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(claim_status='processed', processed_at=timezone.now())
        self.message_user(request, f'{count} claims were marked as processed.')
    mark_as_processed.short_description = "Mark selected claims as processed"
    
    def soft_delete_claims(self, request, queryset):
        count = queryset.update(is_deleted=True)
        self.message_user(request, f'{count} benefit claims were soft deleted.')
    soft_delete_claims.short_description = "Soft delete selected claims"
    
    def restore_claims(self, request, queryset):
        count = queryset.update(is_deleted=False)
        self.message_user(request, f'{count} benefit claims were restored.')
    restore_claims.short_description = "Restore selected claims"

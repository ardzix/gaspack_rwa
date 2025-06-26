from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name', 
        'is_active', 'is_staff', 'is_superuser', 'is_deleted_display',
        'date_joined', 'last_login'
    )
    list_filter = (
        'is_active', 'is_staff', 'is_superuser', 'is_deleted',
        'date_joined', 'last_login'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('id', 'date_joined', 'last_login')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('id', 'is_deleted'),
        }),
    )
    
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
        # Show all users including soft-deleted ones in admin
        return self.model.objects.all()
    
    actions = ['soft_delete_users', 'restore_users']
    
    def soft_delete_users(self, request, queryset):
        count = queryset.update(is_deleted=True, is_active=False)
        self.message_user(request, f'{count} users were soft deleted.')
    soft_delete_users.short_description = "Soft delete selected users"
    
    def restore_users(self, request, queryset):
        count = queryset.update(is_deleted=False, is_active=True)
        self.message_user(request, f'{count} users were restored.')
    restore_users.short_description = "Restore selected users"

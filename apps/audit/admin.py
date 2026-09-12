from django.contrib import admin
from .models import SecurityAuditLog


@admin.register(SecurityAuditLog)
class SecurityAuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'event_type', 'user', 'ip_address', 'path')
    list_filter = ('event_type', 'created_at')
    search_fields = ('user__username', 'ip_address', 'path')
    readonly_fields = ('user', 'event_type', 'ip_address', 'user_agent', 'path', 'details', 'created_at')

    def has_add_permission(self, request):
        # Audit log tidak boleh ditambahkan secara manual
        return False

    def has_change_permission(self, request, obj=None):
        # Audit log bersifat immutable (tidak boleh diedit)
        return False

    def has_delete_permission(self, request, obj=None):
        # Audit log tidak boleh dihapus dari admin panel
        return False

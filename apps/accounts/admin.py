from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'institution', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'institution')
    search_fields = ('username', 'email', 'institution')
    ordering = ('username',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Kontes Hacker', {'fields': ('role', 'phone_number', 'institution', 'last_login_ip')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role & Kontes Hacker', {'fields': ('role', 'phone_number', 'institution')}),
    )

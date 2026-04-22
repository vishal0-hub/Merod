from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ApiKey, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('email',)}),
    )


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'user__username', 'user__email')
    readonly_fields = ('key_prefix', 'encrypted_key', 'created_at', 'updated_at', 'last_used_at')

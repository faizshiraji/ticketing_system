from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Company, User


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "short_code", "is_active", "created_at")
    search_fields = ("name", "short_code")


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "company", "is_active")
    list_filter = ("role", "company", "is_active")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Support role", {"fields": ("role", "company", "phone")}),
    )

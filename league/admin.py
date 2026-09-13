from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class OGUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Associato", {"fields": ("nickname", "membership_number",)}),)

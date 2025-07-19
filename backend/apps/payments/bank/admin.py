# /apps/payments/payment_method/admin.py

from django.contrib import admin


class BankAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")

    def has_change_permission(self, request, obj=None):
        return False
from django.contrib import admin

from .bank.admin import BankAdmin
from .models import Bank, Payment, PaymentMethod
from .payment.admin import PaymentAdmin
from .payment_method.admin import PaymentMethodAdmin

admin.site.register(Bank, BankAdmin)
admin.site.register(PaymentMethod, PaymentMethodAdmin)
admin.site.register(Payment, PaymentAdmin)

# /apps/payments/payment_method/admin.py

from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

from .form import PaymentMethodAdminForm


class PaymentMethodAdmin(admin.ModelAdmin):
    """
    Administración personalizada para PaymentMethod con campos dinámicos
    que se muestran/ocultan según el tipo de método de pago seleccionado.
    """

    form = PaymentMethodAdminForm

    list_display = ("name", "method_type", "currency", "is_active")
    list_filter = ("method_type", "is_active")
    search_fields = ("name",)

    class Media:
        js = (
            "assets/js/vendor/inputmask.min.js",
            "assets/js/core/app-masks.js",
            "assets/js/payment_method_form.js",
        )

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """
        Sobrescribimos la vista de edición para añadir un mensaje de advertencia
        si el objeto está en uso.
        """
        # Obtenemos el objeto que se está editando.
        obj = self.get_object(request, object_id)

        # Si el objeto existe y está en uso, mostramos el mensaje.
        if obj and obj.is_in_use():
            messages.warning(
                request,
                _(
                    "This payment method is in use and its critical details cannot be modified. "
                    "Only the 'Account Nickname' and 'Is Active?' status can be changed."
                ),
            )

        # Llamamos al método original para que la vista se comporte normalmente.
        return super().change_view(request, object_id, form_url, extra_context)

    def get_fieldsets(self, request, obj=None):
        """
        Define los fieldsets dinámicamente, incluyendo todos los campos personalizados
        para que JavaScript pueda manejar su visibilidad.
        """
        fieldsets = [
            (
                None,
                {"fields": ("name", "method_type", "currency_display", "is_active")},
            ),
            (
                _("Account Configuration"),
                {
                    "fields": (
                        "custom_phone",
                        "custom_id_number",
                        "custom_bank",
                        "custom_account_number",
                        "custom_holder_name",
                        "custom_email",
                        "custom_pay_id",
                    ),
                    "description": _(
                        "Fill in the required details for the selected payment method below. "
                        "The system will show/hide fields automatically."
                    ),
                    "classes": ("dynamic-fields",),
                },
            ),
        ]
        return fieldsets

    def has_delete_permission(self, request, obj=None):
        """
        Impide que se muestre el botón de eliminar si el método de pago está en uso.
        """
        # Si el objeto existe y está en uso, no damos permiso para eliminar.
        if obj and obj.is_in_use():
            return False
        # En todos los demás casos, respetamos los permisos por defecto.
        return super().has_delete_permission(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        """
        Asegura que el formulario personalizado se use correctamente.
        """
        kwargs["form"] = self.form
        return super().get_form(request, obj, **kwargs)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    @admin.action(description=_("Delete selected payment methods"))
    def safe_delete_selected(self, request, queryset):
        """
        Acción de eliminación segura que verifica cada objeto antes de borrarlo.
        """
        deletable_objects = 0
        protected_objects = 0

        for obj in queryset:
            if obj.is_in_use():
                protected_objects += 1
            else:
                obj.delete()
                deletable_objects += 1

        if deletable_objects > 0:
            self.message_user(
                request,
                _(f"{deletable_objects} payment methods were successfully deleted."),
                messages.SUCCESS,
            )

        if protected_objects > 0:
            self.message_user(
                request,
                _(
                    f"{protected_objects} payment methods could not be deleted because they are in use."
                ),
                messages.WARNING,
            )

    actions = ["safe_delete_selected"]

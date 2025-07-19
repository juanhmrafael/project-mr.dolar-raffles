# auditing/admin/global_audit_log.py
from datetime import datetime

import simple_history
from django.contrib import admin
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class GlobalAuditLogAdmin(admin.ModelAdmin):
    actions = None

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def _apply_filters(self, history_queryset, request):
        """
        Aplica filtros avanzados a las entradas de historial usando consultas SQL optimizadas.

        Args:
            history_queryset: Queryset de entradas de historial
            request: Objeto de solicitud HTTP con parámetros GET

        Returns:
            Queryset filtrado
        """
        query = Q()

        # Filtro por fecha de inicio
        date_from = request.GET.get("date_from")
        if date_from:
            try:
                date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
                query &= Q(history_date__date__gte=date_from)
            except ValueError:
                pass

        # Filtro por fecha de fin
        date_to = request.GET.get("date_to")
        if date_to:
            try:
                date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
                query &= Q(history_date__date__lte=date_to)
            except ValueError:
                pass

        # Filtro por tipo de acción
        action_type = request.GET.get("action_type")
        if action_type in ["+", "~", "-"]:
            query &= Q(history_type=action_type)

        # Filtro por usuario
        user_email = request.GET.get("user_email")
        if user_email:
            query &= Q(history_user__email__icontains=user_email)

        return history_queryset.filter(query)

    def _calculate_statistics(self, history_list):
        """
        Calcula estadísticas de los cambios en memoria para evitar múltiples consultas.

        Args:
            history_list: Lista de entradas de historial

        Returns:
            Diccionario con estadísticas de cambios
        """
        stats = {
            "total_created": 0,
            "total_updated": 0,
            "total_deleted": 0,
        }
        for entry in history_list:
            if entry.history_type == "+":
                stats["total_created"] += 1
            elif entry.history_type == "~":
                stats["total_updated"] += 1
            elif entry.history_type == "-":
                stats["total_deleted"] += 1
        return stats

    def _get_field_changes(self, entry):
        """
        Obtiene los cambios de campo comparando con el registro anterior.

        Args:
            entry: Entrada de historial actual

        Returns:
            Lista de diccionarios con información de cambios
        """
        changes = []
        if entry.history_type == "~":
            prev_record = entry.prev_record
            if prev_record:
                delta = entry.diff_against(prev_record)
                for change in delta.changes:
                    field_verbose_name = _(change.field)
                    try:
                        field_obj = entry.instance._meta.get_field(change.field)
                        field_verbose_name = field_obj.verbose_name
                    except Exception:
                        pass
                    changes.append(
                        {
                            "field": field_verbose_name,
                            "old": self._format_field_value(change.old),
                            "new": self._format_field_value(change.new),
                        }
                    )
        return changes

    def _format_field_value(self, value):
        """
        Formatea los valores de campo para una mejor presentación.

        Args:
            value: Valor del campo a formatear

        Returns:
            String formateado del valor
        """
        if value is None:
            return "-"
        elif isinstance(value, bool):
            return _("Yes") if value else _("No")
        elif isinstance(value, (list, tuple)):
            return ", ".join(str(item) for item in value)
        elif len(str(value)) > 50:
            return str(value)[:47] + "..."
        else:
            return str(value)

    def _get_admin_url(self, entry):
        """
        Genera la URL del objeto en el admin de Django.

        Args:
            entry: Entrada de historial

        Returns:
            URL del admin o None si no es aplicable
        """
        try:
            if entry.history_type != "-" and entry.instance:
                return reverse(
                    f"admin:{entry.instance._meta.app_label}_{entry.instance._meta.model_name}_change",
                    args=[entry.instance.pk],
                )
        except Exception:
            pass
        return None

    def _get_user_admin_url(self, user):
        """
        Genera la URL del usuario en el admin de Django.

        Args:
            user: Instancia del usuario que realizó el cambio

        Returns:
            URL del admin del usuario o None si no está disponible
        """
        if not user:
            return None

        try:
            # Intentar generar la URL del usuario en el admin
            return reverse(
                f"admin:{user._meta.app_label}_{user._meta.model_name}_change",
                args=[user.pk],
            )
        except Exception:
            # Si falla, podría ser que el modelo User no esté registrado en el admin
            # o que no tengamos permisos para acceder a él
            pass
        return None

    def changelist_view(self, request, extra_context=None):
        """
        Vista principal del log de auditoría con consultas optimizadas y filtros avanzados.

        Args:
            request: Objeto de solicitud HTTP
            extra_context: Contexto adicional opcional

        Returns:
            Respuesta HTTP renderizada
        """
        all_registered_models = simple_history.models.registered_models

        # CORRECCIÓN CLAVE: Crear un mapeo bidireccional entre claves del diccionario
        # y etiquetas de modelo para asegurar consistencia
        model_choices = []
        model_key_mapping = {}  # Mapeo: label_lower -> clave_del_diccionario

        for model_key, model_class in all_registered_models.items():
            label_lower = model_class._meta.label_lower
            verbose_name = model_class._meta.verbose_name

            model_choices.append(
                {
                    "label": label_lower,
                    "verbose_name": verbose_name,
                }
            )

            # Crear mapeo para la búsqueda inversa
            model_key_mapping[label_lower] = model_key

        # Ordenar por nombre legible
        model_choices.sort(key=lambda x: x["verbose_name"])

        history_querysets = []
        selected_model_label = request.GET.get("model_name")

        # LÓGICA DE FILTRADO CORREGIDA
        models_to_query = []
        if selected_model_label:
            # Usar el mapeo para obtener la clave correcta del diccionario
            model_key = model_key_mapping.get(selected_model_label)
            if model_key:
                model_class = all_registered_models.get(model_key)
                if model_class:
                    models_to_query = [model_class]
            # Si no se encuentra el modelo, models_to_query queda vacío (comportamiento correcto)
        else:
            # Si no se selecciona ningún modelo, consultamos todos
            models_to_query = all_registered_models.values()

        # Construir querysets para los modelos seleccionados
        for model in models_to_query:
            base_queryset = model.history.select_related("history_user").order_by(
                "-history_date"
            )
            filtered_queryset = self._apply_filters(base_queryset, request)
            history_querysets.append(filtered_queryset)

        # Combinar y ordenar resultados (limitado para rendimiento)
        combined_history = sorted(
            (item for queryset in history_querysets for item in queryset[:1000]),
            key=lambda x: x.history_date,
            reverse=True,
        )
        history_list = combined_history[:2000]

        # Procesar entradas de historial para la vista
        processed_history = []
        for entry in history_list:
            verbose_name = ""
            try:
                verbose_name = entry.instance._meta.verbose_name
            except AttributeError:
                try:
                    verbose_name = entry.history_object._meta.verbose_name
                except AttributeError:
                    verbose_name = _("Unknown Model")

            processed_history.append(
                {
                    "entry": entry,
                    "changes": self._get_field_changes(entry),
                    "admin_url": self._get_admin_url(entry),
                    "user_admin_url": self._get_user_admin_url(entry.history_user),
                    "verbose_name": verbose_name,
                }
            )

        # Configurar paginación
        paginator = Paginator(processed_history, 20)
        page_number = request.GET.get("page")
        history_page = paginator.get_page(page_number)

        # Calcular estadísticas solo para la página actual
        stats = self._calculate_statistics(
            [item["entry"] for item in history_page.object_list]
        )

        # Preparar contexto para el template
        context = {
            **self.admin_site.each_context(request),
            "title": _("Audit Log"),
            "history_page": history_page,
            "opts": self.model._meta,
            "total_created": stats["total_created"],
            "total_updated": stats["total_updated"],
            "total_deleted": stats["total_deleted"],
            "model_choices": model_choices,
            "has_filters": any(request.GET.values()),
        }

        return render(request, "admin/global_history_log.html", context)

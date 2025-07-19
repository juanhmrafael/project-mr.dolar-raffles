from django.conf import settings

# --- URLS DE INTERNACIONALIZACIÓN (I18N) ---
# Propósito: Proporcionar las vistas y URLs necesarias para que Django
# gestione el cambio de idioma. Esto es un REQUISITO para que la opción
# Documentación de Django: https://docs.djangoproject.com/en/5.0/topics/i18n/translation/#the-set-language-redirect-view
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

from auditing.sites import audit_admin_site

# Las URLs que deben ser traducidas (casi todas las que ve el usuario)
# Por ahora, solo el admin.
urlpatterns = i18n_patterns(
    path("admin/", admin.site.urls),
    path("audit-admin/", audit_admin_site.urls),
    prefix_default_language=False,
)

# Las URLs que NO deben tener prefijo de idioma
# (como la API o el health check)
urlpatterns += [
    # Incluimos la vista 'set_language' que faltaba.
    # Django la buscará dentro de este include.
    path("i18n/", include("django.conf.urls.i18n")),
    path("select2/", include("django_select2.urls")),
    path("", include("payments.urls", namespace="payments")),
    path("", include("raffles.urls", namespace="raffles")),
    path("", include("participants.urls", namespace="participants")),
    # El resto de tus URLs no-traducibles irían aquí.
    # path("api/v1/", include("your_api.urls")),
]

if settings.DEBUG:
    from django.conf import settings
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += [
        # La URL `__debug__/` es el prefijo estándar para las rutas de la toolbar.
        # `include('debug_toolbar.urls')` delega el manejo de estas rutas
        # a la propia librería, creando una configuración limpia y mantenible.
        path("__debug__/", include("debug_toolbar.urls")),
    ]

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Configuración básica del admin - método más simple y efectivo
admin.site.site_header = _(
    "Mr. Dolar's Management System"
)  # Aparece en la parte superior

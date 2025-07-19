# users/models.py
import hashlib

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    Group,
    PermissionsMixin,
)
from django.core.exceptions import PermissionDenied
from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from encrypted_model_fields.fields import EncryptedCharField
from simple_history.models import HistoricalRecords
from utils.validators import validate_natural_person_id

# --- CONSTANTE DE SEGURIDAD ---
SYSTEM_USER_EMAIL = "system@internal.local"


class CustomUserManager(BaseUserManager):
    """
    Manager personalizado para manejar la creación de usuarios y superusuarios.
    """

    def _create_user(self, email, password, **extra_fields):
        """
        Método privado para crear y guardar un usuario con un email normalizado.
        """
        if not email:
            raise ValueError(_("The Email field must be set"))
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_chief_auditor", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True"))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True"))
        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuario personalizado con protección para el usuario del sistema,
    internacionalización y campo de avatar.
    """

    # --- Campos de Identidad ---
    email = models.CharField(
        _("email address"),
        max_length=255,
        unique=True,
        help_text=_("Required. Will be stored in lowercase."),
    )
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)

    # --- Campo Sensible (PII) ---
    identification_number = EncryptedCharField(
        _("identification number"),
        max_length=20,
        unique=True,
        db_index=True,
        validators=[validate_natural_person_id],
        help_text=format_html(
            "{}<br><b>V</b>: Venezolano | <b>E</b>: Extranjero | <b>P</b>: Pasaporte",
            _(
                "Format: L-NNNNNNNN (e.g., V-12345678). It will be formatted automatically."
            ),
        ),
        error_messages={
            "unique": _("A user with that identification number already exists."),
        },
    )

    # --- CAMPO DE HASH PARA BÚSQUEDA ---
    identification_number_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        editable=False,
        null=True,
        blank=True,
    )

    # --- Campos de Estado y Permisos ---
    avatar = models.ImageField(
        _("avatar"),
        upload_to="avatars/",
        null=True,
        blank=True,
        help_text=_("User profile picture"),
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    is_chief_auditor = models.BooleanField(
        _("chief auditor status"),
        default=False,
        help_text=_(
            "Designates that this user has access to the audit management panel."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), auto_now_add=True)

    objects = CustomUserManager()
    history = HistoricalRecords()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "identification_number"]

    class Meta:
        """
        Metadatos para el modelo CustomUser.
        """

        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["email"]

    def __str__(self):
        return self.get_full_name() or self.email

    def get_full_name(self):
        """
        Retorna el nombre completo del usuario.
        """
        return f"{self.first_name} {self.last_name}".strip()

    def clean(self):
        """
        Normaliza el email a minúsculas antes de la validación.
        """
        super().clean()
        self.email = self.email.lower()

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para impedir la modificación del usuario del sistema.
        """
        if self.pk is not None and self.email == SYSTEM_USER_EMAIL:
            raise PermissionDenied(
                _(
                    "The system user ({email}) is read-only and cannot be modified."
                ).format(email=SYSTEM_USER_EMAIL)
            )
        if self.identification_number:
            self.identification_number_hash = hashlib.sha256(
                self.identification_number.encode("utf-8")
            ).hexdigest()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Sobrescribe el método delete para impedir la eliminación del usuario del sistema.
        """
        if self.email == SYSTEM_USER_EMAIL:
            raise PermissionDenied(
                _("The system user ({email}) cannot be deleted.").format(
                    email=SYSTEM_USER_EMAIL
                )
            )
        super().delete(*args, **kwargs)

    def has_perm(self, perm, obj=None):
        """
        Verifica si el usuario tiene un permiso específico.

        Args:
            perm (str): El permiso a verificar en formato 'app_label.permission_codename'
            obj: El objeto específico (para permisos a nivel de objeto)

        Returns:
            bool: True si el usuario tiene el permiso, False en caso contrario
        """
        # Los superusuarios tienen todos los permisos
        if self.is_superuser:
            return True

        # Los usuarios inactivos no tienen permisos
        if not self.is_active:
            return False

        # Verificar permisos específicos de auditoría
        if self.is_chief_auditor:
            # Definir qué permisos específicos puede tener el auditor jefe
            audit_permissions = [
                "audit.view_auditlog",
                "audit.add_auditlog",
                "audit.change_auditlog",
                "audit.delete_auditlog",
                # Agregar más permisos específicos de auditoría aquí
            ]

            # Si el permiso solicitado está en la lista de permisos de auditoría
            if perm in audit_permissions:
                return True

            # También verificar por app_label para dar acceso completo al módulo de auditoría
            if perm.startswith("audit."):
                return True

        # Usar el backend de permisos estándar para otros casos
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        """
        Verifica si el usuario tiene permisos para ver el módulo/app especificado.

        Args:
            app_label (str): El nombre de la aplicación Django

        Returns:
            bool: True si el usuario puede acceder al módulo, False en caso contrario
        """
        # Los superusuarios tienen acceso a todos los módulos
        if self.is_superuser:
            return True

        # Los usuarios inactivos no tienen acceso a módulos
        if not self.is_active:
            return False

        # Los auditores jefe tienen acceso al módulo de auditoría
        if self.is_chief_auditor and app_label == "audit":
            return True

        # Usar el backend de permisos estándar para otros casos
        return super().has_module_perms(app_label)


class CustomGroup(Group):
    """
    Proxy model para extender el modelo Group de Django con historial.
    """

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")

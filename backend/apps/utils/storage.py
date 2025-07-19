# backend/apps/utils/storage.py
"""
Funciones de utilidad para generar rutas de almacenamiento dinámicas y organizadas.

Este módulo centraliza la lógica para nombrar archivos subidos, asegurando que
los nombres sean únicos, legibles y estén estructurados en directorios basados
en el contexto del modelo, como la rifa a la que pertenecen.
"""

import os
from datetime import datetime
from django.utils.text import slugify


def get_image_upload_path(instance, filename: str, prefix: str) -> str:
    """
    Genera una ruta de subida única y organizada para las imágenes.

    La estructura de la ruta es: `raffles/{raffle_slug}/{prefix}/{pk}_{timestamp}_{filename}`.
    Utiliza el 'slug' de la rifa para agrupar todos los archivos relacionados.
    Si el 'pk' de la instancia aún no existe (en la creación), se usa 'new'.

    Args:
        instance: La instancia del modelo que se está guardando.
        filename (str): El nombre original del archivo.
        prefix (str): Un prefijo para categorizar la imagen (ej: 'prize', 'winner', 'banner').

    Returns:
        str: La ruta de archivo relativa y única.
    """
    # Obtiene el slug de la rifa de manera segura.
    if hasattr(instance, "raffle"):
        raffle_slug = instance.raffle.slug
    else:
        raffle_slug = instance.slug

    # ✅ CORRECCIÓN: Separamos el nombre del archivo y la extensión ANTES de slugify.
    # os.path.splitext es la forma más segura de hacer esto.
    original_filename, ext = os.path.splitext(filename)
    # Nos aseguramos de que la extensión esté en minúsculas y no tenga el punto inicial.
    ext = ext.lower().lstrip(".")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Construimos el nombre base del archivo que queremos slugificar.
    base_filename = f"{prefix}_{instance.pk or 'new'}_{timestamp}"

    # Slugificamos SOLO el nombre base.
    slugified_filename = slugify(base_filename)

    # Construimos el nombre final del archivo, añadiendo la extensión al final.
    new_filename = f"{slugified_filename}.{ext}"

    # Retorna la ruta completa y organizada.
    return os.path.join(
        "raffles",
        raffle_slug,
        prefix,
        new_filename,
    )


# --- Funciones parciales para mayor conveniencia en los modelos ---


def raffle_banner_path(instance, filename: str) -> str:
    """Función parcial para la imagen principal (banner) de una rifa."""
    return get_image_upload_path(instance, filename, prefix="banner")


def prize_image_path(instance, filename: str) -> str:
    """Función parcial para la imagen promocional de un premio."""
    return get_image_upload_path(instance, filename, prefix="prize")


def winner_image_path(instance, filename: str) -> str:
    """Función parcial para la foto del ganador con su premio."""
    return get_image_upload_path(instance, filename, prefix="winner")

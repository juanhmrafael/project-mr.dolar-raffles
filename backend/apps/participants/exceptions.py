# backend/apps/participants/exceptions.py
"""Excepciones personalizadas para la aplicación de participantes."""


class ParticipationException(Exception):
    """Clase base para excepciones de participación."""

    pass


class RaffleNotAvailableError(ParticipationException):
    """Lanzada cuando se intenta participar en una rifa no disponible."""

    pass


class NotEnoughTicketsError(ParticipationException):
    """Lanzada cuando no hay suficientes tickets disponibles."""

    pass

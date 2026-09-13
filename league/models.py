"""
Modelli dell'app `league`.

Fase 1 — [TU] modello utente personalizzato.
    Requisiti:
      - classe `User` che estende `django.contrib.auth.models.AbstractUser`
      - campo `nickname`: testo, max 30 caratteri, opzionale (blank=True), mostrato in classifica
      - `__str__` che restituisce il nickname se presente, altrimenti lo username
    Il nome della classe DEVE essere `User` perché settings.AUTH_USER_MODEL = "league.User".

Fase 2 — Season, Tournament, Match, MatchPlayer (vedi docs/plan.md).
"""

from django.db import models

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
from django.contrib.auth.models import AbstractUser

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db.models.constraints import UniqueConstraint


class User(AbstractUser):
    nickname = models.CharField(max_length=30, blank=True)
    membership_number = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.nickname if self.nickname else self.username


class Season(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def clean(self):
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError(
                    "La data di inizio deve essere precedente alla data di fine."
                )

    def __str__(self):
        return self.name


class Tournament(models.Model):
    """Evento BRACKET one-day occasionale. Le sfide libere di stagione NON passano
    da qui: hanno Match.season diretto e Match.tournament=None. Niente punti W/L:
    il ranking è ELO (services/standings.py), un bracket si vince per eliminazione."""

    class Kind(models.TextChoices):
        REGULAR = "REGULAR", "Regular"
        BRACKET = "BRACKET", "Bracket"

    name = models.CharField(max_length=100)
    season = models.ForeignKey(
        Season, on_delete=models.CASCADE, related_name="tournaments"
    )
    kind = models.CharField(max_length=10, choices=Kind.choices)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.season} · {self.name} ({self.get_kind_display()})"

    class Meta:
        ordering = ["season", "name"]


class Match(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "IN_PROGRESS", "In corso"
        PENDING = "PENDING", "In attesa"
        CONFIRMED = "CONFIRMED", "Confermato"
        REJECTED = "REJECTED", "Rifiutato"

    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="matches")
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="matches",
        null=True,
        blank=True,
        help_text="Valorizzato solo se il match fa parte di un evento BRACKET.",
    )
    played_at = models.DateTimeField()
    score_a = models.PositiveSmallIntegerField(validators=[MinValueValidator(0)])
    score_b = models.PositiveSmallIntegerField(validators=[MinValueValidator(0)])
    rounds = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.PENDING
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="matches_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def clean(self):
        if self.score_a is not None and self.score_b is not None:
            if self.score_a == self.score_b:
                raise ValidationError(
                    "I punteggi non possono essere uguali. Deve esserci un vincitore."
                )
        if self.tournament_id and self.tournament.season_id != self.season_id:
            raise ValidationError(
                "Il torneo del match deve appartenere alla stessa stagione del match."
            )

    class Meta:
        ordering = ["-played_at"]

    def __str__(self):
        return f"{self.season} - {self.played_at.strftime('%Y-%m-%d %H:%M')} - A: {self.score_a} - B: {self.score_b}"


class MatchPlayer(models.Model):
    class Side(models.TextChoices):
        TEAM_A = "Team A"
        TEAM_B = "Team B"

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="players")
    player = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="match_users"
    )
    side = models.CharField(choices=Side.choices, max_length=10)
    confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.player} - {self.match}"

    class Meta:
        constraints = [
            UniqueConstraint(fields=["match", "player"], name="unique_match_player")
        ]

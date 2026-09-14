from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Season, Tournament, User, Match, MatchPlayer


@admin.register(User)
class OGUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Associato",
            {
                "fields": (
                    "nickname",
                    "membership_number",
                )
            },
        ),
    )


class TournamentInline(admin.TabularInline):
    model = Tournament
    list_display = ("name", "season", "kind")
    search_fields = ("name",)


class MatchSeasonInline(admin.TabularInline):
    """Match di una Season: la maggior parte (sfide libere, tournament=None)."""

    model = Match
    fk_name = "season"
    list_display = (
        "played_at",
        "tournament",
        "score_a",
        "score_b",
        "rounds",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("status", "tournament")


class MatchTournamentInline(admin.TabularInline):
    """Match di un evento BRACKET."""

    model = Match
    fk_name = "tournament"
    list_display = (
        "played_at",
        "score_a",
        "score_b",
        "rounds",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("status",)


class MatchPlayerInline(admin.TabularInline):
    model = MatchPlayer
    list_display = ("match", "player", "side", "confirmed", "confirmed_at")
    list_filter = (
        "match__season",
        "side",
        "confirmed",
    )
    search_fields = ("match__season__name", "player__username", "player__nickname")


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    inlines = [TournamentInline, MatchSeasonInline]


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ("name", "season", "kind", "is_active")
    list_filter = ("season", "kind", "is_active")
    search_fields = ("name",)
    inlines = [MatchTournamentInline]


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        "season",
        "tournament",
        "played_at",
        "score_a",
        "score_b",
        "rounds",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("season", "tournament", "status")
    search_fields = ("season__name",)
    inlines = [MatchPlayerInline]


@admin.register(MatchPlayer)
class MatchPlayerAdmin(admin.ModelAdmin):
    list_display = ("match", "player", "side", "confirmed", "confirmed_at")
    list_filter = (
        "match__season",
        "side",
        "confirmed",
    )
    search_fields = ("match__season__name", "player__username", "player__nickname")

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


class SeasonInline(admin.TabularInline):
    model = Season
    list_display = ("name", "start_date", "end_date")
    search_fields = ("name",)


class TournamentInline(admin.TabularInline):
    model = Tournament
    list_display = ("name", "season", "kind", "points_per_win", "points_per_loss")
    list_filter = ("season", "kind")
    search_fields = ("name",)


class MatchInline(admin.TabularInline):
    model = Match
    list_display = (
        "tournament",
        "played_at",
        "score_a",
        "score_b",
        "rounds",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("tournament__season", "tournament", "status")
    search_fields = ("tournament__name",)


class MatchPlayerInline(admin.TabularInline):
    model = MatchPlayer
    list_display = ("match", "player", "side", "confirmed", "confirmed_at")
    list_filter = (
        "match__tournament__season",
        "match__tournament",
        "side",
        "confirmed",
    )
    search_fields = ("match__tournament__name", "player__username", "player__nickname")


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    inlines = [TournamentInline]


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "season",
        "kind",
        "points_per_win",
        "points_per_loss",
        "is_active",
    )
    list_filter = ("season", "kind", "is_active")
    search_fields = ("name",)
    inlines = [MatchInline]


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        "tournament",
        "played_at",
        "score_a",
        "score_b",
        "rounds",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("tournament__season", "tournament", "status")
    search_fields = ("tournament__name",)
    inlines = [MatchPlayerInline]


@admin.register(MatchPlayer)
class MatchPlayerAdmin(admin.ModelAdmin):
    list_display = ("match", "player", "side", "confirmed", "confirmed_at")
    list_filter = (
        "match__tournament__season",
        "match__tournament",
        "side",
        "confirmed",
    )
    search_fields = ("match__tournament__name", "player__username", "player__nickname")

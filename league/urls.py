"""
Router DRF: registra un ViewSet e genera automaticamente le URL standard
(list/create/retrieve/update/delete). `basename` serve solo se `queryset` nel
ViewSet non basta a DRF per dedurre il nome delle URL — qui non servirebbe
(Season ha già un queryset esplicito), lo mettiamo comunque per essere
espliciti man mano che si aggiungono ViewSet.
"""

from rest_framework.routers import DefaultRouter

from .views import SeasonViewSet

router = DefaultRouter()
router.register("seasons", SeasonViewSet, basename="season")

# TODO tuo: registra qui TournamentViewSet, MatchViewSet quando li scrivi.
# router.register("tournaments", TournamentViewSet, basename="tournament")
# router.register("matches", MatchViewSet, basename="match")

# TODO tuo: aggiungi gli endpoint ranking (non passano dal router, non sono
# ViewSet legati a un modello) con path() diretto, es:
# from django.urls import path
# from .views import elo_ranking_view, scoring_averages_view
# urlpatterns = router.urls + [
#     path("ranking/elo/", elo_ranking_view),
#     path("ranking/scoring/", scoring_averages_view),
# ]

urlpatterns = router.urls

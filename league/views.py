"""
ViewSet DRF. Un ModelViewSet raggruppa list/retrieve/create/update/delete per un
modello in UNA classe; il router (league/urls.py) genera le URL automaticamente
(GET/POST /api/seasons/, GET/PUT/DELETE /api/seasons/{id}/) — non scrivi path()
a mano per ognuna, come faresti con function-based view.

Fase 4 — [IO] esempio completo per Season. [TU] Tournament/Match (con
create() custom per i players annidati), azioni confirm/reject, endpoint
ranking ELO/PPR-DPR.
"""

from rest_framework import viewsets

from .models import Season
from .serializers import SeasonSerializer


class SeasonViewSet(viewsets.ModelViewSet):
    # queryset + serializer_class sono i due attributi minimi che un
    # ModelViewSet richiede: da dove leggere i dati, come serializzarli.
    # `.all()` qui è ok (poche Season, admin-only in pratica); per Match, con
    # potenzialmente molte righe, ricorda `select_related`/`prefetch_related`
    # per evitare N+1 query (visto in Fase 2 con l'admin inline).
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    # Permessi: eredita IsAuthenticated dal default in REST_FRAMEWORK
    # (settings.py) — nessun utente anonimo può leggere le stagioni.


# TODO tuo — TournamentViewSet: come SeasonViewSet, ancora più semplice
# (sola lettura per ora, valuta ReadOnlyModelViewSet invece di ModelViewSet:
# https://www.django-rest-framework.org/api-guide/viewsets/#readonlymodelviewset).


# TODO tuo — MatchViewSet:
#   - queryset filtrato per ?season= (leggi request.query_params.get("season")
#     in get_queryset(self), non in un attributo statico)
#   - perform_create(self, serializer): imposta created_by=self.request.user
#     prima di salvare (il serializer NON deve accettarlo dal client)
#   - @action(detail=True, methods=["post"]) per confirm/reject — vedi
#     https://www.django-rest-framework.org/api-guide/viewsets/#marking-extra-actions-for-routing
#   - permissions.py con IsParticipant: solo chi ha un MatchPlayer su quel
#     match può confermare/rifiutare


# TODO tuo — endpoint ranking: non serve un ViewSet (non c'è un modello dietro,
# elo_ranking()/scoring_averages() sono funzioni pure). Una APIView o una
# @api_view semplice che chiama il service e restituisce Response(...) basta.

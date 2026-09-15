"""
Serializer DRF. Un serializer converte istanze di modello <-> JSON, e valida i
dati in ingresso (come un ModelForm, ma per API invece che per HTML).

Fase 4 — [IO] esempio completo per Season (sola lettura, nessuna relazione
annidata). [TU] Tournament/Match/MatchPlayer, inclusa la validazione custom
di Match (players annidati, punteggi).
"""


from rest_framework import serializers

from .models import MatchPlayer, Season, Tournament, Match


class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        # Elenco esplicito dei campi esposti in JSON: mai "__all__", per non
        # esporre per sbaglio un campo nuovo aggiunto in futuro senza deciderlo.
        fields = ["id", "name", "start_date", "end_date", "is_active"]


# TournamentSerializer, semplice come SeasonSerializer (nessuna
# relazione annidata da scrivere, solo lettura per ora).
class TournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = ["id", "name", "season", "start_date", "end_date"]


# TODO tuo — MatchSerializer: qui la parte interessante.
# `players` è annidato: in POST arriva come [{"player": <id>, "side": "Team A"}, ...],
# NON è un campo diretto di Match (è un related MatchPlayer separato). Serve:
#   1. un MatchPlayerSerializer minimale (player, side) usato come campo annidato
#      (many=True) dentro MatchSerializer — sola lettura per iniziare, poi vedi
#      `create()` custom per gestire la scrittura annidata (DRF non lo fa da solo).
#   2. `create(self, validated_data)` override: estrai `players` da validated_data
#      (va tolto con .pop() PRIMA di Match.objects.create(**validated_data), altrimenti
#      Match non sa cosa farsene), crea il Match, poi crea i MatchPlayer collegati.
#   3. `created_by` va impostato nella view (request.user), non nel serializer —
#      il client non deve poterlo scegliere lui.

class MatchPlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchPlayer
        fields = ["player", "side"]  # solo i campi che vogliamo esporre in JSON
        
class MatchSerializer(serializers.ModelSerializer):
    players = MatchPlayerSerializer(many=True)  # annidato, lettura e scrittura

    class Meta:
        model = Match
        fields = ["id", "tournament", "scheduled_at", "players", "created_by"]
        read_only_fields = ["created_by"]  # il client non può impostarlo

    def create(self, validated_data):
        players_data = validated_data.pop("players")  # estrai i players annidati
        match = Match.objects.create(**validated_data)  # crea il Match
        for player_data in players_data:
            MatchPlayer.objects.create(match=match, **player_data)  # crea i MatchPlayer
        return match

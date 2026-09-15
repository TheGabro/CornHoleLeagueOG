from django.test import TestCase

from league.models import Season, Match, MatchPlayer, User
from league.services.standings import elo_ranking, INITIAL_RATING


class EloRankingTests(TestCase):
    def setUp(self):
        self.season = Season.objects.create(
            name="2026", start_date="2026-01-01", end_date="2026-12-31"
        )
        self.alice = User.objects.create_user(username="alice")
        self.bob = User.objects.create_user(username="bob")
        self.carol = User.objects.create_user(username="carol")
        self.dave = User.objects.create_user(username="dave")

    def test_no_matches_returns_empty_list(self):
        # nessun Match creato in questo test -> elo_ranking() deve
        # tornare una lista vuota.
        self.assertEqual(elo_ranking(), [])

    def test_chronological_order_matters(self):
        # crea 2 Match CONFIRMED con `played_at` diversi, ma CHIAMA
        # .create() nell'ordine INVERSO rispetto a played_at (prima il più
        # recente, poi il più vecchio). Se elo_ranking() ordina davvero per
        # played_at (non per ordine di creazione/id), il risultato finale deve
        # essere identico a come se li avessi creati in ordine cronologico.
        match_recent = Match.objects.create(
            season=self.season,
            played_at="2026-01-02 10:00:00",
            score_a=10,
            score_b=5,
            rounds=3,
            status=Match.Status.CONFIRMED,
        )
        MatchPlayer.objects.create(
            match=match_recent, player=self.alice, side=MatchPlayer.Side.TEAM_A
        )
        MatchPlayer.objects.create(
            match=match_recent, player=self.bob, side=MatchPlayer.Side.TEAM_B
        )

        match_oldest = Match.objects.create(
            season=self.season,
            played_at="2026-01-01 10:00:00",
            score_a=5,
            score_b=10,
            rounds=2,
            status=Match.Status.CONFIRMED,
        )

        MatchPlayer.objects.create(
            match=match_oldest, player=self.alice, side=MatchPlayer.Side.TEAM_A
        )
        MatchPlayer.objects.create(
            match=match_oldest, player=self.bob, side=MatchPlayer.Side.TEAM_B
        )

        elo = {row["player"]: row["rating"] for row in elo_ranking()}

        self.assertGreater(elo[self.alice], INITIAL_RATING)
        self.assertLess(elo[self.bob], INITIAL_RATING)

    def test_doubles_team_members_get_same_delta(self):

        # un Match 2v2 (2 MatchPlayer per side). Dopo elo_ranking(),
        # verifica che i 2 membri della squadra vincente abbiano guadagnato lo
        # STESSO numero di punti rispetto a INITIAL_RATING (stesso delta), e
        # idem per i 2 della squadra perdente (stesso delta negativo).

        match_recent = Match.objects.create(
            season=self.season,
            played_at="2026-01-02 10:00:00",
            score_a=10,
            score_b=5,
            rounds=3,
            status=Match.Status.CONFIRMED,
        )
        MatchPlayer.objects.create(
            match=match_recent, player=self.alice, side=MatchPlayer.Side.TEAM_A
        )
        MatchPlayer.objects.create(
            match=match_recent, player=self.bob, side=MatchPlayer.Side.TEAM_A
        )
        MatchPlayer.objects.create(
            match=match_recent, player=self.carol, side=MatchPlayer.Side.TEAM_B
        )
        MatchPlayer.objects.create(
            match=match_recent, player=self.dave, side=MatchPlayer.Side.TEAM_B
        )

        elo = {row["player"]: row["rating"] for row in elo_ranking()}

        self.assertEqual(elo[self.alice], elo[self.bob])
        self.assertEqual(elo[self.carol], elo[self.dave])

    def test_non_confirmed_match_does_not_affect_ranking(self):

        # crea un Match con status PENDING o REJECTED (non CONFIRMED).
        # elo_ranking() deve ignorarlo: chi ha giocato solo quel match resta a
        # INITIAL_RATING (o non compare affatto, decidi tu e verificalo).

        match_recent = Match.objects.create(
            season=self.season,
            played_at="2026-01-02 10:00:00",
            score_a=10,
            score_b=5,
            rounds=3,
            status=Match.Status.CONFIRMED,
        )
        MatchPlayer.objects.create(
            match=match_recent, player=self.alice, side=MatchPlayer.Side.TEAM_A
        )
        MatchPlayer.objects.create(
            match=match_recent, player=self.bob, side=MatchPlayer.Side.TEAM_B
        )

        match_oldest = Match.objects.create(
            season=self.season,
            played_at="2026-01-01 10:00:00",
            score_a=5,
            score_b=10,
            rounds=2,
            status=Match.Status.PENDING,
        )

        MatchPlayer.objects.create(
            match=match_oldest, player=self.carol, side=MatchPlayer.Side.TEAM_A
        )
        MatchPlayer.objects.create(
            match=match_oldest, player=self.dave, side=MatchPlayer.Side.TEAM_B
        )
        
        elo = {row["player"]: row["rating"] for row in elo_ranking()}
        
        self.assertNotIn(self.carol, elo)
        self.assertNotIn(self.dave, elo)

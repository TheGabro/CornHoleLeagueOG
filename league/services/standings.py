from league.models import Match, MatchPlayer

INITIAL_RATING = 1000
K_FACTOR = 32


def elo_ranking():
    """
    Ranking ELO globale per giocatore. Rigioca TUTTI i Match CONFIRMED (singolo
    e doppio insieme, con o senza tournament) in ordine cronologico, partendo da
    INITIAL_RATING. Doppio: rating squadra = media dei 2 membri, stesso delta
    applicato a entrambi.

    Ritorna lista di dict {"player": User, "rating": int}, ordinata rating desc
    (poi nickname per stabilità in caso di parità).
    """
    ratings = {}  # player_id -> rating corrente
    players = {}  # player_id -> istanza User (per costruire il ritorno finale)

    matches = (
        Match.objects.filter(status=Match.Status.CONFIRMED)
        .order_by("played_at", "id")
        .prefetch_related("players__player")
    )

    for match in matches:
        team_a = [
            mp.player for mp in match.players.all()
            if mp.side == MatchPlayer.Side.TEAM_A
        ]
        team_b = [
            mp.player for mp in match.players.all()
            if mp.side == MatchPlayer.Side.TEAM_B
        ]
        
        rating_a = sum(ratings.get(p.id, INITIAL_RATING) for p in team_a) / len(team_a)
        rating_b = sum(ratings.get(p.id, INITIAL_RATING) for p in team_b) / len(team_b)
        expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
        actual_a = 1 if match.score_a > match.score_b else 0
        delta = K_FACTOR * (actual_a - expected_a)

        for player in team_a:
            ratings[player.id] = ratings.get(player.id, INITIAL_RATING) + delta
            players[player.id] = player

        for player in team_b:
            ratings[player.id] = ratings.get(player.id, INITIAL_RATING) - delta
            players[player.id] = player


    player_ratings = [
        {"player": players[player_id], "rating": rating}
        for player_id, rating in ratings.items()
    ]
    player_ratings.sort(key=lambda x: (-x["rating"], x["player"].nickname))
    return player_ratings


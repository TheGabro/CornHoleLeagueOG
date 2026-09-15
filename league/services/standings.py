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
            mp.player
            for mp in match.players.all()
            if mp.side == MatchPlayer.Side.TEAM_A
        ]
        team_b = [
            mp.player
            for mp in match.players.all()
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


def scoring_averages():
    """
    PPR (Points Per Round, offensivo) e DPR (Defensive Points Per Round) per
    giocatore, su tutti i Match CONFIRMED (singolo e doppio insieme, come
    elo_ranking — qui l'ordine cronologico non conta, è solo una somma).

    PPR = totale punti fatti / totale round giocati.
    DPR = totale punti subiti / totale round giocati.
    (somma prima, dividi una volta sola alla fine — non fare la media dei
    rapporti per-partita, vedi commento sopra la funzione nel messaggio)

    Ritorna lista di dict {"player": User, "ppr": float, "dpr": float},
    ordinata ppr desc.
    """
    totals = {}  # player_id -> {"for": int, "against": int, "rounds": int}
    players = {}  # player_id -> istanza User

    matches = Match.objects.filter(
        status=Match.Status.CONFIRMED
    ).prefetch_related("players__player")

    for match in matches:

        # 1. per ogni MatchPlayer del match (match.players.all()):
        #    - se side == TEAM_A: punti fatti = match.score_a, subiti = match.score_b
        #    - se side == TEAM_B: punti fatti = match.score_b, subiti = match.score_a
        # 2. usa totals.setdefault(player_id, {"for": 0, "against": 0, "rounds": 0})
        #    e accumula "for", "against", "rounds" (+= match.rounds)
        # 3. ricordati players[player_id] = player, come in elo_ranking
        for mp in match.players.all():
            player_id = mp.player.id
            players[player_id] = mp.player
            if mp.side == MatchPlayer.Side.TEAM_A:
                totals.setdefault(player_id, {"for": 0, "against": 0, "rounds": 0})
                totals[player_id]["for"] += match.score_a
                totals[player_id]["against"] += match.score_b
                totals[player_id]["rounds"] += match.rounds
            elif mp.side == MatchPlayer.Side.TEAM_B:
                totals.setdefault(player_id, {"for": 0, "against": 0, "rounds": 0})
                totals[player_id]["for"] += match.score_b
                totals[player_id]["against"] += match.score_a
                totals[player_id]["rounds"] += match.rounds
    
    # trasforma `totals`/`players` in lista di dict
    # {"player": ..., "ppr": totals["for"]/totals["rounds"], "dpr": totals["against"]/totals["rounds"]},
    # ordinata per ppr decrescente.
    
    result = []
    for player_id, total in totals.items():
        ppr = total["for"] / total["rounds"] if total["rounds"] > 0 else 0
        dpr = total["against"] / total["rounds"] if total["rounds"] > 0 else 0
        result.append({"player": players[player_id], "ppr": ppr, "dpr": dpr})
    result.sort(key=lambda x: -x["ppr"])
    
    return result

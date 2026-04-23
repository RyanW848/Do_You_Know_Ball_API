from services.helpers import convert_to_player_ids

def get_age_multiplier(age):
        if age > 35:
            return 0.9
        elif 25 <= age <= 30:
            return 1.05
        else:
            return 1

def get_versatility_multiplier(pos_count):
    return 0.05 * pos_count + 0.95

def get_injury_multiplier(inj):
    injury_map = {
        'D7': 0.9, '7D': 0.9, 'D10': 0.8, '10D': 0.8,
        'D15': 0.7, '15D': 0.7, 'D60': 0.3, '60D': 0.3
    }
    return injury_map.get(inj, 1.0)

def get_depth_multiplier(depth_map):
    if not depth_map:
        return 0.5
    multiplier = max(
        1.3 * (0.9 ** (x_rank - 1)) 
        for x_rank in depth_map.values()
    )
    return multiplier

def get_scaled_score(avg_rank, total_players):
    avg_players = total_players / 2
    return 0.25 + (avg_players - avg_rank) / avg_players

def compute_valuation(players, data):
    budget = data.get('budget', 260)
    players_left = data.get('players_left_to_draft', 23)
    unavailable = data.get('unavailable_players', [])
    target_players = data.get('players', [])
    relevant_stats = data.get('relevant_stats') or ["HR", "R", "RBI", "SB", "BA", "SLG", "OBP", "OPS", "W", "K", "SV", "ERA", "WHIP"]
    
    avg_player_budget = budget / players_left if players_left > 0 else budget
    budget_for_one = budget - players_left + 1
    unavailable_ids = convert_to_player_ids(unavailable)
    target_player_ids = convert_to_player_ids(target_players)

    available_players = [p for p in players if p.get("mlbId") not in unavailable_ids]
    results = []
    
    if target_player_ids:
        players_to_calculate = [p for p in available_players if p.get("mlbId") in target_player_ids]
    else:
        players_to_calculate = available_players

    total = len(available_players)
    max_rounded_value = 0

    for p in players_to_calculate:
        depth_map = p.get('depthRanks', {})
        
        # --- 1. CALCULATE BASE SCORE ---
        rank_sum = 0
        stat_count = 0
        for stat in relevant_stats:
            rank = p.get('statRanks', {}).get(stat)
            if rank:
                rank_sum += rank
                stat_count += 1
        
        # FALLBACK: If they have NO stats, give them the worst possible average rank
        if stat_count == 0:
            avg_rank = total 
        else:
            avg_rank = rank_sum / stat_count

        # Scale
        scaled_base = get_scaled_score(avg_rank, total)

        # DEPTH CHART LOGIC 
        depth_chart_multiplier = get_depth_multiplier(depth_map)

        # Age Multipliers
        age = p.get('currentAge', 20)
        age_multiplier = get_age_multiplier(age) 
        
        # Versatility: Use 1 as default if not in depth chart
        pos_count = len(depth_map) if depth_map else 1
        versatility_multiplier = get_versatility_multiplier(pos_count)

        # Injury Multiplier
        inj = p.get('injuryStatus', 'A')
        injury_multiplier = get_injury_multiplier(inj)

        final_score = max(0, scaled_base * depth_chart_multiplier * age_multiplier * versatility_multiplier * injury_multiplier)
        initial_player_value = round(final_score * avg_player_budget, 0)

        if initial_player_value > max_rounded_value:
            max_rounded_value = initial_player_value

        results.append({
            "mlbId": p.get("mlbId"),
            "fullName": p.get("fullName"),
            "score": round(final_score, 4),
            "value": initial_player_value,
        })
    
    scaling_factor = 1.0
    if max_rounded_value > budget_for_one and max_rounded_value > 0:
        scaling_factor = budget_for_one / max_rounded_value

    if scaling_factor < 1.0:
        for res in results:
            res["value"] = round(res["value"] * scaling_factor, 0)

    results.sort(key=lambda x: x['score'], reverse=True)

    return {
        "budget": budget,
        "relevant_stats": relevant_stats,
        "player_count": len(results),
        "results": results
    }
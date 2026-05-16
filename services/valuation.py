from services.helpers import convert_to_player_ids

# Assisted by Claude 
def get_age_multiplier(age):
    """Penalize older players, boost prime age (25-30)"""
    if age > 35:
        return 0.9
    elif 25 <= age <= 30:
        return 1.05
    else:
        return 1

def get_versatility_multiplier(pos_count):
    """Each additional position adds 3% value"""
    return 0.03 * pos_count + 0.97

def get_injury_multiplier(inj):
    """Map injury codes to multipliers"""
    injury_map = {
        'D7': 0.9, '7D': 0.9, 'D10': 0.8, '10D': 0.8,
        'D15': 0.7, '15D': 0.7, 'D60': 0.3, '60D': 0.3
    }
    return injury_map.get(inj, 1.0)

def get_depth_multiplier(depth_map):
    """
    Reward players higher on depth charts.
    1st on chart: 1.3x, 2nd: 1.17x, 3rd: 1.053x, etc.
    Takes best position if player plays multiple.
    """
    if not depth_map:
        return 0.5
    multiplier = max(
        1.3 * (0.9 ** (x_rank - 1)) 
        for x_rank in depth_map.values()
    )
    return multiplier

def normalize_z_score(z):
    """
    Convert z-score to a positive value for multiplier use.
    Using sigmoid-like function: (tanh(z/2) + 1) / 2 + 0.5 = centered at 0.5-1.0 range
    
    z = -2: multiplier ≈ 0.21
    z = -1: multiplier ≈ 0.38
    z =  0: multiplier ≈ 0.50 (baseline)
    z = +1: multiplier ≈ 0.62
    z = +2: multiplier ≈ 0.73
    z = +3: multiplier ≈ 0.81
    
    This prevents negative multipliers while giving massive boost to elite players.
    """
    import math
    try:
        return (math.tanh(z / 2.0) + 1.0) / 2.0 + 0.5
    except:
        return 0.5

def compute_valuation(players, data):
    """
    Compute player valuations using z-score based performance.
    
    Args:
        players: List of player documents from MongoDB
        data: Request payload with budget, players_left_to_draft, etc.
    
    Returns:
        Dict with budget, relevant_stats, player_count, and results array
    """
    budget = data.get('budget', 260)
    players_left = data.get('players_left_to_draft', 23)
    unavailable = data.get('unavailable_players', [])
    target_players = data.get('players', [])
    relevant_stats = data.get('relevant_stats') or [
        "HR", "R", "RBI", "SB", "BA", "SLG", "OBP", "OPS", 
        "W", "K", "SV", "ERA", "WHIP"
    ]
    
    avg_player_budget = budget / players_left if players_left > 0 else budget
    budget_for_one = budget - players_left + 1
    unavailable_ids = convert_to_player_ids(unavailable, players)
    target_player_ids = convert_to_player_ids(target_players, players)

    available_players = [p for p in players if p.get("mlbId") not in unavailable_ids]
    results = []
    
    if target_player_ids:
        players_to_calculate = [p for p in available_players if p.get("mlbId") in target_player_ids]
    else:
        players_to_calculate = available_players

    max_rounded_value = 0

    for p in players_to_calculate:
        depth_map = p.get('depthRanks', {})
        z_scores = p.get('statZScores', {})
        
        # --- 1. CALCULATE BASE SCORE FROM Z-SCORES ---
        z_sum = 0
        z_count = 0
        for stat in relevant_stats:
            z = z_scores.get(stat)
            if z is not None:
                z_sum += z
                z_count += 1
        
        # If no z-scores available (shouldn't happen after sync), fallback to 0
        if z_count == 0:
            avg_z = 0
        else:
            avg_z = z_sum / z_count

        # Convert z-score to a multiplier (0.5 = baseline)
        z_multiplier = normalize_z_score(avg_z)

        # --- 2. APPLY MULTIPLIERS ---
        depth_chart_multiplier = get_depth_multiplier(depth_map)

        age = p.get('currentAge', 20)
        age_multiplier = get_age_multiplier(age) 
        
        pos_count = len(p.get("positions", [])) if p.get("positions") else 0
        versatility_multiplier = get_versatility_multiplier(pos_count)

        inj = p.get('injuryStatus', 'A')
        injury_multiplier = get_injury_multiplier(inj)

        # Combine: baseline (z-score normalized) × depth × age × versatility × injury
        final_score = max(
            0.1,  # Floor to prevent division issues
            z_multiplier * depth_chart_multiplier * age_multiplier * versatility_multiplier * injury_multiplier
        )
        
        initial_player_value = round(final_score * avg_player_budget, 0)

        if initial_player_value > max_rounded_value:
            max_rounded_value = initial_player_value

        results.append({
            "mlbId": p.get("mlbId"),
            "fullName": p.get("fullName"),
            "score": round(final_score, 4),
            "value": initial_player_value,
        })
    
    # --- 3. SCALE ALL VALUES TO FIT BUDGET ---
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
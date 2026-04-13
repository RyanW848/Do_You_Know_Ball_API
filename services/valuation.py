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
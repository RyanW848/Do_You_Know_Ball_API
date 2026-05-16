from pymongo import MongoClient, UpdateOne, ASCENDING
import os
from dotenv import load_dotenv
from datetime import datetime
from statistics import mean, stdev
from services.helpers import normalize_text
from services.mlb_service import get_all_teams, get_team_roster, get_players_with_stats
import json

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "doyouknowball"
COLLECTION_NAME = "players"


def get_stats_for_years(stats_groups, target_years):
    results = {}
    raw_2025_merged = {}
    positions_2025 = set()
    valid_pos = {"P", "C", "1B", "2B", "3B", "SS"}
    of_pos = {"LF", "CF", "RF", "OF"}

    for year in target_years:
        results[str(year)] = {
            "hitting": {
                "HR": 0,
                "R": 0,
                "RBI": 0,
                "SB": 0,
                "BA": 0.0,
                "SLG": 0.0,
                "OBP": 0.0,
                "OPS": 0.0,
                "PA": 0,
            },
            "pitching": {"W": 0, "K": 0, "SV": 0, "ERA": 0.0, "WHIP": 0.0, "IP": 0.0},
        }

    for group in stats_groups:
        group_name = group.get("group", {}).get("displayName")
        for split in group.get("splits", []):
            season = split.get("season")
            s = split.get("stat", {})

            if season == "2025":
                for key, val in s.items():
                    if isinstance(val, (int, float)) and key != "age":
                        raw_2025_merged[key] = raw_2025_merged.get(key, 0) + val
                    else:
                        raw_2025_merged[key] = val

            if group_name == "fielding" and season == "2025":
                games_at_pos = s.get("gamesPlayed", 0)
                if games_at_pos >= 10:
                    raw_pos = split.get("position", {}).get("abbreviation")
                    if raw_pos in of_pos:
                        positions_2025.add("OF")
                    elif raw_pos in valid_pos:
                        positions_2025.add(raw_pos)
                    elif raw_pos in ["DH", "TW"]:
                        positions_2025.add("UT")

            def to_f(val):
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return 0.0

            if season in results:
                if group_name == "hitting":
                    results[season]["hitting"] = {
                        "HR": s.get("homeRuns", 0),
                        "R": s.get("runs", 0),
                        "RBI": s.get("rbi", 0),
                        "SB": s.get("stolenBases", 0),
                        "BA": to_f(s.get("avg", 0.0)),
                        "SLG": to_f(s.get("slg", 0.0)),
                        "OBP": to_f(s.get("obp", 0.0)),
                        "OPS": to_f(s.get("ops", 0.0)),
                        "PA": s.get("plateAppearances", 0),
                    }
                elif group_name == "pitching":
                    results[season]["pitching"] = {
                        "W": s.get("wins", 0),
                        "K": s.get("strikeOuts", 0),
                        "SV": s.get("saves", 0),
                        "ERA": to_f(s.get("era", 0.0)),
                        "WHIP": to_f(s.get("whip", 0.0)),
                        "IP": to_f(s.get("inningsPitched", 0.0)),
                    }

    return results, ", ".join(sorted(list(positions_2025))), raw_2025_merged


def get_volume_multiplier_hitter(pa):
    """
    Discount bench players with low PA.
    ~600 PA (full-time): 1.0x
    ~400 PA (regular): 0.95x
    ~200 PA (part-time): 0.85x
    ~100 PA (bench): 0.70x
    
    Uses sigmoid to smoothly transition.
    """
    import math
    try:
        # Sigmoid centered at 400 PA, steepness 0.005
        # 400 PA -> 0.5 -> 0.75x multiplier
        # 600 PA -> 0.73 -> 0.865x multiplier
        # 200 PA -> 0.27 -> 0.635x multiplier
        sigmoid = 1.0 / (1.0 + math.exp(-0.005 * (pa - 400)))
        multiplier = 0.6 + sigmoid * 0.4  # Range [0.6, 1.0]
        return multiplier
    except:
        return 0.8


def get_volume_multiplier_pitcher(ip):
    """
    For pitchers, relief guys with low IP are OK (by design).
    But heavily discount spot appearance guys.
    
    ~200 IP (full-time): 1.0x
    ~100 IP (regular): 0.95x
    ~50 IP (part-time): 0.85x
    ~20 IP (very limited): 0.65x
    """
    import math
    try:
        # Sigmoid centered at 100 IP
        sigmoid = 1.0 / (1.0 + math.exp(-0.015 * (ip - 100)))
        multiplier = 0.6 + sigmoid * 0.4  # Range [0.6, 1.0]
        return multiplier
    except:
        return 0.8


def calculate_z_scores(db):
    """
    Calculate z-scores for all relevant stats and store them.
    Z-score = (value - mean) / stdev
    
    Key improvements:
    - Only divide counting stats by PA/IP. Rates stay as-is.
    - Apply volume penalty: players with low PA/IP are discounted slightly.
    """
    players = list(db[COLLECTION_NAME].find({}))
    if not players:
        return

    hitter_metrics = ["HR", "R", "RBI", "SB", "BA", "SLG", "OBP", "OPS"]
    pitcher_metrics = ["W", "K", "SV", "ERA", "WHIP"]
    counting_stats = {"HR", "R", "RBI", "SB", "W", "K", "SV"}
    rate_stats = {"BA", "SLG", "OBP", "OPS", "ERA", "WHIP"}
    lower_is_better = {"ERA", "WHIP"}
    weights = {"2023": 1, "2024": 2, "2025": 7}

    # Step 1: Collect all weighted values per metric
    metric_values = {}
    for metric in hitter_metrics + pitcher_metrics:
        metric_values[metric] = []

    for p in players:
        history = p.get("statsHistory", {})
        pos_list = p.get("positions", "")
        is_pitcher = "P" in pos_list
        is_hitter = (
            any(pos in pos_list for pos in ["C", "1B", "2B", "3B", "SS", "OF", "UT"])
            or not pos_list
        )

        # Collect hitter metrics (with volume penalty)
        if is_hitter:
            total_pa = sum(history.get(year, {}).get("hitting", {}).get("PA", 0) for year in weights.keys())
            vol_mult = get_volume_multiplier_hitter(total_pa)
            
            for metric in hitter_metrics:
                total_val, total_weight = 0, 0
                for year, weight in weights.items():
                    data = history.get(year, {}).get("hitting", {})
                    pa = data.get("PA", 0)
                    
                    if metric in rate_stats:
                        val = data.get(metric, 0)
                        if val > 0 or (metric in rate_stats and pa > 0):
                            total_val += val * weight
                            total_weight += weight
                    else:
                        if pa > 0:
                            val = data.get(metric, 0)
                            stat_to_add = val / pa
                            total_val += stat_to_add * weight
                            total_weight += weight
                
                if total_weight > 0:
                    weighted_avg = total_val / total_weight
                    # Apply volume penalty
                    weighted_avg *= vol_mult
                    metric_values[metric].append(weighted_avg)

        # Collect pitcher metrics (with volume penalty)
        if is_pitcher:
            total_ip = sum(history.get(year, {}).get("pitching", {}).get("IP", 0) for year in weights.keys())
            vol_mult = get_volume_multiplier_pitcher(total_ip)
            
            for metric in pitcher_metrics:
                total_val, total_weight = 0, 0
                for year, weight in weights.items():
                    data = history.get(year, {}).get("pitching", {})
                    ip = data.get("IP", 0)
                    
                    if metric in rate_stats:
                        val = data.get(metric, 0)
                        if val > 0 or (metric in rate_stats and ip > 0):
                            total_val += val * weight
                            total_weight += weight
                    else:
                        if ip > 0:
                            val = data.get(metric, 0)
                            stat_to_add = val / ip
                            total_val += stat_to_add * weight
                            total_weight += weight
                
                if total_weight > 0:
                    weighted_avg = total_val / total_weight
                    # Apply volume penalty
                    weighted_avg *= vol_mult
                    metric_values[metric].append(weighted_avg)

    # Step 2: Calculate mean and stdev for each metric
    metric_stats = {}
    for metric, values in metric_values.items():
        if len(values) > 1:
            m = mean(values)
            s = stdev(values)
            metric_stats[metric] = {"mean": m, "stdev": s}
        else:
            metric_stats[metric] = {"mean": 0, "stdev": 1}

    # Step 3: Calculate z-scores for each player
    bulk_updates = []
    for p in players:
        history = p.get("statsHistory", {})
        pos_list = p.get("positions", "")
        is_pitcher = "P" in pos_list
        is_hitter = (
            any(pos in pos_list for pos in ["C", "1B", "2B", "3B", "SS", "OF", "UT"])
            or not pos_list
        )

        z_scores = {}

        # Calculate z-scores for hitter metrics (with volume penalty)
        if is_hitter:
            total_pa = sum(history.get(year, {}).get("hitting", {}).get("PA", 0) for year in weights.keys())
            vol_mult = get_volume_multiplier_hitter(total_pa)
            
            for metric in hitter_metrics:
                total_val, total_weight = 0, 0
                for year, weight in weights.items():
                    data = history.get(year, {}).get("hitting", {})
                    pa = data.get("PA", 0)
                    
                    if metric in rate_stats:
                        val = data.get(metric, 0)
                        if val > 0 or (metric in rate_stats and pa > 0):
                            total_val += val * weight
                            total_weight += weight
                    else:
                        if pa > 0:
                            val = data.get(metric, 0)
                            stat_to_add = val / pa
                            total_val += stat_to_add * weight
                            total_weight += weight
                
                if total_weight > 0:
                    weighted_avg = total_val / total_weight
                    weighted_avg *= vol_mult
                    stats = metric_stats[metric]
                    z = (weighted_avg - stats["mean"]) / stats["stdev"] if stats["stdev"] > 0 else 0
                    z_scores[metric] = z

        # Calculate z-scores for pitcher metrics (with volume penalty)
        if is_pitcher:
            total_ip = sum(history.get(year, {}).get("pitching", {}).get("IP", 0) for year in weights.keys())
            vol_mult = get_volume_multiplier_pitcher(total_ip)
            
            for metric in pitcher_metrics:
                total_val, total_weight = 0, 0
                for year, weight in weights.items():
                    data = history.get(year, {}).get("pitching", {})
                    ip = data.get("IP", 0)
                    
                    if metric in rate_stats:
                        val = data.get(metric, 0)
                        if val > 0 or (metric in rate_stats and ip > 0):
                            total_val += val * weight
                            total_weight += weight
                    else:
                        if ip > 0:
                            val = data.get(metric, 0)
                            stat_to_add = val / ip
                            total_val += stat_to_add * weight
                            total_weight += weight
                
                if total_weight > 0:
                    weighted_avg = total_val / total_weight
                    weighted_avg *= vol_mult
                    stats = metric_stats[metric]
                    z = (weighted_avg - stats["mean"]) / stats["stdev"] if stats["stdev"] > 0 else 0
                    if metric in lower_is_better:
                        z = -z
                    z_scores[metric] = z

        bulk_updates.append(
            UpdateOne(
                {"_id": p["_id"]},
                {"$set": {"statZScores": z_scores}}
            )
        )

    if bulk_updates:
        db[COLLECTION_NAME].bulk_write(bulk_updates, ordered=False)
        print(f"Z-scores calculated and stored for {len(bulk_updates)} players")


def bake_json_file(db):
    print("Baking physical JSON cache file...")
    players_col = db[COLLECTION_NAME]
    
    cursor = players_col.find({}, {
        "mlbId": 1, "fullName": 1, "positions": 1, 
        "injuryStatus": 1, "currentTeamId": 1, "raw_2025": 1
    })

    team_map = {}
    try:
        teams_data = get_all_teams().get("teams", [])
        for t in teams_data:
            team_map[t['id']] = {
                "id": t['id'],
                "name": t.get("name"),
                "abbreviation": t.get("abbreviation")
            }
    except:
        pass

    results = []
    for doc in cursor:
        t_id = doc.get("currentTeamId")
        results.append({
            "player": {
                "id": doc.get("mlbId"),
                "name": doc.get("fullName"),
                "position": doc.get("positions"),
                "injuryStatus": doc.get("injuryStatus", "A")
            },
            "team": team_map.get(t_id, {"id": t_id, "name": "Unknown", "abbreviation": "N/A"}),
            "year": "2025",
            "stats": doc.get("raw_2025", {})
        })

    cache_path = os.path.join(os.path.dirname(__file__), "..", "data", "stats_cache.json")
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    
    with open(cache_path, "w") as f:
        json.dump({"count": len(results), "results": results}, f)
    
    print(f"File cache updated at {cache_path}")

def sync_mlb_players():
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        players_col = db[COLLECTION_NAME]
        players_col.delete_many({})

        print("Gathering player list")
        teams = get_all_teams().get("teams", [])

        all_players_metadata = {}
        depth_data = {}

        for team in teams:
            t_id = team.get("id")
            print(f"Processing team {team.get('name')} (ID: {t_id})")
            try:
                d_res = get_team_roster(t_id).get("roster", [])
                pos_counters = {}
                for entry in d_res:
                    pid = entry["person"]["id"]
                    abbr = entry["position"]["abbreviation"]
                    inj = entry.get("status", {}).get("code", "A")

                    if abbr not in pos_counters:
                        pos_counters[abbr] = 0
                    pos_counters[abbr] += 1

                    if pid not in depth_data:
                        depth_data[pid] = {"depthRanks": {}, "injuryStatus": inj}
                    depth_data[pid]["depthRanks"][abbr] = pos_counters[abbr]
            except Exception as e:
                print(f"Error: {e}")

            try:
                roster_data = get_team_roster(t_id, "40Man").get("roster", [])
                for p in roster_data:
                    all_players_metadata[p["person"]["id"]] = {
                        "fullName": p["person"]["fullName"],
                        "teamId": t_id,
                    }
            except Exception as e:
                print(f"Error: {e}")

        pids = list(all_players_metadata.keys())
        batch_size = 160
        all_operations = []

        for i in range(0, len(pids), batch_size):
            batch = pids[i : i + batch_size]
            ids_str = ",".join(map(str, batch))

            try:
                response = get_players_with_stats(ids_str)
                for person in response.get("people", []):
                    player_id = person["id"]
                    meta = all_players_metadata.get(player_id, {})
                    live = depth_data.get(
                        player_id, {"depthRanks": {}, "injuryStatus": "A"}
                    )

                    stats_groups = person.get("stats", [])
                    yearly_stats, pos_string, raw_stats_2025 = get_stats_for_years(
                        stats_groups, ["2023", "2024", "2025"]
                    )

                    if not pos_string:
                        raw_primary = person.get("primaryPosition", {}).get(
                            "abbreviation"
                        )
                        pos_string = (
                            "OF"
                            if raw_primary in ["LF", "CF", "RF", "OF"]
                            else raw_primary
                        )

                    all_operations.append(
                        UpdateOne(
                            {"mlbId": player_id},
                            {
                                "$set": {
                                    "mlbId": player_id,
                                    "fullName": meta.get("fullName"),
                                    "searchName": normalize_text(meta.get("fullName")),
                                    "currentTeamId": meta.get("teamId"),
                                    "currentAge": person.get("currentAge"),
                                    "positions": pos_string,
                                    "depthRanks": live["depthRanks"],
                                    "injuryStatus": live["injuryStatus"],
                                    "statsHistory": yearly_stats,
                                    "raw_2025": raw_stats_2025,
                                    "lastUpdated": datetime.now().strftime(
                                        "%Y-%m-%d %H:%M:%S"
                                    ),
                                }
                            },
                            upsert=True,
                        )
                    )
            except Exception as e:
                print(f"Error in batch: {e}")

        if all_operations:
            players_col.bulk_write(all_operations)
            players_col.create_index([("searchName", ASCENDING)])
            print("Sync complete. Now calculating z-scores...")

        calculate_z_scores(db)
        bake_json_file(db)
        client.close()
    except Exception as e:
        print(f"Critical Failure: {e}")


if __name__ == "__main__":
    sync_mlb_players()
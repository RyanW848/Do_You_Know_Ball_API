from pymongo import MongoClient, UpdateOne, ASCENDING
import os
from dotenv import load_dotenv
from datetime import datetime
from services.mlb_service import get_all_teams, get_team_roster, get_players_with_stats

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "doyouknowball"
COLLECTION_NAME = "players"

def get_stats_for_years(stats_groups, target_years):
    results = {}
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

            if group_name == "fielding" and season == "2025":
                games_at_pos = s.get("gamesPlayed", 0)
                if games_at_pos >= 5:
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

    return results, ", ".join(sorted(list(positions_2025)))


def calculate_weighted_ranks(db):
    players = list(db[COLLECTION_NAME].find({}))
    if not players:
        return

    hitter_metrics = ["HR", "R", "RBI", "SB", "BA", "SLG", "OBP", "OPS"]
    pitcher_metrics = ["W", "K", "SV", "ERA", "WHIP"]
    counting_stats = {"HR", "R", "RBI", "SB", "W", "K", "SV"}
    lower_is_better = {"ERA", "WHIP"}
    weights = {"2023": 1, "2024": 2, "2025": 7}

    player_stats_to_rank = []

    for p in players:
        history = p.get("statsHistory", {})
        processed = {"id": p["_id"], "metrics": {}}
        pos_list = p.get("positions", "")
        is_pitcher = "P" in pos_list
        is_hitter = (
            any(pos in pos_list for pos in ["C", "1B", "2B", "3B", "SS", "OF", "UT"])
            or not pos_list
        )

        if is_hitter:
            for metric in hitter_metrics:
                total_val, total_weight = 0, 0
                for year, weight in weights.items():
                    data = history.get(year, {}).get("hitting", {})
                    pa = data.get("PA", 0)
                    if pa > 0:
                        val = data.get(metric, 0)
                        stat_to_add = (val / pa) if metric in counting_stats else val
                        total_val += stat_to_add * weight
                        total_weight += weight
                processed["metrics"][metric] = (
                    total_val / total_weight if total_weight > 0 else -1
                )

        if is_pitcher:
            for metric in pitcher_metrics:
                total_val, total_weight = 0, 0
                for year, weight in weights.items():
                    data = history.get(year, {}).get("pitching", {})
                    ip = data.get("IP", 0)
                    if ip > 0:
                        val = data.get(metric, 0)
                        stat_to_add = (val / ip) if metric in counting_stats else val
                        total_val += stat_to_add * weight
                        total_weight += weight
                processed["metrics"][metric] = (
                    total_val / total_weight if total_weight > 0 else -1
                )

        player_stats_to_rank.append(processed)

    all_metrics = hitter_metrics + pitcher_metrics
    bulk_updates = []
    for metric in all_metrics:
        valid_players = [
            p
            for p in player_stats_to_rank
            if metric in p["metrics"] and p["metrics"][metric] >= 0
        ]
        should_reverse = metric not in lower_is_better
        valid_players.sort(key=lambda x: x["metrics"][metric], reverse=should_reverse)
        for i, p_data in enumerate(valid_players):
            bulk_updates.append(
                UpdateOne(
                    {"_id": p_data["id"]}, {"$set": {f"statRanks.{metric}": i + 1}}
                )
            )

    if bulk_updates:
        db[COLLECTION_NAME].bulk_write(bulk_updates, ordered=False)


def sync_mlb_players():
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        players_col = db[COLLECTION_NAME]
        players_col.delete_many({})

        print("Gathering player list")
        teams = get_all_teams().get("teams", [])

        all_players_metadata = {}
        depth_data = {}  # Stores live rank and injuries

        for team in teams:
            t_id = team.get("id")
            print(f"Processing team {team.get('name')} (ID: {t_id})")
            # --- FETCH DEPTH CHART ---
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

            # --- FETCH 40 MAN ---
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
                    yearly_stats, pos_string = get_stats_for_years(
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
                                    "searchName": meta.get("fullName", "")
                                    .lower()
                                    .strip(),
                                    "currentTeamId": meta.get("teamId"),
                                    "currentAge": person.get("currentAge"),
                                    "positions": pos_string,
                                    "depthRanks": live["depthRanks"],
                                    "injuryStatus": live["injuryStatus"],
                                    "statsHistory": yearly_stats,
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
            print("Sync complete. Now calculating weighted ranks...")

        calculate_weighted_ranks(db)
        client.close()
    except Exception as e:
        print(f"Critical Failure: {e}")


if __name__ == "__main__":
    sync_mlb_players()

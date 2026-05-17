from services.mlb_service import get_all_teams


def get_teams(predata=None):
    if predata:
        data = predata
    else:
        data = get_all_teams()
        if not data or "teams" not in data:
            return {"error": "Failed to fetch teams"}

    teams_list = []
    for team in data.get("teams", []):
        teams_list.append(
            {
                "id": team.get("id"),
                "name": team.get("name"),
                "abbreviation": team.get("abbreviation"),
            }
        )

    teams_list.sort(key=lambda x: x["name"])

    return {"count": len(teams_list), "teams": teams_list}


def get_all_players(cursor):
    player_list = []
    for p in cursor:
        mlbId = p.get("mlbId")
        url = p.get("headshotUrl")
        if url is None:
            url = f"https://securea.mlb.com/mlb/images/players/head_shot/{mlbId}.jpg"
        player_list.append(
            {
                "name": p.get("fullName"),
                "id": mlbId,
                "headshotUrl": url,
                "positions": p.get("positions"),
            }
        )

    player_list.sort(key=lambda x: x["name"])

    return {"count": len(player_list), "players": player_list}

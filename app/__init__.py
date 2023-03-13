import pathlib
import os
import csv
import json

import pandas as pd
import numpy as np

from flask import Flask, render_template, request, jsonify
from flask_assets import Environment, Bundle
from flask_compress import Compress
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text as textual
from slugify import slugify

db = SQLAlchemy()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
db.init_app(app)

CURRENT_WEEK = 7
INDEX_TO_POS = ["PG", "SG", "SF", "PF", "C"]
TEAMS = [
    "Fiji Kings",
    "Generation M",
    "Purple Haze",
    "Seattle Buckets",
    "Sheep Dogs",
    "Snack Time",
    "White Walkers",
]


def make_ordinal(n):
    """
    Convert an integer into its ordinal representation::

        make_ordinal(0)   => '0th'
        make_ordinal(3)   => '3rd'
        make_ordinal(122) => '122nd'
        make_ordinal(213) => '213th'
    """
    n = int(n)
    if n == 0:
        return "N/A"

    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]

    return str(n) + suffix


def read_csv(path):
    """Read and return the given CSV file."""
    data = []
    with open(os.path.join("app", "data", path)) as f:
        for line in csv.DictReader(f):
            data.append(line)
    return data


def read_json(path):
    """Read and return the given JSON file."""
    with open(os.path.join("app", "data", path)) as f:
        return json.load(f)


def to_percent(n, percents=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100]):
    n = int(round(n, 1) * 100)
    return min(percents, key=lambda x: abs(x - n))


def execute(q, **params):
    """Run the given database query and return its result."""
    text = (pathlib.Path("app/sql") / f"{q}.sql").read_text().format(**params)
    rows = db.session.execute(textual(text)).fetchall()
    return [r._mapping for r in rows]


@app.context_processor
def inject_globals():
    return dict(
        teams=TEAMS,
        slugify=slugify,
        to_ord=make_ordinal,
        social_handle=format_handle,
        # profiles=profiles,
    )


def format_handle(handle):
    """ """
    if not handle:
        return handle
    if handle.endswith("/"):
        handle = handle.strip("/")
    return handle.split("/")[-1]


def get_schedule(by_team=None):
    schedule = read_csv("s1/schedule.csv")
    voids = read_json("s1/void.json")
    reported = []

    history = execute("played")

    seen = []
    for game in schedule:
        teams = game["game"].split(" vs. ")

        voided = voids.get(f"{game['game']} - {game['week']}")
        if by_team and by_team not in teams:
            continue
        elif voided:
            reported.append(
                {
                    "away": voided["L"],
                    "home": voided["W"],
                    "hscore": 0,
                    "ascore": 0,
                    "status": "forfeit",
                    "id": None,
                    "week": game["week"],
                }
            )
            continue

        found = False
        for played in history:
            title = f"{played['away']} @ {played['home']}"
            key = f"{title}-{played['game']}"
            # If the game has been played, we have a result to report.
            if key not in seen and not found:
                if all(team in title for team in teams):
                    seen.append(key)
                    found = True
                    reported.append(
                        {
                            "away": played["away"],
                            "home": played["home"],
                            "hscore": played["home_score"],
                            "ascore": played["away_score"],
                            "status": "played",
                            "id": played["game"],
                            "week": game["week"],
                        }
                    )
                    break

        if not found:
            reported.append(
                {
                    "away": teams[0],
                    "home": teams[1],
                    "hscore": 0,
                    "ascore": 0,
                    "status": "TBD",
                    "week": game["week"],
                }
            )

    return reported


@app.route("/")
def home():
    """Render the home page."""
    recent_games = execute("recent-games")
    return render_template("pages/home.html", scores=recent_games)


@app.route("/players/<code>")
def player(code):
    """Render the given player's profile."""
    player = execute("profile", id=code)[0]

    df = pd.DataFrame.from_dict(execute("leaders"))

    total_g = (CURRENT_WEEK - 1) * 2
    games_req = int(total_g * 0.58)

    stats = {}
    for stat in ["pts", "reb", "ast", "stl", "blk", "3pm", "2pm", "ato", "3p%"]:
        df[stat] = df[stat].astype(float)

        n = float(len(df[stat]))

        tmp = df.sort_values(by=[stat], ascending=False, ignore_index=True)
        q = tmp[tmp["gp"] >= games_req]

        row = q.loc[tmp["pid"] == int(code)]
        if row.empty:
            row = tmp.loc[tmp["pid"] == int(code)]
            stats[stat] = [-1, row[stat], 0]
        else:
            rank = np.where(q["pid"] == int(code))[0]
            stats[stat] = [rank, row[stat], 100 - (rank / n) * 100]

    positions = set()
    teams = set()
    events = set()
    won = 0

    highs = {"3pm": 0, "reb": 0, "ast": 0, "blk": 0, "stl": 0, "pts": 0}
    shot_dist = {"ft": 0, "2": 0, "3": 0}

    games = execute("games", gid=code)
    for game in games:
        # FIXME: We don't want to do this ...
        boxscore = execute("boxscore", gid=game["game"])

        teams = []
        for idx, row in enumerate(boxscore):
            if idx >= 4:
                teams = []
            idx = idx - 5 if idx > 4 else idx

            teams.append(row["team_name"])
            if row["pid"] == int(code):
                fgm = row["fgm"] - row["3pm"]
                shot_dist["2"] += fgm
                shot_dist["3"] += row["3pm"]
                shot_dist["ft"] += row["pts"] - (3 * row["3pm"] + 2 * fgm)
                for k in highs.keys():
                    if row[k] > highs[k]:
                        highs[k] = row[k]
                positions.add(INDEX_TO_POS[idx])

                for team in set(teams):
                    result = execute("wins_by_players", gid=game["game"], team=team)
                    if result:
                        events.add(result[0]["event"])
                        break

                if result and result[0]["won"]:
                    won += 1

    positions = list(positions)
    positions.sort(key=lambda i: INDEX_TO_POS.index(i))

    percentiles = {
        "pts": stats["2pm"][2],
        "3pm": (stats["3pm"][2] + stats["3p%"][2]) / 2,
        "reb": stats["reb"][2],
        "ast": (stats["ast"][2] + stats["ato"][2]) / 2,
        "def": (stats["blk"][2] + stats["stl"][2]) / 2,
    }

    t_df = pd.DataFrame.from_dict(execute("team-records", name=player["team_name"]))
    l_df = pd.DataFrame.from_dict(execute("records"))

    awards = {"tr": set(), "lr": set()}
    for stat in ["pts", "reb", "ast", "stl", "blk", "3pm"]:
        t_df[stat] = t_df[stat].astype(float)
        l_df[stat] = l_df[stat].astype(float)

        holders = t_df[t_df[stat] == t_df[stat].max()].to_dict("records")
        for holder in holders:
            if player["gamertag"] == holder["gamertag"]:
                awards["tr"].add(f"{stat} ({holder[stat]})".upper())

        holders = l_df[l_df[stat] == l_df[stat].max()].to_dict("records")
        for holder in holders:
            if player["gamertag"] == holder["gamertag"]:
                awards["lr"].add(f"{stat} ({holder[stat]})".upper())

    return render_template(
        "pages/player.html",
        player=player,
        stats=stats,
        positions="/".join(positions),
        games=len(games),
        wins=won / len(games),
        events=len(events),
        by_event=execute("stats_by_event", pid=code),
        highs=highs,
        shot_dist=shot_dist,
        percentiles=percentiles,
        awards=awards,
    )


@app.route("/teams/<name>")
def team(name):
    """Render the given team's page."""
    name = name.replace("-", " ").title()

    stats = execute("team-stats", name=name)
    if not stats:
        # No games played yet ...
        return render_template(
            "pages/team.html",
            team=name,
            stats=[],
            games=[],
            seasons=0,
            total=0,
            records={},
        )

    games = execute("games-list", name=name)
    wins = execute("wins", name=name)

    seasons = execute("seasons", name=name)

    results = [0, 0]
    for row in execute("winp", name=name):
        results[0] += 1
        if row["won"]:
            results[1] += 1

    captain = None
    for row in stats:
        if row["captain"]:
            captain = row["gamertag"]

    df = pd.DataFrame.from_dict(execute("team-records", name=name))

    team_records = {}
    for stat in ["pts", "reb", "ast", "stl", "blk", "3pm"]:
        df[stat] = df[stat].astype(float)
        team_records[stat] = df[df[stat] == df[stat].max()].to_dict("records")[0]

    total = results[1] / float(results[0])
    return render_template(
        "pages/team.html",
        team=name,
        stats=stats,
        games=games,
        schedule=get_schedule(by_team=name),
        wins=wins,
        seasons=len(seasons),
        total=total,
        captain=captain,
        gp=len(games),
        records=team_records,
    )


@app.route("/games/<gid>")
def games(gid):
    """Render the league's current standings."""
    game = dict(execute("game", gid=gid)[0])

    if not game["stream"]:
        game["stream"] = ""

    if game["hw"]:
        game["winner"] = "h"
        game["loser"] = "a"
    else:
        game["winner"] = "a"
        game["loser"] = "h"

    progress = execute("stat-progress", gid=gid)
    for stat in ["ast", "reb", "stl", "3pm", "tov"]:
        total = progress[0][stat] + progress[1][stat]
        if game[game["winner"]] == progress[0]["name"]:
            game[game["winner"] + f"p{stat}"] = to_percent(
                progress[0][stat] / float(total)
            )
            game[game["loser"] + f"p{stat}"] = to_percent(
                progress[1][stat] / float(total)
            )

            game[game["winner"] + f"o{stat}"] = progress[0][stat]
            game[game["loser"] + f"o{stat}"] = progress[1][stat]
        else:
            game[game["winner"] + f"p{stat}"] = to_percent(
                progress[1][stat] / float(total)
            )
            game[game["loser"] + f"p{stat}"] = to_percent(
                progress[0][stat] / float(total)
            )

            game[game["winner"] + f"o{stat}"] = progress[1][stat]
            game[game["loser"] + f"o{stat}"] = progress[0][stat]

    boxscore = execute("boxscore", gid=gid)
    return render_template("pages/game.html", game=game, boxscore=boxscore)


@app.route("/stats/<category>")
def stats(category):
    """Render the given stat category."""
    events = execute("events")
    if category == "player":
        df = pd.DataFrame.from_dict(execute("leaders"))

        reported = get_schedule()
        sche_df = pd.DataFrame.from_dict(reported)
        week = int(max(sche_df["week"]))

        total_g = (week - 1) * 2
        games_req = 7  # int(total_g * 0.60)

        lookup = {}
        if not df.empty:
            # df = df[df["gp"] >= games_req]
            for stat in [
                "pts",
                "reb",
                "ast",
                "stl",
                "blk",
                "3pm",
                "fg%",
                "3p%",
                "fls",
                "tov",
            ]:
                df[stat] = df[stat].astype(float)

                s_df = df
                """
                if stat == "fg%":
                    req = 43.9 * (week / 12)
                    s_df = df[df["fgt"] >= req]
                elif stat == "3p%":
                    req = 12.00 * (week / 12)
                    s_df = df[df["3pt"] >= req]
                """

                lookup[stat] = s_df.nlargest(10, [stat]).to_dict("records")

        return render_template(
            f"pages/stats/player.html", stats=lookup, events=events, req=games_req
        )
    elif category == "team":
        return render_template(
            "pages/stats/team.html",
            team=execute("team"),
            oppo=execute("opponent"),
            events=events,
        )
    else:
        df = pd.DataFrame.from_dict(execute("records"))

        records = {}
        if not df.empty:
            for stat in ["pts", "reb", "ast", "stl", "blk", "3pm"]:
                df[stat] = df[stat].astype(float)
                records[stat] = df[df[stat] == df[stat].max()].to_dict("records")

        return render_template("pages/stats/records.html", highs=records)


@app.route("/s1/schedule")
def schedule():
    """Render the league's current schdule."""
    reported = get_schedule()
    return render_template("pages/schedule.html", schedule=reported)


@app.route("/s1/standings")
def standings():
    """Render the league's current schdule."""
    standings = execute("standings")

    voids = read_json("s1/void.json")

    computed = {}
    for row in standings:
        team = row["name"]
        if team not in computed:
            computed[team] = {
                "W": 0,
                "T": 0,
                "HW": 0,
                "HL": 0,
                "AW": 0,
                "AL": 0,
                "FW": 0,
                "FL": 0,
            }

        computed[team]["T"] += 1
        if row["won"]:
            computed[team]["W"] += 1
            if row["team"] == row["home"]:
                computed[team]["HW"] += 1
            else:
                computed[team]["AW"] += 1
        else:
            if row["team"] == row["home"]:
                computed[team]["HL"] += 1
            else:
                computed[team]["AL"] += 1

    for _, v in voids.items():
        if v["W"] not in computed:
            computed[v["W"]] = {
                "W": 0,
                "T": 0,
                "HW": 0,
                "HL": 0,
                "AW": 0,
                "AL": 0,
                "FW": 0,
                "FL": 0,
            }
        elif v["L"] not in computed:
            computed[v["L"]] = {
                "W": 0,
                "T": 0,
                "HW": 0,
                "HL": 0,
                "AW": 0,
                "AL": 0,
                "FW": 0,
                "FL": 0,
            }
        computed[v["W"]]["FW"] += 1
        computed[v["W"]]["W"] += 1
        computed[v["W"]]["T"] += 1
        computed[v["L"]]["FL"] += 1
        computed[v["L"]]["T"] += 1

    team_stats = execute("team")
    oppo_stats = execute("opponent")

    final = []
    for team, v in computed.items():
        ts = [t for t in team_stats if t["name"] == team]
        os = [t for t in oppo_stats if t["name"] == team]
        if not (ts and os):
            ts, os = {"pts": 0}, {"pts": 0}
        else:
            ts = ts[0]
            os = os[0]

        w = v["W"]
        l = v["T"] - v["W"]

        final.append(
            {
                "team": team,
                "W": w,
                "L": l,
                "PCT": w / v["T"],
                "HOME": f"{v['HW']}-{v['HL']}",
                "AWAY": f"{v['AW']}-{v['AL']}",
                "F": f"{v['FW']}-{v['FL']}",
                "GP": w + l,
                "DIFF": ts["pts"] - os["pts"],
            }
        )

    sdf = pd.DataFrame.from_dict(final)
    sdf = sdf.sort_values(by=["PCT", "GP", "DIFF"], ascending=False)

    return render_template(
        "pages/standings.html",
        standings=sdf.to_dict("records"),
        power=read_json("s1/power.json")[(str(CURRENT_WEEK - 1))],
    )


# Static assets
assets = Environment(app)

js = Bundle(
    "js/dep/bootstrap.bundle.min.js",
    output="js/lib.min.js",
)
assets.register("js_all", js)

css = Bundle("css/bootstrap.min.css", output="css/lib.min.css")
assets.register("css_all", css)

Compress(app)

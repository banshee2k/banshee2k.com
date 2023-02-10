import pathlib
import os
import csv
import json

import pandas as pd

from flask import Flask, render_template, request, jsonify
from flask_assets import Environment, Bundle
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text as textual
from slugify import slugify

db = SQLAlchemy()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
db.init_app(app)

CURRENT_WEEK = 4


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
    """ """
    profiles = {}
    for row in execute("profile-card"):
        profiles[row["id"]] = row

    return dict(
        teams=execute("teams"),
        slugify=slugify,
        profiles=profiles,
    )


def format_handle(handle):
    """ """
    if not handle:
        return handle
    if handle.endswith("/"):
        handle = handle.strip("/")
    return handle.split("/")[-1]


@app.context_processor
def utility_processor():
    def profile_card(pid, players):
        player = players.get(pid)
        if not player:
            return f"Player '{pid}' not found."

        tags = []
        if player["admin"]:
            tags.append('<span class="badge text-bg-secondary">admin</span>')
        if player["captain"]:
            tags.append('<span class="badge text-bg-secondary">captain</span>')

        has_handles = (
            player["discord"]
            or player["twitch"]
            or player["instagram"]
            or player["twitter"]
            or player["tiktok"]
        )

        return f"""
            <div class="card-body p-2">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="flex-shrink-0"><img class="avatar p-1" src="/static/img/logos/{player['name']}.png" alt="Jassa Rich"></div>
                    <div class="flex-grow-1 ps-3">
                        <h5>{player['gamertag']}</h5>
                        <p class="text-muted mb-0">{' '.join(tags)}</p>
                    </div>
                </div>
                <hr class="{'hide' if not has_handles else ''} m-0">
                <ul class="list-group list-group-flush rounded-3">
                    <li class="no-border list-group-item d-flex justify-content-between align-items-center {'hide' if not player['discord'] else ''}">
                        <span class="social-icon"><i class="fab fa-discord fa-lg" style="color: #333333;"></i></span>
                        <p class="mb-0 text-muted">@{format_handle(player['discord'])}</p>
                    </li>
                    <li class="no-border list-group-item d-flex justify-content-between align-items-center {'hide' if not player['twitch'] else ''}">
                        <span class="social-icon"><i class="fab fa-twitch fa-lg" style="color: #333333;"></i></span>
                        <p class="mb-0 text-muted">@{format_handle(player['twitch'])}</p>
                    </li>
                    <li class="no-border list-group-item d-flex justify-content-between align-items-center {'hide' if not player['twitter'] else ''}">
                        <span class="social-icon"><i class="fab fa-twitter fa-lg" style="color: #333333;"></i></span>
                        <p class="mb-0 text-muted">@{format_handle(player['twitter'])}</p>
                    </li>
                    <li class="no-border list-group-item d-flex justify-content-between align-items-center {'hide' if not player['instagram'] else ''}">
                        <span class="social-icon"><i class="fab fa-instagram fa-lg" style="color: #333333;"></i></span>
                        <p class="mb-0 text-muted">@{format_handle(player['instagram'])}</p>
                    </li>
                    <li class="no-border list-group-item d-flex justify-content-between align-items-center {'hide' if not player['tiktok'] else ''}">
                        <span class="social-icon"><i class="fab fa-tiktok fa-lg" style="color: #333333;"></i></span>
                        <p class="mb-0 text-muted">@{format_handle(player['tiktok'])}</p>
                    </li>
                </ul>
            </div>
        """

    return dict(profile_card=profile_card)


def get_schedule(by_team=None):
    schedule = read_csv("s1/schedule.csv")
    voids = read_json("s1/void.json")
    reported = []

    history = execute("played")

    seen = []
    for game in schedule:
        teams = game["game"].split(" vs. ")

        voided = voids.get(game["game"])
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
        games_req = int(total_g * 0.58)

        lookup = {}
        if not df.empty:
            df = df[df["gp"] >= games_req]
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
                if stat == "fg%":
                    req = 43.9 * (week / 12)
                    s_df = df[df["fgt"] >= req]
                elif stat == "3p%":
                    req = 12.00 * (week / 12)
                    s_df = df[df["3pt"] >= req]

                lookup[stat] = s_df.nlargest(10, stat).to_dict("records")

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

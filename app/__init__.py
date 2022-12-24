import pathlib
import os

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


def to_percent(n, percents=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100]):
    n = int(round(n, 1) * 100)
    return min(percents, key=lambda x: abs(x - n))


def execute(q, **params):
    """Run the given database query and return its result."""
    text = (pathlib.Path("app/sql") / f"{q}.sql").read_text().format(**params)
    rows = db.session.execute(textual(text)).fetchall()
    return [dict(r) for r in rows]


@app.context_processor
def inject_globals():
    profiles = {}
    for row in execute("profile-card"):
        profiles[row["id"]] = row

    return dict(
        teams=execute("teams"),
        events=execute("events"),
        profiles=profiles,
        slugify=slugify,
    )


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
                        <i class="fab fa-discord fa-lg" style="color: #333333;"></i>
                        <p class="mb-0 text-muted">@{player['discord']}</p>
                    </li>
                    <li class="no-border list-group-item d-flex justify-content-between align-items-center {'hide' if not player['twitch'] else ''}">
                        <i class="fab fa-twitch fa-lg" style="color: #333333;"></i>
                        <p class="mb-0 text-muted">@{player['twitch']}</p>
                    </li>
                    <li class="no-border list-group-item d-flex justify-content-between align-items-center {'hide' if not player['twitter'] else ''}">
                        <i class="fab fa-twitter fa-lg" style="color: #333333;"></i>
                        <p class="mb-0 text-muted">@{player['twitter']}</p>
                    </li>
                    <li class="no-border list-group-item d-flex justify-content-between align-items-center {'hide' if not player['instagram'] else ''}">
                        <i class="fab fa-instagram fa-lg" style="color: #333333;"></i>
                        <p class="mb-0 text-muted">@{player['instagram']}</p>
                    </li>
                    <li class="no-border list-group-item d-flex justify-content-between align-items-center {'hide' if not player['tiktok'] else ''}">
                        <i class="fab fa-tiktok fa-lg" style="color: #333333;"></i>
                        <p class="mb-0 text-muted">@{player['tiktok']}</p>
                    </li>
                </ul>
            </div>
        """

    return dict(profile_card=profile_card)


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
            "pages/team.html", team=name, stats=[], games=[], seasons=0, total=0
        )

    games = execute("games-list", name=name)
    wins = execute("wins", name=name)

    seasons = execute("seasons", name=name)[0]["event"]

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
        wins=wins,
        seasons=seasons,
        total=total,
        captain=captain,
        gp=len(games),
        records=team_records,
    )


@app.route("/games/<gid>")
def games(gid):
    """Render the league's current standings."""
    game = execute("game", gid=gid)[0]

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
    if category == "player":
        df = pd.DataFrame.from_dict(execute("leaders"))

        lookup = {}
        for stat in ["pts", "reb", "ast", "stl", "blk", "3pm"]:
            df[stat] = df[stat].astype(float)
            lookup[stat] = df.nlargest(10, stat).to_dict("records")

        return render_template(f"pages/stats/player.html", stats=lookup)
    elif category == "team":
        return render_template(
            "pages/stats/team.html",
            team=execute("team"),
            oppo=execute("opponent"),
        )
    else:
        df = pd.DataFrame.from_dict(execute("records"))

        records = {}
        for stat in ["pts", "reb", "ast", "stl", "blk", "3pm"]:
            df[stat] = df[stat].astype(float)
            records[stat] = df[df[stat] == df[stat].max()].to_dict("records")[0]

        return render_template("pages/stats/records.html", highs=records)


# Static assets
assets = Environment(app)

js = Bundle(
    "js/dep/bootstrap.bundle.min.js",
    output="js/lib.min.js",
)
assets.register("js_all", js)

css = Bundle("css/bootstrap.min.css", output="css/lib.min.css")
assets.register("css_all", css)

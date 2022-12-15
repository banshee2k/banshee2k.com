import pathlib
import os

import pandas as pd
import records

from flask import Flask, render_template, request, jsonify
from flask_assets import Environment, Bundle
from flask_sqlalchemy import SQLAlchemy

DB = records.Database()

db = SQLAlchemy()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
db.init_app(app)


def load_query(q):
    """
    """
    with open(f"app/data/{q}.bin", "rb") as f:
        return quickle.loads(f.read())


def to_percent(n, percents=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100]):
    n = int(round(n, 1) * 100)
    return min(percents, key=lambda x: abs(x - n))


def query(q, is_file, **params):
    """Run the given database query and return its result."""
    if is_file:
        return DB.query_file(pathlib.Path("app/sql") / f"{q}.sql", **params).as_dict()
    return DB.query(q, **params).as_dict()


def read_query(q, **params):
    """Run the given database query and return its result."""
    return (pathlib.Path("app/sql") / f"{q}.sql").read_text().format(**params)


@app.context_processor
def inject_globals():
    profiles = {}
    for row in query("profile-card", True):
        profiles[row["id"]] = row

    return dict(
        teams=query("teams", True),
        events=query("events", True),
        profiles=profiles,
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

        return f"""
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="flex-shrink-0"><img class="avatar p-1" src="/static/img/logos/{player['name']}.png" alt="Jassa Rich"></div>
                    <div class="flex-grow-1 ps-3">
                        <h5>{player['gamertag']}</h5>
                        <p class="text-muted mb-0">{' '.join(tags)}</p>
                    </div>
                </div>
                <hr class="{'hide' if not player['discord'] else ''} m-0">
                <ul class="list-group list-group-flush rounded-3 {'hide' if not player['discord'] else ''}">
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <i class="fab fa-discord fa-lg" style="color: #333333;"></i>
                        <p class="mb-0 text-muted">@{player['discord']}</p>
                    </li>
                </ul>
            </div>
        """

    return dict(profile_card=profile_card)


@app.route("/")
def home():
    """Render the home page."""
    return render_template("pages/home.html", scores=query("recent-games", True))


@app.route("/teams/<name>")
def team(name):
    """Render the given team's page."""
    team = query("abbr-to-team", True, abbr=name)[0]

    lookup = {}
    for stat in ["PTS", "REB", "AST", "STL", "BLK", "3PM"]:
        q = read_query("team-records", STAT=stat.lower())
        ret = query(q, False, id=team["id"])
        lookup[stat] = ret[0] if len(ret) else 0

    return render_template(
        "pages/team.html",
        team=team["name"],
        stats=query("team-avg", True, id=team["id"]),
        records=lookup,
        games=query("games", True, abbr=name),
    )


@app.route("/games/<gid>")
def games(gid):
    """Render the league's current standings."""
    game = query("game", True, id=gid)[0]

    if not game["stream"]:
        game["stream"] = ""

    if game["hw"]:
        game["winner"] = "h"
        game["loser"] = "a"
    else:
        game["winner"] = "a"
        game["loser"] = "h"

    progress = query("progress", True, id=gid)
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

    boxscore = query("boxscore", True, id=gid)
    return render_template("pages/game.html", game=game, boxscore=boxscore)


@app.route("/s1/standings")
def standings():
    """Render the league's current standings."""
    rows = pd.read_csv(DATA / "build" / "standings.csv").to_dict("records")
    return render_template("pages/standings.html", overall=rows)


@app.route("/s1/playoffs")
def playoffs():
    """Render the league's current standings."""
    rows = read_json("s1/bracket.json")
    return render_template("pages/playoffs.html", bracket=rows)


@app.route("/stats/<category>")
def stats(category):
    """Render the given stat category."""
    if category == "player":
        stats = ["PTS", "REB", "AST", "STL", "BLK", "3PM", "FLS", "TO"]

        lookup = {}
        for stat in stats:
            q = read_query("leaders", STAT=stat.lower())
            lookup[stat] = query(q, False)

        print("DONE!!!!!!!!!!!!!!")
        return render_template(f"pages/stats/player.html", stats=lookup)
    elif category == "team":
        return render_template(
            "pages/stats/team.html",
            team=query("team", True),
            oppo=query("opponent", True),
        )
    else:
        stats = ["PTS", "REB", "AST", "STL", "BLK", "3PM"]

        lookup = {}
        for stat in stats:
            q = read_query("records", STAT=stat.lower())
            lookup[stat] = query(q, False)[0]

        return render_template("pages/stats/records.html", highs=lookup)


@app.route("/s1/schedule")
def schedule():
    """Render the league's current schdule."""
    schedule = read_csv("s1/schedule.csv")
    reported = []

    seen = []
    for game in schedule:
        teams = game["game"].split(" vs. ")

        found = False
        for played in (DATA / "s1" / "games").glob("**/*.csv"):
            title = played.name
            # If the game has been played, we have a result to report.
            if title not in seen and not found:
                if all(team in title for team in teams):
                    seen.append(title)
                    found = True
                    info = read_csv(f"s1/games/{title}")
                    reported.append(
                        {
                            "away": info[0]["Team"],
                            "home": info[1]["Team"],
                            "hscore": info[1]["Total"],
                            "ascore": info[0]["Total"],
                            "status": "played",
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
                }
            )

    return render_template("pages/schedule.html", games=reported)


# Static assets
assets = Environment(app)

js = Bundle(
    "js/dep/bootstrap.bundle.min.js",
    output="js/lib.min.js",
)
assets.register("js_all", js)

css = Bundle("css/bootstrap.min.css", output="css/lib.min.css")
assets.register("css_all", css)

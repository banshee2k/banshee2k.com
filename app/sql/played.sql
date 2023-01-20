SELECT
    game.id           AS "game",
	home.name         AS "home",
	away.name         AS "away",
	home_score.total  AS "home_score",
	away_score.total  AS "away_score"
FROM game
JOIN team AS home
	ON game.home=home.id
JOIN team AS away
	ON game.away=away.id
JOIN score as home_score
	ON home_score.game=game.id AND home_score.team=home.id
JOIN score as away_score
	ON away_score.game=game.id AND away_score.team=away.id;

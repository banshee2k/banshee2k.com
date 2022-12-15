SELECT
    game.id,
    game.date,
    game.stream,
    home.name AS home,
    away.name AS away,
    home_score.total AS home_score,
    away_score.total AS away_score
FROM game
JOIN team AS home
	ON game.home=home.id
JOIN team AS away
	ON game.away=away.id
JOIN score AS home_score
	ON game.home=home_score.team
JOIN score AS away_score
	ON game.away=away_score.team
LIMIT 5;

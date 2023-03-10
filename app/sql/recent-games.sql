SELECT
    game.id,
    game.date,
    game.stream,
    home.name AS home,
    away.name AS away,
    home.abbr AS habbr,
    away.abbr AS aabbr,
    home_score.total AS home_score,
    away_score.total AS away_score
FROM game
JOIN team AS home
	ON game.home=home.id
JOIN team AS away
	ON game.away=away.id
JOIN score AS home_score
	ON game.home=home_score.team AND game.id=home_score.game
JOIN score AS away_score
	ON game.away=away_score.team AND game.id=away_score.game
ORDER BY game.date DESC
LIMIT 5;

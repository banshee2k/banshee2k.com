SELECT DISTINCT
	game.id,
	home.name as home,
    away.name as away,
    game.date
FROM game
JOIN team AS home
	ON game.home = home.id OR game.away = home.id
JOIN team AS away
	ON game.home = away.id OR game.away = away.id
WHERE home.abbr=:abbr AND home.id != away.id

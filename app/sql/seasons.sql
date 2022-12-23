SELECT DISTINCT
	game.event
FROM game
JOIN team
	ON team.id = game.home OR team.id = game.away
WHERE team.name = '{name}';

SELECT
    event.name,
    event."2k"
FROM team
JOIN event
	ON event.winner = team.id
WHERE team.name = '{name}';

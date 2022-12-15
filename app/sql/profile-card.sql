SELECT
	player.id AS id,
    player.gamertag,
    player.discord,
    player.captain,
    player.admin,
    team.name,
    team.abbr
FROM player
JOIN team
	ON team.id=player.team_id

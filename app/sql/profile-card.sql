SELECT
	player.id AS id,
    player.gamertag,
    player.discord,
    player.captain,
    player.admin,
    player.twitch,
    player.tiktok,
    player.instagram,
    player.twitter,
    team.name,
    team.abbr
FROM player
JOIN team
	ON team.id=player.team_id

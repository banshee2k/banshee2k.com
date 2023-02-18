SELECT
    player.name AS gamertag,
    player.twitch,
    player.discord,
    player.tiktok,
    player.instagram,
    player.twitter,
    player.captain,
    player.admin,
    team.name AS team_name,
    team.logo AS team_logo
FROM player
JOIN team
	on player.team=team.id
WHERE player.id='{id}';

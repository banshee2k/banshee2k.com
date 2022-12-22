SELECT
    player.id,
	gamertag,
	MAX("{STAT}") AS computed
FROM stats
JOIN player
	ON stats.player=player.id
JOIN team
	ON player.team=team.id
WHERE team.id=:id
GROUP BY gamertag, player.id
ORDER BY computed DESC
LIMIT 1;

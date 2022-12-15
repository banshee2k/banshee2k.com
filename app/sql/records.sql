SELECT
	gamertag,
	MAX("{STAT}") AS computed
FROM stats
JOIN player
	ON stats.player=player.id
GROUP BY gamertag
ORDER BY computed DESC
LIMIT 1;

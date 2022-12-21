SELECT
	gamertag,
    player.id     AS pid,
	MAX("{stat}") AS computed
FROM stats
JOIN player
	ON stats.player=player.id
GROUP BY gamertag, player.id
ORDER BY computed DESC
LIMIT 1;

SELECT
	player.gamertag,
    player.id              AS pid,
    COUNT(player.gamertag) AS gp,
	AVG(stats.pts)         AS pts,
    AVG(stats.reb)         AS reb,
    AVG(stats.ast)         AS ast,
    AVG(stats.stl)         AS stl,
    AVG(stats.blk)         AS blk,
    AVG(stats."3pm")       AS "3pm"
FROM stats
JOIN player
	ON stats.player=player.id
GROUP BY gamertag, player.id;

SELECT
	event.name,
    Count(player.name)                                AS gp,
    Avg(pts)                                          AS pts,
    Avg(reb)                                          AS reb,
    Avg(ast)                                          AS ast,
    Avg(stl)                                          AS stl,
    Avg(blk)                                          AS blk,
    Avg(stats.to)                                     AS tov,
    Sum("3pm")                                        AS "3pm",
    Sum("3pa")                                        AS "3pa",
    Sum("3pm") / NULLIF(Cast(Sum("3pa") AS FLOAT), 0) AS "3p%",
    Sum("fgm")                                        AS "fgm",
    Sum("fga")                                        AS "fga",
    Sum("fgm") / NULLIF(Cast(Sum("fga") AS FLOAT), 0) AS "fg%"
FROM
    player, stats, game
JOIN event
	on event.id=game.event
WHERE  player.id = '{pid}' AND stats.player = '{pid}' AND stats.game = game.id
GROUP  BY
        event.name
ORDER  BY pts DESC;


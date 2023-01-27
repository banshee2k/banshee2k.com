SELECT
    player.name                                                   AS gamertag,
    player.id                                                     AS pid,
    player.team                                                   AS team,
    COUNT(player.name)                                            AS gp,
    AVG(stats.pts)                                                AS pts,
    AVG(stats.reb)                                                AS reb,
    AVG(stats.ast)                                                AS ast,
    AVG(stats.stl)                                                AS stl,
    AVG(stats.blk)                                                AS blk,
    AVG(stats.to)                                                 AS tov,
    AVG(stats.fls)                                                AS fls,
    AVG(stats."3pm")                                              AS "3pm",
    CAST(SUM(stats."3pm") AS float) / NULLIF(SUM(stats."3pa"), 0) AS "3p%",
    CAST(SUM(stats."fgm") AS float) / NULLIF(SUM(stats."fga"), 0) AS "fg%"
FROM stats
JOIN player
    ON stats.player=player.id
GROUP BY player.name, player.id;

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
    (SUM(stats."fgm") - SUM(stats."3pm")) / COUNT(player.name)    AS "2pm",
    CAST(SUM(stats."ast") AS float) / NULLIF(SUM(stats."to"), 0)  AS "ato",
    CAST(SUM(stats."stl") AS float) / NULLIF(SUM(stats."fls"), 0) AS "sro",
    CAST(SUM(stats."blk") AS float) / NULLIF(SUM(stats."fls"), 0) AS "bro",
    SUM(stats."3pm")                                              AS "3pt",
    SUM(stats."fgm")                                              AS "fgt",
    CAST(SUM(stats."3pm") AS float) / NULLIF(SUM(stats."3pa"), 0) AS "3p%",
    CAST(SUM(stats."fgm") AS float) / NULLIF(SUM(stats."fga"), 0) AS "fg%"
FROM stats
JOIN player
    ON stats.player=player.id
GROUP BY player.name, player.id;

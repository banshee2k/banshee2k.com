SELECT
    gamertag,
    team.NAME,
    team.id,
    player.id                                         AS pid,
    Count(gamertag)                                   AS gp,
    Avg(pts)                                          AS pts,
    Avg(reb)                                          AS reb,
    Avg(ast)                                          AS ast,
    Avg(stl)                                          AS stl,
    Avg(blk)                                          AS blk,
    Avg(stats.to)                                     AS tov,
    Avg("3pm")                                        AS "3pm",
    Avg("3pa")                                        AS "3pa",
    Sum("3pm") / NULLIF(Cast(Sum("3pa") AS FLOAT), 0) AS "3p%",
    Avg("fgm")                                        AS "fgm",
    Avg("fga")                                        AS "fga",
    Sum("fgm") / NULLIF(Cast(Sum("fga") AS FLOAT), 0) AS "fg%"
FROM
    stats,
    player,
    team
WHERE  stats.player = player.id
    AND team.id = player.team
    AND team.name = '{name}'
GROUP  BY gamertag,
        team.NAME,
        team.id,
        player.id
ORDER  BY pts DESC;

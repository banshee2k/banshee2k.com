SELECT
    team.NAME,
    team.abbr                              AS tid,
    Count(team.NAME) / 5                   AS gp,
    Avg(pts)                               AS pts,
    Avg(ast)                               AS ast,
    Avg(reb)                               AS reb,
    Avg("3pm")                             AS "3pm",
    Avg("3pa")                             AS "3pa",
    Sum("3pm") / Cast(Sum("3pa") AS FLOAT) AS "3p%",
    Avg("fgm")                             AS "fgm",
    Avg("fga")                             AS "fga",
    Sum("fgm") / Cast(Sum("fga") AS FLOAT) AS "fg%",
    Avg(stats.to)                          AS tov,
    Avg(blk)                               AS blk,
    Avg(stl)                               AS stl
FROM stats
    JOIN player
        ON stats.player = player.id
    JOIN team
        ON player.team_id = team.id
GROUP BY team.NAME, team.abbr
ORDER BY pts DESC;

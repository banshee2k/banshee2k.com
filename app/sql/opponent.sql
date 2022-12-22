SELECT team.name,
       Count(team.NAME) / 5                   AS gp,
       Sum(pts)                               AS pts,
       Sum(ast)                               AS ast,
       Sum(reb)                               AS reb,
       Sum("3pm")                             AS "3pm",
       Sum("3pa")                             AS "3pa",
       Sum("3pm") / Cast(Sum("3pa") AS FLOAT) AS "3p%",
       Sum("fgm")                             AS "fgm",
       Sum("fga")                             AS "fga",
       Sum("fgm") / Cast(Sum("fga") AS FLOAT) AS "fg%",
       Sum(stats.to)                          AS tov,
       Sum(blk)                               AS blk,
       Sum(stl)                               AS stl
FROM   stats
       JOIN player
         ON stats.player = player.id
       JOIN game
       	 ON stats.game = game.id
       JOIN team
         ON player.team != team.id AND (team.id = game.home OR team.id = game.away)
GROUP  BY team.NAME
ORDER  BY pts ASC;

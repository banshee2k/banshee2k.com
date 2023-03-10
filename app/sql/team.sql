SELECT team.NAME,
       team.abbr                                AS tid,
       Count(team.NAME) / 5                     AS gp,
       Sum(pts) / ( Count(team.NAME) / 5 )      AS pts,
       Sum(ast) / ( Count(team.NAME) / 5 )      AS ast,
       Sum(reb) / ( Count(team.NAME) / 5 )      AS reb,
       Sum("3pm") / ( Count(team.NAME) / 5 )    AS "3pm",
       Sum("3pa") / ( Count(team.NAME) / 5 )    AS "3pa",
       Sum("3pm") / Cast(Sum("3pa") AS FLOAT)   AS "3p%",
       Sum("fgm") / ( Count(team.NAME) / 5 )    AS "fgm",
       Sum("fga") / ( Count(team.NAME) / 5 )    AS "fga",
       Sum("fgm") / Cast(Sum("fga") AS FLOAT)   AS "fg%",
       Sum(stats.to) / ( Count(team.NAME) / 5 ) AS tov,
       Sum(blk) / ( Count(team.NAME) / 5 )      AS blk,
       Sum(stl) / ( Count(team.NAME) / 5 )      AS stl
FROM   stats
       JOIN player
         ON stats.player = player.id
       JOIN team
         ON player.team = team.id
       JOIN game
	     on stats.game=game.id
WHERE game.event=4
GROUP  BY team.NAME,
          team.abbr
ORDER  BY pts DESC;

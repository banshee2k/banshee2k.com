SELECT
    team.name,
    SUM(ast) AS ast,
    SUM(reb) AS reb,
    SUM(stl) AS stl,
    SUM("3pm") AS "3pm",
    SUM("to") AS "tov"
FROM stats
JOIN player
    ON stats.player=player.id
JOIN team
    ON player.team_id=team.id
WHERE stats.game='{gid}'
GROUP BY team.name;

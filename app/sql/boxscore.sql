SELECT
    player.id   AS pid,
    player.name AS gamertag,
    team.name   AS team_name,
    *
FROM stats
JOIN player
    ON stats.player=player.id
JOIN team
    ON team.id=player.team
WHERE stats.game='{gid}'
ORDER BY stats.id;

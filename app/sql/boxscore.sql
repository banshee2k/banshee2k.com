SELECT
    player.id AS pid,
    player.name AS gamertag,
    *
FROM stats
JOIN player
    ON stats.player=player.id
WHERE stats.game='{gid}'
ORDER BY stats.id;

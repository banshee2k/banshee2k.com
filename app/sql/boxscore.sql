SELECT
    player.id AS pid,
    player.name AS gamertag,
    *
FROM stats
JOIN player
    ON stats.player=player.id
JOIN team
    ON player.team=team.id
WHERE stats.game='{gid}';

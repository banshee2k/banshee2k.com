SELECT
    player.id AS pid,
    *
FROM stats
JOIN player
    ON stats.player=player.id
JOIN team
    ON player.team_id=team.id
WHERE stats.game='{gid}';

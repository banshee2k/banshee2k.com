SELECT
    player.id,
	gamertag,
    game.id    AS game,
	MAX(pts)   AS pts,
	MAX(reb)   AS reb,
    MAX(ast)   AS ast,
	MAX(stl)   AS stl,
	MAX(blk)   AS blk,
	MAX("3pm") AS "3pm"
FROM stats
JOIN player
	ON stats.player=player.id
JOIN team
	ON player.team=team.id
JOIN game
	ON stats.game=game.id
WHERE team.name='{name}'
GROUP BY gamertag, player.id, game.id;

SELECT DISTINCT
	*
FROM score
JOIN team
	on team.id=score.team
JOIN game
	on game.id=score.game
WHERE score.game='{gid}' AND team.name='{team}';

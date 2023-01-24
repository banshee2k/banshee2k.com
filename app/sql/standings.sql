SELECT
	*
FROM score
JOIN team
	ON score.team=team.id
JOIN game
	on score.game=game.id;

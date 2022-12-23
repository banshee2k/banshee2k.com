SELECT
	*
FROM score
JOIN team
	ON score.team = team.id
WHERE team.name = '{name}';

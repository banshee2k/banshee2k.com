SELECT
    game.date,
    game.stream,
    home.NAME          AS h,
    away.NAME          AS a,
    home.abbr          AS hab,
    away.abbr          AS aab,
    home_score."1st"   AS h1,
    home_score."2nd"   AS h2,
    home_score."3rd"   AS h3,
    home_score."4th"   AS h4,
    home_score."total" AS htotal,
    home_score.won     AS hw,
    away_score."1st"   AS a1,
    away_score."2nd"   AS a2,
    away_score."3rd"   AS a3,
    away_score."4th"   AS a4,
    away_score."total" AS atotal,
    away_score.won     AS aw
FROM  game
    JOIN team AS home
        ON game.home = home.id
    JOIN team AS away
        ON game.away = away.id
    JOIN score AS home_score
        ON game.id=home_score.game AND game.home = home_score.team
    JOIN score AS away_score
        ON game.id=away_score.game AND game.away = away_score.team
WHERE  game.id = '{gid}';

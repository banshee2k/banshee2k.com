SELECT DISTINCT
    game.id,
    home.name AS home,
    away.name AS away,
    home.abbr AS home_short,
    away.abbr AS away_short,
    game.date
FROM game
    JOIN team AS home
        ON game.home = home.id
            OR game.away = home.id
    JOIN team AS away
        ON game.home = away.id
            OR game.away = away.id
WHERE  home.name = '{name}'
    AND home.id != away.id

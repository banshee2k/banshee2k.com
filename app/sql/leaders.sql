SELECT gamertag,
       player.id,
       team.abbr,
       Count(gamertag) AS gp,
       Avg("{STAT}")   AS computed
FROM   stats,
       player,
       team
WHERE  stats.player = player.id
       AND team.id = player.team_id
GROUP  BY gamertag,
          team.abbr,
          player.id
ORDER  BY computed DESC
LIMIT  10;

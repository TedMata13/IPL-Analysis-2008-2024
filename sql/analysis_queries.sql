-- analysis_queries.sql
-- Analytical queries over the real IPL dataset (2008-2024, matches + deliveries).
-- Tested against SQLite; only trivial syntax changes needed for MySQL/Postgres.

-- =====================================================================
-- 1. Season-wise number of matches and total runs scored
-- =====================================================================
SELECT
    m.season,
    COUNT(DISTINCT m.match_id)                          AS matches_played,
    SUM(d.total_runs)                                   AS total_runs_scored,
    ROUND(SUM(d.total_runs) * 1.0 / COUNT(DISTINCT m.match_id), 1) AS avg_runs_per_match
FROM matches m
JOIN deliveries d ON d.match_id = m.match_id
GROUP BY m.season
ORDER BY m.season;


-- =====================================================================
-- 2. Team win counts and win percentage (across all seasons)
-- =====================================================================
SELECT
    winner AS team,
    COUNT(*) AS total_wins,
    ROUND(
        COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM matches m2 WHERE m2.team1 = winner OR m2.team2 = winner),
        2
    ) AS win_percentage
FROM matches
WHERE winner IS NOT NULL
GROUP BY winner
ORDER BY total_wins DESC;


-- =====================================================================
-- 3. Top 10 run scorers (career)
-- =====================================================================
SELECT
    batter,
    SUM(batsman_runs)                                   AS total_runs,
    COUNT(DISTINCT match_id)                            AS innings_played,
    ROUND(SUM(batsman_runs) * 1.0 / COUNT(DISTINCT match_id), 2) AS avg_runs_per_innings,
    SUM(CASE WHEN batsman_runs = 4 THEN 1 ELSE 0 END)  AS fours,
    SUM(CASE WHEN batsman_runs = 6 THEN 1 ELSE 0 END)  AS sixes
FROM deliveries
GROUP BY batter
ORDER BY total_runs DESC
LIMIT 10;


-- =====================================================================
-- 4. Top 10 wicket takers (career) -- excludes run-outs, not bowler-credited
-- =====================================================================
SELECT
    bowler,
    SUM(is_wicket)                                      AS total_wickets_incl_runouts,
    SUM(CASE WHEN dismissal_kind NOT IN ('run out', 'retired hurt', 'retired out',
                                          'obstructing the field') OR dismissal_kind = ''
             THEN is_wicket ELSE 0 END)                 AS bowler_credited_wickets,
    COUNT(DISTINCT match_id)                            AS matches_bowled
FROM deliveries
GROUP BY bowler
ORDER BY bowler_credited_wickets DESC
LIMIT 10;


-- =====================================================================
-- 5. Toss decision impact: does winning the toss => winning the match?
-- =====================================================================
SELECT
    toss_decision,
    COUNT(*)                                                          AS total_matches,
    SUM(CASE WHEN toss_winner = winner THEN 1 ELSE 0 END)             AS toss_and_match_winner,
    ROUND(SUM(CASE WHEN toss_winner = winner THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS win_pct_after_toss_win
FROM matches
WHERE winner IS NOT NULL
GROUP BY toss_decision;


-- =====================================================================
-- 6. Venue-wise average first-innings score (batting-friendly venues, min 10 matches)
-- =====================================================================
SELECT
    m.venue,
    m.city,
    COUNT(DISTINCT m.match_id) AS matches_hosted,
    ROUND(AVG(inns.first_innings_score), 1) AS avg_first_innings_score
FROM matches m
JOIN (
    SELECT match_id, SUM(total_runs) AS first_innings_score
    FROM deliveries WHERE inning = 1 GROUP BY match_id
) inns ON inns.match_id = m.match_id
GROUP BY m.venue, m.city
HAVING matches_hosted >= 10
ORDER BY avg_first_innings_score DESC;


-- =====================================================================
-- 7. Most Player-of-the-Match awards
-- =====================================================================
SELECT
    player_of_match,
    COUNT(*) AS awards
FROM matches
WHERE player_of_match IS NOT NULL
GROUP BY player_of_match
ORDER BY awards DESC
LIMIT 10;


-- =====================================================================
-- 8. Powerplay (overs 1-6) vs Middle vs Death overs (17-20) scoring comparison
-- =====================================================================
SELECT
    CASE
        WHEN over BETWEEN 0 AND 5   THEN 'Powerplay (1-6)'
        WHEN over BETWEEN 6 AND 15  THEN 'Middle (7-16)'
        WHEN over BETWEEN 16 AND 19 THEN 'Death (17-20)'
    END AS phase,
    SUM(total_runs)  AS runs_scored,
    SUM(is_wicket)   AS wickets_lost
FROM deliveries
GROUP BY phase;


-- =====================================================================
-- 9. Closest matches (won by smallest margin) -- "thrillers"
-- =====================================================================
SELECT match_id, season, team1, team2, winner, result, result_margin, venue
FROM matches
WHERE (result = 'runs' AND result_margin <= 5)
   OR (result = 'wickets' AND result_margin <= 1)
ORDER BY result_margin ASC;


-- =====================================================================
-- 10. Head-to-head record between two specific teams (edit team names to check any rivalry)
-- =====================================================================
SELECT
    winner,
    COUNT(*) AS wins
FROM matches
WHERE (team1 = 'Mumbai Indians' AND team2 = 'Chennai Super Kings')
   OR (team1 = 'Chennai Super Kings' AND team2 = 'Mumbai Indians')
GROUP BY winner;


-- =====================================================================
-- 11. Batter strike rate leaders (min. 500 balls faced, excluding wides)
-- =====================================================================
SELECT
    batter,
    SUM(batsman_runs)                                            AS runs,
    COUNT(*)                                                     AS balls_faced,
    ROUND(SUM(batsman_runs) * 100.0 / COUNT(*), 2)               AS strike_rate
FROM deliveries
WHERE extras_type != 'wides' OR extras_type IS NULL
GROUP BY batter
HAVING COUNT(*) >= 500
ORDER BY strike_rate DESC
LIMIT 10;


-- =====================================================================
-- 12. Bowler economy rate leaders (min. 500 balls bowled)
-- =====================================================================
SELECT
    bowler,
    SUM(total_runs)                                              AS runs_conceded,
    COUNT(*)                                                     AS balls_bowled,
    ROUND(SUM(total_runs) * 1.0 / (COUNT(*) / 6.0), 2)           AS economy_rate
FROM deliveries
GROUP BY bowler
HAVING COUNT(*) >= 500
ORDER BY economy_rate ASC
LIMIT 10;


-- =====================================================================
-- 13. Super Over matches -- the rarest, highest-drama games
-- =====================================================================
SELECT match_id, season, team1, team2, winner, venue, date
FROM matches
WHERE super_over = 'Y'
ORDER BY date;


-- =====================================================================
-- 14. Matches decided under Duckworth-Lewis (D/L) method, by season
-- =====================================================================
SELECT season, COUNT(*) AS dl_affected_matches
FROM matches
WHERE method = 'D/L'
GROUP BY season
ORDER BY season;


-- =====================================================================
-- 15. Finals results -- who has won the trophy each season
-- =====================================================================
SELECT season, team1, team2, winner, venue, player_of_match
FROM matches
WHERE match_type = 'Final'
ORDER BY season;

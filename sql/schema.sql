-- schema.sql
-- Table definitions for the IPL Analytics database (real dataset: 2008-2024).

CREATE TABLE IF NOT EXISTS matches (
    match_id         INTEGER PRIMARY KEY,
    season           INTEGER NOT NULL,
    date             TEXT NOT NULL,
    city             TEXT NOT NULL,
    venue            TEXT NOT NULL,
    match_type       TEXT,                 -- League / Qualifier / Eliminator / Final
    team1            TEXT NOT NULL,
    team2            TEXT NOT NULL,
    toss_winner      TEXT NOT NULL,
    toss_decision    TEXT CHECK (toss_decision IN ('bat', 'field')),
    winner           TEXT,                 -- NULL for 'no result' matches
    result           TEXT CHECK (result IN ('runs', 'wickets', 'tie', 'no result')),
    result_margin    INTEGER,
    super_over       TEXT CHECK (super_over IN ('Y', 'N')),
    method           TEXT,                 -- 'D/L' if Duckworth-Lewis affected, else 'Standard'
    target_runs      INTEGER,
    target_overs     REAL,
    player_of_match  TEXT
);

CREATE TABLE IF NOT EXISTS deliveries (
    match_id          INTEGER NOT NULL,
    inning            INTEGER NOT NULL,
    batting_team      TEXT NOT NULL,
    bowling_team      TEXT NOT NULL,
    over              INTEGER NOT NULL,
    ball              INTEGER NOT NULL,
    batter            TEXT NOT NULL,
    bowler            TEXT NOT NULL,
    non_striker       TEXT,
    batsman_runs      INTEGER NOT NULL,
    extra_runs        INTEGER NOT NULL,
    extras_type       TEXT,               -- '' if no extra; wides/byes/legbyes/noballs/penalty
    total_runs        INTEGER NOT NULL,
    is_wicket         INTEGER NOT NULL,
    dismissal_kind    TEXT,
    player_dismissed  TEXT,
    fielder           TEXT,
    FOREIGN KEY (match_id) REFERENCES matches(match_id)
);

CREATE INDEX IF NOT EXISTS idx_deliveries_match  ON deliveries(match_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_batter ON deliveries(batter);
CREATE INDEX IF NOT EXISTS idx_deliveries_bowler ON deliveries(bowler);
CREATE INDEX IF NOT EXISTS idx_matches_season    ON matches(season);

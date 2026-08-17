"""
export_for_powerbi.py
----------------------
Builds a small set of clean, pre-aggregated CSVs that are easy to import
directly into Power BI (Get Data > Text/CSV), so you don't have to write
DAX for every basic aggregation. Power BI can then add its own DAX measures
on top (see powerbi/README.md) for interactive slicing.

Outputs written to ../powerbi/:
  - batter_summary.csv      (pre-aggregated batting stats per player)
  - bowler_summary.csv      (pre-aggregated bowling stats per player)
  - team_season_summary.csv (team performance per season)

The fact/dimension tables (fact_deliveries, dim_matches) are NOT duplicated
here -- import them straight from ../data/deliveries.csv and ../data/matches.csv
in Power BI to keep the repo lean. See ../powerbi/README.md.
"""

import sqlite3
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "data" / "ipl.db"
OUT_DIR = BASE / "powerbi"
OUT_DIR.mkdir(exist_ok=True)

conn = sqlite3.connect(DB_PATH)

# Pre-aggregated batter summary
batter_summary = pd.read_sql("""
    SELECT
        batter,
        SUM(batsman_runs) AS total_runs,
        COUNT(DISTINCT match_id) AS innings_played,
        SUM(CASE WHEN batsman_runs = 4 THEN 1 ELSE 0 END) AS fours,
        SUM(CASE WHEN batsman_runs = 6 THEN 1 ELSE 0 END) AS sixes,
        ROUND(SUM(batsman_runs) * 100.0 / COUNT(*), 2) AS strike_rate
    FROM deliveries
    GROUP BY batter
    ORDER BY total_runs DESC
""", conn)
batter_summary.to_csv(OUT_DIR / "batter_summary.csv", index=False)

# Pre-aggregated bowler summary (bowler-credited wickets only)
bowler_summary = pd.read_sql("""
    SELECT
        bowler,
        SUM(CASE WHEN dismissal_kind NOT IN ('run out','retired hurt','retired out','obstructing the field')
                       OR dismissal_kind = '' THEN is_wicket ELSE 0 END) AS total_wickets,
        SUM(total_runs) AS runs_conceded,
        COUNT(*) AS balls_bowled,
        ROUND(SUM(total_runs) * 1.0 / (COUNT(*)/6.0), 2) AS economy_rate
    FROM deliveries
    GROUP BY bowler
    ORDER BY total_wickets DESC
""", conn)
bowler_summary.to_csv(OUT_DIR / "bowler_summary.csv", index=False)

# Team performance per season
team_season = pd.read_sql("""
    SELECT season, winner AS team, COUNT(*) AS wins
    FROM matches
    WHERE winner IS NOT NULL
    GROUP BY season, winner
    ORDER BY season, wins DESC
""", conn)
team_season.to_csv(OUT_DIR / "team_season_summary.csv", index=False)

conn.close()
print("Power BI-ready CSVs exported to:", OUT_DIR)
for f in sorted(OUT_DIR.glob("*.csv")):
    print(" -", f.name)

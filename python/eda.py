"""
eda.py
------
Exploratory Data Analysis on the real IPL dataset (2008-2024).
Reads directly from the SQLite database (ipl.db) and saves chart images to
eda_charts/ for quick visual sanity-checks before building the Power BI
dashboard.
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "data" / "ipl.db"
OUT_DIR = BASE / "python" / "eda_charts"
OUT_DIR.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid")
conn = sqlite3.connect(DB_PATH)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT_DIR / name, dpi=150)
    plt.close(fig)
    print(f"Saved {name}")


# 1. Matches per season
df = pd.read_sql("SELECT season, COUNT(*) AS matches FROM matches GROUP BY season", conn)
fig, ax = plt.subplots(figsize=(11, 5))
sns.barplot(data=df, x="season", y="matches", ax=ax, color="#1f77b4")
ax.set_title("IPL Matches Played per Season (2008-2024)")
ax.set_xlabel("Season")
ax.set_ylabel("Matches")
plt.xticks(rotation=45)
save(fig, "01_matches_per_season.png")

# 2. Team total wins
df = pd.read_sql("SELECT winner, COUNT(*) AS wins FROM matches WHERE winner IS NOT NULL GROUP BY winner ORDER BY wins DESC", conn)
fig, ax = plt.subplots(figsize=(10, 7))
sns.barplot(data=df, y="winner", x="wins", ax=ax, hue="winner", legend=False, palette="viridis")
ax.set_title("Total Wins by Team (All Seasons, 2008-2024)")
ax.set_xlabel("Wins")
ax.set_ylabel("")
save(fig, "02_team_wins.png")

# 3. Top 10 run scorers
df = pd.read_sql("""
    SELECT batter, SUM(batsman_runs) AS runs
    FROM deliveries GROUP BY batter ORDER BY runs DESC LIMIT 10
""", conn)
fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(data=df, y="batter", x="runs", ax=ax, hue="batter", legend=False, palette="rocket")
ax.set_title("Top 10 Run Scorers (2008-2024)")
ax.set_xlabel("Total Runs")
ax.set_ylabel("")
save(fig, "03_top_run_scorers.png")

# 4. Top 10 wicket takers (bowler-credited only)
df = pd.read_sql("""
    SELECT bowler,
        SUM(CASE WHEN dismissal_kind NOT IN ('run out','retired hurt','retired out','obstructing the field')
                       OR dismissal_kind = '' THEN is_wicket ELSE 0 END) AS wickets
    FROM deliveries GROUP BY bowler ORDER BY wickets DESC LIMIT 10
""", conn)
fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(data=df, y="bowler", x="wickets", ax=ax, hue="bowler", legend=False, palette="mako")
ax.set_title("Top 10 Wicket Takers (2008-2024)")
ax.set_xlabel("Total Wickets")
ax.set_ylabel("")
save(fig, "04_top_wicket_takers.png")

# 5. Toss decision trend over seasons
df = pd.read_sql("SELECT season, toss_decision, COUNT(*) AS n FROM matches GROUP BY season, toss_decision", conn)
pivot = df.pivot(index="season", columns="toss_decision", values="n").fillna(0)
fig, ax = plt.subplots(figsize=(11, 5))
pivot.plot(kind="bar", stacked=True, ax=ax, color=["#ff7f0e", "#2ca02c"])
ax.set_title("Toss Decision Trend by Season (Bat First vs Field First)")
ax.set_xlabel("Season")
ax.set_ylabel("Matches")
save(fig, "05_toss_decision_trend.png")

# 6. Average first innings score by venue (min 10 matches hosted)
df = pd.read_sql("""
    SELECT m.venue,
           COUNT(DISTINCT m.match_id) AS matches,
           AVG(inns.score) AS avg_score
    FROM matches m
    JOIN (SELECT match_id, SUM(total_runs) AS score FROM deliveries WHERE inning = 1 GROUP BY match_id) inns
      ON inns.match_id = m.match_id
    GROUP BY m.venue
    HAVING matches >= 10
    ORDER BY avg_score DESC
    LIMIT 15
""", conn)
fig, ax = plt.subplots(figsize=(10, 7))
sns.barplot(data=df, y="venue", x="avg_score", ax=ax, hue="venue", legend=False, palette="flare")
ax.set_title("Average 1st Innings Score by Venue (min. 10 matches hosted)")
ax.set_xlabel("Average Score")
ax.set_ylabel("")
save(fig, "06_venue_avg_score.png")

conn.close()
print("\nAll charts saved to:", OUT_DIR)

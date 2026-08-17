"""
load_to_sql.py
---------------
Loads the cleaned matches.csv and deliveries.csv into a SQLite database (ipl.db).

SQLite is used so the whole project stays self-contained and portable for GitHub
(no server setup needed for a reviewer to run it). The same schema/queries work
unchanged against MySQL/PostgreSQL/SQL Server if you prefer a "real" RDBMS --
just swap the connection in this script.
"""

import sqlite3
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "data" / "ipl.db"

def main():
    matches = pd.read_csv(BASE / "data" / "matches.csv")
    deliveries = pd.read_csv(BASE / "data" / "deliveries.csv")

    conn = sqlite3.connect(DB_PATH)

    matches.to_sql("matches", conn, if_exists="replace", index=False)
    deliveries.to_sql("deliveries", conn, if_exists="replace", index=False)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_deliveries_match ON deliveries(match_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_deliveries_batter ON deliveries(batter)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_deliveries_bowler ON deliveries(bowler)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_season ON matches(season)")
    conn.commit()

    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f"Loaded database at: {DB_PATH}")
    print("Tables:", [t[0] for t in tables])
    conn.close()


if __name__ == "__main__":
    main()

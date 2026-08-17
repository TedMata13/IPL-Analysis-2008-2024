"""
clean_data.py
--------------
Cleans the raw IPL dataset and writes analysis-ready versions to
data/matches.csv and data/deliveries.csv.

Source data: "IPL Complete Dataset (2008-2024)" by Patrick B, Kaggle.
https://www.kaggle.com/datasets/patrickb1912/ipl-complete-dataset-20082020
Download matches.csv and deliveries.csv from the link above and place them
at data/raw_matches.csv and data/raw_deliveries.csv before running this script.

This is real historical data, not synthetic, so it required actual cleaning
before it was analysis-ready. Real-world data issues handled here:
  1. Inconsistent season labels ("2007/08", "2009/10", "2020/21") -> a single
     clean `season` year, derived from the match date (unambiguous).
  2. Franchise renames over time (same owner, new name) standardized to the
     CURRENT name, e.g. "Delhi Daredevils" -> "Delhi Capitals". Genuinely
     defunct/different-ownership franchises (Deccan Chargers, Pune Warriors,
     Gujarat Lions, Kochi Tuskers Kerala) are left as their own distinct teams
     -- merging them into a "successor" franchise would misrepresent history.
  3. Missing `city` for the 2014 UAE-leg matches, backfilled from `venue`.
  4. Free-text "NA" strings (a raw-CSV artifact) converted to proper NaN.
  5. Typo/spelling variant "Rising Pune Supergiant" vs "...Supergiants" merged.
  6. Same physical venue renamed/re-sponsored over time (e.g. "Feroz Shah
     Kotla" -> "Arun Jaitley Stadium" in 2018, "Sardar Patel Stadium" ->
     "Narendra Modi Stadium" in 2021) standardized to the current name.
  7. City spelling "Bangalore" -> "Bengaluru" standardized alongside the venue rename.
  8. Column selection/renaming kept close to the original so real IPL data
     drop-in replacement stays simple.
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RAW_MATCHES = BASE / "data" / "raw_matches.csv"
RAW_DELIVERIES = BASE / "data" / "raw_deliveries.csv"
OUT_MATCHES = BASE / "data" / "matches.csv"
OUT_DELIVERIES = BASE / "data" / "deliveries.csv"

# Same-owner, official rename only -- NOT a merge of different franchises
TEAM_RENAME_MAP = {
    "Delhi Daredevils": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings",
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Rising Pune Supergiant": "Rising Pune Supergiants",  # spelling variant, same team
}

# Same physical ground, renamed/re-sponsored over the years -- standardized to
# the current/most-recent name. Confirmed via matching city + non-overlapping
# season ranges (e.g. Feroz Shah Kotla was renamed Arun Jaitley Stadium in 2018).
VENUE_RENAME_MAP = {
    "M.Chinnaswamy Stadium": "M Chinnaswamy Stadium",
    "Punjab Cricket Association Stadium": "Punjab Cricket Association IS Bindra Stadium",
    "Feroz Shah Kotla": "Arun Jaitley Stadium",
    "Sardar Patel Stadium": "Narendra Modi Stadium",
    "Subrata Roy Sahara Stadium": "Maharashtra Cricket Association Stadium",
    "Sheikh Zayed Stadium": "Zayed Cricket Stadium",
}

# City spelling likewise changed alongside the Bangalore -> Bengaluru rename
CITY_RENAME_MAP = {
    "Bangalore": "Bengaluru",
}

# Backfill missing city from venue for the 2014 UAE leg (played outside India)
VENUE_TO_CITY = {
    "Sharjah Cricket Stadium": "Sharjah",
    "Dubai International Cricket Stadium": "Dubai",
}


def standardize_teams(series: pd.Series) -> pd.Series:
    return series.replace(TEAM_RENAME_MAP)


def clean_matches() -> pd.DataFrame:
    m = pd.read_csv(RAW_MATCHES, na_values=["NA", ""])

    m["date"] = pd.to_datetime(m["date"])
    m["season"] = m["date"].dt.year  # unambiguous replacement for "2007/08" etc.

    for col in ["team1", "team2", "toss_winner", "winner"]:
        m[col] = standardize_teams(m[col])

    m["city"] = m["city"].replace(CITY_RENAME_MAP)
    m["city"] = m["city"].fillna(m["venue"].map(VENUE_TO_CITY))
    m["city"] = m["city"].fillna("Unknown")

    # Clean venue text FIRST (some raw entries embed ", <city>", even doubled
    # up in a few rows, e.g. "..., Mohali, Chandigarh") -- must happen before
    # the rename map below, since the rename keys are the bare stadium name
    # and won't exact-match a string that still has a city suffix attached.
    m["venue"] = m["venue"].str.split(",").str[0].str.strip()
    m["venue"] = m["venue"].replace(VENUE_RENAME_MAP)

    m["result_margin"] = m["result_margin"].fillna(0).astype(int)
    m["super_over"] = m["super_over"].fillna("N")
    m["method"] = m["method"].fillna("Standard")  # 'D/L' -> Duckworth-Lewis affected

    m = m.rename(columns={"id": "match_id"})

    cols = [
        "match_id", "season", "date", "city", "venue", "match_type",
        "team1", "team2", "toss_winner", "toss_decision",
        "winner", "result", "result_margin", "super_over", "method",
        "target_runs", "target_overs", "player_of_match",
    ]
    return m[cols].sort_values("match_id").reset_index(drop=True)


def clean_deliveries(valid_match_ids: set) -> pd.DataFrame:
    d = pd.read_csv(RAW_DELIVERIES, na_values=["NA", ""])

    d = d[d["match_id"].isin(valid_match_ids)]

    for col in ["batting_team", "bowling_team"]:
        d[col] = standardize_teams(d[col])

    d["extras_type"] = d["extras_type"].fillna("")
    d["dismissal_kind"] = d["dismissal_kind"].fillna("")
    d["player_dismissed"] = d["player_dismissed"].fillna("")
    d["fielder"] = d["fielder"].fillna("")

    cols = [
        "match_id", "inning", "batting_team", "bowling_team", "over", "ball",
        "batter", "bowler", "non_striker", "batsman_runs", "extra_runs",
        "extras_type", "total_runs", "is_wicket", "dismissal_kind",
        "player_dismissed", "fielder",
    ]
    return d[cols].reset_index(drop=True)


def main():
    matches = clean_matches()
    deliveries = clean_deliveries(set(matches["match_id"]))

    matches.to_csv(OUT_MATCHES, index=False)
    deliveries.to_csv(OUT_DELIVERIES, index=False)

    print(f"matches.csv     -> {len(matches):,} rows (from {RAW_MATCHES.name})")
    print(f"deliveries.csv  -> {len(deliveries):,} rows (from {RAW_DELIVERIES.name})")
    print(f"Seasons: {matches['season'].min()}–{matches['season'].max()}")
    print(f"Teams (post-standardization): {matches['team1'].nunique() + 1} unique franchises")


if __name__ == "__main__":
    main()

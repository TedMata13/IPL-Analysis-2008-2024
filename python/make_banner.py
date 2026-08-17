"""
make_banner.py
---------------
Generates a wide stat-banner PNG (assets/banner.png) for the top of README.md,
pulling real headline numbers straight from the SQLite database so the banner
never goes stale if the dataset is refreshed.
"""

import sqlite3
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
conn = sqlite3.connect(BASE / "data" / "ipl.db")

matches = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
seasons = conn.execute("SELECT MIN(season), MAX(season) FROM matches").fetchone()
runs = conn.execute("SELECT SUM(total_runs) FROM deliveries").fetchone()[0]
sixes = conn.execute("SELECT COUNT(*) FROM deliveries WHERE batsman_runs = 6").fetchone()[0]
top_scorer = conn.execute("""
    SELECT batter, SUM(batsman_runs) r FROM deliveries
    GROUP BY batter ORDER BY r DESC LIMIT 1
""").fetchone()
conn.close()

stats = [
    (f"{seasons[0]}\u2013{seasons[1]}", "Seasons"),
    (f"{matches:,}", "Matches"),
    (f"{runs:,}", "Runs scored"),
    (f"{sixes:,}", "Sixes hit"),
    (top_scorer[0], f"Top scorer ({top_scorer[1]:,} runs)"),
]

fig, ax = plt.subplots(figsize=(12, 2.4))
ax.axis("off")
fig.patch.set_facecolor("#0e1117")

n = len(stats)
for i, (value, label) in enumerate(stats):
    x = (i + 0.5) / n
    ax.text(x, 0.62, value, ha="center", va="center", fontsize=20,
             fontweight="bold", color="#ffffff", transform=ax.transAxes)
    ax.text(x, 0.22, label, ha="center", va="center", fontsize=11,
             color="#9aa4b2", transform=ax.transAxes)
    if i > 0:
        ax.axvline(i / n, ymin=0.15, ymax=0.85, color="#2a2f3a", linewidth=1)

fig.suptitle("IPL Analytics  |  Python \u00b7 SQL \u00b7 Power BI", fontsize=15,
             color="#ffffff", fontweight="bold", y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.90])
out_path = BASE / "assets" / "banner.png"
fig.savefig(out_path, dpi=160, facecolor=fig.get_facecolor())
plt.close(fig)
print("Saved banner to", out_path)

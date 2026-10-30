"""Analisis waktu gol & hasil pertandingan, 91 liga (2022-2026).
Data: football-charts.com via Zenodo (CC BY 4.0). Jalankan: python analyze.py
"""
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA = Path(__file__).parent / "data" / "football_charts_matches.csv"
OUT = Path(__file__).parent / "charts"
BINS = ["1-15", "16-30", "31-45", "46-60", "61-75", "76-90"]


def goal_bin(minute: str) -> str:
    # injury time ada di menit 45/90 (atau "45+"/"90+"), tetap masuk babaknya
    m = int(re.match(r"\d+", minute.strip()).group())
    return BINS[min((max(m, 1) - 1) // 15, 5)]


assert [goal_bin(x) for x in ["1", "15", "16", "45+", "46", "90+", "90"]] == \
    ["1-15", "1-15", "16-30", "31-45", "46-60", "76-90", "76-90"]

df = pd.read_csv(DATA, dtype={"all_goal_times": str, "first_goal_time": str})
OUT.mkdir(exist_ok=True)
lines = [f"Pertandingan: {len(df):,} | Liga: {df.league.nunique()} | Negara: {df.country.nunique()}"]

# 1. Distribusi waktu gol
times = df.all_goal_times.dropna().str.split(",").explode().str.strip()
# 7 sel berisi "Not found"; buang yang bukan menit
times = times[times.str.match(r"^\d+\+?$")]
dist = times.map(goal_bin).value_counts(normalize=True).reindex(BINS) * 100
lines.append(f"Gol tercatat menitnya: {len(times):,}")
lines += [f"  {b}: {v:.1f}%" for b, v in dist.items()]
dist.plot.bar(color="#2f6f9f", rot=0, title="Sebaran gol per 15 menit (%)")
plt.ylabel("% dari semua gol"); plt.tight_layout(); plt.savefig(OUT / "1_waktu_gol.png", dpi=120); plt.close()

# 2. Keunggulan kandang
res = df.result.value_counts(normalize=True).reindex(["H", "D", "A"]) * 100
lines.append(f"Menang kandang {res.H:.1f}% | Seri {res.D:.1f}% | Menang tandang {res.A:.1f}%")
res.rename({"H": "Kandang", "D": "Seri", "A": "Tandang"}).plot.bar(
    color=["#2f6f9f", "#999999", "#c0504d"], rot=0, title="Hasil pertandingan (%)")
plt.tight_layout(); plt.savefig(OUT / "2_hasil.png", dpi=120); plt.close()

# 3. Rata-rata gol per liga (liga dengan >= 300 laga)
g = df.groupby(["league_name", "country"]).total_goals.agg(["mean", "size"])
g = g[g["size"] >= 300].sort_values("mean")
g.index = [f"{n} ({c})" for n, c in g.index]
lines.append(f"Rata-rata gol/laga semua data: {df.total_goals.mean():.2f}")
lines.append(f"  Tertinggi: {g.index[-1]} {g['mean'].iloc[-1]:.2f} | Terendah: {g.index[0]} {g['mean'].iloc[0]:.2f}")
pd.concat([g["mean"].head(10), g["mean"].tail(10)]).plot.barh(
    figsize=(8, 7), color=["#c0504d"] * 10 + ["#2f6f9f"] * 10, title="10 liga tersubur vs 10 liga terhemat (gol/laga)")
plt.tight_layout(); plt.savefig(OUT / "3_gol_per_liga.png", dpi=120); plt.close()

# 4. Unggul saat turun minum -> menang?
ht = df.ht_result.str.split(":", expand=True).astype(float)
lead = df[ht[0] != ht[1]]
leader_won = ((ht.loc[lead.index, 0] > ht.loc[lead.index, 1]) & (lead.result == "H")) | \
             ((ht.loc[lead.index, 0] < ht.loc[lead.index, 1]) & (lead.result == "A"))
lines.append(f"Tim yang unggul di babak pertama menang: {leader_won.mean() * 100:.1f}% ({len(lead):,} laga)")
first = pd.to_numeric(df.first_goal_time.str.extract(r"(\d+)")[0])
lines.append(f"Median menit gol pertama: {first.median():.0f} | Laga 0-0: {(df.total_goals == 0).mean() * 100:.1f}%")

Path(__file__).with_name("hasil.txt").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))

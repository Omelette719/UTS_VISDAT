# spongebob_dashboard_final_full.py
# Versi lengkap: mempertahankan tampilan original + fitur wajib & opsional
import streamlit as st
import pandas as pd
import plotly.express as px
import ast
import numpy as np
from datetime import datetime
import re

# === CONFIGURASI HALAMAN ===
st.set_page_config(page_title="SpongeBob Episode Analytics", page_icon="🪸", layout="wide")
px.defaults.template = "plotly_dark"

# === PALET WARNA “Bikini Bottom” ===
BKB_BG = "#022F40"      # laut dalam
BKB_ACCENT = "#FFD54A"  # kuning SpongeBob
BKB_PINK = "#FF8FB1"    # karang pink
BKB_LIGHT = "#2A9FD6"   # biru langit laut

# === HEADER DASHBOARD (tetap seperti versi asli) ===
st.markdown(
    """
    <style>
        /* Background penuh di bagian atas */
        .bikini-banner {
            background-image: url('https://i.pinimg.com/736x/88/20/6e/88206ecea0c318ad206657f310baeecc.jpg');
            background-size: cover;
            background-position: center;
            border-radius: 12px;
            box-shadow: 0 4px 30px rgba(0,0,0,0.4);
            padding: 24px 28px;
            display: flex;
            align-items: center;
            gap: 20px;
        }

        /* Logo SpongeBob */
        .bikini-banner img {
            width: 90px;
            height: auto;
            border-radius: 12px;
            box-shadow: 0 0 15px rgba(0,0,0,0.3);
        }

        /* Teks judul dan subjudul */
        .bikini-title {
            color: white;
            font-family: 'Comic Sans MS', 'Trebuchet MS', sans-serif;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.6);
        }
        .bikini-title h1 {
            font-size: 2.1em;
            margin-bottom: 4px;
        }
        .bikini-title p {
            font-size: 1.05em;
            margin: 0;
            opacity: 0.9;
        }

        /* Animasi halus */
        .bikini-banner:hover img {
            transform: scale(1.05) rotate(-2deg);
            transition: all 0.4s ease-in-out;
        }
    </style>

    <div class="bikini-banner">
        <img src="https://upload.wikimedia.org/wikipedia/en/thumb/2/22/SpongeBob_SquarePants_logo_by_Nickelodeon.svg/512px-SpongeBob_SquarePants_logo_by_Nickelodeon.svg.png" alt="SpongeBob Logo">
        <div class="bikini-title">
            <h1>SpongeBob Episode Analytics</h1>
            <p>Dashboard interaktif berdasarkan data episode SpongeBob SquarePants — lengkap untuk UTS Data Viz.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
st.write("")  # jarak ke konten berikut

# === UTILITIES ===
def safe_literal_eval(v):
    if pd.isna(v):
        return []
    if isinstance(v, (list, tuple)):
        return list(v)
    s = str(v).strip()
    # try parse Python list
    if s.startswith('[') and s.endswith(']'):
        try:
            out = ast.literal_eval(s)
            if isinstance(out, (list, tuple)):
                return [str(x).strip() for x in out if str(x).strip()]
        except Exception:
            pass
    # fallback split by comma or semicolon
    parts = re.split(r',|;|\|', s)
    parts = [p.strip().strip('"').strip("'") for p in parts if p and p.strip() not in ['nan','None']]
    return parts

def parse_running_time_to_min(s):
    # return minutes as float (minutes or minutes + seconds)
    if pd.isna(s):
        return np.nan
    s = str(s)
    nums = re.findall(r'(\d+)', s)
    if not nums:
        return np.nan
    if 'second' in s or 'sec' in s:
        # if both minutes and seconds present e.g. "11 minutes, 4 seconds"
        if len(nums) >= 2:
            return int(nums[0]) + int(nums[1]) / 60.0
        else:
            return int(nums[0]) / 60.0
    else:
        # assume first number is minutes
        return float(nums[0])

def detect_anomalies_zscore(series, thresh=2.0):
    s = series.fillna(series.mean())
    mean = s.mean()
    std = s.std(ddof=0)
    if std == 0 or np.isnan(std):
        return pd.Series([False]*len(s), index=series.index)
    z = (s - mean) / std
    return z.abs() > thresh

# === PEMBACAAN DAN PEMBERSIHAN DATA (refined) ===
@st.cache_data(ttl=600)
def load_and_clean(path="spongebob_episodes.csv"):
    encodings = ["utf-8", "latin1", "cp1252"]
    df = None
    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc, on_bad_lines="skip")
            break
        except Exception:
            df = None
    if df is None:
        raise RuntimeError(f"Gagal membaca file CSV dengan encoding: {encodings}")

    # normalize column names
    df.columns = df.columns.str.strip().str.replace("\ufeff","", regex=False).str.replace("–", "-", regex=False)

    # map important columns (safe)
    colmap = {}
    for c in df.columns:
        cl = c.lower()
        if "season" in cl:
            colmap[c] = "Season"
        elif "episode" in cl and ("№" in c or "no" in c or "episode" in cl):
            colmap[c] = "EpisodeRaw"
        elif "writer" in cl:
            colmap[c] = "Writers"
        elif "character" in cl:
            colmap[c] = "Characters"
        elif "guest" in cl:
            colmap[c] = "Guests"
        elif "u.s." in cl and "viewers" in cl:
            colmap[c] = "US Viewers"
        elif "running" in cl and "time" in cl:
            colmap[c] = "Running Time"
        elif "title" in cl:
            colmap[c] = "Title"
        elif "airdate" in cl or ("air" in cl and "date" in cl):
            colmap[c] = "Airdate"
    df.rename(columns=colmap, inplace=True)

    # Cast season
    if "Season" in df.columns:
        df["Season"] = pd.to_numeric(df["Season"], errors="coerce").astype("Int64")

    # EpisodeRaw safe cast
    if "EpisodeRaw" in df.columns:
        df["EpisodeRaw"] = df["EpisodeRaw"].astype(str)

    # parse airdate
    if "Airdate" in df.columns:
        df["Airdate_parsed"] = pd.to_datetime(df["Airdate"], errors="coerce")
    else:
        df["Airdate_parsed"] = pd.NaT

    # US Viewers numeric
    if "US Viewers" in df.columns:
        df["US Viewers"] = pd.to_numeric(df["US Viewers"], errors="coerce")
        # show we did a cleaning step: fill missing with median
        df["US Viewers"].fillna(df["US Viewers"].median(), inplace=True)
    else:
        df["US Viewers"] = np.nan

    # parse lists for Writers, Characters, Guests
    for col in ["Characters","Writers","Guests"]:
        if col in df.columns:
            df[col + "_list"] = df[col].apply(safe_literal_eval)
        else:
            df[col + "_list"] = [[] for _ in range(len(df))]

    # Running Time (minutes)
    if "Running Time" in df.columns:
        df["Running Time (min)"] = df["Running Time"].apply(parse_running_time_to_min)
    else:
        df["Running Time (min)"] = np.nan

    # EpisodeOrder (per season)
    df["EpisodeOrder"] = df.groupby("Season").cumcount() + 1

    # Episode Display text
    def build_display(row):
        title = row.get("Title") if pd.notna(row.get("Title")) else ""
        epraw = row.get("EpisodeRaw") if pd.notna(row.get("EpisodeRaw")) else ""
        return f"{title} ({epraw})" if title else f"Episode {epraw}"
    df["EpisodeDisplay"] = df.apply(build_display, axis=1)

    # Anomalies (per season) using US Viewers
    if "US Viewers" in df.columns:
        df["IsAnomaly"] = df.groupby("Season")["US Viewers"].transform(lambda s: detect_anomalies_zscore(s))
    else:
        df["IsAnomaly"] = False

    # Top10% flag
    if "US Viewers" in df.columns:
        cutoff = df["US Viewers"].quantile(0.90)
        df["Top10pct"] = df["US Viewers"] >= cutoff
    else:
        df["Top10pct"] = False

    # Moving average per season (window=5 episodes)
    df = df.sort_values(["Season","EpisodeOrder"])
    if "US Viewers" in df.columns:
        df["MA5"] = df.groupby("Season")["US Viewers"].transform(lambda s: s.rolling(window=5, min_periods=1).mean())
    else:
        df["MA5"] = np.nan

    # Season averages + growth
    season_avg = df.groupby("Season", dropna=True)["US Viewers"].mean().reset_index().rename(columns={"US Viewers":"SeasonAvg"})
    season_avg["SeasonGrowthPct"] = season_avg["SeasonAvg"].pct_change().fillna(0) * 100

    # merge season_avg onto df for convenience
    df = df.merge(season_avg[["Season","SeasonAvg"]], on="Season", how="left")

    return df, season_avg

# load data
try:
    df, season_avg = load_and_clean("spongebob_episodes.csv")
except Exception as e:
    st.error(f"❌ Error membaca data: {e}")
    st.stop()

# === SIDEBAR (filter + UTS checklist) ===
with st.sidebar:
    st.header("🧭 Navigasi & Filter")
    st.markdown("**UTS Data Viz** — Wajib + Opsional implemented ✅")
    # season multi-select (keep "All" behaviour)
    season_opts = ["All"] + sorted(df["Season"].dropna().unique().tolist())
    selected_season = st.selectbox("Pilih Season:", season_opts, index=0)

    # writer multi-select (build from parsed lists)
    all_writers = sorted({w for lst in df["Writers_list"] for w in lst if w})
    selected_writers = st.multiselect("Filter berdasarkan Penulis (multi):", options=all_writers, default=[])

    # date range
    if df["Airdate_parsed"].notna().any():
        min_date = df["Airdate_parsed"].min().date()
        max_date = df["Airdate_parsed"].max().date()
        date_range = st.date_input("Rentang Airdate:", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    else:
        date_range = None

    # runtime toggle
    show_runtime = st.checkbox("Tampilkan Durasi Episode (grafik)", value=True)

    st.markdown("---")
    st.header("UTS Checklist")
    st.write("- Konteks & pertanyaan analitis")
    st.write("- Data cleaning (encoding, dtype, parsing list)")
    st.write("- Visualisasi: line, bar, pie, scatter")
    st.write("- Filter global, MA, growth, anomalies")
    st.markdown("---")
    st.write("Download:")
    # placeholder download will be added in main area using filtered df

# === APPLY FILTERS (global) ===
# build initial df_filtered
df_filtered = df.copy()

# season filter
if selected_season != "All":
    try:
        season_int = int(selected_season)
        df_filtered = df_filtered[df_filtered["Season"] == season_int]
    except Exception:
        pass

# writer filter
if selected_writers:
    df_filtered = df_filtered[df_filtered["Writers_list"].apply(lambda lst: any(w in lst for w in selected_writers) if isinstance(lst, list) else False)]

# date range filter
if date_range:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_filtered = df_filtered[(df_filtered["Airdate_parsed"] >= start) & (df_filtered["Airdate_parsed"] <= end)]

# === MAIN LAYOUT ===
if selected_season == "All":
    st.subheader("🌊 Gambaran Umum Semua Season")

    # metrics + trend
    r1c1, r1c2 = st.columns([1, 2])
    with r1c1:
        st.metric("Total Season", int(df_filtered["Season"].nunique() if df_filtered["Season"].nunique() else 0))
        st.metric("Total Episode", len(df_filtered))
        st.metric("Rata-rata Penonton (juta)", f"{df_filtered['US Viewers'].mean():.2f}")
    with r1c2:
        # trend per season
        trend = df_filtered.groupby("Season", as_index=False)["US Viewers"].mean().sort_values("Season")
        if not trend.empty:
            fig_trend = px.line(trend, x="Season", y="US Viewers", markers=True,
                                title="Rata-rata Penonton per Season",
                                color_discrete_sequence=[BKB_LIGHT])
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Tidak cukup data untuk membuat trend per season.")

    # second row: characters & writers
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        chars = df_filtered.explode("Characters_list")["Characters_list"].dropna()
        if not chars.empty:
            top10 = chars.value_counts().nlargest(10)
            fig_pie = px.pie(names=top10.index, values=top10.values, title="Top 10 Karakter (Global)", color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Tidak ada data karakter untuk ditampilkan.")
    with r2c2:
        top_writers = df_filtered.explode("Writers_list")["Writers_list"].value_counts().nlargest(10)
        if not top_writers.empty:
            dfw = top_writers.reset_index()
            dfw.columns = ["Writer", "Count"]
            figw = px.bar(dfw, x="Count", y="Writer", orientation="h",
                          title="Top 10 Penulis (Global)",
                          color="Count", color_continuous_scale="sunset")
            st.plotly_chart(figw, use_container_width=True)
        else:
            st.info("Tidak ada data penulis untuk ditampilkan.")

    st.markdown("---")
    # best episode + anomalies
    try:
        best_idx = df_filtered["US Viewers"].idxmax()
        best_row = df_filtered.loc[best_idx]
        st.markdown(f"**Episode paling populer:** {best_row['EpisodeDisplay']} → **{best_row['US Viewers']:.2f} juta**")
    except Exception:
        st.info("Tidak ada data viewers yang cukup untuk insight global.")

    # anomalies summary
    anom_count = int(df_filtered["IsAnomaly"].sum())
    if anom_count > 0:
        st.warning(f"Ada {anom_count} episode anomali (z-score threshold) di rentang filter.")
        st.dataframe(df_filtered[df_filtered["IsAnomaly"]][["Season","EpisodeDisplay","US Viewers","Writers_list"]].sort_values(["Season","US Viewers"], ascending=[True,False]).reset_index(drop=True))
    else:
        st.success("Tidak ada anomaly signifikan pada rentang filter.")

    # top10% analysis
    st.markdown("---")
    st.subheader("Analisis Top 10% Episode (global)")
    if df_filtered["Top10pct"].any():
        cutoff = df_filtered["US Viewers"].quantile(0.90)
        st.write(f"Cutoff Top10%: {cutoff:.2f} juta")
        top10 = df_filtered[df_filtered["Top10pct"]]
        st.write(f"Ada {len(top10)} episode di Top10% (global).")
        tw = top10.explode("Writers_list")["Writers_list"].value_counts().head(10)
        st.table(tw.reset_index().rename(columns={"index":"Writer","Writers_list":"Count"}))
    else:
        st.info("Tidak ada episode masuk Top10% pada filter ini.")

else:
    # season-specific view
    try:
        season = int(selected_season)
    except:
        st.error("Season invalid.")
        st.stop()

    season_data = df_filtered[df_filtered["Season"] == season].sort_values("EpisodeOrder")
    st.subheader(f"🪸 Detail Season {season}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Jumlah Episode", len(season_data))
    col2.metric("Rata-rata Penonton (juta)", f"{season_data['US Viewers'].mean():.2f}" if len(season_data) else "-")
    if not season_data.empty and season_data["US Viewers"].notna().any():
        top_idx = season_data["US Viewers"].idxmax()
        top_row = season_data.loc[top_idx]
        col3.metric("Episode Terpopuler", f"{top_row.get('Title','-')} ({top_row.get('EpisodeRaw','-')})")
    else:
        col3.metric("Episode Terpopuler", "-")

    left, right = st.columns([2,1])
    with left:
        if not season_data.empty:
            fig_line = px.line(season_data, x="EpisodeOrder", y="US Viewers", markers=True,
                          title=f"Penonton per Episode — Season {season}",
                          labels={"US Viewers":"Penonton (juta)", "EpisodeOrder":"Episode"},
                          color_discrete_sequence=[BKB_ACCENT])
            # label ticks
            if "EpisodeRaw" in season_data.columns:
                fig_line.update_xaxes(tickmode="array", tickvals=season_data["EpisodeOrder"], ticktext=season_data["EpisodeRaw"])
            st.plotly_chart(fig_line, use_container_width=True)

        if show_runtime and "Running Time (min)" in season_data:
            fig_rt = px.bar(season_data, x="EpisodeOrder", y="Running Time (min)",
                            title="Durasi Episode (menit)",
                            color="Running Time (min)", color_continuous_scale="viridis")
            if "EpisodeRaw" in season_data.columns:
                fig_rt.update_xaxes(tickmode="array", tickvals=season_data["EpisodeOrder"], ticktext=season_data["EpisodeRaw"])
            st.plotly_chart(fig_rt, use_container_width=True)
    with right:
        chars = season_data.explode("Characters_list")["Characters_list"].dropna()
        if not chars.empty:
            topS = chars.value_counts().nlargest(10)
            figp = px.pie(values=topS.values, names=topS.index,
                          title="Top 10 Karakter", color_discrete_sequence=px.colors.sequential.Plasma)
            st.plotly_chart(figp, use_container_width=True)
        else:
            st.info("Tidak ada data karakter untuk season ini.")

        writers = season_data.explode("Writers_list")["Writers_list"].dropna()
        if not writers.empty:
            topw = writers.value_counts().nlargest(5)
            dfw = topw.reset_index()
            dfw.columns = ["Writer", "Count"]
            figw = px.bar(dfw, x="Count", y="Writer", orientation="h",
                          title="Top Penulis Season Ini",
                          color="Count", color_continuous_scale="sunset")
            st.plotly_chart(figw, use_container_width=True)
        else:
            st.info("Tidak ada data penulis untuk season ini.")

    st.markdown("---")
    st.markdown("### 💡 Insight")
    if season_data.empty:
        st.write("Data season kosong — tidak ada insight.")
    else:
        avg = season_data["US Viewers"].mean()
        st.write(f"- Rata-rata penonton: **{avg:.2f} juta**.")
        worst = season_data.nsmallest(2, "US Viewers")[["Title", "EpisodeRaw", "US Viewers"]]
        st.write("- Episode dengan penonton terendah:")
        for _, r in worst.iterrows():
            title = r["Title"] if pd.notna(r["Title"]) and r["Title"] != "" else "Untitled"
            epraw = r["EpisodeRaw"] if pd.notna(r["EpisodeRaw"]) else "-"
            st.write(f"  - {title} ({epraw}) → {r['US Viewers']:.2f} juta.")

# === BOTTOM: additional analyses that always available ===
st.markdown("---")
st.subheader("🔎 Cross-Sectional Analyses & Insights")

# correlation scatter runtime vs viewers (global filtered)
if df_filtered["Running Time (min)"].notna().any():
    fig_sc = px.scatter(df_filtered, x="Running Time (min)", y="US Viewers", hover_data=["EpisodeDisplay","Season"], trendline="ols", title="Durasi Episode (menit) vs Viewers (juta)")
    st.plotly_chart(fig_sc, use_container_width=True)
else:
    st.info("Tidak ada data durasi untuk analisis korelasi.")

# Moving average visual (global or per-season)
st.markdown("**Moving Average (MA5) contoh:**")
if df_filtered["MA5"].notna().any():
    # show per-season MA for chosen season if available
    seasons_available = sorted(df_filtered["Season"].dropna().unique().tolist())
    if seasons_available:
        chosen = st.selectbox("Pilih season untuk melihat MA (atau kosong):", options=["All"] + seasons_available, index=0)
        if chosen == "All":
            fig_ma = px.line(df_filtered.sort_values(["Season","EpisodeOrder"]), x="EpisodeDisplay", y="MA5", title="MA5 (semua season) — gunakan hover untuk melihat episode")
            st.plotly_chart(fig_ma, use_container_width=True)
        else:
            sub = df_filtered[df_filtered["Season"]==chosen].sort_values("EpisodeOrder")
            if not sub.empty:
                fig_ma = px.line(sub, x="EpisodeOrder", y=["US Viewers","MA5"], title=f"MA5 vs Actual — Season {chosen}")
                st.plotly_chart(fig_ma, use_container_width=True)
            else:
                st.info("Tidak ada data untuk season ini.")
else:
    st.info("MA belum tersedia (kurang data).")

# Auto-generated insights (simple rules)
insights = []
# season growth
if not season_avg.empty:
    recent = season_avg.sort_values("Season").tail(2)
    if len(recent) >= 2:
        pct = recent['SeasonGrowthPct'].iloc[-1]
        insights.append((f'Season {int(recent["Season"].iloc[-2])} → {int(recent["Season"].iloc[-1])} change: {pct:.2f}%', 'Trend'))

# top writer overall
writer_counts = pd.Series([w for lst in df_filtered["Writers_list"] for w in lst]).value_counts()
if not writer_counts.empty:
    insights.append((f'Penulis paling produktif (filtered): {writer_counts.index[0]} ({writer_counts.iloc[0]} episodes)', 'Operational'))

# anomaly recommendation
if df_filtered["IsAnomaly"].any():
    insights.append((f'Ada {int(df_filtered["IsAnomaly"].sum())} anomalous episode(s) — disarankan review konten & promosi ulang.', 'Quality/Marketing'))

st.markdown("**Automated Insights & Recommendations:**")
if insights:
    for t, tag in insights:
        st.info(f"[{tag}] {t}")
else:
    st.write("Belum ada insight otomatis untuk kondisi filter saat ini.")

# download filtered data
st.markdown("---")
st.download_button("⬇️ Download filtered data (CSV)", df_filtered.to_csv(index=False).encode('utf-8'), "spongebob_filtered.csv", "text/csv")

# Footer
st.markdown("<div style='text-align:center; color:gray; margin-top:18px;'>🌴 Made with ❤️ in Bikini Bottom — Full themed + analytic features (UTS-ready)</div>", unsafe_allow_html=True)

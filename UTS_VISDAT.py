import streamlit as st
import pandas as pd
import plotly.express as px
import ast
from datetime import datetime

# === CONFIGURASI HALAMAN ===
st.set_page_config(page_title="SpongeBob Episode Analytics", page_icon="🪸", layout="wide")
px.defaults.template = "plotly_dark"

# === PALET WARNA “Bikini Bottom” ===
BKB_BG = "#022F40"      # laut dalam
BKB_ACCENT = "#FFD54A"  # kuning SpongeBob
BKB_PINK = "#FF8FB1"    # karang pink
BKB_LIGHT = "#2A9FD6"   # biru langit laut

# === HEADER DASHBOARD ===
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
            <p>Dashboard interaktif berdasarkan data episode SpongeBob SquarePants.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
st.write("")  # jarak ke konten berikut

# === PEMBACAAN DAN PEMBERSIHAN DATA ===
@st.cache_data(ttl=300)
def load_and_clean(path="spongebob_episodes.csv"):
    encodings = ["utf-8", "latin1", "cp1252"]
    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc, on_bad_lines="skip")
            break
        except Exception:
            df = None
    if df is None:
        raise RuntimeError(f"Gagal membaca file CSV dengan encoding: {encodings}")

    df.columns = df.columns.str.strip().str.replace("\ufeff", "").str.replace("–", "-")

    colmap = {}
    for c in df.columns:
        cl = c.lower()
        if "season" in cl:
            colmap[c] = "Season"
        elif "episode" in cl and ("№" in c or "no" in cl):
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

    if "Season" in df.columns:
        df["Season"] = pd.to_numeric(df["Season"], errors="coerce").astype("Int64")
    if "EpisodeRaw" in df.columns:
        df["EpisodeRaw"] = df["EpisodeRaw"].astype(str)

    if "Airdate" in df.columns:
        df["Airdate"] = pd.to_datetime(df["Airdate"], errors="coerce")

    if "US Viewers" in df.columns:
        df["US Viewers"] = pd.to_numeric(df["US Viewers"], errors="coerce")
        df["US Viewers"].fillna(df["US Viewers"].median(), inplace=True)

    def parse_list(s):
        if pd.isna(s): return []
        s = str(s)
        try:
            val = ast.literal_eval(s)
            if isinstance(val, (list, tuple)):
                return [str(v).strip() for v in val if str(v).strip()]
        except Exception:
            return [v.strip().strip('"').strip("'") for v in s.split(",") if v.strip()]
        return []

    for col in ["Characters", "Writers", "Guests"]:
        if col in df.columns:
            df[col + "_list"] = df[col].apply(parse_list)
        else:
            df[col + "_list"] = [[] for _ in range(len(df))]

    if "Running Time" in df.columns:
        df["Running Time (min)"] = (
            df["Running Time"]
            .astype(str)
            .str.extract(r"(\d+)")[0]
            .astype(float)
        )

    df["EpisodeOrder"] = df.groupby("Season").cumcount() + 1

    def build_display(row):
        title = row.get("Title") if pd.notna(row.get("Title")) else ""
        epraw = row.get("EpisodeRaw") if pd.notna(row.get("EpisodeRaw")) else ""
        return f"{title} ({epraw})" if title else f"Episode {epraw}"

    df["EpisodeDisplay"] = df.apply(build_display, axis=1)
    return df

try:
    df = load_and_clean("spongebob_episodes.csv")
except Exception as e:
    st.error(f"❌ Error membaca data: {e}")
    st.stop()

# === SIDEBAR ===
with st.sidebar:
    st.header("🧭 Navigasi")

    season_opts = ["All"] + sorted(df["Season"].dropna().unique().tolist())
    selected_season = st.selectbox("Pilih Season:", season_opts)

    all_writers = sorted(set(
        w for sublist in df["Writers_list"].dropna() for w in sublist if isinstance(sublist, list)
    ))
    selected_writer = st.selectbox("Filter berdasarkan Penulis:", ["All"] + all_writers)

    show_runtime = True

# === FILTER DATA ===
if selected_writer != "All":
    df_filtered = df[df["Writers_list"].apply(lambda x: selected_writer in x if isinstance(x, list) else False)]
else:
    df_filtered = df.copy()

# === TAMPILAN UTAMA ===
if selected_season == "All":
    st.subheader("🌊 Gambaran Umum Semua Season")

    # Baris pertama: metric dan chart trend
    r1c1, r1c2 = st.columns([1, 2])
    with r1c1:
        st.metric("Total Season", df_filtered["Season"].nunique())
        st.metric("Total Episode", len(df_filtered))
        st.metric("Rata-rata Penonton (juta)", f"{df_filtered['US Viewers'].mean():.2f}")
    with r1c2:
        trend = df_filtered.groupby("Season", as_index=False)["US Viewers"].mean()
        fig_trend = px.line(trend, x="Season", y="US Viewers", markers=True,
                            title="Rata-rata Penonton per Season",
                            color_discrete_sequence=[BKB_LIGHT])
        st.plotly_chart(fig_trend, use_container_width=True)
    
    # Baris kedua: karakter global dan penulis global
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        chars = df_filtered.explode("Characters_list")["Characters_list"].dropna()
        if not chars.empty:
            top10 = chars.value_counts().nlargest(10)
            fig = px.pie(
                names=top10.index,
                values=top5.values,
                title="Top 10 Karakter (Global)",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig, use_container_width=True)
    with r2c2:
        top_writers = df_filtered.explode("Writers_list")["Writers_list"].value_counts().nlargest(10)
        if not top_writers.empty:
            dfw = top_writers.reset_index()
            dfw.columns = ["Writer", "Count"]
            figw = px.bar(dfw, x="Count", y="Writer", orientation="h",
                          title="Top 10 Penulis (Global)",
                          color="Count", color_continuous_scale="sunset")
            st.plotly_chart(figw, use_container_width=True)

    st.markdown("---")
    try:
        best_idx = df_filtered["US Viewers"].idxmax()
        best_row = df_filtered.loc[best_idx]
        st.markdown(f"**Episode paling populer:** {best_row['EpisodeDisplay']} → **{best_row['US Viewers']:.2f} juta**")
    except Exception:
        st.info("Tidak ada data viewers yang cukup untuk insight global.")

else:
    season = int(selected_season)
    season_data = df_filtered[df_filtered["Season"] == season].sort_values("EpisodeOrder")
    st.subheader(f"🪸 Detail Season {season}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Jumlah Episode", len(season_data))
    col2.metric("Rata-rata Penonton (juta)", f"{season_data['US Viewers'].mean():.2f}")

    if not season_data.empty and season_data["US Viewers"].notna().any():
        top_idx = season_data["US Viewers"].idxmax()
        top_row = season_data.loc[top_idx]
        col3.metric("Episode Terpopuler", f"{top_row.get('Title','-')} ({top_row.get('EpisodeRaw','-')})")
    else:
        col3.metric("Episode Terpopuler", "-")

    left, right = st.columns([2, 1])

    with left:
        if not season_data.empty:
            fig = px.line(season_data, x="EpisodeOrder", y="US Viewers", markers=True,
                          title=f"Penonton per Episode — Season {season}",
                          labels={"US Viewers":"Penonton (juta)", "EpisodeOrder":"Episode"},
                          color_discrete_sequence=[BKB_ACCENT])
            fig.update_xaxes(tickmode="array",
                             tickvals=season_data["EpisodeOrder"],
                             ticktext=season_data["EpisodeRaw"])
            st.plotly_chart(fig, use_container_width=True)

        if show_runtime and "Running Time (min)" in season_data:
            fig_rt = px.bar(season_data, x="EpisodeOrder", y="Running Time (min)",
                            title="Durasi Episode (menit)",
                            color="Running Time (min)", color_continuous_scale="viridis")
            fig_rt.update_xaxes(tickmode="array",
                                tickvals=season_data["EpisodeOrder"],
                                ticktext=season_data["EpisodeRaw"])
            st.plotly_chart(fig_rt, use_container_width=True)

    with right:
        chars = season_data.explode("Characters_list")["Characters_list"].dropna()
        if not chars.empty:
            topS = chars.value_counts().nlargest(10)
            figp = px.pie(values=topS.values, names=top3.index,
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

# FOOTER
st.markdown(
    "<div style='text-align:center; color:gray; margin-top:18px;'>🌴 Made with ❤️ in Bikini Bottom</div>",
    unsafe_allow_html=True
)

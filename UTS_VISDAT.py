# 🧽 UTS_VISDAT_Revisi.py — SpongeBob Episode Analytics (Bikini Bottom Edition)
import streamlit as st
import pandas as pd
import plotly.express as px
import ast
from datetime import datetime

# === CONFIGURASI HALAMAN ===
st.set_page_config(page_title="SpongeBob Episode Analytics", page_icon="🪸", layout="wide")
px.defaults.template = "plotly_dark"

# === PALLET WARNA “Bikini Bottom” ===
BKB_BG = "#022F40"      # laut dalam
BKB_ACCENT = "#FFD54A"  # kuning SpongeBob
BKB_PINK = "#FF8FB1"    # karang pink
BKB_LIGHT = "#2A9FD6"   # biru langit laut

# === HEADER DASHBOARD ===
st.markdown(
    f"""
    <div style="
        background: linear-gradient(90deg, {BKB_BG} 0%, #074a62 100%);
        padding: 18px; border-radius: 10px;
        box-shadow: 0 4px 30px rgba(0,0,0,0.3);
        color: white;
    ">
        <h1 style="margin:6px 0 2px 0; font-family: 'Helvetica Neue', Arial;">🧽 SpongeBob Episode Analytics — Bikini Bottom</h1>
        <p style="margin:0; opacity:0.85">Dashboard interaktif berdasarkan data episode SpongeBob SquarePants.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

# === PEMBACAAN DATA ===
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

    # normalisasi nama kolom
    df.columns = df.columns.str.strip().str.replace("\ufeff", "").str.replace("–", "-")

    # mapping kolom penting
    colmap = {}
    for c in df.columns:
        cl = c.lower()
        if "season" in cl and "№" in cl:
            colmap[c] = "Season"
        elif "episode" in cl and "№" in cl:
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

    # konversi season & episode
    if "Season" in df.columns:
        df["Season"] = pd.to_numeric(df["Season"], errors="coerce").astype("Int64")
    if "EpisodeRaw" in df.columns:
        df["EpisodeRaw"] = df["EpisodeRaw"].astype(str)

    # konversi tanggal tayang
    if "Airdate" in df.columns:
        def parse_date(x):
            try:
                return pd.to_datetime(x, errors="coerce")
            except Exception:
                return pd.NaT
        df["Airdate"] = df["Airdate"].apply(parse_date)

    # konversi viewers
    if "US Viewers" in df.columns:
        df["US Viewers"] = pd.to_numeric(df["US Viewers"], errors="coerce")
        df["US Viewers"].fillna(df["US Viewers"].median(), inplace=True)

    # parsing list-like kolom
    def parse_list(s):
        if pd.isna(s): return []
        s = str(s)
        try:
            val = ast.literal_eval(s)
            if isinstance(val, (list, tuple)):
                return [v.strip() for v in val if v.strip()]
        except Exception:
            return [v.strip() for v in s.split(",") if v.strip()]
        return []

    for col in ["Characters", "Writers", "Guests"]:
        if col in df.columns:
            df[col + "_list"] = df[col].apply(parse_list)
        else:
            df[col + "_list"] = [[] for _ in range(len(df))]

    # running time (konversi menit)
    if "Running Time" in df.columns:
        df["Running Time (min)"] = (
            df["Running Time"]
            .astype(str)
            .str.extract(r"(\d+)")[0]
            .astype(float)
        )

    df["EpisodeOrder"] = df.groupby("Season").cumcount() + 1
    df["EpisodeDisplay"] = df.apply(lambda r: f"S{r['Season']}E{r['EpisodeOrder']} — {r.get('Title','')}", axis=1)

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
    show_runtime = st.checkbox("Tampilkan durasi episode", value=False)

# === TAMPILAN UTAMA ===
if selected_season == "All":
    st.subheader("🌊 Gambaran Umum Semua Season")

    c1, c2 = st.columns([1, 2])

    with c1:
        st.metric("Total Season", df["Season"].nunique())
        st.metric("Total Episode", len(df))
        st.metric("Rata-rata Penonton (juta)", f"{df['US Viewers'].mean():.2f}")

        chars = df.explode("Characters_list")["Characters_list"].dropna()
        if not chars.empty:
            top5 = chars.value_counts().nlargest(5)
            fig = px.pie(
                names=top5.index,
                values=top5.values,
                title="Top 5 Karakter (Global)",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        trend = df.groupby("Season", as_index=False)["US Viewers"].mean()
        fig_trend = px.line(trend, x="Season", y="US Viewers", markers=True,
                            title="Rata-rata Penonton per Season",
                            color_discrete_sequence=[BKB_LIGHT])
        fig_trend.update_layout(xaxis=dict(dtick=1))
        st.plotly_chart(fig_trend, use_container_width=True)

        top_writers = df.explode("Writers_list")["Writers_list"].value_counts().nlargest(10)
        if not top_writers.empty:
            dfw = top_writers.reset_index()
            dfw.columns = ["Writer", "Count"]
            figw = px.bar(dfw, x="Count", y="Writer", orientation="h",
                          title="Top 10 Penulis (Global)",
                          color="Count", color_continuous_scale="sunset")
            st.plotly_chart(figw, use_container_width=True)

else:
    season = int(selected_season)
    season_data = df[df["Season"] == season]
    st.subheader(f"🪸 Detail Season {season}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Jumlah Episode", len(season_data))
    col2.metric("Rata-rata Penonton (juta)", f"{season_data['US Viewers'].mean():.2f}")
    top_ep = season_data.loc[season_data['US Viewers'].idxmax()]
    col3.metric("Episode Terpopuler", top_ep['Title'])

    left, right = st.columns([2, 1])

    with left:
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
            st.plotly_chart(fig_rt, use_container_width=True)

    with right:
        chars = season_data.explode("Characters_list")["Characters_list"].dropna()
        if not chars.empty:
            top3 = chars.value_counts().nlargest(3)
            figp = px.pie(values=top3.values, names=top3.index,
                          title="Top 3 Karakter", color_discrete_sequence=px.colors.sequential.Plasma)
            st.plotly_chart(figp, use_container_width=True)

        writers = season_data.explode("Writers_list")["Writers_list"].dropna()
        if not writers.empty:
            topw = writers.value_counts().nlargest(5)
            dfw = topw.reset_index()
            dfw.columns = ["Writer", "Count"]
            figw = px.bar(dfw, x="Count", y="Writer", orientation="h",
                          title="Top Penulis Season Ini",
                          color="Count", color_continuous_scale="sunset")
            st.plotly_chart(figw, use_container_width=True)

    st.markdown("---")
    st.markdown("### 💡 Insight")
    avg = season_data["US Viewers"].mean()
    worst = season_data.nsmallest(2, "US Viewers")[["EpisodeRaw", "US Viewers"]]
    st.write(f"- Rata-rata penonton: **{avg:.2f} juta**.")
    st.write("- Episode dengan penonton terendah:")
    for _, r in worst.iterrows():
        st.write(f"  - {r['EpisodeRaw']} → {r['US Viewers']:.2f} juta.")

# FOOTER
st.markdown(
    "<div style='text-align:center; color:gray; margin-top:18px;'>🌴 Made with ❤️ in Bikini Bottom</div>",
    unsafe_allow_html=True
)

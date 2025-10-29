import streamlit as st
import pandas as pd
import plotly.express as px
import ast
from datetime import datetime

# === CONFIGURASI HALAMAN ===
st.set_page_config(page_title="SpongeBob Episode Analytics", page_icon="🪸", layout="wide")
px.defaults.template = "plotly_white"

# === PALET WARNA “Bikini Bottom” ===
BKB_BG = "#022F40"      # laut dalam
BKB_ACCENT = "#FFD54A"  # kuning SpongeBob
BKB_PINK = "#FF8FB1"    # karang pink
BKB_LIGHT = "#2A9FD6"   # biru langit laut

# === HEADER DASHBOARD ===
st.markdown("""
    <style>
        /* === Background utama === */
        .stApp {
            background: linear-gradient(180deg, #FFF8D6 0%, #FFE97D 50%, #FFD54A 100%);
            background-attachment: fixed;
            color: #222;
            font-family: 'Comic Sans MS', 'Trebuchet MS', sans-serif;
        }

        /* === Sidebar === */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #FFEB99 0%, #E2B664 100%);
            border-right: 3px solid #A05B2C;
            box-shadow: 2px 0 12px rgba(0,0,0,0.25);
            border-top-right-radius: 16px;
        }

        /* Judul Sidebar */
        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3 {
            color: #3B2004;
            text-shadow: 1px 1px 0 #FFF3C4;
        }

        /* Pilihan dropdown dan checkbox */
        div[data-baseweb="select"] > div, .stCheckbox {
            background-color: #FFFBEA !important;
            border-radius: 8px;
            border: 1px solid #C6893F !important;
        }

        /* Tombol */
        .stButton > button {
            background: linear-gradient(180deg, #FFD54A 0%, #F9A602 100%);
            color: #3B2004;
            font-weight: 600;
            border-radius: 12px;
            border: 2px solid #3B2004;
            box-shadow: 0 3px 0 #3B2004;
            transition: all 0.25s ease-in-out;
        }
        .stButton > button:hover {
            background: linear-gradient(180deg, #F9A602 0%, #FFD54A 100%);
            transform: translateY(-3px);
        }

        /* Metric box */
        div[data-testid="stMetricValue"] {
            color: #3B2004 !important;
        }
        div[data-testid="stMetric"] {
            background-color: #FFF5C7;
            border-radius: 14px;
            padding: 12px 18px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            border: 2px solid #FFE97D;
        }

        /* Chart container */
        .js-plotly-plot {
            border-radius: 14px;
            box-shadow: 0 6px 14px rgba(0,0,0,0.25);
            background-color: #FFFDF3 !important;
            padding: 12px;
            transition: all 0.3s ease-in-out;
        }
        .js-plotly-plot:hover {
            transform: translateY(-3px);
        }

        /* Scrollbar SpongeBob-style */
        ::-webkit-scrollbar {
            width: 10px;
        }
        ::-webkit-scrollbar-thumb {
            background: #C6893F;
            border-radius: 5px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #A05B2C;
        }
        ::-webkit-scrollbar-track {
            background: #FFF8D6;
        }

        /* Garis pemisah */
        hr, .stMarkdown hr {
            border-top: 3px dashed #A05B2C;
        }

        /* Footer */
        .stMarkdown div {
            text-align: center;
            color: #3B2004;
            font-weight: 500;
        }
    </style>
""", unsafe_allow_html=True)

st.write("") 

# === GAYA TAMBAHAN: Tema SpongeBob ===
st.markdown("""
    <style>
        /* === Background utama === */
        .stApp {
            background: linear-gradient(180deg, #FFEE88 0%, #FFF8D6 50%, #FFD54A 100%);
            background-attachment: fixed;
            color: #222;
            font-family: 'Trebuchet MS', 'Comic Sans MS', sans-serif;
        }

        /* === Sidebar === */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #FCE77D 0%, #E2B664 100%);
            border-right: 3px solid #C6893F;
            box-shadow: 2px 0 10px rgba(0,0,0,0.2);
        }

        /* Judul Sidebar */
        section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
            color: #3B2004;
            text-shadow: 1px 1px 0 #FFF3C4;
        }

        /* Pilihan dropdown dan checkbox */
        div[data-baseweb="select"] > div, .stCheckbox {
            background-color: #FFF8E1 !important;
            border-radius: 8px;
            border: 1px solid #C6893F !important;
        }

        /* Tombol */
        .stButton > button {
            background: linear-gradient(180deg, #F6C90E 0%, #F9A602 100%);
            color: black;
            font-weight: 600;
            border-radius: 12px;
            border: 2px solid #3B2004;
            box-shadow: 0 3px 0 #3B2004;
            transition: 0.2s ease;
        }
        .stButton > button:hover {
            background: linear-gradient(180deg, #F9A602 0%, #F6C90E 100%);
            transform: translateY(-2px);
        }

        /* Metric box */
        div[data-testid="stMetricValue"] {
            color: #3B2004 !important;
        }
        div[data-testid="stMetricDelta"] {
            color: #D62828 !important;
        }
        div[data-testid="stMetric"] {
            background-color: #FFF3C4;
            border-radius: 12px;
            padding: 10px 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }

        /* Chart container */
        .js-plotly-plot {
            border-radius: 12px;
            box-shadow: 0 4px 18px rgba(0,0,0,0.3);
            background-color: #FFFDF3 !important;
            padding: 8px;
        }

        /* Scrollbar SpongeBob-style */
        ::-webkit-scrollbar {
            width: 10px;
        }
        ::-webkit-scrollbar-thumb {
            background: #C6893F;
            border-radius: 5px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #A05B2C;
        }
        ::-webkit-scrollbar-track {
            background: #FFF8D6;
        }

        /* Footer */
        .stMarkdown div {
            text-align: center;
        }

        /* Garis pemisah */
        hr, .stMarkdown hr {
            border-top: 3px dashed #A05B2C;
        }

        /* Tooltip, tabel, dan teks info */
        [data-testid="stMarkdownContainer"] {
            color: #222;
        }
        .stAlert {
            border-radius: 12px;
        }
    </style>
""", unsafe_allow_html=True)

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
    st.error(f"Error membaca data: {e}")
    st.stop()

# === SIDEBAR ===
with st.sidebar:
    st.header("Navigasi")

    season_opts = ["All"] + sorted(df["Season"].dropna().unique().tolist())
    selected_season = st.selectbox("Pilih Season:", season_opts)

    all_writers = sorted(set(
        w for sublist in df["Writers_list"].dropna() for w in sublist if isinstance(sublist, list)
    ))
    selected_writer = st.selectbox("Filter berdasarkan Penulis:", ["Semua"] + all_writers)

    show_runtime = st.checkbox("Tampilkan durasi episode", value=False)

# === FILTER DATA ===
if selected_writer != "Semua":
    df_filtered = df[df["Writers_list"].apply(lambda x: selected_writer in x if isinstance(x, list) else False)]
else:
    df_filtered = df.copy()

# === TAMPILAN UTAMA ===
if selected_season == "All":
    st.subheader("🌊 Gambaran Umum Semua Season")

    c1, c2 = st.columns([1, 2])

    with c1:
        st.metric("Total Season", df_filtered["Season"].nunique())
        st.metric("Total Episode", len(df_filtered))
        st.metric("Rata-rata Penonton (juta)", f"{df_filtered['US Viewers'].mean():.2f}")

        chars = df_filtered.explode("Characters_list")["Characters_list"].dropna()
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
        trend = df_filtered.groupby("Season", as_index=False)["US Viewers"].mean()
        fig_trend = px.line(trend, x="Season", y="US Viewers", markers=True,
                            title="Rata-rata Penonton per Season",
                            color_discrete_sequence=[BKB_LIGHT])
        fig_trend.update_layout(xaxis=dict(dtick=1))
        st.plotly_chart(fig_trend, use_container_width=True)

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
    st.subheader(f"Detail Season {season}")

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
            top3 = chars.value_counts().nlargest(3)
            figp = px.pie(values=top3.values, names=top3.index,
                          title="Top 3 Karakter", color_discrete_sequence=px.colors.sequential.Plasma)
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
    st.markdown("### Insight")
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
    "<div style='text-align:center; color:gray; margin-top:18px;'>Made with ❤️ in Bikini Bottom</div>",
    unsafe_allow_html=True
)

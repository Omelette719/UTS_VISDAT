# UTS_VISDAT.py
# SpongeBob SquarePants Episode Analytics — Bikini Bottom theme
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ast

# === Page config & theme ===
st.set_page_config(page_title="SpongeBob Episode Analytics", page_icon="🧽", layout="wide")
px.defaults.template = "plotly_dark"

BKB_BG = "#022F40"      # deep ocean
BKB_ACCENT = "#FFD54A"  # Bikini Bottom yellow-ish
BKB_PINK = "#FF8FB1"    # accent
BKB_LIGHT = "#2A9FD6"   # light blue

# Header style
st.markdown(
    f"""
    <div style="
        background: linear-gradient(90deg, {BKB_BG} 0%, #074a62 100%);
        padding: 18px;
        border-radius: 10px;
        box-shadow: 0 4px 30px rgba(0,0,0,0.3);
        color: white;
    ">
        <h1 style="margin:6px 0 2px 0; font-family: 'Helvetica Neue', Arial;">🧽 SpongeBob Episode Analytics — Bikini Bottom</h1>
        <p style="margin:0; opacity:0.85">Interactive UTS dashboard — pilih season untuk 'zoom in' ke episode dan karakter.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")  # spacing

# === Robust data loader ===
@st.cache_data(ttl=300)
def load_and_clean(path="spongebob_episodes.csv"):
    # 1) read with fallback encodings
    tried = []
    for enc in ("utf-8", "latin1", "cp1252"):
        try:
            df = pd.read_csv(path, encoding=enc, on_bad_lines="skip")
            # If it loads and columns look reasonable, break
            tried.append(enc)
            break
        except Exception as e:
            tried.append(f"{enc}:ERR")
            df = None
    if df is None:
        raise RuntimeError(f"File tidak bisa dibaca. Percobaan encoding: {tried}")

    # 2) normalize column names (remove weird characters from encoding mistakes)
    cols = df.columns.astype(str).tolist()
    cols_clean = []
    for c in cols:
        s = c.strip()
        s = s.replace("â„–", "No").replace("\ufeff", "").replace("–", "-")
        s = s.replace("\xa0", " ").strip()
        cols_clean.append(s)
    df.columns = cols_clean

    # 3) heuristics: map likely columns to canonical names (take first match)
    col_map = {}
    used_targets = set()
    for c in df.columns:
        lc = c.lower()
        if ("season" in lc or "season no" in lc or "season " in lc) and "Season" not in used_targets:
            col_map[c] = "Season"; used_targets.add("Season")
        elif ("episode" in lc or "episode no" in lc or "episode â" in lc) and "EpisodeRaw" not in used_targets:
            # map to EpisodeRaw first (we will compute EpisodeOrder)
            col_map[c] = "EpisodeRaw"; used_targets.add("EpisodeRaw")
        elif ("viewer" in lc or "u.s. viewers" in lc or "us. viewers" in lc or "u.s. viewers (millions)" in lc) and "US Viewers" not in used_targets:
            col_map[c] = "US Viewers"; used_targets.add("US Viewers")
        elif ("character" in lc or "characters" in lc or "main" in lc) and "characters_raw" not in used_targets:
            col_map[c] = "characters_raw"; used_targets.add("characters_raw")
        elif ("writer" in lc or "creative" in lc or "writer(s)" in lc) and "writers_raw" not in used_targets:
            col_map[c] = "writers_raw"; used_targets.add("writers_raw")
        elif ("running" in lc and "time" in lc) and "Running Time Raw" not in used_targets:
            col_map[c] = "Running Time Raw"; used_targets.add("Running Time Raw")
        elif ("air" in lc and "date" in lc) and "Airdate" not in used_targets:
            col_map[c] = "Airdate"; used_targets.add("Airdate")
        elif c.lower() == "title" and "Title" not in used_targets:
            col_map[c] = "Title"; used_targets.add("Title")

    df.rename(columns=col_map, inplace=True)

    # 4) ensure required cols exist (we'll allow some missing but inform)
    required = ["Season", "EpisodeRaw", "US Viewers"]
    missing_required = [c for c in required if c not in df.columns]
    if missing_required:
        # show available columns to help debugging
        raise RuntimeError(f"Kolom required tidak ditemukan: {missing_required}. Kolom tersedia: {df.columns.tolist()}")

    # 5) clean US Viewers (to numeric)
    df["US Viewers"] = pd.to_numeric(df["US Viewers"], errors="coerce")
    # fill missing viewers with median (so dashboards don't drop rows entirely)
    if df["US Viewers"].isna().all():
        # fallback to 0 if all missing
        df["US Viewers"] = df["US Viewers"].fillna(0)
    else:
        df["US Viewers"] = df["US Viewers"].fillna(df["US Viewers"].median())

    # 6) normalize Season: sometimes season column contains non-numeric (keep numeric part)
    df["Season"] = df["Season"].astype(str).str.extract(r"(\d+)").astype(float)
    df["Season"] = df["Season"].astype("Int64")  # nullable int

    # 7) keep original order then create EpisodeOrder per season
    df.reset_index(drop=True, inplace=True)
    # EpisodeRaw may be like '1a', '1b', '2a' etc. We'll create EpisodeLabel (string) and EpisodeOrder (int)
    df["EpisodeLabel"] = df["EpisodeRaw"].astype(str).str.strip()
    # EpisodeOrder: sequential index within each Season preserving file order
    df["EpisodeOrder"] = df.groupby("Season").cumcount() + 1

    # 8) Running Time: try extract minutes from strings like "11 minutes" or "11 minutes, 4 seconds"
    if "Running Time Raw" in df.columns:
        df["Running Time"] = (
            df["Running Time Raw"].astype(str)
            .str.extract(r"(\d+)")
            .astype(float)
            .fillna(pd.NA)
        )

    # 9) Parse characters & writers into lists
    def parse_list_cell(cell):
        if pd.isna(cell):
            return []
        s = str(cell).strip()
        # if it's like "['A', 'B']" try ast.literal_eval
        if (s.startswith("[") and s.endswith("]")) or ("'," in s and "[" in s):
            try:
                parsed = ast.literal_eval(s)
                if isinstance(parsed, (list, tuple)):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                pass
        # fallback: split by comma
        parts = [p.strip().strip('"').strip("'") for p in s.split(",") if p.strip()]
        return parts

    if "characters_raw" in df.columns:
        df["characters_list"] = df["characters_raw"].apply(parse_list_cell)
    else:
        df["characters_list"] = [[] for _ in range(len(df))]

    if "writers_raw" in df.columns:
        df["writers_list"] = df["writers_raw"].apply(parse_list_cell)
    else:
        df["writers_list"] = [[] for _ in range(len(df))]

    # 10) Title
    if "Title" not in df.columns and "title" in [c.lower() for c in cols]:
        # try fallback find 'title' ignoring case
        for c in df.columns:
            if c.lower() == "title":
                df.rename(columns={c: "Title"}, inplace=True)
                break

    # 11) drop rows without season or EpisodeOrder
    df = df.dropna(subset=["Season", "EpisodeOrder"])

    # 12) convenience columns for display
    df["Season"] = df["Season"].astype(int)
    df["EpisodeOrder"] = df["EpisodeOrder"].astype(int)
    df["EpisodeDisplay"] = df.apply(lambda r: f"S{r['Season']}E{r['EpisodeOrder']} ({r['EpisodeLabel']})", axis=1)

    return df

# load
try:
    df = load_and_clean("/mnt/data/spongebob_episodes.csv")
except Exception as e:
    st.error(f"Error saat membaca data: {e}")
    st.stop()

# === Sidebar filters ===
with st.sidebar:
    st.header("Controls")
    season_opts = ["All"] + sorted(df["Season"].unique().tolist())
    selected_season = st.selectbox("Pilih Season:", season_opts, index=0)
    show_writers = st.checkbox("Tampilkan penulis (chart)", value=True)
    show_runtime = st.checkbox("Tampilkan running time (jika tersedia)", value=False)

# === Main content: different behavior for All vs Season ===
if selected_season == "All":
    st.subheader("Gambaran Umum — Semua Season")

    c1, c2 = st.columns([1, 2], gap="large")

    # KPI row (top)
    with c1:
        total_eps = len(df)
        total_seasons = df["Season"].nunique()
        avg_view = df["US Viewers"].mean()
        st.metric("Total Episode (dataset)", total_eps)
        st.metric("Total Season", total_seasons)
        st.metric("Rata-rata Penonton (juta)", f"{avg_view:.2f}")

        # Top characters global (top 5)
        # explode characters_list
        char_series = df.explode("characters_list")["characters_list"].dropna()
        if not char_series.empty:
            top5 = char_series.value_counts().nlargest(5)
            fig = px.pie(names=top5.index, values=top5.values, title="Top 5 Karakter (Global)", color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Tidak ada data karakter untuk membuat pie chart.")

    with c2:
        # Trend: average viewers per season
        trend = df.groupby("Season", as_index=False)["US Viewers"].mean()
        fig_trend = px.line(trend, x="Season", y="US Viewers", markers=True, title="Rata-rata Penonton per Season", color_discrete_sequence=[BKB_LIGHT])
        fig_trend.update_layout(xaxis=dict(dtick=1))
        st.plotly_chart(fig_trend, use_container_width=True)

        # Episode counts per season
        ep_count = df.groupby("Season").size().reset_index(name="Jumlah Episode")
        fig_count = px.bar(ep_count, x="Season", y="Jumlah Episode", title="Jumlah Episode per Season", color="Jumlah Episode", color_continuous_scale="solar")
        st.plotly_chart(fig_count, use_container_width=True)

    # Top writers (global)
    if show_writers:
        st.markdown("### Penulis paling produktif (Global)")
        writers_series = df.explode("writers_list")["writers_list"].dropna()
        if not writers_series.empty:
            top_writers = writers_series.value_counts().nlargest(10)
            figw = px.bar(top_writers.reset_index().rename(columns={"index":"Writer", "writers_list":"Count"}), x="Count", y="Writer", orientation="h", title="Top 10 Writers", color="Count")
            st.plotly_chart(figw, use_container_width=True)
        else:
            st.info("Tidak ada data penulis (writers) yang dapat ditampilkan.")

else:
    # Season-specific view
    season = int(selected_season)
    season_data = df[df["Season"] == season].sort_values("EpisodeOrder")
    st.subheader(f"Detail — Season {season}")

    # Top area: KPIs for the season
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Jumlah Episode (Season)", len(season_data))
    with col2:
        st.metric("Rata-rata Penonton (juta)", f"{season_data['US Viewers'].mean():.2f}")
    with col3:
        # Episode with max viewers (guard for empty)
        if season_data["US Viewers"].dropna().empty:
            best_ep_label = "-"
        else:
            idx = season_data["US Viewers"].idxmax()
            best_ep_label = season_data.loc[idx, "EpisodeDisplay"]
        st.metric("Episode Terpopuler", best_ep_label)

    # layout two columns: left = episode trend + runtime, right = characters + writers
    left, right = st.columns([2, 1], gap="large")

    with left:
        # If more than one episode, show trend; else show a detailed card
        if len(season_data) > 1:
            fig_ep_trend = px.line(season_data, x="EpisodeOrder", y="US Viewers", markers=True,
                                   hover_data=["EpisodeDisplay", "Title"], title=f"Penonton per Episode — Season {season}",
                                   labels={"EpisodeOrder": "Episode (order)","US Viewers":"US Viewers (millions)"},
                                   color_discrete_sequence=[BKB_ACCENT])
            # annotate with episode labels on hover; also show EpisodeDisplay ticks
            fig_ep_trend.update_xaxes(tickmode="array", tickvals=season_data["EpisodeOrder"], ticktext=season_data["EpisodeLabel"])
            st.plotly_chart(fig_ep_trend, use_container_width=True)
        else:
            # single episode: show details
            r = season_data.iloc[0]
            st.markdown("#### Hanya satu episode di season ini — detail:")
            st.write(f"**{r.get('Title','-')}** — {r['EpisodeDisplay']}")
            st.write(f"- Penonton: {r['US Viewers']} juta")
            if "Airdate" in r and pd.notna(r.get("Airdate")):
                st.write(f"- Tayang: {r['Airdate']}")
            if r.get("characters_list"):
                st.write(f"- Karakter: {', '.join(r['characters_list'][:8])}")

        # running time chart (optional)
        if show_runtime and "Running Time" in season_data.columns and not season_data["Running Time"].dropna().empty:
            st.markdown("#### Durasi Episode (menit)")
            fig_rt = px.bar(season_data, x="EpisodeOrder", y="Running Time", labels={"EpisodeOrder":"EpisodeOrder","Running Time":"Minutes"}, title="Durasi per Episode", color="Running Time", color_continuous_scale="viridis")
            fig_rt.update_xaxes(tickmode="array", tickvals=season_data["EpisodeOrder"], ticktext=season_data["EpisodeLabel"])
            st.plotly_chart(fig_rt, use_container_width=True)

    with right:
        st.markdown("#### Top 3 Karakter — Season ini")
        chars = season_data.explode("characters_list")["characters_list"].dropna()
        if not chars.empty:
            top3 = chars.value_counts().nlargest(3)
            fig_p = px.pie(values=top3.values, names=top3.index, title="Top 3 Karakter (Season {})".format(season), color_discrete_sequence=px.colors.sequential.Plasma)
            st.plotly_chart(fig_p, use_container_width=True)
        else:
            st.info("Tidak ada data karakter untuk season ini.")

        if show_writers:
            st.markdown("#### Penulis — Season ini")
            w = season_data.explode("writers_list")["writers_list"].dropna()
            if not w.empty:
                wcount = w.value_counts().nlargest(8)
                figw = px.bar(wcount.reset_index().rename(columns={"index":"Writer","writers_list":"Count"}), x="writers_list", y="Writer", orientation="h", title="Top Writers (season)", color="writers_list")
                st.plotly_chart(figw, use_container_width=True)
            else:
                st.info("Tidak ada data penulis untuk season ini.")

    # final insight area
    st.markdown("---")
    st.markdown("### Insight singkat")
    # get some simple actionable insights
    if len(season_data) > 0:
        avg_v = season_data["US Viewers"].mean()
        worst_eps = season_data.nsmallest(2, "US Viewers")[["EpisodeDisplay","US Viewers"]]
        st.write(f"- Rata-rata penonton season: **{avg_v:.2f} juta**.")
        if not worst_eps.empty:
            st.write("- Episode dengan penonton terendah (contoh):")
            for _, row in worst_eps.iterrows():
                st.write(f"  - {row['EpisodeDisplay']} → {row['US Viewers']:.2f} juta")
        st.write("- Rekomendasi: jika ingin meningkatkan viewership, perhatikan karakter yang paling populer dan pertimbangkan penempatan mereka di episode penting.")
    else:
        st.write("Data season kosong — tidak ada insight.")

# Footer
st.markdown(
    f"<div style='text-align:center; color:gray; margin-top:18px;'>Made with ❤️ for UTS — Bikini Bottom theme</div>",
    unsafe_allow_html=True
)

# 🧽 UTS_VISDAT_BikiniBottom.py — SpongeBob Episode Analytics (Bikini Bottom Edition v2)
import streamlit as st
import pandas as pd
import plotly.express as px
import ast

# === KONFIGURASI DASAR ===
st.set_page_config(page_title="SpongeBob Episode Analytics", page_icon="🧽", layout="wide")

# === WARNA TEMA ===
SPONGE_YELLOW = "#FFEB3B"
OCEAN_BLUE = "#AEE7F9"
CORAL_PINK = "#FF8FB1"
SEA_PURPLE = "#CBA0F5"
TEXT_DARK = "#0A2540"

px.defaults.template = "plotly_white"

# === HEADER ===
st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, {OCEAN_BLUE} 0%, {SPONGE_YELLOW} 100%);
        padding: 20px; border-radius: 12px; text-align:center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    ">
        <h1 style="margin-bottom:6px; color:{TEXT_DARK}; font-family:'Trebuchet MS';">🧽 SpongeBob Episode Analytics</h1>
        <p style="margin:0; color:#333; font-size:16px;">Selamat datang di <b>Bikini Bottom Data Center</b> — di mana statistik SpongeBob bersinar seterang spatula emas!</p>
    </div>
""", unsafe_allow_html=True)
st.write("")

# === PEMBACAAN DATA ===
@st.cache_data(ttl=300)
def load_data(path="spongebob_episodes.csv"):
    for enc in ["utf-8", "latin1", "cp1252"]:
        try:
            df = pd.read_csv(path, encoding=enc, on_bad_lines="skip")
            break
        except Exception:
            df = None
    if df is None:
        raise RuntimeError("File tidak bisa dibaca.")

    df.columns = df.columns.str.strip().str.replace("–", "-").str.replace("\ufeff", "")

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
        elif "title" in cl:
            colmap[c] = "Title"
        elif "running" in cl:
            colmap[c] = "Running Time"
    df.rename(columns=colmap, inplace=True)

    # konversi data
    df["Season"] = pd.to_numeric(df.get("Season"), errors="coerce").astype("Int64")
    df["US Viewers"] = pd.to_numeric(df.get("US Viewers"), errors="coerce")
    df["US Viewers"].fillna(df["US Viewers"].median(), inplace=True)

    def parse_list(x):
        if pd.isna(x): return []
        s = str(x)
        try:
            val = ast.literal_eval(s)
            if isinstance(val, list): return val
        except: pass
        return [v.strip() for v in s.split(",") if v.strip()]

    for c in ["Writers", "Characters"]:
        if c in df.columns:
            df[c+"_list"] = df[c].apply(parse_list)
        else:
            df[c+"_list"] = [[] for _ in range(len(df))]

    df["EpisodeOrder"] = df.groupby("Season").cumcount() + 1
    return df

try:
    df = load_data("spongebob_episodes.csv")
except Exception as e:
    st.error(f"❌ Error membaca data: {e}")
    st.stop()

# === SIDEBAR ===
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/3/3b/SpongeBob_SquarePants_character.svg", width=160)
    st.header("🔍 Filter Bikini Bottom")
    season_opts = ["All"] + sorted(df["Season"].dropna().unique().tolist())
    season_choice = st.selectbox("Pilih Season:", season_opts)
    st.markdown("---")
    st.caption("Tema: SpongeBob Cerah 💛💙")

# === ALL SEASON ===
if season_choice == "All":
    st.subheader("🌊 Gambaran Umum Semua Season")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Season", df["Season"].nunique())
    c2.metric("Total Episode", len(df))
    c3.metric("Rata-rata Penonton (juta)", f"{df['US Viewers'].mean():.2f}")

    # tren per season
    trend = df.groupby("Season", as_index=False)["US Viewers"].mean()
    fig_trend = px.line(
        trend, x="Season", y="US Viewers", markers=True,
        title="📈 Tren Rata-rata Penonton per Season",
        color_discrete_sequence=[SPONGE_YELLOW]
    )
    fig_trend.update_layout(plot_bgcolor=OCEAN_BLUE, paper_bgcolor=OCEAN_BLUE)
    st.plotly_chart(fig_trend, use_container_width=True)

    # top karakter global
    chars = df.explode("Characters_list")["Characters_list"].dropna()
    if not chars.empty:
        top5 = chars.value_counts().nlargest(5)
        fig_chars = px.pie(
            names=top5.index, values=top5.values,
            title="🪸 Top 5 Karakter Sepanjang Masa",
            color_discrete_sequence=px.colors.sequential.Aggrnyl
        )
        st.plotly_chart(fig_chars, use_container_width=True)

    # top writer global
    writers = df.explode("Writers_list")["Writers_list"].dropna()
    if not writers.empty:
        top10 = writers.value_counts().nlargest(10)
        dfw = top10.reset_index()
        dfw.columns = ["Writer", "Count"]
        fig_writers = px.bar(
            dfw, x="Count", y="Writer", orientation="h",
            title="✍️ Top 10 Penulis Paling Produktif",
            color="Count", color_continuous_scale="YlOrBr"
        )
        st.plotly_chart(fig_writers, use_container_width=True)

    # insight global
    st.markdown("### 💡 Insight Global")
    best = df.loc[df["US Viewers"].idxmax()]
    avg = df["US Viewers"].mean()
    st.markdown(f"""
    <div style="background-color:{SPONGE_YELLOW}; color:{TEXT_DARK}; padding:14px; border-radius:10px;">
    🧽 <b>Rata-rata penonton:</b> {avg:.2f} juta<br>
    🏆 <b>Episode paling populer:</b> <i>{best['Title']}</i> (<b>{best['EpisodeRaw']}</b>) → {best['US Viewers']:.2f} juta<br>
    📅 <b>Season paling populer:</b> Season {trend.loc[trend['US Viewers'].idxmax(), 'Season']}
    </div>
    """, unsafe_allow_html=True)

# === PER SEASON ===
else:
    s = int(season_choice)
    season_data = df[df["Season"] == s]
    st.subheader(f"🪸 Detail Season {s}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Jumlah Episode", len(season_data))
    col2.metric("Rata-rata Penonton (juta)", f"{season_data['US Viewers'].mean():.2f}")
    best_ep = season_data.loc[season_data["US Viewers"].idxmax()]
    col3.metric("Episode Terpopuler", f"{best_ep['Title']} ({best_ep['EpisodeRaw']})")

    # grafik per episode
    fig_line = px.line(
        season_data, x="EpisodeOrder", y="US Viewers", markers=True,
        title=f"📊 Jumlah Penonton per Episode — Season {s}",
        labels={"EpisodeOrder": "Episode", "US Viewers": "Penonton (juta)"},
        color_discrete_sequence=[SPONGE_YELLOW]
    )
    fig_line.update_traces(line=dict(width=3))
    st.plotly_chart(fig_line, use_container_width=True)

    colL, colR = st.columns([1.5, 1])

    # top karakter di season
    with colL:
        chars = season_data.explode("Characters_list")["Characters_list"].dropna()
        if not chars.empty:
            top3 = chars.value_counts().nlargest(3)
            fig_char = px.pie(
                names=top3.index, values=top3.values,
                title="🧜‍♀️ Top 3 Karakter Season Ini",
                color_discrete_sequence=[SPONGE_YELLOW, OCEAN_BLUE, CORAL_PINK]
            )
            st.plotly_chart(fig_char, use_container_width=True)

    # top penulis di season
    with colR:
        writers = season_data.explode("Writers_list")["Writers_list"].dropna()
        if not writers.empty:
            top5 = writers.value_counts().nlargest(5)
            dfw = top5.reset_index()
            dfw.columns = ["Writer", "Count"]
            fig_w = px.bar(
                dfw, x="Count", y="Writer", orientation="h",
                title="✏️ Top Penulis Season Ini",
                color="Count", color_continuous_scale="YlOrBr"
            )
            st.plotly_chart(fig_w, use_container_width=True)

    # insight season
    st.markdown("---")
    st.markdown("### 💡 Insight Season")
    avg = season_data["US Viewers"].mean()
    max_r = best_ep
    min2 = season_data.nsmallest(2, "US Viewers")

    low_list = [
        f"• *{row['Title']}* (**{row['EpisodeRaw']}**) → {row['US Viewers']:.2f} juta"
        for _, row in min2.iterrows()
    ]

    st.markdown(f"""
    <div style="background-color:{OCEAN_BLUE}; padding:14px; border-radius:10px; color:{TEXT_DARK};">
        <p>📊 <b>Rata-rata penonton:</b> {avg:.2f} juta</p>
        <p>🏆 <b>Episode terpopuler:</b> <i>{max_r['Title']}</i> (<b>{max_r['EpisodeRaw']}</b>) → {max_r['US Viewers']:.2f} juta</p>
        <p>🪼 <b>Episode dengan penonton terendah:</b><br>{"<br>".join(low_list)}</p>
    </div>
    """, unsafe_allow_html=True)

# === FOOTER ===
st.markdown(
    f"<div style='text-align:center; margin-top:18px; color:gray;'>🫧 Made with 💛 in Bikini Bottom</div>",
    unsafe_allow_html=True
)

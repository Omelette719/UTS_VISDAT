import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="🧽 SpongeBob Analytics Dashboard",
    page_icon="🦀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD DATA ---
@st.cache_data
def load_data():
    df = pd.read_csv("spongebob_episodes.csv")

    # Normalisasi kolom
    df.columns = [col.strip().replace("â„–", "").replace("№", "").replace("–", "").replace("\ufeff", "") for col in df.columns]

    # Rename standar
    rename_map = {
        "Season ": "Season",
        "Episode ": "Episode",
        "Running time": "Running Time",
        "U.S. viewers (millions)": "US Viewers",
        "Creative": "Writer"
    }
    df = df.rename(columns=rename_map)

    # Cleaning
    for col in ["Season", "Episode"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "US Viewers" in df.columns:
        df["US Viewers"] = pd.to_numeric(df["US Viewers"], errors="coerce")
        df["US Viewers"].fillna(df["US Viewers"].median(), inplace=True)

    if "Running Time" in df.columns:
        df["Running Time"] = df["Running Time"].astype(str).str.extract("(\d+)").astype(float)
        df["Running Time"].fillna(df["Running Time"].mean(), inplace=True)

    return df

df = load_data()

# --- SIDEBAR ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/en/3/3b/SpongeBob_SquarePants_character.svg", width=150)
st.sidebar.title("🧽 SpongeBob Dashboard")

# Filter
season_list = sorted(df["Season"].dropna().unique().tolist())
selected_season = st.sidebar.selectbox("Pilih Season", ["All"] + list(map(str, season_list)))
if selected_season != "All":
    df = df[df["Season"] == int(selected_season)]

# --- HEADER ---
st.markdown("<h1 style='text-align: center; color: #FFCC00;'>🦀 Krusty Krab Data Dashboard 🐚</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size:18px;'>Analisis Episode SpongeBob SquarePants Berdasarkan Season, Penonton, dan Tim Kreatif</p>", unsafe_allow_html=True)
st.markdown("---")

# --- KPI Cards ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📺 Total Episode", len(df))
with col2:
    st.metric("👀 Rata-rata Penonton (juta)", round(df["US Viewers"].mean(), 2) if "US Viewers" in df.columns else "N/A")
with col3:
    st.metric("⏱️ Durasi Terpanjang (menit)", df["Running Time"].max() if "Running Time" in df.columns else "N/A")

# --- VISUAL 1: Line Chart (Trend Viewers per Season) ---
if "US Viewers" in df.columns:
    viewers_trend = df.groupby("Season")["US Viewers"].mean().reset_index()
    fig_line = px.line(
        viewers_trend, x="Season", y="US Viewers",
        markers=True,
        title="📈 Tren Rata-rata Penonton per Season",
        color_discrete_sequence=["#00BFFF"]
    )

    # Highlight season terpilih
    if selected_season != "All":
        highlight = viewers_trend[viewers_trend["Season"] == int(selected_season)]
        fig_line.add_trace(go.Scatter(
            x=highlight["Season"],
            y=highlight["US Viewers"],
            mode="markers+text",
            marker=dict(size=14, color="red"),
            text=["⭐ Season Terpilih"],
            textposition="top center",
            showlegend=False
        ))

    st.plotly_chart(fig_line, use_container_width=True)

# --- VISUAL 2: Bar Chart (Episode Count per Season) ---
episode_count = df.groupby("Season").size().reset_index(name="Jumlah Episode")
fig_bar = px.bar(
    episode_count, x="Season", y="Jumlah Episode",
    color="Jumlah Episode", color_continuous_scale="sunset",
    title="📊 Jumlah Episode per Season"
)

if selected_season != "All":
    highlight_season = int(selected_season)
    fig_bar.add_trace(go.Bar(
        x=[highlight_season],
        y=episode_count.loc[episode_count["Season"] == highlight_season, "Jumlah Episode"],
        marker_color="red",
        name="Season Terpilih"
    ))

st.plotly_chart(fig_bar, use_container_width=True)

# --- VISUAL 3: Pie Chart (Kontributor Penulis) ---
if "Writer" in df.columns:
    writer_counts = df["Writer"].value_counts().nlargest(8).reset_index()
    writer_counts.columns = ["Writer", "Jumlah Episode"]
    fig_pie = px.pie(
        writer_counts, names="Writer", values="Jumlah Episode",
        title="✍️ Proporsi Episode Berdasarkan Penulis",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# --- VISUAL 4: Scatter Plot (Durasi vs Viewers) ---
if "US Viewers" in df.columns:
    fig_scatter = px.scatter(
        df, x="Running Time", y="US Viewers",
        color="Season", size="US Viewers",
        title="🫧 Hubungan Durasi Episode dan Jumlah Penonton",
        color_continuous_scale="turbo"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# --- INSIGHT SECTION ---
st.markdown("### 🧠 Insight dari Data")
st.markdown("""
- Season dengan rata-rata penonton tertinggi menunjukkan momen puncak popularitas SpongeBob.  
- Episode berdurasi sedang (10–12 menit) cenderung memiliki jumlah penonton stabil.  
- Beberapa penulis memiliki pola kontribusi yang signifikan terhadap episode populer.
""")

st.markdown("---")
st.caption("Data diambil dari SpongeBob Episode Dataset (Kaggle/Wikipedia). Dibuat untuk UTS Visualisasi Data 2025.")


import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

# Konfigurasi halaman
st.set_page_config(
    page_title="SpongeBob Episodes Dashboard",
    page_icon="🧽",
    layout="wide",
    initial_sidebar_state="expanded"
)

alt.themes.enable("dark")

# Load dataset
df = pd.read_csv("spongebob_episodes.csv")

# Bersihkan data viewers jadi numerik
df["U.S. viewers (millions)"] = pd.to_numeric(df["U.S. viewers (millions)"], errors="coerce").fillna(0)

# Sidebar
with st.sidebar:
    st.title("🧽 SpongeBob Dashboard")
    st.markdown("### Bikini Bottom Data Explorer")

    seasons = sorted(df["Season"].unique())
    selected_season = st.selectbox("Pilih Season", seasons)

    df_season = df[df["Season"] == selected_season]

    color_theme_list = ["blues", "viridis", "plasma", "turbo", "magma", "inferno"]
    selected_color = st.selectbox("Pilih Tema Warna", color_theme_list)

# ================= METRIK RINGKAS =================
col1, col2, col3 = st.columns(3)

col1.metric("📺 Jumlah Episode", len(df_season))
col2.metric("⭐ Rata-rata Rating", round(df_season["IMDb"].mean(), 2))
col3.metric("👀 Rata-rata Penonton (juta)", round(df_season["U.S. viewers (millions)"].mean(), 2))

st.markdown("---")

# ================= GRAFIK 1: TREND RATING PER EPISODE =================
st.subheader(f"📊 Rating Tiap Episode - Season {selected_season}")

rating_chart = alt.Chart(df_season).mark_circle(size=100, opacity=0.8).encode(
    x=alt.X("Episode:O", title="Episode ke-"),
    y=alt.Y("IMDb:Q", title="Rating IMDb"),
    tooltip=["Title", "IMDb", "U.S. viewers (millions)"],
    color=alt.Color("IMDb:Q", scale=alt.Scale(scheme=selected_color))
).properties(height=400)

st.altair_chart(rating_chart, use_container_width=True)

# ================= GRAFIK 2: TREN PENONTON PER SEASON =================
st.subheader("👁️ Tren Jumlah Penonton per Season")

avg_viewers = df.groupby("Season")["U.S. viewers (millions)"].mean().reset_index()

fig = px.line(
    avg_viewers,
    x="Season",
    y="U.S. viewers (millions)",
    markers=True,
    color_discrete_sequence=["#FFD700"]
)
fig.update_layout(
    template="plotly_dark",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    title_font_color="#FFD700"
)
st.plotly_chart(fig, use_container_width=True)

# ================= TABEL EPISODE =================
st.subheader(f"📜 Daftar Episode Season {selected_season}")

st.dataframe(
    df_season,
    hide_index=True,
    column_order=("Title", "Original air date", "IMDb", "U.S. viewers (millions)"),
    column_config={
        "Title": st.column_config.TextColumn("Judul Episode"),
        "Original air date": st.column_config.TextColumn("Tanggal Tayang"),
        "IMDb": st.column_config.ProgressColumn("Rating IMDb", format="%.1f", min_value=0, max_value=10),
        "U.S. viewers (millions)": st.column_config.NumberColumn("Penonton (juta)", format="%.2f")
    }
)

# ================= ABOUT =================
with st.expander("Tentang Dashboard", expanded=False):
    st.write("""
        - 🎬 Data diambil dari SpongeBob episode dataset.
        - 📈 Menampilkan statistik rating dan penonton tiap season.
        - 🎨 Tema warna bisa diubah untuk menyesuaikan gaya tampilan.
        - 🧠 Dibuat untuk keperluan UTS Visualisasi Data.
    """)

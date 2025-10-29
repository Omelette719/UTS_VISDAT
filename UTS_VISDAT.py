import streamlit as st
import pandas as pd
import plotly.express as px

# ==============================
# PAGE CONFIGURATION
# ==============================
st.set_page_config(
    page_title="SpongeBob Data Dashboard",
    page_icon="🧽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# LOAD DATA
# ==============================
@st.cache_data
def load_data():
    df = pd.read_csv("spongebob_episodes.csv")

    # --- CLEANING ---
    df = df.rename(columns={
        "Season â„–": "Season",
        "Episode â„–": "Episode",
        "U.S. viewers (millions)": "US Viewers (millions)",
        "Running time": "Running Time"
    })

    # ubah tipe data numerik
    for col in ["Season", "Episode"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # isi nilai kosong di viewers pakai median
    if "US Viewers (millions)" in df.columns:
        df["US Viewers (millions)"] = pd.to_numeric(df["US Viewers (millions)"], errors="coerce")
        df["US Viewers (millions)"].fillna(df["US Viewers (millions)"].median(), inplace=True)

    # isi nilai kosong running time
    if "Running Time" in df.columns:
        df["Running Time"].fillna(df["Running Time"].mode()[0], inplace=True)

    return df

df = load_data()

# ==============================
# SIDEBAR FILTERS
# ==============================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/3/3b/SpongeBob_SquarePants_character.svg", width=120)
    st.title("🧽 SpongeBob Dashboard")
    st.markdown("Analisis data episode SpongeBob SquarePants")

    # filter season
    season_list = sorted(df["Season"].dropna().unique())
    selected_season = st.selectbox("Pilih Season:", options=["All"] + list(map(int, season_list)))

    # filter writer
    if "Storyboard" in df.columns:
        writers = sorted(df["Storyboard"].dropna().unique().tolist())
    elif "Creative" in df.columns:
        writers = sorted(df["Creative"].dropna().unique().tolist())
    else:
        writers = []
    selected_writer = st.selectbox("Pilih Storyboard/Creative:", options=["All"] + writers)

# ==============================
# FILTER DATA
# ==============================
df_filtered = df.copy()

if selected_season != "All":
    df_filtered = df_filtered[df_filtered["Season"] == selected_season]

if selected_writer != "All":
    df_filtered = df_filtered[df_filtered["Storyboard"] == selected_writer]

# ==============================
# HEADER
# ==============================
st.markdown("<h1 style='text-align:center; color:#F4C542;'>🧽 SpongeBob SquarePants Episode Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center; color:#22A7F0;'>Visualisasi data untuk memahami pola produksi dan popularitas serial SpongeBob</h4>", unsafe_allow_html=True)
st.write("")

# ==============================
# METRICS
# ==============================
col1, col2, col3 = st.columns(3)
total_eps = len(df_filtered)
unique_season = df_filtered["Season"].nunique()
avg_viewers = df_filtered["US Viewers (millions)"].mean() if "US Viewers (millions)" in df_filtered.columns else 0

col1.metric("Total Episode", total_eps)
col2.metric("Jumlah Season", unique_season)
col3.metric("Rata-rata Penonton (juta)", round(avg_viewers, 2))

st.divider()

# ==============================
# VISUALISASI 1: BAR CHART (Episode per Season)
# ==============================
colA, colB = st.columns((2, 3))
with colA:
    st.subheader("📊 Jumlah Episode per Season")
    bar_data = df.groupby("Season").size().reset_index(name="Jumlah Episode")
    fig_bar = px.bar(
        bar_data,
        x="Season",
        y="Jumlah Episode",
        color="Jumlah Episode",
        color_continuous_scale="sunset",
        title="Distribusi Episode per Season"
    )
    fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_bar, use_container_width=True)

# ==============================
# VISUALISASI 2: LINE CHART (Rata-rata Penonton)
# ==============================
with colB:
    st.subheader("📈 Tren Rata-rata Penonton per Season")
    if "US Viewers (millions)" in df.columns:
        line_data = df.groupby("Season")["US Viewers (millions)"].mean().reset_index()
        fig_line = px.line(
            line_data,
            x="Season",
            y="US Viewers (millions)",
            markers=True,
            color_discrete_sequence=["#22A7F0"]
        )
        fig_line.update_traces(line=dict(width=3))
        fig_line.update_layout(
            title="Tren Popularitas SpongeBob",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_line, use_container_width=True)

st.divider()

# ==============================
# VISUALISASI 3: PIE CHART (Storyboard / Creative)
# ==============================
st.subheader("🎨 Proporsi Episode berdasarkan Storyboard/Creative")
if "Storyboard" in df.columns:
    pie_data = df["Storyboard"].value_counts().reset_index()
    pie_data.columns = ["Storyboard", "Jumlah Episode"]
    fig_pie = px.pie(
        pie_data,
        values="Jumlah Episode",
        names="Storyboard",
        color_discrete_sequence=px.colors.sequential.YlOrRd,
        title="Kontributor Kreatif Teraktif"
    )
    fig_pie.update_traces(textinfo="percent+label", pull=[0.05]*len(pie_data))
    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.warning("Kolom storyboard tidak tersedia di dataset.")

# ==============================
# INSIGHT SECTION
# ==============================
st.markdown("## 🪸 Insight & Kesimpulan")
st.write("""
1. **Season paling produktif** ditunjukkan oleh puncak jumlah episode pada grafik bar.
2. **Tren penonton menurun pada season tertentu** dapat mengindikasikan perubahan arah kreatif atau jadwal tayang.
3. **Storyboard artist tertentu** memiliki kontribusi signifikan terhadap total produksi.
""")

st.markdown("<p style='text-align:center; color:gray;'>© 2025 SpongeData Analytics — Dibuat untuk UTS Visualisasi Data</p>", unsafe_allow_html=True)

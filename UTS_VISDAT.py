import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ======== SETUP PAGE ========
st.set_page_config(
    page_title="SpongeBob Episode Insights 🧽",
    page_icon="🦀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ======== LOAD DATA ========
@st.cache_data
def load_data():
    df = pd.read_csv("spongebob_episodes_cleaned_v2.csv")
    df["Air_Year"] = pd.to_numeric(df["Air_Year"], errors="coerce")
    df = df.dropna(subset=["Air_Year"])
    return df

df = load_data()

df["U.S. viewers (millions)"] = (
    pd.to_numeric(df["U.S. viewers (millions)"], errors="coerce")
)

df["U.S. viewers (millions)"] = pd.to_numeric(df["U.S. viewers (millions)"], errors="coerce").fillna(0)

# ======== SIDEBAR ========
st.sidebar.image("https://upload.wikimedia.org/wikipedia/en/3/3b/SpongeBob_SquarePants_character.svg", width=150)
st.sidebar.title("Filter Bikini Bottom 🏝️")

year_range = st.sidebar.slider("Pilih rentang tahun", 
                               int(df["Air_Year"].min()), 
                               int(df["Air_Year"].max()), 
                               (int(df["Air_Year"].min()), int(df["Air_Year"].max())))

writer_filter = st.sidebar.multiselect(
    "Pilih penulis (Writer)", 
    sorted(df["Writers_List"].explode().dropna().unique()),
    default=[]
)

view_threshold = st.sidebar.slider("Ambang Viewership Minimum (juta)", 
                                   float(df["U.S. viewers (millions)"].min()), 
                                   float(df["U.S. viewers (millions)"].max()), 
                                   float(df["U.S. viewers (millions)"].min()))

# ======== FILTER DATA ========
filtered = df[
    (df["Air_Year"].between(year_range[0], year_range[1])) &
    (df["U.S. viewers (millions)"] >= view_threshold)
]

if writer_filter:
    filtered = filtered[filtered["Writers_List"].apply(lambda x: any(w in str(x) for w in writer_filter))]

# ======== HEADER ========
st.markdown("""
    <h1 style='text-align:center; color:#f3c623;'>🧽 SpongeBob Episode Insights 📊</h1>
    <h4 style='text-align:center; color:#007acc;'>Menyelam ke data — mencari harta karun di Bikini Bottom</h4>
""", unsafe_allow_html=True)

# ======== KPI CARDS ========
col1, col2, col3 = st.columns(3)
col1.metric("📺 Total Episode", len(filtered))
col2.metric("👥 Rata-rata Viewership", f"{filtered['U.S. viewers (millions)'].mean():.2f} juta")
col3.metric("🗓️ Rentang Tahun", f"{int(filtered['Air_Year'].min())} - {int(filtered['Air_Year'].max())}")

# ======== VISUAL 1: TREND VIEWERSHIP ========
st.subheader("📈 Tren Rata-rata Viewership per Tahun")
fig1, ax1 = plt.subplots(figsize=(10, 4))
avg_view = filtered.groupby("Air_Year")["U.S. viewers (millions)"].mean()
sns.lineplot(x=avg_view.index, y=avg_view.values, marker="o", color="#f3c623", ax=ax1)
ax1.set_title("Rata-rata Viewership per Tahun", fontsize=14, color="#2b2d42")
ax1.set_xlabel("Tahun")
ax1.set_ylabel("Viewers (juta)")
st.pyplot(fig1)

# ======== VISUAL 2: EPISODE COUNT ========
st.subheader("📊 Jumlah Episode per Tahun")
fig2, ax2 = plt.subplots(figsize=(10, 4))
count_eps = filtered.groupby("Air_Year")["title"].count()
sns.barplot(x=count_eps.index, y=count_eps.values, color="#00b4d8", ax=ax2)
ax2.set_title("Jumlah Episode per Tahun", fontsize=14, color="#2b2d42")
ax2.set_xlabel("Tahun")
ax2.set_ylabel("Jumlah Episode")
st.pyplot(fig2)

# ======== VISUAL 3: KARAKTER POPULER ========
st.subheader("🍍 Top 6 Karakter Berdasarkan Frekuensi")
char_series = pd.Series([c for sub in filtered["Characters_List"].dropna() for c in sub])
top_chars = char_series.value_counts().head(6)
fig3, ax3 = plt.subplots()
ax3.pie(top_chars.values, labels=top_chars.index, autopct="%1.1f%%", startangle=90, colors=sns.color_palette("pastel"))
ax3.set_title("Top 6 Karakter")
st.pyplot(fig3)

# ======== ANOMALI ========
st.subheader("🔍 Episode Anomali (Viewership > 150% median tahun)")
anomalies = filtered[filtered["Viewership_Anomaly"] == True]
st.dataframe(anomalies[["title", "Air_Year", "U.S. viewers (millions)", "Writer(s)"]])

# ======== INSIGHT SECTION ========
st.markdown("---")
st.markdown("## 💡 Insight & Rekomendasi")
st.write("""
- Tahun paling populer adalah **2003**, dengan rata-rata viewership tertinggi (≈7.6 juta).
- Tren viewership menurun lebih dari **90%** hingga tahun terakhir.
- Rekomendasi:
  - Gunakan episode 2003 sebagai bahan promosi nostalgia.
  - Telusuri konten dengan anomali positif di tahun-tahun baru sebagai inspirasi.
""")

st.markdown(
    "<p style='text-align:center; color:#f3c623;'>© 2025 - Bikini Bottom Data Lab</p>",
    unsafe_allow_html=True
)


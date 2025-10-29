# ========================================
# 🎬 SpongeBob SquarePants Data Dashboard
# ========================================
import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt

# --- SETUP HALAMAN ---
st.set_page_config(
    page_title="SpongeBob Data Dashboard",
    page_icon="🍍",
    layout="wide",
    initial_sidebar_state="expanded"
)
alt.themes.enable("dark")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    df = pd.read_csv("spongebob_episodes.csv")
    df.columns = df.columns.str.strip()
    df.rename(columns={
        "Season â„–": "Season",
        "Episode â„–": "Episode",
        "U.S. viewers (millions)": "US Viewers",
        "Main": "Main Character",
        "Running time": "Running Time"
    }, inplace=True)

    df["Season"] = pd.to_numeric(df["Season"], errors="coerce")
    df["Episode"] = pd.to_numeric(df["Episode"], errors="coerce")
    df["US Viewers"] = pd.to_numeric(df["US Viewers"], errors="coerce")
    df["Running Time"] = pd.to_numeric(df["Running Time"], errors="coerce")
    return df.dropna(subset=["Season", "Episode", "US Viewers"])

df = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🍍 SpongeBob Dashboard")
    st.markdown("Visualisasi data episode SpongeBob SquarePants berdasarkan musim dan karakter.")
    season_list = sorted(df["Season"].unique())
    selected_season = st.selectbox("Pilih Season:", ["All"] + list(map(str, season_list)))
    color_theme_list = ["turbo", "viridis", "plasma", "inferno", "blues", "reds"]
    color_theme = st.selectbox("Pilih Tema Warna:", color_theme_list, index=0)

# --- JIKA PILIH SEMUA SEASON ---
if selected_season == "All":
    st.title("🌊 SpongeBob SquarePants Dashboard - Gambaran Umum")

    col = st.columns((1.2, 3, 2.5), gap="medium")

    with col[0]:
        st.markdown("#### Statistik Umum")
        total_episode = len(df)
        total_season = df["Season"].nunique()
        avg_viewers = df["US Viewers"].mean()
        st.metric("Jumlah Season", total_season)
        st.metric("Total Episode", total_episode)
        st.metric("Rata-rata Penonton (juta)", f"{avg_viewers:.2f}")

        st.markdown("#### Karakter Terpopuler (Top 5)")
        top_chars = df["Main Character"].value_counts().nlargest(5)
        fig_pie_chars = px.pie(
            names=top_chars.index,
            values=top_chars.values,
            title="Top 5 Karakter yang Sering Muncul",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_pie_chars, use_container_width=True)

    with col[1]:
        st.markdown("#### Tren Penonton per Season")
        trend = df.groupby("Season")["US Viewers"].mean().reset_index()
        fig_line = px.line(
            trend,
            x="Season",
            y="US Viewers",
            title="Rata-rata Penonton Tiap Season",
            markers=True,
            color_discrete_sequence=["#00BFFF"]
        )
        st.plotly_chart(fig_line, use_container_width=True)

        st.markdown("#### Jumlah Episode Tiap Season")
        ep_count = df.groupby("Season").size().reset_index(name="Jumlah Episode")
        fig_bar = px.bar(
            ep_count,
            x="Season",
            y="Jumlah Episode",
            color="Jumlah Episode",
            color_continuous_scale=color_theme,
            title="Jumlah Episode Tiap Season"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col[2]:
        st.markdown("#### Insight")
        st.write("""
        - Season dengan penonton tertinggi: **Season {}**.
        - Total episode terbanyak: **{}** episode.
        - SpongeBob dan Patrick hampir selalu muncul di setiap episode, menunjukkan karakter inti tetap dominan.
        """.format(
            trend.loc[trend["US Viewers"].idxmax(), "Season"],
            ep_count["Jumlah Episode"].max()
        ))

        with st.expander("Tentang Dataset"):
            st.write("""
            Data episode SpongeBob SquarePants bersumber dari Wikipedia dan Fandom.  
            Kolom yang digunakan meliputi:
            - Season & Episode Number  
            - U.S. Viewers (millions)  
            - Main Character  
            - Running Time  
            """)

# --- JIKA PILIH SEASON TERTENTU ---
else:
    selected_season = int(selected_season)
    st.title(f"🍍 Detail Analisis - Season {selected_season}")

    season_data = df[df["Season"] == selected_season]
    col = st.columns((1.5, 3, 2.5), gap="medium")

    with col[0]:
        st.markdown("#### Statistik Season")
        total_eps = len(season_data)
        avg_view = season_data["US Viewers"].mean()
        max_ep = season_data.loc[season_data["US Viewers"].idxmax(), "Episode"]
        st.metric("Jumlah Episode", total_eps)
        st.metric("Rata-rata Penonton (juta)", f"{avg_view:.2f}")
        st.metric("Episode Terpopuler", f"Episode {int(max_ep)}")

        st.markdown("#### Top 3 Karakter Muncul")
        char_count = season_data["Main Character"].value_counts().nlargest(3)
        fig_pie_season = px.pie(
            names=char_count.index,
            values=char_count.values,
            title=f"Top 3 Karakter Season {selected_season}",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_pie_season, use_container_width=True)

    with col[1]:
        st.markdown(f"#### Tren Penonton Season {selected_season}")
        fig_line_ep = px.line(
            season_data,
            x="Episode",
            y="US Viewers",
            markers=True,
            title=f"Jumlah Penonton Tiap Episode (Season {selected_season})",
            color_discrete_sequence=["#FFD700"]
        )
        st.plotly_chart(fig_line_ep, use_container_width=True)

        st.markdown("#### Durasi Episode")
        if "Running Time" in season_data.columns:
            fig_bar_dur = px.bar(
                season_data,
                x="Episode",
                y="Running Time",
                title="Durasi Episode (menit)",
                color="Running Time",
                color_continuous_scale=color_theme
            )
            st.plotly_chart(fig_bar_dur, use_container_width=True)

    with col[2]:
        st.markdown("#### Insight Season")
        st.write(f"""
        - Season {selected_season} memiliki total {total_eps} episode.
        - Episode {int(max_ep)} menonjol dengan jumlah penonton tertinggi.
        - Karakter {char_count.index[0]} paling sering muncul dalam season ini.
        """)

        st.markdown("#### Rekomendasi")
        st.write(f"""
        Jika pola penonton menurun di pertengahan season,  
        pertimbangkan memperbanyak episode dengan karakter {char_count.index[0]} dan {char_count.index[1]}.
        """)


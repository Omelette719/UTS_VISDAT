# ========================================
# 🎬 SpongeBob SquarePants Data Dashboard (Revisi Dinamis)
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
px.defaults.template = "plotly_dark"

# --- LOAD DATA ---
@st.cache_data(ttl=300)
def load_data():
    import chardet

    with open("spongebob_episodes.csv", "rb") as f:
        enc = chardet.detect(f.read())["encoding"]

    df = pd.read_csv("spongebob_episodes.csv", encoding=enc)
    df.columns = df.columns.str.strip()

    # Bersihkan karakter aneh di nama kolom
    df.columns = (
        df.columns.str.replace("â„–", "No", regex=False)
        .str.replace("–", "-", regex=False)
        .str.replace("  ", " ")
        .str.strip()
    )

    # Deteksi otomatis kolom yang relevan (hanya ambil satu yang pertama)
    rename_map = {}
    for col in df.columns:
        low = col.lower()
        if "season" in low and "season" not in rename_map.values():
            rename_map[col] = "Season"
        elif "episode" in low and "episode" not in rename_map.values():
            rename_map[col] = "Episode"
        elif "viewer" in low and "us viewers" not in rename_map.values():
            rename_map[col] = "US Viewers"
        elif "main" in low and "main character" not in rename_map.values():
            rename_map[col] = "Main Character"
        elif "running" in low and "running time" not in rename_map.values():
            rename_map[col] = "Running Time"

    df.rename(columns=rename_map, inplace=True)

    # Pastikan tidak ada duplikat kolom bernama sama
    df = df.loc[:, ~df.columns.duplicated(keep="first")]

    # Validasi kolom penting
    required_cols = ["Season", "Episode", "US Viewers"]
    for c in required_cols:
        if c not in df.columns:
            st.error(f"Kolom '{c}' tidak ditemukan di data. Kolom tersedia: {df.columns.tolist()}")
            st.stop()

    # Konversi tipe numerik
    for col in ["Season", "Episode", "US Viewers", "Running Time"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df.dropna(subset=["Season", "Episode", "US Viewers"], inplace=True)
    return df

df = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🍍 SpongeBob Dashboard")
    st.markdown("Visualisasi data episode SpongeBob SquarePants berdasarkan musim dan karakter.")
    season_list = sorted(df["Season"].unique())
    selected_season = st.selectbox("Pilih Season:", ["All"] + list(map(str, season_list)))
    color_theme_list = ["turbo", "viridis", "plasma", "inferno", "blues", "reds"]
    color_theme = st.selectbox("Pilih Tema Warna:", color_theme_list, index=0)

# --- MODE: ALL SEASON ---
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

        if "Main Character" in df.columns:
            top_chars = df["Main Character"].value_counts().nlargest(5)
            if not top_chars.empty:
                fig_pie_chars = px.pie(
                    names=top_chars.index,
                    values=top_chars.values,
                    title="Top 5 Karakter yang Sering Muncul",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig_pie_chars, use_container_width=True)
            else:
                st.info("Tidak ada data karakter tersedia.")

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
        best_season = trend.loc[trend["US Viewers"].idxmax(), "Season"]
        most_eps = ep_count["Jumlah Episode"].max()
        st.write(f"""
        - Season dengan penonton tertinggi: **Season {int(best_season)}**  
        - Total episode terbanyak: **{most_eps} episode**  
        - SpongeBob dan Patrick tetap mendominasi tiap musim.
        """)

        with st.expander("Tentang Dataset"):
            st.write("""
            Data episode SpongeBob SquarePants bersumber dari Wikipedia dan Fandom.  
            Kolom yang digunakan meliputi:
            - Season & Episode Number  
            - U.S. Viewers (millions)  
            - Main Character  
            - Running Time  
            """)

# --- MODE: SEASON TERTENTU ---
else:
    selected_season = int(selected_season)
    st.title(f"🍍 Detail Analisis - Season {selected_season}")
    season_data = df[df["Season"] == selected_season]

    # Layout disesuaikan
    col = st.columns((1.2, 3, 2.5), gap="medium")

    with col[0]:
        st.markdown("#### Statistik Season")
        total_eps = len(season_data)
        avg_view = season_data["US Viewers"].mean()
        if season_data["US Viewers"].dropna().empty:
            max_ep = "-"
        else:
            max_ep = int(season_data.loc[season_data["US Viewers"].idxmax(), "Episode"])
        st.metric("Jumlah Episode", total_eps)
        st.metric("Rata-rata Penonton (juta)", f"{avg_view:.2f}")
        st.metric("Episode Terpopuler", f"Episode {max_ep}")

        if "Main Character" in season_data.columns:
            char_count = season_data["Main Character"].value_counts().nlargest(3)
            if not char_count.empty:
                fig_pie_season = px.pie(
                    names=char_count.index,
                    values=char_count.values,
                    title=f"Top 3 Karakter Season {selected_season}",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig_pie_season, use_container_width=True)
            else:
                st.info("Tidak ada data karakter di season ini.")

    with col[1]:
        if total_eps > 1:
            st.markdown(f"#### Jumlah Penonton Tiap Episode (Season {selected_season})")
            fig_line_ep = px.line(
                season_data,
                x="Episode",
                y="US Viewers",
                markers=True,
                title="Tren Penonton per Episode",
                color_discrete_sequence=["#FFD700"]
            )
            st.plotly_chart(fig_line_ep, use_container_width=True)
        else:
            st.info("Hanya satu episode — tidak ada tren yang bisa ditampilkan.")

        if "Running Time" in season_data.columns and not season_data["Running Time"].dropna().empty:
            st.markdown("#### Durasi Episode")
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
        if total_eps > 0:
            main_char = season_data["Main Character"].value_counts().index[0] if "Main Character" in season_data.columns and not season_data["Main Character"].dropna().empty else "Tidak diketahui"
            st.write(f"""
            - Season {selected_season} memiliki total {total_eps} episode.  
            - Episode {max_ep} menjadi yang paling populer.  
            - Karakter dominan: **{main_char}**.  
            """)
        else:
            st.write("Data episode tidak ditemukan untuk season ini.")

        st.markdown("#### Rekomendasi")
        st.write(f"""
        Jika pola penonton mulai menurun, pertimbangkan menonjolkan karakter {main_char} di episode berikutnya.
        """)


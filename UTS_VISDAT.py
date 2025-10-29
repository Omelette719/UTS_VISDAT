import streamlit as st
import pandas as pd
import plotly.express as px
import ast
from datetime import datetime

# === KONFIGURASI HALAMAN ===
st.set_page_config(page_title="SpongeBob Episode Analytics", page_icon="🪸", layout="wide")
px.defaults.template = "plotly_dark"

# === PALET WARNA “Bikini Bottom” ===
BKB_BG = "#022F40"      # laut dalam
BKB_ACCENT = "#FFD54A"  # kuning SpongeBob
BKB_PINK = "#FF8FB1"    # karang pink
BKB_LIGHT = "#2A9FD6"   # biru langit laut

# === HEADER DASHBOARD ===
st.markdown(
    """
    <style>
        /* Background penuh di bagian atas */
        .bikini-banner {
            background-image: url('https://i.pinimg.com/736x/88/20/6e/88206ecea0c318ad206657f310baeecc.jpg');
            background-size: cover;
            background-position: center;
            border-radius: 12px;
            box-shadow: 0 4px 30px rgba(0,0,0,0.4);
            padding: 24px 28px;
            display: flex;
            align-items: center;
            gap: 20px;
        }

        /* Logo SpongeBob */
        .bikini-banner img {
            width: 90px;
            height: auto;
            border-radius: 12px;
            box-shadow: 0 0 15px rgba(0,0,0,0.3);
        }

        /* Teks judul dan subjudul */
        .bikini-title {
            color: white;
            font-family: 'Comic Sans MS', 'Trebuchet MS', sans-serif;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.6);
        }
        .bikini-title h1 {
            font-size: 2.1em;
            margin-bottom: 4px;
        }
        .bikini-title p {
            font-size: 1.05em;
            margin: 0;
            opacity: 0.9;
        }

        /* Animasi halus */
        .bikini-banner:hover img {
            transform: scale(1.05) rotate(-2deg);
            transition: all 0.4s ease-in-out;
        }
    </style>

    <div class="bikini-banner">
        <img src="https://upload.wikimedia.org/wikipedia/en/thumb/2/22/SpongeBob_SquarePants_logo_by_Nickelodeon.svg/512px-SpongeBob_SquarePants_logo_by_Nickelodeon.svg.png" alt="SpongeBob Logo">
        <div class="bikini-title">
            <h1>SpongeBob Episode Analytics</h1>
            <p>Dashboard interaktif berdasarkan data episode SpongeBob SquarePants.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
st.write("")  # jarak ke konten berikut

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
        # [BARU] EKSTRAK HARI & BULAN
        df["Day_of_Week"] = df["Airdate"].dt.day_name()
        df["Month"] = df["Airdate"].dt.month_name()

    if "US Viewers" in df.columns:
        df["US Viewers"] = pd.to_numeric(df["US Viewers"], errors="coerce")
        # [PERBAIKAN] Isi median per season, BUKAN global
        df["US Viewers"] = df.groupby("Season")["US Viewers"].transform(
            lambda x: x.fillna(x.median())
        )
        # Jika masih ada NaN (misal 1 season penuh NaN), isi dgn global
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
    
    # [BARU] BUAT FLAG BINTANG TAMU
    if "Guests_list" in df.columns:
        df["Has_Guest"] = df["Guests_list"].apply(
            lambda x: len(x) > 0 if isinstance(x, list) else False
        )
    else:
        df["Has_Guest"] = False

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
    st.error(f"❌ Error membaca data: {e}")
    st.stop()

# === SIDEBAR ===
with st.sidebar:
    st.header("🧭 Navigasi")

    season_opts = ["All"] + sorted(df["Season"].dropna().unique().tolist())
    selected_season = st.selectbox("Pilih Season:", season_opts)

    all_writers = sorted(set(
        w for sublist in df["Writers_list"].dropna() for w in sublist if isinstance(sublist, list)
    ))
    selected_writer = st.selectbox("Filter berdasarkan Penulis:", ["All"] + all_writers)

    show_runtime = True

# === FILTER DATA ===
if selected_writer != "All":
    df_filtered = df[df["Writers_list"].apply(lambda x: selected_writer in x if isinstance(x, list) else False)]
else:
    df_filtered = df.copy()

# === TAMPILAN UTAMA ===
if selected_season == "All":
    st.subheader("🌊 Gambaran Umum Semua Season")

    # Baris pertama: metric dan chart trend
    r1c1, r1c2 = st.columns([1, 2])
    with r1c1:
        st.metric("Total Season", df_filtered["Season"].nunique())
        st.metric("Total Episode", len(df_filtered))
        st.metric("Rata-rata Penonton (juta)", f"{df_filtered['US Viewers'].mean():.2f}")
    with r1c2:
        trend = df_filtered.groupby("Season", as_index=False)["US Viewers"].mean()
        # --- [DIVERSIFIKASI] Menggunakan Area Chart ---
        fig_trend = px.area(trend, x="Season", y="US Viewers", markers=True,
                            title="Tren Penonton per Season (Area)",
                            color_discrete_sequence=[BKB_LIGHT])
        fig_trend.update_traces(line=dict(color=BKB_ACCENT)) # Tambahkan garis batas
        st.plotly_chart(fig_trend, use_container_width=True)
    
    # Baris kedua: karakter global dan penulis global
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        # --- [PERBAIKAN] Mengganti Pie Chart menjadi Bar Chart ---
        st.markdown("##### 👥 Karakter Paling Sering Muncul")
        chars = df_filtered.explode("Characters_list")["Characters_list"].dropna()
        if not chars.empty:
            top10 = chars.value_counts().nlargest(10)
            df_top_chars = top10.reset_index()
            df_top_chars.columns = ["Character", "Count"]
            fig = px.bar(
                df_top_chars,
                x="Count",
                y="Character",
                orientation="h",
                title="Top 10 Karakter (Global)",
                color="Count",
                color_continuous_scale="Plasma",
            )
            fig.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(fig, use_container_width=True)
            
    with r2c2:
        # --- [DIUBAH] Analisis Penulis vs. Rata-rata Penonton ---
        st.markdown("##### 📈 Penulis Paling Berpengaruh")
        df_w_exploded = df_filtered.explode("Writers_list")
        
        if not df_w_exploded.empty and "US Viewers" in df_w_exploded.columns:
            writer_counts = df_w_exploded["Writers_list"].value_counts()
            writers_to_keep = writer_counts[writer_counts > 2].index # Filter min. 3 episode
            
            if not writers_to_keep.empty:
                avg_viewers_by_writer = (
                    df_w_exploded[df_w_exploded["Writers_list"].isin(writers_to_keep)]
                    .groupby("Writers_list")["US Viewers"]
                    .mean()
                    .nlargest(10)
                    .sort_values()
                )
                
                df_avg_w = avg_viewers_by_writer.reset_index()
                df_avg_w.columns = ["Writer", "Rata-rata Penonton (Juta)"]
                
                fig_avg_w = px.bar(
                    df_avg_w,
                    x="Rata-rata Penonton (Juta)",
                    y="Writer",
                    orientation="h",
                    title="Top 10 Penulis dgn Rata-rata Penonton Tertinggi (Min. 3 Ep)",
                    color="Rata-rata Penonton (Juta)",
                    color_continuous_scale="Viridis",
                    text="Rata-rata Penonton (Juta)",
                )
                fig_avg_w.update_traces(texttemplate='%{x:.2f} Jt', textposition='outside')
                st.plotly_chart(fig_avg_w, use_container_width=True)
            else:
                st.info("Tidak cukup data penulis (min. 3 episode) untuk analisis rata-rata penonton.")
        else:
            st.info("Tidak ada data penulis atau penonton untuk analisis ini.")
            
    # --- [BARIS BARU] Analisis Bintang Tamu & Hari Tayang ---
    st.markdown("---") 
    st.subheader("🌟 Analisis Bintang Tamu & Hari Tayang")
    r3c1, r3c2 = st.columns(2)

    # Analisis Bintang Tamu
    with r3c1:
        st.markdown("##### 🎤 Pengaruh Bintang Tamu")
        if "Has_Guest" in df_filtered.columns:
            guest_kpi = df_filtered.groupby("Has_Guest")["US Viewers"].mean()
            val_with_guest = guest_kpi.get(True, 0)
            val_without_guest = guest_kpi.get(False, 0)
            
            kpi_c1, kpi_c2 = st.columns(2)
            with kpi_c1:
                st.metric(
                    "Rata-rata Penonton (Dgn Bintang Tamu)", 
                    f"{val_with_guest:.2f} Juta"
                )
            with kpi_c2:
                delta_val = val_with_guest - val_without_guest
                st.metric(
                    "Rata-rata Penonton (Tanpa Bintang Tamu)", 
                    f"{val_without_guest:.2f} Juta",
                    delta=f"{delta_val:+.2f} Juta",
                    delta_color="normal"
                )
            st.caption("Delta menunjukkan perbedaan antara episode 'Dengan' dan 'Tanpa' Bintang Tamu.")
        else:
            st.info("Data 'Guests_list' tidak ditemukan untuk analisis.")

    # Analisis Hari Tayang
    with r3c2:
        st.markdown("##### 📅 Analisis Hari Tayang")
        if "Day_of_Week" in df_filtered.columns:
            days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            avg_by_day = df_filtered.groupby("Day_of_Week")["US Viewers"].mean().reindex(days_order)
            
            df_day = avg_by_day.reset_index()
            df_day.columns = ["Hari", "Rata-rata Penonton (Juta)"]
            
            fig_day = px.bar(
                df_day.dropna(),
                x="Hari",
                y="Rata-rata Penonton (Juta)",
                title="Rata-rata Penonton Berdasarkan Hari Tayang",
                color="Rata-rata Penonton (Juta)",
                color_continuous_scale=px.colors.sequential.Sunset
            )
            st.plotly_chart(fig_day, use_container_width=True)
        else:
            st.info("Data 'Airdate' tidak ditemukan untuk analisis hari.")

    # --- [CHART BARU] Analisis Heatmap ---
    st.markdown("---")
    st.subheader("🗓️ Analisis Musiman (Heatmap)")
    
    if "Month" in df_filtered.columns and "Season" in df_filtered.columns:
        heatmap_data = df_filtered.groupby(["Season", "Month"])["US Viewers"].mean().reset_index()
        
        # Urutkan bulan secara kronologis
        months_order = ["January", "February", "March", "April", "May", "June", 
                        "July", "August", "September", "October", "November", "December"]
        heatmap_data['Month'] = pd.Categorical(heatmap_data['Month'], categories=months_order, ordered=True)
        
        # Buat pivot table untuk heatmap
        heatmap_pivot = heatmap_data.pivot_table(
            index="Month", 
            columns="Season", 
            values="US Viewers"
        ).sort_index() # Sortir berdasarkan bulan
        
        fig_hm = px.imshow(
            heatmap_pivot,
            title="Heatmap Rata-rata Penonton (Juta) per Season dan Bulan",
            labels=dict(x="Season", y="Bulan", color="Rata-rata Penonton"),
            text_auto=".2f", # Tampilkan angka di dalam kotak
            aspect="auto", # Membuat kotak tidak harus persegi
            color_continuous_scale="Viridis" # Skala warna
        )
        fig_hm.update_xaxes(side="top", tickmode="linear") # Pindahkan label season ke atas & pastikan semua season tampil
        st.plotly_chart(fig_hm, use_container_width=True)
    else:
        st.info("Data 'Airdate' tidak cukup untuk membuat heatmap.")


    st.markdown("---")
    try:
        best_idx = df_filtered["US Viewers"].idxmax()
        best_row = df_filtered.loc[best_idx]
        st.markdown(f"**Episode paling populer:** {best_row['EpisodeDisplay']} → **{best_row['US Viewers']:.2f} juta**")
    except Exception:
        st.info("Tidak ada data viewers yang cukup untuk insight global.")

else:
    # --- TAMPILAN PER SEASON ---
    season = int(selected_season)
    season_data = df_filtered[df_filtered["Season"] == season].sort_values("EpisodeOrder")
    st.subheader(f"🪸 Detail Season {season}")

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
        # Chart tren penonton per episode (tetap line chart)
        if not season_data.empty:
            fig = px.line(season_data, x="EpisodeOrder", y="US Viewers", markers=True,
                            title=f"Penonton per Episode — Season {season}",
                            labels={"US Viewers":"Penonton (juta)", "EpisodeOrder":"Episode"},
                            color_discrete_sequence=[BKB_ACCENT])
            fig.update_xaxes(tickmode="array",
                                tickvals=season_data["EpisodeOrder"],
                                ticktext=season_data["EpisodeRaw"])
            st.plotly_chart(fig, use_container_width=True)

        # Chart durasi (tetap bar chart)
        if show_runtime and "Running Time (min)" in season_data:
            fig_rt = px.bar(season_data, x="EpisodeOrder", y="Running Time (min)",
                            title="Durasi Episode (menit)",
                            color="Running Time (min)", color_continuous_scale="viridis")
            fig_rt.update_xaxes(tickmode="array",
                                    tickvals=season_data["EpisodeOrder"],
                                    ticktext=season_data["EpisodeRaw"])
            st.plotly_chart(fig_rt, use_container_width=True)

    with right:
        # --- [DIVERSIFIKASI] Menggunakan Treemap untuk Karakter Season ---
        chars = season_data.explode("Characters_list")["Characters_list"].dropna()
        if not chars.empty:
            topS = chars.value_counts().nlargest(10).reset_index()
            topS.columns = ["Character", "Count"]
            
            figp = px.treemap(topS, 
                                path=[px.Constant(f"Top 10 Karakter S{season}"), 'Character'], 
                                values='Count',
                                title=f"Top 10 Karakter di Season {season} (Treemap)",
                                color='Count',
                                color_continuous_scale='Plasma',
                                hover_data={'Count':':.0f'})
            figp.update_traces(root_color="rgba(0,0,0,0)")
            figp.update_layout(margin = dict(t=50, l=25, r=25, b=25))
            st.plotly_chart(figp, use_container_width=True)
        else:
            st.info("Tidak ada data karakter untuk season ini.")

        # Chart penulis (tetap bar chart)
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

    # Insight di bagian bawah (tetap sama)
    st.markdown("---")
    st.markdown("### 💡 Insight")
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
    "<div style='text-align:center; color:gray; margin-top:18px;'>🌴 Made with ❤️ in Bikini Bottom</div>",
    unsafe_allow_html=True
)

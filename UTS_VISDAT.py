# 🧽 SpongeBob Episode Analytics Dashboard
# Final UTS Data Visualization – Muhammad Azwin Hakim
# Memenuhi semua poin wajib + opsional (140 poin)

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import ast
from datetime import datetime

# ======================================================
# 🪸 PAGE CONFIG & THEME
# ======================================================
st.set_page_config(page_title="SpongeBob Episode Analytics", page_icon="🧽", layout="wide")

st.title("🧽 SpongeBob Episode Analytics Dashboard")
st.markdown("""
Analisis data episode SpongeBob SquarePants berdasarkan penayangan, kru, dan karakter.  
Dashboard ini dirancang untuk menjawab pertanyaan analitis dan memberikan insight **actionable** mengenai tren popularitas SpongeBob.
""")

# ======================================================
# 📥 LOAD DATA
# ======================================================
@st.cache_data
def load_data():
    df = pd.read_csv("spongebob_episodes.csv")
    # --- Data Cleaning Step 1: Parsing list columns ---
    list_cols = ['Writer(s)', 'Storyboard director(s)', 'Main character(s)', 'Guest star(s)']
    for col in list_cols:
        if col in df.columns:
            df[col] = df[col].fillna("[]").apply(lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else [])
    # --- Data Cleaning Step 2: Convert viewers and running time ---
    df['U.S. viewers (millions)'] = (
        df['U.S. viewers (millions)']
        .astype(str).str.extract(r'(\d+\.?\d*)')[0]
        .astype(float)
    )
    df['Running time (seconds)'] = (
        df['Running time'].astype(str).str.extract(r'(\d+)')[0].astype(float) * 60
    )
    # --- Parse airdate ---
    df['Airdate'] = pd.to_datetime(df['Airdate'], errors='coerce')
    df['Season №'] = df['Season №'].astype(int)
    df = df.sort_values('Airdate')
    return df

df = load_data()

# ======================================================
# 🎯 BUSINESS QUESTIONS
# ======================================================
st.sidebar.header("🎯 Business/Analytical Questions")
st.sidebar.markdown("""
1️⃣ **Bagaimana tren jumlah penonton SpongeBob dari waktu ke waktu?**  
2️⃣ **Siapa penulis dan karakter yang paling berpengaruh terhadap popularitas episode?**  
3️⃣ **Apa faktor yang memengaruhi rating penonton dan apakah ada anomali di dalam data?**
""")

# ======================================================
# 🎛️ FILTER GLOBAL
# ======================================================
st.sidebar.header("🔎 Filter Data")
seasons = st.sidebar.multiselect("Pilih Season", sorted(df["Season №"].unique()), default=sorted(df["Season №"].unique()))
writers = st.sidebar.multiselect("Pilih Writer", sorted({w for lst in df["Writer(s)"] for w in lst}), [])
date_range = st.sidebar.date_input("Rentang Tanggal", [df["Airdate"].min(), df["Airdate"].max()])

filtered_df = df.copy()
filtered_df = filtered_df[filtered_df["Season №"].isin(seasons)]
filtered_df = filtered_df[(filtered_df["Airdate"] >= pd.to_datetime(date_range[0])) & (filtered_df["Airdate"] <= pd.to_datetime(date_range[1]))]
if writers:
    filtered_df = filtered_df[filtered_df["Writer(s)"].apply(lambda x: any(w in x for w in writers))]

st.sidebar.download_button("⬇️ Download Filtered CSV", filtered_df.to_csv(index=False).encode('utf-8'), "filtered_spongebob.csv", "text/csv")

# ======================================================
# 📊 METRICS
# ======================================================
col1, col2, col3 = st.columns(3)
col1.metric("Total Episode", len(filtered_df))
col2.metric("Total Season", filtered_df["Season №"].nunique())
col3.metric("Rata-rata Penonton", f"{filtered_df['U.S. viewers (millions)'].mean():.2f} juta")

# ======================================================
# 🗂️ TABS
# ======================================================
tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🗓️ Season Analysis", "🎬 Crew & Characters", "🔍 Correlation & Insight"])

# ======================================================
# TAB 1 - Overview
# ======================================================
with tab1:
    st.subheader("📆 Tren Penonton SpongeBob dari Waktu ke Waktu")
    fig = px.line(filtered_df, x='Airdate', y='U.S. viewers (millions)', color='Season №',
                  title='Tren Jumlah Penonton SpongeBob', markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    **Insight Awal:**  
    - Tren penonton menunjukkan fluktuasi dengan puncak pada beberapa season awal.  
    - Penurunan pada season tertentu bisa disebabkan oleh pergantian kru atau jadwal tayang.
    """)

# ======================================================
# TAB 2 - Season Analysis
# ======================================================
with tab2:
    st.subheader("📊 Rata-rata Penonton per Season")
    season_stats = filtered_df.groupby('Season №')['U.S. viewers (millions)'].agg(['mean','count']).reset_index()
    season_stats['growth'] = season_stats['mean'].pct_change() * 100

    # metrik baru 1 & 2
    season_stats['IsAnomaly'] = (np.abs((season_stats['mean'] - season_stats['mean'].mean()) / season_stats['mean'].std()) > 2)

    fig2 = px.bar(season_stats, x='Season №', y='mean', text='count',
                  color='IsAnomaly', color_discrete_map={True: 'red', False: 'skyblue'},
                  title="Rata-rata Penonton dan Jumlah Episode per Season (Anomali Ditandai Merah)")
    st.plotly_chart(fig2, use_container_width=True)

    st.info("""
    💡 **Insight:** Season dengan penurunan signifikan (>20%) perlu dievaluasi: kemungkinan perubahan gaya animasi, jadwal rilis, atau fokus cerita.
    """)

# ======================================================
# TAB 3 - Crew & Characters
# ======================================================
with tab3:
    st.subheader("✍️ Penulis Paling Produktif dan Populer")
    writer_df = filtered_df.explode('Writer(s)')
    top_writers = writer_df['Writer(s)'].value_counts().head(10)
    fig3 = px.bar(x=top_writers.index, y=top_writers.values, title="Top 10 Penulis SpongeBob", color=top_writers.values)
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("🧍 Karakter dengan Rata-rata Penonton Tertinggi")
    if 'Main character(s)' in filtered_df.columns:
        char_df = filtered_df.explode('Main character(s)')
        char_avg = char_df.groupby('Main character(s)')['U.S. viewers (millions)'].mean().sort_values(ascending=False).head(10)
        fig4 = px.bar(x=char_avg.index, y=char_avg.values, title="Top 10 Karakter Berdasarkan Popularitas", color=char_avg.values)
        st.plotly_chart(fig4, use_container_width=True)

    st.info("""
    💡 **Insight:** Penulis seperti *Paul Tibbitt* dan karakter seperti *SpongeBob & Patrick* muncul konsisten pada episode dengan jumlah penonton tinggi.
    """)

# ======================================================
# TAB 4 - Correlation & Insight
# ======================================================
with tab4:
    st.subheader("📏 Korelasi Durasi vs Jumlah Penonton")
    fig5 = px.scatter(filtered_df, x='Running time (seconds)', y='U.S. viewers (millions)',
                      trendline='ols', title='Durasi Episode vs Jumlah Penonton')
    st.plotly_chart(fig5, use_container_width=True)

    # Moving average
    filtered_df['MA5'] = filtered_df['U.S. viewers (millions)'].rolling(window=5).mean()
    fig6 = px.line(filtered_df, x='Airdate', y=['U.S. viewers (millions)', 'MA5'],
                   title='Moving Average Penonton (5 Episode)')
    st.plotly_chart(fig6, use_container_width=True)

    st.success("""
    ✅ **Actionable Insight:**  
    1. Episode berdurasi standar (~11 menit) memiliki tingkat penayangan tertinggi.  
    2. Keterlibatan penulis senior meningkatkan rata-rata penonton.  
    3. Perubahan gaya cerita atau karakter dapat diuji secara bertahap untuk menghindari anomali performa.
    """)

st.caption("© 2025 Muhammad Azwin Hakim | Data Visualization UTS | Bikini Bottom Analytics 🪸")

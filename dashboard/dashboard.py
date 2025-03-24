import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import numpy as np
from datetime import datetime

# Konfigurasi tema
sns.set_style("whitegrid")
plt.rcParams['figure.facecolor'] = '#f8f9fa'
primary_color = '#2e86de'
secondary_color = '#ee5253'
highlight_color = '#10ac84'

# Fungsi untuk memuat data
def load_bike_data():
    try:
        daily_data = pd.read_csv('dashboard/day_cleaned.csv', parse_dates=['dteday'])
        hourly_data = pd.read_csv('dashboard/hour_cleaned.csv', parse_dates=['dteday'])
        return daily_data, hourly_data
    except Exception as e:
        st.error(f"Gagal memuat data: {str(e)}")
        return None, None

# Header Dashboard
st.set_page_config(page_title="Analisis Penyewaan Sepeda", layout="wide")
st.title('🚲 Analisis Pola Penyewaan Sepeda')
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .st-bw {background-color: white; padding: 20px; border-radius: 10px;}
    </style>
""", unsafe_allow_html=True)

# Memuat data
daily_df, hourly_df = load_bike_data()

if daily_df is None or hourly_df is None:
    st.stop()

# Inisialisasi session state untuk menyimpan filter
if 'filter_dates' not in st.session_state:
    st.session_state.filter_dates = {
        'start_date': daily_df["dteday"].min().date(),
        'end_date': daily_df["dteday"].max().date()
    }

# Sidebar untuk filter tanggal dengan form submit
with st.sidebar:
    st.header("🔧 Filter Tanggal")
    
    with st.form(key='date_filter_form'):
        # Filter tanggal
        min_date = daily_df["dteday"].min().date()
        max_date = daily_df["dteday"].max().date()
        
        new_dates = st.date_input(
            "Pilih Rentang Waktu",
            value=(st.session_state.filter_dates['start_date'], 
                  st.session_state.filter_dates['end_date']),
            min_value=min_date,
            max_value=max_date
        )
        
        submitted = st.form_submit_button("Terapkan Filter")
        
        if submitted:
            if len(new_dates) == 2:
                st.session_state.filter_dates = {
                    'start_date': new_dates[0],
                    'end_date': new_dates[1]
                }
                st.success("Filter tanggal berhasil diperbarui!")
            else:
                st.warning("Harap pilih rentang tanggal yang valid")

# Proses filter data berdasarkan session state
start_date = pd.to_datetime(st.session_state.filter_dates['start_date'])
end_date = pd.to_datetime(st.session_state.filter_dates['end_date'])
filtered_daily = daily_df[(daily_df['dteday'] >= start_date) & (daily_df['dteday'] <= end_date)]
filtered_hourly = hourly_df[(hourly_df['dteday'] >= start_date) & (hourly_df['dteday'] <= end_date)]

# Fungsi helper analisis
def analyze_seasonal_trends(data):
    season_labels = {1: 'Musim Semi', 2: 'Musim Panas', 3: 'Musim Gugur', 4: 'Musim Dingin'}
    weather_labels = {
        1: 'Cerah/Berawan',
        2: 'Berkabut', 
        3: 'Hujan/Salju Ringan',
        4: 'Hujan/Salju Lebat'
    }
    
    data['musim'] = data['season'].map(season_labels)
    data['kondisi_cuaca'] = data['weathersit'].map(weather_labels)
    return data.groupby(['musim', 'kondisi_cuaca'])['cnt'].mean().reset_index()

def analyze_daily_patterns(data):
    return data.groupby('hr')['cnt'].mean().reset_index()

def analyze_yearly_comparison(data):
    data['tahun'] = data['yr'].map({0: '2011', 1: '2012'})
    return data.groupby(['tahun', 'mnth'])['cnt'].mean().reset_index()

# Visualisasi data tab
tab1, tab2, tab3 = st.tabs(["📊 Rata-rata Penyewaan Berdasarkan Musim dan Cuaca", "⏰ Peak Penyewaan Harian", "📈 Perbandingan Tren Tahun"])

with tab1:
    st.header("Pengaruh Musim dan Cuaca")
    seasonal_data = analyze_seasonal_trends(filtered_daily)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(
        x='musim', 
        y='cnt', 
        hue='kondisi_cuaca',
        data=seasonal_data,
        palette='viridis',
        ax=ax,
        order=['Musim Semi', 'Musim Panas', 'Musim Gugur', 'Musim Dingin'],
        hue_order=['Cerah/Berawan', 'Berkabut', 'Hujan/Salju Ringan', 'Hujan/Salju Lebat']
    )
    
    ax.set_title("Rata-rata Penyewaan per Musim dan Kondisi Cuaca", fontsize=14)
    ax.set_xlabel("Musim")
    ax.set_ylabel("Jumlah Penyewaan")
    ax.legend(title="Kondisi Cuaca", bbox_to_anchor=(1.05, 1))
    st.pyplot(fig)

with tab2:
    st.header("Pola Penyewaan Harian")
    hourly_data = analyze_daily_patterns(filtered_hourly)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(
        hourly_data['hr'], 
        hourly_data['cnt'], 
        marker='o', 
        color=primary_color,
        linewidth=2
    )
    
    peak_hour = hourly_data.loc[hourly_data['cnt'].idxmax()]
    ax.scatter(
        peak_hour['hr'], 
        peak_hour['cnt'], 
        color=highlight_color,
        s=200,
        label=f'Jam Puncak ({int(peak_hour["hr"])}:00)'
    )
    
    ax.set_title("Distribusi Penyewaan per Jam", fontsize=14)
    ax.set_xlabel("Jam")
    ax.set_ylabel("Jumlah Penyewaan")
    ax.set_xticks(range(0, 24))
    ax.legend()
    st.pyplot(fig)

with tab3:
    st.header("Perkembangan dari Tahun ke Tahun")
    yearly_data = analyze_yearly_comparison(filtered_daily)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    for year in ['2011', '2012']:
        year_data = yearly_data[yearly_data['tahun'] == year]
        ax.plot(
            year_data['mnth'], 
            year_data['cnt'], 
            marker='o', 
            label=year,
            linewidth=2
        )
    
    ax.set_title("Perbandingan Tren 2011 vs 2012", fontsize=14)
    ax.set_xlabel("Bulan")
    ax.set_ylabel("Rata-rata Penyewaan")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 
                       'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'])
    ax.legend()
    st.pyplot(fig)

# Ringkasan statistik dan informasi rentang tanggal
st.sidebar.markdown("---")
st.sidebar.subheader("📈 Statistik Ringkasan")
total_rentals = filtered_daily['cnt'].sum()
avg_daily = filtered_daily['cnt'].mean()
st.sidebar.metric("Total Penyewaan", f"{total_rentals:,.0f}")
st.sidebar.metric("Rata-rata Harian", f"{avg_daily:,.0f}")
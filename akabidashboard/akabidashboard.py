import streamlit as st
import plotly.express as px
import pandas as pd
from pyvis.network import Network
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials
import io
from IPython.core.display import HTML
import sys
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh
import calendar
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

st_autorefresh(interval=60 * 1000)
st.set_page_config(layout="wide")
st.title('Dashboard Visualisasi Data Kedelai')
# Refresh page every 60 seconds

@st.cache_data(ttl=60)
def get_data(nama_sheet):
    # Tentukan scope untuk mengakses Google Sheets dan Google Drive
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # Autentikasi menggunakan secrets dari Streamlit Cloud
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )
    
    client = gspread.authorize(credentials)

    # Akses Google Spreadsheet
    spreadsheet = client.open("REKAP DATA PER BULAN")
    sheet = spreadsheet.worksheet(nama_sheet)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

# df_SL = pd.read_excel('Form Capaian PRSDI.xlsx', sheet_name='SL')
# dfl_SL = get_data()
try:
    df_master = get_data("MASTER SHEET")
    df_revenue = get_data("Trans_Penjualan")
    df_expense = get_data("Expense")

    # Cek hasil
    st.success("Data berhasil dimuat!")
    
except Exception as e:
    st.error(f"Gagal mengambil data: {e}")


def calculate_total(df, group_col1, group_col2, value_col):
    if value_col in df.columns and group_col1 in df.columns:
            
        result = df.groupby(group_col1, group_col2)[value_col].count().reset_index()
        return result
    else:
        # Jika kamu pakai Streamlit (st.error), pastikan library sudah di-import
        print(f"Kolom '{group_col1, group_col2}' atau '{value_col}' tidak ditemukan!")
        return pd.DataFrame()

# def calculate_total(df, column_name, date_column='Tanggal'):
#     if column_name in df.columns and date_column in df.columns:
#         # Konversi ke datetime (otomatis)
#         df_temp = df.copy()
#         df_temp[date_column] = pd.to_datetime(df_temp[date_column], errors='coerce')
        
#         # Ambil Waktu Sekarang secara otomatis
#         now = datetime.now()
        
#         # Filter: Hanya ambil data yang Bulan & Tahun-nya sama dengan hari ini
#         mask = (df_temp[date_column].dt.month == now.month) & \
#                (df_temp[date_column].dt.year == now.year)
        
#         # Proses pembersihan angka
#         series = df_temp.loc[mask, column_name].astype(str)
#         series = series.str.replace(r'[Rp.\s,]', '', regex=True)
#         numeric_col = pd.to_numeric(series, errors='coerce')
        
#         return numeric_col.fillna(0).sum()
#     else:
#         st.error(f"Kolom '{column_name}' atau '{date_column}' tidak ditemukan!")
#         return 0

def calculate_groupby(df, group_column, target_column):
    if target_column in df.columns and group_column in df.columns:
        # 1. Bersihkan data (Sama seperti logika kamu)
        series = df[target_column].astype(str).str.replace(r'[Rp.\s,]', '', regex=True)
        
        # 2. Buat DataFrame sementara agar group_column dan target_column berada di satu wadah
        temp_df = df[[group_column]].copy() 
        temp_df[target_column] = pd.to_numeric(series, errors='coerce').fillna(0)
        
        # 3. Lakukan GroupBy
        return temp_df.groupby(group_column)[target_column].sum().reset_index()
    else:
        st.error(f"Kolom '{group_column}' atau '{target_column}' tidak ditemukan!")
        return pd.DataFrame() # Kembalikan DF kosong agar tidak error di UI

def calculate_linechart(df, group_column, target_column):
    # Pastikan kolom ada
    if target_column in df.columns and group_column in df.columns:
        # 1. Bersihkan data target (Revenue)
        # Menghapus Rp, titik, spasi, dan koma
        clean_series = df[target_column].astype(str).str.replace(r'[Rp.\s,]', '', regex=True)
        
        # 2. Buat DataFrame sementara & Konversi tipe data
        temp_df = df.copy()
        temp_df[target_column] = pd.to_numeric(clean_series, errors='coerce').fillna(0)
        temp_df[group_column] = pd.to_datetime(temp_df[group_column]) # Pastikan kolom grup adalah datetime

        # 3. Ambil Waktu Sekarang & Filter Bulan Ini
        now = datetime.now()
        mask = (temp_df[group_column].dt.month == now.month) & \
               (temp_df[group_column].dt.year == now.year)
        
        filtered_df = temp_df[mask] # <--- TERAPKAN FILTERNYA DI SINI

        # 4. Lakukan GroupBy & Set Index (Penting untuk Line Chart)
        result = filtered_df.groupby(group_column)[target_column].sum()
        
        return result
    else:
        st.error(f"Kolom '{group_column}' atau '{target_column}' tidak ditemukan!")
        return pd.Series()

def calculate_order_frequency(df, group_column, target_column):
    if target_column in df.columns and group_column in df.columns:
        # Kita hanya butuh kolom yang relevan
        # .count() akan menghitung semua baris yang tidak null
        result = df.groupby(group_column)[target_column].count().reset_index()
        
        # Rename kolom agar lebih informatif
        result.columns = [group_column, 'Jumlah Order']
        return result
    else:
        # Jika kamu pakai Streamlit (st.error), pastikan library sudah di-import
        print(f"Kolom '{group_column}' atau '{target_column}' tidak ditemukan!")
        return pd.DataFrame()

def calculate_monthly_item_sales(df, date_column, product_column, qty_column):
    if all(col in df.columns for col in [date_column, product_column, qty_column]):
        
        # 1. Pastikan tanggal dalam format datetime
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        
        # 2. Buat kolom Bulan
        df['Bulan'] = df[date_column].dt.to_period('M').astype(str)
        
        # 3. Pastikan Qty numerik
        df[qty_column] = df[qty_column].astype(str).str.replace(r'[Rp.\s,]', '', regex=True)
        df[qty_column] = pd.to_numeric(df[qty_column], errors='coerce').fillna(0)
        
        # 4. Group by Bulan & Produk
        grouped = df.groupby(['Bulan', product_column])[qty_column].sum().reset_index()
        
        # 5. Pivot supaya produk jadi kolom kanan
        pivot = grouped.pivot(index='Bulan', columns=product_column, values=qty_column).fillna(0)
        
        return pivot.reset_index()
    
    else:
        st.error("Kolom tidak ditemukan di DataFrame!")
        return pd.DataFrame()

total_luaspanen = calculate_total(df_master, 'tahun', 'Provinsi', 'Luas Panen (Ha)') 
#income
total_revenue = calculate_total(df_revenue, 'Revenue', date_column='Tanggal')
total_grossprofit = calculate_total(df_revenue, 'Gross Profit', date_column='Tanggal')

revenue_percustomer = (
    calculate_groupby(df_revenue, 'Nama Pelanggan', 'Revenue')
    .sort_values(by='Revenue', ascending=False)
    .head(5)
)

monthly_revenue = calculate_linechart(df_revenue, 'Tanggal', 'Revenue')

order_percustomer = calculate_order_frequency(df_revenue, 'Nama Pelanggan', 'Tanggal')

monthly_items = calculate_monthly_item_sales(
    df_revenue, 
    date_column='Tanggal', 
    product_column='Nama Produk', 
    qty_column='Qty'
)

revenue_peritem = calculate_monthly_item_sales(
    df_revenue, 
    date_column='Tanggal', 
    product_column='Nama Produk', 
    qty_column='Revenue'
)

monthly_grossprofit = calculate_monthly_item_sales(
    df_revenue, 
    date_column='Tanggal', 
    product_column='Nama Produk', 
    qty_column='Gross Profit'
)

#outcome
total_expense = calculate_total(df_expense, 'Jumlah', date_column='Tanggal')

#evaluate
operating_margin = (total_revenue - total_expense) / total_revenue

# Streamlit App
def main():
    st.title("Luas Panen")
    st.line_chart(total_luaspanen)
            
if __name__ == "__main__":
    main()

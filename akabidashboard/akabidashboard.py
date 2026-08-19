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
   
    # Cek hasil
    st.success("Data berhasil dimuat!")
    
except Exception as e:
    st.error(f"Gagal mengambil data: {e}")


def calculate_total(df, group_col1, group_col2, value_col):
    if group_col1 in df.columns and group_col2 in df.columns and value_col in df.columns:
        result = df.groupby([group_col1, group_col2])[value_col].sum().reset_index()
        return result
    else:
        print(f"Kolom tidak ditemukan!")
        return pd.DataFrame()

total_luaspanen = calculate_total(df_master, 'tahun', 'Provinsi', 'Luas Panen (Ha)') 

# Streamlit App
def main():
    st.title("Luas Panen")
    st.line_chart(total_luaspanen)
            
if __name__ == "__main__":
    main()

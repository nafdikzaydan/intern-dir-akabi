import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")
st.title("Dashboard Visualisasi Data Kedelai")

st_autorefresh(interval=60 * 1000)


@st.cache_data(ttl=60)
def get_data(nama_sheet):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    client = gspread.authorize(credentials)

    spreadsheet = client.open("REKAP DATA PER BULAN")
    sheet = spreadsheet.worksheet(nama_sheet)

    data = sheet.get_all_records()

    return pd.DataFrame(data)


# =========================
# LOAD DATA
# =========================

try:
    df_master = get_data("MASTER SHEET")

    st.success(
        f"Data berhasil dimuat! "
        f"{len(df_master)} baris."
    )

except Exception as e:
    st.error(f"Gagal mengambil data: {e}")
    st.stop()


# =========================
# HITUNG LUAS PANEN
# =========================

def calculate_total(df, group_col1, group_col2, value_col):

    required_columns = [
        group_col1,
        group_col2,
        value_col
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        st.error(
            f"Kolom tidak ditemukan: {missing_columns}"
        )
        return pd.DataFrame()

    # Pastikan luas panen berupa angka
    df = df.copy()

    df[value_col] = pd.to_numeric(
        df[value_col],
        errors="coerce"
    ).fillna(0)

    result = (
        df.groupby(
            [group_col1, group_col2]
        )[value_col]
        .sum()
        .reset_index()
    )

    return result


total_luaspanen = calculate_total(
    df_master,
    "Tahun",
    "Provinsi",
    "Luas Panen (Ha)"
)

total_provitas = calculate_total(df_master, "Tahun", "Provinsi", "Produktivitas (Ku/Ha)")

# =========================
# FORMAT CHART
# =========================

chart_luaspanen = total_luaspanen.pivot(
    index="Tahun",
    columns="Provinsi",
    values="Luas Panen (Ha)"
)

chart_provitas = total_provitas.pivot(
    index="Tahun",
    columns="Provinsi",
    values="Produktivitas (Ku/Ha)"
)


# =========================
# DASHBOARD
# =========================

def main():

    st.title("Luas Panen")

    st.line_chart(
        chart_luaspanen,
        x_label="Tahun",
        y_label="Luas Panen (Ha)"
    )

    st.bar_chart(
        chart_provitas,
        x_label="Tahun",
        y_label="Produktivitas (Ku/Ha"
    )


if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
from datetime import datetime, timedelta

# Konfigurasi Branding
st.set_page_config(page_title="ZProfit Analytics", page_icon="📈", layout="wide")

st.title("📈 ZProfit - Smart Business Analytics")
st.write("Sistem Laporan Presisi Berdasarkan Data Riil & Deteksi Bulan Otomatis")

# Fungsi untuk nama bulan Indonesia
def nama_bulan_indo(month_num):
    bulan = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 
        5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus", 
        9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }
    return bulan.get(month_num, "")

# --- LANGKAH 1: UPLOAD DATA ---
st.subheader("1. Integrasi Data Shopee")
file_order = st.file_uploader("Upload File Order Shopee (.xlsx)", type=['xlsx'])

if file_order:
    try:
        df = pd.read_excel(file_order)
        # Ambil sampel tanggal dari kolom 'Waktu Pesanan Dibuat'
        # Pastikan kolom tanggal terdeteksi
        df['Waktu Pesanan Dibuat'] = pd.to_datetime(df['Waktu Pesanan Dibuat'])
        tanggal_sampel = df['Waktu Pesanan Dibuat'].iloc[0]
        
        bulan_sekarang_nama = nama_bulan_indo(tanggal_sampel.month)
        # Hitung bulan depan
        bulan_depan_date = (tanggal_sampel.replace(day=1) + timedelta(days=32)).replace(day=1)
        bulan_depan_nama = nama_bulan_indo(bulan_depan_date.month)

        st.success(f"📅 Terdeteksi Laporan Bulan: {bulan_sekarang_nama}")

        df_clean = df[df['Status Pesanan'] != 'Dibatalkan'].copy()
        
        def get_id(row):
            if pd.notnull(row['SKU Induk']) and str(row['SKU Induk']).strip() != "":
                return str(row['SKU Induk'])
            return str(row['Nama Produk'])
            
        df_clean['Identitas'] = df_clean.apply(get_id, axis=1)
        produk_terjual = sorted(df_clean['Identitas'].unique())

        # --- LANGKAH 2: INPUT HPP ---
        st.divider()
        st.subheader("2. Penyesuaian Modal (HPP)")
        hpp_map = {}
        cols = st.columns(3)
        for i, produk in enumerate(produk_terjual):
            with cols[i % 3]:
                hpp_map[produk] = st.number_input(f"{produk}", key=f"hpp_{i}", min_value=0, step=1000)

        # --- LANGKAH 3: INPUT RIIL DARI PDF INCOME ---
        st.divider()
        st.subheader(f"3. Input Biaya Riil (Data {bulan_sekarang_nama})")
        
        c1, c2 = st.columns(2)
        with c1:
            total_admin_shopee = st.number_input("Total Biaya Admin & Layanan (Cek PDF Shopee)", value=0)
            pengembalian_dana = st.number_input("Total Pengembalian Dana / Retur", value=0)
        with c2:
            biaya_iklan = st.number_input("Total Biaya Iklan", value=0)
            operasional = st.number_input("Biaya Operasional", value=0)

        # --- PROSES PERHITUNGAN ---
        if st.button(f"🚀 GENERATE LAPORAN {bulan_sekarang_nama.upper()}"):
            def clean_num(x):
                if isinstance(x, str): return float(x.replace('Rp', '').replace('.', '').replace(',', '').strip())
                return float(x)

            df_clean['Total Pembayaran'] = df_clean['Total Pembayaran'].apply(clean_num)
            df_clean['HPP_Total'] = df_clean['Identitas'].map(hpp_map) * df_clean['Jumlah']
            
            selesai = df_clean[df_clean['Status Pesanan'] == 'Selesai']
            pending = df_clean[df_clean['Status Pesanan'].isin(['Perlu Dikirim', 'Dikirim'])]
            
            omzet_kotor = df_clean['Total Pembayaran'].sum()
            omzet_selesai = selesai['Total Pembayaran'].sum()
            omzet_pending = pending['Total Pembayaran'].sum()
            total_hpp = df_clean['HPP_Total'].sum()
            
            laba_bersih = omzet_kotor - total_hpp - total_admin_shopee - biaya_iklan - operasional - pengembalian_dana

            st.divider()
            k1, k2, k3 = st.columns(3)
            k1.metric(f"Dana Cair {bulan_sekarang_nama}", f"Rp {omzet_selesai:,.0f}")
            k2.metric(f"Estimasi Cair {bulan_depan_nama}", f"Rp {omzet_pending:,.0f}")
            k3.metric(f"Laba Bersih {bulan_sekarang_nama}", f"Rp {laba_bersih:,.0f}")

            # Cetak PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 15, f"ZPROFIT ANALYTICS - {bulan_sekarang_nama.upper()} {tanggal_sampel.year}", 0, 1, 'C')
            pdf.ln(5)
            
            summary_data = [
                (f"Dana Sudah Cair ({bulan_sekarang_nama})", omzet_selesai),
                (f"Estimasi Akan Cair ({bulan_depan_nama})", omzet_pending),
                ("Total Modal Produk (HPP)", total_hpp),
                ("Biaya Admin & Layanan (Shopee)", total_admin_shopee),
                ("Biaya Iklan", biaya_iklan),
                ("Biaya Operasional", operasional),
                ("Pengembalian Dana / Retur", pengembalian_dana),
                (f"TOTAL LABA BERSIH {bulan_sekarang_nama.upper()}", laba_bersih)
            ]
            
            for label, nilai in summary_data:
                pdf.set_font("Arial", 'B' if "LABA" in label else '', 11)
                pdf.cell(120, 10, label, 1)
                pdf.cell(60, 10, f"Rp {nilai:,.0f}", 1, 1, 'R')

            pdf_out = pdf.output(dest='S').encode('latin-1')
            b64 = base64.b64encode(pdf_out).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="ZProfit_{bulan_sekarang_nama}.pdf" style="text-decoration:none;"><div style="background-color:#28a745;color:white;padding:10px;border-radius:5px;text-align:center;"><b>📥 DOWNLOAD LAPORAN {bulan_sekarang_nama.upper()}</b></div></a>'
            st.markdown(href, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Gagal membaca tanggal/data: {e}")
else:
    st.info("Upload file Order Shopee untuk mendeteksi bulan...")

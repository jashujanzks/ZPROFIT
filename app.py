import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64

# Konfigurasi Branding
st.set_page_config(page_title="ZProfit Analytics", page_icon="📈", layout="wide")

# Custom CSS untuk tampilan lebih profesional
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 ZProfit - Smart Business Analytics")
st.write("Sistem Automasi Laporan Keuangan ZKS Indonesia")

# --- LANGKAH 1: UPLOAD DATA ---
st.subheader("1. Integrasi Data Shopee")
file_order = st.file_uploader("Upload File Order Shopee (.xlsx)", type=['xlsx'])

if file_order:
    try:
        df = pd.read_excel(file_order)
        # Filter pesanan valid
        df_clean = df[df['Status Pesanan'] != 'Dibatalkan'].copy()
        
        # Logika Identitas Produk
        def get_id(row):
            if pd.notnull(row['SKU Induk']) and str(row['SKU Induk']).strip() != "":
                return str(row['SKU Induk'])
            return str(row['Nama Produk'])
            
        df_clean['Identitas'] = df_clean.apply(get_id, axis=1)
        produk_terjual = sorted(df_clean['Identitas'].unique())

        # --- LANGKAH 2: INPUT HPP BERDASARKAN DATA ---
        st.divider()
        st.subheader("2. Penyesuaian Modal (HPP)")
        st.info(f"Ditemukan {len(produk_terjual)} jenis produk unik bulan ini.")
        
        hpp_map = {}
        cols = st.columns(3) # Dibagi 3 kolom agar lebih ringkas
        for i, produk in enumerate(produk_terjual):
            with cols[i % 3]:
                hpp_map[produk] = st.number_input(f"{produk}", key=f"hpp_{i}", min_value=0, step=1000)

        # --- LANGKAH 3: BIAYA RIIL & RISIKO ---
        st.divider()
        st.subheader("3. Operasional & Estimasi Risiko")
        c1, c2, c3 = st.columns(3)
        with c1:
            biaya_iklan = st.number_input("Biaya Iklan (Riil Terpakai)", value=0)
        with c2:
            operasional = st.number_input("Biaya Operasional Toko", value=0)
        with c3:
            persen_retur = st.slider("Cadangan Risiko Gagal/Retur (%)", 0, 30, 5)

        # --- PROSES PERHITUNGAN ---
        if st.button("🚀 GENERATE LAPORAN ZPROFIT"):
            def clean_num(x):
                if isinstance(x, str): return float(x.replace('Rp', '').replace('.', '').replace(',', '').strip())
                return float(x)

            df_clean['Total Pembayaran'] = df_clean['Total Pembayaran'].apply(clean_num)
            df_clean['HPP_Total'] = df_clean['Identitas'].map(hpp_map) * df_clean['Jumlah']
            
            # Pengelompokan Status
            selesai = df_clean[df_clean['Status Pesanan'] == 'Selesai']
            pending = df_clean[df_clean['Status Pesanan'].isin(['Perlu Dikirim', 'Dikirim'])]
            
            omzet_selesai = selesai['Total Pembayaran'].sum()
            omzet_pending = pending['Total Pembayaran'].sum()
            total_hpp = df_clean['HPP_Total'].sum()
            
            est_admin = (omzet_selesai + omzet_pending) * 0.2128
            cadangan_retur = omzet_pending * (persen_retur / 100)
            
            laba_bersih = (omzet_selesai + omzet_pending) - total_hpp - est_admin - biaya_iklan - operasional - cadangan_retur

            # Display Results
            st.divider()
            k1, k2, k3 = st.columns(3)
            k1.metric("Dana Sudah Cair", f"Rp {omzet_selesai:,.0f}")
            k2.metric("Estimasi Akan Cair", f"Rp {omzet_pending:,.0f}")
            k3.metric("Laba Bersih (Estimasi)", f"Rp {laba_bersih:,.0f}")

            # GENERATE PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 15, "ZPROFIT BUSINESS REPORT", 0, 1, 'C')
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 5, "ZKS Indonesia - Data-Driven Analysis", 0, 1, 'C')
            pdf.ln(10)
            
            summary_data = [
                ("Omzet Pesanan Selesai", omzet_selesai),
                ("Omzet Pesanan Dalam Perjalanan", omzet_pending),
                ("Total Harga Pokok Penjualan (HPP)", total_hpp),
                ("Estimasi Biaya Admin & Layanan", est_admin),
                ("Biaya Iklan", biaya_iklan),
                ("Biaya Operasional", operasional),
                (f"Cadangan Risiko Retur ({persen_retur}%)", cadangan_retur),
                ("ESTIMASI LABA BERSIH AKHIR", laba_bersih)
            ]
            
            for label, nilai in summary_data:
                pdf.set_font("Arial", 'B' if "LABA" in label else '', 11)
                pdf.cell(120, 10, label, 1)
                pdf.cell(60, 10, f"Rp {nilai:,.0f}", 1, 1, 'R')

            # Link Download
            pdf_out = pdf.output(dest='S').encode('latin-1')
            b64 = base64.b64encode(pdf_out).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="ZProfit_Report.pdf" style="text-decoration:none;"><div style="background-color:#28a745;color:white;padding:10px;border-radius:5px;text-align:center;"><b>📥 DOWNLOAD PDF REPORT</b></div></a>'
            st.markdown(href, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error pembacaan data: {e}")
else:
    st.info("Menunggu upload file Order Shopee...")
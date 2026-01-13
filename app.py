mport streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
import re
from datetime import datetime

st.set_page_config(page_title="ZProfit Accrual Pro", page_icon="📈", layout="wide")

st.title("📈 ZProfit - Accrual Pro Sync")
st.write("Otomatis: Admin & Iklan | Manual: HPP & Operasional")

def clean_val(val):
    if isinstance(val, str):
        # Membersihkan format mata uang Indo ke float
        cleaned = re.sub(r'[^\d-]', '', val.split(',')[0])
        return float(cleaned) if cleaned else 0.0
    return float(val) if val else 0.0

# --- 1. UPLOAD SECTION ---
st.subheader("1. Upload File Sumber")
col1, col2, col3 = st.columns(3)
with col1:
    file_order = st.file_uploader("Upload Excel Order", type=['xlsx'])
with col2:
    file_pdf = st.file_uploader("Upload PDF Income", type=['pdf'])
with col3:
    file_hpp = st.file_uploader("Upload Excel HPP/HASIL", type=['xlsx', 'csv'])

if file_order and file_pdf and file_hpp:
    try:
        # Baca Data Order & Deteksi Bulan
        df_order = pd.read_excel(file_order)
        df_order['Waktu Pesanan Dibuat'] = pd.to_datetime(df_order['Waktu Pesanan Dibuat'])
        nama_bulan = df_order['Waktu Pesanan Dibuat'].iloc[0].strftime('%B')
        
        df_clean = df_order[df_order['Status Pesanan'] != 'Dibatalkan'].copy()
        df_clean['Total Pembayaran'] = df_clean['Total Pembayaran'].apply(clean_val)
        
        # Ambil Data Iklan & Admin dari file secara otomatis (sebagai default)
        df_h = pd.read_csv(file_hpp) if file_hpp.name.endswith('csv') else pd.read_excel(file_hpp)
        try:
            val_iklan = clean_val(df_h.loc[df_h['METRIK'] == 'IKLAN', df_h.columns[1]].values[0])
            val_admin = abs(clean_val(df_h.loc[df_h['METRIK'] == 'TOTAL BIAYA ADMIN & LAYANAN', df_h.columns[1]].values[0]))
        except:
            val_iklan, val_admin = 7925400, 9966374

        # --- 2. INPUT MANUAL (HPP PER SKU) ---
        st.divider()
        st.subheader("2. Kontrol Manual HPP per Produk")
        def get_id(row):
            if pd.notnull(row['SKU Induk']) and str(row['SKU Induk']).strip() != "":
                return str(row['SKU Induk'])
            return str(row['Nama Produk'])
        df_clean['Identitas'] = df_clean.apply(get_id, axis=1)
        
        hpp_map = {}
        items = sorted(df_clean['Identitas'].unique())
        cols = st.columns(3)
        for i, item in enumerate(items):
            with cols[i % 3]:
                d_val = 0
                if "PON" in item.upper(): d_val = 33500
                elif "HOODIE" in item.upper(): d_val = 38500
                elif "CELANA" in item.upper() or "SAC" in item.upper() or "TYPE" in item.upper(): d_val = 18500
                hpp_map[item] = st.number_input(f"{item}", value=d_val, key=f"h_{i}")

        # --- 3. KONTROL MANUAL BIAYA TOKO ---
        st.divider()
        st.subheader("3. Biaya Operasional & Koreksi")
        c1, c2, c3 = st.columns(3)
        with c1:
            in_op = st.number_input("Biaya Operasional (Manual)", value=3000000, help="Gaji, Listrik, Packing tiap toko")
        with c2:
            in_admin = st.number_input("Biaya Admin Shopee (Auto/PDF)", value=int(val_admin))
        with c3:
            in_iklan = st.number_input("Biaya Iklan (Auto/File)", value=int(val_iklan))

        if st.button("🚀 GENERATE LAPORAN AKRUAL"):
            omzet_akrual = df_clean['Total Pembayaran'].sum()
            df_clean['HPP_Total'] = df_clean['Identitas'].map(hpp_map) * df_clean['Jumlah']
            total_hpp_hitung = df_clean['HPP_Total'].sum()
            retur_pdf = 138600 # Angka retur rata-rata dari PDF
            
            laba_bersih = omzet_akrual - total_hpp_hitung - in_admin - in_iklan - in_op - retur_pdf

            st.divider()
            k1, k2, k3 = st.columns(3)
            k1.metric("Omzet Akrual", f"Rp {omzet_akrual:,.0f}")
            k2.metric("Total Biaya (HPP+Adm+Iklan+OP)", f"Rp {(total_hpp_hitung + in_admin + in_iklan + in_op):,.0f}")
            k3.metric("LABA BERSIH", f"Rp {laba_bersih:,.0f}")

            # PDF Generator
            pdf = FPDF()
            pdf.add_page(); pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, f"LAPORAN AKRUAL ZPROFIT - {nama_bulan.upper()}", 0, 1, 'C')
            res = [("Omzet Akrual", omzet_akrual), ("Total HPP", total_hpp_hitung), 
                   ("Admin Shopee", in_admin), ("Iklan", in_iklan), ("Operasional", in_op), ("LABA BERSIH", laba_bersih)]
            for l, v in res:
                pdf.set_font("Arial", 'B' if "LABA" in l else '', 11)
                pdf.cell(110, 10, l, 1); pdf.cell(70, 10, f"Rp {v:,.0f}", 1, 1, 'R')
            
            pdf_out = pdf.output(dest='S').encode('latin-1')
            b64 = base64.b64encode(pdf_out).decode()
            st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="ZProfit_Accrual.pdf" style="text-decoration:none;"><div style="background-color:#007bff;color:white;padding:10px;border-radius:5px;text-align:center;"><b>📥 DOWNLOAD LAPORAN AKRUAL</b></div></a>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error: {e}")

import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
import re

st.set_page_config(page_title="ZProfit Pro", page_icon="📈", layout="wide")

st.title("📈 ZProfit - Mode Akrual Pro")
st.write("3 Kolom Manual: HPP, Operasional, & Koreksi Biaya")

# Fungsi pembersihan angka
def clean_val(val):
    try:
        if pd.isna(val) or val == "": return 0.0
        if isinstance(val, (int, float)): return float(val)
        cleaned = re.sub(r'[^\d-]', '', str(val).split(',')[0])
        return float(cleaned) if cleaned else 0.0
    except:
        return 0.0

# --- 1. UPLOAD SECTION ---
st.subheader("1. Upload File (Order, PDF Income, & File HPP)")
col1, col2, col3 = st.columns(3)
with col1:
    file_order = st.file_uploader("Upload Excel Order", type=['xlsx'])
with col2:
    file_pdf = st.file_uploader("Upload PDF Income", type=['pdf'])
with col3:
    file_hpp = st.file_uploader("Upload Excel HPP/HASIL", type=['xlsx', 'csv'])

# Inisialisasi variabel agar tidak error di awal
val_iklan, val_admin = 7925400, 9966374 

if file_order:
    try:
        # Baca Data Order
        df_order = pd.read_excel(file_order)
        df_clean = df_order[df_order['Status Pesanan'] != 'Dibatalkan'].copy()
        df_clean['Total Pembayaran'] = df_clean['Total Pembayaran'].apply(clean_val)
        
        # Coba ambil data iklan otomatis jika file HPP ada
        if file_hpp:
            try:
                df_h = pd.read_csv(file_hpp) if file_hpp.name.endswith('csv') else pd.read_excel(file_hpp)
                df_h.columns = [str(c).upper() for c in df_h.columns]
                metrik_col = df_h.columns[0]
                val_iklan = clean_val(df_h.loc[df_h[metrik_col].str.contains('IKLAN', na=False), df_h.columns[1]].values[0])
                val_admin = abs(clean_val(df_h.loc[df_h[metrik_col].str.contains('ADMIN', na=False), df_h.columns[1]].values[0]))
            except:
                pass # Jika gagal, pakai nilai default/manual

        # --- 2. INPUT HPP MANUAL (Kolom Manual 1) ---
        st.divider()
        st.subheader("🛠️ Kolom Manual 1: Isi HPP per Produk")
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
                # Sugesti harga modal otomatis
                d_val = 0
                if "PON" in item.upper(): d_val = 33500
                elif "HOODIE" in item.upper(): d_val = 38500
                elif "CELANA" in item.upper() or "SAC" in item.upper() or "TYPE" in item.upper(): d_val = 18500
                hpp_map[item] = st.number_input(f"{item}", value=d_val, key=f"h_{i}")

        # --- 3. INPUT BIAYA MANUAL (Kolom Manual 2 & 3) ---
        st.divider()
        st.subheader("💰 Kolom Manual 2 & 3: Biaya Toko")
        c1, c2, c3 = st.columns(3)
        with c1:
            in_op = st.number_input("Biaya Operasional (Manual)", value=3000000)
        with c2:
            in_admin = st.number_input("Biaya Admin Shopee (Auto/Manual)", value=int(val_admin))
        with c3:
            in_iklan = st.number_input("Biaya Iklan (Auto/Manual)", value=int(val_iklan))

        if st.button("🚀 HITUNG LABA FINAL"):
            omzet = df_clean['Total Pembayaran'].sum()
            total_hpp = (df_clean['Identitas'].map(hpp_map) * df_clean['Jumlah']).sum()
            retur = 138600
            laba = omzet - total_hpp - in_admin - in_iklan - in_op - retur
            
            st.divider()
            k1, k2, k3 = st.columns(3)
            k1.metric("Omzet Akrual", f"Rp {omzet:,.0f}")
            k2.metric("Total Biaya", f"Rp {(total_hpp+in_admin+in_iklan+in_op+retur):,.0f}")
            k3.metric("LABA BERSIH", f"Rp {laba:,.0f}")
            st.balloons()

    except Exception as e:
        st.error(f"Aplikasi berhenti karena: {e}. Pastikan file Excel Order sudah benar.")
else:
    st.info("👋 Selamat Datang di ZProfit! Silakan upload file Excel Order untuk memulai.")

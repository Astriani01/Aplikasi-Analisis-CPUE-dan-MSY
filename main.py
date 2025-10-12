import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from scipy import stats

st.set_page_config(page_title="Analisis CPUE & MSY - Model Schaefer", layout="wide")

st.title("🐟 Analisis CPUE dan MSY dengan Standarisasi Alat Tangkap (Model Schaefer)")

# ------------------------------------------------------
# Fungsi bantu
# ------------------------------------------------------
def deteksi_kolom(df):
    """Deteksi otomatis nama kolom"""
    kolom_map = {
        "tahun": ["tahun", "year", "thn"],
        "alat_tangkap": ["alat_tangkap", "alat", "gear", "gear_type"],
        "tangkapan": ["tangkapan", "hasil", "catch", "produksi"],
        "upaya": ["upaya", "effort", "trip", "usaha"]
    }
    rename_dict = {}
    for standar, variasi in kolom_map.items():
        for var in variasi:
            cocok = [c for c in df.columns if var.lower() in c.lower()]
            if cocok:
                rename_dict[cocok[0]] = standar
                break
    return df.rename(columns=rename_dict)

def baca_csv_otomatis(file):
    """Baca file CSV dengan deteksi pemisah otomatis"""
    content = file.read().decode('utf-8')
    file.seek(0)
    if ';' in content and ',' not in content.split('\n')[0]:
        df = pd.read_csv(io.StringIO(content), delimiter=';')
    else:
        df = pd.read_csv(io.StringIO(content))
    return df

# ------------------------------------------------------
# FUNGSI ANALISIS UTAMA
# ------------------------------------------------------

def hitung_cpue_per_alat(df):
    """Langkah 2: Hitung CPUE masing-masing alat tangkap"""
    cpue_per_alat = df.groupby('alat_tangkap').agg({
        'tangkapan': 'sum',
        'upaya': 'sum'
    }).reset_index()
    cpue_per_alat['CPUE'] = cpue_per_alat['tangkapan'] / cpue_per_alat['upaya']
    return cpue_per_alat

def hitung_fpi_dan_standarisasi(df, alat_standar_pilihan=None):
    """Hitung FPI dan lakukan standarisasi"""
    # Hitung CPUE per alat
    cpue_per_alat = hitung_cpue_per_alat(df)
    
    # Tentukan alat standar
    if alat_standar_pilihan:
        alat_standar = alat_standar_pilihan
        cpue_standar = cpue_per_alat.loc[cpue_per_alat['alat_tangkap'] == alat_standar, 'CPUE'].values[0]
    else:
        alat_standar_row = cpue_per_alat.loc[cpue_per_alat['CPUE'].idxmax()]
        alat_standar = alat_standar_row['alat_tangkap']
        cpue_standar = alat_standar_row['CPUE']
    
    # Hitung FPI
    cpue_per_alat['FPI'] = cpue_standar / cpue_per_alat['CPUE']
    fpi_dict = dict(zip(cpue_per_alat['alat_tangkap'], cpue_per_alat['FPI']))
    
    # Standarisasi upaya
    df_standar = df.copy()
    df_standar['upaya_standar'] = df_standar.apply(
        lambda row: row['upaya'] * fpi_dict.get(row['alat_tangkap'], 1), 
        axis=1
    )
    
    return df_standar, cpue_per_alat, alat_standar, cpue_standar

def analisis_model_schaefer(cpue_tahunan):
    """Analisis MSY menggunakan Model Schaefer"""
    x = cpue_tahunan['upaya_standar'].values
    y = cpue_tahunan['CPUE'].values
    
    if len(x) > 1:
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        a = intercept
        b = slope
        
        # Rumus MSY Model Schaefer
        E_MSY = -a / (2 * b) if b != 0 else 0
        MSY = -(a ** 2) / (4 * b) if b != 0 else 0
        
        return {
            'parameter': {'a': a, 'b': b, 'r_squared': r_value**2, 'p_value': p_value},
            'msy': MSY,
            'e_msy': E_MSY,
            'success': True
        }
    return {'success': False}

def hitung_tingkat_pemanfaatan(cpue_tahunan, msy, e_msy):
    """Hitung tingkat pemanfaatan untuk setiap tahun"""
    cpue_tahunan['TPc (%)'] = (cpue_tahunan['tangkapan'] / msy) * 100
    cpue_tahunan['TPe (%)'] = (cpue_tahunan['upaya_standar'] / e_msy) * 100
    return cpue_tahunan

def tentukan_status_pemanfaatan(tp_value):
    """Tentukan status pemanfaatan"""
    if tp_value < 50:
        return "Under Exploited", "🟢", "success"
    elif 50 <= tp_value <= 100:
        return "Fully Exploited", "🟡", "warning"
    else:
        return "Over Exploited", "🔴", "error"

# ------------------------------------------------------
# INPUT DATA
# ------------------------------------------------------
st.sidebar.header("📂 Input Data")

opsi_input = st.sidebar.radio("Pilih cara input data:", ["Upload File", "Input Manual"])

if opsi_input == "Upload File":
    uploaded_file = st.sidebar.file_uploader("Unggah file CSV atau Excel", type=["csv", "xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = baca_csv_otomatis(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            df = deteksi_kolom(df)
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")
            df = None
    else:
        df = None
else:
    st.sidebar.subheader("Input Data Manual")
    st.sidebar.info("Format: Tahun, Alat Tangkap, Tangkapan (kg), Upaya (trip)")
    
    data_input = st.sidebar.text_area("Input data (format CSV):", """Tahun,Alat Tangkap,Tangkapan,Upaya
2018,Purse Seine,8000,200
2018,Gill Net,4500,300
2019,Purse Seine,8500,210
2019,Gill Net,4800,320
2020,Purse Seine,9000,220
2020,Gill Net,5000,340
2021,Purse Seine,9200,230
2021,Gill Net,5200,350
2022,Purse Seine,9500,240
2022,Gill Net,5500,360""")
    
    if data_input:
        try:
            df = pd.read_csv(io.StringIO(data_input))
            df = deteksi_kolom(df)
        except Exception as e:
            st.error(f"Error membaca data: {e}")
            df = None

# ------------------------------------------------------
# ANALISIS UTAMA
# ------------------------------------------------------
if df is not None:
    df = deteksi_kolom(df)
    df["tahun"] = df["tahun"].astype(str)

    st.header("📋 Data Awal")
    st.dataframe(df)

    if not {"tangkapan", "upaya"}.issubset(df.columns):
        st.error("⚠️ Kolom wajib 'tangkapan' dan 'upaya' tidak ditemukan.")
    else:
        # ==============================================
        # STANDARISASI ALAT TANGKAP
        # ==============================================
        if "alat_tangkap" in df.columns:
            st.header("🔄 Standarisasi Alat Tangkap")
            
            # Hitung CPUE per alat
            st.subheader("1. Hitung CPUE per Alat Tangkap")
            cpue_per_alat = hitung_cpue_per_alat(df)
            st.dataframe(cpue_per_alat.style.format({
                'tangkapan': '{:.0f}', 'upaya': '{:.0f}', 'CPUE': '{:.3f}'
            }))
            
            # Pilih alat standar
            st.subheader("2. Pilih Alat Tangkap Standar")
            alat_tertinggi = cpue_per_alat.loc[cpue_per_alat['CPUE'].idxmax(), 'alat_tangkap']
            alat_standar_pilihan = st.selectbox(
                "Pilih alat tangkap standar (CPUE tertinggi disarankan):",
                cpue_per_alat['alat_tangkap'].tolist(),
                index=cpue_per_alat['alat_tangkap'].tolist().index(alat_tertinggi)
            )
            
            # Hitung FPI dan standarisasi
            df_standar, cpue_per_alat, alat_standar, cpue_standar = hitung_fpi_dan_standarisasi(df, alat_standar_pilihan)
            
            st.success(f"**Alat Tangkap Standar:** {alat_standar} dengan CPUE = {cpue_standar:.3f} kg/trip")
            
            # Tampilkan FPI
            st.subheader("3. Fishing Power Index (FPI)")
            st.latex(r"FPI = \frac{CPUE_{standar}}{CPUE_i}")
            st.dataframe(cpue_per_alat.style.format({
                'CPUE': '{:.3f}', 'FPI': '{:.3f}'
            }))
            
            # Tampilkan data terstandarisasi
            st.subheader("4. Data dengan Upaya Terstandarisasi")
            st.dataframe(df_standar.style.format({
                'tangkapan': '{:.0f}', 'upaya': '{:.0f}', 'CPUE': '{:.3f}', 'upaya_standar': '{:.3f}'
            }))
            
        else:
            st.warning("ℹ️ Kolom 'alat_tangkap' tidak ditemukan. Analisis dilanjutkan tanpa standarisasi.")
            df_standar = df.copy()
            df_standar['upaya_standar'] = df_standar['upaya']
            df_standar['CPUE'] = df_standar['tangkapan'] / df_standar['upaya']
        
        # ==============================================
        # ANALISIS CPUE TAHUNAN
        # ==============================================
        st.header("📊 CPUE Tahunan (Setelah Standarisasi)")
        cpue_tahunan = df_standar.groupby('tahun').agg({
            'tangkapan': 'sum',
            'upaya_standar': 'sum'
        }).reset_index()
        cpue_tahunan['CPUE'] = cpue_tahunan['tangkapan'] / cpue_tahunan['upaya_standar']
        
        st.dataframe(cpue_tahunan.style.format({
            'tangkapan': '{:.0f}', 'upaya_standar': '{:.3f}', 'CPUE': '{:.3f}'
        }))
        
        # ==============================================
        # ANALISIS MSY - MODEL SCHAEFER
        # ==============================================
        if len(cpue_tahunan) > 1:
            st.header("🧮 Analisis MSY - Model Schaefer")
            
            # Analisis regresi
            hasil_schaefer = analisis_model_schaefer(cpue_tahunan)
            
            if hasil_schaefer['success']:
                param = hasil_schaefer['parameter']
                MSY = hasil_schaefer['msy']
                E_MSY = hasil_schaefer['e_msy']
                
                # Tampilkan parameter
                st.subheader("Hasil Regresi Linear")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Intercept (a)", f"{param['a']:.4f}")
                col2.metric("Slope (b)", f"{param['b']:.6f}")
                col3.metric("R²", f"{param['r_squared']:.4f}")
                col4.metric("p-value", f"{param['p_value']:.4f}")
                
                # Tampilkan MSY
                st.subheader("Estimasi Maximum Sustainable Yield (MSY)")
                st.latex(r"C_{MSY} = -\frac{a^2}{4b}")
                st.latex(r"F_{MSY} = -\frac{a}{2b}")
                
                col1, col2 = st.columns(2)
                col1.metric("MSY", f"{MSY:.2f} kg")
                col2.metric("Upaya Optimal (F_MSY)", f"{E_MSY:.2f} unit")
                
                # ==============================================
                # TINGKAT PEMANFAATAN
                # ==============================================
                st.header("📈 Tingkat Pemanfaatan")
                cpue_tahunan = hitung_tingkat_pemanfaatan(cpue_tahunan, MSY, E_MSY)
                
                # Tampilkan data tingkat pemanfaatan
                st.dataframe(cpue_tahunan.style.format({
                    'tangkapan': '{:.0f}', 'upaya_standar': '{:.3f}', 'CPUE': '{:.3f}',
                    'TPc (%)': '{:.1f}', 'TPe (%)': '{:.1f}'
                }))
                
                # Status tahun terakhir
                tahun_terakhir = cpue_tahunan.iloc[-1]
                tp_c = tahun_terakhir['TPc (%)']
                tp_e = tahun_terakhir['TPe (%)']
                
                col1, col2 = st.columns(2)
                with col1:
                    status_c, icon_c, warna_c = tentukan_status_pemanfaatan(tp_c)
                    st.metric(
                        f"Tingkat Pemanfaatan Produksi {icon_c}",
                        f"{tp_c:.1f}%",
                        status_c
                    )
                
                with col2:
                    status_e, icon_e, warna_e = tentukan_status_pemanfaatan(tp_e)
                    st.metric(
                        f"Tingkat Pemanfaatan Upaya {icon_e}",
                        f"{tp_e:.1f}%",
                        status_e
                    )
                
                # ==============================================
                # VISUALISASI
                # ==============================================
                st.header("📊 Visualisasi Hasil Analisis")
                
                # Buat 3 grafik
                fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))
                
                # Grafik 1: Regresi CPUE vs Upaya
                E_range = np.linspace(0, cpue_tahunan['upaya_standar'].max() * 1.5, 100)
                cpue_pred = param['a'] + param['b'] * E_range
                
                ax1.scatter(cpue_tahunan['upaya_standar'], cpue_tahunan['CPUE'], 
                           color='blue', s=80, label='Data')
                ax1.plot(E_range, cpue_pred, 'red', linewidth=2, 
                        label=f'CPUE = {param["a"]:.3f} + {param["b"]:.5f}E')
                ax1.axvline(E_MSY, color='green', linestyle='--', label=f'F_MSY = {E_MSY:.2f}')
                ax1.set_xlabel("Upaya Standar")
                ax1.set_ylabel("CPUE")
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                
                # Grafik 2: Kurva Produksi (Parabola)
                C_pred = param['a'] * E_range + param['b'] * (E_range ** 2)
                
                ax2.plot(E_range, C_pred, 'purple', linewidth=2, label='Kurva Produksi')
                ax2.axvline(E_MSY, color='green', linestyle='--', label=f'F_MSY')
                ax2.axhline(MSY, color='orange', linestyle='--', label=f'MSY = {MSY:.1f} kg')
                ax2.scatter(cpue_tahunan['upaya_standar'], cpue_tahunan['tangkapan'],
                           color='blue', s=80, label='Data Aktual')
                ax2.set_xlabel("Upaya Standar")
                ax2.set_ylabel("Hasil Tangkapan (kg)")
                ax2.legend()
                ax2.grid(True, alpha=0.3)
                
                # Grafik 3: Parabola dengan Zona
                ax3.plot(E_range, C_pred, 'b-', linewidth=3, 
                        label=f'C = {param["a"]:.3f}E + {param["b"]:.6f}E²')
                ax3.plot(E_MSY, MSY, 'ro', markersize=10, label=f'MSY ({MSY:.1f} kg)')
                ax3.axvline(E_MSY, color='red', linestyle='--', alpha=0.7, label=f'E_MSY ({E_MSY:.1f})')
                ax3.axhline(MSY, color='green', linestyle='--', alpha=0.7)
                
                # Zona warna
                ax3.axvspan(0, E_MSY, alpha=0.2, color='green', label='Underfishing')
                ax3.axvspan(E_MSY, E_range.max(), alpha=0.2, color='red', label='Overfishing')
                
                ax3.scatter(cpue_tahunan['upaya_standar'], cpue_tahunan['tangkapan'],
                           color='orange', s=80, label='Data Aktual')
                ax3.set_xlabel('Upaya Standar')
                ax3.set_ylabel('Hasil Tangkapan (kg)')
                ax3.set_title('Kurva Produksi dengan Zona Pemanfaatan')
                ax3.legend()
                ax3.grid(True, alpha=0.3)
                
                st.pyplot(fig)
                
                # ==============================================
                # SIMULASI INTERAKTIF
                # ==============================================
                st.header("🎛 Simulasi Interaktif")
                
                upaya_simulasi = st.slider(
                    "Pilih tingkat upaya penangkapan:",
                    0.0, float(cpue_tahunan['upaya_standar'].max() * 1.5), 
                    float(E_MSY)
                )
                
                tangkapan_pred = param['a'] * upaya_simulasi + param['b'] * (upaya_simulasi ** 2)
                cpue_pred = param['a'] + param['b'] * upaya_simulasi
                tp_simulasi = (upaya_simulasi / E_MSY) * 100
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Prediksi Tangkapan", f"{tangkapan_pred:.2f} kg")
                col2.metric("Prediksi CPUE", f"{cpue_pred:.3f} kg/unit")
                col3.metric("Tingkat Pemanfaatan", f"{tp_simulasi:.1f}%")
                
                # Rekomendasi
                if tp_simulasi > 100:
                    st.error("**OVER EXPLOITED** - Kurangi upaya penangkapan")
                elif tp_simulasi < 50:
                    st.success("**UNDER EXPLOITED** - Upaya dapat ditingkatkan")
                else:
                    st.info("**FULLY EXPLOITED** - Upaya optimal")
                
                # ==============================================
                # EKSPOR HASIL
                # ==============================================
                st.header("💾 Ekspor Hasil Analisis")
                
                # Siapkan data untuk ekspor
                export_data = cpue_tahunan[['tahun', 'tangkapan', 'upaya_standar', 'CPUE', 'TPc (%)', 'TPe (%)']]
                csv = export_data.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="⬇ Unduh Hasil Analisis (CSV)",
                    data=csv,
                    file_name="hasil_analisis_cpue_msy.csv",
                    mime="text/csv"
                )
                
            else:
                st.error("Gagal melakukan analisis regresi. Periksa data Anda.")
        else:
            st.error("⚠️ Tidak cukup data untuk analisis MSY. Minimal diperlukan 2 tahun data.")

else:
    st.info("Silakan unggah file CSV atau input data manual terlebih dahulu.")

st.markdown("---")
st.markdown("""
**Metodologi:** Analisis menggunakan **Model Schaefer (1954)** dengan standarisasi alat tangkap melalui **Fishing Power Index (FPI)**.

**Rumus Utama:**
- $CPUE = \\frac{Catch}{Effort}$
- $FPI = \\frac{CPUE_{standar}}{CPUE_i}$
- $C_{MSY} = -\\frac{a^2}{4b}$
- $F_{MSY} = -\\frac{a}{2b}$
- $C = aE + bE^2$
""")

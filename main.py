import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

st.set_page_config(page_title="Analisis CPUE & MSY - Model Schaefer", layout="wide")
st.title("🐟 Analisis CPUE dan MSY dengan Standarisasi Alat Tangkap")

# ==============================================
# KONFIGURASI ALAT TANGKAP DAN TAHUN YANG FLEKSIBEL
# ==============================================

# Inisialisasi session state untuk konfigurasi
if 'gear_config' not in st.session_state:
    st.session_state.gear_config = {
        'gears': ['Jaring_Insang_Tetap', 'Jaring_Hela_Dasar', 'Bagan_Berperahu', 'Pancing'],
        'display_names': ['Jaring Insang Tetap', 'Jaring Hela Dasar', 'Bagan Berperahu', 'Pancing'],
        'standard_gear': 'Jaring_Hela_Dasar',
        'years': [2020, 2021, 2022, 2023, 2024],
        'num_years': 5
    }

if 'data_tables' not in st.session_state:
    st.session_state.data_tables = {
        'production': [],
        'effort': []
    }

# Fungsi untuk mendapatkan konfigurasi
def get_config():
    """Mengembalikan konfigurasi alat tangkap dan tahun"""
    return st.session_state.gear_config

# Fungsi untuk menyimpan konfigurasi
def save_config(gears, display_names, standard_gear, years, num_years):
    """Menyimpan konfigurasi ke session state"""
    st.session_state.gear_config = {
        'gears': gears,
        'display_names': display_names,
        'standard_gear': standard_gear,
        'years': years,
        'num_years': num_years
    }
    st.success("Konfigurasi berhasil disimpan!")

# Fungsi untuk generate tahun
def generate_years(start_year, num_years):
    """Generate list tahun berdasarkan tahun mulai dan jumlah tahun"""
    return [start_year + i for i in range(num_years)]

# Fungsi untuk reset data
def reset_data():
    """Reset data produksi dan upaya"""
    st.session_state.data_tables = {
        'production': [],
        'effort': []
    }
    st.success("Data berhasil direset!")

# Fungsi untuk update data berdasarkan konfigurasi baru
def update_data_structure():
    """Update struktur data ketika konfigurasi berubah"""
    config = get_config()
    current_production = st.session_state.data_tables.get('production', [])
    current_effort = st.session_state.data_tables.get('effort', [])
    
    new_production = []
    new_effort = []
    
    for i, year in enumerate(config['years']):
        prod_row = {'Tahun': year}
        eff_row = {'Tahun': year}
        
        # Jika ada data existing, gunakan data tersebut
        if i < len(current_production):
            existing_prod = current_production[i]
            existing_eff = current_effort[i]
        else:
            existing_prod = {}
            existing_eff = {}
        
        # Isi data untuk setiap alat tangkap
        for gear in config['gears']:
            prod_row[gear] = existing_prod.get(gear, 1000 * (i+1) * (config['gears'].index(gear)+1))
            eff_row[gear] = existing_eff.get(gear, 100 * (i+1) * (config['gears'].index(gear)+1))
        
        # Hitung total
        prod_row['Jumlah'] = sum([prod_row[gear] for gear in config['gears']])
        eff_row['Jumlah'] = sum([eff_row[gear] for gear in config['gears']])
        
        new_production.append(prod_row)
        new_effort.append(eff_row)
    
    st.session_state.data_tables = {
        'production': new_production,
        'effort': new_effort
    }

# ==============================================
# FUNGSI UTAMA YANG DIPERBAIKI
# ==============================================

def hitung_cpue(produksi_df, upaya_df, gears):
    """Hitung CPUE untuk setiap alat tangkap"""
    cpue_data = []
    years = produksi_df['Tahun'].values
    
    for year in years:
        year_data = {'Tahun': year}
        
        # CPUE untuk setiap alat tangkap
        for gear in gears:
            prod = produksi_df[produksi_df['Tahun'] == year][gear].values[0]
            eff = upaya_df[upaya_df['Tahun'] == year][gear].values[0]
            
            if eff > 0:
                cpue = prod / eff
            else:
                cpue = 0
                
            year_data[gear] = cpue
        
        # CPUE total
        total_cpue = sum([year_data[gear] for gear in gears])
        year_data['Jumlah'] = total_cpue
        
        cpue_data.append(year_data)
    
    return pd.DataFrame(cpue_data)

def hitung_fpi_per_tahun(cpue_df, gears, standard_gear):
    """Hitung FPI per tahun"""
    fpi_data = []
    years = cpue_df['Tahun'].values
    
    for year in years:
        year_data = {'Tahun': year}
        
        # Ambil CPUE standar
        cpue_standard = cpue_df[cpue_df['Tahun'] == year][standard_gear].values[0]
        
        # Hitung FPI: CPUE alat / CPUE standar
        for gear in gears:
            cpue_gear = cpue_df[cpue_df['Tahun'] == year][gear].values[0]
            
            if cpue_standard > 0:
                fpi = cpue_gear / cpue_standard
            else:
                fpi = 0
            
            year_data[gear] = fpi
        
        # Total FPI
        total_fpi = sum([year_data[gear] for gear in gears])
        year_data['Jumlah'] = total_fpi
        
        fpi_data.append(year_data)
    
    return pd.DataFrame(fpi_data)

def hitung_upaya_standar(upaya_df, fpi_df, gears):
    """Hitung upaya standar"""
    standard_effort_data = []
    years = upaya_df['Tahun'].values
    
    for year in years:
        year_data = {'Tahun': year}
        
        total_standard_effort = 0
        
        # Upaya standar untuk setiap alat tangkap
        for gear in gears:
            eff = upaya_df[upaya_df['Tahun'] == year][gear].values[0]
            fpi = fpi_df[fpi_df['Tahun'] == year][gear].values[0]
            
            standard_effort = eff * fpi
            year_data[gear] = standard_effort
            total_standard_effort += standard_effort
        
        # Total upaya standar
        year_data['Jumlah'] = total_standard_effort
        
        standard_effort_data.append(year_data)
    
    return pd.DataFrame(standard_effort_data)

def hitung_cpue_standar(produksi_df, standard_effort_df, gears):
    """Hitung CPUE standar"""
    standard_cpue_data = []
    years = produksi_df['Tahun'].values
    
    for year in years:
        year_data = {'Tahun': year}
        
        total_production = produksi_df[produksi_df['Tahun'] == year]['Jumlah'].values[0]
        total_standard_effort = standard_effort_df[standard_effort_df['Tahun'] == year]['Jumlah'].values[0]
        
        # CPUE Standar Total: Total Produksi / Total Upaya Standar
        if total_standard_effort > 0:
            cpue_standar_total = total_production / total_standard_effort
        else:
            cpue_standar_total = 0
        
        year_data['CPUE_Standar_Total'] = cpue_standar_total
        year_data['Ln_CPUE'] = np.log(cpue_standar_total) if cpue_standar_total > 0 else 0
        
        standard_cpue_data.append(year_data)
    
    return pd.DataFrame(standard_cpue_data)

def analisis_msy_schaefer(standard_effort_total, cpue_standard_total):
    """Analisis MSY menggunakan Model Schaefer"""
    if len(standard_effort_total) < 2:
        return None
    
    # Regresi linear: CPUE = a + b * Effort
    slope, intercept, r_value, p_value, std_err = stats.linregress(standard_effort_total, cpue_standard_total)
    
    a = intercept
    b = slope
    
    # Validasi model
    if b >= 0:
        return {
            'success': False,
            'error': 'Slope (b) harus negatif untuk model Schaefer yang valid'
        }
    
    # Hitung MSY dan F_MSY
    if b != 0:
        F_MSY = -a / (2 * b)
        C_MSY = -(a ** 2) / (4 * b)
    else:
        F_MSY = 0
        C_MSY = 0
    
    return {
        'a': a,
        'b': b,
        'r_squared': r_value ** 2,
        'p_value': p_value,
        'std_err': std_err,
        'F_MSY': F_MSY,
        'C_MSY': C_MSY,
        'success': True
    }

def buat_grafik_lengkap(results, effort_values, cpue_values, production_values, years, 
                       df_cpue, df_fpi, df_standard_effort, gears, display_names, standard_gear):
    """Buat grafik analisis yang lengkap"""
    
    fig = plt.figure(figsize=(20, 12))
    
    # 1. Trend Produksi dan Upaya
    ax1 = plt.subplot(2, 3, 1)
    ax1.bar(years, production_values, color='skyblue', alpha=0.7, label='Produksi')
    ax1.set_xlabel('Tahun')
    ax1.set_ylabel('Produksi (Kg)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.set_title('A. Trend Produksi per Tahun')
    
    ax1_twin = ax1.twinx()
    ax1_twin.plot(years, effort_values, 'ro-', linewidth=2, markersize=6, label='Upaya Standar')
    ax1_twin.set_ylabel('Upaya Standar', color='red')
    ax1_twin.tick_params(axis='y', labelcolor='red')
    
    ax1.legend(loc='upper left')
    ax1_twin.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # 2. Hubungan Upaya vs CPUE
    ax2 = plt.subplot(2, 3, 2)
    ax2.scatter(effort_values, cpue_values, color='blue', s=80, label='Data Aktual', zorder=5)
    
    # Plot garis regresi
    effort_range = np.linspace(min(effort_values), max(effort_values) * 1.2, 100)
    cpue_pred = results['a'] + results['b'] * effort_range
    ax2.plot(effort_range, cpue_pred, 'red', linewidth=2, 
            label=f'Regresi: CPUE = {results["a"]:,.1f} + {results["b"]:,.1f}E')
    
    ax2.axvline(results['F_MSY'], color='green', linestyle='--', 
               label=f'F_MSY = {results["F_MSY"]:.9f}')
    
    ax2.set_xlabel('Upaya Standar Total')
    ax2.set_ylabel('CPUE Standar Total')
    ax2.set_title('B. Hubungan Upaya vs CPUE (Model Schaefer)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Kurva Produksi MSY
    ax3 = plt.subplot(2, 3, 3)
    effort_range_prod = np.linspace(0, max(effort_values) * 1.5, 100)
    catch_pred = results['a'] * effort_range_prod + results['b'] * (effort_range_prod ** 2)
    
    ax3.plot(effort_range_prod, catch_pred, 'purple', linewidth=3, label='Kurva Produksi Schaefer')
    ax3.axvline(results['F_MSY'], color='green', linestyle='--', linewidth=2, label=f'F_MSY')
    ax3.axhline(results['C_MSY'], color='orange', linestyle='--', linewidth=2, 
               label=f'MSY = {results["C_MSY"]:,.0f} kg')
    
    # Plot data aktual
    ax3.scatter(effort_values, production_values, 
               color='blue', s=100, label='Data Aktual', zorder=5)
    
    # Annotate data points
    for i, (x, y) in enumerate(zip(effort_values, production_values)):
        ax3.annotate(f'{years[i]}', (x, y), 
                    xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    ax3.set_xlabel('Upaya Standar Total')
    ax3.set_ylabel('Hasil Tangkapan (Kg)')
    ax3.set_title('C. Kurva Produksi Maximum Sustainable Yield')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Trend CPUE per Alat Tangkap
    ax4 = plt.subplot(2, 3, 4)
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
    
    for i, gear in enumerate(gears):
        if i < len(colors):
            ax4.plot(years, df_cpue[gear].values, 'o-', color=colors[i],
                    label=display_names[i], linewidth=2, markersize=4)
    
    ax4.set_xlabel('Tahun')
    ax4.set_ylabel('CPUE')
    ax4.set_title('D. Trend CPUE per Alat Tangkap')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 5. Trend FPI per Alat Tangkap
    ax5 = plt.subplot(2, 3, 5)
    
    # Tampilkan semua alat kecuali standar
    fpi_gears = [gear for gear in gears if gear != standard_gear]
    fpi_display_names = [display_names[i] for i, gear in enumerate(gears) if gear != standard_gear]
    
    for i, gear in enumerate(fpi_gears):
        if i < len(colors):
            ax5.plot(years, df_fpi[gear].values, 's-', color=colors[i],
                    label=fpi_display_names[i], linewidth=2, markersize=4)
    
    ax5.set_xlabel('Tahun')
    ax5.set_ylabel('FPI')
    ax5.set_title('E. Trend FPI per Alat Tangkap')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # 6. Komposisi Upaya Standar
    ax6 = plt.subplot(2, 3, 6)
    
    # Hitung rata-rata upaya standar per alat
    avg_effort = []
    for gear in gears:
        avg_effort.append(df_standard_effort[gear].mean())
    
    colors_pie = ['lightcoral', 'lightblue', 'lightgreen', 'gold', 'lightpink', 'lightsalmon', 'lightcyan']
    wedges, texts, autotexts = ax6.pie(avg_effort, labels=display_names, colors=colors_pie[:len(gears)], 
                                      autopct='%1.1f%%', startangle=90)
    ax6.set_title('F. Komposisi Rata-rata Upaya Standar')
    
    plt.tight_layout()
    return fig

def hitung_analisis_statistik(df_production, df_effort, df_standard_effort, df_standard_cpue, gears):
    """Hitung berbagai analisis statistik"""
    
    # Statistik produksi
    stat_produksi = df_production[gears + ['Jumlah']].describe()
    
    # Statistik upaya
    stat_upaya = df_effort[gears + ['Jumlah']].describe()
    
    # Trend produksi
    years = np.arange(len(df_production))
    trend_produksi, _, _, _, _ = stats.linregress(years, df_production['Jumlah'].values)
    
    # Trend upaya standar
    trend_upaya, _, _, _, _ = stats.linregress(years, df_standard_effort['Jumlah'].values)
    
    # Trend CPUE standar
    trend_cpue, _, _, _, _ = stats.linregress(years, df_standard_cpue['CPUE_Standar_Total'].values)
    
    return {
        'stat_produksi': stat_produksi,
        'stat_upaya': stat_upaya,
        'trend_produksi': trend_produksi,
        'trend_upaya': trend_upaya,
        'trend_cpue': trend_cpue
    }

# ==============================================
# SIDEBAR - KONFIGURASI
# ==============================================
st.sidebar.header("⚙️ Konfigurasi")

# Konfigurasi Tahun
st.sidebar.subheader("📅 Konfigurasi Tahun")
start_year = st.sidebar.number_input("Tahun Mulai", min_value=2000, max_value=2030, value=2020, key="start_year")
num_years = st.sidebar.number_input("Jumlah Tahun", min_value=2, max_value=20, value=5, key="num_years")

# Konfigurasi Alat Tangkap
st.sidebar.subheader("🎣 Konfigurasi Alat Tangkap")
num_gears = st.sidebar.number_input("Jumlah Alat Tangkap", min_value=2, max_value=8, value=4, key="num_gears")

# Input nama alat tangkap
st.sidebar.subheader("Nama Alat Tangkap")
gear_names = []
display_names = []

config = get_config()

for i in range(num_gears):
    col1, col2 = st.sidebar.columns(2)
    with col1:
        # Gunakan nama existing jika ada, jika tidak buat baru
        if i < len(config['gears']):
            default_internal = config['gears'][i]
            default_display = config['display_names'][i]
        else:
            default_internal = f"Alat_{i+1}"
            default_display = f"Alat Tangkap {i+1}"
            
        internal_name = st.text_input(f"Kode {i+1}", value=default_internal, key=f"internal_{i}")
    with col2:
        display_name = st.text_input(f"Nama Tampilan {i+1}", value=default_display, key=f"display_{i}")
    
    gear_names.append(internal_name)
    display_names.append(display_name)

# Pilih alat standar
standard_gear = st.sidebar.selectbox("Pilih Alat Standar (untuk FPI)", gear_names, 
                                    index=min(1, len(gear_names)-1))

# Simpan konfigurasi
if st.sidebar.button("💾 Simpan Konfigurasi"):
    years = generate_years(start_year, num_years)
    save_config(gear_names, display_names, standard_gear, years, num_years)
    update_data_structure()

# Reset data
if st.sidebar.button("🔄 Reset Data"):
    reset_data()

# ==============================================
# INPUT DATA MANUAL
# ==============================================
st.sidebar.header("📊 Input Data")

# Dapatkan konfigurasi terbaru
config = get_config()
gears = config['gears']
display_names = config['display_names']
standard_gear = config['standard_gear']
years = config['years']

# Input Data Produksi
st.header("1. Data Produksi (Kg)")
st.info(f"**Alat Tangkap:** {', '.join(display_names)}")
st.info(f"**Periode:** {years[0]} - {years[-1]} ({len(years)} tahun)")

# Tabel Produksi
headers = ["Tahun"] + display_names + ["Jumlah"]
prod_cols = st.columns(len(headers))

for i, header in enumerate(headers):
    with prod_cols[i]:
        st.markdown(f"**{header}**")

production_inputs = []
for i, year in enumerate(years):
    cols = st.columns(len(headers))
    
    row_data = {'Tahun': year}
    
    with cols[0]:
        st.markdown(f"**{year}**")
    
    total_prod = 0
    for j, gear in enumerate(gears):
        with cols[j+1]:
            # Gunakan data existing jika ada, jika tidak gunakan default
            if (st.session_state.data_tables['production'] and 
                i < len(st.session_state.data_tables['production'])):
                default_val = st.session_state.data_tables['production'][i].get(gear, 1000 * (i+1) * (j+1))
            else:
                default_val = 1000 * (i+1) * (j+1)
                
            prod_value = st.number_input(
                f"{display_names[j]} {year}", 
                min_value=0.0, 
                value=float(default_val),
                key=f"prod_{gear}_{year}"
            )
            row_data[gear] = prod_value
            total_prod += prod_value
    
    with cols[-1]:
        st.markdown(f"**{total_prod:,.0f}**")
        row_data['Jumlah'] = total_prod
    
    production_inputs.append(row_data)

# Simpan data produksi
st.session_state.data_tables['production'] = production_inputs

# Input Data Upaya
st.header("2. Data Upaya (Trip)")

# Tabel Upaya
effort_cols = st.columns(len(headers))
for i, header in enumerate(headers):
    with effort_cols[i]:
        st.markdown(f"**{header}**")

effort_inputs = []
for i, year in enumerate(years):
    cols = st.columns(len(headers))
    
    row_data = {'Tahun': year}
    
    with cols[0]:
        st.markdown(f"**{year}**")
    
    total_eff = 0
    for j, gear in enumerate(gears):
        with cols[j+1]:
            # Gunakan data existing jika ada, jika tidak gunakan default
            if (st.session_state.data_tables['effort'] and 
                i < len(st.session_state.data_tables['effort'])):
                default_val = st.session_state.data_tables['effort'][i].get(gear, 100 * (i+1) * (j+1))
            else:
                default_val = 100 * (i+1) * (j+1)
                
            eff_value = st.number_input(
                f"Upaya {display_names[j]} {year}", 
                min_value=0, 
                value=int(default_val),
                key=f"eff_{gear}_{year}"
            )
            row_data[gear] = eff_value
            total_eff += eff_value
    
    with cols[-1]:
        st.markdown(f"**{total_eff:,}**")
        row_data['Jumlah'] = total_eff
    
    effort_inputs.append(row_data)

# Simpan data upaya
st.session_state.data_tables['effort'] = effort_inputs

# ==============================================
# EKSPOR DATA
# ==============================================
st.sidebar.header("💾 Ekspor Data")

def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

def convert_df_to_excel(df_list, sheet_names):
    """Convert multiple dataframes to Excel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for i, df in enumerate(df_list):
            df.to_excel(writer, sheet_name=sheet_names[i], index=False)
    return output.getvalue()

# ==============================================
# PROSES ANALISIS
# ==============================================
if st.button("🚀 Lakukan Analisis CPUE dan MSY", type="primary"):
    
    # Konversi ke DataFrame
    df_production = pd.DataFrame(production_inputs)
    df_effort = pd.DataFrame(effort_inputs)
    
    # ==============================================
    # 1. PERHITUNGAN CPUE
    # ==============================================
    st.header("📈 1. Perhitungan CPUE")
    
    st.latex(r"CPUE = \frac{Produksi}{Upaya}")
    
    df_cpue = hitung_cpue(df_production, df_effort, gears)
    
    # Tampilkan CPUE
    cpue_display = df_cpue.copy()
    cpue_display.columns = ['Tahun'] + display_names + ['Jumlah']
    
    st.dataframe(cpue_display.style.format({
        **{name: '{:.4f}' for name in display_names},
        'Jumlah': '{:.4f}'
    }))
    
    # Ekspor CPUE
    csv_cpue = convert_df_to_csv(cpue_display)
    st.download_button(
        label="📥 Download Data CPUE (CSV)",
        data=csv_cpue,
        file_name="data_cpue.csv",
        mime="text/csv",
        key="download_cpue"
    )
    
    # ==============================================
    # 2. PERHITUNGAN FPI
    # ==============================================
    st.header("🎯 2. Perhitungan FPI (Fishing Power Index)")
    
    st.latex(r"FPI = \frac{CPUE\,alat\,tangkap}{CPUE\,alat\,standar}")
    st.info(f"**Alat Standar:** {display_names[gears.index(standard_gear)]} (FPI = 1)")
    st.info("**Metodologi:** FPI dihitung per tahun berdasarkan CPUE aktual setiap tahun")
    
    df_fpi = hitung_fpi_per_tahun(df_cpue, gears, standard_gear)
    
    # Tampilkan FPI
    fpi_display = df_fpi.copy()
    fpi_display.columns = ['Tahun'] + display_names + ['Jumlah']
    
    st.dataframe(fpi_display.style.format({
        **{name: '{:.9f}' for name in display_names},
        'Jumlah': '{:.9f}'
    }))
    
    # Ekspor FPI
    csv_fpi = convert_df_to_csv(fpi_display)
    st.download_button(
        label="📥 Download Data FPI (CSV)",
        data=csv_fpi,
        file_name="data_fpi.csv",
        mime="text/csv",
        key="download_fpi"
    )
    
    # ==============================================
    # 3. PERHITUNGAN UPAYA STANDAR
    # ==============================================
    st.header("⚖️ 3. Perhitungan Upaya Standar")
    
    st.latex(r"Upaya_{standar} = Upaya \times FPI")
    
    df_standard_effort = hitung_upaya_standar(df_effort, df_fpi, gears)
    
    # Tampilkan Upaya Standar
    standard_effort_display = df_standard_effort.copy()
    standard_effort_display.columns = ['Tahun'] + display_names + ['Jumlah']
    
    st.dataframe(standard_effort_display.style.format({
        **{name: '{:.10f}' for name in display_names},
        'Jumlah': '{:.9f}'
    }))
    
    # Ekspor Upaya Standar
    csv_standard_effort = convert_df_to_csv(standard_effort_display)
    st.download_button(
        label="📥 Download Data Upaya Standar (CSV)",
        data=csv_standard_effort,
        file_name="data_upaya_standar.csv",
        mime="text/csv",
        key="download_standard_effort"
    )
    
    # ==============================================
    # 4. PERHITUNGAN CPUE STANDAR
    # ==============================================
    st.header("📊 4. Perhitungan CPUE Standar")
    
    st.latex(r"CPUE_{standar} = \frac{Total\,Produksi}{Total\,Upaya\,Standar}")
    
    df_standard_cpue = hitung_cpue_standar(df_production, df_standard_effort, gears)
    
    # Tampilkan CPUE Standar
    standard_cpue_display = df_standard_cpue.copy()
    standard_cpue_display.columns = ['Tahun', 'CPUE Standar Total', 'Ln CPUE']
    
    st.dataframe(standard_cpue_display.style.format({
        'CPUE Standar Total': '{:.1f}',
        'Ln CPUE': '{:.8f}'
    }))
    
    # Ekspor CPUE Standar
    csv_standard_cpue = convert_df_to_csv(standard_cpue_display)
    st.download_button(
        label="📥 Download Data CPUE Standar (CSV)",
        data=csv_standard_cpue,
        file_name="data_cpue_standar.csv",
        mime="text/csv",
        key="download_standard_cpue"
    )
    
    # ==============================================
    # 5. ANALISIS MSY - MODEL SCHAEFER
    # ==============================================
    st.header("🧮 5. Analisis MSY - Model Schaefer")
    
    # Data untuk regresi
    effort_values = df_standard_effort['Jumlah'].values
    cpue_values = df_standard_cpue['CPUE_Standar_Total'].values
    production_values = df_production['Jumlah'].values
    
    results = analisis_msy_schaefer(effort_values, cpue_values)
    
    if results and results['success']:
        # Tampilkan parameter
        st.subheader("Hasil Regresi Linear")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Intercept (a)", f"{results['a']:,.1f}")
        col2.metric("Slope (b)", f"{results['b']:,.1f}")
        col3.metric("R²", f"{results['r_squared']:.6f}")
        col4.metric("p-value", f"{results['p_value']:.6f}")
        
        # Tampilkan MSY
        st.subheader("Estimasi Maximum Sustainable Yield (MSY)")
        
        st.latex(r"C_{MSY} = -\frac{a^2}{4b}")
        st.latex(r"F_{MSY} = -\frac{a}{2b}")
        
        col1, col2 = st.columns(2)
        col1.metric("F_MSY (Upaya Optimal)", f"{results['F_MSY']:.9f}")
        col2.metric("C_MSY (MSY)", f"{results['C_MSY']:,.2f} kg")
        
        # Validasi hasil
        if results['C_MSY'] < 0:
            st.error("⚠️ **Peringatan**: Nilai MSY negatif. Model mungkin tidak sesuai dengan data.")
        elif results['r_squared'] < 0.3:
            st.warning("⚠️ **Peringatan**: Nilai R² rendah. Hubungan antara upaya dan CPUE mungkin lemah.")
        
        # ==============================================
        # 6. ANALISIS STATISTIK
        # ==============================================
        st.header("📊 6. Analisis Statistik")
        
        statistik = hitung_analisis_statistik(df_production, df_effort, df_standard_effort, df_standard_cpue, gears)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Trend Produksi", f"{statistik['trend_produksi']:+.2f} kg/tahun",
                     delta="Naik" if statistik['trend_produksi'] > 0 else "Turun")
        
        with col2:
            st.metric("Trend Upaya Standar", f"{statistik['trend_upaya']:+.6f}/tahun",
                     delta="Naik" if statistik['trend_upaya'] > 0 else "Turun")
        
        with col3:
            st.metric("Trend CPUE Standar", f"{statistik['trend_cpue']:+.4f}/tahun",
                     delta="Naik" if statistik['trend_cpue'] > 0 else "Turun")
        
        # ==============================================
        # 7. VISUALISASI GRAFIK LENGKAP
        # ==============================================
        st.header("📈 7. Visualisasi Hasil Analisis")
        
        fig = buat_grafik_lengkap(results, effort_values, cpue_values, production_values, years,
                                 df_cpue, df_fpi, df_standard_effort, gears, display_names, standard_gear)
        st.pyplot(fig)
        
        # ==============================================
        # 8. INTERPRETASI DAN REKOMENDASI
        # ==============================================
        st.header("🎯 8. Interpretasi dan Rekomendasi")
        
        # Analisis tingkat pemanfaatan
        latest_effort = effort_values[-1]
        latest_production = production_values[-1]
        
        utilization_effort = (latest_effort / results['F_MSY']) * 100 if results['F_MSY'] > 0 else 0
        utilization_production = (latest_production / results['C_MSY']) * 100 if results['C_MSY'] > 0 else 0
        
        col1, col2 = st.columns(2)
        
        with col1:
            if utilization_effort < 80:
                status = "🟢 UNDER EXPLOITED"
                rekomendasi = "**Rekomendasi**: Tingkatkan upaya penangkapan secara bertahap"
            elif utilization_effort <= 100:
                status = "🟡 FULLY EXPLOITED"
                rekomendasi = "**Rekomendasi**: Pertahankan upaya saat ini dengan monitoring ketat"
            else:
                status = "🔴 OVER EXPLOITED"
                rekomendasi = "**Rekomendasi**: Kurangi upaya penangkapan untuk keberlanjutan"
            
            st.metric("Status Pemanfaatan Upaya", status, f"{utilization_effort:.1f}%")
            st.info(rekomendasi)
        
        with col2:
            st.metric(
                "Produksi vs MSY", 
                f"{latest_production:,.0f} kg",
                f"{utilization_production:.1f}% dari MSY"
            )
        
        # ==============================================
        # 9. EKSPOR SEMUA HASIL
        # ==============================================
        st.header("💾 9. Ekspor Semua Hasil Analisis")
        
        # Buat Excel file dengan semua sheet
        excel_data = convert_df_to_excel(
            [df_production, df_effort, cpue_display, fpi_display, standard_effort_display, standard_cpue_display],
            ['Data Produksi', 'Data Upaya', 'CPUE', 'FPI', 'Upaya Standar', 'CPUE Standar']
        )
        
        st.download_button(
            label="📥 Download Semua Hasil (Excel)",
            data=excel_data,
            file_name="hasil_analisis_cpue_msy.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_all"
        )
        
    else:
        if results and 'error' in results:
            st.error(f"❌ **Error dalam analisis MSY**: {results['error']}")
        else:
            st.error("Tidak dapat melakukan analisis MSY. Data tidak mencukupi.")

# ==============================================
# FOOTER
# ==============================================
st.markdown("---")
st.markdown("""

*Dikembangkan untuk Analisis Perikanan Berkelanjutan | Astriani © 2025*
""") 

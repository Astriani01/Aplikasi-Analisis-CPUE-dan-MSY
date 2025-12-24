import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from scipy import stats
from scipy.optimize import curve_fit
import warnings
from matplotlib.ticker import FuncFormatter
import base64
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import tempfile
import matplotlib

warnings.filterwarnings('ignore')
matplotlib.use('Agg')

# =====================================================
# KONFIGURASI HALAMAN
# =====================================================
st.set_page_config(
    page_title="Website Pendugaan Potensi Lestari Ikan Kurisi - PPN Karangantu",
    layout="wide",
    page_icon="🐟"
)

st.title("🐟 WEBSITE PENDUGAAN POTENSI LESTARI IKAN KURISI (Nemipterus spp)")
st.subheader("📍 Pelabuhan Perikanan Nusantara (PPN) Karangantu, Banten")
st.caption("Analisis CPUE, MSY (JTB), dan Rekomendasi Pengelolaan | Satuan: Produksi (kg), Upaya (trip), CPUE (kg/trip)")

# =====================================================
# INISIALISASI SESSION STATE
# =====================================================
def initialize_session_state():
    """Inisialisasi konfigurasi, data, dan state aplikasi"""

    if 'gear_config' not in st.session_state:
        st.session_state.gear_config = {
            'gears': [
                'Jaring_Insang_Tetap',
                'Jaring_Hela_Dasar',
                'Bagan_Berperahu',
                'Pancing'
            ],
            'display_names': [
                'Jaring Insang Tetap',
                'Jaring Hela Dasar',
                'Bagan Berperahu',
                'Pancing'
            ],
            'standard_gear': 'Jaring_Hela_Dasar',
            'years': [2018, 2019, 2020, 2021, 2022, 2023, 2024],
            'num_years': 7
        }

    if 'data_tables' not in st.session_state:
        st.session_state.data_tables = {
            'production': [
                {'Tahun': 2018, 'Jaring_Insang_Tetap': 1004, 'Jaring_Hela_Dasar': 6105, 'Bagan_Berperahu': 628, 'Pancing': 811, 'Jumlah': 8548},
                {'Tahun': 2019, 'Jaring_Insang_Tetap': 2189, 'Jaring_Hela_Dasar': 10145, 'Bagan_Berperahu': 77, 'Pancing': 396, 'Jumlah': 12807},
                {'Tahun': 2020, 'Jaring_Insang_Tetap': 122, 'Jaring_Hela_Dasar': 9338, 'Bagan_Berperahu': 187, 'Pancing': 311, 'Jumlah': 9958},
                {'Tahun': 2021, 'Jaring_Insang_Tetap': 8, 'Jaring_Hela_Dasar': 10439, 'Bagan_Berperahu': 377, 'Pancing': 418, 'Jumlah': 11242},
                {'Tahun': 2022, 'Jaring_Insang_Tetap': 23, 'Jaring_Hela_Dasar': 10880, 'Bagan_Berperahu': 189, 'Pancing': 21, 'Jumlah': 11113},
                {'Tahun': 2023, 'Jaring_Insang_Tetap': 67, 'Jaring_Hela_Dasar': 13174, 'Bagan_Berperahu': 33, 'Pancing': 13, 'Jumlah': 13287},
                {'Tahun': 2024, 'Jaring_Insang_Tetap': 0, 'Jaring_Hela_Dasar': 12512, 'Bagan_Berperahu': 315, 'Pancing': 85, 'Jumlah': 12913}
            ],
            'effort': [
                {'Tahun': 2018, 'Jaring_Insang_Tetap': 6452, 'Jaring_Hela_Dasar': 2430, 'Bagan_Berperahu': 2434, 'Pancing': 246, 'Jumlah': 11562},
                {'Tahun': 2019, 'Jaring_Insang_Tetap': 9894, 'Jaring_Hela_Dasar': 6270, 'Bagan_Berperahu': 1835, 'Pancing': 139, 'Jumlah': 18138},
                {'Tahun': 2020, 'Jaring_Insang_Tetap': 10122, 'Jaring_Hela_Dasar': 7076, 'Bagan_Berperahu': 1915, 'Pancing': 191, 'Jumlah': 19304},
                {'Tahun': 2021, 'Jaring_Insang_Tetap': 11010, 'Jaring_Hela_Dasar': 7315, 'Bagan_Berperahu': 1445, 'Pancing': 162, 'Jumlah': 19932},
                {'Tahun': 2022, 'Jaring_Insang_Tetap': 18796, 'Jaring_Hela_Dasar': 10183, 'Bagan_Berperahu': 1151, 'Pancing': 77, 'Jumlah': 30207},
                {'Tahun': 2023, 'Jaring_Insang_Tetap': 15899, 'Jaring_Hela_Dasar': 8205, 'Bagan_Berperahu': 777, 'Pancing': 78, 'Jumlah': 24959},
                {'Tahun': 2024, 'Jaring_Insang_Tetap': 16151, 'Jaring_Hela_Dasar': 7241, 'Bagan_Berperahu': 1047, 'Pancing': 71, 'Jumlah': 24510}
            ]
        }

    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None

    if 'selected_models' not in st.session_state:
        st.session_state.selected_models = ['Schaefer', 'Fox']

    if 'uploaded_data' not in st.session_state:
        st.session_state.uploaded_data = None

# =====================================================
# TEMPLATE EXCEL
# =====================================================
def create_excel_template():
    """Membuat template Excel (Produksi dalam kg, Upaya dalam trip)"""

    production_data = {
        'Tahun': [2018, 2019, 2020, 2021, 2022, 2023, 2024],
        'Jaring_Insang_Tetap': [1004, 2189, 122, 8, 23, 67, 0],
        'Jaring_Hela_Dasar': [6105, 10145, 9338, 10439, 10880, 13174, 12512],
        'Bagan_Berperahu': [628, 77, 187, 377, 189, 33, 315],
        'Pancing': [811, 396, 311, 418, 21, 13, 85],
        'Jumlah': [8548, 12807, 9958, 11242, 11113, 13287, 12912]
    }

    effort_data = {
        'Tahun': [2018, 2019, 2020, 2021, 2022, 2023, 2024],
        'Jaring_Insang_Tetap': [6452, 9894, 10122, 11010, 18796, 15899, 16151],
        'Jaring_Hela_Dasar': [2430, 6270, 7076, 7315, 10183, 8205, 7241],
        'Bagan_Berperahu': [2434, 1835, 1915, 1445, 1151, 777, 1047],
        'Pancing': [246, 139, 191, 162, 77, 78, 71],
        'Jumlah': [11562, 18138, 19304, 19932, 30207, 24959, 24510]
    }

    df_prod = pd.DataFrame(production_data)
    df_eff = pd.DataFrame(effort_data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_prod.to_excel(writer, sheet_name='Produksi', index=False)
        df_eff.to_excel(writer, sheet_name='Upaya', index=False)

        workbook = writer.book
        num_fmt = workbook.add_format({'num_format': '#,##0'})

        for sheet in ['Produksi', 'Upaya']:
            ws = writer.sheets[sheet]
            ws.set_column(0, len(df_prod.columns), 16, num_fmt)

    return output.getvalue()

# =====================================================
# TAMPILAN TEMPLATE
# =====================================================
def render_template_section():
    st.header("📋 Template Data Excel")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
**Struktur Template:**

**Sheet Produksi (kg):**
- Tahun
- Produksi per alat tangkap (kg)
- Jumlah (kg)

**Sheet Upaya (trip):**
- Tahun
- Upaya per alat tangkap (trip)
- Jumlah (trip)

**Catatan Penting:**
- Satuan produksi wajib kilogram (kg)
- Nama alat tangkap harus konsisten
- Tahun harus berurutan
- Data numerik tanpa teks
""")

    with col2:
        st.download_button(
            label="📥 Download Template Excel",
            data=create_excel_template(),
            file_name="Template_Data_Perikanan_kg.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# ==============================================
# FUNGSI UPLOAD DATA
# ==============================================
def process_uploaded_file(uploaded_file):
    """Proses file yang diupload (Excel atau CSV)"""
    try:
        if uploaded_file.name.endswith('.xlsx') or uploaded_file.name.endswith('.xls'):
            # Baca semua sheet
            excel_data = pd.read_excel(uploaded_file, sheet_name=None)
            
            st.info(f"📊 Sheet yang ditemukan: {list(excel_data.keys())}")
            
            # PENDETEKSIAN SEDERHANA
            sheet_names = list(excel_data.keys())
            
            if len(sheet_names) >= 2:
                # Otomatis deteksi berdasarkan urutan
                production_sheet = excel_data[sheet_names[0]]
                effort_sheet = excel_data[sheet_names[1]]
                st.success(f"✅ Menggunakan sheet 1 ({sheet_names[0]}) sebagai Produksi")
                st.success(f"✅ Menggunakan sheet 2 ({sheet_names[1]}) sebagai Upaya")
            else:
                # Hanya ada 1 sheet
                production_sheet = excel_data[sheet_names[0]]
                effort_sheet = None
                st.warning("⚠ Hanya 1 sheet ditemukan. Data upaya akan dibuat otomatis.")
                
        elif uploaded_file.name.endswith('.csv'):
            # Baca file CSV
            csv_data = pd.read_csv(uploaded_file)
            production_sheet = csv_data
            effort_sheet = None
            st.info("📊 File CSV dibaca sebagai data produksi")
            
        else:
            st.error("❌ Format file tidak didukung. Harap upload file Excel (.xlsx, .xls) atau CSV (.csv)")
            return None
        
        return {
            'production': production_sheet,
            'effort': effort_sheet,
            'sheet_names': sheet_names if uploaded_file.name.endswith(('.xlsx', '.xls')) else ['CSV File']
        }
        
    except Exception as e:
        st.error(f"❌ Error membaca file: {str(e)}")
        return None

def validate_uploaded_data(uploaded_data):
    """Validasi data yang diupload"""
    production_df = uploaded_data['production']
    
    if production_df is None or production_df.empty:
        st.error("❌ Data produksi tidak ditemukan atau kosong")
        return False
    
    st.success(f"✅ Data produksi valid: {len(production_df)} baris, {len(production_df.columns)} kolom")
    st.write(f"📋 Kolom produksi: {list(production_df.columns)}")
    
    # Cek data upaya jika ada
    effort_df = uploaded_data['effort']
    if effort_df is not None and not effort_df.empty:
        st.success(f"✅ Data upaya valid: {len(effort_df)} baris, {len(effort_df.columns)} kolom")
        st.write(f"📋 Kolom upaya: {list(effort_df.columns)}")
    else:
        st.warning("⚠ Data upaya tidak ditemukan, akan dibuat otomatis")
    
    return True

def convert_uploaded_data(uploaded_data):
    """Konversi data yang diupload ke format aplikasi"""
    production_df = uploaded_data['production']
    effort_df = uploaded_data['effort']
    
    st.write("🔄 Mengkonversi format data...")
    
    def process_dataframe(df, data_type="Produksi"):
        """Proses dataframe menjadi format aplikasi"""
        # Cari kolom tahun
        year_columns = ['tahun', 'year', 'tahun', 'thn', 'yr']
        year_col = None
        for col in df.columns:
            if str(col).lower() in year_columns:
                year_col = col
                break
        if year_col is None:
            year_col = df.columns[0]  # Kolom pertama sebagai tahun
        
        # Identifikasi kolom alat tangkap (selain tahun dan total)
        total_columns = ['jumlah', 'total', 'sum', 'grand total', 'total produksi', 'total upaya']
        gear_columns = [col for col in df.columns 
                       if col != year_col and str(col).lower() not in total_columns]
        
        st.write(f"🔧 {data_type} - Kolom tahun: '{year_col}'")
        st.write(f"🔧 {data_type} - Kolom alat tangkap: {gear_columns}")
        
        # Konversi data
        result_data = []
        for _, row in df.iterrows():
            try:
                year_val = row[year_col]
                if pd.isna(year_val):
                    continue
                    
                # Konversi tahun ke integer
                try:
                    year_val = int(float(year_val))
                except:
                    continue
                
                year_data = {'Tahun': year_val}
                total = 0
                
                for gear in gear_columns:
                    if gear in row:
                        value = float(row[gear]) if pd.notna(row[gear]) else 0
                    else:
                        value = 0
                    year_data[gear] = value
                    total += value
                
                year_data['Jumlah'] = total
                result_data.append(year_data)
                
            except Exception as e:
                st.warning(f"⚠ Skip baris {data_type} dengan error: {e}")
                continue
        
        return result_data, gear_columns
    
    # Proses data produksi
    production_data, prod_gears = process_dataframe(production_df, "Produksi")
    
    # Proses data upaya
    if effort_df is not None and not effort_df.empty:
        effort_data, effort_gears = process_dataframe(effort_df, "Upaya")
        
        # Pastikan kolom alat tangkap konsisten
        if set(prod_gears) != set(effort_gears):
            st.warning("⚠ Kolom alat tangkap tidak konsisten antara produksi dan upaya")
            # Gunakan intersection dari kedua set
            common_gears = list(set(prod_gears) & set(effort_gears))
            if common_gears:
                st.info(f"🔧 Menggunakan kolom umum: {common_gears}")
                gear_columns = common_gears
            else:
                st.error("❌ Tidak ada kolom alat tangkap yang sama antara produksi dan upaya")
                return None
        else:
            gear_columns = prod_gears
    else:
        # Buat data upaya default
        st.info("🔄 Membuat data upaya default...")
        effort_data = []
        for prod_row in production_data:
            year_data = {'Tahun': prod_row['Tahun']}
            total = 0
            for gear in prod_gears:
                # Default: upaya = 10x akar kuadrat produksi (lebih realistis)
                value = max(100, int(np.sqrt(prod_row[gear]) * 10)) if prod_row[gear] > 0 else 100
                year_data[gear] = value
                total += value
            year_data['Jumlah'] = total
            effort_data.append(year_data)
        gear_columns = prod_gears
    
    st.success(f"✅ Konversi selesai: {len(production_data)} tahun, {len(gear_columns)} alat tangkap")
    
    return {
        'production': production_data,
        'effort': effort_data,
        'gears': gear_columns,
        'display_names': gear_columns
    }

def render_upload_section():
    """Render section untuk upload file"""
    st.header("📤 Upload Data")
    
    # Tampilkan template section
    render_template_section()
    
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "Upload file Excel atau CSV data perikanan",
        type=['xlsx', 'xls', 'csv'],
        help="Upload file Excel dengan 2 sheet (Produksi dan Upaya) atau file CSV"
    )
    
    if uploaded_file is not None:
        with st.status("📤 Memproses file...", expanded=True) as status:
            st.write("📖 Membaca file...")
            uploaded_data = process_uploaded_file(uploaded_file)
            
            if uploaded_data is not None:
                st.write("✅ File berhasil dibaca")
                st.write("🔍 Memvalidasi data...")
                
                if validate_uploaded_data(uploaded_data):
                    st.write("✅ Data valid")
                    st.write("🔄 Mengkonversi format...")
                    
                    converted_data = convert_uploaded_data(uploaded_data)
                    
                    if converted_data is not None:
                        st.session_state.uploaded_data = converted_data
                        status.update(label="✅ Data berhasil diproses!", state="complete")
                        
                        # Tampilkan preview
                        st.subheader("👀 Preview Data")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("📊 Data Produksi")
                            st.dataframe(
                                pd.DataFrame(converted_data['production']).style.format({
                                    col: "{:,.1f}" for col in converted_data['gears']
                                }), 
                                use_container_width=True
                            )
                        
                        with col2:
                            st.write("🎣 Data Upaya")
                            st.dataframe(
                                pd.DataFrame(converted_data['effort']).style.format({
                                    col: "{:,}" for col in converted_data['gears']
                                }), 
                                use_container_width=True
                            )
                        
                        # Tombol untuk menggunakan data yang diupload
                        if st.button("💾 Gunakan Data yang Diupload", type="primary", use_container_width=True):
                            gears = converted_data['gears']
                            display_names = converted_data['display_names']
                            years = [data['Tahun'] for data in converted_data['production']]
                            
                            st.session_state.gear_config = {
                                'gears': gears,
                                'display_names': display_names,
                                'standard_gear': gears[0] if gears else 'Jaring_Hela_Dasar',
                                'years': years,
                                'num_years': len(years)
                            }
                            
                            st.session_state.data_tables = {
                                'production': converted_data['production'],
                                'effort': converted_data['effort']
                            }
                            
                            st.session_state.analysis_results = None
                            st.success("✅ Data berhasil diterapkan!")
                            st.rerun()
                    else:
                        status.update(label="❌ Gagal mengkonversi data", state="error")
                else:
                    status.update(label="❌ Data tidak valid", state="error")
            else:
                status.update(label="❌ Gagal membaca file", state="error")
    
    return None, None

# ==============================================
# FUNGSI MODEL MSY - MULTI MODEL
# ==============================================
def analisis_msy_schaefer(standard_effort_total, cpue_standard_total):
    """Analisis MSY menggunakan Model Schaefer (Linear)"""
    if len(standard_effort_total) < 2:
        return None
    
    try:
        slope, intercept, r_value, p_value, std_err = stats.linregress(standard_effort_total, cpue_standard_total)
        
        if slope >= 0:
            return {'success': False, 'error': 'Slope (b) harus negatif untuk model Schaefer yang valid'}
        
        # Hitung MSY parameters
        F_MSY = -intercept / (2 * slope) if slope != 0 else 0
        C_MSY = -(intercept ** 2) / (4 * slope) if slope != 0 else 0
        U_MSY = C_MSY / F_MSY if F_MSY > 0 else 0
        
        return {
            'model': 'Schaefer',
            'a': intercept, 'b': slope, 'r_squared': r_value ** 2, 'p_value': p_value,
            'std_err': std_err, 'F_MSY': F_MSY, 'C_MSY': C_MSY, 'U_MSY': U_MSY,
            'success': True,
            'equation': f"CPUE = {intercept:.4f} + {slope:.6f} × F"
        }
    except Exception as e:
        return {'success': False, 'error': f'Error dalam model Schaefer: {str(e)}'}

def model_fox(F, a, b):
    """Model Fox: C = F * exp(a - b*F)"""
    return F * np.exp(a - b * F)

def analisis_msy_fox(standard_effort_total, production_total):
    """Analisis MSY menggunakan Model Fox (Exponential)"""
    if len(standard_effort_total) < 3:
        return None
    
    try:
        # Initial guess untuk parameter
        initial_guess = [1.0, 0.001]
        
        # Curve fitting
        popt, pcov = curve_fit(model_fox, standard_effort_total, production_total, p0=initial_guess, maxfev=5000)
        a, b = popt
        
        if b <= 0:
            return {'success': False, 'error': 'Parameter b harus positif untuk model Fox yang valid'}
        
        # Hitung MSY parameters untuk model Fox
        F_MSY = 1 / b
        C_MSY = (1 / b) * np.exp(a - 1)
        U_MSY = C_MSY / F_MSY if F_MSY > 0 else 0
        
        # Hitung R-squared
        predictions = model_fox(standard_effort_total, a, b)
        ss_res = np.sum((production_total - predictions) ** 2)
        ss_tot = np.sum((production_total - np.mean(production_total)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {
            'model': 'Fox',
            'a': a, 'b': b, 'r_squared': r_squared, 'p_value': 0.001,
            'std_err': np.sqrt(np.diag(pcov))[0], 'F_MSY': F_MSY, 'C_MSY': C_MSY, 'U_MSY': U_MSY,
            'success': True,
            'equation': f"C = F × exp({a:.4f} - {b:.6f} × F)"
        }
    except Exception as e:
        return {'success': False, 'error': f'Error dalam model Fox: {str(e)}'}

def bandingkan_model_msy(standard_effort_total, cpue_standard_total, production_total, selected_models):
    """Bandingkan beberapa model MSY"""
    results = {}
    
    if 'Schaefer' in selected_models:
        results['Schaefer'] = analisis_msy_schaefer(standard_effort_total, cpue_standard_total)
    
    if 'Fox' in selected_models:
        results['Fox'] = analisis_msy_fox(standard_effort_total, production_total)
    
    return results

# ==============================================
# FUNGSI GRAFIK MSY
# ==============================================
def buat_grafik_msy_schaefer(ax, effort_data, cpue_data, model_results):
    """Buat grafik MSY untuk model Schaefer"""
    if not model_results['success']:
        return
    
    # Data observasi
    ax.scatter(effort_data, cpue_data, color='blue', s=60, zorder=5, label='Data Observasi')
    
    # Garis regresi
    x_fit = np.linspace(0, max(effort_data) * 1.2, 100)
    y_fit = model_results['a'] + model_results['b'] * x_fit
    ax.plot(x_fit, y_fit, 'r-', linewidth=2, label='Model Schaefer')
    
    # Titik MSY
    msy_x = model_results['F_MSY']
    msy_y = model_results['U_MSY']
    ax.scatter([msy_x], [msy_y], color='green', s=100, zorder=6, label='MSY Point')
    ax.axvline(x=msy_x, color='green', linestyle='--', alpha=0.7)
    ax.axhline(y=msy_y, color='green', linestyle='--', alpha=0.7)
    
    ax.set_xlabel('Upaya Penangkapan (F)')
    ax.set_ylabel('CPUE (U)')
    ax.set_title('Model Schaefer: CPUE vs Upaya')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Anotasi MSY
    ax.annotate(f'MSY\nF={msy_x:.1f}\nU={msy_y:.3f}', 
                xy=(msy_x, msy_y), xytext=(msy_x*1.1, msy_y*1.1),
                arrowprops=dict(arrowstyle='->', color='green'))

def buat_grafik_produksi_schaefer(ax, effort_data, production_data, model_results):
    """Buat grafik produksi vs upaya untuk model Schaefer"""
    if not model_results['success']:
        return
    
    # Data observasi
    ax.scatter(effort_data, production_data, color='blue', s=60, zorder=5, label='Data Observasi')
    
    # Kurva produksi Schaefer: C = aF + bF²
    x_fit = np.linspace(0, max(effort_data) * 1.2, 100)
    y_fit = model_results['a'] * x_fit + model_results['b'] * (x_fit ** 2)
    ax.plot(x_fit, y_fit, 'r-', linewidth=2, label='Kurva Produksi')
    
    # Titik MSY
    msy_x = model_results['F_MSY']
    msy_y = model_results['C_MSY']
    ax.scatter([msy_x], [msy_y], color='green', s=100, zorder=6, label='MSY Point')
    ax.axvline(x=msy_x, color='green', linestyle='--', alpha=0.7)
    
    ax.set_xlabel('Upaya Penangkapan (F)')
    ax.set_ylabel('Produksi (C)')
    ax.set_title('Model Schaefer: Produksi vs Upaya')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Anotasi MSY
    ax.annotate(f'MSY\nF={msy_x:.1f}\nC={msy_y:.1f} kg', 
                xy=(msy_x, msy_y), xytext=(msy_x*1.1, msy_y*0.9),
                arrowprops=dict(arrowstyle='->', color='green'))

def buat_grafik_fox(ax, effort_data, production_data, model_results):
    """Buat grafik untuk model Fox"""
    if not model_results['success']:
        return
    
    # Data observasi
    ax.scatter(effort_data, production_data, color='blue', s=60, zorder=5, label='Data Observasi')
    
    # Kurva model Fox
    x_fit = np.linspace(0.1, max(effort_data) * 1.2, 100)
    y_fit = model_fox(x_fit, model_results['a'], model_results['b'])
    ax.plot(x_fit, y_fit, 'r-', linewidth=2, label='Model Fox')
    
    # Titik MSY
    msy_x = model_results['F_MSY']
    msy_y = model_results['C_MSY']
    ax.scatter([msy_x], [msy_y], color='green', s=100, zorder=6, label='MSY Point')
    ax.axvline(x=msy_x, color='green', linestyle='--', alpha=0.7)
    
    ax.set_xlabel('Upaya Penangkapan (F)')
    ax.set_ylabel('Produksi (C)')
    ax.set_title('Model Fox: Produksi vs Upaya')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Anotasi MSY
    ax.annotate(f'MSY\nF={msy_x:.1f}\nC={msy_y:.1f} kg', 
                xy=(msy_x, msy_y), xytext=(msy_x*1.1, msy_y*0.9),
                arrowprops=dict(arrowstyle='->', color='green'))

def buat_grafik_perbandingan_model(ax, effort_data, production_data, all_results):
    """Buat grafik perbandingan semua model"""
    colors = ['red', 'blue']  # Hanya 2 warna untuk 2 model
    line_styles = ['-', '--']
    
    # Data observasi
    ax.scatter(effort_data, production_data, color='black', s=80, zorder=5, label='Data Observasi')
    
    # Plot setiap model yang berhasil
    for i, (model_name, results) in enumerate(all_results.items()):
        if results and results['success']:
            x_fit = np.linspace(0.1, max(effort_data) * 1.2, 100)
            
            if model_name == 'Schaefer':
                y_fit = results['a'] * x_fit + results['b'] * (x_fit ** 2)
            elif model_name == 'Fox':
                y_fit = model_fox(x_fit, results['a'], results['b'])
            else:
                continue
                
            ax.plot(x_fit, y_fit, color=colors[i % len(colors)], 
                   linestyle=line_styles[i % len(line_styles)], 
                   linewidth=2, label=model_name)
            
            # Titik MSY untuk setiap model
            ax.scatter([results['F_MSY']], [results['C_MSY']], 
                      color=colors[i % len(colors)], s=100, marker='*', zorder=6)
    
    ax.set_xlabel('Upaya Penangkapan (F)')
    ax.set_ylabel('Produksi (C)')
    ax.set_title('Perbandingan Model MSY (Schaefer vs Fox)')
    ax.legend()
    ax.grid(True, alpha=0.3)

def render_grafik_msy_lengkap(effort_data, cpue_data, production_data, msy_results):
    """Render grafik MSY yang lengkap"""
    st.header("📈 Grafik Analisis MSY")
    
    successful_models = {k: v for k, v in msy_results.items() if v and v['success']}
    
    if not successful_models:
        st.warning("Tidak ada model yang berhasil untuk ditampilkan grafiknya.")
        return
    
    # Tab untuk berbagai jenis grafik
    tab1, tab2, tab3 = st.tabs(["📊 Grafik Individual", "📈 Grafik Produksi", "🆚 Perbandingan Model"])
    
    with tab1:
        st.subheader("Grafik Individual Setiap Model")
        
        # Tentukan layout berdasarkan jumlah model
        n_models = len(successful_models)
        cols = st.columns(n_models)
        
        for i, (model_name, results) in enumerate(successful_models.items()):
            with cols[i]:
                fig, ax = plt.subplots(figsize=(6, 4))
                
                if model_name == 'Schaefer':
                    buat_grafik_msy_schaefer(ax, effort_data, cpue_data, results)
                elif model_name == 'Fox':
                    buat_grafik_fox(ax, effort_data, production_data, results)
                
                st.pyplot(fig)
                plt.close()
    
    with tab2:
        st.subheader("Grafik Produksi vs Upaya")
        
        # Tentukan layout
        n_models = len(successful_models)
        cols = st.columns(n_models)
        
        for i, (model_name, results) in enumerate(successful_models.items()):
            with cols[i]:
                fig, ax = plt.subplots(figsize=(6, 4))
                
                if model_name == 'Schaefer':
                    buat_grafik_produksi_schaefer(ax, effort_data, production_data, results)
                elif model_name == 'Fox':
                    buat_grafik_fox(ax, effort_data, production_data, results)
                
                st.pyplot(fig)
                plt.close()
    
    with tab3:
        st.subheader("Perbandingan Model Schaefer vs Fox")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        buat_grafik_perbandingan_model(ax, effort_data, production_data, successful_models)
        st.pyplot(fig)
        plt.close()
        
        # Tambahkan tabel perbandingan
        st.subheader("📋 Tabel Perbandingan Model")
        comparison_data = []
        for model_name, results in successful_models.items():
            comparison_data.append({
                'Model': model_name,
                'MSY/JTB (kg)': f"{results['C_MSY']:,.1f}",
                'F_MSY': f"{results['F_MSY']:,.1f}",
                'U_MSY': f"{results['U_MSY']:.3f}",
                'R²': f"{results['r_squared']:.3f}",
                'Persamaan': results['equation']
            })
        
        st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)

# ==============================================
# ANALISIS STATUS STOK DAN REKOMENDASI
# ==============================================
def analisis_status_stok(msy_results, production_values, effort_values, years):
    """Analisis status stok berdasarkan hasil MSY"""
    successful_models = {k: v for k, v in msy_results.items() if v and v['success']}
    if not successful_models:
        return None
    
    # Pilih model terbaik berdasarkan R² tertinggi
    best_model_name, best_model = max(successful_models.items(), key=lambda x: x[1]['r_squared'])
    
    # Data terkini
    current_year = years[-1] if years else None
    current_production = production_values[-1] if len(production_values) > 0 else 0
    current_effort = effort_values[-1] if len(effort_values) > 0 else 0
    
    # Parameter MSY/JTB
    jtb_value = best_model['C_MSY']  # MSY = JTB
    f_msy_value = best_model['F_MSY']
    
    # Analisis status berdasarkan ratio produksi
    production_ratio = (current_production / jtb_value) * 100 if jtb_value > 0 else 0
    
    if production_ratio <= 80:
        status_stok = "UNDERFISHING"
        status_color = "green"
        status_icon = "🟢"
        kategori = "Stok belum tereksploitasi optimal"
        rekomendasi = "Tingkatkan upaya penangkapan secara bertahap hingga mencapai F_MSY"
    elif 80 < production_ratio <= 100:
        status_stok = "FULLY EXPLOITED"
        status_color = "orange"
        status_icon = "🟡"
        kategori = "Stok sudah dieksploitasi optimal"
        rekomendasi = "Pertahankan upaya penangkapan pada level F_MSY"
    else:
        status_stok = "OVERFISHING"
        status_color = "red"
        status_icon = "🔴"
        kategori = "Stok mengalami tekanan berlebih"
        rekomendasi = "Kurangi upaya penangkapan segera"
    
    # Analisis trend
    if len(production_values) >= 3:
        trend = np.polyfit(range(len(production_values[-3:])), production_values[-3:], 1)[0]
        if trend > 0:
            trend_status = "📈 Meningkat"
            trend_direction = "positif"
        elif trend < 0:
            trend_status = "📉 Menurun"
            trend_direction = "negatif"
        else:
            trend_status = "➡ Stabil"
            trend_direction = "stabil"
    else:
        trend_status = "📊 Data tidak cukup"
        trend_direction = "tidak diketahui"
    
    # Hitung rekomendasi kuantitatif
    if status_stok == "OVERFISHING":
        target_pengurangan = current_effort - f_msy_value
        persentase_pengurangan = (target_pengurangan / current_effort * 100) if current_effort > 0 else 0
        aksi_khusus = f"Kurangi {target_pengurangan:,.0f} trip ({persentase_pengurangan:.1f}%)"
    elif status_stok == "UNDERFISHING":
        target_peningkatan = f_msy_value - current_effort
        persentase_peningkatan = (target_peningkatan / current_effort * 100) if current_effort > 0 else 0
        aksi_khusus = f"Tingkatkan {target_peningkatan:,.0f} trip ({persentase_peningkatan:.1f}%)"
    else:
        aksi_khusus = "Pertahankan status saat ini"
    
    return {
        'best_model': best_model_name,
        'current_year': current_year,
        'current_production': current_production,
        'current_effort': current_effort,
        'msy': best_model['C_MSY'],
        'f_msy': best_model['F_MSY'],
        'u_msy': best_model['U_MSY'],
        'jtb': jtb_value,
        'production_ratio': production_ratio,
        'status_stok': status_stok,
        'status_color': status_color,
        'status_icon': status_icon,
        'kategori': kategori,
        'rekomendasi': rekomendasi,
        'trend_status': trend_status,
        'trend_direction': trend_direction,
        'aksi_khusus': aksi_khusus,
        'tahun_data': years
    }

def render_rekomendasi(recommendations, production_data, years):
    """Render rekomendasi pengelolaan dan JTB"""
    st.header("🎯 REKOMENDASI PENGELOLAAN DAN JTB")
    
    # Kartu Status Utama
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"### {recommendations['status_icon']} {recommendations['status_stok']}")
        st.caption(recommendations['kategori'])
    
    with col2:
        st.metric(
            "JTB (Jumlah Tangkapan yang Diperbolehkan)", 
            f"{recommendations['jtb']:,.1f} kg",
            delta=f"{recommendations['production_ratio']:.1f}% dari JTB"
        )
    
    with col3:
        st.metric("Upaya Optimal (F_MSY)", f"{recommendations['f_msy']:,.1f} trip")
    
    with col4:
        st.metric("Trend Produksi", recommendations['trend_status'])
    
    # Grafik Produksi vs JTB
    st.subheader("📈 PERBANDINGAN PRODUKSI DAN JTB")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    production_values = [d['Jumlah'] for d in production_data]
    
    ax.plot(years, production_values, 'bo-', linewidth=2, markersize=8, label='Produksi Aktual')
    ax.axhline(y=recommendations['msy'], color='red', linestyle='--', linewidth=2, label='JTB (MSY)')
    
    # Warna area berdasarkan status
    if recommendations['status_stok'] == "OVERFISHING":
        ax.fill_between(years, recommendations['msy'], max(production_values + [recommendations['msy']]), 
                       color='red', alpha=0.2, label='Area Overfishing')
    elif recommendations['status_stok'] == "UNDERFISHING":
        ax.fill_between(years, 0, recommendations['msy'], 
                       color='green', alpha=0.2, label='Area Underfishing')
    else:
        ax.fill_between(years, 0.9*recommendations['msy'], 1.1*recommendations['msy'], 
                       color='orange', alpha=0.2, label='Area Optimal')
    
    ax.set_xlabel('Tahun')
    ax.set_ylabel('Produksi (kg)')
    ax.set_title('Produksi vs JTB (Jumlah Tangkapan yang Diperbolehkan)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    st.pyplot(fig)
    
    # Rekomendasi Detail
    st.subheader("📋 REKOMENDASI PENGELOLAAN")
    
    st.info(f"**{recommendations['rekomendasi']}**")
    st.write(f"**Aksi Khusus:** {recommendations['aksi_khusus']}")
    
    # Rencana Aksi Berdasarkan Status
    st.subheader("🎯 RENCANA AKSI BERDASARKAN STATUS")
    
    if recommendations['status_stok'] == "OVERFISHING":
        st.error("""
        **🔴 RENCANA AKSI OVERFISHING:**
        
        **1. PENURUNAN SEGERA (1-3 bulan):**
        - Turunkan upaya penangkapan sesuai rekomendasi
        - Implementasi sistem kuota ketat berdasarkan JTB
        - Batasi alat tangkap yang tidak selektif
        
        **2. MONITORING INTENSIF (3-12 bulan):**
        - Pemantauan CPUE bulanan
        - Early warning system untuk stok kritis
        - Patroli pengawasan intensif
        
        **3. REHABILITASI JANGKA MENENGAH (1-2 tahun):**
        - Program restocking jika diperlukan
        - Perlindungan area spawning ground
        - Revisi peraturan alat tangkap
        """)
    
    elif recommendations['status_stok'] == "FULLY EXPLOITED":
        st.warning("""
        **🟡 RENCANA AKSI FULLY EXPLOITED:**
        
        **1. PEMELIHARAAN STATUS (1-3 bulan):**
        - Pertahankan upaya pada level F_MSY
        - Sistem kuota berbasis JTB
        - Optimalisasi alat tangkap
        
        **2. MONITORING RUTIN (3-12 bulan):**
        - Pemantauan stok triwulan
        - Sistem deteksi dini perubahan stok
        - Database produksi real-time
        
        **3. OPTIMASI BERKELANJUTAN (1-2 tahun):**
        - Perbaikan alat tangkap lebih selektif
        - Peningkatan nilai tambah produk
        - Sertifikasi keberlanjutan
        """)
    
    else:  # UNDERFISHING
        st.success("""
        **🟢 RENCANA AKSI UNDERFISHING:**
        
        **1. PENINGKATAN BERTAHAP (1-3 bulan):**
        - Tingkatkan upaya menuju F_MSY
        - Roadmap peningkatan produksi
        - Efisiensi operasi penangkapan
        
        **2. OPTIMASI EFISIENSI (3-12 bulan):**
        - Peningkatan CPUE melalui pelatihan
        - Perbaikan teknologi alat tangkap
        - Manajemen trip yang efektif
        
        **3. EKSPANSI BERKELANJUTAN (1-2 tahun):**
        - Diversifikasi area penangkapan
        - Pengembangan pasar produk
        - Peningkatan kapasitas nelayan
        """)
    
    # Tabel Parameter Pengelolaan
    st.subheader("📊 PARAMETER PENGELOLAAN")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Parameter Kunci")
        param_data = {
            'Parameter': [
                'JTB (MSY)',
                'F_MSY (Upaya Optimal)',
                'U_MSY (CPUE Optimal)',
                'Produksi Terkini',
                'Upaya Terkini',
                'CPUE Terkini'
            ],
            'Nilai': [
                f"{recommendations['jtb']:,.1f} kg",
                f"{recommendations['f_msy']:,.1f} trip",
                f"{recommendations['u_msy']:.3f} kg/trip",
                f"{recommendations['current_production']:,.1f} kg",
                f"{recommendations['current_effort']:,.1f} trip",
                f"{recommendations['current_production']/recommendations['current_effort']:.3f} kg/trip" if recommendations['current_effort'] > 0 else "0 kg/trip"
            ]
        }
        st.dataframe(pd.DataFrame(param_data), use_container_width=True)
    
    with col2:
        st.markdown("##### Analisis Status")
        analisis_data = {
            'Analisis': [
                'Status Stok',
                'Rasio Produksi/JTB',
                'Trend Produksi',
                'Model Terbaik',
                'Tahun Analisis',
                'Rekomendasi Utama'
            ],
            'Hasil': [
                recommendations['status_stok'],
                f"{recommendations['production_ratio']:.1f}%",
                recommendations['trend_status'],
                recommendations['best_model'],
                f"{min(years)}-{max(years)}",
                "Lihat rencana aksi"
            ]
        }
        st.dataframe(pd.DataFrame(analisis_data), use_container_width=True)
    
    # Catatan Penting
    st.info("""
    **💡 CATATAN PENTING:**
    1. **JTB (Jumlah Tangkapan yang Diperbolehkan)** adalah batas maksimal tangkapan yang dapat diambil tanpa mengancam keberlanjutan stok
    2. Rekomendasi ini berdasarkan analisis ilmiah model **{}**
    3. Implementasi harus disesuaikan dengan kondisi lapangan dan regulasi setempat
    4. Monitoring berkala diperlukan untuk evaluasi dan penyesuaian
    5. Partisipasi stakeholder (nelayan, pengusaha, pemerintah) sangat penting untuk keberhasilan
    """.format(recommendations['best_model']))

# ==============================================
# FUNGSI PERHITUNGAN CPUE, FPI, dll. - DIPERBAIKI
# ==============================================
def hitung_cpue(produksi_df, upaya_df, gears):
    """Hitung CPUE untuk setiap alat tangkap"""
    cpue_data = []
    years = produksi_df['Tahun'].values
    
    for year in years:
        clean_year = int(year) if isinstance(year, float) and year.is_integer() else year
        year_data = {'Tahun': clean_year}
        for gear in gears:
            prod = produksi_df[produksi_df['Tahun'] == year][gear].values[0]
            eff = upaya_df[upaya_df['Tahun'] == year][gear].values[0]
            cpue = prod / eff if eff > 0 else 0
            year_data[gear] = cpue
        
        year_data['Jumlah'] = sum([year_data[gear] for gear in gears])
        cpue_data.append(year_data)
    
    return pd.DataFrame(cpue_data)

def hitung_fpi_per_tahun(cpue_df, gears, standard_gear):
    """Hitung FPI per tahun - FPI diambil dari nilai CPUE tertinggi = 1"""
    fpi_data = []
    years = cpue_df['Tahun'].values
    
    for year in years:
        clean_year = int(year) if isinstance(year, float) and year.is_integer() else year
        year_data = {'Tahun': clean_year}
        
        # Cari nilai CPUE maksimum untuk tahun ini
        cpue_values = [cpue_df[cpue_df['Tahun'] == year][gear].values[0] for gear in gears]
        max_cpue = max(cpue_values) if cpue_values else 1
        
        for gear in gears:
            cpue_gear = cpue_df[cpue_df['Tahun'] == year][gear].values[0]
            # FPI = CPUE gear / CPUE maksimum (sehingga nilai tertinggi = 1)
            fpi = cpue_gear / max_cpue if max_cpue > 0 else 0
            year_data[gear] = fpi
        
        year_data['Jumlah'] = sum([year_data[gear] for gear in gears])
        fpi_data.append(year_data)
    
    return pd.DataFrame(fpi_data)

def hitung_upaya_standar(upaya_df, fpi_df, gears):
    """Hitung upaya standar"""
    standard_effort_data = []
    years = upaya_df['Tahun'].values
    
    for year in years:
        clean_year = int(year) if isinstance(year, float) and year.is_integer() else year
        year_data = {'Tahun': clean_year}
        total_standard_effort = 0
        
        for gear in gears:
            eff = upaya_df[upaya_df['Tahun'] == year][gear].values[0]
            fpi = fpi_df[fpi_df['Tahun'] == year][gear].values[0]
            standard_effort = eff * fpi
            year_data[gear] = standard_effort
            total_standard_effort += standard_effort
        
        year_data['Jumlah'] = total_standard_effort
        standard_effort_data.append(year_data)
    
    return pd.DataFrame(standard_effort_data)

def hitung_cpue_standar(produksi_df, standard_effort_df, gears):
    """Hitung CPUE standar per alat tangkap dan total - DIPERBAIKI"""
    standard_cpue_data = []
    years = produksi_df['Tahun'].values
    
    for year in years:
        clean_year = int(year) if isinstance(year, float) and year.is_integer() else year
        year_data = {'Tahun': clean_year}
        
        # Hitung CPUE standar per alat tangkap
        for gear in gears:
            prod = produksi_df[produksi_df['Tahun'] == year][gear].values[0]
            std_eff = standard_effort_df[standard_effort_df['Tahun'] == year][gear].values[0]
            cpue_standar = prod / std_eff if std_eff > 0 else 0
            year_data[f'{gear}_Std_CPUE'] = cpue_standar
        
        # Hitung CPUE standar total
        total_production = produksi_df[produksi_df['Tahun'] == year]['Jumlah'].values[0]
        total_standard_effort = standard_effort_df[standard_effort_df['Tahun'] == year]['Jumlah'].values[0]
        
        cpue_standar_total = total_production / total_standard_effort if total_standard_effort > 0 else 0
        year_data['CPUE_Standar_Total'] = cpue_standar_total
        year_data['Ln_CPUE'] = np.log(cpue_standar_total) if cpue_standar_total > 0 else 0
        
        standard_cpue_data.append(year_data)
    
    return pd.DataFrame(standard_cpue_data)

# ==============================================
# FUNGSI EKSPOR HASIL ANALISIS - DIPERBAIKI
# ==============================================
def ekspor_hasil_analisis():
    """Ekspor hasil analisis ke file Excel termasuk rekomendasi"""
    if st.session_state.analysis_results is None:
        st.error("❌ Tidak ada hasil analisis untuk diekspor. Silakan lakukan analisis terlebih dahulu.")
        return None
    
    try:
        results = st.session_state.analysis_results
        
        # Buat file Excel dalam memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Sheet Data Dasar
            results['df_production'].to_excel(writer, sheet_name='Data Produksi', index=False)
            results['df_effort'].to_excel(writer, sheet_name='Data Upaya', index=False)
            results['df_cpue'].to_excel(writer, sheet_name='CPUE Data', index=False)
            results['df_fpi'].to_excel(writer, sheet_name='FPI Data', index=False)
            results['df_standard_effort'].to_excel(writer, sheet_name='Upaya Standar', index=False)
            results['df_standard_cpue'].to_excel(writer, sheet_name='CPUE Standar', index=False)  # DIPERBAIKI
            
            # Sheet Hasil MSY
            msy_data = []
            for model_name, model_results in results['msy_results'].items():
                if model_results and model_results['success']:
                    msy_data.append({
                        'Model': model_name,
                        'JTB (kg)': model_results['C_MSY'],
                        'F_MSY': model_results['F_MSY'],
                        'U_MSY': model_results['U_MSY'],
                        'R²': model_results['r_squared'],
                        'Persamaan': model_results['equation'],
                        'Status': 'Valid'
                    })
                else:
                    msy_data.append({
                        'Model': model_name,
                        'JTB (kg)': '-',
                        'F_MSY': '-',
                        'U_MSY': '-',
                        'R²': '-',
                        'Persamaan': '-',
                        'Status': model_results.get('error', 'Gagal') if model_results else 'Tidak ada hasil'
                    })
            
            df_msy = pd.DataFrame(msy_data)
            df_msy.to_excel(writer, sheet_name='Hasil MSY', index=False)
            
            # Sheet Rekomendasi (jika ada)
            if 'recommendations' in results:
                rec = results['recommendations']
                
                # Sheet Ringkasan Rekomendasi
                summary_data = pd.DataFrame({
                    'Parameter': [
                        'Tahun Analisis', 'Status Stok', 'JTB (kg)', 'F_MSY', 'U_MSY',
                        'Produksi Terkini (kg)', 'Upaya Terkini (trip)', 
                        'Rasio Produksi/JTB (%)', 'Trend Produksi', 'Model Terbaik', 'Rekomendasi Utama'
                    ],
                    'Nilai': [
                        rec['current_year'], rec['status_stok'], f"{rec['jtb']:,.1f}", 
                        f"{rec['f_msy']:,.1f}", f"{rec['u_msy']:.3f}",
                        f"{rec['current_production']:,.1f}", f"{rec['current_effort']:,.1f}",
                        f"{rec['production_ratio']:.1f}", rec['trend_status'], rec['best_model'], rec['rekomendasi']
                    ]
                })
                summary_data.to_excel(writer, sheet_name='Rekomendasi', index=False)
                
                # Sheet Rencana Aksi Detail
                if rec['status_stok'] == "OVERFISHING":
                    action_data = pd.DataFrame({
                        'Prioritas': ['Segera (1-3 bulan)', 'Jangka Pendek (3-12 bulan)', 'Jangka Menengah (1-2 tahun)', 'Jangka Panjang (2+ tahun)'],
                        'Aksi': [
                            'Pengurangan upaya penangkapan',
                            'Implementasi sistem kuota',
                            'Restorasi habitat dan stok',
                            'Kelembagaan berkelanjutan'
                        ],
                        'Target': [
                            '-30% dari level saat ini',
                            f'100% compliance kuota {rec["jtb"]:,.0f} kg',
                            'Peningkatan 20% stok',
                            'Sertifikasi keberlanjutan'
                        ]
                    })
                elif rec['status_stok'] == "FULLY EXPLOITED":
                    action_data = pd.DataFrame({
                        'Prioritas': ['Segera (1-3 bulan)', 'Jangka Pendek (3-12 bulan)', 'Jangka Menengah (1-2 tahun)', 'Jangka Panjang (2+ tahun)'],
                        'Aksi': [
                            'Pemeliharaan upaya optimal',
                            'Monitoring intensif',
                            'Pengembangan early warning',
                            'Optimalisasi berkelanjutan'
                        ],
                        'Target': [
                            f'Pertahankan {rec["f_msy"]:,.0f} trip',
                            'Real-time monitoring system',
                            'Sistem deteksi dini',
                            'Sertifikasi MSC'
                        ]
                    })
                else:  # UNDERFISHING
                    action_data = pd.DataFrame({
                        'Prioritas': ['Segera (1-3 bulan)', 'Jangka Pendek (3-12 bulan)', 'Jangka Menengah (1-2 tahun)', 'Jangka Panjang (2+ tahun)'],
                        'Aksi': [
                            'Peningkatan bertahap',
                            'Optimasi efisiensi',
                            'Ekspansi berkelanjutan',
                            'Pengembangan pasar'
                        ],
                        'Target': [
                            'Roadmap peningkatan',
                            '+20% efisiensi alat tangkap',
                            '3 area baru berkelanjutan',
                            'Ekspor produk premium'
                        ]
                    })
                action_data.to_excel(writer, sheet_name='Rencana Aksi', index=False)
            
            workbook = writer.book
            worksheet_summary = workbook.add_worksheet('Ringkasan Analisis')
            
            # Formatting
            format_header = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC'})
            
            # Tulis ringkasan
            worksheet_summary.write('A1', 'RINGKASAN HASIL ANALISIS CPUE, MSY DAN REKOMENDASI', format_header)
            worksheet_summary.write('A3', 'Parameter', format_header)
            worksheet_summary.write('B3', 'Nilai', format_header)
            
            # Cari model terbaik
            successful_models = {k: v for k, v in results['msy_results'].items() 
                               if v and v['success']}
            if successful_models:
                best_model = max(successful_models.items(), key=lambda x: x[1]['r_squared'])
                best_model_name, best_model_results = best_model
                
                summary_data = [
                    ('Model Terbaik', best_model_name),
                    ('JTB (Jumlah Tangkapan yang Diperbolehkan)', f"{best_model_results['C_MSY']:,.1f} kg"),
                    ('Upaya Optimal (F_MSY)', f"{best_model_results['F_MSY']:,.1f}"),
                    ('CPUE Optimum (U_MSY)', f"{best_model_results['U_MSY']:.3f}"),
                    ('Koefisien Determinasi (R²)', f"{best_model_results['r_squared']:.3f}"),
                    ('Jumlah Tahun Data', len(results['df_production'])),
                    ('Jumlah Alat Tangkap', len(st.session_state.gear_config['gears'])),
                    ('Alat Tangkap Standar', st.session_state.gear_config['standard_gear']),
                    ('Rentang Tahun', f"{results['df_production']['Tahun'].min()} - {results['df_production']['Tahun'].max()}")
                ]
                
                if 'recommendations' in results:
                    rec = results['recommendations']
                    summary_data.append(('Status Stok', rec['status_stok']))
                    summary_data.append(('Rasio Produksi/JTB', f"{rec['production_ratio']:.1f}%"))
                    summary_data.append(('Trend Produksi', rec['trend_status']))
                
                for i, (param, value) in enumerate(summary_data, start=4):
                    worksheet_summary.write(f'A{i}', param)
                    worksheet_summary.write(f'B{i}', value)
            
            worksheet_summary.set_column('A:A', 35)
            worksheet_summary.set_column('B:B', 35)
        
        processed_data = output.getvalue()
        return processed_data
        
    except Exception as e:
        st.error(f"❌ Error saat mengekspor hasil: {str(e)}")
        return None

def render_ekspor_section():
    """Render section untuk ekspor hasil"""
    if st.session_state.analysis_results is None:
        st.warning("📊 Hasil analisis belum tersedia. Silakan lakukan analisis terlebih dahulu.")
        return
    
    st.header("📤 Ekspor Hasil Analisis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        *📁 File Excel yang Akan Dihasilkan:*
        
        *Sheet 'Data Produksi'*: Data produksi per alat tangkap
        *Sheet 'Data Upaya'*: Data upaya penangkapan per alat tangkap  
        *Sheet 'CPUE Data'*: Hasil perhitungan CPUE
        *Sheet 'FPI Data'*: Hasil perhitungan Fishing Power Index
        *Sheet 'Upaya Standar'*: Hasil standardisasi upaya
        *Sheet 'CPUE Standar'*: **Hasil CPUE standar per alat tangkap**  ← DIPERBAIKI
        *Sheet 'Hasil MSY'*: Perbandingan model Schaefer vs Fox
        *Sheet 'Rekomendasi'*: **Rekomendasi pengelolaan dan JTB**
        *Sheet 'Rencana Aksi'*: **Rencana aksi berdasarkan status stok**
        *Sheet 'Ringkasan Analisis'*: Ringkasan lengkap hasil analisis
        
        *💡 Informasi:*
        - File berisi semua data dan hasil analisis
        - **Termasuk rekomendasi pengelolaan berbasis JTB**
        - Format Excel (.xlsx) yang mudah dibaca
        - Dapat digunakan untuk laporan dan pengambilan keputusan
        """)
    
    with col2:
        # Ekspor hasil analisis
        export_data = ekspor_hasil_analisis()
        if export_data is not None:
            st.download_button(
                label="📥 Download Hasil Analisis + Rekomendasi",
                data=export_data,
                file_name=f"Hasil_Analisis_Rekomendasi_IKAN_KURISI_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
            )
        
        st.markdown("""
        *🔧 Cara Penggunaan:*
        1. Lakukan analisis terlebih dahulu
        2. Klik tombol download di samping
        3. File Excel akan berisi semua hasil **termasuk rekomendasi**
        4. Gunakan untuk dokumentasi, laporan, dan pengambilan keputusan
        """)

# ==============================================
# FUNGSI UTILITAS DAN KONFIGURASI
# ==============================================
def get_config():
    return st.session_state.gear_config

def save_config(gears, display_names, standard_gear, years, num_years):
    st.session_state.gear_config = {
        'gears': gears, 'display_names': display_names, 'standard_gear': standard_gear,
        'years': years, 'num_years': num_years
    }

def generate_years(start_year, num_years):
    return [start_year + i for i in range(num_years)]

def reset_data():
    # Reset ke data contoh yang konsisten
    st.session_state.data_tables = {
         'production': [
                {'Tahun': 2018, 'Jaring_Insang_Tetap': 1004, 'Jaring_Hela_Dasar': 6105, 'Bagan_Berperahu': 628, 'Pancing': 811, 'Jumlah': 8548},
                {'Tahun': 2019, 'Jaring_Insang_Tetap': 2189, 'Jaring_Hela_Dasar': 10145, 'Bagan_Berperahu': 77, 'Pancing': 396, 'Jumlah': 12807},
                {'Tahun': 2020, 'Jaring_Insang_Tetap': 122, 'Jaring_Hela_Dasar': 9338, 'Bagan_Berperahu': 187, 'Pancing': 311, 'Jumlah': 9958},
                {'Tahun': 2021, 'Jaring_Insang_Tetap': 8, 'Jaring_Hela_Dasar': 10439, 'Bagan_Berperahu': 377, 'Pancing': 418, 'Jumlah': 11242},
                {'Tahun': 2022, 'Jaring_Insang_Tetap': 23, 'Jaring_Hela_Dasar': 10880, 'Bagan_Berperahu': 189, 'Pancing': 21, 'Jumlah': 11113},
                {'Tahun': 2023, 'Jaring_Insang_Tetap': 67, 'Jaring_Hela_Dasar': 13174, 'Bagan_Berperahu': 33, 'Pancing': 13, 'Jumlah': 13287},
                {'Tahun': 2024, 'Jaring_Insang_Tetap': 0, 'Jaring_Hela_Dasar': 12512, 'Bagan_Berperahu': 315, 'Pancing': 85, 'Jumlah': 12913}
            ],
            'effort': [
                {'Tahun': 2018, 'Jaring_Insang_Tetap': 6452, 'Jaring_Hela_Dasar': 2430, 'Bagan_Berperahu': 2434, 'Pancing': 246, 'Jumlah': 11562},
                {'Tahun': 2019, 'Jaring_Insang_Tetap': 9894, 'Jaring_Hela_Dasar': 6270, 'Bagan_Berperahu': 1835, 'Pancing': 139, 'Jumlah': 18138},
                {'Tahun': 2020, 'Jaring_Insang_Tetap': 10122, 'Jaring_Hela_Dasar': 7076, 'Bagan_Berperahu': 1915, 'Pancing': 191, 'Jumlah': 19304},
                {'Tahun': 2021, 'Jaring_Insang_Tetap': 11010, 'Jaring_Hela_Dasar': 7315, 'Bagan_Berperahu': 1445, 'Pancing': 162, 'Jumlah': 19932},
                {'Tahun': 2022, 'Jaring_Insang_Tetap': 18796, 'Jaring_Hela_Dasar': 10183, 'Bagan_Berperahu': 1151, 'Pancing': 77, 'Jumlah': 30207},
                {'Tahun': 2023, 'Jaring_Insang_Tetap': 15899, 'Jaring_Hela_Dasar': 8205, 'Bagan_Berperahu': 777, 'Pancing': 78, 'Jumlah': 24959},
                {'Tahun': 2024, 'Jaring_Insang_Tetap': 16151, 'Jaring_Hela_Dasar': 7241, 'Bagan_Berperahu': 1047, 'Pancing': 71, 'Jumlah': 24510}
            ]
    }
    st.session_state.analysis_results = None

def update_data_structure():
    config = get_config()
    current_production = st.session_state.data_tables.get('production', [])
    current_effort = st.session_state.data_tables.get('effort', [])
    
    new_production = []
    new_effort = []
    
    for i, year in enumerate(config['years']):
        prod_row = {'Tahun': year}
        eff_row = {'Tahun': year}
        
        for gear in config['gears']:
            # Cari nilai dari data current jika ada
            prod_val = 0
            eff_val = 0
            
            # Cari di data produksi current
            for current_prod in current_production:
                if current_prod['Tahun'] == year and gear in current_prod:
                    prod_val = current_prod[gear]
                    break
            
            # Cari di data upaya current
            for current_eff in current_effort:
                if current_eff['Tahun'] == year and gear in current_eff:
                    eff_val = current_eff[gear]
                    break
            
            # Jika tidak ditemukan, gunakan default
            if prod_val == 0:
                prod_val = 1000 * (i+1)
            if eff_val == 0:
                eff_val = 100 * (i+1)
                
            prod_row[gear] = prod_val
            eff_row[gear] = eff_val
        
        prod_row['Jumlah'] = sum([prod_row[gear] for gear in config['gears']])
        eff_row['Jumlah'] = sum([eff_row[gear] for gear in config['gears']])
        
        new_production.append(prod_row)
        new_effort.append(eff_row)
    
    st.session_state.data_tables = {'production': new_production, 'effort': new_effort}

# ==============================================
# FUNGSI SIDEBAR
# ==============================================
def render_sidebar():
    """Render sidebar dengan fitur upload"""
    st.sidebar.header("⚙ KONFIGURASI ANALISIS")
    
    # Pilihan Model MSY - Hanya Schaefer dan Fox
    st.sidebar.subheader("🔧 Pilih Model MSY")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        schaefer = st.checkbox("Schaefer", value=True, key="schaefer_model")
    with col2:
        fox = st.checkbox("Fox", value=True, key="fox_model")
    
    # Simpan pilihan model
    selected_models = []
    if schaefer:
        selected_models.append('Schaefer')
    if fox:
        selected_models.append('Fox')
    
    st.session_state.selected_models = selected_models
    
    # Konfigurasi Tahun
    st.sidebar.subheader("📅 Konfigurasi Tahun")
    start_year = st.sidebar.number_input("Tahun Mulai", min_value=2000, max_value=2030, value=2018)
    num_years = st.sidebar.number_input("Jumlah Tahun", min_value=2, max_value=20, value=6)
    
    # Konfigurasi Alat Tangkap
    st.sidebar.subheader("🎣 Konfigurasi Alat Tangkap")
    num_gears = st.sidebar.number_input("Jumlah Alat Tangkap", min_value=2, max_value=8, value=4)
    
    # Input nama alat tangkap
    gear_names = []
    display_names = []
    
    config = get_config()
    
    for i in range(num_gears):
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if i < len(config['gears']):
                default_internal = config['gears'][i]
                default_display = config['display_names'][i]
            else:
                default_internal = f"Alat_{i+1}"
                default_display = f"Alat {i+1}"
                
            internal_name = st.text_input(f"Kode {i+1}", value=default_internal, key=f"internal_{i}")
        with col2:
            display_name = st.text_input(f"Nama {i+1}", value=default_display, key=f"display_{i}")
        
        gear_names.append(internal_name)
        display_names.append(display_name)
    
    standard_gear = st.sidebar.selectbox("Alat Standar (FPI)", gear_names, index=min(1, len(gear_names)-1))
    
    # Simpan konfigurasi
    if st.sidebar.button("💾 Simpan Konfigurasi", use_container_width=True, key="save_config"):
        years = generate_years(start_year, num_years)
        save_config(gear_names, display_names, standard_gear, years, num_years)
        update_data_structure()
        st.sidebar.success("Konfigurasi berhasil disimpan!")
        st.rerun()
    
    # Reset data
    if st.sidebar.button("🔄 Reset ke Data Contoh", use_container_width=True, key="reset_data"):
        reset_data()
        st.sidebar.success("Data berhasil direset!")
        st.rerun()
    
    # Informasi Upload
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **🐟 IKAN KURISI (Nemipterus spp)**
    
    **📍 LOKASI:** PPN Karangantu, Banten
    
    **📊 SATUAN:**
    - Produksi: kilogram (kg)
    - Upaya: trip
    - CPUE: kg/trip
    - **JTB:** kg/tahun
    
    **🔧 MODEL ANALISIS:**
    - Schaefer: Model linear
    - Fox: Model eksponensial
    
    **🎯 OUTPUT BARU:**
    - **JTB (Jumlah Tangkapan yang Diperbolehkan)**
    - **Rekomendasi pengelolaan**
    - **Status stok (Underfishing/Fully/Overfishing)**
    - **Rencana aksi detail**
    """)

# ==============================================
# FUNGSI INPUT DATA MANUAL DAN UPLOAD
# ==============================================
def render_manual_input():
    """Render input data manual"""
    config = get_config()
    gears = config['gears']
    display_names = config['display_names']
    years = config['years']
    
    st.header("📊 Input Data Perikanan Manual")
    
    # Tampilkan data current
    current_data = st.session_state.data_tables['production']
    if current_data:
        st.info(f"*Data terkini:* {len(current_data)} tahun ({years[0]} - {years[-1]}), {len(gears)} alat tangkap")
    
    # Input Data Produksi
    st.subheader("🍤 Data Produksi (kg)")
    
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
            st.markdown(f"{year}")
        
        total_prod = 0
        for j, gear in enumerate(gears):
            with cols[j+1]:
                # Cari nilai default dari data current
                default_val = 0
                for prod_data in st.session_state.data_tables['production']:
                    if prod_data['Tahun'] == year and gear in prod_data:
                        default_val = prod_data[gear]
                        break
                
                if default_val == 0:
                    default_val = 1000 * (i+1)
                    
                prod_value = st.number_input(
                    f"prod_{gear}_{year}", 
                    min_value=0.0,
                    value=float(default_val),
                    step=100.0,
                    format="%.1f",
                    label_visibility="collapsed",
                    key=f"prod_{gear}_{year}"
                )
                row_data[gear] = prod_value
                total_prod += prod_value
        
        with cols[-1]:
            st.markdown(f"**{total_prod:,.1f}**")
            row_data['Jumlah'] = total_prod
        
        production_inputs.append(row_data)
    
    # Input Data Upaya
    st.subheader("🎣 Data Upaya (trip)")
    
    effort_cols = st.columns(len(headers))
    for i, header in enumerate(headers):
        with effort_cols[i]:
            st.markdown(f"**{header}**")
    
    effort_inputs = []
    for i, year in enumerate(years):
        cols = st.columns(len(headers))
        row_data = {'Tahun': year}
        
        with cols[0]:
            st.markdown(f"{year}")
        
        total_eff = 0
        for j, gear in enumerate(gears):
            with cols[j+1]:
                # Cari nilai default dari data current
                default_val = 0
                for eff_data in st.session_state.data_tables['effort']:
                    if eff_data['Tahun'] == year and gear in eff_data:
                        default_val = eff_data[gear]
                        break
                
                if default_val == 0:
                    default_val = 100 * (i+1)
                    
                eff_value = st.number_input(
                    f"eff_{gear}_{year}", 
                    min_value=0,
                    value=int(default_val),
                    step=10,
                    label_visibility="collapsed",
                    key=f"eff_{gear}_{year}"
                )
                row_data[gear] = eff_value
                total_eff += eff_value
        
        with cols[-1]:
            st.markdown(f"**{total_eff:,}**")
            row_data['Jumlah'] = total_eff
        
        effort_inputs.append(row_data)
    
    # Simpan data
    st.session_state.data_tables['production'] = production_inputs
    st.session_state.data_tables['effort'] = effort_inputs
    
    return production_inputs, effort_inputs

def render_data_input():
    """Render input data manual dan upload"""
    
    # Tab untuk pilihan input method
    tab1, tab2 = st.tabs(["📤 Upload File", "✍ Input Manual"])
    
    with tab1:
        production_inputs, effort_inputs = render_upload_section()
    
    with tab2:
        production_inputs, effort_inputs = render_manual_input()
    
    # Kembalikan data dari session state sebagai fallback
    if production_inputs is None or effort_inputs is None:
        production_inputs = st.session_state.data_tables['production']
        effort_inputs = st.session_state.data_tables['effort']
    
    return production_inputs, effort_inputs

# ==============================================
# PROSES ANALISIS UTAMA DENGAN REKOMENDASI - DIPERBAIKI
# ==============================================
def buat_visualisasi_sederhana(df_production, df_effort, df_cpue, df_fpi, df_standard_effort, df_standard_cpue, results_dict, gears, display_names):
    """Buat visualisasi sederhana untuk hasil analisis"""
    
    # Tab untuk visualisasi tambahan
    tab1, tab2, tab3 = st.tabs(["📈 Trend Produksi & Upaya", "🎯 CPUE & FPI", "📊 CPUE Standar"])
    
    with tab1:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Plot produksi
        ax1.plot(df_production['Tahun'], df_production['Jumlah'], 'bo-', linewidth=2, markersize=8, label='Produksi')
        ax1.set_title('Total Produksi per Tahun')
        ax1.set_xlabel('Tahun')
        ax1.set_ylabel('Produksi (kg)')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Plot upaya
        ax2.plot(df_effort['Tahun'], df_effort['Jumlah'], 'rs-', linewidth=2, markersize=8, label='Upaya')
        ax2.set_title('Total Upaya per Tahun')
        ax2.set_xlabel('Tahun')
        ax2.set_ylabel('Upaya (trip)')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        plt.tight_layout()
        st.pyplot(fig)
    
    with tab2:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Plot CPUE
        for i, gear in enumerate(gears):
            ax1.plot(df_cpue['Tahun'], df_cpue[gear], 'o-', label=display_names[i], markersize=4)
        ax1.set_title('CPUE per Alat Tangkap')
        ax1.set_xlabel('Tahun')
        ax1.set_ylabel('CPUE (kg/trip)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot FPI
        for i, gear in enumerate(gears):
            ax2.plot(df_fpi['Tahun'], df_fpi[gear], 's-', label=display_names[i], markersize=4)
        ax2.set_title('FPI per Alat Tangkap')
        ax2.set_xlabel('Tahun')
        ax2.set_ylabel('FPI')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        st.pyplot(fig)
    
    with tab3:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Plot CPUE Standar per alat tangkap
        # Cari kolom CPUE Standar
        cpue_std_cols = [col for col in df_standard_cpue.columns if '_Std_CPUE' in col]
        
        if cpue_std_cols:
            for i, col in enumerate(cpue_std_cols):
                # Ekstrak nama alat tangkap dari nama kolom
                gear_name = col.replace('_Std_CPUE', '')
                display_name = display_names[gears.index(gear_name)] if gear_name in gears else gear_name
                ax1.plot(df_standard_cpue['Tahun'], df_standard_cpue[col], 'o-', 
                        label=display_name, markersize=4)
        
        ax1.set_title('CPUE Standar per Alat Tangkap')
        ax1.set_xlabel('Tahun')
        ax1.set_ylabel('CPUE Standar (kg/trip)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot CPUE Standar Total
        ax2.plot(df_standard_cpue['Tahun'], df_standard_cpue['CPUE_Standar_Total'], 
                'go-', linewidth=2, markersize=8, label='CPUE Standar Total')
        ax2.set_title('CPUE Standar Total')
        ax2.set_xlabel('Tahun')
        ax2.set_ylabel('CPUE Standar Total (kg/trip)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        st.pyplot(fig)

def proses_analisis_utama(production_inputs, effort_inputs):
    """Proses analisis utama dengan multi-model MSY dan rekomendasi"""
    df_production = pd.DataFrame(production_inputs)
    df_effort = pd.DataFrame(effort_inputs)
    config = get_config()
    gears = config['gears']
    display_names = config['display_names']
    standard_gear = config['standard_gear']
    
    with st.status("🔄 Sedang menganalisis...", expanded=True) as status:
        st.write("📈 Menghitung CPUE...")
        df_cpue = hitung_cpue(df_production, df_effort, gears)
        
        st.write("🎯 Menghitung FPI...")
        df_fpi = hitung_fpi_per_tahun(df_cpue, gears, standard_gear)
        
        st.write("⚖ Menghitung upaya standar...")
        df_standard_effort = hitung_upaya_standar(df_effort, df_fpi, gears)
        
        st.write("📊 Menghitung CPUE standar...")  # DIPERBAIKI
        df_standard_cpue = hitung_cpue_standar(df_production, df_standard_effort, gears)
        
        st.write("🧮 Analisis MSY Multi-Model...")
        effort_values = df_standard_effort['Jumlah'].values
        cpue_values = df_standard_cpue['CPUE_Standar_Total'].values
        production_values = df_production['Jumlah'].values
        
        results_dict = bandingkan_model_msy(effort_values, cpue_values, production_values, st.session_state.selected_models)
        
        st.write("📊 Menganalisis status stok dan rekomendasi...")
        
        status.update(label="✅ Analisis selesai!", state="complete", expanded=False)
    
    st.session_state.analysis_results = {
        'df_production': df_production,
        'df_effort': df_effort,
        'df_cpue': df_cpue,
        'df_fpi': df_fpi,
        'df_standard_effort': df_standard_effort,
        'df_standard_cpue': df_standard_cpue,  # DIPERBAIKI
        'msy_results': results_dict
    }
    
    successful_models = {k: v for k, v in results_dict.items() if v and v['success']}
    
    if successful_models:
        st.success(f"Analisis berhasil! {len(successful_models)} model valid.")
        
        best_model_name = max(successful_models.items(), key=lambda x: x[1]['r_squared'])[0]
        best_model = successful_models[best_model_name]
        
        st.markdown("---")
        st.header("📊 HASIL ANALISIS CPUE DAN MSY")
        st.info(f"*Model terbaik*: {best_model_name} (R² = {best_model['r_squared']:.3f})")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("MSY/JTB", f"{best_model['C_MSY']:,.1f} kg")
        with col2:
            st.metric("F_MSY", f"{best_model['F_MSY']:,.1f} trip")
        with col3:
            st.metric("U_MSY", f"{best_model['U_MSY']:.3f} kg/trip")
        with col4:
            st.metric("R²", f"{best_model['r_squared']:.3f}")
        
        # Tampilkan tabel-tabel hasil - DIPERBAIKI DENGAN TAB CPUE STANDAR
        st.header("📋 HASIL PERHITUNGAN")
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🍤 Produksi", "🎣 Upaya", "📊 CPUE", "🎯 FPI", "⚖ Upaya Standar", "📈 CPUE Standar"])
        
        with tab1:
            st.dataframe(df_production.style.format({col: "{:,.1f}" for col in df_production.columns if col != 'Tahun'}), use_container_width=True)
        
        with tab2:
            st.dataframe(df_effort.style.format({col: "{:,}" for col in df_effort.columns if col != 'Tahun'}), use_container_width=True)
        
        with tab3:
            st.dataframe(df_cpue.style.format({col: "{:.3f}" for col in df_cpue.columns if col != 'Tahun'}), use_container_width=True)
        
        with tab4:
            st.dataframe(df_fpi.style.format({col: "{:.3f}" for col in df_fpi.columns if col != 'Tahun'}), use_container_width=True)
        
        with tab5:
            st.dataframe(df_standard_effort.style.format({col: "{:,.1f}" for col in df_standard_effort.columns if col != 'Tahun'}), use_container_width=True)
        
        # TAB BARU: CPUE STANDAR - DIPERBAIKI
        with tab6:
            st.markdown("**CPUE Standar per Alat Tangkap (kg/trip setelah standardisasi)**")
            
            # Format kolom untuk tampilan yang lebih baik
            format_dict = {}
            for col in df_standard_cpue.columns:
                if col == 'Tahun':
                    format_dict[col] = "{:.0f}"
                elif '_Std_CPUE' in col or col == 'CPUE_Standar_Total':
                    format_dict[col] = "{:.4f}"
                elif col == 'Ln_CPUE':
                    format_dict[col] = "{:.6f}"
            
            st.dataframe(
                df_standard_cpue.style.format(format_dict), 
                use_container_width=True,
                height=400
            )
            
            # Tambahkan penjelasan
            st.markdown("""
            **Keterangan:**
            - `[AlatTangkap]_Std_CPUE`: CPUE standar per alat tangkap (setelah dikalikan dengan FPI)
            - `CPUE_Standar_Total`: CPUE total setelah standardisasi
            - `Ln_CPUE`: Logaritma natural dari CPUE standar total (untuk analisis regresi)
            
            **Cara membaca:** CPUE standar adalah CPUE yang telah distandardisasi dengan FPI, 
            sehingga nilai CPUE dari berbagai alat tangkap dapat dibandingkan secara langsung.
            """)
        
        # Analisis Status Stok dan Rekomendasi
        st.markdown("---")
        years = df_production['Tahun'].tolist()
        recommendations = analisis_status_stok(results_dict, production_values, effort_values, years)
        
        if recommendations:
            render_rekomendasi(recommendations, production_inputs, years)
            # Simpan rekomendasi ke session state untuk ekspor
            st.session_state.analysis_results['recommendations'] = recommendations
        
        # Visualisasi
        st.header("📈 VISUALISASI HASIL")
        
        # Panggil fungsi grafik MSY yang baru
        render_grafik_msy_lengkap(effort_values, cpue_values, production_values, results_dict)
        
        # Visualisasi sederhana lainnya
        buat_visualisasi_sederhana(df_production, df_effort, df_cpue, df_fpi, df_standard_effort, df_standard_cpue, results_dict, gears, display_names)
        
    else:
        st.error("Analisis MSY gagal pada semua model. Periksa data input.")
        
        for model_name, results in results_dict.items():
            if results and 'error' in results:
                st.error(f"{model_name}: {results['error']}")

# =====================================================
# FUNGSI EKSPOR PDF BARU - LENGKAP DENGAN SEMUA HASIL
# =====================================================
def save_matplotlib_fig_to_buffer(fig):
    """Simpan gambar matplotlib ke buffer"""
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    return buf

def create_data_table_for_pdf(dataframe, title):
    """Buat tabel untuk PDF dari dataframe"""
    # Konversi dataframe ke list of lists untuk tabel
    data = [dataframe.columns.tolist()]
    for _, row in dataframe.iterrows():
        data.append(row.tolist())
    
    # Buat tabel dengan styling
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    return table

def create_pdf_with_all_results():
    """Buat PDF lengkap dengan semua hasil analisis"""
    if st.session_state.analysis_results is None:
        st.error("❌ Tidak ada hasil analisis untuk diekspor ke PDF.")
        return None
    
    try:
        results = st.session_state.analysis_results
        config = st.session_state.gear_config
        
        # Buat file PDF sementara
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_path = tmp_file.name
        
        # Buat dokumen PDF
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Judul Utama
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1E3A8A'),
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        story.append(Paragraph("LAPORAN ANALISIS POTENSI LESTARI IKAN KURISI", title_style))
        
        # Subjudul
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#3B82F6'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        story.append(Paragraph(f"Pelabuhan Perikanan Nusantara (PPN) Karangantu, Banten", subtitle_style))
        story.append(Paragraph(f"Tanggal: {pd.Timestamp.now().strftime('%d %B %Y %H:%M')}", subtitle_style))
        story.append(Spacer(1, 20))
        
        # 1. INFORMASI ANALISIS
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#0F766E'),
            spaceAfter=10,
            spaceBefore=20
        )
        
        story.append(Paragraph("1. INFORMASI ANALISIS", section_style))
        
        info_data = [
            ["Parameter", "Nilai"],
            ["Jumlah Tahun Data", str(len(results['df_production']))],
            ["Rentang Tahun", f"{results['df_production']['Tahun'].min()} - {results['df_production']['Tahun'].max()}"],
            ["Jumlah Alat Tangkap", str(len(config['gears']))],
            ["Alat Tangkap Standar", config['standard_gear']],
            ["Model yang Dianalisis", ", ".join(st.session_state.selected_models)]
        ]
        
        info_table = Table(info_data)
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#10B981')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('BACKGROUND', (0, 1), (1, -1), colors.HexColor('#F0F9FF')),
            ('GRID', (0, 0), (1, -1), 1, colors.HexColor('#CBD5E1')),
            ('FONTSIZE', (0, 1), (1, -1), 9),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 30))
        
        # 2. DATA PRODUKSI
        story.append(Paragraph("2. DATA PRODUKSI (kg)", section_style))
        story.append(create_data_table_for_pdf(results['df_production'], "Produksi"))
        story.append(Spacer(1, 20))
        
        # 3. DATA UPAYA
        story.append(Paragraph("3. DATA UPAYA (trip)", section_style))
        story.append(create_data_table_for_pdf(results['df_effort'], "Upaya"))
        story.append(Spacer(1, 20))
        
        # 4. HASIL CPUE
        story.append(Paragraph("4. HASIL PERHITUNGAN CPUE (kg/trip)", section_style))
        story.append(create_data_table_for_pdf(results['df_cpue'], "CPUE"))
        story.append(Spacer(1, 20))
        
        # 5. HASIL FPI
        story.append(Paragraph("5. HASIL FISHING POWER INDEX (FPI)", section_style))
        story.append(create_data_table_for_pdf(results['df_fpi'], "FPI"))
        story.append(Spacer(1, 20))
        
        # 6. UPAYA STANDAR
        story.append(Paragraph("6. UPAYA STANDAR", section_style))
        story.append(create_data_table_for_pdf(results['df_standard_effort'], "Upaya Standar"))
        story.append(Spacer(1, 20))
        
        # 7. CPUE STANDAR - DIPERBAIKI
        story.append(Paragraph("7. CPUE STANDAR (kg/trip setelah standardisasi)", section_style))
        story.append(create_data_table_for_pdf(results['df_standard_cpue'], "CPUE Standar"))
        story.append(Spacer(1, 20))
        
        # 8. HASIL ANALISIS MSY
        story.append(PageBreak())
        story.append(Paragraph("8. HASIL ANALISIS MSY (JTB)", section_style))
        
        successful_models = {k: v for k, v in results['msy_results'].items() if v and v['success']}
        
        if successful_models:
            # Tabel perbandingan model
            msy_data = [["Model", "MSY/JTB (kg)", "F_MSY", "U_MSY", "R²", "Status"]]
            
            for model_name, model_results in successful_models.items():
                msy_data.append([
                    model_name,
                    f"{model_results['C_MSY']:,.1f}",
                    f"{model_results['F_MSY']:,.1f}",
                    f"{model_results['U_MSY']:.3f}",
                    f"{model_results['r_squared']:.3f}",
                    "VALID"
                ])
            
            msy_table = Table(msy_data)
            msy_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F766E')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F0FDF4')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#86EFAC')),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            story.append(msy_table)
            story.append(Spacer(1, 20))
            
            # Tambahkan model terbaik
            best_model_name = max(successful_models.items(), key=lambda x: x[1]['r_squared'])[0]
            best_model = successful_models[best_model_name]
            
            story.append(Paragraph(f"Model Terbaik: {best_model_name} (R² = {best_model['r_squared']:.3f})", 
                                  ParagraphStyle('Normal', fontSize=10, spaceAfter=10)))
            
            story.append(Paragraph(f"Persamaan: {best_model['equation']}", 
                                  ParagraphStyle('Normal', fontSize=9, textColor=colors.grey, spaceAfter=20)))
        
        # 9. REKOMENDASI PENGELOLAAN
        story.append(Paragraph("9. REKOMENDASI PENGELOLAAN DAN JTB", section_style))
        
        if 'recommendations' in results:
            rec = results['recommendations']
            
            # Status stok dengan warna
            status_color = colors.red if rec['status_stok'] == "OVERFISHING" else \
                          colors.orange if rec['status_stok'] == "FULLY EXPLOITED" else colors.green
            
            status_data = [
                ["Parameter", "Nilai"],
                ["Status Stok", rec['status_stok']],
                ["JTB (Jumlah Tangkapan yang Diperbolehkan)", f"{rec['jtb']:,.1f} kg"],
                ["Upaya Optimal (F_MSY)", f"{rec['f_msy']:,.1f} trip"],
                ["Produksi Terkini", f"{rec['current_production']:,.1f} kg"],
                ["Rasio Produksi/JTB", f"{rec['production_ratio']:.1f}%"],
                ["Trend Produksi", rec['trend_status']],
                ["Model Terbaik", rec['best_model']]
            ]
            
            status_table = Table(status_data)
            status_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (1, 0), status_color),
                ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
                ('ALIGN', (0, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (1, 0), 12),
                ('BACKGROUND', (0, 1), (1, -1), colors.HexColor('#FEF3C7')),
                ('GRID', (0, 0), (1, -1), 1, colors.HexColor('#FBBF24')),
                ('FONTSIZE', (0, 1), (1, -1), 9),
                ('TEXTCOLOR', (0, 1), (0, 1), status_color),
                ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
            ]))
            
            story.append(status_table)
            story.append(Spacer(1, 20))
            
            # Rekomendasi detail
            story.append(Paragraph("Rekomendasi Utama:", 
                                  ParagraphStyle('Heading3', fontSize=11, spaceAfter=5)))
            story.append(Paragraph(rec['rekomendasi'], 
                                  ParagraphStyle('Normal', fontSize=10, spaceAfter=10)))
            
            story.append(Paragraph("Aksi Khusus:", 
                                  ParagraphStyle('Heading3', fontSize=11, spaceAfter=5)))
            story.append(Paragraph(rec['aksi_khusus'], 
                                  ParagraphStyle('Normal', fontSize=10, spaceAfter=20)))
        
        # 10. GRAFIK ANALISIS
        story.append(PageBreak())
        story.append(Paragraph("10. GRAFIK ANALISIS", section_style))
        
        # Buat grafik-grafik untuk PDF
        effort_values = results['df_standard_effort']['Jumlah'].values
        cpue_values = results['df_standard_cpue']['CPUE_Standar_Total'].values
        production_values = results['df_production']['Jumlah'].values
        
        # Grafik 1: Trend Produksi
        story.append(Paragraph("Grafik Trend Produksi", 
                              ParagraphStyle('Heading3', fontSize=12, spaceAfter=10)))
        
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        years = results['df_production']['Tahun'].tolist()
        ax1.plot(years, production_values, 'bo-', linewidth=2, markersize=6, label='Produksi Aktual')
        
        if 'recommendations' in results:
            ax1.axhline(y=results['recommendations']['msy'], color='red', linestyle='--', 
                       linewidth=1.5, label='JTB (MSY)')
        
        ax1.set_xlabel('Tahun')
        ax1.set_ylabel('Produksi (kg)')
        ax1.set_title('Trend Produksi Ikan Kurisi')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        img_buffer1 = save_matplotlib_fig_to_buffer(fig1)
        story.append(Image(img_buffer1, width=6*inch, height=3*inch))
        story.append(Spacer(1, 20))
        plt.close(fig1)
        
        # Grafik 2: Perbandingan Model MSY
        story.append(Paragraph("Grafik Perbandingan Model MSY", 
                              ParagraphStyle('Heading3', fontSize=12, spaceAfter=10)))
        
        if successful_models:
            fig2, ax2 = plt.subplots(figsize=(8, 4))
            colors_list = ['red', 'blue']
            line_styles = ['-', '--']
            
            ax2.scatter(effort_values, production_values, color='black', s=50, 
                       zorder=5, label='Data Observasi')
            
            for i, (model_name, model_results) in enumerate(successful_models.items()):
                if model_results['success']:
                    x_fit = np.linspace(0.1, max(effort_values) * 1.2, 100)
                    
                    if model_name == 'Schaefer':
                        y_fit = model_results['a'] * x_fit + model_results['b'] * (x_fit ** 2)
                    elif model_name == 'Fox':
                        y_fit = model_fox(x_fit, model_results['a'], model_results['b'])
                    else:
                        continue
                        
                    ax2.plot(x_fit, y_fit, color=colors_list[i % len(colors_list)], 
                            linestyle=line_styles[i % len(line_styles)], 
                            linewidth=1.5, label=model_name)
                    
                    ax2.scatter([model_results['F_MSY']], [model_results['C_MSY']], 
                               color=colors_list[i % len(colors_list)], s=80, marker='*', zorder=6)
            
            ax2.set_xlabel('Upaya Penangkapan (F)')
            ax2.set_ylabel('Produksi (C)')
            ax2.set_title('Perbandingan Model MSY')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            img_buffer2 = save_matplotlib_fig_to_buffer(fig2)
            story.append(Image(img_buffer2, width=6*inch, height=3*inch))
            story.append(Spacer(1, 20))
            plt.close(fig2)
        
        # 11. CATATAN PENTING
        story.append(Paragraph("11. CATATAN PENTING", section_style))
        
        notes_style = ParagraphStyle(
            'Notes',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            spaceAfter=5
        )
        
        notes = [
            "1. JTB (Jumlah Tangkapan yang Diperbolehkan) adalah batas maksimal tangkapan",
            "2. Rekomendasi berdasarkan analisis ilmiah model Schaefer dan Fox",
            "3. Implementasi harus disesuaikan dengan kondisi lapangan",
            "4. Monitoring berkala diperlukan untuk evaluasi dan penyesuaian",
            "5. Partisipasi stakeholder sangat penting untuk keberhasilan",
            "6. CPUE Standar adalah CPUE yang telah distandardisasi dengan FPI",
            "7. CPUE Standar memungkinkan perbandingan langsung antar alat tangkap"
        ]
        
        for note in notes:
            story.append(Paragraph(note, notes_style))
        
        # Footer
        story.append(Spacer(1, 40))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        
        story.append(Paragraph("Dikembangkan untuk mendukung pengelolaan perikanan berkelanjutan", footer_style))
        story.append(Paragraph("© 2025 - PPN Karangantu, Banten", footer_style))
        
        # Build PDF
        doc.build(story)
        
        # Baca file PDF yang sudah dibuat
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        # Hapus file sementara
        import os
        os.unlink(pdf_path)
        
        return pdf_data
        
    except Exception as e:
        st.error(f"❌ Error membuat PDF: {str(e)}")
        return None

def render_pdf_section():
    """Render section untuk ekspor PDF"""
    if st.session_state.analysis_results is None:
        st.warning("📊 Hasil analisis belum tersedia. Silakan lakukan analisis terlebih dahulu.")
        return
    
    st.header("🖨️ Ekspor ke PDF Lengkap")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **📋 KONTEN PDF YANG AKAN DIHASILKAN:**
        
        **1. INFORMASI ANALISIS**
        - Parameter analisis dan konfigurasi
        
        **2. DATA PRODUKSI (kg)**
        - Tabel lengkap data produksi per alat tangkap
        
        **3. DATA UPAYA (trip)**
        - Tabel lengkap data upaya penangkapan
        
        **4. HASIL CPUE (kg/trip)**
        - Tabel hasil perhitungan CPUE
        
        **5. HASIL FPI (Fishing Power Index)**
        - Tabel standardisasi alat tangkap
        
        **6. UPAYA STANDAR**
        - Tabel upaya standar hasil konversi
        
        **7. CPUE STANDAR (DIPERBAIKI)**
        - **Tabel CPUE standar per alat tangkap**
        - CPUE yang telah distandardisasi dengan FPI
        
        **8. HASIL ANALISIS MSY (JTB)**
        - Perbandingan model Schaefer vs Fox
        - Nilai MSY/JTB, F_MSY, U_MSY
        - Model terbaik dan persamaan
        
        **9. REKOMENDASI PENGELOLAAN**
        - Status stok (Underfishing/Fully/Overfishing)
        - JTB (Jumlah Tangkapan yang Diperbolehkan)
        - Rekomendasi utama dan aksi khusus
        
        **10. GRAFIK ANALISIS**
        - Grafik trend produksi
        - Grafik perbandingan model MSY
        
        **11. CATATAN PENTING**
        - Panduan implementasi
        
        **📄 FORMAT:** PDF standar, siap cetak dan dibagikan
        """)
    
    with col2:
        # Tombol untuk membuat PDF
        if st.button("📥 Buat dan Download PDF Lengkap", 
                    use_container_width=True, 
                    type="primary",
                    help="Klik untuk membuat PDF dengan semua hasil analisis"):
            
            with st.spinner("🔄 Membuat PDF lengkap..."):
                pdf_data = create_pdf_with_all_results()
                
                if pdf_data is not None:
                    # Encode PDF untuk download
                    b64 = base64.b64encode(pdf_data).decode()
                    href = f'<a href="data:application/pdf;base64,{b64}" download="Laporan_Analisis_IKAN_KURISI_{pd.Timestamp.now().strftime("%Y%m%d_%H%M")}.pdf">Download PDF</a>'
                    
                    st.success("✅ PDF berhasil dibuat!")
                    st.markdown(href, unsafe_allow_html=True)
                    
                    # Tampilkan preview kecil
                    st.info("📄 **Preview PDF:** File berisi 3-5 halaman dengan semua hasil analisis")
                else:
                    st.error("❌ Gagal membuat PDF")

# ==============================================
# APLIKASI UTAMA
# ==============================================
def main():
    """Aplikasi utama dengan model Schaefer dan Fox serta rekomendasi"""
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render input data (manual dan upload)
    production_inputs, effort_inputs = render_data_input()
    
    # Tombol analisis
    if st.button("🚀 LAKUKAN ANALISIS CPUE, MSY (JTB), DAN REKOMENDASI", type="primary", use_container_width=True, key="analyze_button"):
        if st.session_state.data_tables['production'] and st.session_state.data_tables['effort']:
            if not st.session_state.selected_models:
                st.error("Pilih minimal satu model MSY untuk dianalisis.")
            else:
                proses_analisis_utama(production_inputs, effort_inputs)
        else:
            st.error("Silakan isi data terlebih dahulu.")
    
    # TAMPILKAN SECTION PDF JIKA ADA HASIL ANALISIS
    if st.session_state.analysis_results is not None:
        st.markdown("---")
        # RENDER BAGIAN PDF LENGKAP
        render_pdf_section()
        st.markdown("---")
        render_ekspor_section()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    **📚 WEBSITE PENDUGAAN POTENSI LESTARI IKAN KURISI DENGAN REKOMENDASI JTB**
    
    **🔬 METODE ANALISIS:**
    - Perhitungan CPUE (Catch Per Unit Effort)
    - Standardisasi upaya dengan FPI (Fishing Power Index)
    - **Perhitungan CPUE Standar per alat tangkap** ← DIPERBAIKI
    - Pendugaan MSY/JTB dengan model Schaefer dan Fox
    - **Analisis status stok dan rekomendasi pengelolaan**
    
    **🎯 TUJUAN:**
    - **Menentukan JTB (Jumlah Tangkapan yang Diperbolehkan)**
    - Mendukung implementasi kebijakan penangkapan terukur (PP No. 11/2023)
    - Menyediakan rekomendasi pengelolaan berbasis data ilmiah
    - Membantu pengambilan keputusan untuk keberlanjutan perikanan
    
    **📊 DATA DEFAULT:** Data produksi ikan kurisi PPN Karangantu tahun 2018-2024
    
    **⚠️ PERHATIAN:** JTB merupakan batas maksimal tangkapan untuk menjaga keberlanjutan stok
    
    **✨ FITUR BARU:** CPUE Standar per alat tangkap untuk analisis yang lebih akurat
    
    Dikembangkan untuk mendukung pengelolaan perikanan berkelanjutan | © 2025
    """)

# ==============================================
# JALANKAN APLIKASI
# ==============================================
if __name__ == "__main__":
    main()


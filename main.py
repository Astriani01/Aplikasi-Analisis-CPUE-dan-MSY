import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from scipy import stats
from scipy.optimize import curve_fit
import warnings
from matplotlib.ticker import FuncFormatter

warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Analisis CPUE & MSY - Multi Model", 
    layout="wide",
    page_icon="🐟"
)

st.title("🐟 Analisis CPUE dan MSY dengan Multi-Model")

# ==============================================
# INISIALISASI SESSION STATE
# ==============================================
def initialize_session_state():
    """Inisialisasi session state untuk konfigurasi dan data"""
    if 'gear_config' not in st.session_state:
        st.session_state.gear_config = {
            'gears': ['Jaring_Insang_Tetap', 'Jaring_Hela_Dasar', 'Bagan_Berperahu', 'Pancing'],
            'display_names': ['Jaring Insang Tetap', 'Jaring Hela Dasar', 'Bagan Berperahu', 'Pancing'],
            'standard_gear': 'Jaring_Hela_Dasar',
            'years': [2018, 2019, 2020, 2021, 2022, 2023],
            'num_years': 6
        }

    if 'data_tables' not in st.session_state:
        st.session_state.data_tables = {
            'production': [
                {'Tahun': 2018, 'Jaring_Insang_Tetap': 1004, 'Jaring_Hela_Dasar': 6105, 'Bagan_Berperahu': 628, 'Pancing': 811, 'Jumlah': 8548},
                {'Tahun': 2019, 'Jaring_Insang_Tetap': 2189, 'Jaring_Hela_Dasar': 10145, 'Bagan_Berperahu': 77, 'Pancing': 396, 'Jumlah': 12807},
                {'Tahun': 2020, 'Jaring_Insang_Tetap': 122, 'Jaring_Hela_Dasar': 9338, 'Bagan_Berperahu': 187, 'Pancing': 311, 'Jumlah': 9958},
                {'Tahun': 2021, 'Jaring_Insang_Tetap': 8, 'Jaring_Hela_Dasar': 10439, 'Bagan_Berperahu': 377, 'Pancing': 418, 'Jumlah': 11242},
                {'Tahun': 2022, 'Jaring_Insang_Tetap': 23, 'Jaring_Hela_Dasar': 10880, 'Bagan_Berperahu': 189, 'Pancing': 21, 'Jumlah': 11113},
                {'Tahun': 2023, 'Jaring_Insang_Tetap': 67, 'Jaring_Hela_Dasar': 13174, 'Bagan_Berperahu': 33, 'Pancing': 13, 'Jumlah': 13287}
            ],
            'effort': [
                {'Tahun': 2018, 'Jaring_Insang_Tetap': 2230, 'Jaring_Hela_Dasar': 5998, 'Bagan_Berperahu': 2434, 'Pancing': 246, 'Jumlah': 10908},
                {'Tahun': 2019, 'Jaring_Insang_Tetap': 26878, 'Jaring_Hela_Dasar': 10731, 'Bagan_Berperahu': 1385, 'Pancing': 139, 'Jumlah': 39583},
                {'Tahun': 2020, 'Jaring_Insang_Tetap': 10122, 'Jaring_Hela_Dasar': 7076, 'Bagan_Berperahu': 1915, 'Pancing': 191, 'Jumlah': 19304},
                {'Tahun': 2021, 'Jaring_Insang_Tetap': 11010, 'Jaring_Hela_Dasar': 7315, 'Bagan_Berperahu': 1445, 'Pancing': 162, 'Jumlah': 19932},
                {'Tahun': 2022, 'Jaring_Insang_Tetap': 18796, 'Jaring_Hela_Dasar': 10183, 'Bagan_Berperahu': 1151, 'Pancing': 77, 'Jumlah': 30207},
                {'Tahun': 2023, 'Jaring_Insang_Tetap': 15899, 'Jaring_Hela_Dasar': 8205, 'Bagan_Berperahu': 777, 'Pancing': 78, 'Jumlah': 24959}
            ]
        }
    
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    
    if 'selected_models' not in st.session_state:
        st.session_state.selected_models = ['Schaefer', 'Fox']
    
    if 'uploaded_data' not in st.session_state:
        st.session_state.uploaded_data = None

# ==============================================
# FUNGSI TEMPLATE EXCEL
# ==============================================
def create_excel_template():
    """Buat template Excel untuk diunduh"""
    
    # Data contoh untuk template
    production_data = {
        'Tahun': [2018, 2019, 2020, 2021, 2022, 2023],
        'Jaring_Insang_Tetap': [1004, 2189, 122, 8, 23, 67],
        'Jaring_Hela_Dasar': [6105, 10145, 9338, 10438, 10879, 13174],
        'Bagan_Berperahu': [628, 77, 187, 377, 189, 33],
        'Pancing': [811, 396, 311, 418, 21, 13],
        'Jumlah': [8548, 12807, 9958, 11242, 11113, 13287]
    }
    
    effort_data = {
        'Tahun': [2018, 2019, 2020, 2021, 2022, 2023],
        'Jaring_Insang_Tetap': [2230, 26878, 10122, 11010, 18796, 15899],
        'Jaring_Hela_Dasar': [5998, 10731, 7076, 7315, 10183, 8205],
        'Bagan_Berperahu': [2434, 1385, 1915, 1445, 1151, 777],
        'Pancing': [246, 139, 191, 162, 77, 78],
        'Jumlah': [10908, 39583, 19304, 19932, 30207, 24959]
    }
    
    # Buat DataFrame
    df_production = pd.DataFrame(production_data)
    df_effort = pd.DataFrame(effort_data)
    
    # Buat file Excel dalam memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_production.to_excel(writer, sheet_name='Produksi', index=False)
        df_effort.to_excel(writer, sheet_name='Upaya', index=False)
        
        # Formatting
        workbook = writer.book
        
        # Format untuk sheet Produksi
        format_production = workbook.add_format({'num_format': '#,##0'})
        worksheet_production = writer.sheets['Produksi']
        for col_num, value in enumerate(df_production.columns.values):
            worksheet_production.set_column(col_num, col_num, 15, format_production)
        
        # Format untuk sheet Upaya
        format_effort = workbook.add_format({'num_format': '#,##0'})
        worksheet_effort = writer.sheets['Upaya']
        for col_num, value in enumerate(df_effort.columns.values):
            worksheet_effort.set_column(col_num, col_num, 15, format_effort)
    
    processed_data = output.getvalue()
    return processed_data

def render_template_section():
    """Render section untuk download template"""
    st.header("📋 Template Data Excel")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        *📝 Struktur Template Excel:*
        
        *Sheet 'Produksi' (dalam Ton):*
        - Kolom A: Tahun
        - Kolom B-E: Nama alat tangkap (contoh: Jaring_Insang_Tetap, Jaring_Hela_Dasar, dll.)
        - Kolom F: Jumlah (total)
        
        *Sheet 'Upaya' (dalam Trip):*
        - Kolom A: Tahun
        - Kolom B-E: Nama alat tangkap (harus sama dengan sheet Produksi)
        - Kolom F: Jumlah (total)
        
        *💡 Tips:*
        - Nama alat tangkap harus sama di kedua sheet
        - Tahun harus sama dan berurutan
        - Data harus numerik (tanpa teks atau karakter khusus)
        """)
    
    with col2:
        # Download template
        template_data = create_excel_template()
        st.download_button(
            label="📥 Download Template Excel",
            data=template_data,
            file_name="Template_Data_Perikanan.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        st.markdown("""
        *🔧 Cara Penggunaan:*
        1. Download template
        2. Isi dengan data Anda
        3. Upload file yang sudah diisi
        4. Klik 'Gunakan Data yang Diupload'
        """)

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
    ax.annotate(f'MSY\nF={msy_x:.1f}\nC={msy_y:.1f} ton', 
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
    ax.annotate(f'MSY\nF={msy_x:.1f}\nC={msy_y:.1f} ton', 
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
                'C_MSY (ton)': f"{results['C_MSY']:,.1f}",
                'F_MSY': f"{results['F_MSY']:,.1f}",
                'U_MSY': f"{results['U_MSY']:.3f}",
                'R²': f"{results['r_squared']:.3f}",
                'Persamaan': results['equation']
            })
        
        st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)

# ==============================================
# FUNGSI EKSPOR HASIL ANALISIS
# ==============================================
def ekspor_hasil_analisis():
    """Ekspor hasil analisis ke file Excel"""
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
            results['df_cpue'].to_excel(writer, sheet_name='CPUE', index=False)
            results['df_fpi'].to_excel(writer, sheet_name='FPI', index=False)
            results['df_standard_effort'].to_excel(writer, sheet_name='Upaya Standar', index=False)
            results['df_standard_cpue'].to_excel(writer, sheet_name='CPUE Standar', index=False)
            
            # Sheet Hasil MSY
            msy_data = []
            for model_name, model_results in results['msy_results'].items():
                if model_results and model_results['success']:
                    msy_data.append({
                        'Model': model_name,
                        'C_MSY (ton)': model_results['C_MSY'],
                        'F_MSY': model_results['F_MSY'],
                        'U_MSY': model_results['U_MSY'],
                        'R²': model_results['r_squared'],
                        'Persamaan': model_results['equation'],
                        'Status': 'Valid'
                    })
                else:
                    msy_data.append({
                        'Model': model_name,
                        'C_MSY (ton)': '-',
                        'F_MSY': '-',
                        'U_MSY': '-',
                        'R²': '-',
                        'Persamaan': '-',
                        'Status': model_results.get('error', 'Gagal') if model_results else 'Tidak ada hasil'
                    })
            
            df_msy = pd.DataFrame(msy_data)
            df_msy.to_excel(writer, sheet_name='Hasil MSY', index=False)
            
            # Sheet Ringkasan
            workbook = writer.book
            worksheet_summary = workbook.add_worksheet('Ringkasan Analisis')
            
            # Formatting
            format_header = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC'})
            format_value = workbook.add_format({'num_format': '#,##0.00'})
            
            # Tulis ringkasan
            worksheet_summary.write('A1', 'RINGKASAN HASIL ANALISIS CPUE & MSY', format_header)
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
                    ('Maximum Sustainable Yield (MSY)', f"{best_model_results['C_MSY']:,.1f} ton"),
                    ('Optimum Fishing Effort (F_MSY)', f"{best_model_results['F_MSY']:,.1f}"),
                    ('CPUE Optimum (U_MSY)', f"{best_model_results['U_MSY']:.3f}"),
                    ('Koefisien Determinasi (R²)', f"{best_model_results['r_squared']:.3f}"),
                    ('Jumlah Tahun Data', len(results['df_production'])),
                    ('Jumlah Alat Tangkap', len(st.session_state.gear_config['gears'])),
                    ('Alat Tangkap Standar', st.session_state.gear_config['standard_gear']),
                    ('Rentang Tahun', f"{results['df_production']['Tahun'].min()} - {results['df_production']['Tahun'].max()}")
                ]
                
                for i, (param, value) in enumerate(summary_data, start=4):
                    worksheet_summary.write(f'A{i}', param)
                    worksheet_summary.write(f'B{i}', value)
            
            worksheet_summary.set_column('A:A', 25)
            worksheet_summary.set_column('B:B', 20)
        
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
        *Sheet 'CPUE'*: Hasil perhitungan CPUE
        *Sheet 'FPI'*: Hasil perhitungan Fishing Power Index
        *Sheet 'Upaya Standar'*: Hasil standardisasi upaya
        *Sheet 'CPUE Standar'*: Hasil CPUE standar
        *Sheet 'Hasil MSY'*: Perbandingan model Schaefer vs Fox
        *Sheet 'Ringkasan Analisis'*: Ringkasan lengkap hasil analisis
        
        *💡 Informasi:*
        - File berisi semua data dan hasil analisis
        - Format Excel (.xlsx) yang mudah dibaca
        - Dapat digunakan untuk laporan lebih lanjut
        """)
    
    with col2:
        # Ekspor hasil analisis
        export_data = ekspor_hasil_analisis()
        if export_data is not None:
            st.download_button(
                label="📥 Download Hasil Analisis",
                data=export_data,
                file_name=f"Hasil_Analisis_CPUE_MSY_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
            )
        
        st.markdown("""
        *🔧 Cara Penggunaan:*
        1. Lakukan analisis terlebih dahulu
        2. Klik tombol download di samping
        3. File Excel akan berisi semua hasil
        4. Gunakan untuk dokumentasi dan laporan
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
            {'Tahun': 2023, 'Jaring_Insang_Tetap': 67, 'Jaring_Hela_Dasar': 13174, 'Bagan_Berperahu': 33, 'Pancing': 13, 'Jumlah': 13287}
        ],
        'effort': [
            {'Tahun': 2018, 'Jaring_Insang_Tetap': 2230, 'Jaring_Hela_Dasar': 5998, 'Bagan_Berperahu': 2434, 'Pancing': 246, 'Jumlah': 10908},
            {'Tahun': 2019, 'Jaring_Insang_Tetap': 26878, 'Jaring_Hela_Dasar': 10731, 'Bagan_Berperahu': 1385, 'Pancing': 139, 'Jumlah': 39583},
            {'Tahun': 2020, 'Jaring_Insang_Tetap': 10122, 'Jaring_Hela_Dasar': 7076, 'Bagan_Berperahu': 1915, 'Pancing': 191, 'Jumlah': 19304},
            {'Tahun': 2021, 'Jaring_Insang_Tetap': 11010, 'Jaring_Hela_Dasar': 7315, 'Bagan_Berperahu': 1445, 'Pancing': 162, 'Jumlah': 19932},
            {'Tahun': 2022, 'Jaring_Insang_Tetap': 18796, 'Jaring_Hela_Dasar': 10183, 'Bagan_Berperahu': 1151, 'Pancing': 77, 'Jumlah': 30207},
            {'Tahun': 2023, 'Jaring_Insang_Tetap': 15899, 'Jaring_Hela_Dasar': 8205, 'Bagan_Berperahu': 777, 'Pancing': 78, 'Jumlah': 24959}
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
    st.sidebar.header("⚙ Konfigurasi Analisis")
    
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
    *📝 Panduan Upload:*
    - *Excel*: Sheet 1 = Produksi, Sheet 2 = Upaya
    - *CSV*: File tunggal dengan data produksi
    - *Kolom*: Tahun, [alat_tangkap1], [alat_tangkap2], ...
    - *Template*: Download template untuk format yang benar
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
    st.subheader("🍤 Data Produksi (Ton)")
    
    headers = ["Tahun"] + display_names + ["Jumlah"]
    prod_cols = st.columns(len(headers))
    
    for i, header in enumerate(headers):
        with prod_cols[i]:
            st.markdown(f"{header}")
    
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
            st.markdown(f"{total_prod:,.1f}")
            row_data['Jumlah'] = total_prod
        
        production_inputs.append(row_data)
    
    # Input Data Upaya
    st.subheader("🎣 Data Upaya (Trip)")
    
    effort_cols = st.columns(len(headers))
    for i, header in enumerate(headers):
        with effort_cols[i]:
            st.markdown(f"{header}")
    
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
            st.markdown(f"{total_eff:,}")
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
# FUNGSI PERHITUNGAN CPUE, FPI, dll.
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
    """Hitung CPUE standar"""
    standard_cpue_data = []
    years = produksi_df['Tahun'].values
    
    for year in years:
        clean_year = int(year) if isinstance(year, float) and year.is_integer() else year
        year_data = {'Tahun': clean_year}
        total_production = produksi_df[produksi_df['Tahun'] == year]['Jumlah'].values[0]
        total_standard_effort = standard_effort_df[standard_effort_df['Tahun'] == year]['Jumlah'].values[0]
        
        cpue_standar_total = total_production / total_standard_effort if total_standard_effort > 0 else 0
        year_data['CPUE_Standar_Total'] = cpue_standar_total
        year_data['Ln_CPUE'] = np.log(cpue_standar_total) if cpue_standar_total > 0 else 0
        
        standard_cpue_data.append(year_data)
    
    return pd.DataFrame(standard_cpue_data)

# ==============================================
# PROSES ANALISIS UTAMA
# ==============================================
def proses_analisis_utama(production_inputs, effort_inputs):
    """Proses analisis utama dengan multi-model MSY"""
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
        
        st.write("📊 Menghitung CPUE standar...")
        df_standard_cpue = hitung_cpue_standar(df_production, df_standard_effort, gears)
        
        st.write("🧮 Analisis MSY Multi-Model...")
        effort_values = df_standard_effort['Jumlah'].values
        cpue_values = df_standard_cpue['CPUE_Standar_Total'].values
        production_values = df_production['Jumlah'].values
        
        results_dict = bandingkan_model_msy(effort_values, cpue_values, production_values, st.session_state.selected_models)
        
        st.write("🎨 Membuat visualisasi...")
        
        status.update(label="✅ Analisis selesai!", state="complete", expanded=False)
    
    st.session_state.analysis_results = {
        'df_production': df_production,
        'df_effort': df_effort,
        'df_cpue': df_cpue,
        'df_fpi': df_fpi,
        'df_standard_effort': df_standard_effort,
        'df_standard_cpue': df_standard_cpue,
        'msy_results': results_dict
    }
    
    successful_models = {k: v for k, v in results_dict.items() if v and v['success']}
    
    if successful_models:
        st.success(f"Analisis berhasil! {len(successful_models)} model valid.")
        
        best_model_name = max(successful_models.items(), key=lambda x: x[1]['r_squared'])[0]
        best_model = successful_models[best_model_name]
        
        st.markdown("---")
        st.header("📊 Hasil Analisis CPUE dan MSY")
        st.info(f"*Model terbaik*: {best_model_name} (R² = {best_model['r_squared']:.3f})")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Maximum Sustainable Yield (MSY)", f"{best_model['C_MSY']:,.1f} ton")
        with col2:
            st.metric("Optimum Fishing Effort (F_MSY)", f"{best_model['F_MSY']:,.1f}")
        with col3:
            st.metric("CPUE Optimum (U_MSY)", f"{best_model['U_MSY']:.3f}")
        with col4:
            st.metric("Koefisien Determinasi (R²)", f"{best_model['r_squared']:.3f}")
        
        # Tampilkan tabel-tabel hasil
        st.header("📋 Hasil Perhitungan")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🍤 Produksi", "🎣 Upaya", "📊 CPUE", "🎯 FPI", "⚖ Upaya Standar"])
        
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
        
        # Visualisasi
        st.header("📈 Visualisasi Hasil")
        
        # Panggil fungsi grafik MSY yang baru
        render_grafik_msy_lengkap(effort_values, cpue_values, production_values, results_dict)
        
        # Visualisasi sederhana lainnya
        buat_visualisasi_sederhana(df_production, df_effort, df_cpue, df_fpi, df_standard_effort, df_standard_cpue, results_dict, gears, display_names)
        
    else:
        st.error("Analisis MSY gagal pada semua model. Periksa data input.")
        
        for model_name, results in results_dict.items():
            if results and 'error' in results:
                st.error(f"{model_name}: {results['error']}")

def buat_visualisasi_sederhana(df_production, df_effort, df_cpue, df_fpi, df_standard_effort, df_standard_cpue, results_dict, gears, display_names):
    """Buat visualisasi sederhana untuk hasil analisis"""
    
    # Tab untuk visualisasi tambahan
    tab1, tab2 = st.tabs(["📈 Trend Produksi & Upaya", "🎯 CPUE & FPI"])
    
    with tab1:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Plot produksi
        ax1.plot(df_production['Tahun'], df_production['Jumlah'], 'o-', linewidth=2, markersize=8, color='blue')
        ax1.set_title('Total Produksi per Tahun')
        ax1.set_xlabel('Tahun')
        ax1.set_ylabel('Produksi (Ton)')
        ax1.grid(True, alpha=0.3)
        
        # Plot upaya
        ax2.plot(df_effort['Tahun'], df_effort['Jumlah'], 's-', linewidth=2, markersize=8, color='red')
        ax2.set_title('Total Upaya per Tahun')
        ax2.set_xlabel('Tahun')
        ax2.set_ylabel('Upaya (Trip)')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        st.pyplot(fig)
    
    with tab2:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Plot CPUE
        for i, gear in enumerate(gears):
            ax1.plot(df_cpue['Tahun'], df_cpue[gear], 'o-', label=display_names[i], markersize=4)
        ax1.set_title('CPUE per Alat Tangkap')
        ax1.set_xlabel('Tahun')
        ax1.set_ylabel('CPUE (Ton/Trip)')
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

# ==============================================
# APLIKASI UTAMA
# ==============================================
def main():
    """Aplikasi utama dengan model Schaefer dan Fox saja"""
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render input data (manual dan upload)
    production_inputs, effort_inputs = render_data_input()
    
    # Tombol analisis
    if st.button("🚀 Lakukan Analisis CPUE dan MSY", type="primary", use_container_width=True, key="analyze_button"):
        if st.session_state.data_tables['production'] and st.session_state.data_tables['effort']:
            if not st.session_state.selected_models:
                st.error("Pilih minimal satu model MSY untuk dianalisis.")
            else:
                proses_analisis_utama(production_inputs, effort_inputs)
        else:
            st.error("Silakan isi data terlebih dahulu.")
    
    # TAMPILKAN SECTION EKSPOR JIKA ADA HASIL ANALISIS
    if st.session_state.analysis_results is not None:
        st.markdown("---")
        render_ekspor_section()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    *📚 Model MSY yang Tersedia:*
    - *Schaefer*: Model linear sederhana - CPUE vs Upaya
    - *Fox*: Model eksponensial - Produksi vs Upaya  
    
    *📈 Grafik MSY yang Dihasilkan:*
    - Grafik individual setiap model
    - Grafik produksi vs upaya
    - Perbandingan model Schaefer vs Fox
    - Titik MSY dan kurva produksi
    
    *🔍 Analisis yang Dilakukan:*
    - Perhitungan CPUE (Catch Per Unit Effort)
    - Standardisasi upaya penangkapan dengan FPI
    - Estimasi MSY dengan dua model (Schaefer & Fox)
    - Analisis tingkat pemanfaatan sumber daya
    
    *📤 Fitur Upload:*
    - Support file Excel (.xlsx, .xls) dan CSV (.csv)
    - *Template Excel* tersedia untuk diunduh
    - *Excel*: Sheet 1 = Produksi, Sheet 2 = Upaya
    - Konversi otomatis ke format aplikasi
    
    Aplikasi akan membandingkan kedua model dan merekomendasikan yang terbaik.
    
    Dikembangkan untuk Analisis Perikanan Berkelanjutan | © 2025
    """)

# PERBAIKAN: Gunakan __name__ yang benar
if __name__ == "__main__":
    main()

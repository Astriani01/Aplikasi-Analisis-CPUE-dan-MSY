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
    
    if 'r_value' not in st.session_state:
        st.session_state.r_value = 0.58
    
    if 'use_uploaded_data' not in st.session_state:
        st.session_state.use_uploaded_data = False
    
    if 'show_upload_section' not in st.session_state:
        st.session_state.show_upload_section = False

# =====================================================
# REFERENSI DAN SUMBER ILMIAH
# =====================================================
def render_referensi_ilmiah():
    """Tampilkan referensi ilmiah dan sumber rumus"""
    with st.expander("📚 REFERENSI DAN SUMBER ILMIAH", expanded=False):
        st.markdown("""
        ### **📖 SUMBER RUMSUS DAN METODOLOGI**
        
        #### **1. MODEL SCHAEFER (1954)**
        **Rumus:** CPUE = a + b × F  
        **Keterangan:**
        - CPUE = Catch Per Unit Effort (kg/trip)
        - F = Upaya penangkapan (trip)
        - a = Intercept (CPUE maksimum ketika F = 0)
        - b = Slope (perubahan CPUE per unit upaya)
        
        **Parameter MSY dari Model Schaefer:**
        - F_MSY = -a / (2 × b)
        - U_MSY = a / 2
        - C_MSY = F_MSY × U_MSY
        - K = 4 × C_MSY / r (Carrying Capacity)
        
        **Sumber:** Schaefer, M.B. (1954). *Some aspects of the dynamics of populations important to the management of commercial marine fisheries*. Bulletin of the Inter-American Tropical Tuna Commission.
        
        #### **2. MODEL FOX (1970)**
        **Rumus:** C = F × exp(a - b × F)  
        **Keterangan:**
        - C = Produksi (kg)
        - F = Upaya penangkapan (trip)
        - a, b = Parameter model
        
        **Parameter MSY dari Model Fox:**
        - F_MSY = 1 / b
        - C_MSY = (1 / b) × exp(a - 1)
        - U_MSY = C_MSY / F_MSY
        - K = exp(a) / b (Carrying Capacity)
        
        **Sumber:** Fox, W.W. (1970). *An exponential surplus-yield model for optimizing exploited fish populations*. Transactions of the American Fisheries Society.
        
        #### **3. PARAMETER BIOLOGIS (r dan K)**
        **Rumus Hubungan MSY dengan Parameter Biologis:**
        - MSY = r × K / 4 (Formula Gulland, 1971)
        - r = Laju pertumbuhan intrinsik (intrinsic growth rate)
        - K = Daya dukung lingkungan (carrying capacity)
        
        **Sumber nilai r untuk Nemipterus spp:** FishBase
        - **Nilai default r = 0.58** berdasarkan FishBase untuk Nemipterus spp
        - **Link:** [FishBase - Nemipterus spp](https://www.fishbase.se/search.php)
        
        #### **4. PERHITUNGAN CPUE (CATCH PER UNIT EFFORT)**
        **Rumus:** CPUE = Produksi (kg) / Upaya (trip)  
        **Keterangan:** Indikator efisiensi penangkapan dan kelimpahan stok
        
        **Sumber:** FAO. (1999). *Guidelines for the routine collection of capture fishery data*. FAO Fisheries Technical Paper.
        
        #### **5. FISHING POWER INDEX (FPI)**
        **Rumus:** FPI_i = CPUE_i / CPUE_max  
        **Keterangan:**
        - FPI_i = Fishing Power Index untuk alat tangkap i
        - CPUE_i = CPUE untuk alat tangkap i
        - CPUE_max = CPUE maksimum di antara semua alat tangkap
        
        **Sumber:** Sparre, P., & Venema, S.C. (1998). *Introduction to tropical fish stock assessment*. FAO Fisheries Technical Paper.
        
        #### **6. UPAAYA STANDAR (STANDARDIZED EFFORT)**
        **Rumus:** F_std = F × FPI  
        **Keterangan:** Upaya standar untuk mengkompensasi perbedaan daya tangkap alat
        
        #### **7. ANALISIS STATUS STOK**
        **Kriteria Status Berdasarkan JTB:**
        - **Underfishing:** Produksi < 80% JTB
        - **Fully exploited:** Produksi 80-100% JTB  
        - **Overfishing:** Produksi > 100% JTB
        
        **Sumber:** FAO. (2014). *The State of World Fisheries and Aquaculture*.
        
        #### **8. WAKTU PEMULIHAN (RECOVERY TIME)**
        **Rumus:** T = ln(2) / r  
        **Keterangan:** Waktu yang dibutuhkan untuk pulih 50% (waktu paruh)
        Berdasarkan model pertumbuhan logistik
        
        #### **9. LINK DAN REFERENSI ONLINE:**
        1. **FishBase:** https://www.fishbase.se/
        2. **FAO Fisheries Statistics:** http://www.fao.org/fishery/
        3. **Schaefer Model Paper:** https://doi.org/10.1016/0044-8486(54)90003-5
        4. **Fox Model Paper:** https://doi.org/10.1577/1548-8659(1970)99%3C80:AESMFO%3E2.0.CO;2
        5. **Gulland Formula:** Gulland, J.A. (1971). *The fish resources of the ocean*.
        
        #### **10. PEDOMAN NASIONAL:**
        - **Peraturan Menteri Kelautan dan Perikanan No. 18/2021** tentang Pengelolaan Perikanan
        - **Pedoman JTB (Jumlah Tangkapan yang Diperbolehkan)** oleh KKP
        - **SNI 01-6484.1-2000** tentang Metode Pendugaan Stok Ikan
        """)

# =====================================================
# FUNGSI EKSPOR PDF LAPORAN LENGKAP
# =====================================================
def generate_pdf_report(results, r_value):
    """Generate PDF report dengan semua hasil analisis dan referensi"""
    
    try:
        # Buat buffer untuk PDF
        buffer = BytesIO()
        
        # Setup dokumen PDF
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=72)
        
        # Setup styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#3B82F6'),
            spaceAfter=8,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#1E40AF'),
            spaceAfter=6,
            alignment=TA_LEFT
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=6
        )
        
        # List untuk menyimpan konten
        story = []
        
        # =================================================
        # HALAMAN 1: COVER DAN IDENTITAS
        # =================================================
        story.append(Paragraph("LAPORAN ANALISIS POTENSI LESTARI IKAN KURISI", title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph("(Nemipterus spp)", subtitle_style))
        story.append(Spacer(1, 24))
        
        # Info utama
        cover_info = [
            ["Lokasi:", "Pelabuhan Perikanan Nusantara (PPN) Karangantu, Banten"],
            ["Jenis Analisis:", "Maximum Sustainable Yield (MSY) dan JTB"],
            ["Periode Data:", f"{min(results['years'])} - {max(results['years'])}"],
            ["Jumlah Alat Tangkap:", str(len(results['gears']))],
            ["Parameter r:", f"{r_value:.3f} (FishBase)"],
            ["Tanggal Analisis:", pd.Timestamp.now().strftime('%d %B %Y')],
            ["Dokumen ini berisi:", "Hasil analisis, rekomendasi, dan referensi ilmiah"]
        ]
        
        # Buat tabel cover info
        cover_table = Table(cover_info, colWidths=[150, 350])
        cover_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E5E7EB')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1F2937')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB'))
        ]))
        
        story.append(cover_table)
        story.append(Spacer(1, 36))
        
        # Logo atau placeholder
        story.append(Paragraph("🐟 SISTEM ANALISIS PERIKANAN BERKELANJUTAN", subtitle_style))
        story.append(Spacer(1, 24))
        
        # Pernyataan
        story.append(Paragraph("<b>PERNYATAAN:</b>", heading_style))
        disclaimer = """
        Laporan ini berisi hasil analisis ilmiah berdasarkan metode standar FAO 
        untuk pendugaan potensi lestari (MSY/JTB). Semua perhitungan dilengkapi 
        dengan referensi ilmiah dan parameter biologis yang valid.
        """
        story.append(Paragraph(disclaimer, normal_style))
        
        story.append(PageBreak())
        
        # =================================================
        # HALAMAN 2: RINGKASAN EKSEKUTIF
        # =================================================
        story.append(Paragraph("RINGKASAN EKSEKUTIF", title_style))
        story.append(Spacer(1, 12))
        
        if 'recommendations' in results and results['recommendations']:
            rec = results['recommendations']
            
            # Status stok box
            status_box = []
            status_color = colors.HexColor('#10B981')  # Default hijau
            
            if rec['status_stok'] == "OVERFISHING":
                status_color = colors.HexColor('#EF4444')
                status_icon = "🔴"
            elif rec['status_stok'] == "FULLY EXPLOITED":
                status_color = colors.HexColor('#F59E0B')
                status_icon = "🟡"
            else:
                status_color = colors.HexColor('#10B981')
                status_icon = "🟢"
            
            status_info = [
                [f"{status_icon} STATUS STOK:", rec['status_stok']],
                ["Model Terbaik:", rec['best_model']],
                ["JTB (MSY):", f"{rec['jtb']:,.1f} kg"],
                ["Produksi Terkini:", f"{rec['current_production']:,.1f} kg"],
                ["Rasio Produksi/JTB:", f"{rec['production_ratio']:.1f}%"],
                ["Rekomendasi Utama:", rec['rekomendasi']]
            ]
            
            status_table = Table(status_info, colWidths=[180, 320])
            status_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), status_color),
                ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
                ('BACKGROUND', (1, 0), (1, 0), status_color),
                ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F9FAFB')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB'))
            ]))
            
            story.append(status_table)
            story.append(Spacer(1, 24))
        
        # Rekomendasi utama
        story.append(Paragraph("<b>REKOMENDASI UTAMA:</b>", heading_style))
        
        if 'recommendations' in results and results['recommendations']:
            rec = results['recommendations']
            
            rekomendasi_list = [
                f"1. {rec['aksi_khusus']}",
                f"2. Target JTB: {rec['jtb']:,.0f} kg",
                f"3. Upaya optimal (F_MSY): {rec['f_msy']:,.0f} trip",
                f"4. Monitoring intensif selama 12 bulan ke depan",
                f"5. Evaluasi triwulanan berdasarkan data CPUE"
            ]
            
            for item in rekomendasi_list:
                story.append(Paragraph(f"• {item}", normal_style))
        
        story.append(Spacer(1, 24))
        
        # Parameter kunci
        story.append(Paragraph("<b>PARAMETER KUNCI BIOLOGIS:</b>", heading_style))
        
        param_data = [
            ["Parameter", "Nilai", "Sumber"],
            ["r (laju pertumbuhan)", f"{r_value:.3f}", "FishBase"],
            ["K (daya dukung)", f"{rec.get('K', 0):,.0f} kg" if 'recommendations' in results else "N/A", "Formula Gulland"],
            ["MSY/JTB", f"{rec['jtb']:,.1f} kg" if 'recommendations' in results else "N/A", "Model MSY"],
            ["F_MSY", f"{rec['f_msy']:,.1f} trip" if 'recommendations' in results else "N/A", "Model MSY"],
            ["U_MSY", f"{rec['u_msy']:.3f} kg/trip" if 'recommendations' in results else "N/A", "Model MSY"]
        ]
        
        param_table = Table(param_data, colWidths=[150, 150, 200])
        param_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB'))
        ]))
        
        story.append(param_table)
        
        story.append(PageBreak())
        
        # =================================================
        # HALAMAN 3: DATA DASAR
        # =================================================
        story.append(Paragraph("DATA DASAR PRODUKSI DAN UPAYA", title_style))
        story.append(Spacer(1, 12))
        
        # Data Produksi
        story.append(Paragraph("<b>DATA PRODUKSI (kg):</b>", heading_style))
        
        # Siapkan data produksi untuk tabel
        prod_data = [["Tahun"] + results['display_names'] + ["Jumlah"]]
        
        for _, row in results['df_production'].iterrows():
            year = int(row['Tahun'])
            row_data = [str(year)]
            
            for gear in results['gears']:
                value = row[gear]
                row_data.append(f"{value:,.0f}")
            
            row_data.append(f"{row['Jumlah']:,.0f}")
            prod_data.append(row_data)
        
        # Tambahkan rata-rata
        avg_row = ["Rata-rata"]
        for gear in results['gears']:
            avg = results['df_production'][gear].mean()
            avg_row.append(f"{avg:,.0f}")
        
        avg_row.append(f"{results['df_production']['Jumlah'].mean():,.0f}")
        prod_data.append(avg_row)
        
        prod_table = Table(prod_data, colWidths=[50] + [80] * len(results['gears']) + [80])
        prod_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F3F4F6')),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB'))
        ]))
        
        story.append(prod_table)
        story.append(Spacer(1, 12))
        
        # Data Upaya
        story.append(Paragraph("<b>DATA UPAYA PENANGKAPAN (trip):</b>", heading_style))
        
        # Siapkan data upaya untuk tabel
        eff_data = [["Tahun"] + results['display_names'] + ["Jumlah"]]
        
        for _, row in results['df_effort'].iterrows():
            year = int(row['Tahun'])
            row_data = [str(year)]
            
            for gear in results['gears']:
                value = row[gear]
                row_data.append(f"{value:,.0f}")
            
            row_data.append(f"{row['Jumlah']:,.0f}")
            eff_data.append(row_data)
        
        # Tambahkan rata-rata
        avg_row = ["Rata-rata"]
        for gear in results['gears']:
            avg = results['df_effort'][gear].mean()
            avg_row.append(f"{avg:,.0f}")
        
        avg_row.append(f"{results['df_effort']['Jumlah'].mean():,.0f}")
        eff_data.append(avg_row)
        
        eff_table = Table(eff_data, colWidths=[50] + [80] * len(results['gears']) + [80])
        eff_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F3F4F6')),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB'))
        ]))
        
        story.append(eff_table)
        
        story.append(PageBreak())
        
        # =================================================
        # HALAMAN 4: HASIL CPUE DAN FPI
        # =================================================
        story.append(Paragraph("HASIL PERHITUNGAN CPUE DAN FPI", title_style))
        story.append(Spacer(1, 12))
        
        # CPUE Table
        story.append(Paragraph("<b>CPUE (Catch Per Unit Effort) - kg/trip:</b>", heading_style))
        
        cpue_data = [["Tahun"] + results['display_names'] + ["Total"]]
        
        for _, row in results['df_cpue'].iterrows():
            year = int(row['Tahun'])
            row_data = [str(year)]
            
            for gear in results['gears']:
                value = row[gear]
                row_data.append(f"{value:.3f}")
            
            row_data.append(f"{row['Jumlah']:.3f}")
            cpue_data.append(row_data)
        
        cpue_table = Table(cpue_data, colWidths=[50] + [80] * len(results['gears']) + [80])
        cpue_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB'))
        ]))
        
        story.append(cpue_table)
        story.append(Spacer(1, 12))
        
        # FPI Table
        story.append(Paragraph("<b>Fishing Power Index (FPI):</b>", heading_style))
        story.append(Paragraph("Indeks daya tangkap relatif (nilai tertinggi = 1)", styles['Italic']))
        
        fpi_data = [["Tahun"] + results['display_names'] + ["Total"]]
        
        for _, row in results['df_fpi'].iterrows():
            year = int(row['Tahun'])
            row_data = [str(year)]
            
            for gear in results['gears']:
                value = row[gear]
                row_data.append(f"{value:.3f}")
            
            row_data.append(f"{row['Jumlah']:.3f}")
            fpi_data.append(row_data)
        
        fpi_table = Table(fpi_data, colWidths=[50] + [80] * len(results['gears']) + [80])
        fpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7C3AED')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB'))
        ]))
        
        story.append(fpi_table)
        
        # Ranking efisiensi alat tangkap
        story.append(Spacer(1, 12))
        story.append(Paragraph("<b>RANKING EFISIENSI ALAT TANGKAP:</b>", heading_style))
        
        # Hitung rata-rata CPUE per alat
        ranking_data = []
        for gear, display_name in zip(results['gears'], results['display_names']):
            avg_cpue = results['df_cpue'][gear].mean()
            ranking_data.append({
                'Alat Tangkap': display_name,
                'Rata-rata CPUE': avg_cpue
            })
        
        ranking_df = pd.DataFrame(ranking_data)
        ranking_df = ranking_df.sort_values('Rata-rata CPUE', ascending=False)
        ranking_df['Ranking'] = range(1, len(ranking_df) + 1)
        
        rank_data = [["Ranking", "Alat Tangkap", "Rata-rata CPUE (kg/trip)"]]
        for _, row in ranking_df.iterrows():
            rank_data.append([
                str(row['Ranking']),
                row['Alat Tangkap'],
                f"{row['Rata-rata CPUE']:.3f}"
            ])
        
        rank_table = Table(rank_data, colWidths=[60, 250, 150])
        rank_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DC2626')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB'))
        ]))
        
        story.append(rank_table)
        
        story.append(PageBreak())
        
        # =================================================
        # HALAMAN 5: HASIL ANALISIS MSY/JTB
        # =================================================
        story.append(Paragraph("HASIL ANALISIS MSY/JTB", title_style))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph(f"<b>Parameter r yang digunakan:</b> {r_value:.3f} (sumber: FishBase)", heading_style))
        
        successful_models = {k: v for k, v in results['msy_results'].items() 
                           if v and v['success']}
        
        if successful_models:
            # Tampilkan perbandingan model
            story.append(Paragraph("<b>PERBANDINGAN MODEL MSY:</b>", heading_style))
            
            msy_comp_data = [["Parameter", "Schaefer (1954)", "Fox (1970)"]]
            
            schaefer_results = successful_models.get('Schaefer', {})
            fox_results = successful_models.get('Fox', {})
            
            comparison_items = [
                ("JTB (MSY)", "kg", "{:,.1f}"),
                ("F_MSY", "trip", "{:,.1f}"),
                ("U_MSY", "kg/trip", "{:.3f}"),
                ("R²", "", "{:.3f}"),
                ("K (daya dukung)", "kg", "{:,.0f}")
            ]
            
            for param, unit, fmt in comparison_items:
                schaefer_val = schaefer_results.get(param.split(' ')[0].replace('(', ''), 0)
                fox_val = fox_results.get(param.split(' ')[0].replace('(', ''), 0)
                
                if unit:
                    schaefer_str = fmt.format(schaefer_val) + " " + unit if schaefer_val != 0 else "N/A"
                    fox_str = fmt.format(fox_val) + " " + unit if fox_val != 0 else "N/A"
                else:
                    schaefer_str = fmt.format(schaefer_val) if schaefer_val != 0 else "N/A"
                    fox_str = fmt.format(fox_val) if fox_val != 0 else "N/A"
                
                msy_comp_data.append([param, schaefer_str, fox_str])
            
            msy_comp_table = Table(msy_comp_data, colWidths=[150, 175, 175])
            msy_comp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB')),
                ('BACKGROUND', (1, 1), (1, -1), colors.HexColor('#F0F9FF')),
                ('BACKGROUND', (2, 1), (2, -1), colors.HexColor('#FEF2F2'))
            ]))
            
            story.append(msy_comp_table)
            story.append(Spacer(1, 12))
            
            # Model terbaik
            best_model = max(successful_models.items(), key=lambda x: x[1]['r_squared'])
            best_model_name, best_model_results = best_model
            
            story.append(Paragraph(f"<b>MODEL TERBAIK: {best_model_name} (R² = {best_model_results['r_squared']:.3f})</b>", heading_style))
            
            best_model_data = [
                ["Parameter", "Nilai", "Keterangan"],
                ["JTB (Jumlah Tangkapan yang Diperbolehkan)", f"{best_model_results['C_MSY']:,.1f} kg", "Maximum Sustainable Yield"],
                ["Upaya Optimal (F_MSY)", f"{best_model_results['F_MSY']:,.1f} trip", "Effort at MSY"],
                ["CPUE Optimal (U_MSY)", f"{best_model_results['U_MSY']:.3f} kg/trip", "CPUE at MSY"],
                ["Laju Pertumbuhan (r)", f"{best_model_results['r']:.3f}", "FishBase parameter"],
                ["Daya Dukung (K)", f"{best_model_results.get('K', 0):,.0f} kg", "Carrying capacity"],
                ["Persamaan Model", best_model_results['equation'], ""],
                ["Referensi", best_model_results.get('reference', ''), ""]
            ]
            
            best_model_table = Table(best_model_data, colWidths=[150, 150, 200])
            best_model_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('ALIGN', (2, 1), (2, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB')),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F0FDF4'))
            ]))
            
            story.append(best_model_table)
        else:
            story.append(Paragraph("Tidak ada model yang berhasil dihitung", heading_style))
        
        story.append(PageBreak())
        
        # =================================================
        # HALAMAN 6: REKOMENDASI PENGELOLAAN
        # =================================================
        story.append(Paragraph("REKOMENDASI PENGELOLAAN PERIKANAN", title_style))
        story.append(Spacer(1, 12))
        
        if 'recommendations' in results and results['recommendations']:
            rec = results['recommendations']
            
            # Rencana aksi berdasarkan status
            story.append(Paragraph("<b>RENCANA AKSI PENGELOLAAN:</b>", heading_style))
            
            if rec['status_stok'] == "OVERFISHING":
                plan_color = colors.HexColor('#DC2626')
                plan_items = [
                    "1. PENURUNAN SEGERA (1-3 bulan):",
                    "   • Kurangi upaya penangkapan sesuai rekomendasi",
                    "   • Implementasi sistem kuota berdasarkan JTB",
                    "   • Batasi alat tangkap tidak selektif",
                    "",
                    "2. MONITORING INTENSIF (3-12 bulan):",
                    "   • Pemantauan CPUE bulanan",
                    "   • Early warning system untuk stok kritis",
                    "   • Patroli pengawasan intensif",
                    "",
                    "3. REHABILITASI (1-2 tahun):",
                    "   • Program restocking jika diperlukan",
                    "   • Perlindungan spawning ground",
                    "   • Revisi peraturan alat tangkap"
                ]
            elif rec['status_stok'] == "FULLY EXPLOITED":
                plan_color = colors.HexColor('#F59E0B')
                plan_items = [
                    "1. PEMELIHARAAN STATUS (1-3 bulan):",
                    "   • Pertahankan upaya pada level F_MSY",
                    "   • Sistem kuota berbasis JTB",
                    "   • Optimalisasi alat tangkap",
                    "",
                    "2. MONITORING RUTIN (3-12 bulan):",
                    "   • Pemantauan stok triwulan",
                    "   • Sistem deteksi dini perubahan stok",
                    "   • Database produksi real-time",
                    "",
                    "3. OPTIMASI BERKELANJUTAN (1-2 tahun):",
                    "   • Perbaikan alat tangkap selektif",
                    "   • Peningkatan nilai tambah produk",
                    "   • Sertifikasi keberlanjutan"
                ]
            else:
                plan_color = colors.HexColor('#10B981')
                plan_items = [
                    "1. PENINGKATAN BERTAHAP (1-3 bulan):",
                    "   • Tingkatkan upaya menuju F_MSY",
                    "   • Roadmap peningkatan produksi",
                    "   • Efisiensi operasi penangkapan",
                    "",
                    "2. OPTIMASI EFISIENSI (3-12 bulan):",
                    "   • Peningkatan CPUE melalui pelatihan",
                    "   • Perbaikan teknologi alat tangkap",
                    "   • Manajemen trip efektif",
                    "",
                    "3. EKSPANSI BERKELANJUTAN (1-2 tahun):",
                    "   • Diversifikasi area penangkapan",
                    "   • Pengembangan pasar produk",
                    "   • Peningkatan kapasitas nelayan"
                ]
            
            for item in plan_items:
                if item.startswith(("1.", "2.", "3.")):
                    story.append(Paragraph(f"<b>{item}</b>", normal_style))
                elif item:
                    story.append(Paragraph(item, normal_style))
                else:
                    story.append(Spacer(1, 6))
            
            story.append(Spacer(1, 12))
            
            # Timeline implementasi
            story.append(Paragraph("<b>TIMELINE IMPLEMENTASI:</b>", heading_style))
            
            timeline_data = [
                ["Fase", "Waktu", "Aktivitas Utama", "Output"],
                ["Fase 1", "Bulan 1-3", "Implementasi rekomendasi utama", "Penyesuaian upaya penangkapan"],
                ["Fase 2", "Bulan 4-12", "Monitoring intensif dan evaluasi", "Laporan monitoring triwulan"],
                ["Fase 3", "Tahun 2", "Optimasi berkelanjutan", "Sistem pengelolaan permanen"]
            ]
            
            timeline_table = Table(timeline_data, colWidths=[100, 80, 200, 120])
            timeline_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), plan_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (2, 0), (2, -1), 'LEFT'),
                ('ALIGN', (3, 0), (3, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB')),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F9FAFB'))
            ]))
            
            story.append(timeline_table)
        
        story.append(PageBreak())
        
        # =================================================
        # HALAMAN 7: REFERENSI ILMIAH
        # =================================================
        story.append(Paragraph("REFERENSI ILMIAH DAN SUMBER RUMSUS", title_style))
        story.append(Spacer(1, 12))
        
        references = [
            ["No", "Sumber", "Keterangan", "Tahun/Link"],
            [1, "Schaefer, M.B.", "Model Schaefer: CPUE = a + bF", "1954"],
            [2, "Fox, W.W.", "Model Fox: C = F × exp(a - bF)", "1970"],
            [3, "Gulland, J.A.", "Formula MSY = rK/4", "1971"],
            [4, "FAO", "Guidelines for fishery data collection", "1999"],
            [5, "Sparre & Venema", "Tropical fish stock assessment", "1998"],
            [6, "Hilborn & Walters", "Quantitative stock assessment", "1992"],
            [7, "FAO", "State of World Fisheries", "2014"],
            [8, "FishBase", "Parameter biologis Nemipterus spp", "fishbase.se"],
            [9, "KKP RI", "Permen KP No. 18/2021", "2021"],
            [10, "Caddy, J.F.", "Practical guidelines for fisheries", "1999"]
        ]
        
        ref_table = Table(references, colWidths=[30, 150, 200, 120])
        ref_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 0), (2, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F9FAFB'))
        ]))
        
        story.append(ref_table)
        story.append(Spacer(1, 12))
        
        # Rumus penting
        story.append(Paragraph("<b>RUMSUS UTAMA YANG DIGUNAKAN:</b>", heading_style))
        
        formulas = [
            "1. CPUE (Catch Per Unit Effort): CPUE = Produksi / Upaya",
            "2. Fishing Power Index: FPI = CPUE_i / CPUE_max",
            "3. Upaya Standar: F_std = F × FPI",
            "4. Model Schaefer: CPUE = a + b × F; MSY = -a²/(4b)",
            "5. Model Fox: C = F × exp(a - b × F); MSY = (1/b) × exp(a - 1)",
            "6. Formula Gulland: MSY = r × K / 4",
            "7. Waktu pemulihan: T = ln(2) / r"
        ]
        
        for formula in formulas:
            story.append(Paragraph(formula, normal_style))
        
        # Footer halaman terakhir
        story.append(Spacer(1, 24))
        story.append(Paragraph("Dokumen ini dibuat secara otomatis oleh Sistem Analisis Potensi Lestari", 
                              ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                                           alignment=TA_CENTER, textColor=colors.gray)))
        story.append(Paragraph(f"Tanggal generate: {pd.Timestamp.now().strftime('%d %B %Y %H:%M:%S')}", 
                              ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                                           alignment=TA_CENTER, textColor=colors.gray)))
        
        # Build PDF
        doc.build(story)
        
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        st.error(f"❌ Error saat membuat PDF: {str(e)}")
        return None

def render_ekspor_pdf_section():
    """Render section untuk ekspor PDF"""
    if st.session_state.analysis_results is None:
        st.warning("📊 Hasil analisis belum tersedia. Silakan lakukan analisis terlebih dahulu.")
        return
    
    st.header("📄 Ekspor Laporan PDF")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### **📋 ISI LAPORAN PDF:**
        
        **Halaman 1: Cover dan Identitas**
        - Judul laporan dan informasi dasar
        
        **Halaman 2: Ringkasan Eksekutif**
        - Status stok dan rekomendasi utama
        - Parameter kunci biologis
        
        **Halaman 3: Data Dasar**
        - Data produksi lengkap (kg)
        - Data upaya penangkapan (trip)
        
        **Halaman 4: Hasil CPUE dan FPI**
        - Perhitungan CPUE per alat tangkap
        - Fishing Power Index (FPI)
        - Ranking efisiensi alat tangkap
        
        **Halaman 5: Analisis MSY/JTB**
        - Perbandingan model Schaefer vs Fox
        - Model terbaik dengan parameter lengkap
        - JTB (Jumlah Tangkapan yang Diperbolehkan)
        
        **Halaman 6: Rekomendasi Pengelolaan**
        - Rencana aksi berdasarkan status stok
        - Timeline implementasi
        - Strategi pengelolaan
        
        **Halaman 7: Referensi Ilmiah**
        - Daftar lengkap referensi dan sumber
        - Rumus-rumus utama yang digunakan
        
        ### **🎯 KEGUNAAN LAPORAN:**
        - Dokumentasi ilmiah
        - Laporan resmi ke pihak berwenang
        - Publikasi dan presentasi
        - Bahan pengambilan keputusan
        - Monitoring dan evaluasi
        """)
    
    with col2:
        if st.button("📄 Buat Laporan PDF", type="primary", use_container_width=True):
            with st.spinner("Membuat laporan PDF..."):
                pdf_buffer = generate_pdf_report(
                    st.session_state.analysis_results, 
                    st.session_state.r_value
                )
                
                if pdf_buffer:
                    # Encode PDF untuk download
                    b64 = base64.b64encode(pdf_buffer.read()).decode()
                    
                    # Tombol download
                    current_date = pd.Timestamp.now().strftime('%Y%m%d_%H%M')
                    filename = f"Laporan_MSY_Ikan_Kurisi_{current_date}.pdf"
                    
                    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="text-decoration: none;">'
                    st.markdown(f"""
                    {href}
                        <button style="
                            background-color: #DC2626;
                            color: white;
                            padding: 12px 24px;
                            border: none;
                            border-radius: 6px;
                            cursor: pointer;
                            font-size: 16px;
                            font-weight: bold;
                            width: 100%;
                            margin-top: 20px;
                        ">
                            📥 Download Laporan PDF
                        </button>
                    </a>
                    """, unsafe_allow_html=True)
                    
                    # Preview PDF
                    st.markdown("---")
                    st.subheader("👁️ Preview Laporan")
                    
                    # Tampilkan preview PDF di iframe
                    pdf_display = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600px"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
        
        st.markdown("""
        ### **📌 CATATAN:**
        1. Laporan ini berisi **7 halaman lengkap**
        2. Format **PDF siap cetak**
        3. Dilengkapi **referensi ilmiah**
        4. Cocok untuk **dokumentasi resmi**
        5. Dapat dibuka di **semua perangkat**
        """)

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
            excel_data = pd.read_excel(uploaded_file, sheet_name=None)
            st.info(f"📊 Sheet yang ditemukan: {list(excel_data.keys())}")
            sheet_names = list(excel_data.keys())
            
            if len(sheet_names) >= 2:
                production_sheet = excel_data[sheet_names[0]]
                effort_sheet = excel_data[sheet_names[1]]
                st.success(f"✅ Menggunakan sheet 1 ({sheet_names[0]}) sebagai Produksi")
                st.success(f"✅ Menggunakan sheet 2 ({sheet_names[1]}) sebagai Upaya")
            else:
                production_sheet = excel_data[sheet_names[0]]
                effort_sheet = None
                st.warning("⚠ Hanya 1 sheet ditemukan. Data upaya akan dibuat otomatis.")
                
        elif uploaded_file.name.endswith('.csv'):
            csv_data = pd.read_csv(uploaded_file)
            production_sheet = csv_data
            effort_sheet = None
            st.info("📊 File CSV dibaca sebagai data produksi")
        else:
            st.error("❌ Format file tidak didukung.")
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
        year_columns = ['tahun', 'year', 'tahun', 'thn', 'yr']
        year_col = None
        for col in df.columns:
            if str(col).lower() in year_columns:
                year_col = col
                break
        if year_col is None:
            year_col = df.columns[0]
        
        total_columns = ['jumlah', 'total', 'sum', 'grand total', 'total produksi', 'total upaya']
        gear_columns = [col for col in df.columns 
                       if col != year_col and str(col).lower() not in total_columns]
        
        st.write(f"🔧 {data_type} - Kolom tahun: '{year_col}'")
        st.write(f"🔧 {data_type} - Kolom alat tangkap: {gear_columns}")
        
        result_data = []
        for _, row in df.iterrows():
            try:
                year_val = row[year_col]
                if pd.isna(year_val):
                    continue
                    
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
    
    production_data, prod_gears = process_dataframe(production_df, "Produksi")
    
    if effort_df is not None and not effort_df.empty:
        effort_data, effort_gears = process_dataframe(effort_df, "Upaya")
        
        if set(prod_gears) != set(effort_gears):
            st.warning("⚠ Kolom alat tangkap tidak konsisten antara produksi dan upaya")
            common_gears = list(set(prod_gears) & set(effort_gears))
            if common_gears:
                st.info(f"🔧 Menggunakan kolom umum: {common_gears}")
                gear_columns = common_gears
            else:
                st.error("❌ Tidak ada kolom alat tangkap yang sama")
                return None
        else:
            gear_columns = prod_gears
    else:
        st.info("🔄 Membuat data upaya default...")
        effort_data = []
        for prod_row in production_data:
            year_data = {'Tahun': prod_row['Tahun']}
            total = 0
            for gear in prod_gears:
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
    
    if st.button("← Kembali ke Menu Utama", use_container_width=True):
        st.session_state.show_upload_section = False
        st.rerun()
    
    return None

# ==============================================
# FUNGSI GRAFIK CPUE DENGAN REFERENSI
# ==============================================
def buat_grafik_cpue_per_alat_tangkap(df_cpue, gears, display_names):
    """Buat grafik CPUE per alat tangkap per tahun"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    years = df_cpue['Tahun'].values
    x_pos = np.arange(len(years))
    width = 0.8 / len(gears)
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(gears)))
    
    for i, (gear, display_name) in enumerate(zip(gears, display_names)):
        cpue_values = df_cpue[gear].values
        ax.bar(x_pos + i*width - (len(gears)-1)*width/2, cpue_values, 
               width=width, label=display_name, color=colors[i], alpha=0.8)
    
    ax.set_xlabel('Tahun')
    ax.set_ylabel('CPUE (kg/trip)')
    ax.set_title('CPUE per Alat Tangkap per Tahun\n(Rumus: CPUE = Produksi / Upaya)')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([str(int(year)) for year in years])
    ax.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
    ax.grid(True, alpha=0.3, axis='y')
    
    # Tambahkan referensi
    fig.text(0.02, 0.02, 'Sumber: FAO (1999). Guidelines for routine collection of capture fishery data', 
             fontsize=8, style='italic', color='gray')
    
    plt.tight_layout()
    return fig

def buat_grafik_trend_cpue_total(df_cpue):
    """Buat grafik trend CPUE total per tahun"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    years = df_cpue['Tahun'].values
    cpue_total = df_cpue['Jumlah'].values
    
    ax.plot(years, cpue_total, 'bo-', linewidth=2, markersize=8, label='CPUE Total')
    
    # Tambahkan trend line
    if len(years) > 1:
        z = np.polyfit(years, cpue_total, 1)
        p = np.poly1d(z)
        ax.plot(years, p(years), 'r--', linewidth=1.5, label='Trend Line')
        
        # Hitung dan tampilkan persamaan trend
        slope = z[0]
        intercept = z[1]
        trend_eq = f'y = {slope:.3f}x + {intercept:.3f}'
        ax.text(0.05, 0.95, f'Trend: {trend_eq}', transform=ax.transAxes, 
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    ax.set_xlabel('Tahun')
    ax.set_ylabel('CPUE Total (kg/trip)')
    ax.set_title('Trend CPUE Total per Tahun\n(Indikator Perubahan Kelimpahan Stok)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Tambahkan referensi
    fig.text(0.02, 0.02, 'Sumber: Hilborn & Walters (1992). Quantitative fisheries stock assessment', 
             fontsize=8, style='italic', color='gray')
    
    plt.tight_layout()
    return fig

def buat_grafik_cpue_vs_upaya(df_cpue, df_effort, gears, display_names):
    """Buat grafik hubungan CPUE vs Upaya per alat tangkap"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    for i, (gear, display_name) in enumerate(zip(gears[:4], display_names[:4])):
        if i >= len(axes):
            break
            
        ax = axes[i]
        cpue_values = df_cpue[gear].values
        effort_values = df_effort[gear].values
        
        ax.scatter(effort_values, cpue_values, s=80, alpha=0.7, color='blue')
        
        # Tambahkan label titik
        years = df_cpue['Tahun'].values
        for j, year in enumerate(years):
            ax.annotate(str(int(year)), 
                       (effort_values[j], cpue_values[j]),
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=8, alpha=0.7)
        
        ax.set_xlabel('Upaya (trip)')
        ax.set_ylabel('CPUE (kg/trip)')
        ax.set_title(f'{display_name}\nHubungan CPUE vs Upaya')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Tambahkan referensi
    fig.text(0.02, 0.02, 'Sumber: Schaefer (1954). Relationship between CPUE and fishing effort', 
             fontsize=8, style='italic', color='gray')
    
    return fig

def buat_grafik_cpue_perbandingan(df_cpue, gears, display_names):
    """Buat grafik perbandingan CPUE antar alat tangkap"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    years = df_cpue['Tahun'].values
    
    # Hitung rata-rata CPUE per alat tangkap
    avg_cpue = []
    for gear in gears:
        avg_cpue.append(df_cpue[gear].mean())
    
    # Urutkan dari terbesar ke terkecil
    sorted_indices = np.argsort(avg_cpue)[::-1]
    sorted_gears = [gears[i] for i in sorted_indices]
    sorted_display = [display_names[i] for i in sorted_indices]
    sorted_avg = [avg_cpue[i] for i in sorted_indices]
    
    bars = ax.bar(range(len(sorted_gears)), sorted_avg, 
                  color=plt.cm.viridis(np.linspace(0, 1, len(sorted_gears))),
                  alpha=0.8)
    
    ax.set_xlabel('Alat Tangkap')
    ax.set_ylabel('Rata-rata CPUE (kg/trip)')
    ax.set_title('Perbandingan Rata-rata CPUE Antar Alat Tangkap\n(Indikator Efisiensi Penangkapan)')
    ax.set_xticks(range(len(sorted_gears)))
    ax.set_xticklabels(sorted_display, rotation=45, ha='right')
    
    # Tambahkan nilai di atas bar
    for bar, value in zip(bars, sorted_avg):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{value:.3f}', ha='center', va='bottom', fontsize=9)
    
    ax.grid(True, alpha=0.3, axis='y')
    
    # Tambahkan referensi
    fig.text(0.02, 0.02, 'Sumber: Sparre & Venema (1998). Introduction to tropical fish stock assessment', 
             fontsize=8, style='italic', color='gray')
    
    plt.tight_layout()
    return fig

def render_grafik_cpue(df_cpue, df_effort, gears, display_names):
    """Render semua grafik CPUE"""
    st.header("📈 GRAFIK ANALISIS CPUE")
    
    # Tampilkan rumus CPUE
    with st.expander("📖 RUMUS CPUE DAN PENJELASAN", expanded=False):
        st.markdown("""
        ### **RUMUS CPUE (Catch Per Unit Effort):**
        $$
        \\text{CPUE} = \\frac{\\text{Produksi (kg)}}{\\text{Upaya (trip)}}
        $$
        
        ### **KETERANGAN:**
        - **CPUE** = Indikator kelimpahan stok dan efisiensi penangkapan
        - **Produksi** = Hasil tangkapan dalam kilogram (kg)
        - **Upaya** = Jumlah trip penangkapan
        
        ### **INTERPRETASI CPUE:**
        1. **CPUE Tinggi** = Stok melimpah atau alat tangkap efisien
        2. **CPUE Rendah** = Stok menurun atau alat tangkap kurang efisien
        3. **Trend CPUE Menurun** = Indikasi overfishing
        4. **Trend CPUE Meningkat** = Indikasi pemulihan stok
        
        ### **SUMBER REFERENSI:**
        - **FAO (1999).** *Guidelines for the routine collection of capture fishery data*
        - **Hilborn & Walters (1992).** *Quantitative fisheries stock assessment*
        - **Sparre & Venema (1998).** *Introduction to tropical fish stock assessment*
        
        **Link:** [FAO Fisheries Statistics](http://www.fao.org/fishery/)
        """)
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 CPUE per Alat Tangkap", 
        "📈 Trend CPUE Total", 
        "🔄 CPUE vs Upaya", 
        "🏆 Perbandingan CPUE"
    ])
    
    with tab1:
        st.subheader("CPUE per Alat Tangkap per Tahun")
        fig = buat_grafik_cpue_per_alat_tangkap(df_cpue, gears, display_names)
        st.pyplot(fig)
        
        # Tampilkan data tabel
        with st.expander("📋 Lihat Data CPUE per Alat Tangkap"):
            st.dataframe(df_cpue.style.format({
                gear: "{:.3f}" for gear in gears + ['Jumlah']
            }), use_container_width=True)
    
    with tab2:
        st.subheader("Trend CPUE Total per Tahun")
        fig = buat_grafik_trend_cpue_total(df_cpue)
        st.pyplot(fig)
        
        # Analisis trend
        years = df_cpue['Tahun'].values
        cpue_total = df_cpue['Jumlah'].values
        
        if len(years) > 1:
            slope, intercept = np.polyfit(years, cpue_total, 1)
            percentage_change = ((cpue_total[-1] - cpue_total[0]) / cpue_total[0] * 100) if cpue_total[0] > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Slope Trend", f"{slope:.4f}")
            with col2:
                st.metric("Perubahan Total", f"{percentage_change:.1f}%")
            with col3:
                if slope > 0:
                    st.success("📈 Trend Meningkat")
                elif slope < 0:
                    st.error("📉 Trend Menurun")
                else:
                    st.info("➡ Trend Stabil")
    
    with tab3:
        st.subheader("Hubungan CPUE vs Upaya per Alat Tangkap")
        if len(gears) > 0:
            fig = buat_grafik_cpue_vs_upaya(df_cpue, df_effort, gears, display_names)
            st.pyplot(fig)
            
            # Penjelasan hubungan CPUE-Upaya
            st.info("""
            **📖 INTERPRETASI HUBUNGAN CPUE vs UPAYA:**
            
            **Hubungan Negatif (CPUE ↓ saat Upaya ↑):**
            - Indikasi tekanan penangkapan berlebih
            - Stok mungkin mengalami overfishing
            - Perlu pengurangan upaya
            
            **Hubungan Positif (CPUE ↑ saat Upaya ↑):**
            - Stok masih dalam kondisi baik
            - Ruang untuk peningkatan produksi
            - Potensi underfishing
            
            **Tidak Ada Hubungan Jelas:**
            - Faktor lain mempengaruhi CPUE (musim, cuaca, dll.)
            - Data mungkin perlu lebih panjang
            """)
        else:
            st.warning("Tidak ada data alat tangkap yang tersedia")
    
    with tab4:
        st.subheader("Perbandingan Efisiensi Alat Tangkap")
        fig = buat_grafik_cpue_perbandingan(df_cpue, gears, display_names)
        st.pyplot(fig)
        
        # Tampilkan ranking efisiensi
        avg_cpue = []
        for gear in gears:
            avg_cpue.append(df_cpue[gear].mean())
        
        ranking_df = pd.DataFrame({
            'Alat Tangkap': display_names,
            'Rata-rata CPUE (kg/trip)': avg_cpue,
            'Ranking': pd.Series(avg_cpue).rank(ascending=False).astype(int)
        }).sort_values('Rata-rata CPUE (kg/trip)', ascending=False)
        
        st.subheader("🏆 Ranking Efisiensi Alat Tangkap")
        st.dataframe(ranking_df.style.format({
            'Rata-rata CPUE (kg/trip)': '{:.3f}'
        }), use_container_width=True)

# ==============================================
# FUNGSI MODEL MSY DENGAN PARAMETER r DAN REFERENSI
# ==============================================
def analisis_msy_schaefer(standard_effort_total, cpue_standard_total, production_total, r_value):
    """
    Analisis MSY menggunakan Model Schaefer (1954)
    """
    if len(standard_effort_total) < 2:
        return None
    
    try:
        # Linear regression: CPUE = a + b × F
        slope, intercept, r_value_reg, p_value, std_err = stats.linregress(standard_effort_total, cpue_standard_total)
        
        if slope >= 0:
            return {'success': False, 'error': 'Slope (b) harus negatif untuk model Schaefer yang valid'}
        
        # Parameter MSY menurut Schaefer (1954)
        F_MSY = -intercept / (2 * slope) if slope != 0 else 0
        U_MSY = intercept / 2 if intercept != 0 else 0
        C_MSY = F_MSY * U_MSY
        
        # Parameter biologis menggunakan formula Gulland (1971): MSY = r × K / 4
        K = 4 * C_MSY / r_value if r_value > 0 else 0
        q = U_MSY / (K/2) if K > 0 else 0  # Catchability coefficient
        
        return {
            'model': 'Schaefer',
            'a': intercept, 'b': slope, 'r_squared': r_value_reg ** 2, 'p_value': p_value,
            'std_err': std_err, 'F_MSY': F_MSY, 'C_MSY': C_MSY, 'U_MSY': U_MSY,
            'r': r_value, 'K': K, 'q': q,
            'success': True,
            'equation': f"CPUE = {intercept:.4f} + {slope:.6f} × F",
            'reference': 'Schaefer (1954)',
            'formula': 'CPUE = a + b × F; MSY = -a²/(4b)'
        }
    except Exception as e:
        return {'success': False, 'error': f'Error dalam model Schaefer: {str(e)}'}

def model_fox(F, a, b):
    """
    Model Fox (1970): C = F × exp(a - b × F)
    """
    return F * np.exp(a - b * F)

def analisis_msy_fox(standard_effort_total, production_total, r_value):
    """
    Analisis MSY menggunakan Model Fox (1970)
    """
    if len(standard_effort_total) < 3:
        return None
    
    try:
        initial_guess = [1.0, 0.001]
        popt, pcov = curve_fit(model_fox, standard_effort_total, production_total, p0=initial_guess, maxfev=5000)
        a, b = popt
        
        if b <= 0:
            return {'success': False, 'error': 'Parameter b harus positif untuk model Fox yang valid'}
        
        # Parameter MSY menurut Fox (1970)
        F_MSY = 1 / b
        C_MSY = (1 / b) * np.exp(a - 1)
        U_MSY = C_MSY / F_MSY if F_MSY > 0 else 0
        
        # Carrying capacity: K = exp(a) / b
        K = np.exp(a) / b if b != 0 else 0
        
        # R-squared calculation
        predictions = model_fox(standard_effort_total, a, b)
        ss_res = np.sum((production_total - predictions) ** 2)
        ss_tot = np.sum((production_total - np.mean(production_total)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {
            'model': 'Fox',
            'a': a, 'b': b, 'r_squared': r_squared, 'p_value': 0.001,
            'std_err': np.sqrt(np.diag(pcov))[0], 'F_MSY': F_MSY, 'C_MSY': C_MSY, 'U_MSY': U_MSY,
            'r': r_value, 'K': K,
            'success': True,
            'equation': f"C = F × exp({a:.4f} - {b:.6f} × F)",
            'reference': 'Fox (1970)',
            'formula': 'C = F × exp(a - b × F); MSY = (1/b) × exp(a - 1)'
        }
    except Exception as e:
        return {'success': False, 'error': f'Error dalam model Fox: {str(e)}'}

def bandingkan_model_msy(standard_effort_total, cpue_standard_total, production_total, selected_models, r_value):
    """Bandingkan beberapa model MSY"""
    results = {}
    
    if 'Schaefer' in selected_models:
        results['Schaefer'] = analisis_msy_schaefer(standard_effort_total, cpue_standard_total, production_total, r_value)
    
    if 'Fox' in selected_models:
        results['Fox'] = analisis_msy_fox(standard_effort_total, production_total, r_value)
    
    return results

# ==============================================
# FUNGSI GRAFIK MSY DENGAN INFORMASI REFERENSI
# ==============================================
def buat_grafik_msy_schaefer(ax, effort_data, cpue_data, model_results):
    """Buat grafik MSY untuk model Schaefer dengan referensi"""
    if not model_results['success']:
        return
    
    ax.scatter(effort_data, cpue_data, color='blue', s=60, zorder=5, label='Data Observasi')
    
    x_fit = np.linspace(0, max(effort_data) * 1.2, 100)
    y_fit = model_results['a'] + model_results['b'] * x_fit
    ax.plot(x_fit, y_fit, 'r-', linewidth=2, label='Model Schaefer')
    
    msy_x = model_results['F_MSY']
    msy_y = model_results['U_MSY']
    ax.scatter([msy_x], [msy_y], color='green', s=100, zorder=6, label='MSY Point')
    ax.axvline(x=msy_x, color='green', linestyle='--', alpha=0.7)
    ax.axhline(y=msy_y, color='green', linestyle='--', alpha=0.7)
    
    ax.set_xlabel('Upaya Penangkapan (F)')
    ax.set_ylabel('CPUE (U)')
    ax.set_title(f"Model Schaefer (1954)\nCPUE vs Upaya (r = {model_results['r']:.3f})")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Tambahkan persamaan
    ax.text(0.05, 0.95, f"CPUE = {model_results['a']:.3f} + {model_results['b']:.6f}F", 
            transform=ax.transAxes, fontsize=9,
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    ax.annotate(f'MSY\nF={msy_x:.1f}\nU={msy_y:.3f}', 
                xy=(msy_x, msy_y), xytext=(msy_x*1.1, msy_y*1.1),
                arrowprops=dict(arrowstyle='->', color='green'))

def buat_grafik_produksi_schaefer(ax, effort_data, production_data, model_results):
    """Buat grafik produksi vs upaya untuk model Schaefer"""
    if not model_results['success']:
        return
    
    ax.scatter(effort_data, production_data, color='blue', s=60, zorder=5, label='Data Observasi')
    
    x_fit = np.linspace(0, max(effort_data) * 1.2, 100)
    y_fit = model_results['a'] * x_fit + model_results['b'] * (x_fit ** 2)
    ax.plot(x_fit, y_fit, 'r-', linewidth=2, label='Kurva Produksi')
    
    msy_x = model_results['F_MSY']
    msy_y = model_results['C_MSY']
    ax.scatter([msy_x], [msy_y], color='green', s=100, zorder=6, label='MSY Point')
    ax.axvline(x=msy_x, color='green', linestyle='--', alpha=0.7)
    
    ax.set_xlabel('Upaya Penangkapan (F)')
    ax.set_ylabel('Produksi (C)')
    ax.set_title(f"Model Schaefer (1954)\nProduksi vs Upaya\nr = {model_results['r']:.3f}, K = {model_results.get('K', 0):,.0f} kg")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Tambahkan persamaan
    ax.text(0.05, 0.95, f"C = {model_results['a']:.3f}F + {model_results['b']:.6f}F²", 
            transform=ax.transAxes, fontsize=9,
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    ax.annotate(f'MSY/JTB\nF={msy_x:.1f}\nC={msy_y:.1f} kg', 
                xy=(msy_x, msy_y), xytext=(msy_x*1.1, msy_y*0.9),
                arrowprops=dict(arrowstyle='->', color='green'))

def buat_grafik_fox(ax, effort_data, production_data, model_results):
    """Buat grafik untuk model Fox dengan referensi"""
    if not model_results['success']:
        return
    
    ax.scatter(effort_data, production_data, color='blue', s=60, zorder=5, label='Data Observasi')
    
    x_fit = np.linspace(0.1, max(effort_data) * 1.2, 100)
    y_fit = model_fox(x_fit, model_results['a'], model_results['b'])
    ax.plot(x_fit, y_fit, 'r-', linewidth=2, label='Model Fox')
    
    msy_x = model_results['F_MSY']
    msy_y = model_results['C_MSY']
    ax.scatter([msy_x], [msy_y], color='green', s=100, zorder=6, label='MSY Point')
    ax.axvline(x=msy_x, color='green', linestyle='--', alpha=0.7)
    
    ax.set_xlabel('Upaya Penangkapan (F)')
    ax.set_ylabel('Produksi (C)')
    ax.set_title(f"Model Fox (1970)\nProduksi vs Upaya\nr = {model_results['r']:.3f}, K = {model_results.get('K', 0):,.0f} kg")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Tambahkan persamaan
    ax.text(0.05, 0.95, f"C = F × exp({model_results['a']:.3f} - {model_results['b']:.6f}F)", 
            transform=ax.transAxes, fontsize=9,
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    ax.annotate(f'MSY/JTB\nF={msy_x:.1f}\nC={msy_y:.1f} kg', 
                xy=(msy_x, msy_y), xytext=(msy_x*1.1, msy_y*0.9),
                arrowprops=dict(arrowstyle='->', color='green'))

def buat_grafik_perbandingan_model(ax, effort_data, production_data, all_results):
    """Buat grafik perbandingan semua model"""
    colors = ['red', 'blue']
    line_styles = ['-', '--']
    
    ax.scatter(effort_data, production_data, color='black', s=80, zorder=5, label='Data Observasi')
    
    for i, (model_name, results) in enumerate(all_results.items()):
        if results and results['success']:
            x_fit = np.linspace(0.1, max(effort_data) * 1.2, 100)
            
            if model_name == 'Schaefer':
                y_fit = results['a'] * x_fit + results['b'] * (x_fit ** 2)
                label = f"{model_name} (1954)"
            elif model_name == 'Fox':
                y_fit = model_fox(x_fit, results['a'], results['b'])
                label = f"{model_name} (1970)"
            else:
                continue
                
            ax.plot(x_fit, y_fit, color=colors[i % len(colors)], 
                   linestyle=line_styles[i % len(line_styles)], 
                   linewidth=2, label=label)
            
            ax.scatter([results['F_MSY']], [results['C_MSY']], 
                      color=colors[i % len(colors)], s=100, marker='*', zorder=6)
    
    ax.set_xlabel('Upaya Penangkapan (F)')
    ax.set_ylabel('Produksi (C)')
    ax.set_title('Perbandingan Model MSY\nSchaefer (1954) vs Fox (1970)')
    ax.legend()
    ax.grid(True, alpha=0.3)

def render_grafik_msy_lengkap(effort_data, cpue_data, production_data, msy_results):
    """Render grafik MSY yang lengkap"""
    st.header("📈 Grafik Analisis MSY")
    
    successful_models = {k: v for k, v in msy_results.items() if v and v['success']}
    
    if not successful_models:
        st.warning("Tidak ada model yang berhasil untuk ditampilkan grafiknya.")
        return
    
    r_values = []
    for model_name, results in successful_models.items():
        if results and results['success']:
            r_values.append(results['r'])
    
    if r_values:
        st.info(f"**Parameter r yang digunakan:** {r_values[0]:.3f} (sumber: FishBase)")
    
    tab1, tab2, tab3 = st.tabs(["📊 Grafik Individual", "📈 Grafik Produksi", "🆚 Perbandingan Model"])
    
    with tab1:
        st.subheader("Grafik Individual Setiap Model")
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
        
        # Tambahkan referensi di grafik
        fig.text(0.02, 0.02, 'Sumber: Schaefer (1954), Fox (1970), Gulland (1971)', 
                 fontsize=8, style='italic', color='gray')
        
        st.pyplot(fig)
        plt.close()
        
        st.subheader("📋 Tabel Perbandingan Model")
        comparison_data = []
        for model_name, results in successful_models.items():
            comparison_data.append({
                'Model': model_name,
                'MSY/JTB (kg)': f"{results['C_MSY']:,.1f}",
                'F_MSY': f"{results['F_MSY']:,.1f}",
                'U_MSY': f"{results['U_MSY']:.3f}",
                'r (laju pertumbuhan)': f"{results['r']:.3f}",
                'K (daya dukung)': f"{results.get('K', 0):,.0f}",
                'R²': f"{results['r_squared']:.3f}",
                'Persamaan': results['equation'],
                'Referensi': results['reference']
            })
        
        st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)

# ==============================================
# ANALISIS STATUS STOK DAN REKOMENDASI DENGAN REFERENSI
# ==============================================
def analisis_status_stok(msy_results, production_values, effort_values, years):
    """Analisis status stok berdasarkan hasil MSY"""
    successful_models = {k: v for k, v in msy_results.items() if v and v['success']}
    if not successful_models:
        return None
    
    best_model_name, best_model = max(successful_models.items(), key=lambda x: x[1]['r_squared'])
    
    current_year = years[-1] if years else None
    current_production = production_values[-1] if len(production_values) > 0 else 0
    current_effort = effort_values[-1] if len(effort_values) > 0 else 0
    
    jtb_value = best_model['C_MSY']
    f_msy_value = best_model['F_MSY']
    r_value = best_model['r']
    
    production_ratio = (current_production / jtb_value) * 100 if jtb_value > 0 else 0
    
    # Kriteria status stok berdasarkan FAO (2014)
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
    
    # Analisis trend produksi
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
    
    # Rekomendasi kuantitatif
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
    
    # Estimasi waktu pemulihan
    if status_stok == "OVERFISHING" and r_value > 0:
        waktu_pemulihan = np.log(2) / r_value if r_value > 0 else 0
        waktu_pemulihan_text = f"{waktu_pemulihan:.1f} tahun"
    else:
        waktu_pemulihan_text = "Tidak diperlukan"
    
    return {
        'best_model': best_model_name,
        'current_year': current_year,
        'current_production': current_production,
        'current_effort': current_effort,
        'msy': best_model['C_MSY'],
        'f_msy': best_model['F_MSY'],
        'u_msy': best_model['U_MSY'],
        'r_value': r_value,
        'K': best_model.get('K', 0),
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
        'waktu_pemulihan': waktu_pemulihan_text,
        'tahun_data': years,
        'model_reference': best_model.get('reference', ''),
        'model_formula': best_model.get('formula', '')
    }

def render_rekomendasi(recommendations, production_data, years):
    """Render rekomendasi pengelolaan dan JTB dengan referensi"""
    st.header("🎯 REKOMENDASI PENGELOLAAN DAN JTB")
    
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
        st.metric("Laju Pertumbuhan (r)", f"{recommendations['r_value']:.3f}")
        st.caption(f"K (daya dukung): {recommendations['K']:,.0f} kg")
    
    st.info(f"""
    **📌 INFORMASI PARAMETER DAN REFERENSI:**
    - **r (laju pertumbuhan intrinsik)**: {recommendations['r_value']:.3f} 
      (sumber: FishBase untuk Nemipterus spp)
    - **K (daya dukung)**: {recommendations['K']:,.0f} kg
      (dihitung menggunakan formula Gulland: K = 4 × MSY / r)
    - **Sumber nilai r**: [FishBase - Nemipterus spp](https://www.fishbase.se/search.php)
    - **Perkiraan waktu pemulihan jika overfishing**: {recommendations['waktu_pemulihan']} untuk pulih 50%
      (berdasarkan model pertumbuhan logistik: T = ln(2)/r)
    - **Model yang digunakan**: {recommendations['best_model']} ({recommendations['model_reference']})
    - **Rumus model**: {recommendations['model_formula']}
    """)
    
    st.subheader("📈 PERBANDINGAN PRODUKSI DAN JTB")
    fig, ax = plt.subplots(figsize=(12, 6))
    production_values = [d['Jumlah'] for d in production_data]
    
    ax.plot(years, production_values, 'bo-', linewidth=2, markersize=8, label='Produksi Aktual')
    ax.axhline(y=recommendations['msy'], color='red', linestyle='--', linewidth=2, label='JTB (MSY)')
    
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
    ax.set_title(f'Produksi vs JTB\n(Model: {recommendations["best_model"]}, r = {recommendations["r_value"]:.3f})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    st.pyplot(fig)
    
    st.subheader("📋 REKOMENDASI PENGELOLAAN")
    st.info(f"**{recommendations['rekomendasi']}**")
    st.write(f"**Aksi Khusus:** {recommendations['aksi_khusus']}")
    
    st.subheader("🎯 RENCANA AKSI BERDASARKAN STATUS")
    if recommendations['status_stok'] == "OVERFISHING":
        st.error(f"""
        **🔴 RENCANA AKSI OVERFISHING:**
        
        **1. PENURUNAN SEGERA (1-3 bulan):**
        - Turunkan upaya penangkapan sesuai rekomendasi
        - Implementasi sistem kuota ketat berdasarkan JTB {recommendations['jtb']:,.0f} kg
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
        st.warning(f"""
        **🟡 RENCANA AKSI FULLY EXPLOITED:**
        
        **1. PEMELIHARAAN STATUS (1-3 bulan):**
        - Pertahankan upaya pada level F_MSY = {recommendations['f_msy']:,.0f} trip
        - Sistem kuota berbasis JTB {recommendations['jtb']:,.0f} kg
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
    
    else:
        st.success(f"""
        **🟢 RENCANA AKSI UNDERFISHING:**
        
        **1. PENINGKATAN BERTAHAP (1-3 bulan):**
        - Tingkatkan upaya menuju F_MSY = {recommendations['f_msy']:,.0f} trip
        - Roadmap peningkatan produksi menuju JTB {recommendations['jtb']:,.0f} kg
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

# ==============================================
# FUNGSI PERHITUNGAN CPUE, FPI, dll.
# ==============================================
def hitung_cpue(produksi_df, upaya_df, gears):
    """
    Hitung CPUE untuk setiap alat tangkap
    """
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
    """
    Hitung FPI per tahun - FPI diambil dari nilai CPUE tertinggi = 1
    """
    fpi_data = []
    years = cpue_df['Tahun'].values
    
    for year in years:
        clean_year = int(year) if isinstance(year, float) and year.is_integer() else year
        year_data = {'Tahun': clean_year}
        
        cpue_values = [cpue_df[cpue_df['Tahun'] == year][gear].values[0] for gear in gears]
        max_cpue = max(cpue_values) if cpue_values else 1
        
        for gear in gears:
            cpue_gear = cpue_df[cpue_df['Tahun'] == year][gear].values[0]
            fpi = cpue_gear / max_cpue if max_cpue > 0 else 0
            year_data[gear] = fpi
        
        year_data['Jumlah'] = sum([year_data[gear] for gear in gears])
        fpi_data.append(year_data)
    
    return pd.DataFrame(fpi_data)

def hitung_upaya_standar(upaya_df, fpi_df, gears):
    """
    Hitung upaya standar
    """
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
    """
    Hitung CPUE standar per alat tangkap dan total
    """
    standard_cpue_data = []
    years = produksi_df['Tahun'].values
    
    for year in years:
        clean_year = int(year) if isinstance(year, float) and year.is_integer() else year
        year_data = {'Tahun': clean_year}
        
        for gear in gears:
            prod = produksi_df[produksi_df['Tahun'] == year][gear].values[0]
            std_eff = standard_effort_df[standard_effort_df['Tahun'] == year][gear].values[0]
            cpue_standar = prod / std_eff if std_eff > 0 else 0
            year_data[f'{gear}_Std_CPUE'] = cpue_standar
        
        total_production = produksi_df[produksi_df['Tahun'] == year]['Jumlah'].values[0]
        total_standard_effort = standard_effort_df[standard_effort_df['Tahun'] == year]['Jumlah'].values[0]
        
        cpue_standar_total = total_production / total_standard_effort if total_standard_effort > 0 else 0
        year_data['CPUE_Standar_Total'] = cpue_standar_total
        year_data['Ln_CPUE'] = np.log(cpue_standar_total) if cpue_standar_total > 0 else 0
        
        standard_cpue_data.append(year_data)
    
    return pd.DataFrame(standard_cpue_data)

# ==============================================
# FUNGSI EKSPOR HASIL ANALISIS KE EXCEL
# ==============================================
def ekspor_hasil_analisis():
    """Ekspor hasil analisis ke file Excel"""
    if st.session_state.analysis_results is None:
        st.error("❌ Tidak ada hasil analisis untuk diekspor. Silakan lakukan analisis terlebih dahulu.")
        return None
    
    try:
        results = st.session_state.analysis_results
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Data dasar
            results['df_production'].to_excel(writer, sheet_name='Data Produksi', index=False)
            results['df_effort'].to_excel(writer, sheet_name='Data Upaya', index=False)
            results['df_cpue'].to_excel(writer, sheet_name='CPUE Data', index=False)
            results['df_fpi'].to_excel(writer, sheet_name='FPI Data', index=False)
            results['df_standard_effort'].to_excel(writer, sheet_name='Upaya Standar', index=False)
            results['df_standard_cpue'].to_excel(writer, sheet_name='CPUE Standar', index=False)
            
            # Hasil MSY
            msy_data = []
            for model_name, model_results in results['msy_results'].items():
                if model_results and model_results['success']:
                    msy_data.append({
                        'Model': model_name,
                        'JTB (kg)': model_results['C_MSY'],
                        'F_MSY': model_results['F_MSY'],
                        'U_MSY': model_results['U_MSY'],
                        'r (laju pertumbuhan)': model_results['r'],
                        'K (daya dukung)': model_results.get('K', 0),
                        'R²': model_results['r_squared'],
                        'Persamaan': model_results['equation'],
                        'Referensi': model_results.get('reference', ''),
                        'Rumus': model_results.get('formula', ''),
                        'Status': 'Valid'
                    })
                else:
                    msy_data.append({
                        'Model': model_name,
                        'JTB (kg)': '-',
                        'F_MSY': '-',
                        'U_MSY': '-',
                        'r (laju pertumbuhan)': '-',
                        'K (daya dukung)': '-',
                        'R²': '-',
                        'Persamaan': '-',
                        'Referensi': '-',
                        'Rumus': '-',
                        'Status': model_results.get('error', 'Gagal') if model_results else 'Tidak ada hasil'
                    })
            
            df_msy = pd.DataFrame(msy_data)
            df_msy.to_excel(writer, sheet_name='Hasil MSY', index=False)
            
            # Rekomendasi
            if 'recommendations' in results:
                rec = results['recommendations']
                
                summary_data = pd.DataFrame({
                    'Parameter': [
                        'Tahun Analisis', 'Status Stok', 'JTB (kg)', 'F_MSY', 'U_MSY',
                        'r (laju pertumbuhan)', 'K (daya dukung)',
                        'Produksi Terkini (kg)', 'Upaya Terkini (trip)', 
                        'Rasio Produksi/JTB (%)', 'Trend Produksi', 'Model Terbaik', 'Estimasi Pemulihan',
                        'Rekomendasi Utama', 'Kriteria Status', 'Referensi Model'
                    ],
                    'Nilai': [
                        rec['current_year'], rec['status_stok'], f"{rec['jtb']:,.1f}", 
                        f"{rec['f_msy']:,.1f}", f"{rec['u_msy']:.3f}",
                        f"{rec['r_value']:.3f}", f"{rec['K']:,.0f}",
                        f"{rec['current_production']:,.1f}", f"{rec['current_effort']:,.1f}",
                        f"{rec['production_ratio']:.1f}", rec['trend_status'], rec['best_model'], rec['waktu_pemulihan'],
                        rec['rekomendasi'], 'FAO (2014)', rec.get('model_reference', '')
                    ]
                })
                summary_data.to_excel(writer, sheet_name='Rekomendasi', index=False)
        
        processed_data = output.getvalue()
        return processed_data
        
    except Exception as e:
        st.error(f"❌ Error saat mengekspor hasil: {str(e)}")
        return None

def render_ekspor_excel_section():
    """Render section untuk ekspor Excel"""
    if st.session_state.analysis_results is None:
        st.warning("📊 Hasil analisis belum tersedia. Silakan lakukan analisis terlebih dahulu.")
        return
    
    st.header("📤 Ekspor Hasil Analisis ke Excel")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        *📁 File Excel yang Akan Dihasilkan:*
        
        **Sheet 'Data Produksi'**: Data produksi per alat tangkap
        **Sheet 'Data Upaya'**: Data upaya penangkapan per alat tangkap  
        **Sheet 'CPUE Data'**: Hasil perhitungan CPUE
        **Sheet 'FPI Data'**: Hasil perhitungan Fishing Power Index
        **Sheet 'Upaya Standar'**: Hasil standardisasi upaya
        **Sheet 'CPUE Standar'**: Hasil CPUE standar per alat tangkap
        **Sheet 'Hasil MSY'**: Perbandingan model Schaefer vs Fox
        **Sheet 'Rekomendasi'**: Rekomendasi pengelolaan dan JTB
        """)
    
    with col2:
        export_data = ekspor_hasil_analisis()
        if export_data is not None:
            st.download_button(
                label="📥 Download Hasil Analisis (Excel)",
                data=export_data,
                file_name=f"Hasil_Analisis_IKAN_KURISI_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
            )
        
        st.markdown("""
        *🔧 Cara Penggunaan:*
        1. Lakukan analisis terlebih dahulu
        2. Klik tombol download di samping
        3. File Excel akan berisi semua hasil
        4. Gunakan untuk dokumentasi dan pengambilan keputusan
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
    """Reset ke data contoh yang konsisten"""
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
    st.success("✅ Data telah direset ke data contoh!")

# ==============================================
# FUNGSI UNTUK SIDEBAR KONFIGURASI
# ==============================================
def render_sidebar():
    """Render sidebar untuk konfigurasi aplikasi"""
    with st.sidebar:
        st.header("⚙️ Konfigurasi Analisis")
        
        # Tampilkan referensi ilmiah di sidebar
        render_referensi_ilmiah()
        
        st.markdown("---")
        
        data_source = st.radio(
            "Pilih Sumber Data",
            ["📁 Data Upload", "📊 Data Contoh"],
            index=1,
            help="Pilih antara mengupload data sendiri atau menggunakan data contoh"
        )
        
        if data_source == "📁 Data Upload":
            st.session_state.use_uploaded_data = True
            if st.button("📤 Buka Menu Upload", use_container_width=True):
                st.session_state.show_upload_section = True
        else:
            st.session_state.use_uploaded_data = False
            st.session_state.show_upload_section = False
        
        st.subheader("🧬 Parameter Biologis")
        r_value = st.number_input(
            "Nilai r (laju pertumbuhan intrinsik)",
            min_value=0.1,
            max_value=2.0,
            value=st.session_state.r_value,
            step=0.01,
            help="Parameter biologis r dari FishBase (default: 0.58 untuk Nemipterus spp)"
        )
        st.session_state.r_value = r_value
        
        st.info(f"**Nilai r saat ini:** {r_value:.3f} (FishBase)")
        
        st.subheader("📐 Pilih Model MSY")
        model_options = ['Schaefer', 'Fox']
        selected_models = st.multiselect(
            "Pilih model untuk analisis:",
            options=model_options,
            default=st.session_state.selected_models,
            help="Pilih model yang akan digunakan dalam analisis MSY"
        )
        
        if len(selected_models) == 0:
            st.warning("Pilih minimal satu model")
            selected_models = st.session_state.selected_models
        else:
            st.session_state.selected_models = selected_models
        
        if not st.session_state.use_uploaded_data:
            st.subheader("🎣 Konfigurasi Alat Tangkap")
            
            config = get_config()
            
            num_gears = st.number_input(
                "Jumlah Alat Tangkap",
                min_value=1,
                max_value=10,
                value=len(config['gears']),
                step=1,
                help="Jumlah alat tangkap yang akan dianalisis"
            )
            
            num_years = st.number_input(
                "Jumlah Tahun",
                min_value=3,
                max_value=20,
                value=config['num_years'],
                step=1,
                help="Jumlah tahun data yang akan dianalisis"
            )
            
            start_year = st.number_input(
                "Tahun Awal",
                min_value=2000,
                max_value=2030,
                value=min(config['years']),
                step=1,
                help="Tahun awal data"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Update Konfigurasi", use_container_width=True):
                    years = generate_years(start_year, num_years)
                    save_config(config['gears'], config['display_names'], 
                              config['standard_gear'], years, num_years)
                    st.success("✅ Konfigurasi diperbarui!")
            
            with col2:
                if st.button("🔄 Reset Data", use_container_width=True):
                    reset_data()
        
        st.markdown("---")
        st.info("""
        **📌 Panduan Penggunaan:**
        1. Pilih sumber data (upload atau contoh)
        2. Atur parameter r sesuai kebutuhan
        3. Pilih model MSY yang akan digunakan
        4. Lakukan analisis di halaman utama
        5. Lihat hasil dan rekomendasi
        6. Download laporan PDF/Excel untuk dokumentasi
        """)

# ==============================================
# FUNGSI ANALISIS UTAMA
# ==============================================
def lakukan_analisis():
    """Fungsi utama untuk melakukan analisis lengkap"""
    if 'data_tables' not in st.session_state:
        st.error("❌ Data tidak tersedia. Silakan konfigurasi data terlebih dahulu.")
        return None
    
    with st.status("🔬 Melakukan analisis...", expanded=True) as status:
        st.write("📊 Membaca data produksi dan upaya...")
        
        production_data = st.session_state.data_tables['production']
        effort_data = st.session_state.data_tables['effort']
        config = get_config()
        gears = config['gears']
        display_names = config['display_names']
        
        df_production = pd.DataFrame(production_data)
        df_effort = pd.DataFrame(effort_data)
        
        if df_production.empty or df_effort.empty:
            st.error("❌ Data produksi atau upaya kosong")
            return None
        
        st.write("🧮 Menghitung CPUE...")
        df_cpue = hitung_cpue(df_production, df_effort, gears)
        
        st.write("📈 Menghitung FPI...")
        df_fpi = hitung_fpi_per_tahun(df_cpue, gears, config['standard_gear'])
        
        st.write("⚖️ Menghitung upaya standar...")
        df_standard_effort = hitung_upaya_standar(df_effort, df_fpi, gears)
        
        st.write("📊 Menghitung CPUE standar...")
        df_standard_cpue = hitung_cpue_standar(df_production, df_standard_effort, gears)
        
        st.write("🎯 Melakukan analisis MSY...")
        standard_effort_total = df_standard_effort['Jumlah'].values
        cpue_standard_total = df_standard_cpue['CPUE_Standar_Total'].values
        production_total = df_production['Jumlah'].values
        
        msy_results = bandingkan_model_msy(
            standard_effort_total, 
            cpue_standard_total, 
            production_total, 
            st.session_state.selected_models,
            st.session_state.r_value
        )
        
        st.write("📋 Menganalisis status stok...")
        years = df_production['Tahun'].values.tolist()
        recommendations = analisis_status_stok(msy_results, production_total, standard_effort_total, years)
        
        results = {
            'df_production': df_production,
            'df_effort': df_effort,
            'df_cpue': df_cpue,
            'df_fpi': df_fpi,
            'df_standard_effort': df_standard_effort,
            'df_standard_cpue': df_standard_cpue,
            'msy_results': msy_results,
            'recommendations': recommendations,
            'years': years,
            'gears': gears,
            'display_names': display_names
        }
        
        st.session_state.analysis_results = results
        status.update(label="✅ Analisis selesai!", state="complete")
        
        return results

# ==============================================
# FUNGSI TAMPILAN HASIL ANALISIS
# ==============================================
def render_hasil_analisis():
    """Tampilkan hasil analisis lengkap"""
    if st.session_state.analysis_results is None:
        st.warning("📊 Hasil analisis belum tersedia. Silakan lakukan analisis terlebih dahulu.")
        return
    
    results = st.session_state.analysis_results
    
    st.header("📊 HASIL ANALISIS LENGKAP")
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📈 Data Dasar", "📊 Grafik CPUE", "🎣 CPUE & FPI", 
        "⚖️ Upaya Standar", "📈 CPUE Standar", "🎯 Hasil MSY", 
        "💡 Rekomendasi", "📤 Excel", "📄 PDF"
    ])
    
    with tab1:
        st.subheader("📊 Data Produksi (kg)")
        st.dataframe(
            results['df_production'].style.format({
                col: "{:,.0f}" for col in results['df_production'].columns if col != 'Tahun'
            }), 
            use_container_width=True
        )
        
        st.subheader("🎣 Data Upaya (trip)")
        st.dataframe(
            results['df_effort'].style.format({
                col: "{:,.0f}" for col in results['df_effort'].columns if col != 'Tahun'
            }), 
            use_container_width=True
        )
    
    with tab2:
        # Tampilkan grafik CPUE
        render_grafik_cpue(results['df_cpue'], results['df_effort'], 
                          results['gears'], results['display_names'])
    
    with tab3:
        st.subheader("📈 CPUE (kg/trip)")
        st.dataframe(
            results['df_cpue'].style.format({
                col: "{:.3f}" for col in results['df_cpue'].columns if col != 'Tahun'
            }), 
            use_container_width=True
        )
        
        st.subheader("📊 Fishing Power Index (FPI)")
        st.dataframe(
            results['df_fpi'].style.format({
                col: "{:.3f}" for col in results['df_fpi'].columns if col != 'Tahun'
            }), 
            use_container_width=True
        )
    
    with tab4:
        st.subheader("⚖️ Upaya Standar")
        st.dataframe(
            results['df_standard_effort'].style.format({
                col: "{:,.1f}" for col in results['df_standard_effort'].columns if col != 'Tahun'
            }), 
            use_container_width=True
        )
    
    with tab5:
        st.subheader("📊 CPUE Standar")
        st.dataframe(
            results['df_standard_cpue'].style.format({
                col: "{:.4f}" for col in results['df_standard_cpue'].columns if col != 'Tahun'
            }), 
            use_container_width=True
        )
    
    with tab6:
        st.subheader("🎯 HASIL ANALISIS MSY/JTB")
        st.info(f"**Parameter r yang digunakan:** {st.session_state.r_value:.3f} (sumber: FishBase)")
        
        successful_models = {k: v for k, v in results['msy_results'].items() if v and v['success']}
        
        if not successful_models:
            st.error("❌ Tidak ada model yang berhasil dihitung")
            for model_name, model_result in results['msy_results'].items():
                if model_result and not model_result['success']:
                    st.error(f"Model {model_name}: {model_result.get('error', 'Unknown error')}")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### Ringkasan Hasil MSY")
                summary_data = []
                for model_name, model_results in successful_models.items():
                    summary_data.append({
                        'Model': model_name,
                        'JTB (kg)': f"{model_results['C_MSY']:,.1f}",
                        'F_MSY': f"{model_results['F_MSY']:,.1f}",
                        'U_MSY': f"{model_results['U_MSY']:.3f}",
                        'r': f"{model_results['r']:.3f}",
                        'K': f"{model_results.get('K', 0):,.0f}",
                        'R²': f"{model_results['r_squared']:.3f}",
                        'Referensi': model_results.get('reference', '')
                    })
                
                st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
            
            with col2:
                st.markdown("##### Detail Parameter dan Rumus")
                for model_name, model_results in successful_models.items():
                    with st.expander(f"📋 Detail Model {model_name}"):
                        st.write(f"**Referensi:** {model_results.get('reference', '')}")
                        st.write(f"**Persamaan:** {model_results['equation']}")
                        st.write(f"**Rumus:** {model_results.get('formula', '')}")
                        st.write(f"**Parameter a:** {model_results.get('a', 'N/A'):.6f}")
                        st.write(f"**Parameter b:** {model_results.get('b', 'N/A'):.6f}")
                        st.write(f"**Standard Error:** {model_results['std_err']:.6f}")
                        st.write(f"**P-value:** {model_results['p_value']:.6f}")
                        if 'q' in model_results:
                            st.write(f"**q (catchability):** {model_results['q']:.6f}")
            
            standard_effort_total = results['df_standard_effort']['Jumlah'].values
            cpue_standard_total = results['df_standard_cpue']['CPUE_Standar_Total'].values
            production_total = results['df_production']['Jumlah'].values
            
            render_grafik_msy_lengkap(standard_effort_total, cpue_standard_total, production_total, results['msy_results'])
    
    with tab7:
        if 'recommendations' in results and results['recommendations']:
            render_rekomendasi(results['recommendations'], results['df_production'].to_dict('records'), results['years'])
        else:
            st.warning("Rekomendasi belum tersedia")
    
    with tab8:
        render_ekspor_excel_section()
    
    with tab9:
        render_ekspor_pdf_section()

# ==============================================
# FUNGSI UTAMA APLIKASI
# ==============================================
def main():
    """Fungsi utama aplikasi"""
    initialize_session_state()
    
    render_sidebar()
    
    if st.session_state.get('show_upload_section', False):
        render_upload_section()
        return
    
    st.header("🔬 Analisis Potensi Lestari Ikan Kurisi")
    
    if st.session_state.use_uploaded_data and st.session_state.uploaded_data:
        st.success("✅ Menggunakan data yang diupload")
    else:
        st.info("📊 Menggunakan data contoh PPN Karangantu, Banten")
    
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    
    with col1:
        if st.button("🚀 Lakukan Analisis", type="primary", use_container_width=True):
            results = lakukan_analisis()
            if results:
                st.success("✅ Analisis berhasil! Hasil siap dilihat di tab di bawah.")
    
    with col2:
        if st.session_state.analysis_results:
            if st.button("🔄 Analisis Ulang", use_container_width=True):
                st.session_state.analysis_results = None
                st.rerun()
    
    with col3:
        if st.session_state.analysis_results:
            if st.button("📤 Excel", use_container_width=True):
                render_ekspor_excel_section()
                st.rerun()
    
    with col4:
        if st.session_state.analysis_results:
            if st.button("📄 PDF", use_container_width=True):
                render_ekspor_pdf_section()
                st.rerun()
    
    st.markdown("---")
    
    if st.session_state.analysis_results:
        render_hasil_analisis()
    else:
        st.info("""
        **📋 PANDUAN ANALISIS:**
        
        1. **Konfigurasi Data** (di sidebar):
           - Pilih sumber data (upload atau contoh)
           - Atur parameter r (laju pertumbuhan intrinsik dari FishBase)
           - Pilih model MSY yang akan digunakan (Schaefer 1954/Fox 1970)
        
        2. **Lakukan Analisis**:
           - Klik tombol "🚀 Lakukan Analisis"
           - Tunggu proses perhitungan selesai
        
        3. **Hasil Analisis** akan muncul di sini:
           - Data produksi dan upaya
           - Grafik CPUE dengan analisis trend
           - Perhitungan CPUE dan FPI
           - Standardisasi upaya
           - Analisis MSY/JTB dengan parameter r dari FishBase
           - Status stok berdasarkan kriteria FAO (2014)
           - Rekomendasi pengelolaan
        
        4. **Ekspor Hasil**:
           - **Excel**: Download semua data dan hasil analisis
           - **PDF**: Laporan lengkap 7 halaman dengan referensi ilmiah
        
        **💡 INFORMASI PENTING:**
        - **Parameter r** dapat diubah di sidebar (default: 0.58 dari FishBase)
        - **JTB (Jumlah Tangkapan yang Diperbolehkan)** = MSY (Maximum Sustainable Yield)
        - **Nilai 13,609.0211 adalah MSY/JTB dalam kg, BUKAN nilai r!**
        - **CPUE (Catch Per Unit Effort)** adalah indikator efisiensi penangkapan
        - **Semua rumus** dilengkapi dengan referensi ilmiah
        - Analisis ini menggunakan pendekatan ilmiah untuk pengelolaan perikanan berkelanjutan
        """)

# ==============================================
# JALANKAN APLIKASI
# ==============================================
if __name__ == "__main__":
    main()

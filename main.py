import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="Analisis CPUE dan MSY - PPN Karangantu", layout="wide")

st.title("🐟 Analisis CPUE dan MSY Ikan yang Didaratkan di PPN Karangantu")

st.markdown("""
Aplikasi ini digunakan untuk menganalisis **Catch Per Unit Effort (CPUE)** dan **Maximum Sustainable Yield (MSY)** 
berdasarkan data tangkapan dan upaya penangkapan ikan.
""")

# ------------------------------------------------------
# Fungsi bantu
# ------------------------------------------------------
def deteksi_kolom(df):
    kolom_map = {
        "tahun": ["tahun", "year", "thn"],
        "jenis_ikan": ["jenis_ikan", "ikan", "spesies", "species"],
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
    content = file.read().decode('utf-8')
    file.seek(0)
    # deteksi pemisah otomatis
    if ';' in content and ',' not in content.split('\n')[0]:
        df = pd.read_csv(io.StringIO(content), delimiter=';')
    else:
        df = pd.read_csv(io.StringIO(content))
    return df

# ------------------------------------------------------
# Input data
# ------------------------------------------------------
st.sidebar.header("📂 Input Data")

opsi_input = st.sidebar.radio("Pilih cara input data:", ["Upload File", "Input Manual"])

if opsi_input == "Upload File":
    file = st.sidebar.file_uploader("Upload file CSV atau Excel", type=["csv", "xlsx"])
    if file:
        try:
            if file.name.endswith(".csv"):
                df = baca_csv_otomatis(file)
            else:
                df = pd.read_excel(file)
            df = deteksi_kolom(df)
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")
            df = None
    else:
        df = None
else:
    tahun = st.sidebar.text_input("Tahun (pisahkan dengan koma)", "2020,2021,2022,2023,2024")
    tangkapan = st.sidebar.text_input("Tangkapan (kg)", "9958,11242,11113,13287,12912")
    upaya = st.sidebar.text_input("Upaya (trip)", "19.304,19.932,30.207,24.959,24.510")
    df = pd.DataFrame({
        "tahun": [int(t) for t in tahun.split(",")],
        "tangkapan": [float(t) for t in tangkapan.split(",")],
        "upaya": [float(u) for u in upaya.split(",")]
    })

# ------------------------------------------------------
# Analisis utama
# ------------------------------------------------------
if df is not None:
    df = deteksi_kolom(df)

    # Format kolom tahun tanpa koma
    df["tahun"] = df["tahun"].astype(str)

    st.subheader("📋 Data Awal")
    st.dataframe(df)

    if not {"tangkapan", "upaya"}.issubset(df.columns):
        st.error("⚠️ Kolom wajib 'tangkapan' dan 'upaya' tidak ditemukan. Pastikan nama kolom benar.")
    else:
        # Hitung CPUE
        df["CPUE"] = df["tangkapan"] / df["upaya"]

        st.subheader("📊 Data dengan CPUE")
        st.dataframe(df.style.format({"tangkapan": "{:.2f}", "upaya": "{:.3f}", "CPUE": "{:.3f}"}))

        # Regresi Linear: CPUE = a + bE
        x = df["upaya"]
        y = df["CPUE"]
        a, b = np.polyfit(x, y, 1)

        # Hitung MSY (Model Schaefer)
        Emsy = -a / (2 * b)
        MSY = a**2 / (-4 * b)
        tingkat_pemanfaatan = (df["tangkapan"].mean() / MSY) * 100

        st.subheader("🧮 Hasil Analisis MSY")
        col1, col2, col3 = st.columns(3)
        col1.metric("Intercept (a)", f"{a:.4f}")
        col2.metric("Slope (b)", f"{b:.6f}")
        col3.metric("MSY (kg)", f"{MSY:.2f}")

        if tingkat_pemanfaatan < 100:
            st.success("🟢 Stok ikan masih lestari.")
        elif 100 <= tingkat_pemanfaatan <= 120:
            st.warning("🟠 Stok ikan mendekati batas lestari (MSY).")
        else:
            st.error("🔴 Overfishing! Kurangi upaya penangkapan.")

        # ------------------------------------------------------
        # Grafik CPUE vs Upaya (regresi linear)
        # ------------------------------------------------------
        st.subheader("📈 Hubungan Upaya dan CPUE")
        fig, ax = plt.subplots()
        ax.scatter(x, y, color="blue", label="Data CPUE")
        ax.plot(x, a + b*x, color="red", label=f"Regresi: CPUE = {a:.3f} + {b:.5f}E")
        ax.set_xlabel("Upaya (trip)")
        ax.set_ylabel("CPUE (kg/trip)")
        ax.legend()
        st.pyplot(fig)

        # ------------------------------------------------------
        # Kurva Parabola (C = aE + bE²)
        # ------------------------------------------------------
        st.subheader("🌊 Kurva Hubungan Upaya dan Hasil Tangkapan (Model Schaefer)")
        E = np.linspace(0, df["upaya"].max() * 1.5, 200)
        C = E * (a + b * E)  # C = E × CPUE

        fig2, ax2 = plt.subplots()
        ax2.plot(E, C, color="green", label="Kurva Produksi (C = aE + bE²)")
        ax2.axvline(Emsy, color="orange", linestyle="--", label=f"E_MSY = {Emsy:.2f}")
        ax2.axhline(MSY, color="red", linestyle="--", label=f"MSY = {MSY:.2f} kg")
        ax2.scatter(df["upaya"], df["tangkapan"], color="blue", label="Data Aktual")
        ax2.set_xlabel("Upaya (trip)")
        ax2.set_ylabel("Tangkapan (kg)")
        ax2.legend()
        st.pyplot(fig2)

        # ------------------------------------------------------
        # Simulasi interaktif
        # ------------------------------------------------------
        st.subheader("🎛 Simulasi Interaktif MSY")
        sim_upaya = st.slider("Atur nilai upaya (trip)", 0.0, float(df["upaya"].max() * 1.5), float(df["upaya"].mean()))
        pred_catch = sim_upaya * (a + b * sim_upaya)
        st.success(f"Prediksi tangkapan pada {sim_upaya:.2f} trip: **{pred_catch:.2f} kg**")

else:
    st.info("Silakan upload file atau input data manual untuk mulai analisis.")


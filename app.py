import streamlit as st
from fpdf import FPDF
from datetime import datetime
import os

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="ST Medikal Panel", layout="centered")

# --- GÜVENLİK (Şifre: ST2025) ---
if "giris" not in st.session_state:
    st.session_state["giris"] = False

if not st.session_state["giris"]:
    st.markdown("## 🔒 ST Medikal Giriş")
    sifre = st.text_input("Şifre:", type="password")
    if st.button("Giriş Yap"):
        if sifre == "ST2025":
            st.session_state["giris"] = True
            st.rerun()
    st.stop()

# --- ANA EKRAN ---
st.title("📄 Proforma Oluşturucu")
st.info("Sistem, yüklediğin 'sablon.png' dosyası üzerine yazacaktır.")

# Girdi Alanları
col1, col2 = st.columns(2)
with col1:
    kurum_adi = st.text_input("Kurum Adı")
    adres = st.text_input("Adres")
    # Ülke şablonda yazılıysa burayı pas geçebilirsin
    # ulke = st.text_input("Ülke", value="TÜRKİYE") 
with col2:
    tarih = st.date_input("Tarih", datetime.now())
    telefon = st.text_input("Telefon")
    para_birimi = st.selectbox("Para Birimi", ["EUR", "USD", "TRY", "GBP"])

st.markdown("---")

# Ürün Listesi
if "urunler" not in st.session_state:
    st.session_state.urunler = [{"adet": 1, "tanim": "", "fiyat": 0.0}]

def satir_ekle(): st.session_state.urunler.append({"adet": 1, "tanim": "", "fiyat": 0.0})
def satir_sil(): 
    if len(st.session_state.urunler) > 1: st.session_state.urunler.pop()

c1, c2 = st.columns([1,1])
c1.button("➕ Satır Ekle", on_click=satir_ekle)
c2.button("➖ Satır Sil", on_click=satir_sil)

toplam_tutar = 0
for i, urun in enumerate(st.session_state.urunler):
    c_a, c_b, c_c = st.columns([1, 3, 2])
    urun['adet'] = c_a.number_input(f"Adet", min_value=1, key=f"adet_{i}", label_visibility="collapsed")
    urun['tanim'] = c_b.text_input(f"Tanım", value=urun['tanim'], key=f"tanim_{i}", label_visibility="collapsed")
    urun['fiyat'] = c_c.number_input(f"Fiyat", value=urun['fiyat'], key=f"fiyat_{i}", label_visibility="collapsed")
    toplam_tutar += urun['adet'] * urun['fiyat']

kdv_orani = st.number_input("KDV Oranı (%)", value=20)
gecerlilik = st.number_input("Geçerlilik (Gün)", value=15)
odeme_vadesi = st.text_input("Ödeme Vadesi", value="PEŞİN")

# --- PDF MOTORU ---
class PDF(FPDF):
    def header(self):
        # Arka plan resmi
        if os.path.exists("sablon.png"):
            self.image("sablon.png", x=0, y=0, w=210, h=297)

def tr_char(text):
    if not text: return ""
    return text.replace('İ', 'I').replace('ı', 'i').replace('ğ', 'g').replace('Ğ', 'G').replace('ş', 's').replace('Ş', 'S').replace('ö', 'o').replace('Ö', 'O').replace('ü', 'u').replace('Ü', 'U').replace('ç', 'c').replace('Ç', 'C')

def create_pdf():
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # 1. BAŞLIKLARI YERLEŞTİR (Koordinatlar)
    
    # Kurum Adı
    pdf.set_xy(45, 62) 
    pdf.cell(100, 5, tr_char(kurum_adi))

    # Adres
    pdf.set_xy(45, 70) 
    pdf.cell(100, 5, tr_char(adres))
    
    # Tarih (Sağda)
    pdf.set_xy(165, 68) 
    pdf.cell(40, 5, tarih.strftime('%d.%m.%Y'))
    
    # Telefon (Ortada)
    pdf.set_xy(115, 80)
    pdf.cell(50, 5, tr_char(telefon))

    # 2. TABLO ÇİZİMİ
    pdf.set_xy(20, 100) # Başlangıç yüksekliği
    
    # Başlıklar (Gri arka plan)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(15, 8, "Adet", 1, 0, 'C', True)
    pdf.cell(105, 8, tr_char("Urun Tanimi"), 1, 0, 'C', True)
    pdf.cell(30, 8, "Birim Fiyat", 1, 0, 'C', True)
    pdf.cell(30, 8, "Toplam", 1, 1, 'C', True)
    
    # Satırlar
    pdf.set_font("Arial", '', 9)
    for u in st.session_state.urunler:
        pdf.cell(15, 8, str(u['adet']), 1, 0, 'C')
        pdf.cell(105, 8, tr_char(u['tanim']), 1, 0, 'L')
        pdf.cell(30, 8, f"{u['fiyat']:.2f}", 1, 0, 'R')
        tutar = u['adet'] * u['fiyat']
        pdf.cell(30, 8, f"{tutar:.2f}", 1, 1, 'R')

    # 3. TOPLAMLAR
    pdf.set_x(140) # Sağa yasla
    pdf.cell(30, 8, "Ara Toplam:", 0, 0, 'R')
    pdf.cell(30, 8, f"{toplam_tutar:.2f} {para_birimi}", 0, 1, 'R')
    
    kdv_tutar = toplam_tutar * (kdv_orani / 100)
    genel = toplam_tutar + kdv_tutar
    
    pdf.set_x(140)
    pdf.cell(30, 8, f"KDV (%{kdv_orani}):", 0, 0, 'R')
    pdf.cell(30, 8, f"{kdv_tutar:.2f} {para_birimi}", 0, 1, 'R')
    
    pdf.set_font("Arial", 'B', 10)
    pdf.set_x(140)
    pdf.cell(30, 8, "GENEL TOPLAM:", 0, 0, 'R')
    pdf.cell(30, 8, f"{genel:.2f} {para_birimi}", 0, 1, 'R')

    # 4. NOTLAR (En alta)
    pdf.set_xy(20, 210) 
    pdf.set_font("Arial", '', 8)
    notlar = (
        f"- Bu belge fatura yerine gecmez.\n"
        f"- Is bu fiyatlar {gecerlilik} gun gecerlidir.\n"
        f"- Fiyatlara %{kdv_orani} KDV eklenecektir.\n"
        f"- Fiyatlar {para_birimi} olarak verilmistir.\n"
        f"- Odeme vadesi: {tr_char(odeme_vadesi)}"
    )
    pdf.multi_cell(0, 5, tr_char(notlar))

    return pdf.output(dest='S').encode('latin-1', 'replace')

if st.button("Şablonlu PDF İndir"):
    data = create_pdf()
    dosya_ismi = f"Proforma_{datetime.now().strftime('%Y%m%d')}.pdf"
    st.download_button("📥 İndir", data=data, file_name=dosya_ismi, mime="application/pdf")

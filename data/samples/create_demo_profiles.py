from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def create_ekstre(dosya_adi, kullanici_adi, hesap_no, donem, gelir, islemler):
    doc = SimpleDocTemplate(f"data/samples/{dosya_adi}", pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("DEMO BANK - Hesap Ekstresi", styles["Title"]))
    elements.append(Paragraph(f"Hesap Sahibi: {kullanici_adi}", styles["Normal"]))
    elements.append(Paragraph(f"Hesap No: {hesap_no}", styles["Normal"]))
    elements.append(Paragraph(f"Donem: {donem}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    data = [["Tarih", "Aciklama", "Tutar (TL)", "Bakiye (TL)"]]
    bakiye = gelir

    for islem in islemler:
        bakiye += islem[2]
        data.append([islem[0], islem[1], f"{islem[2]:+,.2f}", f"{bakiye:,.2f}"])

    table = Table(data, colWidths=[90, 220, 100, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Toplam Gelir: {gelir:,.2f} TL", styles["Normal"]))
    elements.append(Paragraph(f"Donem Sonu Bakiye: {bakiye:,.2f} TL", styles["Normal"]))
    doc.build(elements)
    print(f"Olusturuldu: data/samples/{dosya_adi}")


# ── Profil 1: Ayse — Orta Gelir, Yuksek Kira Yuku ─────────
create_ekstre(
    dosya_adi="ayse_nisan_2026.pdf",
    kullanici_adi="Ayse Yilmaz",
    hesap_no="TR12 0001 0002 0003",
    donem="01.04.2026 - 30.04.2026",
    gelir=28000,
    islemler=[
        ("01.04.2026", "Maas Odemesi", +28000),
        ("02.04.2026", "Kira Odemesi", -10000),
        ("03.04.2026", "Migros Market", -1200),
        ("05.04.2026", "BEDAS Elektrik", -980),
        ("06.04.2026", "IGDAS Dogalgaz", -650),
        ("08.04.2026", "Carrefour Market", -890),
        ("10.04.2026", "Shell Yakit", -1400),
        ("12.04.2026", "Netflix Abonelik", -349),
        ("14.04.2026", "Spotify Abonelik", -99),
        ("15.04.2026", "Eczane", -320),
        ("17.04.2026", "A101 Market", -560),
        ("18.04.2026", "Opet Yakit", -1100),
        ("20.04.2026", "Kafe - Starbucks", -210),
        ("22.04.2026", "Telefon Faturasi", -449),
        ("24.04.2026", "BIM Market", -430),
        ("26.04.2026", "Sinema", -260),
        ("28.04.2026", "Internet Faturasi", -399),
        ("29.04.2026", "ATM Para Cekme", -1000),
    ]
)

# ── Profil 2: Mehmet — Yuksek Gelir, Cok Abonelik ─────────
create_ekstre(
    dosya_adi="mehmet_nisan_2026.pdf",
    kullanici_adi="Mehmet Kaya",
    hesap_no="TR12 0001 0002 0004",
    donem="01.04.2026 - 30.04.2026",
    gelir=65000,
    islemler=[
        ("01.04.2026", "Maas Odemesi", +65000),
        ("02.04.2026", "Kira Odemesi", -18000),
        ("03.04.2026", "Migros Market", -2400),
        ("04.04.2026", "Netflix Abonelik", -349),
        ("04.04.2026", "Spotify Abonelik", -99),
        ("04.04.2026", "Amazon Prime", -299),
        ("04.04.2026", "Apple iCloud", -149),
        ("04.04.2026", "YouTube Premium", -189),
        ("05.04.2026", "BEDAS Elektrik", -2100),
        ("07.04.2026", "Shell Yakit", -2800),
        ("09.04.2026", "Arac Bakim Servisi", -4500),
        ("11.04.2026", "CarrefourSA Market", -1800),
        ("13.04.2026", "Restoran", -1200),
        ("15.04.2026", "Opet Yakit", -2400),
        ("17.04.2026", "Kafe", -450),
        ("19.04.2026", "Netflix Abonelik", -349),
        ("20.04.2026", "Spor Salonu", -800),
        ("22.04.2026", "Hastane", -1500),
        ("24.04.2026", "Telefon Faturasi", -899),
        ("26.04.2026", "Ulasim", -650),
        ("28.04.2026", "Market", -980),
        ("30.04.2026", "ATM Para Cekme", -3000),
    ]
)

# ── Profil 3: Zeynep — Dusuk Tasarruf, Kritik Durum ───────
create_ekstre(
    dosya_adi="zeynep_nisan_2026.pdf",
    kullanici_adi="Zeynep Demir",
    hesap_no="TR12 0001 0002 0005",
    donem="01.04.2026 - 30.04.2026",
    gelir=18000,
    islemler=[
        ("01.04.2026", "Maas Odemesi", +18000),
        ("02.04.2026", "Kira Odemesi", -8500),
        ("03.04.2026", "A101 Market", -780),
        ("05.04.2026", "BEDAS Elektrik", -720),
        ("06.04.2026", "IGDAS Dogalgaz", -480),
        ("08.04.2026", "BIM Market", -620),
        ("10.04.2026", "Otobus Kart Yukleme", -500),
        ("12.04.2026", "Netflix Abonelik", -349),
        ("14.04.2026", "Eczane", -280),
        ("15.04.2026", "Migros Market", -950),
        ("17.04.2026", "Telefon Faturasi", -349),
        ("18.04.2026", "Kafe", -180),
        ("20.04.2026", "Internet Faturasi", -299),
        ("22.04.2026", "Market", -560),
        ("24.04.2026", "Ulasim", -400),
        ("26.04.2026", "Kozmetik", -340),
        ("28.04.2026", "ATM Para Cekme", -500),
        ("29.04.2026", "Kredi Karti Odeme", -2000),
    ]
)

print("\nTum demo profiller olusturuldu.")
print("data/samples/ klasorunu kontrol edin.")
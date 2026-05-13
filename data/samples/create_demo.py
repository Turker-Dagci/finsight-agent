from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def create_demo_statement():
    doc = SimpleDocTemplate("data/samples/demo_ekstre.pdf", pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("DEMO BANK - Hesap Ekstresi", styles["Title"]))
    elements.append(Paragraph("Hesap No: TR12 0001 0002 0003 0004 05", styles["Normal"]))
    elements.append(Paragraph("Dönem: 01.04.2026 - 30.04.2026", styles["Normal"]))
    elements.append(Spacer(1, 20))

    data = [
        ["Tarih", "Açıklama", "Tutar (TL)", "Bakiye (TL)"],
        ["01.04.2026", "Maaş Ödemesi - ABC Şirketi", "+42.000,00", "42.000,00"],
        ["02.04.2026", "Migros Market", "-1.240,50", "40.759,50"],
        ["03.04.2026", "Shell Yakıt İstasyonu", "-1.850,00", "38.909,50"],
        ["04.04.2026", "Netflix Abonelik", "-349,99", "38.559,51"],
        ["05.04.2026", "Spotify Abonelik", "-99,99", "38.459,52"],
        ["07.04.2026", "Carrefour Market", "-980,00", "37.479,52"],
        ["08.04.2026", "BEDAŞ Elektrik Faturası", "-2.340,00", "35.139,52"],
        ["09.04.2026", "İGDAŞ Doğalgaz", "-1.120,00", "34.019,52"],
        ["10.04.2026", "İSKİ Su Faturası", "-380,00", "33.639,52"],
        ["12.04.2026", "Opet Yakıt İstasyonu", "-1.650,00", "31.989,52"],
        ["14.04.2026", "Amazon Prime Abonelik", "-299,99", "31.689,53"],
        ["15.04.2026", "Eczane - İlaç", "-450,00", "31.239,53"],
        ["16.04.2026", "Migros Market", "-1.560,00", "29.679,53"],
        ["18.04.2026", "Kafe - Starbucks", "-285,00", "29.394,53"],
        ["19.04.2026", "Araç Bakım - Servisi", "-3.200,00", "26.194,53"],
        ["20.04.2026", "Netflix Abonelik", "-349,99", "25.844,54"],
        ["21.04.2026", "Bowling Salonu", "-450,00", "25.394,54"],
        ["22.04.2026", "CarrefourSA Market", "-1.890,00", "23.504,54"],
        ["24.04.2026", "Shell Yakıt İstasyonu", "-1.750,00", "21.754,54"],
        ["25.04.2026", "Kira Ödemesi", "-12.000,00", "9.754,54"],
        ["26.04.2026", "Telefon Faturası - Turkcell", "-649,00", "9.105,54"],
        ["28.04.2026", "A101 Market", "-720,00", "8.385,54"],
        ["29.04.2026", "Sinema - CinemaPink", "-380,00", "8.005,54"],
        ["30.04.2026", "ATM Para Çekme", "-2.000,00", "6.005,54"],
    ]

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
    elements.append(Paragraph(f"Dönem Sonu Bakiye: 6.005,54 TL", styles["Normal"]))
    elements.append(Paragraph(f"Toplam Gelir: 42.000,00 TL", styles["Normal"]))
    elements.append(Paragraph(f"Toplam Gider: 35.994,46 TL", styles["Normal"]))

    doc.build(elements)
    print("Demo ekstre oluşturuldu: data/samples/demo_ekstre.pdf")

if __name__ == "__main__":
    create_demo_statement()
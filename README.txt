# FinSight Agent

Çok-Ajanlı KOBİ Finansal Analiz Sistemi

## Stack
- FastAPI · LangGraph · Gemini 2.5 · Qdrant · Streamlit

## Özellikler
- PDF banka ekstresi ve fatura analizi
- Enflasyon düzeltmeli harcama analizi
- Kişisel harcama kategorilendirmesi (Ev, Araç, Aktiviteler)
- Finansal profil tabanlı gelir/gider dengesi
- Görünmez vergi yükü hesaplama (KDV, ÖTV)
- Abonelik dedektörü
- Döviz kalkanı analizi (TCMB API)
- Gelecek ay bütçe tahmini ve yönlendirme
- Proaktif uyarı ajanı

## Kurulum
\`\`\`bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
\`\`\`

## Çalıştırma
\`\`\`bash
# Terminal 1
cd backend && uvicorn main:app --reload

# Terminal 2
streamlit run frontend/app.py
\`\`\`
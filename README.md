# 💰 FinSight Agent

**Türkiye'deki KOBİ'ler ve bireyler için çok-ajanlı yapay zeka destekli finansal analiz sistemi.**

> "Kullanıcılar her ay rakamlarına bakıyor ama gerçekte ne kadar yoksullaştığını göremiyorlar. Biz bunu görünür kılıyoruz."

---

## 🎯 Problem

Türkiye'de yüksek enflasyon ortamında insanlar harcamalarını takip ediyor ama nominal TL rakamlarının arkasındaki gerçek satın alma gücü kaybını göremiyorlar. Harcamalarının içindeki gizli vergi yükünü (KDV, ÖTV) bilmiyorlar. Döviz kurundaki dalgalanmaların bütçelerine gerçek etkisini hesaplayamıyorlar.

---

## ✨ Özellikler

**Çekirdek Analiz**
- PDF Banka Ekstresi Parse — Gemini Vision ile otomatik işlem çıkarma
- Enflasyon Düzeltmesi — TÜİK TÜFE verileriyle nominal → reel değer dönüşümü
- Vergi X-Ray — KDV ve ÖTV gizli yük hesabı (kategori bazlı)
- Anomali Tespiti — Tekrar eden ve olağandışı ödemeler
- Abonelik Dedektörü — Döviz bazlı aboneliklerin TL maliyet artışı

**Akıllı Özellikler**
- Döviz Kalkanı — TCMB canlı kurlarla aylık harcamanın USD/EUR karşılığı
- Finansal Sağlık Skoru — 5 bileşenli 100 üzerinden değerlendirme
- Hedef Odaklı Bütçe — 50/30/20 kuralı ile kişisel hedef analizi
- Senaryo Planlama — "Ya şöyle olursa?" simülasyonu
- Doğal Dil İşlem Girişi — "Kadıköy'de kafede 450 TL ödedim" → otomatik parse
- Proaktif Uyarılar — Kullanıcı sormadan bütçe aşımı bildirimi

**Teknik Altyapı**
- Güvenlik — Rate limiting, prompt injection koruması, magic bytes kontrolü
- Retry Mekanizması — Gemini 503 hatalarında exponential backoff
- Yapılandırılmış Loglama — Her ajan için ayrı log dosyası
- Session Kalıcılığı — Sunucu restart sonrası oturumlar korunur

---

## 🏗️ Teknik Mimari

**Sistem Akışı**

Kullanıcı → FastAPI Backend → LangGraph Orchestrator → Ajan Zinciri → Qdrant Vector DB

**Ajanlar**

- Parser Agent: PDF/görüntü → Gemini Vision → JSON işlemler → Qdrant embedding
- Analyst Agent: Kategorilendirme → Enflasyon → Vergi X-Ray → Anomali → Abonelik
- Subscription Optimizer Agent: Abonelik yükü %15 üzerindeyse dinamik olarak devreye girer
- Advisory Agent: TCMB canlı kur + TÜİK enflasyon + haberler + kullanıcı profili → Kişisel tavsiye

**Dinamik Routing**

LangGraph, Analyst Agent sonucuna göre hangi ajanın devreye gireceğine otomatik karar verir. Bu yapı sistemi gerçek anlamda agentic kılar.

---

## 🛠️ Teknoloji Stack

| Teknoloji | Kullanım |
|---|---|
| Gemini 2.5 Flash | PDF parse, NLP, tavsiye üretimi |
| LangGraph | Çok-ajanlı orkestrasyon, dinamik routing |
| Qdrant Cloud | Vektör veritabanı, semantic search |
| FastAPI | REST API backend |
| Streamlit | Web arayüzü |
| TCMB API | Gerçek zamanlı döviz kurları |

---

## 🚀 Kurulum

**Gereksinimler**
- Python 3.10+
- Gemini API Key — aistudio.google.com
- Qdrant Cloud hesabı — cloud.qdrant.io

**Adımlar**

Repoyu klonla:

    git clone https://github.com/Turker-Dagci/finsight-agent.git
    cd finsight-agent

Virtual environment oluştur:

    python -m venv venv
    venv\Scripts\activate

Bağımlılıkları yükle:

    pip install -r requirements.txt

.env dosyası oluştur ve API key'leri ekle:

    GEMINI_API_KEY=your_gemini_api_key
    QDRANT_URL=your_qdrant_cluster_url
    QDRANT_API_KEY=your_qdrant_api_key
    QDRANT_COLLECTION=finsight_transactions

**Çalıştırma**

Terminal 1 — Backend:

    cd backend
    uvicorn main:app --reload

Terminal 2 — Frontend:

    streamlit run frontend/app.py

Tarayıcıda http://localhost:8501 adresine gidin.

API dokümantasyonu için http://localhost:8000/docs adresini ziyaret edin.

---

## 📡 API Endpoints

| Method | Endpoint | Açıklama |
|---|---|---|
| GET | /health | Sistem durumu |
| POST | /upload | PDF/görüntü yükleme |
| POST | /analyze | Tam ajan zinciri analizi |
| POST | /query | Doğal dil sorgusu |
| POST | /profile | Finansal profil kaydetme |
| POST | /scenario | Senaryo simülasyonu |
| POST | /nlp-transaction | Doğal dil işlem girişi |
| GET | /session/{id} | Oturum verisi |

---

## 🔒 Güvenlik

- Dosya boyutu limiti: 10MB
- Magic bytes kontrolü: Sahte PDF koruması
- Rate limiting: Dakikada 5-20 istek
- Prompt injection koruması: 15 tehlikeli kalıp filtreleme
- Session yönetimi: UUID bazlı kalıcı saklama

---

## 📁 Proje Yapısı

    finsight-agent/
    ├── backend/
    │   ├── agents/
    │   │   ├── parser_agent.py
    │   │   ├── analyst_agent.py
    │   │   ├── advisory_agent.py
    │   │   └── nlp_parser.py
    │   ├── graph/
    │   │   └── workflow.py
    │   ├── utils/
    │   │   ├── gemini.py
    │   │   ├── context_fetcher.py
    │   │   ├── logger.py
    │   │   ├── sanitizer.py
    │   │   ├── health_score.py
    │   │   ├── awareness.py
    │   │   ├── financial_profile.py
    │   │   └── scenario_planner.py
    │   ├── db/
    │   │   └── qdrant_db.py
    │   ├── config.py
    │   └── main.py
    ├── frontend/
    │   └── app.py
    ├── data/
    │   └── samples/
    ├── tests/
    │   └── test_analyst.py
    ├── ARCHITECTURE.md
    ├── README.md
    ├── requirements.txt
    └── .env.example

---

## 👤 Geliştirici

**İrfan Türker Dağcı**
İnönü Üniversitesi — Yazılım Mühendisliği

---

*FinSight Agent — Hackathon 2026*
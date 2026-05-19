# 💰 FinSight Agent

**Türkiye'deki KOBİ'ler ve bireyler için çok-ajanlı yapay zeka destekli finansal analiz sistemi.**

> "Kullanıcılar her ay rakamlarına bakıyor ama gerçekte ne kadar yoksullaştığını göremiyorlar. Biz bunu görünür kılıyoruz."

---

## 🎬 Demo

📹 **[Demo Videosu](#)** *(yakında)*
🌐 **[GitHub](https://github.com/Turker-Dagci/finsight-agent)**

---

## 🎯 Problem

Türkiye'de yüksek enflasyon ortamında insanlar harcamalarını takip ediyor ama şunları göremiyorlar:

- **Satın alma gücü kaybı** — 10.000 TL kira ödüyorum ama bu kiranın reel değeri ne?
- **Gizli vergi yükü** — Harcamalarımın içinde ne kadar KDV ve ÖTV var?
- **Döviz etkisi** — Dolar yükselince bütçem nasıl etkileniyor?
- **Enflasyon farkı** — Kategori bazlı enflasyon nasıl farklılaşıyor?

Global uygulamalar (Copilot, Monarch Money, YNAB) bu soruları yanıtlayamıyor — çünkü Türkiye'ye özgü bir problem.

---

## ✨ Özellikler

### 🔍 Çekirdek Analiz

**Enflasyon Düzeltmesi**
Harcamalarınızı TÜİK TÜFE verileriyle kategori bazlı düzeltiyor. Nominal TL rakamlarının arkasındaki gerçek satın alma gücü kaybını gösteriyor. Kira için %89.3, fatura için %78.4, ulaşım için %61.2 gibi kategori bazlı enflasyon oranları uygulanıyor.

**Vergi X-Ray**
Her harcama kategorisindeki gizli KDV ve ÖTV yükünü hesaplıyor. "Bu ay 20.296 TL harcadınız ama bunun 2.470 TL'si devlete vergi olarak gitti" gibi somut bulgular sunuyor.

**Döviz Kalkanı**
TCMB'nin gerçek zamanlı API'sinden alınan kurlarla aylık harcamanızın USD ve EUR karşılığını gösteriyor. Döviz kurundaki değişimlerin bütçenize etkisini anlık takip edebiliyorsunuz.

**Anomali Tespiti**
Tekrar eden ve olağandışı ödemeleri otomatik tespit ediyor. Aynı dönemde iki kez çekilen abonelikler, beklenmedik büyük harcamalar işaretleniyor.

**Abonelik Dedektörü**
Tüm abonelikleri listeler, döviz bazlı olanları işaretler ve toplam aylık yükü hesaplar. Kullanılmayan abonelikleri iptal etmeniz durumundaki tasarrufu gösteriyor.

### 🧠 Akıllı Özellikler

**Finansal Sağlık Skoru**
5 bileşenden oluşan 100 üzerinden değerlendirme: tasarruf oranı, enflasyon direnci, abonelik yükü, anomali durumu ve bütçe dengesi. Gauge chart ile görsel sunum.

**Aylık Sade Dil Özeti**
Copilot tarzı, teknik terim içermeyen aylık özet. "Bu ay 28.000 TL gelirin oldu ve 7.704 TL tasarruf etmeyi başardın — harika bir performans" gibi arkadaşça bir anlatımla.

**Finansal Bilinçlendirme Mesajları**
Kullanıcının profiline ve analizine göre bağlamsal ipuçları. Abonelik yükü yüksekse abonelik mesajı, enflasyon etkisi büyükse enflasyon mesajı gösteriyor.

**Davranışsal Koçluk**
Harcama alışkanlıklarını analiz ediyor. "Bu ay ATM'den 1.000 TL nakit çekildi — nakit harcamalar takip edilemiyor" veya "Hafta sonlarında harcamanın %45'i gerçekleşiyor" gibi davranışsal içgörüler sunuyor.

**Proaktif Uyarılar**
Kullanıcı sormadan kritik durumları bildiriyor. Kira oranı gelirin %35'ini aşınca, tasarruf oranı %10'un altına düşünce, yüksek enflasyonlu kategorilerde büyük harcama olunca otomatik uyarı üretiyor.

**Senaryo Planlama**
"Ya şöyle olursa?" simülasyonu. Aylık 5.000 TL tatil harcaması 3 ay boyunca bütçemi nasıl etkiler? Tasarruf hedefime ulaşmam kaç ay gecikir? Somut rakamlarla yanıtlıyor.

**Doğal Dil İşlem Girişi**
PDF olmadan da işlem girebiliyorsunuz. "Dün Kadıköy'de kafede 450 TL ödedim" yazın — tarih, tutar, kategori ve yer otomatik çıkarılıyor, analize anlık yansıtılıyor.

**Öngörülen Giderler**
Abonelik tarihleri ve sabit giderlerden yola çıkarak önümüzdeki 30 günün beklenen giderlerini listeler. "1 Haziran — Kira Ödemesi — 10.000 TL" gibi.

**30 Günlük Nakit Akış Tahmini**
Mevcut harcama hızına ve öngörülen giderlere göre ay sonu bakiye tahmini ve günlük harcama limiti hesaplar.

**Öğrenen Kategori Sistemi**
Kullanıcı yanlış kategorize edilen işlemi düzelttiğinde sistem Qdrant'a kaydediyor. Bir sonraki analizde benzer işlemler otomatik doğru kategorize ediliyor.

**Finansal Profil ve Hedefler**
Gelir, yatırım (döviz, altın, vadeli birikim), borç ve nakit bilgilerini girerek net servet hesaplıyor. Yatırım getirileri BIST100 ve TCMB verilerinden alınıyor. Finansal hedefler için sürdürülebilirlik analizi yapıyor.

**Günlük Piyasa Verileri**
TCMB'den anlık döviz kurları, Yahoo Finance'den BIST100 aylık getirisi, TCMB politika faizini gerçek zamanlı çekiyor.

### 🔒 Güvenlik ve Altyapı

- Rate limiting: dakikada 5-20 istek sınırı
- Prompt injection koruması: 15+ tehlikeli kalıp filtreleme
- Magic bytes kontrolü: sahte PDF koruması
- Session yönetimi: UUID bazlı, sunucu restart sonrası korunur
- Exponential backoff: Gemini 503 hatalarında otomatik yeniden deneme
- Yapılandırılmış loglama: her ajan için ayrı log dosyası

---

## 🏗️ Teknik Mimari

### Ajan Zinciri

```
Kullanıcı (Streamlit UI)
         ↓
   FastAPI Backend
         ↓
  LangGraph Orchestrator
    ↙         ↓         ↘
Parser      Analyst    [Dinamik Routing]
Agent       Agent            ↓
  ↓           ↓      Subscription    Advisory
Gemini    Enflasyon   Optimizer      Agent
Vision    Vergi         Agent      Gemini +
PDF→JSON  Anomali              TCMB + BIST
  ↓       Abonelik                   ↓
Qdrant    Davranış              Kişisel Tavsiye
Vector DB  Koçluk
```

### Parser Agent
PDF veya görüntü dosyasını Gemini Vision ile okur. JSON formatında işlem listesi çıkarır. Prompt injection ve magic bytes kontrolü uygular. İşlemleri Gemini Embedding ile vektörleştirip Qdrant'a kaydeder.

### Analyst Agent
5 modül sırayla çalışır: Kategorilendirme → Enflasyon Düzeltmesi → Vergi X-Ray → Anomali Tespiti → Abonelik Dedektörü → Davranışsal Koçluk → Finansal Sağlık Skoru.

### Dinamik Routing
LangGraph, Analyst Agent sonucuna göre hangi ajanın devreye gireceğine otomatik karar verir. Abonelik yükü gelirin %15'ini aşarsa Subscription Optimizer Agent devreye girer. Bu yapı sistemi gerçek anlamda agentic kılar.

### Subscription Optimizer Agent
Abonelik yükü yüksek olduğunda dinamik olarak devreye girer. Hangi aboneliklerin iptal edilmesinin en büyük tasarrufu sağlayacağını hesaplar.

### Advisory Agent
TCMB canlı döviz kurları, TÜİK enflasyon verileri, BIST100 güncel performansı ve ekonomik haberlerle zenginleştirilmiş bağlam üzerinde Gemini ile kişisel tavsiye üretir. Zorunlu harcamaları (kira, fatura, gıda) kesinlikle kısmayı önermez — sadece esnek harcamalara odaklanır.

---

## 🛠️ Teknoloji Stack

| Teknoloji | Versiyon | Kullanım |
|---|---|---|
| Gemini API | 2.5 Flash | PDF parse, NLP, embedding, tavsiye |
| LangGraph | Latest | Çok-ajanlı orkestrasyon, dinamik routing |
| Qdrant Cloud | v1.17 | Vektör veritabanı, kategori öğrenme |
| FastAPI | Latest | REST API backend |
| Streamlit | Latest | Web arayüzü |
| TCMB API | - | Gerçek zamanlı döviz kurları |
| Yahoo Finance | yfinance | BIST100 aylık getiri |
| slowapi | - | Rate limiting |

---

## 🚀 Kurulum

### Gereksinimler
- Python 3.10+
- Gemini API Key — aistudio.google.com
- Qdrant Cloud hesabı — cloud.qdrant.io

### Adımlar

```bash
git clone https://github.com/Turker-Dagci/finsight-agent.git
cd finsight-agent

python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

`.env` dosyası oluşturun:

```
GEMINI_API_KEY=your_gemini_api_key
QDRANT_URL=your_qdrant_cluster_url
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=finsight_transactions
```

### Çalıştırma

Terminal 1 — Backend:

    cd backend
    uvicorn main:app --reload

Terminal 2 — Frontend:

    streamlit run frontend/app.py

Tarayıcıda http://localhost:8501 adresine gidin.
API dokümantasyonu: http://localhost:8000/docs

---

## 📡 API Endpoints

| Method | Endpoint | Açıklama |
|---|---|---|
| GET | /health | Sistem durumu |
| POST | /upload | PDF/görüntü yükleme (maks 10MB) |
| POST | /analyze | Tam 4-ajan zinciri analizi |
| POST | /query | Doğal dil sohbet sorgusu |
| POST | /profile | Finansal profil ve hedef kaydetme |
| POST | /scenario | Harcama senaryosu simülasyonu |
| POST | /nlp-transaction | Doğal dil işlem girişi |
| POST | /correct-category | Kategori düzeltme ve öğrenme |
| GET | /session/{id} | Oturum verisi |

---

## 📁 Proje Yapısı

    finsight-agent/
    ├── backend/
    │   ├── agents/
    │   │   ├── parser_agent.py       # Gemini Vision PDF parse
    │   │   ├── analyst_agent.py      # 6 modüllü analiz motoru
    │   │   ├── advisory_agent.py     # Piyasa bağlamlı tavsiye
    │   │   └── nlp_parser.py         # Doğal dil işlem girişi
    │   ├── graph/
    │   │   └── workflow.py           # LangGraph orkestrasyon
    │   ├── utils/
    │   │   ├── gemini.py             # Gemini istemcisi + retry
    │   │   ├── context_fetcher.py    # TCMB, BIST, enflasyon
    │   │   ├── health_score.py       # Finansal sağlık skoru
    │   │   ├── awareness.py          # Bilinçlendirme mesajları
    │   │   ├── financial_profile.py  # Profil ve bütçe planı
    │   │   ├── scenario_planner.py   # Senaryo simülasyonu
    │   │   ├── monthly_summary.py    # Aylık sade dil özeti
    │   │   ├── predicted_expenses.py # Öngörülen giderler
    │   │   ├── cashflow_forecast.py  # Nakit akış tahmini
    │   │   ├── category_learning.py  # Öğrenen kategori sistemi
    │   │   ├── logger.py             # Yapılandırılmış loglama
    │   │   └── sanitizer.py          # Güvenlik filtreleri
    │   ├── db/
    │   │   └── qdrant_db.py          # Qdrant bağlantısı
    │   ├── config.py                 # Merkezi yapılandırma
    │   └── main.py                   # FastAPI uygulaması
    ├── frontend/
    │   └── app.py                    # 6 sayfalı Streamlit UI
    ├── data/
    │   └── samples/                  # Demo PDF profilleri
    ├── tests/
    │   └── test_analyst.py           # 11 unit test
    ├── ARCHITECTURE.md               # Teknik mimari detayları
    ├── README.md
    ├── requirements.txt
    └── .env.example

---

## 🧪 Testler

```bash
python -m pytest tests/test_analyst.py -v
```

11 unit test — kategorilendirme, enflasyon hesabı, vergi X-Ray, anomali tespiti, abonelik dedektörü.

---

## 🔒 Güvenlik

- Dosya boyutu limiti: 10MB
- Magic bytes kontrolü: sahte PDF engelleme
- Rate limiting: dakikada 5-20 istek
- Prompt injection: 15+ tehlikeli kalıp filtreleme
- Session yönetimi: UUID bazlı kalıcı saklama
- Hassas dosya koruması: .env git geçmişinden temizlendi

---

## 🗺️ Roadmap

Mevcut sürümde tek dönem analizi destekleniyor. Gelecek sürümler için planlar:

- Çok dönemli analiz: 3-6 aylık ekstre karşılaştırması
- Aile/çift modu: ortak bütçe yönetimi
- Open Banking entegrasyonu: banka API bağlantısı
- Mobil uygulama
- Fatura müzakeresi önerileri

---

## 👤 Geliştirici

**İrfan Türker Dağcı**
İnönü Üniversitesi — Yazılım Mühendisliği 2. Sınıf
**Nihat Burak Eraslan**
İnönü Üniversitesi — Yazılım Mühendisliği 2. Sınıf
**Samet Çakmak**
İnönü Üniversitesi — Bilgisayar Mühendisliği 3. Sınıf
---

*FinSight Agent — Hackathon 2026*

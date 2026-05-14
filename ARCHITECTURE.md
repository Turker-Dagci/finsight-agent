# FinSight Agent — Teknik Mimari Dökümanı

## Proje Özeti

FinSight, Türkiye'deki KOBİ'ler ve bireyler için
geliştirilmiş çok-ajanlı yapay zeka destekli finansal
analiz sistemidir.

Temel fark: Türkiye'ye özel enflasyon düzeltmesi,
gizli vergi hesabı ve gerçek zamanlı TCMB verileriyle
çalışan ilk finansal analiz ajanı.

---

## Sistem Akışı

    Kullanıcı (Streamlit)
           │
           ▼ HTTP/REST
      FastAPI Backend
           │
           ▼
     LangGraph Orchestrator
           │
     ┌─────┴─────┐
     ▼           ▼
  Parser      Analyst
  Agent        Agent
     │           │
  Gemini     Enflasyon
  Vision     Vergi X-Ray
  PDF→JSON   Anomali
     │           │
     └─────┬─────┘
           │
     [Dinamik Routing]
      ┌────┴────┐
      ▼         ▼
Subscription  Advisory
Optimizer     Agent
Agent            │
             Gemini +
             TCMB API +
             Haberler
                 │
                 ▼
          Kullanıcı Yanıtı

---

## Ajan Mimarisi

### 1. Parser Agent

Görev: Ham belge → Yapılandırılmış veri

Akış:
- PDF veya görüntü dosyası alır
- Gemini Vision API ile içeriği okur
- JSON formatında işlem listesi üretir
- Her işlemi 768 boyutlu vektöre çevirir
- Qdrant vektör veritabanına yazar

Neden ayrı ajan?
Hata izolasyonu sağlar. PDF parse başarısız
olursa analiz katmanı etkilenmez. Ayrıca
bağımsız test edilebilir.

---

### 2. Analyst Agent

Görev: İşlem listesi → Çok katmanlı analiz

Beş modül sırayla çalışır:

Kategorilendirme
- Gıda, ulaşım, fatura, eğlence, sağlık, kira

Enflasyon Düzeltmesi
- TÜİK TÜFE verileri kategori bazlı uygulanır
- Nominal TL → Reel satın alma gücü dönüşümü
- Örnek: Kiraya 12.000 TL ödendi, reel değer
  11.299 TL — 701 TL satın alma gücü kaybı

Vergi X-Ray
- Her kategoriye KDV ve ÖTV oranı uygulanır
- Toplam gizli vergi yükü hesaplanır
- Örnek: 35.994 TL harcamada 4.230 TL vergi

Anomali Tespiti
- Aynı açıklamalı tekrar eden ödemeler
- Olağandışı tutar hareketleri

Abonelik Dedektörü
- Netflix, Spotify, Amazon gibi servisler
- Döviz bazlı olanlar işaretlenir

---

### 3. Subscription Optimizer Agent (Dinamik)

Görev: Abonelik yükü analizi ve tasarruf önerileri

Ne zaman devreye girer?
Abonelik giderleri toplam harcamanın yüzde
onbeşini geçtiğinde Analyst Agent'tan sonra
otomatik olarak çalışır.

Ne üretir?
- Döviz bazlı aboneliklerin TL maliyet artışı
- İptal önerileri
- Aylık tasarruf potansiyeli

---

### 4. Advisory Agent

Görev: Tüm analiz + piyasa bağlamı → Kişisel tavsiye

Veri kaynakları:
- Parser ve Analyst çıktıları
- TCMB API gerçek zamanlı döviz kurları
- TÜİK TÜFE kategori bazlı enflasyon
- Güncel ekonomi haberleri
- Kullanıcı finansal profili

Ürettiği çıktılar:
- Döviz Kalkanı analizi
- Proaktif bütçe uyarıları
- Gemini destekli kişisel finansal tavsiye
- Finansal bilinçlendirme notu

---

## Dinamik Routing Mantığı

LangGraph'ta route_after_analyst fonksiyonu
Analyst sonucuna göre hangi ajanın çalışacağına
karar verir:

Abonelik oranı yüzde onbeşi geçiyorsa
→ Subscription Optimizer devreye girer
→ Sonra Advisory'e geçer

Anomali sayısı ikiden fazlaysa
→ Direkt Advisory'e geçer

Normal akışta
→ Direkt Advisory'e geçer

Bu yapı sistemi gerçek anlamda agentic kılıyor.
Kullanıcının verisine göre farklı ajan zincirleri
çalışıyor, statik bir sıra yok.

---

## Teknoloji Kararları

### LangGraph — Orkestrasyon

Basit fonksiyon çağrısı yerine LangGraph:
- Hata izolasyonu: Bir ajan çökerse diğerleri çalışır
- Dinamik routing: Veriye göre farklı ajan seçimi
- State yönetimi: Ajanlar ortak TypedDict üzerinde çalışır
- Genişletilebilirlik: Yeni ajan = yeni node + edge

### Qdrant — Vektör Veritabanı

Normal SQL yerine Qdrant:
- Semantic search: "Gıda harcaması" sorgusu
  kelime değil anlam eşleştirmesiyle çalışır
- Cosine distance: Tutar büyüklüğünden bağımsız,
  harcama türüne göre eşleştirme
- Açık kaynak, Türkiye erişiminde sorun yok

### Gemini — Dil Modeli

- Hackathon zorunluluğu ve Vision desteği
- Tek model: Hem PDF parse hem metin üretimi
- gemini-2.5-flash: Hız ve kalite dengesi optimal
- System prompt ile FinSight bağlamında kilitli

### FastAPI — Backend

- Streamlit ve LangGraph arası REST köprüsü
- Pydantic ile otomatik tip doğrulama
- Swagger UI ile endpoint testi
- Gelecekte farklı frontend eklenebilir

---

## Vektör Veritabanı Tasarımı

Koleksiyon: finsight_transactions
Vektör boyutu: 768
Mesafe: Cosine Similarity
Model: gemini-embedding-001

Payload alanları:
- session_id: Oturum kimliği
- user_id: Kullanıcı kimliği (finansal hafıza)
- tarih: İşlem tarihi
- aciklama: İşlem açıklaması
- tutar: Tutar (float)
- tur: gelir veya gider
- kategori: Harcama kategorisi
- donem: Ekstre dönemi

Neden 768 boyut?
Gemini embedding-001 varsayılan olarak 3072
boyut üretiyor. output_dimensionality parametresi
ile 768'e kıstık. Finansal işlem açıklamaları
kısa metinler — 3072 boyut overkill, 768 anlam
kalitesi ve depolama maliyeti arasında optimal.

---

## Güvenlik Katmanı

Input Validation
- Dosya uzantısı kontrolü: pdf, png, jpg, jpeg
- Magic bytes kontrolü: PDF için ilk 4 byte %PDF
- Boyut limiti: Maksimum 10MB

Rate Limiting
- Dakikada 10 istek (slowapi)

Session Yönetimi
- UUID bazlı oturum kimlikleri
- JSON dosyasında kalıcı saklama
- Sunucu restart sonrası oturumlar korunur

Logging
- Her ajan için ayrı logger
- Dosya ve konsol çıktısı
- Günlük log rotasyonu

---

## Retry Mekanizması

Gemini 503 veya 429 hatasında:
- 1. deneme başarısız → 1 saniye bekle
- 2. deneme başarısız → 2 saniye bekle
- 3. deneme başarısız → 4 saniye bekle
- Tüm denemeler başarısız → kullanıcıya
  anlaşılır hata mesajı döner, sistem çökmez

---

## Proje Yapısı

    finsight-agent/
    ├── backend/
    │   ├── agents/
    │   │   ├── parser_agent.py
    │   │   ├── analyst_agent.py
    │   │   └── advisory_agent.py
    │   ├── graph/
    │   │   └── workflow.py
    │   ├── utils/
    │   │   ├── gemini.py
    │   │   ├── context_fetcher.py
    │   │   └── logger.py
    │   ├── db/
    │   │   └── qdrant_db.py
    │   ├── config.py
    │   └── main.py
    ├── frontend/
    │   └── app.py
    ├── data/
    │   └── samples/
    ├── tests/
    ├── logs/
    ├── ARCHITECTURE.md
    └── README.md
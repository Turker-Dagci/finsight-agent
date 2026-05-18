import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="FinSight Agent",
    page_icon="💰",
    layout="wide"
)

st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .metric-label { font-size: 13px !important; color: #8b9dc3 !important; }
    .metric-value { font-size: 24px !important; font-weight: 600 !important; }
    .awareness-box {
        background: linear-gradient(135deg, #1a2744, #1e3a5f);
        border-left: 4px solid #2e75b6;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 12px 0;
        font-size: 14px;
        color: #c9d8f0;
    }
    .stButton button {
        background: linear-gradient(135deg, #1e3a5f, #2e75b6);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("💰 FinSight Agent")
    st.caption("Çok-Ajanlı KOBİ Finansal Analiz Sistemi")
    st.divider()
    page = st.radio(
        "Sayfa",
        ["📤 Ekstre Yükle", "📊 Analiz", "💬 Sohbet",
         "🎯 Profil & Hedefler", "🔮 Senaryo", "📝 Günlük İşlem Ekle"]
    )
    st.divider()
    if "session_id" in st.session_state:
        st.success("Aktif oturum")
        st.caption(f"ID: {st.session_state['session_id'][:8]}...")
    st.divider()
    st.caption("Gemini 2.5 · LangGraph · Qdrant")
    st.caption("FastAPI · Streamlit")

# Sayfa 1: Yükleme
if page == "📤 Ekstre Yükle":
    st.title("📤 Banka Ekstresi Yükle")
    st.caption("PDF veya görüntü formatında banka ekstresi yükleyin.")

    uploaded = st.file_uploader("Dosya seçin", type=["pdf", "png", "jpg", "jpeg"])

    if uploaded:
        st.success(f"✅ {uploaded.name}")
        query = st.text_input(
            "Analiz sorusu",
            value="Bu ay nasıl harcadım ve önümüzdeki ay ne yapmalıyım?"
        )

        if st.button("🚀 Analizi Başlat", type="primary"):
            with st.spinner("📤 Dosya yükleniyor..."):
                files = {"file": (uploaded.name, uploaded.getvalue())}
                upload_resp = requests.post(f"{API_URL}/upload", files=files)
                if upload_resp.status_code != 200:
                    st.error(f"Yükleme hatası: {upload_resp.text}")
                    st.stop()
                session_id = upload_resp.json()["session_id"]
                st.session_state["session_id"] = session_id

            with st.spinner("🤖 Ajanlar analiz ediyor... (30-60 saniye)"):
                analyze_resp = requests.post(
                    f"{API_URL}/analyze",
                    params={"session_id": session_id, "query": query},
                    timeout=180
                )
                if analyze_resp.status_code != 200:
                    st.error(f"Analiz hatası: {analyze_resp.text}")
                    st.stop()
                result = analyze_resp.json()
                st.session_state["result"] = result

            st.success("✅ Analiz tamamlandı!")
            st.balloons()
            st.info("Sol menüden 'Analiz' sayfasına geçin.")

# Sayfa 2: Analiz
elif page == "📊 Analiz":
    st.title("📊 Finansal Analiz")

    if "result" not in st.session_state:
        st.warning("Henüz analiz yapılmadı. Önce ekstre yükleyin.")
        st.stop()

    result = st.session_state["result"]
    summary = result.get("parsed_summary", {}) or {}
    categories = result.get("categories", {}) or {}
    health = result.get("health_score", {}) or {}
    awareness = result.get("awareness_message", "")
    monthly = result.get("monthly_summary", "")

    # Aylık özet
    if monthly:
        st.info(f"📅 **Bu Ayın Özeti:** {monthly}")

    # Bilinçlendirme mesajı
    if awareness:
        st.markdown(f'<div class="awareness-box">{awareness}</div>', unsafe_allow_html=True)

    # Özet metrikler
    gelir = summary.get("toplam_gelir") or 0
    gider = abs(summary.get("toplam_gider") or 0)
    net = gelir - gider
    vergi = result.get("tax_total") or 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Toplam Gelir", f"{gelir:,.0f} TL")
    col2.metric("Toplam Gider", f"{gider:,.0f} TL")
    col3.metric("Net Tasarruf", f"{net:,.0f} TL",
                delta=f"%{net/gelir*100:.1f}" if gelir > 0 else None)
    col4.metric("Vergi Yükü (KDV+ÖTV)", f"{vergi:,.0f} TL" if vergi > 0 else "Hesaplanıyor...")

    st.divider()

    # Sağlık skoru + kategoriler
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("🏥 Finansal Sağlık")
        if health:
            skor = health.get("toplam_skor", 0)
            seviye = health.get("seviye", "")
            mesaj = health.get("mesaj", "")

            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=skor,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": seviye, "font": {"size": 16}},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#2e75b6"},
                    "steps": [
                        {"range": [0, 30], "color": "#3d1a1a"},
                        {"range": [30, 50], "color": "#3d2e1a"},
                        {"range": [50, 70], "color": "#2e3d1a"},
                        {"range": [70, 85], "color": "#1a3d2e"},
                        {"range": [85, 100], "color": "#1a2e3d"},
                    ],
                    "threshold": {
                        "line": {"color": "#ffffff", "width": 2},
                        "thickness": 0.75,
                        "value": skor
                    }
                }
            ))
            fig_gauge.update_layout(
                height=220,
                margin=dict(t=30, b=10, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="white"
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
            st.caption(mesaj)

            bilesenler = health.get("bilesenler", {})
            detay = health.get("detay", {})
            for k, v in bilesenler.items():
                st.caption(f"{k.capitalize()}: {v} puan — {detay.get(k, '')}")

    with col_right:
        st.subheader("📊 Harcama Dağılımı")
        if categories:
            df = pd.DataFrame(
                list(categories.items()),
                columns=["Kategori", "Tutar (TL)"]
            ).sort_values("Tutar (TL)", ascending=False)

            fig = px.bar(
                df, x="Kategori", y="Tutar (TL)",
                color="Tutar (TL)",
                color_continuous_scale="Blues",
            )
            fig.update_layout(
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                showlegend=False,
                margin=dict(t=10, b=40, l=40, r=10)
            )
            st.plotly_chart(fig, use_container_width=True)

        # Kategori düzeltme
        with st.expander("✏️ Kategori Düzelt"):
            st.caption("Yanlış kategorize edilen işlemi düzeltin, sistem öğrenir.")
            col_k1, col_k2, col_k3 = st.columns(3)
            islem_adi = col_k1.text_input("İşlem adı", placeholder="Shell Yakıt")
            eski_kat = col_k2.selectbox(
                "Mevcut kategori",
                ["gida", "ulasim", "fatura", "eglence", "saglik", "kira", "diger"]
            )
            yeni_kat = col_k3.selectbox(
                "Doğru kategori",
                ["gida", "ulasim", "fatura", "eglence", "saglik", "kira", "diger"],
                index=1
            )
            if st.button("💾 Düzeltmeyi Kaydet"):
                if islem_adi:
                    resp = requests.post(
                        f"{API_URL}/correct-category",
                        json={
                            "aciklama": islem_adi,
                            "eski_kategori": eski_kat,
                            "yeni_kategori": yeni_kat
                        }
                    )
                    if resp.status_code == 200:
                        st.success("✅ Sistem bu düzeltmeyi öğrendi!")
                else:
                    st.warning("İşlem adı girin.")

    st.divider()

    # Döviz kalkanı
    fx = result.get("fx_shield", {}) or {}
    if fx:
        st.subheader("💱 Döviz Kalkanı")
        c1, c2, c3 = st.columns(3)
        c1.metric("Aylık Gider", f"{fx.get('aylik_gider_tl', 0):,.0f} TL")
        c2.metric("USD Karşılığı", f"{fx.get('aylik_gider_usd', 0):,.0f} $")
        c3.metric("EUR Karşılığı", f"{fx.get('aylik_gider_eur', 0):,.0f} €")

    st.divider()

    # Piyasa verileri
    st.divider()
    st.subheader("📈 Güncel Piyasa Verileri")

    market_col1, market_col2, market_col3, market_col4 = st.columns(4)
    market_col1.metric("USD/TL", f"{result.get('fx_shield', {}).get('usd_kur', 0):,.2f} TL")
    market_col2.metric("EUR/TL", f"{result.get('fx_shield', {}).get('eur_kur', 0):,.2f} TL")
    market_col3.metric("BIST100 Aylık", f"%{result.get('bist_aylik', 0):,.1f}")
    market_col4.metric("Mevduat Faizi", f"%{result.get('mevduat_faizi', 0):,.1f}")

    # Öngörülen giderler
    predicted = result.get("predicted_expenses", {}) or {}
    if predicted and predicted.get("tahminler"):
        st.subheader("📅 Önümüzdeki 30 Gün — Beklenen Giderler")
        st.caption(f"Toplam beklenen: {predicted.get('toplam', 0):,.0f} TL")
        for t in predicted.get("tahminler", []):
            renk = "🔴" if t["tur"] == "zorunlu" else "🟡"
            st.markdown(
                f"{renk} **{t['tarih']}** — {t['aciklama']} — **{t['tutar']:,.0f} TL**"
            )

    st.divider()

    # Nakit akış tahmini
    cashflow = result.get("cashflow_forecast", {}) or {}
    if cashflow:
        st.subheader("💵 30 Günlük Nakit Akış Tahmini")
        renk_fn = {
            "success": st.success,
            "warning": st.warning,
            "error": st.error
        }.get(cashflow.get("risk_renk", "warning"), st.info)
        renk_fn(cashflow.get("risk_mesaj", ""))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Mevcut Nakit", f"{cashflow.get('mevcut_nakit', 0):,.0f} TL")
        c2.metric("Ay Sonu Tahmini", f"{cashflow.get('ay_sonu_tahmini', 0):,.0f} TL")
        c3.metric("Günlük Limit", f"{cashflow.get('gunluk_guvenli_limit', 0):,.0f} TL/gün")
        c4.metric("Kalan Gün", f"{cashflow.get('ayin_kalan_gunu', 0)} gün")

    st.divider()

    # Uyarılar ve anomaliler
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("⚠️ Proaktif Uyarılar")
        alerts = result.get("proactive_alerts", []) or []
        if alerts:
            for a in alerts:
                st.warning(a)
        else:
            st.success("Kritik uyarı yok.")

    with col_b:
        st.subheader("🔍 Anomaliler")
        anomalies = result.get("anomalies", []) or []
        if anomalies:
            for a in anomalies:
                st.error(a)
        else:
            st.success("Anomali tespit edilmedi.")

    st.divider()

    # Davranışsal koçluk
    insights = result.get("behavioral_insights", []) or []
    if insights:
        st.subheader("🧠 Davranışsal Analiz")
        for i in insights:
            st.info(i)

    st.divider()

    # Gemini tavsiyesi
    st.subheader("🤖 FinSight Tavsiyesi")
    final = result.get("final_response", "")
    if final and final != "Analiz geçici olarak kullanılamıyor. Lütfen tekrar deneyin.":
        st.markdown(final)
    elif final:
        st.warning(final)
        st.info("Sohbet sayfasından 'Genel analiz yap' yazarak yeniden tavsiye alabilirsiniz.")
    else:
        st.info("Tavsiye almak için Sohbet sayfasına gidin ve bir soru sorun.")

# Sayfa 3: Sohbet
elif page == "💬 Sohbet":
    st.title("💬 FinSight ile Sohbet")

    if "session_id" not in st.session_state:
        st.warning("Önce ekstre yükleyin.")
        st.stop()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Sor: 'Bu ay aboneliklerimi azaltırsam ne tasarruf ederim?'"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analiz ediliyor..."):
                resp = requests.post(
                    f"{API_URL}/query",
                    json={"session_id": st.session_state["session_id"], "query": prompt},
                    timeout=60
                )
                answer = resp.json().get("response", "Yanıt alınamadı.")
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

# Sayfa 4: Profil & Hedefler
elif page == "🎯 Profil & Hedefler":
    st.title("🎯 Finansal Profil & Hedefler")

    if "session_id" not in st.session_state:
        st.warning("Önce ekstre yükleyin.")
        st.stop()

    st.subheader("Profiliniz")
    col1, col2 = st.columns(2)

    with col1:
        gelir_kaynak = st.selectbox(
            "Gelir Kaynağı",
            ["Maaş", "Serbest Meslek", "Emekli", "Kira Geliri", "Diğer"]
        )
        aylik_gelir = st.number_input("Aylık Net Gelir (TL)", min_value=0, value=0, step=500)
        ek_gelir_ad = st.text_input("Ek Gelir Kaynağı", placeholder="Freelance, kira vb.")
        ek_gelir_tutar = st.number_input("Ek Gelir Tutarı (TL/ay)", min_value=0, value=0, step=500)

    with col2:
        borc_tutar = st.number_input("Toplam Borç (TL)", min_value=0, value=0, step=1000)
        yatirim_var = st.radio("Yatırımınız var mı?", ["Hayır", "Evet"], horizontal=True)

        yatirim_listesi = []
        yatirimlar_str = "Yok"
        toplam_yatirim = 0

        if yatirim_var == "Evet":
            st.caption("Her yatırım türü için ayrı tutar girin.")
            YATIRIM_TURLERI = ["Döviz (USD/EUR)", "Altın", "Hisse Senedi", "Mevduat"]
            for tur in YATIRIM_TURLERI:
                col_y1, col_y2 = st.columns([2, 3])
                with col_y1:
                    secili = st.checkbox(tur, key=f"yatirim_cb_{tur}")
                with col_y2:
                    if secili:
                        tutar = st.number_input(
                            f"{tur} (TL)",
                            min_value=0, value=0, step=5000,
                            key=f"yatirim_tutar_{tur}"
                        )
                        if tutar > 0:
                            yatirim_listesi.append({"tur": tur, "tutar": tutar})
                            toplam_yatirim += tutar
            if yatirim_listesi:
                st.caption("Seçilen yatırımlar:")
                for y in yatirim_listesi:
                    st.markdown(f"• **{y['tur']}**: {y['tutar']:,.0f} TL")
                yatirimlar_str = ", ".join([y['tur'] for y in yatirim_listesi])

        birikim_tutar = st.number_input("Faizli/Vadeli Birikim (TL)", min_value=0, value=0, step=1000)
        nakit_tutar = st.number_input("Nakit/Vadesiz Hesap (TL)", min_value=0, value=0, step=1000)

    st.subheader("Finansal Hedefleriniz")
    st.caption("En fazla 3 hedef ekleyebilirsiniz.")

    hedefler = []
    for i in range(3):
        with st.expander(f"Hedef {i+1}", expanded=(i == 0)):
            ad = st.text_input(
                "Hedef adı",
                placeholder="Yurt dışı tatil, acil fon, yeni araba...",
                key=f"hedef_ad_{i}"
            )
            col_h1, col_h2, col_h3 = st.columns(3)
            tutar = col_h1.number_input("Hedef Tutar (TL)", min_value=0, value=0, step=1000, key=f"hedef_tutar_{i}")
            butce = col_h2.number_input("Aylık Bütçe (TL)", min_value=0, value=0, step=500, key=f"hedef_butce_{i}")
            sure = col_h3.number_input("Süre (ay)", min_value=1, value=12, step=1, key=f"hedef_sure_{i}")
            if ad:
                hedefler.append({"ad": ad, "hedef_tutar": tutar, "aylik_butce": butce, "sure_ay": sure})

    if st.button("💾 Profili Kaydet ve Analiz Et", type="primary"):
        gercek_aylik_gelir = aylik_gelir + ek_gelir_tutar
        with st.spinner("Profil kaydediliyor..."):
            resp = requests.post(
                f"{API_URL}/profile",
                json={
                    "session_id": st.session_state["session_id"],
                    "gelir_kaynak": gelir_kaynak,
                    "aylik_gelir": aylik_gelir + ek_gelir_tutar,
                    "ek_gelir": f"{ek_gelir_ad} ({ek_gelir_tutar:,.0f} TL/ay)" if ek_gelir_ad else "Yok",
                    "borclar": str(borc_tutar),
                    "yatirimlar": yatirimlar_str,
                    "yatirim_tutar": toplam_yatirim,
                    "yatirim_listesi": yatirim_listesi,
                    "birikim_tutar": birikim_tutar,
                    "nakit_tutar": nakit_tutar,
                    "borc_tutar": borc_tutar,
                    "hedefler": hedefler
    }
)

            if resp.status_code == 200:
                data = resp.json()
                st.session_state["budget_plan"] = data.get("budget_plan", {})
                st.success("✅ Profil kaydedildi!")

                if plan.get("aylik_yatirim_getirisi", 0) > 0:
                    st.info(
                        f"💹 Yatırımlarınızdan aylık tahmini "
                        f"**{plan.get('aylik_yatirim_getirisi', 0):,.0f} TL** getiri hesaplandı."
                    )
                for y in plan.get("yatirim_detay", []):
                    st.caption(
                        f"• {y['tur']}: {y['tutar']:,.0f} TL → "
                        f"aylık ~{y['aylik_getiri_tl']:,.0f} TL getiri"
                    )

                plan = data.get("budget_plan", {}) or {}
                st.subheader("Bütçe Analizi")

                col_p1, col_p2, col_p3, col_p4 = st.columns(4)
                col_p1.metric("Mevcut Tasarruf", f"{plan.get('mevcut_tasarruf', 0):,.0f} TL/ay")
                ideal = plan.get("ideal_dagilim", {})
                col_p2.metric("İdeal Tasarruf (20%)", f"{ideal.get('tasarruf_20', 0):,.0f} TL/ay")
                col_p3.metric("Genel Durum", plan.get("genel_durum", "").capitalize())
                col_p4.metric("Net Servet", f"{plan.get('net_servet', 0):,.0f} TL")

                hedef_analizi = plan.get("hedef_analizi", [])
                if hedef_analizi:
                    st.subheader("Hedef İlerleme")
                    for h in hedef_analizi:
                        if h.get("hedef_tutar") and h.get("gercekci_sure_ay"):
                            ilerleme = min(plan.get("mevcut_tasarruf", 0) / h["hedef_tutar"], 1.0)
                            st.caption(f"🎯 {h['ad']}")
                            st.progress(ilerleme)
                            st.caption(
                                f"Mevcut hızla {h['gercekci_sure_ay']} ayda ulaşılır "
                                f"(hedef: {h['sure_ay']} ay)"
                            )
            else:
                st.error(f"Hata: {resp.text}")

# Sayfa 5: Senaryo
elif page == "🔮 Senaryo":
    st.title("🔮 Harcama Simülasyonu")
    st.caption("Yapmayı düşündüğünüz bir harcamanın bütçenize etkisini önceden hesaplayın.")

    if "session_id" not in st.session_state:
        st.warning("Önce ekstre yükleyin.")
        st.stop()

    st.subheader("Hızlı Senaryo Seç")
    hizli = st.selectbox(
        "Hazır senaryolardan seçin veya kendiniz girin:",
        ["Kendiniz girin...", "Yurt dışı tatil — 15.000 TL", "Yeni telefon — 25.000 TL",
         "Spor salonu + takviye — 2.000 TL/ay", "Araba bakım — 8.000 TL", "Kurs / eğitim — 5.000 TL"]
    )

    defaults = {
        "Yurt dışı tatil — 15.000 TL": ("Yurt dışı tatil", 15000),
        "Yeni telefon — 25.000 TL": ("Yeni telefon", 25000),
        "Spor salonu + takviye — 2.000 TL/ay": ("Spor salonu", 2000),
        "Araba bakım — 8.000 TL": ("Araba bakım", 8000),
        "Kurs / eğitim — 5.000 TL": ("Kurs / eğitim", 5000),
    }
    default_ad, default_tutar = defaults.get(hizli, ("", 0))

    st.divider()
    st.subheader("Senaryo Detayı")

    col1, col2 = st.columns(2)
    with col1:
        senaryo_ad = st.text_input("Harcama adı", value=default_ad, placeholder="Örn: Yurt dışı tatil")
        senaryo_tutar = st.number_input(
            "Harcama tutarı (TL)", min_value=0, value=default_tutar, step=500,
            help="Tek seferlik veya aylık harcama tutarını girin"
        )
    with col2:
        hedef_tutar = st.number_input(
            "Birikim hedefiniz (TL) — opsiyonel", min_value=0, value=0, step=1000,
            help="Hedefiniz varsa girin."
        )
        sure_ay = st.number_input(
    "Ne kadar sürecek ? (ay)",
    min_value=1, value=12, step=1,
    help="Örn: 12 = 1 yıl, 6 = 6 ay"
)

    st.info("💡 Bu araç, yapmayı düşündüğünüz harcamanın aylık tasarrufunuzu ve birikim hedefinizi nasıl etkileyeceğini hesaplar.")

    if st.button("🔮 Simüle Et", type="primary"):
        if not senaryo_ad or senaryo_tutar == 0:
            st.warning("Harcama adı ve tutar giriniz.")
        else:
            with st.spinner("Simülasyon hesaplanıyor..."):
                resp = requests.post(
                    f"{API_URL}/scenario",
                    json={
                        "session_id": st.session_state["session_id"],
                        "senaryo_tutar": senaryo_tutar,
                        "senaryo_aciklama": senaryo_ad,
                        "hedef_tutar": hedef_tutar if hedef_tutar > 0 else None,
                        "sure_ay": sure_ay
                    }
                )

                if resp.status_code == 200:
                    data = resp.json()
                    etki = data.get("etki_seviyesi", "")
                    renk = {"minimal": "success", "düşük": "success", "orta": "warning",
                            "yüksek": "warning", "kritik": "error"}.get(etki, "info")
                    getattr(st, renk)(f"Etki: {etki.upper()} — {data.get('tavsiye', '')}")

                    col_s1, col_s2, col_s3 = st.columns(3)
                    mevcut = data.get("mevcut_durum", {})
                    senaryo = data.get("senaryo_sonrasi", {})
                    col_s1.metric("Mevcut Aylık Tasarruf", f"{mevcut.get('aylik_tasarruf', 0):,.0f} TL")
                    col_s2.metric("Senaryo Sonrası", f"{senaryo.get('aylik_tasarruf', 0):,.0f} TL",
                                  delta=f"-{senaryo_tutar:,.0f} TL")
                    col_s3.metric("Yıllık Etki", f"{senaryo.get('fark', 0):,.0f} TL kayıp")

                    h = data.get("hedef_analizi")
                    if h and h.get("mevcut_sure_ay"):
                        gecikme = h.get("gecikme_ay", 0) or 0
                        st.info(
                            f"🎯 {h['hedef_tutar']:,.0f} TL hedefinize:\n\n"
                            f"Mevcut hızla **{h['mevcut_sure_ay']} ayda** ulaşırsınız. "
                            f"Bu harcama sonrası **{h.get('senaryo_sure_ay', '?')} aya** çıkar "
                            f"({gecikme} ay gecikme)."
                        )
                else:
                    st.error(f"Hata: {resp.text}")

# Sayfa 6: Günlük İşlem Ekle
elif page == "📝 Günlük İşlem Ekle":
    st.title("📝 Günlük İşlem Ekle")
    st.caption("PDF olmadan da harcama veya gelir girebilirsiniz. Sistem anlık olarak öğrenir.")

    if "session_id" not in st.session_state:
        st.warning("Önce ekstre yükleyin.")
        st.stop()

    st.subheader("İşleminizi yazın")
    st.caption("Hem harcama hem gelir girebilirsiniz.")

    ornek = st.selectbox(
        "Örnek seçin veya kendiniz yazın:",
        [
            "Örnek seçin...",
            "Dün Kadıköy'de kafede 450 TL ödedim",
            "Bu sabah Migros'tan 380 TL market yaptım",
            "Shell'den 1200 TL benzin aldım",
            "Netflix aboneliği 349 TL çekti",
            "Doktora 600 TL ödedim",
            "Bugün 500 TL harçlık aldım",
            "Freelance iş için 2000 TL ödeme aldım",
            "Komşuya verdiğim 800 TL geri geldi",
        ]
    )

    text = st.text_area(
        "İşlem açıklaması",
        value=ornek if ornek != "Örnek seçin..." else "",
        height=100,
        placeholder="Örn: Dün akşam Kadıköy'de bir kafede 450 TL ödedim"
    )

    if st.button("✅ İşlemi Ekle", type="primary"):
        if not text.strip():
            st.warning("Lütfen bir işlem açıklaması girin.")
        else:
            with st.spinner("Parse ediliyor..."):
                resp = requests.post(
                    f"{API_URL}/nlp-transaction",
                    json={"session_id": st.session_state["session_id"], "text": text}
                )

                if resp.status_code == 200:
                    data = resp.json()
                    parsed = data.get("parsed", {})
                    saved = data.get("saved", False)

                    if parsed:
                        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                        col_r1.metric("Tarih", parsed.get("tarih", "-"))
                        col_r2.metric("Tutar", f"{parsed.get('tutar', 0):,.0f} TL")
                        col_r3.metric("Kategori", parsed.get("kategori", "-").capitalize())
                        col_r4.metric("Yer", parsed.get("yer") or "Belirtilmedi")

                        tur = parsed.get("tur", "gider")
                        if tur == "gelir":
                            st.success(f"✅ '{parsed.get('aciklama')}' gelir işlemi kaydedildi.")
                        else:
                            st.success(f"✅ '{parsed.get('aciklama')}' gider işlemi kaydedildi.")
                        updated_cats = data.get("updated_categories", {})
                        if updated_cats:
                            st.subheader("📊 Güncel Harcama Durumu")
                            st.caption("Bu işlem analize yansıtıldı.")
                            df = pd.DataFrame(
                                list(updated_cats.items()),
                                columns=["Kategori", "Tutar (TL)"]
                            ).sort_values("Tutar (TL)", ascending=False)
                            st.dataframe(df, use_container_width=True, hide_index=True)

                            if "result" in st.session_state:
                                st.session_state["result"]["categories"] = updated_cats
                else:
                    st.error(f"Hata: {resp.text}")
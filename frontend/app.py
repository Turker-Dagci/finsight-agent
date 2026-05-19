import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

API_URL = "http://localhost:8000"

st.set_page_config(page_title="FinSight Agent", page_icon="💰", layout="wide")

st.markdown("""
<style>
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
        color: white; border: none; border-radius: 8px; font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

if "islem_gecmisi" not in st.session_state:
    st.session_state["islem_gecmisi"] = []

with st.sidebar:
    st.title("💰 FinSight Agent")
    st.caption("Çok-Ajanlı KOBİ Finansal Analiz Sistemi")
    st.divider()
    page = st.radio("Sayfa", ["📤 Ekstre Yükle", "📊 Analiz", "💬 Sohbet",
                               "🎯 Profil & Hedefler", "🔮 Senaryo", "📝 Günlük İşlem Ekle"])
    st.divider()
    if "session_id" in st.session_state:
        st.success("Aktif oturum")
        st.caption(f"ID: {st.session_state['session_id'][:8]}...")
    st.divider()

if page == "📤 Ekstre Yükle":
    st.title("📤 Banka Ekstresi Yükle")
    st.caption("PDF veya görüntü formatında banka ekstresi yükleyin.")
    uploaded = st.file_uploader("Dosya seçin", type=["pdf", "png", "jpg", "jpeg"])
    if uploaded:
        st.success(f"✅ {uploaded.name}")
        query = st.text_input("Analiz sorusu", value="Bu ay nasıl harcadım ve önümüzdeki ay ne yapmalıyım?")
        if st.button("🚀 Analizi Başlat", type="primary"):
            with st.spinner("📤 Dosya yükleniyor..."):
                files = {"file": (uploaded.name, uploaded.getvalue())}
                upload_resp = requests.post(f"{API_URL}/upload", files=files)
                if upload_resp.status_code != 200:
                    st.error(f"Yükleme hatası: {upload_resp.text}"); st.stop()
                session_id = upload_resp.json()["session_id"]
                st.session_state["session_id"] = session_id
                st.session_state["islem_gecmisi"] = []
            with st.spinner("🤖 Ajanlar analiz ediyor... (30-60 saniye)"):
                analyze_resp = requests.post(f"{API_URL}/analyze",
                                              params={"session_id": session_id, "query": query}, timeout=180)
                if analyze_resp.status_code != 200:
                    st.error(f"Analiz hatası: {analyze_resp.text}"); st.stop()
                result = analyze_resp.json()
                st.session_state["result"] = result
            st.success("✅ Analiz tamamlandı!")
            st.balloons()
            st.info("Sol menüden 'Analiz' sayfasına geçin.")

elif page == "📊 Analiz":
    st.title("📊 Finansal Analiz")
    if "result" not in st.session_state:
        st.warning("Henüz analiz yapılmadı. Önce ekstre yükleyin.")
        st.stop()

    result = st.session_state["result"]
    errors = result.get("errors", [])
    if errors:
        st.error(f"⚠️ {errors[0]}")
        st.info("Lütfen tekrar analiz başlatın.")
        st.stop()

    summary = result.get("parsed_summary", {}) or {}
    categories = result.get("categories", {}) or {}
    health = result.get("health_score", {}) or {}

    if result.get("monthly_summary"):
        st.info(f"📅 **Bu Ayın Özeti:** {result['monthly_summary']}")
    if result.get("awareness_message"):
        st.markdown(f'<div class="awareness-box">{result["awareness_message"]}</div>', unsafe_allow_html=True)

    gelir = summary.get("toplam_gelir") or 0
    gider = abs(summary.get("toplam_gider") or 0)
    net = gelir - gider
    vergi = result.get("tax_total") or 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Toplam Gelir", f"{gelir:,.0f} TL")
    col2.metric("Toplam Gider", f"{gider:,.0f} TL")
    col3.metric("Net Tasarruf", f"{net:,.0f} TL", delta=f"%{net/gelir*100:.1f}" if gelir > 0 else None)
    col4.metric("Vergi Yükü (KDV+ÖTV)", f"{vergi:,.0f} TL" if vergi > 0 else "Hesaplanıyor...")

    st.divider()
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("🏥 Finansal Sağlık")
        if health:
            skor = health.get("toplam_skor", 0)
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number", value=skor,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": health.get("seviye", ""), "font": {"size": 16}},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#2e75b6"},
                    "steps": [
                        {"range": [0, 30], "color": "#3d1a1a"},
                        {"range": [30, 50], "color": "#3d2e1a"},
                        {"range": [50, 70], "color": "#2e3d1a"},
                        {"range": [70, 85], "color": "#1a3d2e"},
                        {"range": [85, 100], "color": "#1a2e3d"}
                    ],
                    "threshold": {"line": {"color": "#ffffff", "width": 2}, "thickness": 0.75, "value": skor}
                }
            ))
            fig_gauge.update_layout(
                height=220, margin=dict(t=30, b=10, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)", font_color="white"
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
            st.caption(health.get("mesaj", ""))
            for k, v in health.get("bilesenler", {}).items():
                st.caption(f"{k.capitalize()}: {v} puan — {health.get('detay', {}).get(k, '')}")

    with col_right:
        st.subheader("📊 Harcama Dağılımı")
        if categories:
            df = pd.DataFrame(list(categories.items()), columns=["Kategori", "Tutar (TL)"]).sort_values("Tutar (TL)", ascending=False)
            fig = px.bar(df, x="Kategori", y="Tutar (TL)", color="Tutar (TL)", color_continuous_scale="Blues")
            fig.update_layout(
                height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="white", showlegend=False, margin=dict(t=10, b=40, l=40, r=10)
            )
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("✏️ Kategori Düzelt — Sistem Öğrenir"):
            st.caption("Yanlış kategorize edilen işlemi düzeltin.")
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
                        json={"aciklama": islem_adi, "eski_kategori": eski_kat, "yeni_kategori": yeni_kat}
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.success("✅ Sistem bu düzeltmeyi öğrendi ve işlemlere uyguladı!")
                        if data.get("updated_categories"):
                            st.session_state["result"]["categories"] = data["updated_categories"]
                            st.rerun()
                else:
                    st.warning("İşlem adı girin.")

    st.divider()
    fx = result.get("fx_shield", {}) or {}
    if fx:
        st.subheader("💱 Döviz Kalkanı")
        c1, c2, c3 = st.columns(3)
        c1.metric("Aylık Gider", f"{abs(fx.get('aylik_gider_tl', 0)):,.0f} TL")
        c2.metric("USD Karşılığı", f"{abs(fx.get('aylik_gider_usd', 0)):,.0f} $")
        c3.metric("EUR Karşılığı", f"{abs(fx.get('aylik_gider_eur', 0)):,.0f} €")

    st.divider()
    st.subheader("📈 Güncel Piyasa Verileri")
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("USD/TL", f"{fx.get('usd_kur', 0):,.2f} TL")
    mc2.metric("EUR/TL", f"{fx.get('eur_kur', 0):,.2f} TL")
    mc3.metric("BIST100 Aylık", f"%{result.get('bist_aylik', 0):,.1f}")
    mc4.metric("Mevduat Faizi", f"%{result.get('mevduat_faizi', 0):,.1f}")

    predicted = result.get("predicted_expenses", {}) or {}
    if predicted and predicted.get("tahminler"):
        st.divider()
        st.subheader("📅 Önümüzdeki 30 Gün — Beklenen Giderler")
        st.caption(f"Toplam beklenen: {predicted.get('toplam', 0):,.0f} TL")
        for t in predicted.get("tahminler", []):
            renk = "🔴" if t["tur"] == "zorunlu" else "🟡"
            st.markdown(f"{renk} **{t['tarih']}** — {t['aciklama']} — **{t['tutar']:,.0f} TL**")

    cashflow = result.get("cashflow_forecast", {}) or {}
    if cashflow:
        st.divider()
        st.subheader("💵 30 Günlük Nakit Akış Tahmini")
        renk_fn = {"success": st.success, "warning": st.warning, "error": st.error}.get(
            cashflow.get("risk_renk", "warning"), st.info)
        renk_fn(cashflow.get("risk_mesaj", ""))
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Mevcut Nakit", f"{cashflow.get('mevcut_nakit', 0):,.0f} TL")
        c2.metric("Ay Sonu Tahmini", f"{cashflow.get('ay_sonu_tahmini', 0):,.0f} TL")
        c3.metric("Günlük Harcama Limiti", f"{cashflow.get('gunluk_guvenli_limit', 0):,.0f} TL/gün",
                  help="Sabit giderler düşüldükten sonra kalan günlere bölünen kullanılabilir günlük bütçeniz.")
        c4.metric("Kalan Gün", f"{cashflow.get('ayin_kalan_gunu', 0)} gün")

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("⚠️ Proaktif Uyarılar")
        alerts = result.get("proactive_alerts", []) or []
        for a in alerts:
            st.warning(a)
        if not alerts:
            st.success("Kritik uyarı yok.")
    with col_b:
        st.subheader("🔍 Anomaliler")
        anomalies = result.get("anomalies", []) or []
        for a in anomalies:
            st.error(a)
        if not anomalies:
            st.success("Anomali tespit edilmedi.")

    insights = result.get("behavioral_insights", []) or []
    if insights:
        st.divider()
        st.subheader("🧠 Davranışsal Analiz")
        for i in insights:
            st.info(i)

    st.divider()
    st.subheader("🤖 FinSight Tavsiyesi")
    final = result.get("final_response", "")
    if final and final != "Analiz geçici olarak kullanılamıyor. Lütfen tekrar deneyin.":
        st.markdown(final)
    elif final:
        st.warning(final)
        st.info("Sohbet sayfasından 'Genel analiz yap' yazarak yeniden tavsiye alabilirsiniz.")
    else:
        st.info("Tavsiye almak için Sohbet sayfasına gidin ve bir soru sorun.")

elif page == "💬 Sohbet":
    st.title("💬 FinSight ile Sohbet")
    if "session_id" not in st.session_state:
        st.warning("Önce ekstre yükleyin."); st.stop()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    if prompt := st.chat_input("Sor: 'Bu ay aboneliklerimi azaltırsam ne tasarruf ederim?'"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Analiz ediliyor..."):
                resp = requests.post(f"{API_URL}/query",
                                      json={"session_id": st.session_state["session_id"], "query": prompt}, timeout=60)
                answer = resp.json().get("response", "Yanıt alınamadı.")
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

elif page == "🎯 Profil & Hedefler":
    st.title("🎯 Finansal Profil & Hedefler")
    if "session_id" not in st.session_state:
        st.warning("Önce ekstre yükleyin."); st.stop()

    st.caption("Doldurmak istemediğiniz alanları boş bırakabilirsiniz.")
    st.subheader("Gelir Bilgileri")
    col1, col2 = st.columns(2)
    with col1:
        gelir_kaynak = st.selectbox("Birincil Gelir Kaynağı",
                                     ["Belirtmek istemiyorum", "Maaş", "Serbest Meslek", "Emekli", "Kira Geliri", "Diğer"])
        aylik_gelir = st.number_input("Aylık Net Gelir (TL)", min_value=0, value=0, step=500,
                                       help="Ek geliriniz varsa aşağıdan ayrıca ekleyin.")
    with col2:
        ek_gelir_var = st.radio("Ek geliriniz var mı?", ["Hayır", "Evet"], horizontal=True)
        ek_gelir_ad = ""; ek_gelir_tutar = 0
        if ek_gelir_var == "Evet":
            ek_gelir_ad = st.text_input("Ek gelir kaynağı", placeholder="Freelance, kira, ikinci iş...")
            ek_gelir_tutar = st.number_input("Aylık ek gelir tutarı (TL)", min_value=0, value=0, step=500)

    st.divider()
    st.subheader("Varlıklar ve Borçlar")
    col3, col4 = st.columns(2)
    with col3:
        borc_var = st.radio("Krediniz veya borcunuz var mı?", ["Hayır", "Evet"], horizontal=True)
        borc_tutar = 0
        if borc_var == "Evet":
            borc_tutar = st.number_input("Toplam borç (TL)", min_value=0, value=0, step=1000)
            st.number_input("Aylık ödeme (TL)", min_value=0, value=0, step=100, help="Bilgi amaçlı.")
        nakit_tutar = st.number_input("Nakit / Vadesiz Hesap (TL)", min_value=0, value=0, step=1000)

    with col4:
        yatirim_var = st.radio("Yatırımınız var mı?", ["Hayır", "Evet"], horizontal=True)
        yatirim_listesi = []; yatirimlar_str = "Yok"; toplam_yatirim = 0
        if yatirim_var == "Evet":
            st.caption("Sahip olduğunuz yatırımları ve tutarlarını girin.")

            # Döviz (Dolar)
            col_y1, col_y2 = st.columns([2, 3])
            dolar_secili = col_y1.checkbox("Döviz (Dolar)")
            if dolar_secili:
                dolar_miktar = col_y2.number_input(
                    "Dolar miktarı (USD)", min_value=0.0, value=0.0, step=100.0, key="dolar_m"
                )
                if dolar_miktar > 0:
                    usd_kur = st.session_state.get("result", {}).get("fx_shield", {}).get("usd_kur", 45.5)
                    dolar_tl = round(dolar_miktar * usd_kur, 0)
                    col_y2.caption(f"≈ {dolar_tl:,.0f} TL (kur: {usd_kur:.2f})")
                    yatirim_listesi.append({"tur": "Döviz (USD/EUR)", "tutar": dolar_tl})
                    toplam_yatirim += dolar_tl

            # Döviz (Euro)
            col_y1, col_y2 = st.columns([2, 3])
            euro_secili = col_y1.checkbox("Döviz (Euro)")
            if euro_secili:
                euro_miktar = col_y2.number_input(
                    "Euro miktarı (EUR)", min_value=0.0, value=0.0, step=100.0, key="euro_m"
                )
                if euro_miktar > 0:
                    eur_kur = st.session_state.get("result", {}).get("fx_shield", {}).get("eur_kur", 52.9)
                    euro_tl = round(euro_miktar * eur_kur, 0)
                    col_y2.caption(f"≈ {euro_tl:,.0f} TL (kur: {eur_kur:.2f})")
                    yatirim_listesi.append({"tur": "Döviz (USD/EUR)", "tutar": euro_tl})
                    toplam_yatirim += euro_tl

            # Altın
            col_y1, col_y2 = st.columns([2, 3])
            altin_secili = col_y1.checkbox("Altın")
            if altin_secili:
                altin_tutar = col_y2.number_input("Altın tutarı (TL)", min_value=0, value=0, step=5000, key="altin_t")
                if altin_tutar > 0:
                    yatirim_listesi.append({"tur": "Altın", "tutar": altin_tutar})
                    toplam_yatirim += altin_tutar

            # Vadeli Birikim
            col_y1, col_y2 = st.columns([2, 3])
            vadeli_secili = col_y1.checkbox("Vadeli Birikim")
            if vadeli_secili:
                vadeli_tutar = col_y2.number_input("Birikim tutarı (TL)", min_value=0, value=0, step=5000, key="vadeli_t")
                vadeli_faiz = st.number_input(
                    "Yıllık faiz oranı (%)", min_value=0.0, max_value=100.0, value=43.0, step=0.5,
                    help="Bankanızın sunduğu yıllık faiz oranı."
                )
                if vadeli_tutar > 0:
                    yatirim_listesi.append({"tur": "Mevduat", "tutar": vadeli_tutar, "ozel_faiz": vadeli_faiz})
                    toplam_yatirim += vadeli_tutar

            if yatirim_listesi:
                yatirimlar_str = ", ".join([y["tur"] for y in yatirim_listesi])
                st.caption("Seçilen yatırımlar:")
                for y in yatirim_listesi:
                    st.markdown(f"• **{y['tur']}**: {y['tutar']:,.0f} TL")

    st.divider()
    st.subheader("Finansal Hedefleriniz")
    st.caption("Hedefinizi girin — sistem aylık bütçenize etkisini ve sürdürülebilirliğini hesaplar.")
    hedefler = []
    mevcut_tasarruf_tahmini = max(
        (aylik_gelir + ek_gelir_tutar) -
        abs(st.session_state.get("result", {}).get("parsed_summary", {}).get("toplam_gider", 0) or 0), 0
    )

    for i in range(3):
        with st.expander(f"Hedef {i+1}", expanded=(i == 0)):
            ad = st.text_input("Hedef adı", placeholder="Yurt dışı tatil, acil fon, borç kapatma...", key=f"h_ad_{i}")
            col_h1, col_h2 = st.columns(2)
            tutar = col_h1.number_input("Hedef miktarı (TL)", min_value=0, value=0, step=1000, key=f"h_tutar_{i}")
            sure = col_h2.number_input("Hedef için belirlenen süre (ay)", min_value=1, value=12, step=1, key=f"h_sure_{i}")
            if ad and tutar > 0:
                aylik_etki = round(tutar / sure, 0)
                st.caption(f"📊 Aylık bütçeye etkisi: **{aylik_etki:,.0f} TL/ay** | Yıllık: **{aylik_etki*12:,.0f} TL**")
                if mevcut_tasarruf_tahmini > 0:
                    if aylik_etki <= mevcut_tasarruf_tahmini:
                        st.success("✅ Mevcut tasarruf hızınızla bu hedef sürdürülebilir görünüyor.")
                    else:
                        st.warning(f"⚠️ Bu hedef için aylık {aylik_etki:,.0f} TL ayırmanız gerekiyor. Harcamalardan kısma gerekebilir.")
                hedefler.append({"ad": ad, "hedef_tutar": tutar, "aylik_butce": aylik_etki, "sure_ay": sure})

    if st.button("💾 Profili Kaydet ve Analiz Et", type="primary"):
        gercek_aylik_gelir = (aylik_gelir or 0) + (ek_gelir_tutar or 0)
        with st.spinner("Profil kaydediliyor..."):
            resp = requests.post(f"{API_URL}/profile", json={
                "session_id": st.session_state["session_id"],
                "gelir_kaynak": gelir_kaynak if gelir_kaynak != "Belirtmek istemiyorum" else "Belirtilmedi",
                "aylik_gelir": gercek_aylik_gelir,
                "ek_gelir": f"{ek_gelir_ad} ({ek_gelir_tutar:,.0f} TL/ay)" if ek_gelir_ad else "Yok",
                "borclar": str(borc_tutar) if borc_var == "Evet" else "Yok",
                "yatirimlar": yatirimlar_str,
                "yatirim_tutar": toplam_yatirim,
                "yatirim_listesi": yatirim_listesi,
                "birikim_tutar": 0,
                "nakit_tutar": nakit_tutar or 0,
                "borc_tutar": borc_tutar or 0,
                "hedefler": hedefler
            })
            if resp.status_code == 200:
                data = resp.json(); st.success("✅ Profil kaydedildi!")
                plan = data.get("budget_plan", {}) or {}
                col_p1, col_p2, col_p3, col_p4 = st.columns(4)
                col_p1.metric("Aylık Tasarruf", f"{plan.get('mevcut_tasarruf', 0):,.0f} TL/ay")
                col_p2.metric("İdeal Tasarruf (20%)", f"{plan.get('ideal_dagilim', {}).get('tasarruf_20', 0):,.0f} TL/ay")
                col_p3.metric("Genel Durum", plan.get("genel_durum", "").capitalize())
                col_p4.metric("Net Servet", f"{plan.get('net_servet', 0):,.0f} TL")
                if plan.get("aylik_yatirim_getirisi", 0) > 0:
                    st.info(f"💹 Yatırımlarınızdan aylık tahmini **{plan.get('aylik_yatirim_getirisi', 0):,.0f} TL** getiri hesaplandı.")
                    for y in plan.get("yatirim_detay", []):
                        st.caption(f"• {y['tur']}: {y['tutar']:,.0f} TL → aylık ~{y['aylik_getiri_tl']:,.0f} TL (%{y['aylik_getiri_yuzde']:.1f} yıllık)")
                for h in plan.get("hedef_analizi", []):
                    if h.get("hedef_tutar") and h.get("gercekci_sure_ay"):
                        ilerleme = min(plan.get("mevcut_tasarruf", 0) / h["hedef_tutar"], 1.0)
                        st.caption(f"🎯 {h['ad']} — {h['hedef_tutar']:,.0f} TL")
                        st.progress(ilerleme)
                        st.caption(f"Mevcut hızla **{h['gercekci_sure_ay']} ayda** ulaşılır (hedef: {h['sure_ay']} ay)")
            else:
                st.error(f"Hata: {resp.text}")

elif page == "🔮 Senaryo":
    st.title("🔮 Harcama Simülasyonu")
    st.caption("Yapmayı düşündüğünüz bir harcamanın bütçenize etkisini önceden hesaplayın.")
    if "session_id" not in st.session_state:
        st.warning("Önce ekstre yükleyin."); st.stop()

    hizli = st.selectbox("Hazır senaryolardan seçin veya kendiniz girin:",
                          ["Kendiniz girin...", "Yurt dışı tatil — 15.000 TL", "Yeni telefon — 25.000 TL",
                           "Spor salonu + takviye — 2.000 TL/ay", "Araba bakım — 8.000 TL", "Kurs / eğitim — 5.000 TL"])
    defaults = {"Yurt dışı tatil — 15.000 TL": ("Yurt dışı tatil", 15000),
                "Yeni telefon — 25.000 TL": ("Yeni telefon", 25000),
                "Spor salonu + takviye — 2.000 TL/ay": ("Spor salonu", 2000),
                "Araba bakım — 8.000 TL": ("Araba bakım", 8000),
                "Kurs / eğitim — 5.000 TL": ("Kurs / eğitim", 5000)}
    default_ad, default_tutar = defaults.get(hizli, ("", 0))
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        senaryo_ad = st.text_input("Harcama adı", value=default_ad, placeholder="Örn: Yurt dışı tatil")
        senaryo_tutar = st.number_input(
            "Aylık Harcama/Gider Tutarı (TL)",
            min_value=0, value=default_tutar, step=500,
            help="Bu harcamayı her ay yapacaksanız aylık tutarını girin."
        )
    with col2:
        hedef_tutar = st.number_input(
            "Aylık Birikim Hedefi (TL) — opsiyonel",
            min_value=0, value=0, step=1000,
            help="Her ay biriktirmek istediğiniz tutar."
        )
        sure_ay = st.number_input("Ne kadar sürecek? (ay)", min_value=1, value=12, step=1, help="Örn: 12 = 1 yıl")

    st.info("💡 Bu araç, yapmayı düşündüğünüz harcamanın aylık tasarrufunuzu ve birikim hedefinizi nasıl etkileyeceğini hesaplar.")
    if st.button("🔮 Simüle Et", type="primary"):
        if not senaryo_ad or senaryo_tutar == 0:
            st.warning("Harcama adı ve tutar giriniz.")
        else:
            with st.spinner("Simülasyon hesaplanıyor..."):
                resp = requests.post(f"{API_URL}/scenario", json={
                    "session_id": st.session_state["session_id"],
                    "senaryo_tutar": senaryo_tutar, "senaryo_aciklama": senaryo_ad,
                    "hedef_tutar": hedef_tutar if hedef_tutar > 0 else None, "sure_ay": sure_ay
                })
                if resp.status_code == 200:
                    data = resp.json()
                    etki = data.get("etki_seviyesi", "")
                    renk = {"minimal": "success", "düşük": "success", "orta": "warning",
                            "yüksek": "warning", "kritik": "error"}.get(etki, "info")
                    getattr(st, renk)(f"Etki: {etki.upper()} — {data.get('tavsiye', '')}")
                    col_s1, col_s2, col_s3 = st.columns(3)
                    mevcut = data.get("mevcut_durum", {}); senaryo = data.get("senaryo_sonrasi", {})
                    col_s1.metric("Mevcut Aylık Tasarruf", f"{mevcut.get('aylik_tasarruf', 0):,.0f} TL")
                    col_s2.metric("Senaryo Sonrası", f"{senaryo.get('aylik_tasarruf', 0):,.0f} TL", delta=f"-{senaryo_tutar:,.0f} TL")
                    col_s3.metric(
                        f"{sure_ay} Aylık Toplam Etki",
                        f"{senaryo.get('sure_bazli_etki', senaryo.get('fark', 0)):,.0f} TL"
                    )
                    h = data.get("hedef_analizi")
                    if h and h.get("mevcut_sure_ay"):
                        gecikme = h.get("gecikme_ay", 0) or 0
                        st.info(f"🎯 {h['hedef_tutar']:,.0f} TL hedefinize:\n\nMevcut hızla **{h['mevcut_sure_ay']} ayda** ulaşırsınız. Bu harcama sonrası **{h.get('senaryo_sure_ay', '?')} aya** çıkar ({gecikme} ay gecikme).")
                else:
                    st.error(f"Hata: {resp.text}")

elif page == "📝 Günlük İşlem Ekle":
    st.title("📝 Günlük İşlem Ekle")
    st.caption("PDF olmadan da harcama veya gelir girebilirsiniz. İşlemler anlık olarak analize yansır.")
    if "session_id" not in st.session_state:
        st.warning("Önce ekstre yükleyin."); st.stop()

    col_form, col_liste = st.columns([1, 1])
    with col_form:
        st.subheader("Yeni İşlem")
        ornek = st.selectbox("Örnek seçin veya kendiniz yazın:",
                              ["Örnek seçin...", "Dün Kadıköy'de kafede 450 TL ödedim",
                               "Bu sabah Migros'tan 380 TL market yaptım", "Shell'den 1200 TL benzin aldım",
                               "Netflix aboneliği 349 TL çekti", "Doktora 600 TL ödedim",
                               "Bugün 500 TL harçlık aldım", "Freelance iş için 2000 TL ödeme aldım",
                               "Komşuya verdiğim 800 TL geri geldi"])
        text = st.text_area("İşlem açıklaması",
                             value=ornek if ornek != "Örnek seçin..." else "",
                             height=100, placeholder="Örn: Dün akşam Kadıköy'de kafede 450 TL ödedim")
        if st.button("✅ İşlemi Ekle", type="primary"):
            if not text.strip():
                st.warning("Lütfen bir işlem açıklaması girin.")
            else:
                with st.spinner("Parse ediliyor..."):
                    resp = requests.post(f"{API_URL}/nlp-transaction",
                                          json={"session_id": st.session_state["session_id"], "text": text})
                    if resp.status_code == 200:
                        data = resp.json(); parsed = data.get("parsed", {})
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
                            st.session_state["islem_gecmisi"].append({
                                "tarih": parsed.get("tarih", "-"), "aciklama": parsed.get("aciklama", text[:30]),
                                "tutar": parsed.get("tutar", 0), "tur": tur, "kategori": parsed.get("kategori", "-"),
                            })
                            updated_cats = data.get("updated_categories", {})
                            if updated_cats and "result" in st.session_state:
                                st.session_state["result"]["categories"] = updated_cats
                                st.subheader("📊 Güncel Harcama Durumu")
                                st.caption("Bu işlem analize yansıtıldı.")
                                df = pd.DataFrame(list(updated_cats.items()), columns=["Kategori", "Tutar (TL)"]).sort_values("Tutar (TL)", ascending=False)
                                st.dataframe(df, use_container_width=True, hide_index=True)
                                if "result" in st.session_state:
                                    st.session_state["result"]["categories"] = updated_cats
                                if data.get("updated_health_score"):
                                    st.session_state["result"]["health_score"] = data["updated_health_score"]
                                if data.get("updated_cashflow"):
                                    st.session_state["result"]["cashflow_forecast"] = data["updated_cashflow"]
                    else:
                        st.error(f"Hata: {resp.text}")

    with col_liste:
        st.subheader("📋 Girilen İşlemler")
        gecmis = st.session_state.get("islem_gecmisi", [])
        if not gecmis:
            st.caption("Henüz işlem girilmedi.")
        else:
            for islem in reversed(gecmis):
                ikon = "🟢" if islem["tur"] == "gelir" else "🔴"
                st.markdown(f"{ikon} **{islem['tarih']}** — {islem['aciklama']} — **{islem['tutar']:,.0f} TL** _{islem['kategori']}_")
            if st.button("🗑️ Listeyi Temizle"):
                st.session_state["islem_gecmisi"] = []; st.rerun()
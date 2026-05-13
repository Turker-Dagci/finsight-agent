import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="FinSight Agent",
    page_icon="💰",
    layout="wide"
)

with st.sidebar:
    st.title("💰 FinSight Agent")
    st.caption("Çok-Ajanlı KOBİ Finansal Analiz Sistemi")
    st.divider()
    page = st.radio("Sayfa", ["📤 Ekstre Yükle", "💬 Analiz & Sohbet"])
    st.divider()
    st.info("Gemini 2.5 · LangGraph · Qdrant")

if page == "📤 Ekstre Yükle":
    st.title("Banka Ekstresi veya Fatura Yükle")

    uploaded = st.file_uploader(
        "PDF veya görüntü formatında yükleyin",
        type=["pdf", "png", "jpg", "jpeg"]
    )

    if uploaded:
        st.success(f"Dosya seçildi: {uploaded.name}")

        if st.button("Analizi Başlat", type="primary"):
            with st.spinner("Yükleniyor..."):
                try:
                    files = {"file": (uploaded.name, uploaded.getvalue())}
                    response = requests.post(f"{API_URL}/upload", files=files)
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state["file_id"] = result["file_id"]
                        st.success("Yükleme başarılı!")
                        st.json(result)
                    else:
                        st.error(f"Hata: {response.text}")
                except Exception as e:
                    st.error(f"API bağlantı hatası: {e}")

elif page == "💬 Analiz & Sohbet":
    st.title("Finansal Analizin")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Sor: 'Bu ay en çok neye harcadım?'"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Ajanlar analiz ediyor..."):
                try:
                    response = requests.post(
                        f"{API_URL}/query",
                        json={"query": prompt}
                    )
                    answer = response.json().get("response", "Yanıt alınamadı.")
                except:
                    answer = "API bağlantısı kurulamadı. Backend çalışıyor mu?"
                st.markdown(answer)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )
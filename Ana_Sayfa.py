import streamlit as st

st.set_page_config(
    page_title="EPİAŞ Portal",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ EPİAŞ Analiz Portalı")
st.caption("EPİAŞ Şeffaflık Platformu — Hesaplama & Sorgulama Araçları")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("### ⚡ YEKDEM Hesap Makinesi")
    st.markdown(
        "EPİAŞ verilerine dayalı **YEKTOB / YEKDEM / YGT** hesaplama aracı. "
        "Tarih aralığı, kapasite faktörleri ve LÜYTOB fiyatlarını girerek "
        "tahmini YEKDEM fiyatını hesaplayın."
    )
    st.page_link("pages/1_YEKDEM_Hesap_Makinesi.py", label="Hesap Makinesine Git →", icon="⚡")

with col2:
    st.markdown("### 🏭 Tesis Listesi")
    st.markdown(
        "Tüm organizasyonları ve bu organizasyonlara bağlı **UEVCB tesislerini** "
        "API'den otomatik çekerek listeleyin. Excel ve JSON formatında indirin."
    )
    st.page_link("pages/2_Tesis_Listesi.py", label="Tesis Listesine Git →", icon="🏭")

st.divider()
st.caption("Yeni modüller ilerleyen süreçte eklenecektir.")

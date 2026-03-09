import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta, date

st.set_page_config(page_title="YEKDEM Hesap Makinesi", page_icon="⚡", layout="wide")
st.title("⚡ YEKDEM Hesap Makinesi")
st.caption("EPİAŞ Şeffaflık Platformu verilerine dayalı YEKTOB / YEKDEM / YGT hesaplama aracı")

URL_PTF     = "https://seffaflik.epias.com.tr/electricity-service/v1/markets/dam/data/mcp"
URL_TUKETIM = "https://seffaflik.epias.com.tr/electricity-service/v1/consumption/data/realtime-consumption"
URL_YEKDEM  = "https://seffaflik.epias.com.tr/electricity-service/v1/renewables/data/licensed-realtime-generation"
URL_KURULU  = "https://seffaflik.epias.com.tr/electricity-service/v1/renewables/data/new-installed-capacity"
URL_AUTH    = "https://giris.epias.com.tr/cas/v1/tickets"

def get_tgt(username, password):
    now = datetime.now()
    if "tgt" in st.session_state and "tgt_time" in st.session_state:
        if now - st.session_state["tgt_time"] < timedelta(hours=2):
            return st.session_state["tgt"]
    r = requests.post(URL_AUTH,
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    if r.status_code == 201:
        tgt = r.headers["Location"].split("/")[-1]
        st.session_state["tgt"] = tgt
        st.session_state["tgt_time"] = now
        return tgt
    st.error(f"❌ TGT alınamadı. HTTP {r.status_code}")
    return None

# ── SIDEBAR ──────────────────────────────────
with st.sidebar:
    st.header("🔐 Giriş Bilgileri")
    default_user = st.secrets.get("epias", {}).get("username", "") if hasattr(st, "secrets") else ""
    default_pass = st.secrets.get("epias", {}).get("password", "") if hasattr(st, "secrets") else ""
    username = st.text_input("EPİAŞ Kullanıcı Adı", value=default_user)
    password = st.text_input("EPİAŞ Şifre", value=default_pass, type="password")
    st.divider()
    st.header("📅 Tarih Aralığı")
    bugun = date.today()
    start_date = st.date_input("Başlangıç Tarihi", value=bugun.replace(day=1))
    end_date   = st.date_input("Bitiş Tarihi",     value=bugun)
    st.divider()
    st.header("💱 Kur")
    dolar = st.number_input("Dolar Kuru (₺)", min_value=0.0, value=33.0, step=0.1, format="%.2f")
    hesapla = st.button("🚀 Hesapla", use_container_width=True, type="primary")

# ── GİRİŞ ALANLARI ───────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.subheader("📊 Kapasite Faktörleri (%)")
    ruzgar_cf    = st.number_input("Rüzgar (%)",      min_value=0.0, max_value=100.0, value=30.0, step=0.1) / 100
    biogaz_cf    = st.number_input("Biyogaz (%)",     min_value=0.0, max_value=100.0, value=80.0, step=0.1) / 100
    kanaltipi_cf = st.number_input("Kanal Tipli (%)", min_value=0.0, max_value=100.0, value=50.0, step=0.1) / 100
    biyokutle_cf = st.number_input("Biyokütle (%)",   min_value=0.0, max_value=100.0, value=80.0, step=0.1) / 100
    gunes_cf     = st.number_input("Güneş (%)",       min_value=0.0, max_value=100.0, value=20.0, step=0.1) / 100
    diger_cf     = st.number_input("Diğer (%)",       min_value=0.0, max_value=100.0, value=50.0, step=0.1) / 100

with col2:
    st.subheader("💰 LÜYTOB Birim Fiyatları (₺/MWh)")
    ruzgar_lbf    = st.number_input("Rüzgar (₺)",      min_value=0.0, value=500.0, step=1.0)
    biogaz_lbf    = st.number_input("Biyogaz (₺)",     min_value=0.0, value=800.0, step=1.0)
    kanaltipi_lbf = st.number_input("Kanal Tipli (₺)", min_value=0.0, value=400.0, step=1.0)
    biyokutle_lbf = st.number_input("Biyokütle (₺)",   min_value=0.0, value=700.0, step=1.0)
    gunes_lbf     = st.number_input("Güneş (₺)",       min_value=0.0, value=600.0, step=1.0)
    diger_lbf     = st.number_input("Diğer (₺)",       min_value=0.0, value=500.0, step=1.0)

# ── HESAPLAMA ─────────────────────────────────
if hesapla:
    if not username or not password:
        st.warning("⚠️ Lütfen EPİAŞ kullanıcı adı ve şifresini girin.")
        st.stop()
    if start_date > end_date:
        st.error("❌ Başlangıç tarihi bitiş tarihinden büyük olamaz.")
        st.stop()

    with st.spinner("🔄 EPİAŞ'tan veriler çekiliyor..."):
        tgt = get_tgt(username, password)
        if not tgt:
            st.stop()

        start_dt   = datetime.combine(start_date, datetime.min.time())
        end_dt     = datetime.combine(end_date,   datetime.min.time())
        gun_sayisi = (end_dt - start_dt).days + 1
        middle_dt  = start_dt + (end_dt - start_dt) / 2

        start_iso  = start_date.strftime("%Y-%m-%dT00:00:00+03:00")
        end_iso    = end_date.strftime("%Y-%m-%dT00:00:00+03:00")
        middle_iso = middle_dt.strftime("%Y-%m-%dT00:00:00+03:00")

        headers     = {"TGT": tgt}
        body_tarih  = {"startDate": start_iso, "endDate": end_iso, "page": {"sort": {"field": "date", "direction": "ASC"}}}
        body_kurulu = {"period": middle_iso}

        try:
            r_ptf = requests.post(URL_PTF,     headers=headers, json=body_tarih); r_ptf.raise_for_status()
            r_tuk = requests.post(URL_TUKETIM, headers=headers, json=body_tarih); r_tuk.raise_for_status()
            r_yek = requests.post(URL_YEKDEM,  headers=headers, json=body_tarih); r_yek.raise_for_status()
            r_kur = requests.post(URL_KURULU,  headers=headers, json=body_kurulu); r_kur.raise_for_status()
        except requests.exceptions.RequestException as e:
            st.error(f"❌ API hatası: {e}")
            st.stop()

        ptf_ort    = r_ptf.json()["statistic"]["priceAvg"]
        tuk_totals = r_tuk.json().get("statistics", {})
        yek_totals = r_yek.json()["totals"]
        kurulu_guc = r_kur.json().get("installedCapacities", [])
        total_kguc = r_kur.json()["statisticsDto"]

        bioKutle    = yek_totals["lfgTotal"] + yek_totals["biogasTotal"] + yek_totals["biomassTotal"]
        kanalTipli  = yek_totals["canalTypeTotal"] + yek_totals["riverTotal"]
        rezervuarli = yek_totals["reservoirTotal"] + yek_totals["otherTotal"]
        gunes_lis   = yek_totals["solarTotal"]
        ruzgar_lis  = yek_totals["windTotal"]
        jeotermal   = yek_totals["geothermalTotal"]
        lisansliTotal = bioKutle + kanalTipli + rezervuarli + gunes_lis + ruzgar_lis + jeotermal

        k_gunes     = kurulu_guc[0]["unlicencedCapacity"]
        k_ruzgar    = kurulu_guc[1]["unlicencedCapacity"]
        k_kanal     = kurulu_guc[3]["unlicencedCapacity"]
        k_biyokutle = kurulu_guc[4]["unlicencedCapacity"]
        k_diger     = kurulu_guc[6]["unlicencedCapacity"]
        k_biogaz    = kurulu_guc[9]["unlicencedCapacity"]
        k_toplam    = total_kguc["totalUnlicencedCapacity"]

        ls_ruzgar    = ruzgar_cf    * k_ruzgar    * 24 * gun_sayisi
        ls_biogaz    = biogaz_cf    * k_biogaz    * 24 * gun_sayisi
        ls_kanal     = kanaltipi_cf * k_kanal     * 24 * gun_sayisi
        ls_biyokutle = biyokutle_cf * k_biyokutle * 24 * gun_sayisi
        ls_gunes     = gunes_cf     * k_gunes     * 24 * gun_sayisi
        ls_diger     = diger_cf     * k_diger     * 24 * gun_sayisi

        luytob_ruzgar    = ruzgar_lbf    * ls_ruzgar
        luytob_biogaz    = biogaz_lbf    * ls_biogaz
        luytob_kanal     = kanaltipi_lbf * ls_kanal
        luytob_biyokutle = biyokutle_lbf * ls_biyokutle
        luytob_gunes     = gunes_lbf     * ls_gunes
        luytob_diger     = diger_lbf     * ls_diger
        luytob_toplam    = luytob_ruzgar + luytob_biogaz + luytob_kanal + luytob_biyokutle + luytob_gunes + luytob_diger

        yekf = [13.37, 9.03, 7.15, 7.33, 10.31, 6.98]
        yektob_lisansli = (bioKutle*yekf[0] + gunes_lis*yekf[1] + kanalTipli*yekf[2] +
                           rezervuarli*yekf[3] + jeotermal*yekf[4] + ruzgar_lis*yekf[5]) * dolar * 10
        yektob_toplam   = yektob_lisansli + luytob_toplam

        ygt_orani     = 0.86
        toplamTuketim = tuk_totals.get("consumptionTotal", 0)
        uecm_orani    = 0.8
        uecm          = toplamTuketim * uecm_orani
        ygt_lisansli  = ptf_ort * lisansliTotal
        ygt_lisanssiz = ptf_ort * (ls_ruzgar+ls_biogaz+ls_kanal+ls_biyokutle+ls_gunes+ls_diger) * ygt_orani
        ygt_toplam    = ygt_lisansli + ygt_lisanssiz
        yekdem_fiyat  = (yektob_toplam - ygt_toplam) / uecm if uecm > 0 else 0

    st.success(f"✅ {gun_sayisi} günlük veri başarıyla çekildi.")
    st.divider()
    st.subheader("📌 Ana Sonuçlar")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("YEKDEM Tahmini Fiyat", f"₺{yekdem_fiyat:,.2f} /MWh")
    m2.metric("YEKTOB",               f"₺{yektob_toplam:,.0f}")
    m3.metric("YGT",                  f"₺{ygt_toplam:,.0f}")
    m4.metric("Aylık Ort. PTF",       f"₺{ptf_ort:,.2f} /MWh")
    m5, m6, m7, m8 = st.columns(4)
    m5.metric("YEKTOB Lisanslı",  f"₺{yektob_lisansli:,.0f}")
    m6.metric("YEKTOB Lisanssız", f"₺{luytob_toplam:,.0f}")
    m7.metric("YGT Lisanssız",    f"₺{ygt_lisanssiz:,.0f}")
    m8.metric("UEÇM",             f"{uecm:,.0f} MWh")
    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🏭 Lisanslı Üretim (MWh)")
        df_lis = pd.DataFrame({
            "Kaynak":       ["Biyokütle","Kanal Tipli","Rezervuarlı","Güneş","Rüzgar","Jeotermal","TOPLAM"],
            "Üretim (MWh)": [bioKutle, kanalTipli, rezervuarli, gunes_lis, ruzgar_lis, jeotermal, lisansliTotal]
        })
        df_lis["Üretim (MWh)"] = df_lis["Üretim (MWh)"].map(lambda x: f"{x:,.2f}")
        st.dataframe(df_lis, use_container_width=True, hide_index=True)
    with col_b:
        st.subheader("🔋 Lisanssız Kurulu Güç (MW)")
        df_kur = pd.DataFrame({
            "Kaynak":   ["Güneş","Rüzgar","Kanal Tipli","Biyokütle","Diğer","Biyogaz","TOPLAM"],
            "Güç (MW)": [k_gunes, k_ruzgar, k_kanal, k_biyokutle, k_diger, k_biogaz, k_toplam]
        })
        df_kur["Güç (MW)"] = df_kur["Güç (MW)"].map(lambda x: f"{x:,.2f}")
        st.dataframe(df_kur, use_container_width=True, hide_index=True)

    st.subheader("☀️ Lisanssız Üretim & LÜYTOB")
    df_luy = pd.DataFrame({
        "Kaynak":          ["Rüzgar","Biyogaz","Kanal Tipli","Biyokütle","Güneş","Diğer"],
        "Üretim (MWh)":    [ls_ruzgar, ls_biogaz, ls_kanal, ls_biyokutle, ls_gunes, ls_diger],
        "Birim Fiyat (₺)": [ruzgar_lbf, biogaz_lbf, kanaltipi_lbf, biyokutle_lbf, gunes_lbf, diger_lbf],
        "Toplam (₺)":      [luytob_ruzgar, luytob_biogaz, luytob_kanal, luytob_biyokutle, luytob_gunes, luytob_diger]
    })
    for col in ["Üretim (MWh)", "Birim Fiyat (₺)", "Toplam (₺)"]:
        df_luy[col] = df_luy[col].map(lambda x: f"{x:,.2f}")
    st.dataframe(df_luy, use_container_width=True, hide_index=True)

    st.divider()
    with st.expander("📋 Hesaplama Özeti"):
        st.write(f"**Tarih:** {start_date} → {end_date} ({gun_sayisi} gün)")
        st.write(f"**Dolar:** ₺{dolar:,.2f}  |  **PTF:** ₺{ptf_ort:,.2f} /MWh")
        st.write(f"**Toplam Tüketim:** {toplamTuketim:,.2f} MWh  |  **UEÇM:** {uecm:,.2f} MWh ({uecm_orani})")
        st.write(f"**Toplam Lisanssız Kurulu Güç:** {k_toplam:,.2f} MW")

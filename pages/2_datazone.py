import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Crypto Zone Tracker", layout="wide")
st.title("📊 HUNTERS X HUNTERS")

# ========== CONFIG ==========
CMC_API_KEY = st.secrets["CMC_API_KEY"]
HEADERS = {"Accepts": "application/json", "X-CMC_PRO_API_KEY": CMC_API_KEY}

# ========== CMC: LẤY DANH SÁCH ZONE & TOKEN (MỖI 24H) ==========
@st.cache_data(ttl=86400)
def get_cmc_zone_tokens():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/categories"
    try:
        res = requests.get(url, headers=HEADERS)
        res.raise_for_status()
        data = res.json()["data"]

        all_rows = []
        for category in data:
            zone = category["name"]
            for token in category.get("coins", []):
                all_rows.append({"zone": zone, "token": token})

        df = pd.DataFrame(all_rows)
        return df
    except Exception as e:
        st.error(f"Lỗi khi lấy Zone từ CoinMarketCap: {e}")
        return pd.DataFrame()

# ========== COINGECKO: LẤY GIÁ & VOLUME THEO TOKEN ==========
@st.cache_data(ttl=300)
def get_prices_from_coingecko(tokens):
    url = "https://api.coingecko.com/api/v3/simple/price"
    token_ids = ",".join(tokens)
    params = {
        "ids": token_ids,
        "vs_currencies": "usd",
        "include_24hr_vol": "true",
        "include_24hr_change": "true"
    }
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"Lỗi khi lấy dữ liệu từ CoinGecko: {e}")
        return {}

# ========== LOAD & MERGE ==========
df_zone_map = get_cmc_zone_tokens()

if df_zone_map.empty:
    st.error("❌ Không lấy được danh sách Zone từ CoinMarketCap.")
    st.stop()

unique_tokens = df_zone_map["token"].dropna().str.lower().unique().tolist()
price_data = get_prices_from_coingecko(unique_tokens)

# Merge lại bảng tổng hợp
df_zone_map["token_lc"] = df_zone_map["token"].str.lower()
df_zone_map["price"] = df_zone_map["token_lc"].apply(lambda x: price_data.get(x, {}).get("usd"))
df_zone_map["volume_24h"] = df_zone_map["token_lc"].apply(lambda x: price_data.get(x, {}).get("usd_24h_vol"))
df_zone_map["change_24h"] = df_zone_map["token_lc"].apply(lambda x: price_data.get(x, {}).get("usd_24h_change"))

# ========== TỔNG HỢP ZONE ==========
zone_stats = (
    df_zone_map.dropna(subset=["price", "change_24h"])
    .groupby("zone")
    .agg(
        avg_price_change_24h=("change_24h", "mean"),
        avg_volume_24h=("volume_24h", "sum"),
        token_count=("token", "count")
    )
    .reset_index()
    .sort_values("avg_price_change_24h", ascending=False)
)

# ========== HIỂN THỊ GIAO DIỆN ==========
col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("📦 Tổng quan Zone")
    selected_zone = st.selectbox("🔍 Chọn Zone:", zone_stats["zone"].tolist())

    st.dataframe(
        zone_stats.rename(columns={
            "zone": "Zone",
            "avg_price_change_24h": "Avg Price Change 24H (%)",
            "avg_volume_24h": "Total Volume 24H",
            "token_count": "Số lượng Token"
        }).style.format({
            "Avg Price Change 24H (%)": "{:+.2f}%",
            "Total Volume 24H": "{:,.0f}"
        }),
        use_container_width=True
    )

with col2:
    st.subheader(f"📈 Token trong Zone: `{selected_zone}`")
    df_zone = df_zone_map[df_zone_map["zone"] == selected_zone].copy()

    if not df_zone.empty:
        df_zone_display = df_zone[["token", "price", "change_24h", "volume_24h"]].copy()
        df_zone_display.columns = ["Token", "Current Price", "Price Change 24H (%)", "Volume 24H"]

        df_zone_display["Current Price"] = df_zone_display["Current Price"].apply(lambda x: f"{x:,.4f}$")
        df_zone_display["Price Change 24H (%)"] = df_zone_display["Price Change 24H (%)"].apply(lambda x: f"{x:+.2f}%")
        df_zone_display["Volume 24H"] = df_zone_display["Volume 24H"].apply(lambda x: f"{x:,.0f}")

        st.dataframe(df_zone_display, use_container_width=True)
    else:
        st.warning("❌ Không có dữ liệu token trong zone này.")

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

        st.markdown(f"🛰️ Đang gọi API: `{url}`")
        st.success(f"✅ Status code: {res.status_code}")
        st.code(res.text, language="json")

        data = res.json().get("data", [])
        if not data:
            return pd.DataFrame()

        all_rows = []
        for category in data:
            zone = category.get("name", "")
            top_coins = category.get("top_3_coins", [])
            for coin_url in top_coins:
                coin_id = coin_url.split("/")[-1].replace(".png", "")
                all_rows.append({"zone": zone, "token_id": coin_id})

        df = pd.DataFrame(all_rows)
        return df
    except Exception as e:
        st.error(f"Lỗi khi lấy Zone từ CoinMarketCap: {e}")
        return pd.DataFrame()

# ========== COINGECKO: LẤY GIÁ & VOLUME THEO TOKEN ==========
@st.cache_data(ttl=300)
def get_prices_from_coingecko(token_ids):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(token_ids),
        "order": "market_cap_desc",
        "per_page": 250,
        "page": 1,
        "price_change_percentage": "24h"
    }
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"Lỗi khi lấy dữ liệu từ CoinGecko: {e}")
        return []

# ========== LOAD & MERGE ==========
df_zone_map = get_cmc_zone_tokens()

if df_zone_map.empty:
    st.error("❌ Không lấy được danh sách Zone từ CoinMarketCap.")
    st.stop()

unique_token_ids = df_zone_map["token_id"].dropna().unique().tolist()
price_data = get_prices_from_coingecko(unique_token_ids)

price_df = pd.DataFrame(price_data)
price_df = price_df.rename(columns={"id": "token_id"})

# Merge lại bảng tổng hợp
merged_df = pd.merge(df_zone_map, price_df, on="token_id", how="left")
merged_df = merged_df.dropna(subset=["current_price", "price_change_percentage_24h"])

# ========== TỔNG HỢP ZONE ==========
zone_stats = (
    merged_df.groupby("zone")
    .agg(
        avg_price_change_24h=("price_change_percentage_24h", "mean"),
        avg_volume_24h=("total_volume", "sum"),
        token_count=("token_id", "count")
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
    df_zone = merged_df[merged_df["zone"] == selected_zone].copy()

    if not df_zone.empty:
        df_zone_display = df_zone[["name", "current_price", "price_change_percentage_24h", "total_volume"]].copy()
        df_zone_display.columns = ["Token", "Current Price", "Price Change 24H (%)", "Volume 24H"]

        df_zone_display["Current Price"] = df_zone_display["Current Price"].apply(lambda x: f"{x:,.4f}$")
        df_zone_display["Price Change 24H (%)"] = df_zone_display["Price Change 24H (%)"].apply(lambda x: f"{x:+.2f}%")
        df_zone_display["Volume 24H"] = df_zone_display["Volume 24H"].apply(lambda x: f"{x:,.0f}")

        st.dataframe(df_zone_display, use_container_width=True)
    else:
        st.warning("❌ Không có dữ liệu token trong zone này.")

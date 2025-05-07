import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Crypto Zone Tracker", layout="wide")
st.title("📊 HUNTERS X HUNTERS")

# ========== GET DATA FROM BINANCE ==========
@st.cache_data(ttl=600)
def get_zone_data():
    url = "https://www.binance.com/bapi/asset/v2/public/asset-service/product/get-products"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers).json()
        data = res["data"]
        df = pd.DataFrame(data)

        # Chỉ lấy các cặp USDT đang giao dịch
        df = df[(df["s"].str.endswith("USDT")) & (df["st"] == "TRADING")]

        # Dữ liệu cần
        df["zone"] = df["cs"]
        df["token"] = df["b"]
        df["symbol"] = df["s"]
        df["price"] = pd.to_numeric(df["c"], errors="coerce")
        df["vol_24h"] = pd.to_numeric(df["v"], errors="coerce")
        df["vol_change_24h"] = pd.to_numeric(df["cr"], errors="coerce")
        df["price_change_24h"] = pd.to_numeric(df["p"], errors="coerce")

        return df.dropna(subset=["zone", "price_change_24h"])
    except Exception as e:
        st.error("Không lấy được dữ liệu từ Binance.")
        return pd.DataFrame()

df_all = get_zone_data()

# ========== TỔNG HỢP ZONE ==========
zone_stats = (
    df_all.groupby("zone")
    .agg(
        avg_price_change_24h=("price_change_24h", "mean"),
        avg_vol_change_24h=("vol_change_24h", "mean")
    )
    .reset_index()
    .sort_values("avg_price_change_24h", ascending=False)
)

# ========== LAYOUT 2:3 ==========
col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("🧭 Tổng quan theo Zone")
    selected_zone = st.selectbox("🔍 Chọn Zone:", zone_stats["zone"].tolist())

    st.markdown("### 📌 Thống kê biến động theo Zone")
    st.dataframe(
        zone_stats.rename(columns={
            "zone": "Zone",
            "avg_price_change_24h": "Avg Price Change 24H (%)",
            "avg_vol_change_24h": "Avg Volume Change 24H (%)"
        }).style.format({
            "Avg Price Change 24H (%)": "{:+.2f}%",
            "Avg Volume Change 24H (%)": "{:+.2f}%"
        }),
        use_container_width=True
    )

with col2:
    st.subheader(f"📈 Token trong Zone: `{selected_zone}`")

    df_zone = df_all[df_all["zone"] == selected_zone].copy()
    if not df_zone.empty:
        df_zone_display = df_zone[["token", "price", "vol_change_24h", "vol_24h"]].copy()
        df_zone_display.columns = ["Token", "Current Price", "Volume Change 24H (%)", "Current Volume (M)"]

        df_zone_display["Current Price"] = df_zone_display["Current Price"].apply(lambda x: f"{x:,.4f}$")
        df_zone_display["Volume Change 24H (%)"] = df_zone_display["Volume Change 24H (%)"].apply(lambda x: f"{x:+.2f}%")
        df_zone_display["Current Volume (M)"] = df_zone_display["Current Volume (M)"].apply(lambda x: f"{x / 1e6:.1f}M")

        st.dataframe(df_zone_display, use_container_width=True)
    else:
        st.warning("Không có dữ liệu token trong zone này.")

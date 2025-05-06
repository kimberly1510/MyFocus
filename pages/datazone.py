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
        df = df[df["s"].str.endswith("USDT")]  # chỉ lấy cặp USDT
        df["zone"] = df["cs"]  # zone = category segment
        df["symbol"] = df["s"]
        df["token"] = df["b"]
        df["price"] = pd.to_numeric(df["c"], errors="coerce")
        df["vol24h"] = pd.to_numeric(df["v"], errors="coerce")
        df["vol_change_24h"] = pd.to_numeric(df["cr"], errors="coerce")
        return df
    except Exception as e:
        st.error("Không lấy được dữ liệu từ Binance.")
        return pd.DataFrame()

df_all = get_zone_data()

# ========== BUILD ZONE TABLE ==========
zone_stats = (
    df_all.groupby("zone")
    .agg(avg_price_change_24h=("cr", "mean"))
    .reset_index()
    .sort_values("avg_price_change_24h", ascending=False)
)

# ========== LAYOUT 2:3 ==========
col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("🧭 Zone Overview")
    selected_zone = st.selectbox(
        "Chọn một Zone để xem chi tiết:",
        zone_stats["zone"].tolist()
    )

    st.markdown("### 📌 Average Price Change 24H (%)")
    st.dataframe(
        zone_stats[["zone", "avg_price_change_24h"]].rename(
            columns={"zone": "Zone", "avg_price_change_24h": "Average Price Change 24H (%)"}
        ).style.format({"Average Price Change 24H (%)": "{:+.2f}%"}),
        use_container_width=True
    )

with col2:
    st.subheader(f"🔍 Token trong Zone: `{selected_zone}`")
    df_zone = df_all[df_all["zone"] == selected_zone].copy()

    if not df_zone.empty:
        df_zone_display = df_zone[["token", "price", "vol_change_24h", "vol24h"]].copy()
        df_zone_display.columns = ["Token", "Current Price", "Volume Change 24H (%)", "Current Volume (M)"]
        df_zone_display["Current Price"] = df_zone_display["Current Price"].apply(lambda x: f"{x:,.4f}$")
        df_zone_display["Volume Change 24H (%)"] = df_zone_display["Volume Change 24H (%)"].apply(lambda x: f"{x:+.2f}%")
        df_zone_display["Current Volume (M)"] = df_zone_display["Current Volume (M)"].apply(lambda x: f"{x/1e6:.1f}M")

        st.dataframe(df_zone_display, use_container_width=True)
    else:
        st.warning("Zone này không có token nào hiển thị.")

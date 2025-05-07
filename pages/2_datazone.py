import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Crypto Zone Tracker", layout="wide")
st.title("\ud83d\udcca HUNTERS X HUNTERS")

# ========== GET DATA FROM BINANCE ==========
# (Tạm thời bỏ cache để debug)
def get_zone_data():
    url = "https://www.binance.com/bapi/asset/v2/public/asset-service/product/get-products"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        data = res.json().get("data", [])
        df = pd.DataFrame(data)

        if df.empty:
            st.error("\u274c Không có dữ liệu từ API Binance.")
            return pd.DataFrame()

        # Debug cột có sẵn
        st.subheader("\ud83d\udce6 Debug: Thông tin DataFrame")
        st.write("\ud83d\udccc Các cột có trong df:", df.columns.tolist())
        st.dataframe(df.head())

        # Gán zone từ 'cs' nếu có
        if "cs" in df.columns:
            df["zone"] = df["cs"]
        elif "tags" in df.columns:
            df["zone"] = df["tags"].apply(lambda x: x[0] if isinstance(x, list) and x else "Unknown")
        else:
            st.error("\u274c Không tìm thấy 'cs' hoặc 'tags' để xác định zone.")
            return pd.DataFrame()

        # Chỉ lấy các cặp USDT đang giao dịch
        df = df[(df["s"].str.endswith("USDT")) & (df["st"] == "TRADING")]

        df["token"] = df["b"]
        df["symbol"] = df["s"]
        df["price"] = pd.to_numeric(df["c"], errors="coerce")
        df["vol_24h"] = pd.to_numeric(df["v"], errors="coerce")
        df["vol_change_24h"] = pd.to_numeric(df["cr"], errors="coerce")
        df["price_change_24h"] = pd.to_numeric(df["p"], errors="coerce")

        df = df.dropna(subset=["zone", "price_change_24h"])
        return df

    except Exception as e:
        st.error(f"L\u1ed7i khi l\u1ea5y d\u1eef li\u1ec7u t\u1eeb Binance: {e}")
        return pd.DataFrame()

# ========== LOAD DATA ==========
df_all = get_zone_data()

if "zone" in df_all.columns:
    zone_stats = (
        df_all.groupby("zone")
        .agg(
            avg_price_change_24h=("price_change_24h", "mean"),
            avg_vol_change_24h=("vol_change_24h", "mean")
        )
        .reset_index()
        .sort_values("avg_price_change_24h", ascending=False)
    )
else:
    st.error("\u274c Không có cột 'zone' trong dữ liệu.")
    st.stop()

# ========== LAYOUT 2:3 ==========
col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("\ud83e\uddf1\u Tổng quan theo Zone")
    selected_zone = st.selectbox("\ud83d\udd0d Chọn Zone:", zone_stats["zone"].tolist())

    st.markdown("### \ud83d\udcc8 Thống kê biến động theo Zone")
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
    st.subheader(f"\ud83d\udcc8 Token trong Zone: `{selected_zone}`")
    df_zone = df_all[df_all["zone"] == selected_zone].copy()

    if not df_zone.empty:
        df_zone_display = df_zone[["token", "price", "vol_change_24h", "vol_24h"]].copy()
        df_zone_display.columns = ["Token", "Current Price", "Volume Change 24H (%)", "Current Volume (M)"]

        df_zone_display["Current Price"] = df_zone_display["Current Price"].apply(lambda x: f"{x:,.4f}$")
        df_zone_display["Volume Change 24H (%)"] = df_zone_display["Volume Change 24H (%)"].apply(lambda x: f"{x:+.2f}%")
        df_zone_display["Current Volume (M)"] = df_zone_display["Current Volume (M)"].apply(lambda x: f"{x / 1e6:.1f}M")

        st.dataframe(df_zone_display, use_container_width=True)
    else:
        st.warning("\u274c Không có dữ liệu token trong zone này.")

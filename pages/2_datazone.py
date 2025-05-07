import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# API key và headers cho CoinMarketCap
CMC_API_KEY = "YOUR_CMC_API_KEY"
HEADERS = {
    "Accepts": "application/json",
    "X-CMC_PRO_API_KEY": CMC_API_KEY
}

# Hàm lấy dữ liệu Zone từ CoinMarketCap
def get_zones_from_cmc():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/category"
    params = {
        "start": 1,
        "limit": 500
    }
    response = requests.get(url, headers=HEADERS, params=params)
    data = response.json()

    if "data" not in data:
        raise ValueError("Không lấy được dữ liệu Zone từ CMC: " + str(data))

    records = []
    for item in data["data"]:
        records.append({
            "Zone Name": item.get("name"),
            "Num Tokens": item.get("num_tokens"),
            "Avg Price Change %": item.get("avg_price_change"),
            "Market Cap": item.get("market_cap"),
            "Market Cap Change %": item.get("market_cap_change"),
            "Volume": item.get("volume"),
            "Volume Change %": item.get("volume_change"),
            "Last Updated": item.get("last_updated")
        })

    df = pd.DataFrame(records)
    df["Last Updated"] = pd.to_datetime(df["Last Updated"])
    return df

# Giao diện Streamlit
st.set_page_config(page_title="DataZone Monitor", layout="wide")
st.title("📊 CoinMarketCap DataZone Tracker")

st.write("Đang tải dữ liệu từ CoinMarketCap...")

try:
    df = get_zones_from_cmc()
    st.success("✅ Dữ liệu đã được tải thành công!")
    st.dataframe(df, use_container_width=True)

    # Tải xuống Excel
    now = datetime.now().strftime("%Y%m%d_%H%M")
    file_name = f"zone_data_cmc_{now}.xlsx"
    df.to_excel(file_name, index=False)

    with open(file_name, "rb") as f:
        st.download_button(
            label="📥 Tải Excel dữ liệu Zone",
            data=f,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

except Exception as e:
    st.error(f"❌ Lỗi khi tải dữ liệu: {e}")

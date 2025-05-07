import requests
import pandas as pd
import datetime

# API key và headers cho CoinMarketCap
CMC_API_KEY = "YOUR_CMC_API_KEY"
HEADERS = {
    "Accepts": "application/json",
    "X-CMC_PRO_API_KEY": CMC_API_KEY
}

# Hàm lấy dữ liệu Zone từ CoinMarketCap (bổ sung thêm thời gian cập nhật)
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

# Gọi hàm và xuất dữ liệu ra file Excel
if __name__ == "__main__":
    try:
        df = get_zones_from_cmc()
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        df.to_excel(f"zone_data_cmc_{now}.xlsx", index=False)
        print("Dữ liệu đã được lưu thành công.")
    except Exception as e:
        print("Lỗi khi lấy dữ liệu:", e)

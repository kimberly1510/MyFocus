import streamlit as st
import requests
import pandas as pd

# ========== CONFIG ==========
st.set_page_config(page_title="Crypto Money Flow Tracker", layout="wide")
st.title("🔁 Crypto Money Flow Phase Tracker")

# ========== GET DATA ==========
@st.cache_data(ttl=180)
def get_btc_dominance():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/global").json()
        return r["data"]["market_cap_percentage"]["btc"]
    except:
        return None

@st.cache_data(ttl=180)
def get_eth_btc_ratio():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "ethereum,bitcoin", "vs_currencies": "usd"}
        r = requests.get(url, params=params).json()
        return r["ethereum"]["usd"] / r["bitcoin"]["usd"]
    except:
        return None

@st.cache_data(ttl=180)
def get_large_caps():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 100,
            "page": 1,
            "price_change_percentage": "24h"
        }
        data = requests.get(url, params=params).json()
        df = pd.DataFrame(data)
        df["symbol"] = df["symbol"].str.upper()
        return df
    except:
        return pd.DataFrame()

# ========== PHASE DETECTION ==========
def detect_phase(btc_d, eth_btc_ratio, df_large_caps):
    if btc_d and btc_d > 52:
        return "Phase 1 - Bitcoin"
    elif eth_btc_ratio and eth_btc_ratio > 0.06:
        return "Phase 2 - Ethereum"
    elif not df_large_caps.empty:
        top_largecap = df_large_caps.iloc[10:30]
        avg_largecap_change = top_largecap["price_change_percentage_24h"].mean()

        altcoins = df_large_caps.iloc[30:]
        avg_alt_change = altcoins["price_change_percentage_24h"].mean()
        altcoin_drop_rate = (altcoins["price_change_percentage_24h"] < -5).sum() / len(altcoins)

        if avg_largecap_change > 5:
            return "Phase 3 - Large Caps"
        elif avg_alt_change > 10:
            return "Phase 4 - Altseason"
        elif altcoin_drop_rate > 0.4:
            return "Phase 5 - Reset"
    return "Phase 5 - Reset"

# ========== SUGGESTION ==========
def suggest_action(phase):
    suggestions = {
        "Phase 1 - Bitcoin": "✅ Ưu tiên hold/long BTC, không all-in altcoin.",
        "Phase 2 - Ethereum": "✅ Long ETH và các token hệ ETH (L2, LSD...).",
        "Phase 3 - Large Caps": "✅ Tập trung coin top 10–30, narrative mạnh.",
        "Phase 4 - Altseason": "⚠️ Lướt sóng nhanh, take profit liên tục.",
        "Phase 5 - Reset": "🔴 Thoát hàng, về USDT, dừng giao dịch.",
    }
    return suggestions.get(phase, "Không rõ Phase.")

# ========== METRICS + PHASE EXECUTION ==========
col1, col2 = st.columns(2)

btc_d = get_btc_dominance()
eth_btc = get_eth_btc_ratio()

with col1:
    st.metric("BTC Dominance", f"{btc_d:.2f}%" if btc_d is not None else "Không lấy được dữ liệu")

with col2:
    st.metric("ETH/BTC Ratio", f"{eth_btc:.4f}" if eth_btc else "Không lấy được dữ liệu")

df = get_large_caps()
phase = detect_phase(btc_d, eth_btc, df)
st.session_state["current_phase"] = phase

st.subheader(f"📊 Current Phase: **{phase}**")
st.info(suggest_action(phase))

# ========== BẢNG TOP 100 COIN (HTML TABLE) ==========
st.markdown("---")
with st.expander("🔎 Xem dữ liệu top 100 coin:"):
    if not df.empty:
        df_display = df[["id", "name", "symbol", "current_price", "price_change_percentage_24h", "total_volume"]].copy()
        df_display.columns = ["ID", "Name", "Symbol", "Current Price", "Price Change 24H (%)", "Total Volume"]

        df_display["Current Price"] = df_display["Current Price"].apply(lambda x: f"{x:,.2f}")
        df_display["Price Change 24H (%)"] = df_display["Price Change 24H (%)"].apply(lambda x: f"{x:+.2f}%")
        df_display["Total Volume"] = df_display["Total Volume"].apply(lambda x: f"{x:,.0f}")

        # ===== STYLE CSS =====
        st.markdown("""
        <style>
        .table-container {
            max-height: 600px;
            overflow-y: auto;
            border: 1px solid #444;
        }
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th {
            position: sticky;
            top: 0;
            background-color: #202020;
            color: white;
            padding: 6px 8px;
            font-weight: bold;
            font-family: Roboto, sans-serif;
            font-size: 14px;
            text-align: center;
            z-index: 1;
        }
        td {
            padding: 6px 8px;
            font-family: Roboto, sans-serif;
            font-size: 13px;
            color: white;
        }
        td.left { text-align: left; }
        td.center { text-align: center; }
        td.right { text-align: right; }
        </style>
        """, unsafe_allow_html=True)

        # ===== TOÀN BỘ HTML TABLE =====
        html = "<div class='table-container'><table><thead><tr>"
        html += "<th>ID</th><th>Name</th><th>Symbol</th><th>Current Price</th><th>Price Change 24H (%)</th><th>Total Volume</th>"
        html += "</tr></thead><tbody>"

        for _, row in df_display.iterrows():
            html += "<tr>"
            html += f"<td class='left'>{row['ID']}</td>"
            html += f"<td class='left'>{row['Name']}</td>"
            html += f"<td class='center'>{row['Symbol']}</td>"
            html += f"<td class='right'>{row['Current Price']}</td>"
            html += f"<td class='right'>{row['Price Change 24H (%)']}</td>"
            html += f"<td class='right'>{row['Total Volume']}</td>"
            html += "</tr>"

        html += "</tbody></table></div>"
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.warning("Không lấy được dữ liệu coin.")

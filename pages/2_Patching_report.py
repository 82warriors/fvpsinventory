import streamlit as st
import pandas as pd
import requests
import re

st.set_page_config(page_title="Patching Report", layout="wide")

st.title("🛠️ Patching Report")
st.caption("Always pulls the latest worksheet tab (skips Summary) and shows raw data only")

SPREADSHEET_ID = "1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE"

REQUIRED_HEADERS = [
    "ASSET TAG","SERIAL NUMBER","SCHOOL","HOSTNAME","DEVICE TYPE",
    "BRAND","MODEL","PROFILE","CUSTODIAN NAME","CSM","SSOE LOCATION","STATUS"
]

@st.cache_data(ttl=300)
def get_sheets():
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
    html = requests.get(url).text
    matches = re.findall(r'"sheetId":(\d+).*?"title":"(.*?)"', html)
    return [{"gid": gid, "name": name} for gid, name in matches]

@st.cache_data(ttl=300)
def get_latest_sheet():
    sheets = get_sheets()
    if not sheets:
        return None, "No worksheets at all"

    # filter out Summary tabs
    filtered = [s for s in sheets if s["name"].strip().lower() != "summary"]

    if filtered:
        latest = filtered[-1]  # newest non-summary tab
        return latest["gid"], latest["name"]
    else:
        # fallback: use the last tab even if it's Summary
        latest = sheets[-1]
        return latest["gid"], latest["name"]

def load_latest_sheet():
    gid, sheet_name = get_latest_sheet()
    if gid is None:
        st.error("❌ No valid worksheets found")
        st.stop()

    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={gid}"
    df = pd.read_csv(url, dtype=str)
    df.columns = df.columns.astype(str).str.strip().str.upper()

    if not all(h in df.columns for h in REQUIRED_HEADERS):
        st.error(f"❌ Required headers missing in {sheet_name}")
        st.write(df.columns.tolist())
        st.stop()

    return df, sheet_name

# 🚀 Load data
df, sheet_name = load_latest_sheet()
st.info(f"📄 Showing worksheet: {sheet_name}")

# Raw data only
st.markdown("## 🗂️ Full Data (Worksheet)")
st.dataframe(df, use_container_width=True)

# 🔄 Refresh button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

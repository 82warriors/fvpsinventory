import streamlit as st
import pandas as pd
import requests
import re

st.set_page_config(page_title="Patching Report", layout="wide")

st.title("🛠️ Patching Report")
st.caption("Loads the worksheet immediately to the right of 'Summary' and shows raw data only")

SPREADSHEET_ID = "1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE"

@st.cache_data(ttl=300)
def get_sheets():
    url = f"https://docs.google.com/spreadsheets/d/1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE"
    html = requests.get(url).text
    matches = re.findall(r'"sheetId":(\d+).*?"title":"(.*?)"', html)
    return [{"gid": gid, "name": name} for gid, name in matches]

@st.cache_data(ttl=300)
def get_sheet_right_of_summary():
    sheets = get_sheets()
    if not sheets:
        return None, "No worksheets at all"

    for i, s in enumerate(sheets):
        if s["name"].strip().lower() == "summary":
            if i + 1 < len(sheets):
                return sheets[i + 1]["gid"], sheets[i + 1]["name"]
            else:
                return sheets[-1]["gid"], sheets[-1]["name"]

    # if Summary not found, fallback to last tab
    latest = sheets[-1]
    return latest["gid"], latest["name"]

def load_target_sheet():
    gid, sheet_name = get_sheet_right_of_summary()
    if gid is None:
        st.error("❌ Could not find a worksheet right of Summary")
        st.stop()

    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={gid}"
    df = pd.read_csv(url, dtype=str)
    df.columns = df.columns.astype(str).str.strip().str.upper()

    return df, sheet_name

# 🚀 Load data
df, sheet_name = load_target_sheet()
st.info(f"📄 Showing worksheet: {sheet_name}")

# Raw data only
st.markdown("## 🗂️ Full Data (Worksheet)")
st.dataframe(df, use_container_width=True)

# 🔄 Refresh button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

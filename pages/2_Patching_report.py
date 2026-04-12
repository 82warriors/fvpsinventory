import streamlit as st
import pandas as pd
import requests
import re

st.set_page_config(page_title="Patching Report", layout="wide")

st.title("🛠️ Patching Report")
st.caption("Always pulls the latest worksheet for raw data, summary calculated separately")

SPREADSHEET_ID = "1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE"

REQUIRED_HEADERS = [
    "ADMIN INSTALLED","ACAD INSTALLED","ADMIN SCCM EPP > 4 WKS","ACAD SCCM EPP > 4 WKS",
    "ADMIN NOT CONNECTED","ACAD NOT CONNECTED","ADMIN REQUIRED","ACAD REQUIRED",
    "ADMIN UNKNOWN","ACAD UNKNOWN","E-EXAM","FAULTY","TECH REFRESH","PERCENTAGE"
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
    if sheets:
        latest = sheets[-1]  # newest tab
        return latest["gid"], latest["name"]
    return None, "Default Sheet"

def load_latest_sheet():
    gid, sheet_name = get_latest_sheet()
    if gid is None:
        st.error("❌ No worksheets found")
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
st.info(f"📄 Using latest worksheet: {sheet_name}")

# Raw data
st.markdown("## 🗂️ Full Data (Latest Worksheet)")
st.dataframe(df, use_container_width=True)

# Convert numeric columns
for col in REQUIRED_HEADERS:
    if col != "PERCENTAGE":
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

df["PERCENTAGE"] = pd.to_numeric(df["PERCENTAGE"], errors="coerce").fillna(0)

# Summary totals
totals = df[REQUIRED_HEADERS].sum()

st.markdown("## 📊 Overview Totals")
c1, c2, c3 = st.columns(3)
c1.metric("✅ Admin Installed", int(totals["ADMIN INSTALLED"]))
c2.metric("✅ Acad Installed", int(totals["ACAD INSTALLED"]))
c3.metric("📈 Avg Completion %", f"{df['PERCENTAGE'].mean():.1f}%")

# Summary table
st.markdown("## 📋 Patching Summary")
summary_table = pd.DataFrame(totals).reset_index()
summary_table.columns = ["Category","Count"]
st.dataframe(summary_table, use_container_width=True, hide_index=True)

# Chart
st.markdown("## 📈 Patching Distribution")
st.bar_chart(summary_table.set_index("Category"))

# Progress bars
st.markdown("## 🔄 Completion Progress")
for i, row in df.iterrows():
    st.write(f"Row {i+1}")
    st.progress(row["PERCENTAGE"]/100)

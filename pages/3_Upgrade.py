import streamlit as st
import pandas as pd

st.set_page_config(page_title="Upgrade Tracking", layout="wide")

st.title("⬆️ Upgrade Status Dashboard")
st.caption("Always pulls the latest worksheet for raw data, summary calculated separately")

SPREADSHEET_ID = "1x4EP6dO3FpkFRMBXqHDku0pl4vtHrWnE1S3J-e86vt0"
GID = "550442716"  # your tab ID

url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GID}"

# ✅ Read sheet, first row is header
df = pd.read_csv(url, dtype=str)
df.columns = df.columns.astype(str).str.strip().str.upper()

REQUIRED_HEADERS = [
    "SCHOOL NAME","HOSTNAME","SERIAL NUMBER","ASSET TAG",
    "CUSTODIAN","LOCATION","BRAND","MODEL",
    "CATEGORY","IPU STATUS","EOL STATUS"
]

# Validate headers
if not all(h in df.columns for h in REQUIRED_HEADERS):
    st.error("❌ Required headers missing")
    st.write(df.columns.tolist())
    st.stop()

st.info("📄 Using latest worksheet")

# Show raw data
st.markdown("## 🗂️ Full Updated Data")
st.dataframe(df, use_container_width=True)

# Normalize values
df["MODEL"] = df["MODEL"].astype(str).str.upper().str.strip()
df["IPU STATUS"] = df["IPU STATUS"].astype(str).str.title().str.strip()

TARGET_MODELS = [
    "ACER VX2670G DESKTOP",
    "LENOVO K14 GEN2",
    "LENOVO L13 YOGA G4"
]

df = df[df["MODEL"].isin(TARGET_MODELS)]

# Build summary
summary = df.groupby(["MODEL","IPU STATUS"]).size().unstack(fill_value=0)
for col in ["Completed","Not Completed"]:
    if col not in summary.columns:
        summary[col] = 0

summary = summary.reset_index()
summary["Total"] = summary["Completed"] + summary["Not Completed"]
summary["Completion %"] = (summary["Completed"]/summary["Total"]).fillna(0)*100
summary["Completion %"] = summary["Completion %"].round(1)

# KPIs
st.markdown("## 📊 Overview")
completed = int(summary["Completed"].sum())
not_completed = int(summary["Not Completed"].sum())
total = completed + not_completed
rate = (completed/total*100) if total>0 else 0

c1,c2,c3 = st.columns(3)
c1.metric("✅ Completed",completed)
c2.metric("❌ Not Completed",not_completed)
c3.metric("📈 Completion Rate",f"{rate:.1f}%")

# Summary table
st.markdown("## 📋 Upgrade Summary")
st.dataframe(summary[["MODEL","Completed","Not Completed","Completion %"]],
             use_container_width=True,hide_index=True)

# Chart
st.markdown("## 📈 Upgrade Progress")
chart_df = summary.set_index("MODEL")[["Completed","Not Completed"]]
st.bar_chart(chart_df)

# Progress bars
st.markdown("## 🔄 Progress by Model")
for _,row in summary.iterrows():
    st.write(f"**{row['MODEL']}**")
    st.progress(row["Completion %"]/100)

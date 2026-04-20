import streamlit as st
import pandas as pd
import altair as alt
import requests
import io

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Upgrade Tracking", layout="wide")

st.title("⬆️ Upgrade Status Dashboard")
st.caption("Auto-updated from LATEST sheet")

SPREADSHEET_ID = "1x4EP6dO3FpkFRMBXqHDku0pl4vtHrWnE1S3J-e86vt0"
GID = "1946114847"  # ✅ your LATEST sheet

CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&gid={GID}"

# ==============================
# LOAD DATA (SAFE)
# ==============================
@st.cache_data(ttl=60)
def load_data(url):
    try:
        res = requests.get(url)

        if res.status_code != 200:
            return None, f"HTTP Error {res.status_code}"

        if "text/html" in res.headers.get("Content-Type", ""):
            return None, "Google returned HTML → check sharing permissions"

        df = pd.read_csv(io.StringIO(res.text), dtype=str)
        df.columns = df.columns.astype(str).str.strip().str.upper()

        return df, None

    except Exception as e:
        return None, str(e)


df, error = load_data(CSV_URL)

if error:
    st.error("❌ Failed to load data")
    st.warning(error)
    st.info("👉 Make sure Google Sheet is set to: Anyone with link → Viewer")
    st.stop()

st.success("✅ Data loaded successfully")
st.info("📄 Data Source: LATEST (auto-updated)")

# ==============================
# VALIDATION
# ==============================
REQUIRED_HEADERS = [
    "SCHOOL NAME","HOSTNAME","SERIAL NUMBER","ASSET TAG",
    "CUSTODIAN","LOCATION","BRAND","MODEL",
    "CATEGORY","IPU STATUS","EOL STATUS"
]

if not all(h in df.columns for h in REQUIRED_HEADERS):
    st.error("❌ Required headers missing")
    st.write("Detected columns:", df.columns.tolist())
    st.stop()

# ==============================
# RAW DATA
# ==============================
st.markdown("## 🗂️ Full Updated Data")
st.dataframe(df, use_container_width=True)

# ==============================
# CLEAN DATA
# ==============================
df["MODEL"] = df["MODEL"].astype(str).str.upper().str.strip()
df["IPU STATUS"] = df["IPU STATUS"].astype(str).str.title().str.strip()

TARGET_MODELS = [
    "ACER VX2670G DESKTOP",
    "LENOVO K14 GEN2",
    "LENOVO L13 YOGA G4"
]

df = df[df["MODEL"].isin(TARGET_MODELS)]

# ==============================
# SUMMARY
# ==============================
summary = df.groupby(["MODEL","IPU STATUS"]).size().unstack(fill_value=0)

for col in ["Completed","Not Completed"]:
    if col not in summary.columns:
        summary[col] = 0

summary = summary.reset_index()
summary["Total"] = summary["Completed"] + summary["Not Completed"]
summary["Completion %"] = (summary["Completed"]/summary["Total"]).fillna(0)*100
summary["Completion %"] = summary["Completion %"].round(2)

# ==============================
# KPIs
# ==============================
st.markdown("## 📊 Overview")

completed = int(summary["Completed"].sum())
not_completed = int(summary["Not Completed"].sum())
total = completed + not_completed
rate = (completed/total*100) if total > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("✅ Completed", completed)
c2.metric("❌ Not Completed", not_completed)
c3.metric("📈 Completion Rate", f"{rate:.2f}%")

# ==============================
# TABLE
# ==============================
st.markdown("## 📋 Upgrade Summary")
st.dataframe(
    summary[["MODEL","Completed","Not Completed","Total","Completion %"]],
    use_container_width=True,
    hide_index=True
)

# ==============================
# CHART
# ==============================
st.markdown("## 📈 Upgrade Progress")

chart_df = summary.melt(
    id_vars=["MODEL","Total"],
    value_vars=["Completed","Not Completed"],
    var_name="Status",
    value_name="Count"
)

chart_df["Percent"] = (chart_df["Count"] / chart_df["Total"] * 100).round(1)
chart_df["Label"] = chart_df["Percent"].astype(str) + "%"

base = alt.Chart(chart_df).encode(
    x=alt.X("MODEL:N", title="Model"),
    y=alt.Y("Count:Q", title="Number of Devices"),
    xOffset="Status:N"
)

bars = base.mark_bar().encode(
    color=alt.Color("Status:N", title="")
)

text = base.mark_text(
    dy=-5,
    fontSize=12
).encode(
    text="Label"
)

chart = (bars + text).properties(height=400)

st.altair_chart(chart, use_container_width=True)

# ==============================
# PROGRESS BARS
# ==============================
st.markdown("## 🔄 Progress by Model")

for _, row in summary.iterrows():
    st.write(f"**{row['MODEL']}** ({row['Completion %']}%)")
    st.progress(row["Completion %"]/100)

# ==============================
# MANUAL REFRESH BUTTON
# ==============================
if st.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()

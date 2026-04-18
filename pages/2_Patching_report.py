import streamlit as st
import pandas as pd
import time
import urllib.parse
import altair as alt

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="Patching Report", layout="wide")

SPREADSHEET_ID = "1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE"

st.title("🛠️ Patching Report Dashboard")
st.caption("Live device health monitoring")

# ==================================================
# AUTO REFRESH (30 sec)
# ==================================================
REFRESH_INTERVAL = 30

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > REFRESH_INTERVAL:
    st.session_state.last_refresh = time.time()
    st.rerun()

# ==================================================
# GET META (Latest Sheet)
# ==================================================
@st.cache_data(ttl=30)
def get_latest_sheet():
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=META"
    df = pd.read_csv(url, header=None)

    if df.shape[0] < 2:
        raise Exception("META sheet missing data")

    sheet_name = str(df.iloc[1, 0]).strip()

    if not sheet_name or sheet_name.lower() == "none":
        raise Exception("LatestSheet is empty")

    return sheet_name

# ==================================================
# LOAD SHEET
# ==================================================
@st.cache_data(ttl=30)
def load_sheet(sheet_name):
    encoded = urllib.parse.quote(sheet_name)

    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"

    df = pd.read_csv(url, dtype=str)

    if df.empty:
        raise Exception("Sheet is empty or inaccessible")

    df.columns = df.columns.str.strip().str.upper()

    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    return df

# ==================================================
# DEVICE STATUS + TOTAL + %
# ==================================================
def device_status_count(df):
    devices = [
        "LENOVO K14 GEN2",
        "LENOVO L13 YOGA G4",
        "ACER VX2670G DESKTOP"
    ]

    statuses = [
        "INSTALLED",
        "SCCM EPP > 4 WKS",
        "NOT CONNECTED",
        "REQUIRED"
    ]

    result = []

    for device in devices:
        row = {"Device": device.title()}
        total = 0

        for status in statuses:
            count = df[
                (df.iloc[:, 6].str.upper() == device) &
                (df.iloc[:, 11].str.upper() == status)
            ].shape[0]

            row[status] = count
            total += count

        row["TOTAL"] = total
        row["% INSTALLED"] = round((row["INSTALLED"] / total * 100), 1) if total else 0

        result.append(row)

    return pd.DataFrame(result)

# ==================================================
# MAIN LOAD
# ==================================================
try:
    sheet_name = get_latest_sheet()
    df = load_sheet(sheet_name)

    st.success(f"📅 Latest Data: {sheet_name}")

except Exception as e:
    st.error("❌ Failed to load data")
    st.exception(e)
    st.stop()

# ==================================================
# DEVICE TABLE (COMBINED)
# ==================================================
device_df = device_status_count(df)

# Clean column names
device_df.columns = [
    "Device",
    "Installed",
    "SCCM > 4 wks",
    "Not Connected",
    "Required",
    "Total",
    "% Installed"
]

st.subheader("💻 Device Status Breakdown")

st.dataframe(
    device_df.style.highlight_min(subset=["% Installed"], color="salmon"),
    use_container_width=True
)

# ==================================================
# 🎨 PROFESSIONAL GROUPED BAR CHART
# ==================================================
st.subheader("📊 Status Distribution (Professional View)")

chart_df = device_df.set_index("Device")[[
    "Installed",
    "SCCM > 4 wks",
    "Not Connected",
    "Required"
]]

long_df = chart_df.reset_index().melt(
    id_vars="Device",
    var_name="Status",
    value_name="Count"
)

# Color scheme
color_scale = alt.Scale(
    domain=[
        "Installed",
        "SCCM > 4 wks",
        "Not Connected",
        "Required"
    ],
    range=[
        "#2ecc71",  # green
        "#f39c12",  # orange
        "#e74c3c",  # red
        "#3498db"   # blue
    ]
)

chart = (
    alt.Chart(long_df)
    .mark_bar(size=35)
    .encode(
        x=alt.X("Device:N", title="Device"),
        xOffset="Status:N",
        y=alt.Y("Count:Q", title="Number of Devices"),
        color=alt.Color("Status:N", scale=color_scale),
        tooltip=["Device", "Status", "Count"]
    )
    .properties(height=400)
)

st.altair_chart(chart, use_container_width=True)

# ==================================================
# RAW DATA
# ==================================================
st.subheader("📄 Raw Data")
st.dataframe(df, use_container_width=True)

# ==================================================
# FOOTER
# ==================================================
st.caption("🔄 Auto refresh every 30 seconds")

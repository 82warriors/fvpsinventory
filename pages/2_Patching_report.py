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
# GET META
# ==================================================
@st.cache_data(ttl=30)
def get_latest_sheet():
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=META"
    df = pd.read_csv(url, header=None)

    if df.shape[0] < 2:
        raise Exception("META sheet missing data")

    return str(df.iloc[1, 0]).strip()

# ==================================================
# LOAD SHEET
# ==================================================
@st.cache_data(ttl=30)
def load_sheet(sheet_name):
    encoded = urllib.parse.quote(sheet_name)

    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"

    df = pd.read_csv(url, dtype=str)

    if df.empty:
        raise Exception("Sheet is empty")

    df.columns = df.columns.str.strip().str.upper()

    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    return df

# ==================================================
# DEVICE CALCULATION (WITH UNKNOWN)
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
        "REQUIRED",
        "UNKNOWN"
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

        percent = (row["INSTALLED"] / total * 100) if total else 0

        row["TOTAL"] = total
        row["% INSTALLED"] = percent

        result.append(row)

    return pd.DataFrame(result)

# ==================================================
# LOAD DATA
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
# TABLE
# ==================================================
device_df = device_status_count(df)

device_df.columns = [
    "Device",
    "Installed",
    "SCCM > 4 wks",
    "Not Connected",
    "Required",
    "Unknown",
    "Total",
    "% Installed"
]

# Format % to 2 decimal places
device_df["% Installed"] = device_df["% Installed"].map(lambda x: f"{x:.2f}")

st.subheader("💻 Device Status Breakdown")

styled_df = (
    device_df.style
    .hide(axis="index")
    .set_properties(**{"text-align": "center"})
    .set_table_styles([
        {
            "selector": "th",
            "props": [
                ("font-weight", "bold"),
                ("color", "black"),
                ("text-align", "center")
            ]
        }
    ])
    .highlight_min(subset=["% Installed"], color="#f28b82")
    .highlight_max(subset=["Unknown"], color="#d3d3d3")  # highlight unknown
)

st.table(styled_df)

# ==================================================
# 📊 PROFESSIONAL CHART (WITH UNKNOWN)
# ==================================================
st.subheader("📊 Status Distribution")

chart_df = device_df.set_index("Device")[[
    "Installed",
    "SCCM > 4 wks",
    "Not Connected",
    "Required",
    "Unknown"
]].astype(int)

long_df = chart_df.reset_index().melt(
    id_vars="Device",
    var_name="Status",
    value_name="Count"
)

color_scale = alt.Scale(
    domain=[
        "Installed",
        "SCCM > 4 wks",
        "Not Connected",
        "Required",
        "Unknown"
    ],
    range=[
        "#2ecc71",  # green
        "#f39c12",  # orange
        "#e74c3c",  # red
        "#3498db",  # blue
        "#95a5a6"   # grey
    ]
)

chart = (
    alt.Chart(long_df)
    .mark_bar(size=35)
    .encode(
        x=alt.X("Device:N"),
        xOffset="Status:N",
        y=alt.Y("Count:Q"),
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

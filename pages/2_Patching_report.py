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
# GET META (LATEST)
# ==================================================
@st.cache_data(ttl=30)
def get_latest_sheet():
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=META"
    df = pd.read_csv(url, header=None)

    if df.shape[0] < 2:
        raise Exception("META sheet missing data")

    return str(df.iloc[1, 0]).strip()

# ==================================================
# GET ALL SHEETS
# ==================================================
@st.cache_data(ttl=60)
def get_all_sheets():
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=META"
    df = pd.read_csv(url, header=None)

    sheets = df.iloc[1:, 0].dropna().tolist()
    return [str(s).strip() for s in sheets]

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
    df = df.apply(lambda x: x.astype(str).str.strip())

    return df

# ==================================================
# DEVICE CALCULATION
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
# LOAD LATEST DATA
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
# LATEST TABLE
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
                ("text-align", "center")
            ]
        }
    ])
    .highlight_min(subset=["% Installed"], color="#f28b82")
    .highlight_max(subset=["Unknown"], color="#d3d3d3")
)

st.table(styled_df)

# ==================================================
# CHART
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

chart = (
    alt.Chart(long_df)
    .mark_bar(size=35)
    .encode(
        x="Device:N",
        xOffset="Status:N",
        y="Count:Q",
        color="Status:N",
        tooltip=["Device", "Status", "Count"]
    )
    .properties(height=400)
)

st.altair_chart(chart, use_container_width=True)

# ==================================================
# 📅 WEEKLY DEVICE BREAKDOWN
# ==================================================
st.subheader("📅 Weekly Device Breakdown")

try:
    sheet_list = get_all_sheets()
except:
    st.error("Failed to load sheet list")
    st.stop()

devices = [
    "Lenovo K14 Gen2",
    "Lenovo L13 Yoga G4",
    "Acer Vx2670G Desktop"
]

for device in devices:
    st.markdown(f"### 💻 {device}")

    weekly_data = []

    for sheet in sheet_list:
        try:
            df_week = load_sheet(sheet)
            temp_df = device_status_count(df_week)

            row = temp_df[temp_df["Device"] == device]

            if not row.empty:
                row = row.iloc[0].to_dict()
                row["Week"] = sheet
                weekly_data.append(row)

        except:
            continue

    if not weekly_data:
        st.warning("No data available")
        continue

    weekly_df = pd.DataFrame(weekly_data)

    weekly_df = weekly_df[[
        "Week",
        "INSTALLED",
        "SCCM EPP > 4 WKS",
        "NOT CONNECTED",
        "REQUIRED",
        "UNKNOWN",
        "TOTAL",
        "% INSTALLED"
    ]]

    weekly_df.columns = [
        "Week",
        "Installed",
        "SCCM > 4 wks",
        "Not Connected",
        "Required",
        "Unknown",
        "Total",
        "% Installed"
    ]

    weekly_df["% Installed"] = weekly_df["% Installed"].map(lambda x: f"{x:.2f}")

    weekly_df = weekly_df.sort_values("Week", ascending=False)

    st.dataframe(weekly_df, use_container_width=True)

# ==================================================
# RAW DATA
# ==================================================
st.subheader("📄 Raw Data")
st.dataframe(df, use_container_width=True)

# ==================================================
# FOOTER
# ==================================================
st.caption("🔄 Auto refresh every 30 seconds")

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
sheet_name = get_latest_sheet()
df = load_sheet(sheet_name)

st.success(f"📅 Latest Data: {sheet_name}")

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

st.dataframe(device_df, use_container_width=True)

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
# 📅 CONSOLIDATED WEEKLY DATA
# ==================================================
st.subheader("📅 Weekly Device Overview")

sheet_list = get_all_sheets()

all_weeks_data = []

for sheet in sheet_list:
    try:
        df_week = load_sheet(sheet)
        temp_df = device_status_count(df_week)
        temp_df["Week"] = sheet
        all_weeks_data.append(temp_df)
    except:
        continue

combined_df = pd.concat(all_weeks_data, ignore_index=True)

combined_df = combined_df[[
    "Week",
    "Device",
    "INSTALLED",
    "SCCM EPP > 4 WKS",
    "NOT CONNECTED",
    "REQUIRED",
    "UNKNOWN",
    "TOTAL",
    "% INSTALLED"
]]

combined_df.columns = [
    "Week",
    "Device",
    "Installed",
    "SCCM > 4 wks",
    "Not Connected",
    "Required",
    "Unknown",
    "Total",
    "% Installed"
]

combined_df["% Installed"] = combined_df["% Installed"].map(lambda x: f"{x:.2f}")

# ==================================================
# 🔍 FILTERS
# ==================================================
st.markdown("### 🔍 Filters")

col1, col2 = st.columns(2)

with col1:
    selected_week = st.selectbox(
        "Select Week",
        ["All"] + sorted(combined_df["Week"].unique(), reverse=True)
    )

with col2:
    selected_device = st.selectbox(
        "Select Device",
        ["All"] + sorted(combined_df["Device"].unique())
    )

# Apply filters
filtered_df = combined_df.copy()

if selected_week != "All":
    filtered_df = filtered_df[filtered_df["Week"] == selected_week]

if selected_device != "All":
    filtered_df = filtered_df[filtered_df["Device"] == selected_device]

# ==================================================
# DISPLAY FILTERED TABLE
# ==================================================
st.dataframe(filtered_df, use_container_width=True)

# ==================================================
# FOOTER
# ==================================================
st.caption("🔄 Auto refresh every 30 seconds")

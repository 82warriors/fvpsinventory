import streamlit as st
import pandas as pd
import time
import urllib.parse
import altair as alt

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="Patching Report Dashboard",
    layout="wide"
)

SPREADSHEET_ID = "1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE"

st.title("🛠️ Patching Report Dashboard")
st.caption("Live device health monitoring with historical weekly tracking")

# ==================================================
# AUTO REFRESH
# ==================================================
REFRESH_INTERVAL = 30

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > REFRESH_INTERVAL:
    st.session_state.last_refresh = time.time()
    st.rerun()

# ==================================================
# GET LATEST SHEET
# ==================================================
@st.cache_data(ttl=30)
def get_latest_sheet():

    url = (
        f"https://docs.google.com/spreadsheets/d/"
        f"{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=META"
    )

    df = pd.read_csv(url, header=None)

    return str(df.iloc[1, 0]).strip()

# ==================================================
# GET ALL SHEETS
# ==================================================
@st.cache_data(ttl=60)
def get_all_sheets():

    url = (
        f"https://docs.google.com/spreadsheets/d/"
        f"{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=META"
    )

    df = pd.read_csv(url, header=None)

    sheets = df.iloc[1:, 0].dropna().tolist()

    return [str(s).strip() for s in sheets]

# ==================================================
# LOAD SHEET
# ==================================================
@st.cache_data(ttl=30)
def load_sheet(sheet_name):

    encoded = urllib.parse.quote(sheet_name)

    url = (
        f"https://docs.google.com/spreadsheets/d/"
        f"{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
    )

    df = pd.read_csv(url, dtype=str)

    df.columns = df.columns.str.strip().str.upper()

    df = df.fillna("")

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

    results = []

    for device in devices:

        row = {
            "Device": device.title()
        }

        total = 0

        for status in statuses:

            count = df[
                (df.iloc[:, 6].str.upper() == device) &
                (df.iloc[:, 11].str.upper() == status)
            ].shape[0]

            row[status] = count

            total += count

        percent = (row["INSTALLED"] / total * 100) if total > 0 else 0

        row["TOTAL"] = total
        row["% INSTALLED"] = round(percent, 2)

        results.append(row)

    return pd.DataFrame(results)

# ==================================================
# LOAD CURRENT WEEK
# ==================================================
latest_sheet = get_latest_sheet()

latest_df = load_sheet(latest_sheet)

st.success(f"📅 Current Week: {latest_sheet}")

# ==================================================
# CURRENT WEEK BREAKDOWN
# ==================================================
st.subheader("💻 Current Week Device Breakdown")

current_df = device_status_count(latest_df)

current_df.columns = [
    "Device",
    "Installed",
    "SCCM > 4 wks",
    "Not Connected",
    "Required",
    "Unknown",
    "Total",
    "% Installed"
]

display_current_df = current_df.copy()

display_current_df["% Installed"] = (
    display_current_df["% Installed"]
    .map(lambda x: f"{x:.2f}")
)

st.dataframe(
    display_current_df,
    use_container_width=True,
    hide_index=True
)

# ==================================================
# CURRENT WEEK CHART
# ==================================================
st.subheader("📊 Current Week Status Distribution")

chart_df = current_df.set_index("Device")[[
    "Installed",
    "SCCM > 4 wks",
    "Not Connected",
    "Required",
    "Unknown"
]].astype(int)

long_df = (
    chart_df
    .reset_index()
    .melt(
        id_vars="Device",
        var_name="Status",
        value_name="Count"
    )
)

chart = (
    alt.Chart(long_df)
    .mark_bar(size=35)
    .encode(
        x=alt.X("Device:N", title="Device"),
        xOffset="Status:N",
        y=alt.Y("Count:Q", title="Count"),
        color="Status:N",
        tooltip=["Device", "Status", "Count"]
    )
    .properties(height=400)
)

st.altair_chart(chart, use_container_width=True)

# ==================================================
# LOAD ALL HISTORICAL DATA
# ==================================================
sheet_list = get_all_sheets()

all_data = []

progress = st.progress(0)

for index, sheet in enumerate(sheet_list):

    try:

        temp_sheet_df = load_sheet(sheet)

        temp_result_df = device_status_count(temp_sheet_df)

        temp_result_df["Week"] = sheet

        all_data.append(temp_result_df)

    except:
        pass

    progress.progress((index + 1) / len(sheet_list))

progress.empty()

# ==================================================
# COMBINE HISTORICAL DATA
# ==================================================
combined_df = pd.concat(all_data, ignore_index=True)

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

# ==================================================
# CONVERT DATE
# ==================================================
def convert_week(x):

    try:
        return pd.to_datetime(x, dayfirst=True)
    except:
        return pd.NaT

combined_df["Week_Date"] = combined_df["Week"].apply(convert_week)

combined_df = combined_df.sort_values(
    by="Week_Date",
    ascending=False
)

# ==================================================
# FILTERS
# ==================================================
st.markdown("### 🔍 Filters")

col1, col2 = st.columns(2)

with col1:

    selected_week = st.selectbox(
        "Select Week",
        ["All"] + combined_df["Week"].dropna().unique().tolist()
    )

with col2:

    selected_device = st.selectbox(
        "Select Device",
        ["All"] + sorted(combined_df["Device"].unique())
    )

# ==================================================
# APPLY FILTERS
# ==================================================
filtered_df = combined_df.copy()

if selected_week != "All":

    filtered_df = filtered_df[
        filtered_df["Week"] == selected_week
    ]

if selected_device != "All":

    filtered_df = filtered_df[
        filtered_df["Device"] == selected_device
    ]

# ==================================================
# FORMAT DISPLAY
# ==================================================
display_df = filtered_df.copy()

display_df["% Installed"] = (
    display_df["% Installed"]
    .map(lambda x: f"{x:.2f}")
)

display_df = display_df.drop(columns=["Week_Date"])

# ==================================================
# DATABASE TABS
# ==================================================
tab1, tab2 = st.tabs([
    "📅 Historical Weekly Database",
    "🗄️ Raw Database"
])

# ==================================================
# TAB 1 - HISTORICAL DATABASE
# ==================================================
with tab1:

    st.subheader("📅 Historical Weekly Breakdown")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

# ==================================================
# TAB 2 - RAW DATABASE
# ==================================================
with tab2:

    st.subheader("🗄️ Raw Weekly Database")

    raw_database = []

    progress2 = st.progress(0)

    for index, sheet in enumerate(sheet_list):

        try:

            temp_raw_df = load_sheet(sheet)

            temp_raw_df["WEEK"] = sheet

            raw_database.append(temp_raw_df)

        except:
            pass

        progress2.progress((index + 1) / len(sheet_list))

    progress2.empty()

    raw_df = pd.concat(raw_database, ignore_index=True)

    st.dataframe(
        raw_df,
        use_container_width=True,
        height=600
    )

# ==================================================
# FOOTER
# ==================================================
st.caption("🔄 Auto refresh every 30 seconds")

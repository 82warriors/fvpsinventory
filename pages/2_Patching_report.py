import streamlit as st
import pandas as pd
import time
import urllib.parse
import altair as alt

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(
    page_title="Patching Report Dashboard",
    layout="wide"
)

SPREADSHEET_ID = "1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE"

st.title("🛠️ Patching Report Dashboard")
st.caption("Live device health monitoring with weekly historical breakdown")

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
# LOAD META
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

    return [str(x).strip() for x in sheets]

# ==================================================
# LOAD GOOGLE SHEET
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
# DEVICE STATUS COUNT
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

        result.append(row)

    return pd.DataFrame(result)

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

current_device_df = device_status_count(latest_df)

current_device_df.columns = [
    "Device",
    "Installed",
    "SCCM > 4 wks",
    "Not Connected",
    "Required",
    "Unknown",
    "Total",
    "% Installed"
]

display_current = current_device_df.copy()

display_current["% Installed"] = (
    display_current["% Installed"]
    .map(lambda x: f"{x:.2f}")
)

st.dataframe(
    display_current,
    use_container_width=True,
    hide_index=True
)

# ==================================================
# CURRENT WEEK CHART
# ==================================================
st.subheader("📊 Current Week Status Distribution")

chart_df = current_device_df.set_index("Device")[[
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
# LOAD ALL WEEK DATABASE
# ==================================================
st.subheader("🗂️ Historical Weekly Database")

sheet_list = get_all_sheets()

database_list = []

progress = st.progress(0)

for index, sheet in enumerate(sheet_list):

    try:
        week_df = load_sheet(sheet)

        temp = device_status_count(week_df)

        temp["Week"] = sheet

        database_list.append(temp)

    except:
        pass

    progress.progress((index + 1) / len(sheet_list))

progress.empty()

# ==================================================
# COMBINE DATABASE
# ==================================================
combined_df = pd.concat(database_list, ignore_index=True)

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
# SORT WEEKS PROPERLY
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
st.markdown("### 🔍 Database Filters")

col1, col2, col3 = st.columns(3)

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

with col3:

    selected_status = st.selectbox(
        "View",
        [
            "All",
            "Installed Only",
            "Non Installed"
        ]
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

if selected_status == "Installed Only":
    filtered_df = filtered_df[
        filtered_df["Installed"] > 0
    ]

if selected_status == "Non Installed":
    filtered_df = filtered_df[
        (
            filtered_df["SCCM > 4 wks"] +
            filtered_df["Not Connected"] +
            filtered_df["Required"] +
            filtered_df["Unknown"]
        ) > 0
    ]


# ==================================================
# DISPLAY DATABASE
# ==================================================
display_df = filtered_df.copy()

display_df["% Installed"] = (
    display_df["% Installed"]
    .map(lambda x: f"{x:.2f}")
)

display_df = display_df.drop(columns=["Week_Date"])

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)

# ==================================================
# HISTORICAL TREND CHART
# ==================================================
st.subheader("📈 Historical Installation Trend")

trend_df = combined_df.copy()

if selected_device != "All":
    trend_df = trend_df[
        trend_df["Device"] == selected_device
    ]

line_chart = (
    alt.Chart(trend_df)
    .mark_line(point=True)
    .encode(
        x=alt.X("Week_Date:T", title="Week"),
        y=alt.Y("% Installed:Q", title="% Installed"),
        color="Device:N",
        tooltip=[
            "Week",
            "Device",
            "% Installed"
        ]
    )
    .properties(height=400)
)

st.altair_chart(line_chart, use_container_width=True)

# ==================================================
# RAW DATABASE
# ==================================================
with st.expander("🗄️ View Raw Database"):

    raw_database = []

    for sheet in sheet_list:

        try:
            temp_df = load_sheet(sheet)

            temp_df["WEEK"] = sheet

            raw_database.append(temp_df)

        except:
            pass

    raw_df = pd.concat(raw_database, ignore_index=True)

    st.dataframe(
        raw_df,
        use_container_width=True,
        height=500
    )

# ==================================================
# FOOTER
# ==================================================
st.caption("🔄 Dashboard auto refreshes every 30 seconds")

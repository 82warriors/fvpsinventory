import streamlit as st
import pandas as pd
import html
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="FVPS Inventory", layout="wide")
st.title("📦 FVPS Inventory System")

# ==================================================
# AUTO REFRESH
# ==================================================
st_autorefresh(interval=30 * 1000, key="datarefresh")

# ==================================================
# CONSTANTS
# ==================================================
MASTER_COLUMNS = [
    "Status","Category","EquipmentType","Vendor","BrandModel",
    "Profile","Custodian",
    "AssetNo","SerialNumber",
    "Location","Venue",
    "StartDate","EndDate",
    "Hostname","SSOE PO Number","Cart No",
    "What's in the box","Upgrade Item List","Addon Item List","Bundle Item list",
    "Lamp Hour","HDMI",
    "Duration in Use","Fault","Last Updated","Remarks"
]

BASE_URL = "https://docs.google.com/spreadsheets/d/1lmCotLUgTLJBKska2y7od2LTPT_qooIFS0_zyVnRI0A/export?format=csv&gid="

# ==================================================
# LOAD DATA
# ==================================================
@st.cache_data(ttl=30)
def load_data(gid, sheet_name, header_row):
    try:
        df = pd.read_csv(BASE_URL + gid, header=header_row)

        df.columns = df.columns.astype(str).str.strip()
        df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]

        # ==================================================
        # CLEAN LOCATION
        # ==================================================
        if "Location" in df.columns:
            df["Location"] = df["Location"].apply(
                lambda x: str(int(float(x))).zfill(2)
                if pd.notna(x) and str(x).replace('.', '', 1).isdigit()
                else x
            )

        # ==================================================
        # CLEAN TEXT
        # ==================================================
        if "EquipmentType" in df.columns:
            df["EquipmentType"] = (
                df["EquipmentType"]
                .astype(str)
                .str.strip()
                .str.title()
            )

        if "BrandModel" in df.columns:
            df["BrandModel"] = (
                df["BrandModel"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

        # ==================================================
        # DATE COLUMNS
        # ==================================================
        for col in ["StartDate", "EndDate", "Last Updated"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # ==================================================
        # CATEGORY
        # ==================================================
        df["Category"] = "SSOE" if sheet_name == "SSOE" else "NON-SSOE"

        # ==================================================
        # ENSURE ALL COLUMNS EXIST
        # ==================================================
        for col in MASTER_COLUMNS:
            if col not in df.columns:
                df[col] = None

        return df

    except Exception as e:
        st.error(f"Error loading {sheet_name}: {e}")
        return pd.DataFrame(columns=MASTER_COLUMNS)

# ==================================================
# LOAD ALL DATA
# ==================================================
def load_all():
    datasets = [
        ("555308035", "SSOE", 3),
        ("1895613573", "Level 1", 3),
        ("451567212", "Level 2", 3),
        ("365079300", "Level 3", 3),
        ("1105352624", "Level 4", 3),
        ("1046028540", "Level 6", 3),
        ("1253302028", "Others", 2),
    ]

    frames = [load_data(gid, name, header) for gid, name, header in datasets]

    df = pd.concat(frames, ignore_index=True)

    if "BrandModel" in df.columns and "EquipmentType" in df.columns:
        df = df[
            df["BrandModel"].notna() &
            df["EquipmentType"].notna()
        ]

    return df

df = load_all()

# ==================================================
# FILTERS
# ==================================================
st.subheader("🔍 Filters")

col1, col2, col3 = st.columns(3)

with col1:
    category = st.selectbox(
        "Category",
        ["All", "SSOE", "NON-SSOE"]
    )

with col2:
    eq_list = sorted(df["EquipmentType"].dropna().unique())
    eq = st.selectbox(
        "Equipment Type",
        ["All"] + eq_list
    )

with col3:
    search = st.text_input("🔎 Search")

# ==================================================
# APPLY FILTERS
# ==================================================
filtered_df = df.copy()

if category != "All":
    filtered_df = filtered_df[
        filtered_df["Category"] == category
    ]

if eq != "All":
    filtered_df = filtered_df[
        filtered_df["EquipmentType"] == eq
    ]

if search:
    filtered_df = filtered_df[
        filtered_df.apply(
            lambda row: row.astype(str)
            .str.contains(search, case=False)
            .any(),
            axis=1
        )
    ]

# ==================================================
# EXPIRY STATUS
# ==================================================
def get_expiry_status(date):
    if pd.isna(date):
        return ""

    today = pd.Timestamp.today()

    if date < today:
        return "Expired"

    elif date <= today + pd.Timedelta(days=30):
        return "Expiring Soon"

    return "Active"

filtered_df["Expiry Status"] = (
    filtered_df["EndDate"]
    .apply(get_expiry_status)
)

# ==================================================
# OVERVIEW
# ==================================================
st.subheader("📊 Overview")

c1, c2, c3, c4 = st.columns(4)

c1.metric("💻 Total Devices", len(filtered_df))

c2.metric(
    "🖥️ SSOE",
    len(filtered_df[
        filtered_df["Category"] == "SSOE"
    ])
)

c3.metric(
    "📦 NON-SSOE",
    len(filtered_df[
        filtered_df["Category"] == "NON-SSOE"
    ])
)

fault_count = filtered_df["Fault"].notna().sum() if "Fault" in filtered_df.columns else 0
c4.metric("⚠️ Fault Reports", fault_count)

# ==================================================
# EXPIRY SUMMARY
# ==================================================
st.subheader("⏳ Expiry Summary")

expiry_counts = filtered_df["Expiry Status"].value_counts()

expired = expiry_counts.get("Expired", 0)
expiring = expiry_counts.get("Expiring Soon", 0)
active = expiry_counts.get("Active", 0)

e1, e2, e3 = st.columns(3)

e1.metric("🔴 Expired", expired)
e2.metric("🟡 Expiring Soon", expiring)
e3.metric("🟢 Active", active)

# ==================================================
# EQUIPMENT DISTRIBUTION
# ==================================================
st.subheader("📊 Equipment Distribution")

equipment_counts = (
    filtered_df["EquipmentType"]
    .value_counts()
    .reset_index()
)

equipment_counts.columns = [
    "Equipment Type",
    "Count"
]

# ==================================================
# PIE CHART
# ==================================================
fig = px.pie(
    equipment_counts,
    names="Equipment Type",
    values="Count",
    hole=0.4
)

st.plotly_chart(fig, use_container_width=True)

# ==================================================
# SUMMARY TABLE STYLE
# ==================================================
def render_summary_table(df):

    html_table = """
    <style>
    .summary-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 15px;
    }

    .summary-table th {
        background-color: #1f4e79;
        color: white;
        padding: 10px;
        border: 2px solid black;
        text-align: center;
    }

    .summary-table td {
        padding: 8px;
        border: 2px solid black;
        text-align: center;
    }
    </style>

    <table class="summary-table">
    <thead><tr>
    """

    for col in df.columns:
        html_table += f"<th>{col}</th>"

    html_table += "</tr></thead><tbody>"

    for _, row in df.iterrows():

        html_table += "<tr>"

        for val in row:
            html_table += f"<td>{val}</td>"

        html_table += "</tr>"

    html_table += "</tbody></table>"

    return html_table

st.markdown(
    render_summary_table(equipment_counts),
    unsafe_allow_html=True
)

# ==================================================
# DOWNLOAD
# ==================================================
st.download_button(
    "⬇️ Download CSV",
    filtered_df.to_csv(index=False),
    file_name="inventory.csv",
    mime="text/csv"
)

# ==================================================
# TABLE STYLE
# ==================================================
def render_table(df):

    html_table = """
    <style>

    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }

    .custom-table th {
        background-color: #2e7d32;
        color: white;
        padding: 10px;
        border: 2px solid #111;
        position: sticky;
        top: 0;
        z-index: 100;
    }

    .custom-table td {
        padding: 8px;
        border: 2px solid #333;
        text-align: center;
    }

    .expired {
        background-color: #f8d7da;
    }

    .warning {
        background-color: #fff3cd;
    }

    .active {
        background-color: #d4edda;
    }

    </style>

    <div style='overflow-x:auto; max-height:700px;'>

    <table class="custom-table">
    <thead><tr>
    """

    for col in df.columns:
        html_table += f"<th>{html.escape(str(col))}</th>"

    html_table += "</tr></thead><tbody>"

    today = pd.Timestamp.today()

    for _, row in df.iterrows():

        html_table += "<tr>"

        for col, val in row.items():

            cell_class = ""

            if col == "EndDate" and pd.notna(val):

                if val < today:
                    cell_class = "expired"

                elif val <= today + pd.Timedelta(days=30):
                    cell_class = "warning"

                else:
                    cell_class = "active"

            # ==================================================
            # DATE FORMAT
            # ==================================================
            if pd.isna(val):
                safe_val = ""

            elif col in ["StartDate", "EndDate", "Last Updated"]:

                if isinstance(val, pd.Timestamp):
                    safe_val = val.strftime("%d %b %Y")

                else:
                    safe_val = str(val)

            else:
                safe_val = html.escape(str(val))

            html_table += (
                f"<td class='{cell_class}'>{safe_val}</td>"
            )

        html_table += "</tr>"

    html_table += "</tbody></table></div>"

    return html_table

# ==================================================
# TABS
# ==================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Full Inventory",
    "⏳ Expiry Tracking",
    "⚠️ Fault Tracking",
    "🗄️ Database"
])

# ==================================================
# FULL INVENTORY
# ==================================================
with tab1:

    st.subheader("📋 Full Inventory Data")

    st.markdown(
        render_table(filtered_df),
        unsafe_allow_html=True
    )

# ==================================================
# EXPIRY TRACKING
# ==================================================
with tab2:

    st.subheader("⏳ Expiry Tracking")

    expiry_df = (
        filtered_df[
            filtered_df["EndDate"].notna()
        ]
        .sort_values(by="EndDate")
    )

    st.markdown(
        render_table(expiry_df),
        unsafe_allow_html=True
    )

# ==================================================
# FAULT TRACKING
# ==================================================
with tab3:

    st.subheader("⚠️ Fault Tracking")

    fault_df = filtered_df[
        filtered_df["Fault"].notna()
    ]

    if len(fault_df) > 0:

        st.markdown(
            render_table(fault_df),
            unsafe_allow_html=True
        )

    else:
        st.success("✅ No active faults found")

# ==================================================
# DATABASE VIEW
# ==================================================
with tab4:

    st.subheader("🗄️ Database View")

    db_search = st.text_input(
        "🔎 Search Database",
        key="dbsearch"
    )

    database_df = filtered_df.copy()

    if db_search:
        database_df = database_df[
            database_df.apply(
                lambda row: row.astype(str)
                .str.contains(db_search, case=False)
                .any(),
                axis=1
            )
        ]

    st.dataframe(
        database_df,
        use_container_width=True,
        height=700
    )

# ==================================================
# FOOTER
# ==================================================
st.caption("🔄 Auto refresh every 30 seconds")

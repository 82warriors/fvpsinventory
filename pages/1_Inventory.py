import streamlit as st
import pandas as pd
import html

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="FVPS Inventory", layout="wide")
st.title("📦 Inventory System")

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
# LOAD DATA (CACHED)
# ==================================================
@st.cache_data(ttl=300)
def load_data(gid, sheet_name, header_row):
    try:
        df = pd.read_csv(BASE_URL + gid, header=header_row)

        # Clean columns
        df.columns = df.columns.astype(str).str.strip()
        df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]

        # Fix Location
        if "Location" in df.columns:
            df["Location"] = df["Location"].apply(
                lambda x: str(int(float(x))).zfill(2)
                if pd.notna(x) and str(x).replace('.', '', 1).isdigit()
                else x
            )

        # Clean text fields
        if "EquipmentType" in df.columns:
            df["EquipmentType"] = (
                df["EquipmentType"].astype(str).str.strip().str.title()
            )

        if "BrandModel" in df.columns:
            df["BrandModel"] = (
                df["BrandModel"].astype(str).str.strip().str.upper()
            )

        # Dates
        date_cols = ["StartDate", "EndDate", "Last Updated"]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Category
        df["Category"] = "SSOE" if sheet_name == "SSOE" else "NON-SSOE"

        # Align columns
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

    # Remove junk rows safely
    if "BrandModel" in df.columns and "EquipmentType" in df.columns:
        df = df[df["BrandModel"].notna() & df["EquipmentType"].notna()]

    return df

df = load_all()

# ==================================================
# FILTERS
# ==================================================
st.subheader("🔍 Filters")

col1, col2, col3 = st.columns(3)

with col1:
    category = st.selectbox("Category", ["All", "SSOE", "NON-SSOE"])

with col2:
    eq_list = sorted(df["EquipmentType"].dropna().unique())
    eq = st.selectbox("Equipment", ["All"] + eq_list)

with col3:
    search = st.text_input("🔎 Search")

# ==================================================
# APPLY FILTERS
# ==================================================
filtered_df = df.copy()

if category != "All":
    filtered_df = filtered_df[filtered_df["Category"] == category]

if eq != "All":
    filtered_df = filtered_df[filtered_df["EquipmentType"] == eq]

if search:
    filtered_df = filtered_df[
        filtered_df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
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

if "EndDate" in filtered_df.columns:
    filtered_df["Expiry Status"] = filtered_df["EndDate"].apply(get_expiry_status)

# ==================================================
# SUMMARY
# ==================================================
st.subheader("📊 Overview")

c1, c2, c3 = st.columns(3)
c1.metric("Total Devices", len(filtered_df))
c2.metric("SSOE", len(filtered_df[filtered_df["Category"] == "SSOE"]))
c3.metric("NON-SSOE", len(filtered_df[filtered_df["Category"] == "NON-SSOE"]))

# ==================================================
# CHART
# ==================================================
st.subheader("📊 Equipment Distribution")
st.bar_chart(filtered_df["EquipmentType"].value_counts())

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
# TABLE RENDER
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
        border: 1px solid #222;
    }
    .custom-table td {
        padding: 8px;
        border: 1px solid #444;
        text-align: center;
    }
    .expired { background-color: #f8d7da; }
    .warning { background-color: #fff3cd; }
    </style>
    <table class="custom-table"><thead><tr>
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

            safe_val = "" if pd.isna(val) else html.escape(str(val))
            html_table += f"<td class='{cell_class}'>{safe_val}</td>"

        html_table += "</tr>"

    html_table += "</tbody></table>"
    return html_table

# ==================================================
# TABS
# ==================================================
tab1, tab2 = st.tabs(["📋 Full Inventory", "⏳ Expiry Tracking"])

with tab1:
    st.subheader("📋 Inventory Data")
    st.markdown(render_table(filtered_df), unsafe_allow_html=True)

with tab2:
    st.subheader("⏳ Expiry Tracking")

    expiry_df = filtered_df[
        filtered_df["EndDate"].notna()
    ].sort_values(by="EndDate")

    st.markdown(render_table(expiry_df), unsafe_allow_html=True)

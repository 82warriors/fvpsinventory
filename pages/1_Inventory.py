import streamlit as st
import pandas as pd
import html   # ✅ IMPORTANT (fix for broken HTML)

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="FVPS Inventory", layout="wide")

st.title("📦 Inventory System")

# ==================================================
# MASTER COLUMNS
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

# ==================================================
# GOOGLE SHEET BASE URL
# ==================================================
BASE_URL = "https://docs.google.com/spreadsheets/d/1lmCotLUgTLJBKska2y7od2LTPT_qooIFS0_zyVnRI0A/export?format=csv&gid="

# ==================================================
# LOAD FUNCTION
# ==================================================
def load_data(gid, sheet_name, header_row):
    try:
        df = pd.read_csv(BASE_URL + gid, header=header_row)

        df.columns = df.columns.astype(str).str.strip()
        df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]

        # Fix Location → 01, 02
        if "Location" in df.columns:
            df["Location"] = df["Location"].apply(
                lambda x: str(int(float(x))).zfill(2)
                if pd.notna(x) and str(x).replace('.', '', 1).isdigit()
                else x
            )

        # Clean EquipmentType
        if "EquipmentType" in df.columns:
            df["EquipmentType"] = (
                df["EquipmentType"]
                .astype(str)
                .str.strip()
                .str.title()
                .replace({"Nan": None, "None": None, "": None})
            )

        # Clean BrandModel
        if "BrandModel" in df.columns:
            df["BrandModel"] = (
                df["BrandModel"]
                .astype(str)
                .str.strip()
                .str.upper()
                .replace({"NAN": None, "NONE": None, "": None})
            )

        # ✅ Convert + format EndDate
        if "EndDate" in df.columns:
            df["EndDate"] = pd.to_datetime(df["EndDate"], errors="coerce")
            df["EndDate_Display"] = df["EndDate"].dt.strftime("%d %B %Y")

        # Force Category
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
# LOAD DATA
# ==================================================
ssoe = load_data("555308035", "SSOE", 3)

lvl1 = load_data("1895613573", "Level 1", 3)
lvl2 = load_data("451567212", "Level 2", 3)
lvl3 = load_data("365079300", "Level 3", 3)
lvl4 = load_data("1105352624", "Level 4", 3)
lvl6 = load_data("1046028540", "Level 6", 3)

others = load_data("1253302028", "Others", 2)

df = pd.concat([ssoe, lvl1, lvl2, lvl3, lvl4, lvl6, others], ignore_index=True)

# Remove empty rows
df = df[
    df["BrandModel"].notna() &
    df["EquipmentType"].notna()
]

# ==================================================
# FILTERS
# ==================================================
st.subheader("🔍 Filters")

col1, col2 = st.columns(2)

with col1:
    category = st.selectbox("Category", ["All", "SSOE", "NON-SSOE"])

with col2:
    if category == "SSOE":
        eq_list = ["Printer", "Notebook", "Mobile Devices", "Others", "Wog"]
    elif category == "NON-SSOE":
        eq_list = sorted(df[df["Category"] == "NON-SSOE"]["EquipmentType"].dropna().unique())
    else:
        eq_list = sorted(df["EquipmentType"].dropna().unique())

    eq = st.selectbox("Equipment", ["All"] + list(eq_list))

# ==================================================
# APPLY FILTERS
# ==================================================
filtered_df = df.copy()

if category != "All":
    filtered_df = filtered_df[filtered_df["Category"] == category]

if eq != "All":
    filtered_df = filtered_df[filtered_df["EquipmentType"] == eq]

# ==================================================
# SUMMARY
# ==================================================
st.subheader("📊 Overview")

c1, c2, c3 = st.columns(3)
c1.metric("Total Devices", len(filtered_df))
c2.metric("SSOE", len(filtered_df[filtered_df["Category"] == "SSOE"]))
c3.metric("NON-SSOE", len(filtered_df[filtered_df["Category"] == "NON-SSOE"]))

# ==================================================
# TABLE RENDER (SAFE HTML + EXPIRY)
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
        font-weight: bold;
        padding: 10px;
        border: 2px solid #222;
        text-align: center;
    }

    .custom-table td {
        padding: 8px;
        border: 1px solid #444;
        text-align: center;
    }

    .expired { background-color: #f8d7da; }
    .warning { background-color: #fff3cd; }
    </style>

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

            if col in ["EndDate", "Expiry Date"] and pd.notna(val):
                try:
                    date_val = pd.to_datetime(val)
                    if date_val < today:
                        cell_class = "expired"
                    elif date_val <= today + pd.Timedelta(days=30):
                        cell_class = "warning"
                except:
                    pass

            safe_val = "" if pd.isna(val) else html.escape(str(val))  # ✅ FIX
            html_table += f"<td class='{cell_class}'>{safe_val}</td>"

        html_table += "</tr>"

    html_table += "</tbody></table>"
    return html_table

# ==================================================
# TABS
# ==================================================
tab1, tab2 = st.tabs(["📋 Full Inventory", "⏳ Equipment Expiry"])

# TAB 1
with tab1:
    st.subheader("📋 Inventory Data")
    st.markdown(render_table(filtered_df), unsafe_allow_html=True)

# TAB 2
with tab2:
    st.subheader("⏳ Expiry Tracking")

    expiry_df = (
        filtered_df
        .groupby("BrandModel")
        .agg({
            "EndDate": "min",
            "BrandModel": "count"
        })
        .rename(columns={
            "EndDate": "Expiry Date",
            "BrandModel": "Count"
        })
        .reset_index()
        .sort_values(by="Expiry Date", ascending=True)
    )

    st.markdown(render_table(expiry_df), unsafe_allow_html=True)

import streamlit as st
import pandas as pd

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="FVPS Inventory", layout="wide")

st.title("📦 Inventory System")

# ==================================================
# MASTER COLUMN STRUCTURE
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
# LOAD DATA FUNCTION
# ==================================================
def load_data(gid, sheet_name, header_row):
    try:
        df = pd.read_csv(BASE_URL + gid, header=header_row)

        df.columns = df.columns.astype(str).str.strip()
        df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]

        # Normalize EquipmentType
        if "EquipmentType" in df.columns:
            df["EquipmentType"] = (
                df["EquipmentType"]
                .astype(str)
                .str.strip()
                .str.title()
                .replace({"Nan": None, "None": None, "": None})
            )

        df["Category"] = "SSOE" if sheet_name == "SSOE" else "NON-SSOE"

        for col in MASTER_COLUMNS:
            if col not in df.columns:
                df[col] = None

        return df[MASTER_COLUMNS]

    except Exception as e:
        st.error(f"Error loading {sheet_name}: {e}")
        return pd.DataFrame(columns=MASTER_COLUMNS)

# ==================================================
# LOAD DATA
# ==================================================
ssoe = load_data("555308035", "SSOE", header_row=3)

lvl1 = load_data("1895613573", "Level 1", header_row=3)
lvl2 = load_data("451567212", "Level 2", header_row=3)
lvl3 = load_data("365079300", "Level 3", header_row=3)
lvl4 = load_data("1105352624", "Level 4", header_row=3)
lvl6 = load_data("1046028540", "Level 6", header_row=3)

others = load_data("1253302028", "Others", header_row=2)

df = pd.concat([ssoe, lvl1, lvl2, lvl3, lvl4, lvl6, others], ignore_index=True)
df = df.dropna(how="all")

# ==================================================
# FILTERS
# ==================================================
st.subheader("🔍 Filters")

col1, col2 = st.columns(2)

with col1:
    category = st.selectbox("Category", ["All", "SSOE", "NON-SSOE"])

with col2:
    if "EquipmentType" in df.columns:

        if category == "SSOE":
            eq_list = ["Printer", "Notebook", "Mobile Devices", "Others", "Wog"]

        elif category == "NON-SSOE":
            eq_series = df[df["Category"] == "NON-SSOE"]["EquipmentType"]
            eq_list = sorted([x for x in eq_series.dropna().unique() if x])

        else:
            eq_series = df["EquipmentType"]
            eq_list = sorted([x for x in eq_series.dropna().unique() if x])

        eq = st.selectbox("Equipment", ["All"] + eq_list)

    else:
        eq = "All"

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
# 🎨 HTML TABLE RENDER
# ==================================================
def render_table(df):
    html = """
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

    .custom-table tr:nth-child(even) {
        background-color: #f4f4f4;
    }

    .custom-table tr:hover {
        background-color: #e8f5e9;
    }
    </style>

    <table class="custom-table">
        <thead><tr>
    """

    for col in df.columns:
        html += f"<th>{col}</th>"

    html += "</tr></thead><tbody>"

    for _, row in df.iterrows():
        html += "<tr>"
        for val in row:
            html += f"<td>{'' if pd.isna(val) else val}</td>"
        html += "</tr>"

    html += "</tbody></table>"

    return html

# ==================================================
# DISPLAY
# ==================================================
st.subheader("📋 Inventory Data")

st.markdown(render_table(filtered_df), unsafe_allow_html=True)

import streamlit as st
import pandas as pd

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="FVPS Inventory", layout="wide")

st.title("📦 Inventory System")

# ==================================================
# MASTER COLUMN STRUCTURE (UNIFIED)
# ==================================================
MASTER_COLUMNS = [
    "Status","Category","EquipmentType","Vendor","BrandModel","Profile","Custodian",
    "AssetNo","SerialNumber","Location","Venue",
    "StartDate","EndDate","Hostname","SSOE PO Number","Cart No",
    "What's in the box","Upgrade Item List","Addon Item List","Bundle Item list",
    "Duration in Use","Fault","Last Updated","Remarks"
]

# ==================================================
# GOOGLE SHEET BASE URL
# ==================================================
BASE_URL = "https://docs.google.com/spreadsheets/d/1lmCotLUgTLJBKska2y7od2LTPT_qooIFS0_zyVnRI0A/export?format=csv&gid="

# ==================================================
# LOAD + ALIGN FUNCTION
# ==================================================
def load_data(gid, sheet_name, header_row):
    try:
        df = pd.read_csv(BASE_URL + gid, header=header_row)

        # Clean headers
        df.columns = df.columns.astype(str).str.strip()
        df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]

        # Clean EquipmentType
        if "EquipmentType" in df.columns:
            df["EquipmentType"] = (
                df["EquipmentType"]
                .astype(str)
                .str.strip()
                .replace({"nan": None, "None": None, "": None})
            )

        # Force Category
        if sheet_name == "SSOE":
            df["Category"] = "SSOE"
        else:
            df["Category"] = "NON-SSOE"

        # ==================================================
        # ALIGN TO MASTER COLUMNS
        # ==================================================
        for col in MASTER_COLUMNS:
            if col not in df.columns:
                df[col] = None

        # Keep only master columns
        df = df[MASTER_COLUMNS]

        return df

    except Exception as e:
        st.error(f"Error loading {sheet_name}: {e}")
        return pd.DataFrame(columns=MASTER_COLUMNS)

# ==================================================
# LOAD DATA
# ==================================================
ssoe = load_data("555308035", "SSOE", header_row=5)

lvl1 = load_data("1895613573", "Level 1", header_row=0)
lvl2 = load_data("451567212", "Level 2", header_row=0)
lvl3 = load_data("365079300", "Level 3", header_row=0)
lvl4 = load_data("1105352624", "Level 4", header_row=0)
lvl6 = load_data("1046028540", "Level 6", header_row=0)
others = load_data("1253302028", "Others", header_row=0)

# Combine into ONE table
df = pd.concat([ssoe, lvl1, lvl2, lvl3, lvl4, lvl6, others], ignore_index=True)

# ==================================================
# FILTERS
# ==================================================
st.subheader("🔍 Filters")

col1, col2 = st.columns(2)

with col1:
    category = st.selectbox("Category", ["All", "SSOE", "NON-SSOE"])

with col2:
    if "EquipmentType" in df.columns:
        if category == "All":
            eq_series = df["EquipmentType"]
        elif category == "SSOE":
            eq_series = df[df["Category"] == "SSOE"]["EquipmentType"]
        else:
            eq_series = df[df["Category"] == "NON-SSOE"]["EquipmentType"]

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
# DISPLAY
# ==================================================
st.subheader("📋 Inventory Data")

st.dataframe(
    filtered_df,
    use_container_width=True,
    height=600,
    hide_index=True
)

import streamlit as st
import pandas as pd

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="FVPS Inventory", layout="wide")

st.title("📦 Inventory System")

# ==================================================
# GOOGLE SHEET BASE URL
# ==================================================
BASE_URL = "https://docs.google.com/spreadsheets/d/1lmCotLUgTLJBKska2y7od2LTPT_qooIFS0_zyVnRI0A/export?format=csv&gid="

# ==================================================
# LOAD DATA (SAFE VERSION - NO DATA LOSS)
# ==================================================
def load_data(gid, sheet_name):
    try:
        df = pd.read_csv(BASE_URL + gid, header=2)

        # Basic cleanup only (DO NOT over-clean)
        df.columns = df.columns.str.strip()
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

        # Clean EquipmentType but DO NOT drop rows
        if "EquipmentType" in df.columns:
            df["EquipmentType"] = (
                df["EquipmentType"]
                .astype(str)
                .str.strip()
                .replace({"nan": None, "None": None, "": None})
            )

        # ==================================================
        # FORCE CATEGORY BASED ON SHEET (KEY FIX)
        # ==================================================
        if sheet_name == "SSOE":
            df["Category"] = "SSOE"
        else:
            df["Category"] = "NON-SSOE"

        return df

    except Exception as e:
        st.error(f"Error loading {sheet_name}: {e}")
        return pd.DataFrame()

# ==================================================
# LOAD ALL SHEETS
# ==================================================
ssoe = load_data("555308035", "SSOE")
lvl1 = load_data("1895613573", "Level 1")
lvl2 = load_data("451567212", "Level 2")
lvl3 = load_data("365079300", "Level 3")
lvl4 = load_data("1105352624", "Level 4")
lvl6 = load_data("1046028540", "Level 6")
others = load_data("1253302028", "Others")

df = pd.concat([ssoe, lvl1, lvl2, lvl3, lvl4, lvl6, others], ignore_index=True)

# ==================================================
# DEBUG (REMOVE LATER)
# ==================================================
st.write("SSOE rows:", len(df[df["Category"] == "SSOE"]))

# ==================================================
# FILTERS
# ==================================================
st.subheader("🔍 Filters")

col1, col2 = st.columns(2)

# CATEGORY FILTER
with col1:
    category = st.selectbox("Category", ["All", "SSOE", "NON-SSOE"])

# EQUIPMENT FILTER (SAFE)
with col2:
    if "EquipmentType" in df.columns:

        if category == "All":
            eq_series = df["EquipmentType"]

        elif category == "SSOE":
            eq_series = df[df["Category"] == "SSOE"]["EquipmentType"]

        else:
            eq_series = df[df["Category"] == "NON-SSOE"]["EquipmentType"]

        # SAFE UNIQUE VALUES
        eq_list = sorted([x for x in eq_series.dropna().unique() if x is not None])

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
# SEARCH
# ==================================================
search = st.text_input("🔎 Search")

if search:
    filtered_df = filtered_df[
        filtered_df.astype(str)
        .apply(lambda row: row.str.contains(search, case=False).any(), axis=1)
    ]

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

import streamlit as st
import pandas as pd

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="FVPS Inventory",
    layout="wide"
)

st.title("📦 Inventory System")

# ==================================================
# CUSTOM UI STYLING
# ==================================================
st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
}
.stDataFrame {
    border-radius: 10px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)

# ==================================================
# LOAD DATA FROM GOOGLE SHEETS
# ==================================================
BASE_URL = "https://docs.google.com/spreadsheets/d/1lmCotLUgTLJBKska2y7od2LTPT_qooIFS0_zyVnRI0A/export?format=csv&gid="

def load_data(gid, name):
    try:
        df = pd.read_csv(BASE_URL + gid, header=2)

        # Remove empty rows
        df = df.dropna(how="all")

        # Clean headers
        df.columns = df.columns.str.strip()

        # Remove "Unnamed"
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

        # Replace "None" text
        df.replace("None", pd.NA, inplace=True)

        # =========================
        # 🔥 FORCE CATEGORY (CRITICAL FIX)
        # =========================
        if "Category" in df.columns:
            df["Category"] = (
                df["Category"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

        # 🚨 FORCE SSOE FOR SSOE SHEET
        if name == "SSOE":
            df["Category"] = "SSOE"

        # Standardise NON-SSOE
        if "Category" in df.columns:
            df["Category"] = df["Category"].replace({
                "NON SSOE": "NON-SSOE",
                "NON-SSOE": "NON-SSOE"
            })

# ==================================================
# KEEP VALID ROWS (DIFFERENT LOGIC FOR SSOE)
# ==================================================
if name == "SSOE":
    # For SSOE: keep rows if EquipmentType exists
    if "EquipmentType" in df.columns:
        df = df[df["EquipmentType"].notna()]
else:
    # For other sheets: stricter cleaning
    important_cols = ["AssetNo", "SerialNumber", "BrandModel", "EquipmentType"]
    existing_cols = [col for col in important_cols if col in df.columns]

    if existing_cols:
        df = df.dropna(subset=existing_cols, how="all")

        # Clean EquipmentType
        if "EquipmentType" in df.columns:
            df["EquipmentType"] = df["EquipmentType"].astype(str).str.strip()

        return df

    except Exception as e:
        st.warning(f"Error loading {name}: {e}")
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
df = df.dropna(how="all").reset_index(drop=True)

# ==================================================
# 🔍 FILTERS (RESPONSIVE)
# ==================================================
st.subheader("🔍 Filters")

col1, col2 = st.columns(2)

# CATEGORY (FIXED OPTIONS)
with col1:
    category = st.selectbox("Category", ["All", "SSOE", "NON-SSOE"])

# EQUIPMENT (DYNAMIC)
with col2:
    if "EquipmentType" in df.columns:

        if category == "All":
            eq_list = sorted(df["EquipmentType"].dropna().unique())

        elif category == "SSOE":
            eq_list = sorted(
                df[df["Category"] == "SSOE"]["EquipmentType"]
                .dropna()
                .unique()
            )

        else:  # NON-SSOE
            eq_list = sorted(
                df[df["Category"] == "NON-SSOE"]["EquipmentType"]
                .dropna()
                .unique()
            )

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
# 📊 SUMMARY CARDS
# ==================================================
st.subheader("📊 Overview")

c1, c2, c3 = st.columns(3)

c1.metric("Total Devices", len(filtered_df))
c2.metric("SSOE", len(filtered_df[filtered_df["Category"] == "SSOE"]))
c3.metric("NON-SSOE", len(filtered_df[filtered_df["Category"] == "NON-SSOE"]))

# ==================================================
# 🔎 SEARCH
# ==================================================
search = st.text_input("🔎 Search")

if search:
    filtered_df = filtered_df[
        filtered_df.astype(str)
        .apply(lambda row: row.str.contains(search, case=False).any(), axis=1)
    ]

# ==================================================
# 📋 DISPLAY TABLE (FULL WIDTH)
# ==================================================
st.subheader("📋 Inventory Data")

st.dataframe(
    filtered_df,
    use_container_width=True,
    height=600,
    hide_index=True
)

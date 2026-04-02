import streamlit as st
import pandas as pd

st.title("📦 Inventory")

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

        # Remove Unnamed columns
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

        # Convert "None" to null
        df.replace("None", pd.NA, inplace=True)

        # =========================
        # FIX CATEGORY VALUES
        # =========================
        if "Category" in df.columns:
            df["Category"] = (
                df["Category"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

            df["Category"] = df["Category"].replace({
                "NON SSOE": "NON-SSOE",
                "NON-SSOE": "NON-SSOE",
                "SSOE": "SSOE"
            })

        # =========================
        # REMOVE EMPTY DEVICE ROWS
        # =========================
        important_cols = ["AssetNo", "SerialNumber", "BrandModel", "EquipmentType"]
        existing_cols = [col for col in important_cols if col in df.columns]

        if existing_cols:
            df = df.dropna(subset=existing_cols, how="all")

        # Track source (optional)
        df["Source"] = name

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

# Combine
df = pd.concat([ssoe, lvl1, lvl2, lvl3, lvl4, lvl6, others], ignore_index=True)
df = df.dropna(how="all").reset_index(drop=True)

# ==================================================
# 🔍 FILTERS (FINAL LOGIC)
# ==================================================
st.subheader("🔍 Filters")

col1, col2 = st.columns(2)

# -----------------------------
# CATEGORY (FIXED OPTIONS)
# -----------------------------
with col1:
    category = st.selectbox(
        "Category",
        ["All", "SSOE", "NON-SSOE"]
    )

# -----------------------------
# EQUIPMENT (DYNAMIC)
# -----------------------------
with col2:
    if "EquipmentType" in df.columns:

        # Clean Equipment values
        df["EquipmentType"] = df["EquipmentType"].astype(str).str.strip()

        if category == "All":
            eq_list = sorted(df["EquipmentType"].dropna().unique())

        elif category == "SSOE":
            eq_list = sorted(
                df[df["Category"] == "SSOE"]["EquipmentType"]
                .dropna()
                .unique()
            )

        elif category == "NON-SSOE":
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
# DISPLAY (ONLY ONE TABLE)
# ==================================================
st.subheader("📋 Inventory Data")
st.dataframe(filtered_df, use_container_width=True)

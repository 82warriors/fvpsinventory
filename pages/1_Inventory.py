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

        # Remove completely empty rows
        df = df.dropna(how="all")

        # Clean column names
        df.columns = df.columns.str.strip()

        # Remove "Unnamed" columns
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

        # Convert "None" text to actual null
        df.replace("None", pd.NA, inplace=True)

        # ==================================================
        # 🔥 FIX CATEGORY (CRITICAL)
        # ==================================================
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

        # ==================================================
        # REMOVE EMPTY / USELESS ROWS
        # ==================================================
        important_cols = ["AssetNo", "SerialNumber", "BrandModel", "EquipmentType"]
        existing_cols = [col for col in important_cols if col in df.columns]

        if existing_cols:
            df = df.dropna(subset=existing_cols, how="all")

        # Track sheet source
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

# Combine all sheets
df = pd.concat([ssoe, lvl1, lvl2, lvl3, lvl4, lvl6, others], ignore_index=True)
df = df.dropna(how="all").reset_index(drop=True)

# ==================================================
# 🔍 FILTERS (DYNAMIC + FIXED)
# ==================================================
st.subheader("🔍 Filters")

col1, col2 = st.columns(2)

# -----------------------------
# CATEGORY FILTER
# -----------------------------
with col1:
    if "Category" in df.columns:
        category_list = sorted(df["Category"].dropna().unique())
        category = st.selectbox("Category", ["All"] + category_list)
    else:
        category = "All"

# -----------------------------
# EQUIPMENT FILTER (DYNAMIC)
# -----------------------------
with col2:
    if "EquipmentType" in df.columns:

        if category == "All":
            eq_list = sorted(df["EquipmentType"].dropna().unique())
        else:
            filtered_eq = df[df["Category"] == category]
            eq_list = sorted(filtered_eq["EquipmentType"].dropna().unique())

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

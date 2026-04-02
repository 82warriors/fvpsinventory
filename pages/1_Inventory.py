import streamlit as st
import pandas as pd

st.title("📦 Inventory System")

BASE_URL = "https://docs.google.com/spreadsheets/d/1lmCotLUgTLJBKska2y7od2LTPT_qooIFS0_zyVnRI0A/export?format=csv&gid="

# -----------------------------
# LOAD ALL SHEETS
# -----------------------------
def load_data(gid, name):
    try:
        df = pd.read_csv(BASE_URL + gid)
        df["Source"] = name
        return df
    except:
        return pd.DataFrame()

ssoe = load_data("555308035", "SSOE")
lvl1 = load_data("1895613573", "Level 1")
lvl2 = load_data("451567212", "Level 2")
lvl3 = load_data("365079300", "Level 3")
lvl4 = load_data("1105352624", "Level 4")
lvl6 = load_data("1046028540", "Level 6")
others = load_data("1253302028", "Others")

# Combine all
df = pd.concat([ssoe, lvl1, lvl2, lvl3, lvl4, lvl6, others], ignore_index=True)

# Clean columns
df.columns = df.columns.str.strip()

st.subheader("📊 Combined Inventory")
st.dataframe(df, use_container_width=True)

# -----------------------------
# FILTERS
# -----------------------------
st.subheader("🔍 Filters")

# Source filter
source = st.selectbox("Select Location", ["All"] + list(df["Source"].dropna().unique()))
if source != "All":
    df = df[df["Source"] == source]

# Equipment filter
if "EquipmentType" in df.columns:
    eq = st.selectbox("Equipment Type", ["All"] + list(df["EquipmentType"].dropna().unique()))
    if eq != "All":
        df = df[df["EquipmentType"] == eq]

# Room filter
if "Room" in df.columns:
    room = st.selectbox("Room", ["All"] + list(df["Room"].dropna().unique()))
    if room != "All":
        df = df[df["Room"] == room]

st.subheader("📋 Filtered Inventory")
st.dataframe(df, use_container_width=True)

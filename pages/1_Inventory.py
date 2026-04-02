import streamlit as st
import pandas as pd

st.title("📦 Inventory")

BASE_URL = "https://docs.google.com/spreadsheets/d/1lmCotLUgTLJBKska2y7od2LTPT_qooIFS0_zyVnRI0A/export?format=csv&gid="

def load_data(gid, name):
    try:
        df = pd.read_csv(BASE_URL + gid, header=2)
        df = df.dropna(how="all")
        df.columns = df.columns.str.strip()
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        df["Source"] = name
        return df
    except:
        return pd.DataFrame()

# Load sheets
ssoe = load_data("555308035", "SSOE")
lvl1 = load_data("1895613573", "Level 1")
lvl2 = load_data("451567212", "Level 2")
lvl3 = load_data("365079300", "Level 3")
lvl4 = load_data("1105352624", "Level 4")
lvl6 = load_data("1046028540", "Level 6")
others = load_data("1253302028", "Others")

df = pd.concat([ssoe, lvl1, lvl2, lvl3, lvl4, lvl6, others], ignore_index=True)
df = df.dropna(how="all").reset_index(drop=True)

# Filters
col1, col2, col3 = st.columns(3)

with col1:
    source = st.selectbox("Location", ["All"] + sorted(df["Source"].dropna().unique()))

with col2:
    if "EquipmentType" in df.columns:
        eq = st.selectbox("Equipment", ["All"] + sorted(df["EquipmentType"].dropna().unique()))
    else:
        eq = "All"

with col3:
    if "Location" in df.columns:
        room = st.selectbox("Room", ["All"] + sorted(df["Location"].dropna().unique()))
    else:
        room = "All"

if source != "All":
    df = df[df["Source"] == source]

if eq != "All":
    df = df[df["EquipmentType"] == eq]

if room != "All":
    df = df[df["Location"] == room]

st.dataframe(df, use_container_width=True)

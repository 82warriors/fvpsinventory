import streamlit as st
import pandas as pd
import html

st.set_page_config(page_title="Inventory", layout="wide")

st.title("📦 Inventory")

# =========================
# LOAD DATA
# =========================
@st.cache_data(ttl=120)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1lmCotLUgTLJBKska2y7od2LTPT_qooIFS0_zyVnRI0A/export?format=csv"
    df = pd.read_csv(url, header=3)

    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    df["BrandModel"] = df["BrandModel"].astype(str).str.upper().str.strip()
    df["EquipmentType"] = df["EquipmentType"].astype(str).str.title().str.strip()

    df["EndDate"] = pd.to_datetime(df["EndDate"], errors="coerce")
    df["StartDate"] = pd.to_datetime(df["StartDate"], errors="coerce")

    return df

df = load_data()

# =========================
# FILTERS
# =========================
st.markdown("### 🔍 Filters")

col1, col2 = st.columns(2)

category = col1.selectbox("Category", ["All", "SSOE", "NON-SSOE"])
equipment = col2.selectbox("Equipment", ["All"] + list(df["EquipmentType"].dropna().unique()))

filtered_df = df.copy()

if equipment != "All":
    filtered_df = filtered_df[filtered_df["EquipmentType"] == equipment]

# =========================
# KPI
# =========================
st.markdown("### 📊 Overview")

c1, c2 = st.columns(2)

c1.metric("Total Devices", len(filtered_df))
c2.metric("Unique Models", filtered_df["BrandModel"].nunique())

# =========================
# EXPORT
# =========================
csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button("📥 Export CSV", csv, "inventory.csv", "text/csv")

# =========================
# TABLE
# =========================
st.markdown("### 📋 Inventory Table")

def render(df):
    html_table = "<table border='1' style='width:100%;border-collapse:collapse'>"
    html_table += "<tr>"

    for col in df.columns:
        html_table += f"<th>{html.escape(col)}</th>"

    html_table += "</tr>"

    for _, row in df.iterrows():
        html_table += "<tr>"
        for val in row:
            safe = "" if pd.isna(val) else html.escape(str(val))
            html_table += f"<td>{safe}</td>"
        html_table += "</tr>"

    html_table += "</table>"
    return html_table

st.markdown(render(filtered_df), unsafe_allow_html=True)

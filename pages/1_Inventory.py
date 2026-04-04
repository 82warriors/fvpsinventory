import streamlit as st
import pandas as pd
import html

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="Inventory", layout="wide")

st.title("📦 Inventory System")

# ==================================================
# LOAD DATA (ROBUST VERSION)
# ==================================================
@st.cache_data(ttl=120)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1lmCotLUgTLJBKska2y7od2LTPT_qooIFS0_zyVnRI0A/export?format=csv"

    # First attempt
    df = pd.read_csv(url)
    df.columns = df.columns.astype(str).str.strip()

    # If BrandModel not found → try correct header row
    if "BrandModel" not in df.columns:
        df = pd.read_csv(url, header=3)
        df.columns = df.columns.astype(str).str.strip()

    # Final check
    if "BrandModel" not in df.columns:
        st.error("❌ 'BrandModel' column not found. Check Google Sheet header row.")
        st.write("Detected columns:", df.columns.tolist())
        st.stop()

    # ==================================================
    # NORMALIZE COLUMN NAMES
    # ==================================================
    df = df.rename(columns={
        "Brand Model": "BrandModel",
        "Equipment Type": "EquipmentType",
        "Start Date": "StartDate",
        "End Date": "EndDate",
        "Last Updated": "Last Updated"
    })

    # ==================================================
    # CLEAN DATA
    # ==================================================
    df["BrandModel"] = df["BrandModel"].astype(str).str.upper().str.strip()

    if "EquipmentType" in df.columns:
        df["EquipmentType"] = df["EquipmentType"].astype(str).str.title().str.strip()

    # Fix Location (01, 02)
    if "Location" in df.columns:
        df["Location"] = df["Location"].apply(
            lambda x: str(int(float(x))).zfill(2)
            if pd.notna(x) and str(x).replace('.', '', 1).isdigit()
            else x
        )

    # ==================================================
    # FORMAT DATES
    # ==================================================
    date_cols = ["StartDate", "EndDate", "Last Updated"]

    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Display format
    if "EndDate" in df.columns:
        df["EndDate_Display"] = df["EndDate"].dt.strftime("%d %B %Y")

    for col in date_cols:
        if col in df.columns:
            df[col] = df[col].dt.strftime("%d %B %Y")

    # ==================================================
    # REMOVE EMPTY ROWS
    # ==================================================
    if "BrandModel" in df.columns and "EquipmentType" in df.columns:
        df = df[
            df["BrandModel"].notna() &
            df["EquipmentType"].notna()
        ]

    return df


df = load_data()

# ==================================================
# FILTERS
# ==================================================
st.subheader("🔍 Filters")

col1, col2 = st.columns(2)

with col1:
    category = st.selectbox("Category", ["All", "SSOE", "NON-SSOE"])

with col2:
    if "EquipmentType" in df.columns:
        eq_list = sorted(df["EquipmentType"].dropna().unique())
    else:
        eq_list = []

    eq = st.selectbox("Equipment", ["All"] + list(eq_list))

# ==================================================
# APPLY FILTERS
# ==================================================
filtered_df = df.copy()

if eq != "All":
    filtered_df = filtered_df[filtered_df["EquipmentType"] == eq]

# ==================================================
# KPI SECTION
# ==================================================
st.subheader("📊 Overview")

c1, c2, c3 = st.columns(3)

c1.metric("Total Devices", len(filtered_df))
c2.metric("Unique Models", filtered_df["BrandModel"].nunique())
c3.metric("Equipment Types", filtered_df["EquipmentType"].nunique())

# ==================================================
# EXPORT
# ==================================================
csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    "📥 Export Inventory",
    csv,
    "inventory.csv",
    "text/csv"
)

# ==================================================
# TABLE RENDER (SAFE + HIGHLIGHT)
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

            safe_val = "" if pd.isna(val) else html.escape(str(val))
            html_table += f"<td class='{cell_class}'>{safe_val}</td>"

        html_table += "</tr>"

    html_table += "</tbody></table>"
    return html_table

# ==================================================
# TABS
# ==================================================
tab1, tab2 = st.tabs(["📋 Inventory", "⏳ Expiry"])

# -------------------------------
# TAB 1
# -------------------------------
with tab1:
    st.markdown("### 📋 Inventory Data")

    display_df = filtered_df.drop(columns=["EndDate_Display"], errors="ignore")

    st.markdown(render_table(display_df), unsafe_allow_html=True)

# -------------------------------
# TAB 2
# -------------------------------
with tab2:
    st.markdown("### ⏳ Expiry Tracking")

    if "EndDate" in filtered_df.columns:

        expiry_df = (
            filtered_df
            .groupby(["BrandModel", "EndDate"])   # ✅ correct grouping
            .size()
            .reset_index(name="Count")
            .rename(columns={"EndDate": "Expiry Date"})
            .sort_values(by="Expiry Date")
        )

        st.markdown(render_table(expiry_df), unsafe_allow_html=True)

    else:
        st.warning("No expiry data available.")

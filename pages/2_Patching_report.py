import streamlit as st
import pandas as pd

#====================================
# PAGE REFRESH
#=====================================
# Refresh button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()

@st.cache_data(ttl=120)
def load_data():
    df = pd.read_csv(URL, header=1)
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    return df

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="Patching Report", layout="wide")

st.title("🛠 Patching Report")

# ==================================================
# DATA SOURCE
# ==================================================
URL = "https://docs.google.com/spreadsheets/d/1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE/export?format=csv"

# ==================================================
# LOAD DATA
# ==================================================
@st.cache_data
def load_data():
    df = pd.read_csv(URL, header=1)

    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    return df

df = load_data()

# ==================================================
# FILTER
# ==================================================
if "Week" in df.columns:
    week_list = sorted(df["Week"].dropna().unique())
    selected_week = st.selectbox("Select Week", ["All"] + week_list)
else:
    selected_week = "All"

filtered_df = df.copy()

if selected_week != "All":
    filtered_df = filtered_df[filtered_df["Week"] == selected_week]

# ==================================================
# 🎨 BUILD HTML TABLE (FULL CONTROL)
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
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        padding: 10px;
        border: 2px solid #333;
        text-align: center;
    }

    .custom-table td {
        padding: 8px;
        border: 1px solid #555;
        text-align: center;
    }

    .custom-table tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    </style>

    <table class="custom-table">
        <thead>
            <tr>
    """

    # Headers
    for col in df.columns:
        html += f"<th>{col}</th>"

    html += "</tr></thead><tbody>"

    # Rows
    for _, row in df.iterrows():
        html += "<tr>"
        for val in row:
            html += f"<td>{val}</td>"
        html += "</tr>"

    html += "</tbody></table>"

    return html

# ==================================================
# DISPLAY
# ==================================================
st.subheader("📋 Raw Data")

st.markdown(render_table(filtered_df), unsafe_allow_html=True)

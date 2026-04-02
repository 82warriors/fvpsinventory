import streamlit as st
import pandas as pd

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

    # Clean headers
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    return df

df = load_data()

# ==================================================
# FILTER - WEEK
# ==================================================
st.subheader("📅 Filter by Week")

if "Week" in df.columns:
    week_list = sorted(df["Week"].dropna().unique())
    selected_week = st.selectbox("Select Week", ["All"] + week_list)
else:
    selected_week = "All"

# Apply filter
filtered_df = df.copy()

if selected_week != "All":
    filtered_df = filtered_df[filtered_df["Week"] == selected_week]

# ==================================================
# SUMMARY DASHBOARD
# ==================================================
st.subheader("📊 Summary")

if "Status" in filtered_df.columns:
    summary = filtered_df.groupby("Status")["Count"].sum().reset_index()

    col1, col2, col3 = st.columns(3)

    for i, row in summary.iterrows():
        if i % 3 == 0:
            col1.metric(row["Status"], int(row["Count"]))
        elif i % 3 == 1:
            col2.metric(row["Status"], int(row["Count"]))
        else:
            col3.metric(row["Status"], int(row["Count"]))

# ==================================================
# RAW DATA
# ==================================================
st.subheader("📋 Raw Data")

st.dataframe(
    filtered_df,
    use_container_width=True,
    height=600,
    hide_index=True
)

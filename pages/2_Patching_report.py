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
    df = pd.read_csv(URL, header=3)

    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    return df

df = load_data()

# ==================================================
# FILTER
# ==================================================
st.subheader("📅 Filter by Week")

if "Week" in df.columns:
    week_list = sorted(df["Week"].dropna().unique())
    selected_week = st.selectbox("Select Week", ["All"] + week_list)
else:
    selected_week = "All"

filtered_df = df.copy()

if selected_week != "All":
    filtered_df = filtered_df[filtered_df["Week"] == selected_week]

# ==================================================
# SUMMARY
# ==================================================
st.subheader("📊 Summary")

if "Status" in filtered_df.columns:
    summary = filtered_df.groupby("Status")["Count"].sum().reset_index()

    cols = st.columns(len(summary))

    for i, row in summary.iterrows():
        cols[i].metric(row["Status"], int(row["Count"]))

# ==================================================
# 🎨 STYLING FUNCTION
# ==================================================
def style_table(df):
    return (
        df.style
        .set_table_styles([
            {
                "selector": "thead th",
                "props": [
                    ("background-color", "#1f77b4"),
                    ("color", "white"),
                    ("font-weight", "bold"),
                    ("text-align", "center")
                ]
            }
        ])
        .set_properties(**{
            "text-align": "center"
        })
    )

# ==================================================
# DISPLAY
# ==================================================
st.subheader("📋 Raw Data")

styled_df = style_table(filtered_df)

st.dataframe(
    styled_df,
    use_container_width=True,
    height=600
)

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

    # Clean columns
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    return df

df = load_data()

# ==================================================
# FILTER (OPTIONAL)
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
# 🎨 STYLING FUNCTION (HEADER + CELLS)
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
                    ("text-align", "center"),
                    ("border", "1px solid black")
                ]
            }
        ])
        .set_properties(**{
            "text-align": "center",
            "border": "1px solid #ddd"
        })
    )

# ==================================================
# DISPLAY
# ==================================================
st.subheader("📋 Raw Data")

styled_df = style_table(filtered_df)

# ⚠️ IMPORTANT: use st.write for styling
st.write(styled_df)

import streamlit as st
import pandas as pd

st.title("🛠 Patching Report")

url = "https://docs.google.com/spreadsheets/d/1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE/export?format=csv"
df = pd.read_csv(BASE, header=3)

st.dataframe(df)

if "Week" in df.columns:
    week = st.selectbox("Select Week", ["All"] + list(df["Week"].dropna().unique()))

    if week != "All":
        st.dataframe(df[df["Week"] == week])

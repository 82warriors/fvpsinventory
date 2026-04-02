import streamlit as st
import pandas as pd

st.title("📦 Inventory")

url = "https://docs.google.com/spreadsheets/d/1lmCotLUgTLJBKska2y7od2LTPT_qooIFS0_zyVnRI0A/export?format=csv"
df = pd.read_csv(url)

st.dataframe(df, use_container_width=True)

if "EquipmentType" in df.columns:
    option = st.selectbox("Filter Equipment", ["All"] + list(df["EquipmentType"].dropna().unique()))
    if option != "All":
        df = df[df["EquipmentType"] == option]

st.dataframe(df)

import streamlit as st
import pandas as pd

st.title("📊 Dashboard")

url = "https://docs.google.com/spreadsheets/d/1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE/export?format=csv"
df = pd.read_csv(url)

if all(col in df.columns for col in ["Week","Status","Count"]):

    summary = df.groupby(["Week","Status"])["Count"].sum().unstack().fillna(0)

    st.subheader("📊 Weekly Status")
    st.dataframe(summary)
    st.line_chart(summary)

    installed = df[df["Status"] == "Installed"].groupby("Week")["Count"].sum()
    total = df.groupby("Week")["Count"].sum()

    percent = (installed / total * 100).round(2)

    st.subheader("📈 Patching %")
    st.line_chart(percent)

else:
    st.warning("⚠️ Your patching sheet must have: Week, Status, Count")

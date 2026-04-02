import streamlit as st
import pandas as pd

st.title("📊 Dashboard")

url = "https://docs.google.com/spreadsheets/d/1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE/export?format=csv"
df = pd.read_csv(url)
df.columns = df.columns.str.strip()

try:
    df_long = df.melt(id_vars=["Week"], var_name="Type", value_name="Count")
    df_long[["Category", "Status"]] = df_long["Type"].str.split(" ", n=1, expand=True)

    summary = df_long.groupby(["Week","Status"])["Count"].sum().unstack().fillna(0)

    st.line_chart(summary)

    installed = df_long[df_long["Status"] == "Installed"].groupby("Week")["Count"].sum()
    total = df_long.groupby("Week")["Count"].sum()

    percent = (installed / total * 100).round(2)

    st.subheader("📈 Patching %")
    st.line_chart(percent)

except:
    st.warning("Check patching format")

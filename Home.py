import streamlit as st
import pandas as pd
import plotly.express as px

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="FVPS Dashboard", layout="wide")

st.title("📊 FVPS IT Management Dashboard")
st.caption("Real-time monitoring of FVPS IT infrastructure • Auto-updated from central data source")

# ==================================================
# 🏫 OVERVIEW (NEW UX SECTION)
# ==================================================
st.markdown("""
## 🏫 System Overview

This dashboard provides a real-time view of the school's IT environment.

It helps to monitor:

- 📦 **Inventory Status** – Total devices, active usage, faulty equipment  
- 🧯 **Fault Monitoring** – Devices and locations with issues  
- 🔄 **Patching Compliance** – Weekly update and security status  
- 📊 **Operational Insights** – Trends to support planning and decisions  

Use the filters and charts below to explore system performance.
""")

st.divider()


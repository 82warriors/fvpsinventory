import streamlit as st
import pandas as pd
import plotly.express as px

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="FVPS IT Dashboard",
    page_icon="🔴",
    layout="wide"
)

# ==================================================
# HIDE STREAMLIT DEFAULT UI
# ==================================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==================================================
# CUSTOM HEADER
# ==================================================
st.markdown("""
<h1 style='margin-bottom:0;'>🔴 FVPS IT Management Dashboard</h1>
<p style='color:gray;margin-top:0;font-size:16px;'>
Real-time monitoring of FVPS IT infrastructure
</p>
""", unsafe_allow_html=True)

st.write("")  # spacing

# ==================================================
# OVERVIEW SECTION (CARD STYLE)
# ==================================================
st.markdown("## 🏫 System Overview")

# Card styling
st.markdown("""
<style>
.card {
    padding: 18px;
    border-radius: 12px;
    background-color: #f8f9fa;
    border: 1px solid #e0e0e0;
    height: 140px;
}
.card h4 {
    margin-bottom: 8px;
}
.card p {
    font-size: 14px;
    color: #555;
}
</style>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("""
    <div class="card">
        <h4>📦 Inventory</h4>
        <p>Total devices, usage status, and distribution across locations.</p>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="card">
        <h4>🧯 Fault Monitoring</h4>
        <p>Track faulty equipment and identify problem areas quickly.</p>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="card">
        <h4>🔄 Patching</h4>
        <p>Monitor update compliance and system security status weekly.</p>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown("""
    <div class="card">
        <h4>📊 Insights</h4>
        <p>Visualise trends to support planning and operational decisions.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

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
# 🔥 FULL UI CLEANUP (WORKING VERSION)
# ==================================================
st.markdown("""
<style>

/* Hide Streamlit header completely */
header {visibility: hidden;}
[data-testid="stHeader"] {display: none;}
[data-testid="stToolbar"] {display: none;}

/* Hide menu + footer */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Remove top padding gap */
.block-container {
    padding-top: 1rem;
}

/* Card styling */
.card {
    padding: 18px;
    border-radius: 12px;
    background-color: #f8f9fa;
    border: 1px solid #e0e0e0;
    height: 140px;
    transition: 0.2s;
}
.card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
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

# ==================================================
# 🔴 CUSTOM HEADER (REPLACES STREAMLIT HEADER)
# ==================================================
st.markdown("""
<h1 style='margin-bottom:0;'>🔴 FVPS IT Management Dashboard</h1>
<p style='color:gray;margin-top:0;font-size:15px;'>
Real-time monitoring of FVPS IT infrastructure
</p>
""", unsafe_allow_html=True)

st.write("")  # spacing

# ==================================================
# 🏫 SYSTEM OVERVIEW (CARD STYLE)
# ==================================================
st.markdown("## 🏫 System Overview")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("""
    <div class="card">
        <h4>📦 Inventory</h4>
        <p>Total devices, active usage, and distribution across locations.</p>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="card">
        <h4>🧯 Fault Monitoring</h4>
        <p>Track faulty equipment and identify affected areas quickly.</p>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="card">
        <h4>🔄 Patching</h4>
        <p>Monitor system updates, compliance, and security status.</p>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown("""
    <div class="card">
        <h4>📊 Insights</h4>
        <p>Analyse trends to support planning and operational decisions.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

import streamlit as st
from pathlib import Path

# MUST BE FIRST
st.set_page_config(
    page_title="FVPS Dashboard",
    page_icon="🔴",
    layout="wide"
)

# Hide Streamlit UI
st.markdown("""
<style>
header {visibility: hidden;}
[data-testid="stHeader"] {display: none;}
[data-testid="stToolbar"] {display: none;}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.block-container {padding-top: 1rem;}
</style>
""", unsafe_allow_html=True)

# ==============================
# SESSION STATE (TITLE)
# ==============================
if "app_title" not in st.session_state:
    st.session_state.app_title = "FVPS IT Management Dashboard"

# Sidebar control
new_title = st.sidebar.text_input(
    "✏️ Update Header Title",
    st.session_state.app_title
)

if new_title != st.session_state.app_title:
    st.session_state.app_title = new_title
    st.rerun()

# ==============================
# HEADER WITH LOGO
# ==============================
logo_path = Path(__file__).parent / "logo.png"

col1, col2 = st.columns([1, 10])

with col1:
    st.image(logo_path, width=70)

with col2:
    st.markdown(f"""
    <h1 style='margin-bottom:0;'>{st.session_state.app_title}</h1>
    <p style='color:gray;margin-top:0;'>Real-time monitoring dashboard</p>
    """, unsafe_allow_html=True)

st.divider()

# ==============================
# LANDING PAGE MESSAGE
# ==============================
st.info("👈 Select a page from the sidebar")

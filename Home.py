import streamlit as st

# ==================================================
# PAGE CONFIG (STATIC - cannot change dynamically)
# ==================================================
st.set_page_config(
    page_title="FVPS Dashboard",
    page_icon="🔴",
    layout="wide"
)

# ==================================================
# HIDE STREAMLIT UI
# ==================================================
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

# ==================================================
# SESSION STATE (PERSIST TITLE)
# ==================================================
if "app_title" not in st.session_state:
    st.session_state.app_title = "FVPS IT Management Dashboard"

# ==================================================
# SIDEBAR CONTROL (LIVE UPDATE)
# ==================================================
new_title = st.sidebar.text_input(
    "✏️ Update Header Title",
    value=st.session_state.app_title
)

# 🔥 FORCE UPDATE
if new_title != st.session_state.app_title:
    st.session_state.app_title = new_title
    st.rerun()

# ==================================================
# 🔴 CUSTOM HEADER (ONLY THIS CONTROLS TITLE)
# ==================================================
col1, col2 = st.columns([1, 10])

with col1:
    st.image("logo.png", width=70)  # Make sure logo.png exists

with col2:
    st.markdown(f"""
    <h1 style='margin-bottom:0;'>{st.session_state.app_title}</h1>
    <p style='color:gray;margin-top:0;font-size:14px;'>
    Real-time monitoring of FVPS IT infrastructure
    </p>
    """, unsafe_allow_html=True)

st.divider()

# ==================================================
# DEBUG (optional - remove later)
# ==================================================
st.write("Current Title:", st.session_state.app_title)

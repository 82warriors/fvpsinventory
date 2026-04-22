import streamlit as st

# ==================================================
# CONFIG (FAVICON)
# ==================================================
st.set_page_config(
    page_title="FVPS Inventory System",
    page_icon="inventory.png",
    layout="wide"
)

# ==================================================
# HEADER (LOGO + TITLE)
# ==================================================
col1, col2 = st.columns([1, 6])

with col1:
    st.image("inventory.png", width=80)

with col2:
    st.title("FVPS Inventory & Monitoring System")
    st.caption("A centralised platform for device tracking, patching and upgrades")

st.divider()

# ==================================================
# ABOUT
# ==================================================
st.subheader("📖 About This System")

st.write("""
This system is designed to support IT operations by providing a **centralised dashboard**
for managing and monitoring devices across the organisation.

It integrates directly with Google Sheets to deliver **real-time updates** on:

- Device patching status  
- Upgrade progress  
- Inventory tracking  

The goal is to provide clear visibility and help IT teams make faster, informed decisions.
""")

# ==================================================
# KEY FEATURES
# ==================================================
st.subheader("✨ Key Features")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
### 📦 Inventory
- View all registered devices  
- Track equipment details  
- Manage asset information  
""")

with col2:
    st.markdown("""
### 🛠️ Patching Report
- Monitor patching status  
- Identify devices requiring action  
- Track installation progress  
""")

col3, col4 = st.columns(2)

with col3:
    st.markdown("""
### ⬆️ Upgrade Tracking
- Track upgrade progress  
- Identify incomplete upgrades  
- Monitor deployment status  
""")

with col4:
    st.markdown("""
### 🔄 Real-Time Sync
- Data updates automatically  
- No manual refresh required  
- Always reflects latest records  
""")

st.divider()

# ==================================================
# HOW TO USE
# ==================================================
st.subheader("🚀 How to Use")

st.write("""
Use the navigation menu on the left to access different modules:

- **Inventory** → View all devices  
- **Patching Report** → Monitor patching status  
- **Upgrade** → Track upgrade progress  

Each page provides detailed insights and data visualisation.
""")

st.divider()

# ==================================================
# FOOTER
# ==================================================
st.caption("FVPS Inventory System @Copyright2026FVPS")

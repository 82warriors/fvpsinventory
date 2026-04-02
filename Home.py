import streamlit as st

st.set_page_config(page_title="FVPS IT System", layout="wide")

st.title("🏫 FVPS IT Inventory & Patching System")

st.markdown("""
Welcome to the **FVPS IT Management Dashboard**.

This system provides a centralized platform to manage and monitor:

### 📦 Inventory
- View all IT equipment across levels
- Filter by location, equipment type, and room
- Track asset details (Serial No, Asset No, Custodian)

### 📊 Dashboard
- Overview of total devices
- Active vs faulty devices
- Patching trends and statistics

### 🛠 Patching Report
- Weekly patching updates
- Historical tracking
- Status breakdown (Installed, Not Connected, etc.)

---

### 🚀 How to Use
Use the **sidebar** to navigate between:
- 📦 Inventory  
- 📊 Dashboard  
- 🛠 Patching Report  

---

### 🎯 Purpose
This system helps:
- Improve visibility of IT assets  
- Track patching compliance  
- Support decision-making for maintenance and upgrades  

---

### 👨‍💻 Maintained by
FVPS IT Team
""")

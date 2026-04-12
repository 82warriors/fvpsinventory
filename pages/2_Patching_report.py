import streamlit as st
import pandas as pd

# ==================================================
# KPI (DEVICE-LEVEL CALCULATION)
# ==================================================
st.markdown("## 📊 Overview")

# --- CLEAN COLUMNS ---
df["BrandModel"] = df["BrandModel"].astype(str).str.strip()
df["Profile"] = df["Profile"].astype(str).str.upper().str.strip()
df["Status"] = df["Status"].astype(str).str.upper().str.strip()

# ==================================================
# CALCULATIONS
# ==================================================

# 1. Total Admin (Lenovo Yoga L13)
total_admin = df[
    (df["BrandModel"] == "Lenovo Yoga L13")
].shape[0]

# 2. Total Admin Patched
total_admin_patched = df[
    (df["BrandModel"] == "Lenovo Yoga L13") &
    (df["Profile"] == "ADMIN") &
    (df["Status"] == "INSTALLED")
].shape[0]

# 3. Total Acad (Lenovo K14 Gen2, Profile Acad)
total_acad = df[
    (df["BrandModel"] == "Lenovo K14 Gen2") &
    (df["Profile"] == "ACAD")
].shape[0]

# 4. Total Acad Patched
total_acad_patched = df[
    (df["BrandModel"] == "Lenovo K14 Gen2") &
    (df["Profile"] == "ACAD") &
    (df["Status"] == "INSTALLED")
].shape[0]

# 5. Total Shared Admin (K14 Gen2, Admin)
total_shared_admin = df[
    (df["BrandModel"] == "Lenovo K14 Gen2") &
    (df["Profile"] == "ADMIN")
].shape[0]

# 6. Total Shared Admin Patched
total_shared_admin_patched = df[
    (df["BrandModel"] == "Lenovo K14 Gen2") &
    (df["Profile"] == "ADMIN") &
    (df["Status"] == "INSTALLED")
].shape[0]

# ==================================================
# DISPLAY
# ==================================================

col1, col2, col3 = st.columns(3)

col1.metric("Total Admin (Yoga L13)", total_admin)
col1.metric("Admin Patched", total_admin_patched)

col2.metric("Total Acad (K14 Gen2)", total_acad)
col2.metric("Acad Patched", total_acad_patched)

col3.metric("Total Shared Admin", total_shared_admin)
col3.metric("Shared Admin Patched", total_shared_admin_patched)

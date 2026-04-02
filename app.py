import streamlit as st
import pandas as pd

st.set_page_config(page_title="FVPS Inventory System", layout="wide")

st.title("📊 FVPS Inventory & Patching System")

# ==================================================
# SIDEBAR NAVIGATION
# ==================================================
view = st.sidebar.radio(
    "Navigation",
    ["📦 Inventory", "📊 Dashboard", "🛠 Patching Report"]
)

# ==================================================
# LOAD INVENTORY (ALL SHEETS)
# ==================================================
BASE_URL = "https://docs.google.com/spreadsheets/d/1lmCotLUgTLJBKska2y7od2LTPT_qooIFS0_zyVnRI0A/export?format=csv&gid="

def load_data(gid, name):
    try:
        df = pd.read_csv(BASE_URL + gid, header=2)

        # Clean
        df = df.dropna(how="all")
        df.columns = df.columns.str.strip()

        # Remove "Unnamed"
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

        df["Source"] = name

        return df

    except Exception as e:
        st.warning(f"Error loading {name}: {e}")
        return pd.DataFrame()

# Load all sheets
ssoe = load_data("555308035", "SSOE")
lvl1 = load_data("1895613573", "Level 1")
lvl2 = load_data("451567212", "Level 2")
lvl3 = load_data("365079300", "Level 3")
lvl4 = load_data("1105352624", "Level 4")
lvl6 = load_data("1046028540", "Level 6")
others = load_data("1253302028", "Others")

# Combine
inventory_df = pd.concat(
    [ssoe, lvl1, lvl2, lvl3, lvl4, lvl6, others],
    ignore_index=True
)

inventory_df = inventory_df.dropna(how="all").reset_index(drop=True)

# ==================================================
# LOAD PATCHING
# ==================================================
patch_url = "https://docs.google.com/spreadsheets/d/1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE/export?format=csv"

patch_df = pd.read_csv(patch_url)
patch_df.columns = patch_df.columns.str.strip()

# Convert wide → long
try:
    patch_long = patch_df.melt(id_vars=["Week"], var_name="Type", value_name="Count")
    patch_long[["Category", "Status"]] = patch_long["Type"].str.split(" ", n=1, expand=True)
except:
    patch_long = patch_df

# ==================================================
# 📦 INVENTORY (ALWAYS SHOWN)
# ==================================================
st.subheader("📦 Combined Inventory")

df = inventory_df.copy()

# -----------------------------
# FILTERS
# -----------------------------
col1, col2, col3 = st.columns(3)

with col1:
    source_list = sorted(df["Source"].dropna().astype(str).unique())
    source = st.selectbox("Location", ["All"] + source_list)

with col2:
    if "EquipmentType" in df.columns:
        eq_list = sorted(df["EquipmentType"].dropna().astype(str).unique())
        eq = st.selectbox("Equipment", ["All"] + eq_list)
    else:
        eq = "All"

with col3:
    if "Location" in df.columns:
        room_list = sorted(df["Location"].dropna().astype(str).unique())
        room = st.selectbox("Room", ["All"] + room_list)
    else:
        room = "All"

# Apply filters
if source != "All":
    df = df[df["Source"] == source]

if eq != "All":
    df = df[df["EquipmentType"] == eq]

if room != "All":
    df = df[df["Location"] == room]

st.dataframe(df, use_container_width=True)

# ==================================================
# 📊 DASHBOARD
# ==================================================
if view == "📊 Dashboard":

    st.subheader("📊 Dashboard")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Devices", len(inventory_df))

    if "Status" in inventory_df.columns:
        active = len(inventory_df[inventory_df["Status"].astype(str).str.contains("Active", na=False)])
        col2.metric("Active Devices", active)

    if "Fault" in inventory_df.columns:
        faulty = len(inventory_df[inventory_df["Fault"].notna()])
        col3.metric("Faulty Devices", faulty)

    if all(col in patch_long.columns for col in ["Week","Status","Count"]):
        summary = patch_long.groupby(["Week","Status"])["Count"].sum().unstack().fillna(0)

        st.subheader("📈 Patching Trend")
        st.line_chart(summary)

        installed = patch_long[patch_long["Status"] == "Installed"].groupby("Week")["Count"].sum()
        total = patch_long.groupby("Week")["Count"].sum()

        percent = (installed / total * 100).round(2)

        st.subheader("📊 Patching %")
        st.line_chart(percent)

# ==================================================
# 🛠 PATCHING REPORT
# ==================================================
elif view == "🛠 Patching Report":

    st.subheader("🛠 Patching Report")

    st.dataframe(patch_long)

    if "Week" in patch_long.columns:
        week = st.selectbox("Select Week", ["All"] + list(patch_long["Week"].dropna().unique()))

        if week != "All":
            st.dataframe(patch_long[patch_long["Week"] == week])

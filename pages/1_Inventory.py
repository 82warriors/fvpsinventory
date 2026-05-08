import streamlit as st
import pandas as pd
import plotly.express as px
import html
from streamlit_autorefresh import st_autorefresh

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="FVPS Inventory System",
    layout="wide"
)

st.title("📦 FVPS Inventory System")

# ==================================================
# AUTO REFRESH
# ==================================================
st_autorefresh(interval=30 * 1000, key="refresh")

# ==================================================
# CONSTANTS
# ==================================================
MASTER_COLUMNS = [
    "Status",
    "Category",
    "EquipmentType",
    "Vendor",
    "BrandModel",
    "Profile",
    "Custodian",
    "AssetNo",
    "SerialNumber",
    "Location",
    "Venue",
    "StartDate",
    "EndDate",
    "Hostname",
    "SSOE PO Number",
    "Cart No",
    "What's in the box",
    "Upgrade Item List",
    "Addon Item List",
    "Bundle Item list",
    "Lamp Hour",
    "HDMI",
    "Duration in Use",
    "Fault",
    "Last Updated",
    "Remarks"
]

BASE_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1lmCotLUgTLJBKska2y7od2LTPT_qooIFS0_zyVnRI0A/"
    "export?format=csv&gid="
)

# ==================================================
# LOAD DATA
# ==================================================
@st.cache_data(ttl=30)
def load_data(gid, sheet_name, header_row):

    try:
        df = pd.read_csv(
            BASE_URL + gid,
            header=header_row
        )

        # ==================================================
        # CLEAN HEADERS
        # ==================================================
        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
        )

        df = df.loc[
            :,
            ~df.columns.str.contains("^Unnamed", na=False)
        ]

        # ==================================================
        # FORMAT LOCATION
        # ==================================================
        if "Location" in df.columns:

            df["Location"] = df["Location"].apply(
                lambda x:
                str(int(float(x))).zfill(2)
                if pd.notna(x)
                and str(x).replace(".", "", 1).isdigit()
                else x
            )

        # ==================================================
        # FORMAT TEXT
        # ==================================================
        if "EquipmentType" in df.columns:

            df["EquipmentType"] = (
                df["EquipmentType"]
                .astype(str)
                .str.strip()
                .str.title()
            )

        if "BrandModel" in df.columns:

            df["BrandModel"] = (
                df["BrandModel"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

        # ==================================================
        # DATE COLUMNS
        # ==================================================
        date_cols = [
            "StartDate",
            "EndDate",
            "Last Updated"
        ]

        for col in date_cols:

            if col in df.columns:

                df[col] = pd.to_datetime(
                    df[col],
                    errors="coerce"
                )

        # ==================================================
        # CATEGORY
        # ==================================================
        if sheet_name == "SSOE":
            df["Category"] = "SSOE"
        else:
            df["Category"] = "NON-SSOE"

        # ==================================================
        # ENSURE ALL COLUMNS EXIST
        # ==================================================
        for col in MASTER_COLUMNS:

            if col not in df.columns:
                df[col] = None

        return df

    except Exception as e:

        st.error(f"Error loading {sheet_name}: {e}")

        return pd.DataFrame(columns=MASTER_COLUMNS)

# ==================================================
# LOAD ALL DATA
# ==================================================
def load_all():

    datasets = [
        ("555308035", "SSOE", 3),
        ("1895613573", "Level 1", 3),
        ("451567212", "Level 2", 3),
        ("365079300", "Level 3", 3),
        ("1105352624", "Level 4", 3),
        ("1046028540", "Level 6", 3),
        ("1253302028", "Others", 2),
    ]

    frames = []

    for gid, name, header in datasets:

        temp_df = load_data(gid, name, header)
        frames.append(temp_df)

    final_df = pd.concat(
        frames,
        ignore_index=True
    )

    # ==================================================
    # REMOVE EMPTY DATA
    # ==================================================
    final_df = final_df[
        final_df["EquipmentType"].notna()
    ]

    final_df = final_df[
        final_df["BrandModel"].notna()
    ]

    return final_df

# ==================================================
# LOAD MAIN DATAFRAME
# ==================================================
df = load_all()

# ==================================================
# FILTERS
# ==================================================
st.subheader("🔍 Filters")

f1, f2, f3 = st.columns(3)

with f1:

    category = st.selectbox(
        "Category",
        ["All", "SSOE", "NON-SSOE"]
    )

with f2:

    equipment_list = sorted(
        df["EquipmentType"]
        .dropna()
        .unique()
    )

    equipment = st.selectbox(
        "Equipment Type",
        ["All"] + equipment_list
    )

with f3:

    search = st.text_input("🔎 Search")

# ==================================================
# APPLY FILTERS
# ==================================================
filtered_df = df.copy()

if category != "All":

    filtered_df = filtered_df[
        filtered_df["Category"] == category
    ]

if equipment != "All":

    filtered_df = filtered_df[
        filtered_df["EquipmentType"] == equipment
    ]

if search:

    filtered_df = filtered_df[
        filtered_df.apply(
            lambda row:
            row.astype(str)
            .str.contains(
                search,
                case=False
            )
            .any(),
            axis=1
        )
    ]

# ==================================================
# EXPIRY STATUS
# ==================================================
def get_expiry_status(date):

    if pd.isna(date):
        return ""

    today = pd.Timestamp.today()

    if date < today:
        return "Expired"

    elif date <= today + pd.Timedelta(days=30):
        return "Expiring Soon"

    else:
        return "Active"

filtered_df["Expiry Status"] = (
    filtered_df["EndDate"]
    .apply(get_expiry_status)
)

# ==================================================
# OVERVIEW METRICS
# ==================================================
st.subheader("📊 Overview")

m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "💻 Total Devices",
    len(filtered_df)
)

m2.metric(
    "🖥️ SSOE",
    len(
        filtered_df[
            filtered_df["Category"] == "SSOE"
        ]
    )
)

m3.metric(
    "📦 NON-SSOE",
    len(
        filtered_df[
            filtered_df["Category"] == "NON-SSOE"
        ]
    )
)

fault_count = (
    filtered_df["Fault"]
    .notna()
    .sum()
)

m4.metric(
    "⚠️ Fault Reports",
    fault_count
)

# ==================================================
# EXPIRY SUMMARY
# ==================================================
st.subheader("⏳ Expiry Summary")

expiry_counts = (
    filtered_df["Expiry Status"]
    .value_counts()
)

expired = expiry_counts.get("Expired", 0)
expiring = expiry_counts.get("Expiring Soon", 0)
active = expiry_counts.get("Active", 0)

e1, e2, e3 = st.columns(3)

e1.metric("🔴 Expired", expired)
e2.metric("🟡 Expiring Soon", expiring)
e3.metric("🟢 Active", active)

# ==================================================
# EQUIPMENT DISTRIBUTION
# ==================================================
st.subheader("📊 Equipment Distribution")

equipment_summary = (
    filtered_df["EquipmentType"]
    .value_counts()
    .reset_index()
)

equipment_summary.columns = [
    "Equipment Type",
    "Count"
]

# ==================================================
# CHART
# ==================================================
fig = px.bar(
    equipment_summary,
    x="Equipment Type",
    y="Count",
    text="Count"
)

fig.update_traces(
    textposition="outside"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==================================================
# DOWNLOAD BUTTON
# ==================================================
st.download_button(
    label="⬇️ Download CSV",
    data=filtered_df.to_csv(index=False),
    file_name="inventory.csv",
    mime="text/csv"
)

# ==================================================
# CUSTOM TABLE
# ==================================================
def render_table(df):

    html_table = """
    <style>

    .inventory-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }

    .inventory-table th {
        background-color: #1f4e79;
        color: white;
        padding: 10px;
        border: 2px solid black;
        position: sticky;
        top: 0;
        z-index: 100;
    }

    .inventory-table td {
        padding: 8px;
        border: 2px solid #444;
        text-align: center;
    }

    .expired {
        background-color: #f8d7da;
    }

    .warning {
        background-color: #fff3cd;
    }

    .active {
        background-color: #d4edda;
    }

    </style>

    <div style='overflow-x:auto; max-height:700px;'>

    <table class='inventory-table'>
    <thead>
    <tr>
    """

    for col in df.columns:

        html_table += (
            f"<th>{html.escape(str(col))}</th>"
        )

    html_table += "</tr></thead><tbody>"

    today = pd.Timestamp.today()

    for _, row in df.iterrows():

        html_table += "<tr>"

        for col, val in row.items():

            cell_class = ""

            if col == "EndDate" and pd.notna(val):

                if val < today:
                    cell_class = "expired"

                elif val <= today + pd.Timedelta(days=30):
                    cell_class = "warning"

                else:
                    cell_class = "active"

            # ==================================================
            # FORMAT DATES
            # ==================================================
            if pd.isna(val):

                safe_val = ""

            elif col in [
                "StartDate",
                "EndDate",
                "Last Updated"
            ]:

                if isinstance(val, pd.Timestamp):

                    safe_val = (
                        val.strftime("%d %b %Y")
                    )

                else:
                    safe_val = str(val)

            else:

                safe_val = html.escape(str(val))

            html_table += (
                f"<td class='{cell_class}'>{safe_val}</td>"
            )

        html_table += "</tr>"

    html_table += """
    </tbody>
    </table>
    </div>
    """

    return html_table

# ==================================================
# TABS
# ==================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Full Inventory",
    "⏳ Expiry Tracking",
    "⚠️ Fault Tracking",
    "🗄️ Database"
])

# ==================================================
# FULL INVENTORY
# ==================================================
with tab1:

    st.subheader("📋 Full Inventory")

    st.markdown(
        render_table(filtered_df),
        unsafe_allow_html=True
    )

# ==================================================
# EXPIRY TRACKING
# ==================================================
with tab2:

    st.subheader("⏳ Expiry Tracking")

    expiry_df = (
        filtered_df[
            filtered_df["EndDate"].notna()
        ]
        .sort_values(by="EndDate")
    )

    st.markdown(
        render_table(expiry_df),
        unsafe_allow_html=True
    )

# ==================================================
# FAULT TRACKING
# ==================================================
with tab3:

    st.subheader("⚠️ Fault Tracking")

    fault_df = filtered_df[
        filtered_df["Fault"].notna()
    ]

    if len(fault_df) > 0:

        st.markdown(
            render_table(fault_df),
            unsafe_allow_html=True
        )

    else:

        st.success(
            "✅ No active faults detected"
        )

# ==================================================
# DATABASE VIEW
# ==================================================
with tab4:

    st.subheader("🗄️ Database View")

    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=700
    )

# ==================================================
# FOOTER
# ==================================================
st.caption("🔄 Auto refresh every 30 seconds")

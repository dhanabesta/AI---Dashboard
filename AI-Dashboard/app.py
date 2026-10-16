import streamlit as st
import pandas as pd
import plotly.express as px
from db import get_asset_data

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI Asset Dashboard",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 AI-Powered Asset Master Dashboard")
st.caption("Asset Management | Analytics | Maintenance Monitoring")

# ---------------- LOAD DATABASE ----------------
try:
    df = get_asset_data()

except Exception as e:
    st.error("Database connection failed. Please check your db.py and .env files.")
    st.exception(e)
    st.stop()

if df is None or df.empty:
    st.warning(
        "No asset records found in the database. "
        "Please add asset records to the asset_master table."
    )
    st.stop()

# ---------------- DATA CLEANING ----------------
date_columns = [
    "purchase_date",
    "warranty_expiry_date",
    "last_maintenance_date",
    "next_maintenance_date"
]

for col in date_columns:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

numeric_columns = [
    "purchase_cost",
    "utilization_percent",
    "useful_life_years",
    "salvage_value"
]

for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        ).fillna(0)

# ---------------- SIDEBAR FILTERS ----------------
st.sidebar.title("🔎 Dashboard Filters")

filtered_df = df.copy()

filter_columns = [
    ("asset_category", "Asset Category"),
    ("department", "Department"),
    ("asset_status", "Asset Status")
]

for column, label in filter_columns:
    if column in filtered_df.columns:
        options = sorted(
            filtered_df[column]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected = st.sidebar.multiselect(
            label,
            options,
            default=options
        )

        filtered_df = filtered_df[
            filtered_df[column].astype(str).isin(selected)
        ]

if filtered_df.empty:
    st.warning("No assets match the selected filters.")
    st.stop()

# ---------------- KPI CARDS ----------------
total_assets = len(filtered_df)

total_cost = (
    filtered_df["purchase_cost"].sum()
    if "purchase_cost" in filtered_df.columns
    else 0
)

if "asset_status" in filtered_df.columns:
    in_use = (
        filtered_df["asset_status"]
        .astype(str)
        .str.lower()
        .isin(["in use", "in-use", "active", "assigned"])
        .sum()
    )
else:
    in_use = 0

if "utilization_percent" in filtered_df.columns:
    avg_utilization = filtered_df["utilization_percent"].mean()
else:
    avg_utilization = 0

today = pd.Timestamp.today().normalize()

warranty_due = 0

if "warranty_expiry_date" in filtered_df.columns:
    warranty_due = (
        (filtered_df["warranty_expiry_date"] >= today)
        & (
            filtered_df["warranty_expiry_date"]
            <= today + pd.Timedelta(days=90)
        )
    ).sum()

maintenance_due = 0

if "next_maintenance_date" in filtered_df.columns:
    maintenance_due = (
        filtered_df["next_maintenance_date"].notna()
        & (filtered_df["next_maintenance_date"] <= today)
    ).sum()

st.subheader("📌 Asset Overview")

col1, col2, col3 = st.columns(3)

col1.metric("📦 Total Assets", f"{total_assets:,}")
col2.metric("💰 Total Purchase Cost", f"{total_cost:,.2f}")
col3.metric("✅ Assets In Use", f"{in_use:,}")

col4, col5, col6 = st.columns(3)

col4.metric(
    "📊 Average Utilization",
    f"{avg_utilization:.1f}%"
)

col5.metric(
    "🛡️ Warranty Expiring in 90 Days",
    f"{warranty_due:,}"
)

col6.metric(
    "🛠️ Maintenance Due",
    f"{maintenance_due:,}"
)

st.divider()

# ---------------- CATEGORY AND STATUS CHARTS ----------------
left, right = st.columns(2)

with left:
    st.subheader("📊 Assets by Category")

    if "asset_category" in filtered_df.columns:
        category_data = (
            filtered_df.groupby("asset_category", dropna=False)
            .size()
            .reset_index(name="Asset Count")
        )

        fig_category = px.bar(
            category_data,
            x="asset_category",
            y="Asset Count",
            title="Category-wise Asset Count",
            labels={
                "asset_category": "Asset Category"
            }
        )

        st.plotly_chart(
            fig_category,
            use_container_width=True
        )

with right:
    st.subheader("🥧 Assets by Status")

    if "asset_status" in filtered_df.columns:
        status_data = (
            filtered_df.groupby("asset_status", dropna=False)
            .size()
            .reset_index(name="Asset Count")
        )

        fig_status = px.pie(
            status_data,
            names="asset_status",
            values="Asset Count",
            title="Asset Status Distribution"
        )

        st.plotly_chart(
            fig_status,
            use_container_width=True
        )

# ---------------- DEPARTMENT ASSET VALUE ----------------
st.subheader("🏢 Department-wise Asset Value")

if {"department", "purchase_cost"}.issubset(filtered_df.columns):

    department_data = (
        filtered_df.groupby("department", dropna=False)["purchase_cost"]
        .sum()
        .reset_index()
    )

    fig_department = px.bar(
        department_data,
        x="department",
        y="purchase_cost",
        title="Purchase Value by Department",
        labels={
            "department": "Department",
            "purchase_cost": "Total Purchase Value"
        }
    )

    st.plotly_chart(
        fig_department,
        use_container_width=True
    )

# ---------------- ASSET UTILIZATION ----------------
st.subheader("⚙️ Asset Utilization")

if {"asset_name", "utilization_percent"}.issubset(filtered_df.columns):

    utilization_data = filtered_df.nlargest(
        15, "utilization_percent"
    )

    fig_utilization = px.bar(
        utilization_data,
        x="asset_name",
        y="utilization_percent",
        title="Top 15 Assets by Utilization",
        labels={
            "asset_name": "Asset Name",
            "utilization_percent": "Utilization (%)"
        }
    )

    st.plotly_chart(
        fig_utilization,
        use_container_width=True
    )

# ---------------- ASSET MASTER TABLE ----------------
st.divider()
st.subheader("📋 Asset Master Table")

st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)

# ---------------- CSV DOWNLOAD ----------------
csv_data = filtered_df.to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    label="📥 Download Asset Data (CSV)",
    data=csv_data,
    file_name="asset_master.csv",
    mime="text/csv"
)

# ---------------- AI-STYLE INSIGHTS ----------------
st.divider()
st.subheader("🤖 Asset Insights")

if "utilization_percent" in filtered_df.columns:

    low_usage = filtered_df[
        filtered_df["utilization_percent"] < 30
    ]

    st.info(
        f"Low utilization assets: {len(low_usage)}. "
        "Review these assets to identify opportunities "
        "for reassignment or improved utilization."
    )

if "asset_condition" in filtered_df.columns:

    poor_condition = filtered_df[
        filtered_df["asset_condition"]
        .astype(str)
        .str.lower()
        .isin(["poor", "damaged", "critical"])
    ]

    st.warning(
        f"Assets needing condition review: {len(poor_condition)}."
    )

if warranty_due > 0:
    st.warning(
        f"{warranty_due} asset(s) have warranties expiring "
        "within the next 90 days."
    )

if maintenance_due > 0:
    st.warning(
        f"{maintenance_due} asset(s) have maintenance due."
    )

st.success("Dashboard loaded successfully!")
import streamlit as st
import pandas as pd
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="European Bank Churn Dashboard", layout="wide")

# --- CUSTOM CSS FOR KPI CARDS ---
st.markdown("""
<style>
    .kpi-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #e9ecef;
        margin-bottom: 10px;
        text-align: center;
    }
    .kpi-label {
        font-size: 14px;
        color: #6c757d;
        font-weight: 500;
        margin-bottom: 5px;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #212529;
    }
    .kpi-subtext {
        font-size: 12px;
        color: #dc3545;
        background: #f8d7da;
        padding: 2px 6px;
        border-radius: 4px;
        display: inline-block;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. DATA INGESTION ---
@st.cache_data
def load_data():
    rows = 1000
    data = pd.DataFrame({
        "CustomerId": range(1000, 1000 + rows),
        "Surname": np.random.choice(["Smith", "Garcia", "Müller", "Lopez"], rows),
        "CreditScore": np.random.randint(300, 850, rows),
        "Geography": np.random.choice(["France", "Spain", "Germany"], rows),
        "Gender": np.random.choice(["Female", "Male"], rows),
        "Age": np.random.randint(18, 93, rows),
        "Tenure": np.random.randint(0, 11, rows),
        "Balance": np.random.uniform(0, 250000, rows),
        "NumOfProducts": np.random.randint(1, 5, rows),
        "IsActiveMember": np.random.choice([0, 1], rows),
        "EstimatedSalary": np.random.uniform(20000, 150000, rows),
        "Exited": np.random.choice([0, 1], rows, p=[0.8, 0.2]) 
    })
    
    # Pre-processing Segments
    data['AgeGroup'] = pd.cut(data['Age'], bins=[0, 30, 45, 60, 100], labels=['<30', '30-45', '46-60', '60+'])
    data['CreditBand'] = pd.cut(data['CreditScore'], bins=[0, 580, 670, 850], labels=['Low', 'Medium', 'High'])
    data['TenureGroup'] = pd.cut(data['Tenure'], bins=[-1, 2, 5, 11], labels=['New', 'Mid-term', 'Long-term'])
    
    return data

df = load_data()

# --- 2. HEADER & SIDEBAR ---
st.markdown("<h1 style='text-align: center; font-size: 3rem; text-decoration: underline;'>European Banking Churn Analysis</h1>", unsafe_allow_html=True)

st.sidebar.title("Navigation")
module = st.sidebar.radio(
    "Select Module", 
    ["Overall Churn Summary", "Geography Analysis", "Demographic Comparison", "High-Value Explorer"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Segment Filters")
geo_selection = st.sidebar.multiselect("Geography", options=df['Geography'].unique(), default=df['Geography'].unique())
credit_selection = st.sidebar.multiselect("Credit Band", options=df['CreditBand'].unique(), default=['Low', 'Medium', 'High'])
age_range = st.sidebar.slider("Age Range", int(df["Age"].min()), int(df["Age"].max()), (18, 75))

# --- 3. FILTERING LOGIC ---
mask = (df["Geography"].isin(geo_selection)) & \
        (df["CreditBand"].isin(credit_selection)) & \
        (df["Age"].between(age_range[0], age_range[1]))

filtered_df = df[mask]

# --- 4. TOP-LEVEL KPI UI ---
st.markdown("## Key Performance Indicators")
if not filtered_df.empty:
    total_cust = len(filtered_df)
    churn_rate = (filtered_df["Exited"].sum() / total_cust) * 100 
    hv_mask = filtered_df["Balance"] > 150000
    hv_churn_count = filtered_df[hv_mask & (filtered_df["Exited"] == 1)].shape[0]
    hv_churn_ratio = (hv_churn_count / filtered_df[hv_mask].shape[0] * 100) if any(hv_mask) else 0
    total_revenue_at_risk = filtered_df[filtered_df["Exited"] == 1]["Balance"].sum()
    engagement_drop = filtered_df[filtered_df["IsActiveMember"] == 0].shape[0]
    engagement_drop_pct = (engagement_drop / total_cust) * 100

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Overall Churn Rate</div><div class="kpi-value">{churn_rate:.2f}%</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">High-Value Churn Ratio ⓘ</div><div class="kpi-value">{hv_churn_ratio:.2f}%</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Total Revenue at Risk</div><div class="kpi-value">${total_revenue_at_risk:,.0f}</div><div class="kpi-subtext">Capital Lost to Churn</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Engagement Drop ⓘ</div><div class="kpi-value">{engagement_drop}</div><div class="kpi-subtext">↓ {engagement_drop_pct:.1f}% of Total</div></div>', unsafe_allow_html=True)
else:
    st.warning("No data matches current filters.")

st.markdown("---")

# --- 5. ANALYTICS MODULES ---
st.title(f"🔍 {module}")

if module == "Overall Churn Summary":
    # --- NEW: ACTIVE VS NUM PRODUCTS CHURN ---
    st.markdown("### Segment-wise Churn Rates (Active Status vs. Num Products)")
    # Create a pivot table for the grouped bar chart
    active_prod_churn = filtered_df.pivot_table(
        index="NumOfProducts", 
        columns="IsActiveMember", 
        values="Exited", 
        aggfunc="mean"
    )
    active_prod_churn.columns = ["Inactive Member Churn", "Active Member Churn"]
    st.bar_chart(active_prod_churn)
    
    # --- CHURN CONTRIBUTION BY GEOGRAPHY ---
    st.markdown("### Churn Contribution by Segment Size (Geography)")
    total_churned = filtered_df["Exited"].sum()
    if total_churned > 0:
        geo_contrib = filtered_df[filtered_df["Exited"] == 1].groupby("Geography").size() / total_churned
        st.bar_chart(geo_contrib)
    else:
        st.write("No churn data to display contribution.")

    st.markdown("### Churn Distribution by Credit Band")
    credit_churn = filtered_df.groupby("CreditBand", observed=False)["Exited"].mean()
    st.bar_chart(credit_churn)

elif module == "Geography Analysis":
    geo_data = filtered_df.groupby(["Geography", "Exited"]).size().unstack(fill_value=0)
    geo_data.columns = ["Retained", "Churned"]
    st.bar_chart(geo_data, color=["#2ecc71", "#e74c3c"])
    st.dataframe(filtered_df.groupby("Geography")["Exited"].agg(['count', 'sum', 'mean']), use_container_width=True)

elif module == "Demographic Comparison":
    col_age, col_ten = st.columns(2)
    with col_age:
        st.write("#### Churn by Age Group")
        st.line_chart(filtered_df.groupby("AgeGroup", observed=False)["Exited"].mean())
    with col_ten:
        st.write("#### Churn by Tenure Group")
        st.area_chart(filtered_df.groupby("TenureGroup", observed=False)["Exited"].mean())

elif module == "High-Value Explorer":
    threshold = df["Balance"].quantile(0.75)
    hv_df = filtered_df[filtered_df["Balance"] >= threshold]
    
    if not hv_df.empty:
        risk_capital = hv_df[hv_df["Exited"] == 1]["Balance"].sum()
        st.error(f"High-Value Capital at Risk: ${risk_capital:,.0f}")
        
        st.markdown("### Salary vs. Balance Churn Patterns")
        chart_data = hv_df[hv_df["Exited"] == 1].groupby('Geography')[['Balance', 'EstimatedSalary']].mean()
        st.area_chart(chart_data)
        
        st.markdown("### Top High-Balance Churners")
        st.dataframe(hv_df[hv_df["Exited"] == 1].sort_values(by="Balance", ascending=False).head(10))
    else:
        st.write("No high-value customers in current filter.")

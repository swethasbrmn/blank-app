import streamlit as st
import pandas as pd
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="European Banking Churn Analytics", layout="wide")

# --- 1. DATA INGESTION & VALIDATION ---
@st.cache_data
def load_data():
    # In production use: df = pd.read_csv("Customer-Churn-Records.csv")
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
    
    # --- DATA CLEANING & PREPARATION (Segmentation Design) ---
    # Geographic segmentation is inherent in 'Geography'
    
    # Age Segmentation (<30, 30–45, 46–60, 60+)
    data['AgeGroup'] = pd.cut(data['Age'], bins=[0, 30, 45, 60, 100], labels=['<30', '30-45', '46-60', '60+'])
    
    # Credit Score Bands (Low, Medium, High)
    data['CreditBand'] = pd.cut(data['CreditScore'], bins=[0, 580, 670, 850], labels=['Low', 'Medium', 'High'])
    
    # Tenure Groups (New, Mid-term, Long-term)
    data['TenureGroup'] = pd.cut(data['Tenure'], bins=[-1, 2, 5, 11], labels=['New', 'Mid-term', 'Long-term'])
    
    # Balance Segments (Zero, Low, High)
    data['BalanceSegment'] = pd.cut(data['Balance'], bins=[-1, 1, 50000, 250000], labels=['Zero', 'Low', 'High'])

    return data

df = load_data()

# --- 2. SIDEBAR NAVIGATION & USER CAPABILITIES ---
st.sidebar.title("App Navigation")
module = st.sidebar.radio(
    "Select Module", 
    ["Overall Summary", "Geography Analysis", "Demographic Comparison", "High-Value Explorer"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Segment Filters")
# Filters for dynamic KPI updates and drill-down views
geo_selection = st.sidebar.multiselect("Geography", options=df['Geography'].unique(), default=df['Geography'].unique())
credit_selection = st.sidebar.multiselect("Credit Band", options=df['CreditBand'].unique(), default=['Low', 'Medium', 'High'])
age_range = st.sidebar.slider("Age Range", int(df["Age"].min()), int(df["Age"].max()), (18, 75))

# --- 3. FILTERING LOGIC ---
mask = (df["Geography"].isin(geo_selection)) & \
       (df["CreditBand"].isin(credit_selection)) & \
       (df["Age"].between(age_range[0], age_range[1]))

filtered_df = df[mask]

# --- 4. KPI AREA ---
st.title(f"📊 {module}")

if not filtered_df.empty:
    total_cust = len(filtered_df)
    churn_rate = (filtered_df["Exited"].sum() / total_cust) * 100
    avg_balance = filtered_df["Balance"].mean()
    active_ratio = (filtered_df["IsActiveMember"].sum() / total_cust) * 100

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Customers", total_cust)
    kpi2.metric("Avg. Churn Rate", f"{churn_rate:.2f}%")
    kpi3.metric("Avg. Account Balance", f"${avg_balance:,.0f}")
    kpi4.metric("Active Member %", f"{active_ratio:.1f}%")
else:
    st.warning("No data available for selected filters.")

st.markdown("---")

# --- 5. MODULE ROUTING ---

if module == "Overall Summary":
    col_left, col_right = st.columns(2)
    with col_left:
        st.write("### Churn by Product Count")
        prod_churn = filtered_df.groupby("NumOfProducts")["Exited"].mean()
        st.bar_chart(prod_churn)
        
    with col_right:
        st.write("### Churn Distribution by Credit Band")
        # Uses the Ratio Method: Churn rate per credit segment
        credit_churn = filtered_df.groupby("CreditBand", observed=False)["Exited"].mean()
        st.bar_chart(credit_churn)

elif module == "Geography Analysis":
    st.write("### Regional Churn Breakdown (Retained vs Churned)")
    geo_data = filtered_df.groupby(["Geography", "Exited"]).size().unstack(fill_value=0)
    geo_data.columns = ["Retained", "Churned"]
    st.bar_chart(geo_data, color=["#2ecc71", "#e74c3c"])
    
    st.write("#### Geography Churn Ratios")
    geo_detail = filtered_df.groupby("Geography")["Exited"].agg(['count', 'sum', 'mean'])
    geo_detail.columns = ["Total Customers", "Churned Count", "Churn Rate (%)"]
    st.dataframe(geo_detail.style.format({"Churn Rate (%)": "{:.2%}"}), use_container_width=True)

elif module == "Demographic Comparison":
    st.write("### Age & Tenure Interaction")
    col_age, col_ten = st.columns(2)
    
    with col_age:
        st.write("#### Churn by Age Group")
        age_churn = filtered_df.groupby("AgeGroup", observed=False)["Exited"].mean()
        st.bar_chart(age_churn)
        
    with col_ten:
        st.write("#### Churn by Tenure Group")
        tenure_churn = filtered_df.groupby("TenureGroup", observed=False)["Exited"].mean()
        st.area_chart(tenure_churn)

elif module == "High-Value Explorer":
    st.write("### High-Value Customer Churn Analysis")
    # Identify high-balance churners (Top 25% of overall data balance)
    threshold = df["Balance"].quantile(0.75)
    hv_df = filtered_df[filtered_df["Balance"] >= threshold]
    
    if not hv_df.empty:
        st.info(f"Analyzing customers with Account Balances above ${threshold:,.2f}")
        
        # Quantify revenue risk
        risk_capital = hv_df[hv_df["Exited"] == 1]["Balance"].sum()
        st.error(f"Total Capital at Risk (Churned HV Customers): ${risk_capital:,.0f}")
        
        st.write("#### Financial Stability: Salary vs Balance (Churned)")
        # Area chart comparing financial metrics of those who left
        stability_data = hv_df[hv_df["Exited"] == 1].groupby('Geography')[['Balance', 'EstimatedSalary']].mean()
        st.area_chart(stability_data)
        
        if st.checkbox("Show Detailed Churner List"):
            st.dataframe(
                hv_df[hv_df["Exited"] == 1][["Surname", "Geography", "Balance", "EstimatedSalary"]]
                .sort_values(by="Balance", ascending=False),
                use_container_width=True
            )
    else:
        st.write("No high-value customers found in this segment.")

import streamlit as st
import pandas as pd
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="European Banking Churn Analytics", layout="wide")

# --- 1. DATA LOADING ---
@st.cache_data
def load_data():
    # In a real scenario, use: df = pd.read_csv("Customer-Churn-Records.csv")
    # Generating dummy data based on provided dataset description
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
        "Exited": np.random.choice([0, 1], rows, p=[0.8, 0.2]) # 1 = Churned
    })
    return data

df = load_data()

# --- 2. SIDEBAR NAVIGATION & FILTERS ---
st.sidebar.title("App Navigation")
module = st.sidebar.radio(
    "Select Module", 
    ["Overall Summary", "Geography Analysis", "Age & Tenure Comparison", "High-Value Explorer"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Segment Filters")
# Global filters affecting all modules
geo_selection = st.sidebar.multiselect("Geography", ["France", "Spain", "Germany"], default=["France", "Spain", "Germany"])
gender_selection = st.sidebar.selectbox("Gender", ["All", "Male", "Female"])
age_range = st.sidebar.slider("Age Range", int(df["Age"].min()), int(df["Age"].max()), (18, 65))

# --- 3. FILTERING LOGIC ---
mask = (df["Geography"].isin(geo_selection)) & (df["Age"].between(age_range[0], age_range[1]))
if gender_selection != "All":
    mask &= (df["Gender"] == gender_selection)

filtered_df = df[mask]

# --- 4. KPI AREA ---
st.title(f"📊 {module}")

if not filtered_df.empty:
    total_cust = len(filtered_df)
    churn_rate = (filtered_df["Exited"].sum() / total_cust) * 100
    total_balance = filtered_df["Balance"].sum()
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Customers", total_cust)
    kpi2.metric("Avg. Churn Rate", f"{churn_rate:.2f}%")
    kpi3.metric("Total Assets (Balance)", f"${total_balance:,.0f}")
else:
    st.warning("No data available for the selected filters.")

st.markdown("---")

# --- 5. MODULE ROUTING ---

if module == "Overall Summary":
    col_left, col_right = st.columns(2)
    with col_left:
        st.write("### Churn Volume by Age")
        age_churn = filtered_df.groupby("Age")["Exited"].sum()
        st.line_chart(age_churn)
    with col_right:
        st.write("### Churn by Product Count")
        prod_churn = filtered_df.groupby("NumOfProducts")["Exited"].mean()
        st.bar_chart(prod_churn)

elif module == "Geography Analysis":
    st.write("### Regional Churn Breakdown")
    # Aggregating by geography
    geo_data = filtered_df.groupby(["Geography", "Exited"]).size().unstack(fill_value=0)
    geo_data.columns = ["Retained", "Churned"]
    st.bar_chart(geo_data, color=["#2ecc71", "#e74c3c"])
    
    # Drill-down Table
    st.write("#### Detailed Regional View")
    st.dataframe(geo_data)

elif module == "Age & Tenure Comparison":
    col_age, col_tenure = st.columns(2)
    with col_age:
        st.write("### Age: Stayed vs Churned")
        age_dist = filtered_df.groupby(["Age", "Exited"]).size().unstack(fill_value=0)
        age_dist.columns = ["Stayed", "Churned"]
        st.bar_chart(age_dist, color=["#2ecc71", "#e74c3c"])

    with col_tenure:
        st.write("### Tenure: Stayed vs Churned")
        # Pre-process Tenure from dataset
        tenure_dist = filtered_df.groupby(["Tenure", "Exited"]).size().unstack(fill_value=0)
        tenure_dist.columns = ["Stayed", "Churned"]
        st.bar_chart(tenure_dist, color=["#2ecc71", "#e74c3c"])

elif module == "High-Value Explorer":
    st.write("### High-Value Customer Churn Analysis")
    # Defined as customers with balances in the top 25th percentile
    threshold = df["Balance"].quantile(0.75)
    hv_df = filtered_df[filtered_df["Balance"] >= threshold]
    
    st.info(f"Analyzing customers with Account Balances above ${threshold:,.2f}")
    
    if not hv_df.empty:
        st.write("#### Balance vs Age Distribution")
        st.scatter_chart(hv_df, x="Age", y="Balance", color="Exited")
        
        if st.checkbox("Show High-Value Churner List"):
            st.write(hv_df[hv_df["Exited"] == 1][["Surname", "Geography", "Balance", "NumOfProducts"]])
    else:
        st.write("No high-value customers found in this segment.")

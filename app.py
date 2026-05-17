"""
app.py — Navigation router

Defines page order and display names for the multi-page dashboard.
All page content lives in pages/. st.set_page_config must be called here,
before pg.run(), and must not appear in any page file.
"""

import streamlit as st

st.set_page_config(
    page_title="Customer Retention Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation([
    st.Page("pages/0_About_the_Data.py",         title="About the Data",         icon="📋"),
    st.Page("pages/1_Executive_Summary.py",       title="Executive Summary",       icon="📊"),
    st.Page("pages/2_Churn_Drivers.py",           title="Churn Drivers",           icon="📉"),
    st.Page("pages/3_Retention_Priority_List.py", title="Retention Priority List", icon="🎯"),
    st.Page("pages/4_Revenue_at_Risk.py",         title="Revenue at Risk",         icon="💰"),
    st.Page("pages/5_ROI_Calculator.py",          title="ROI Calculator",          icon="🧮"),
])
pg.run()

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

# Simple test dashboard
def main():
    st.title("Error Dashboard Test")
    st.write("This is a test dashboard to check if Streamlit is working.")
    
    # Simple metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Errors", 5)
    
    with col2:
        st.metric("Services", 3)
    
    with col3:
        st.metric("Error Types", 2)
    
    # Simple table
    data = {
        'Service': ['Service A', 'Service B'],
        'Errors': [3, 2],
        'Status': ['Active', 'Active']
    }
    df = pd.DataFrame(data)
    st.dataframe(df)
    
    st.write("Dashboard test completed successfully!")

if __name__ == "__main__":
    main() 
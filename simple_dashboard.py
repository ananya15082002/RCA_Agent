import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Error Dashboard",
    page_icon="🚨",
    layout="wide"
)

def load_error_data():
    """Load error data from error_outputs directory"""
    error_data = []
    error_outputs_dir = "error_outputs"
    
    if not os.path.exists(error_outputs_dir):
        return error_data
    
    for error_dir in os.listdir(error_outputs_dir):
        error_path = os.path.join(error_outputs_dir, error_dir)
        if os.path.isdir(error_path):
            # Look for error card JSON file
            error_card_path = os.path.join(error_path, "error_card.json")
            if os.path.exists(error_card_path):
                try:
                    with open(error_card_path, 'r') as f:
                        error_card = json.load(f)
                        error_data.append(error_card)
                except:
                    continue
    
    return error_data

def main():
    st.title("🚨 Error Dashboard")
    st.write("Monitoring system errors and performance")
    
    # Load data
    error_data = load_error_data()
    
    if not error_data:
        st.info("No error data found. The system is running smoothly!")
        return
    
    # Calculate basic metrics
    total_errors = len(error_data)
    unique_services = len(set(error.get('service', 'Unknown') for error in error_data))
    unique_error_types = len(set(f"{error.get('http_code', 'Unknown')} - {error.get('exception', 'Unknown')}" for error in error_data))
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Errors", total_errors)
    
    with col2:
        st.metric("Services Affected", unique_services)
    
    with col3:
        st.metric("Error Types", unique_error_types)
    
    with col4:
        st.metric("Last Updated", datetime.now().strftime('%H:%M'))
    
    # Display error summary table
    st.subheader("📊 Error Summary")
    
    if error_data:
        # Create summary data
        summary_data = []
        for error in error_data:
            summary_data.append({
                'Service': error.get('service', 'Unknown'),
                'Error Type': f"{error.get('exception', 'Unknown')} (HTTP {error.get('http_code', 'Unknown')})",
                'Count': error.get('count', 0),
                'First Seen': error.get('first_encountered', 'Unknown'),
                'Last Seen': error.get('last_encountered', 'Unknown'),
                'Error Directory': error.get('error_dir', 'Unknown')
            })
        
        df = pd.DataFrame(summary_data)
        st.dataframe(df, use_container_width=True)
        
        # Add view report buttons
        st.subheader("🔍 View Detailed Reports")
        for error in error_data:
            error_dir = error.get('error_dir', '')
            if error_dir:
                report_url = f"http://3.7.67.210:8501/?error_dir={error_dir}"
                st.markdown(f"**[{error.get('service', 'Unknown')}]** - {error.get('exception', 'Unknown')} - [📊 View RCA Report]({report_url})")
    
    st.write("---")
    st.write("Dashboard is working! 🎉")

if __name__ == "__main__":
    main() 
import streamlit as st
import pandas as pd
import os
import json
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64
from io import BytesIO
from streamlit_ace import st_ace
import pytz

# Configure IST timezone
IST = pytz.timezone('Asia/Kolkata')

def format_timestamp_to_ist(timestamp_str):
    """Convert timestamp string to IST format"""
    if not timestamp_str or timestamp_str == 'Unknown':
        return 'Unknown'
    try:
        # Handle different timestamp formats
        if 'T' in timestamp_str and '+' in timestamp_str:
            # ISO format with timezone
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        elif 'T' in timestamp_str:
            # ISO format without timezone (assume UTC)
            dt = datetime.fromisoformat(timestamp_str + '+00:00')
        else:
            # Try parsing as regular datetime
            dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            dt = pytz.utc.localize(dt)
        
        # Convert to IST
        ist_time = dt.astimezone(IST)
        return ist_time.strftime('%Y-%m-%d %H:%M:%S IST')
    except Exception:
        return timestamp_str

# Configure page
st.set_page_config(
    page_title="RCA Analysis Portal",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .error-card {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        color: white;
    }
    .status-500 { background-color: #dc3545; }
    .status-502 { background-color: #fd7e14; }
    .status-503 { background-color: #ffc107; color: black; }
    .status-504 { background-color: #6f42c1; }
</style>
""", unsafe_allow_html=True)

# Add custom CSS for tree visualization
st.markdown("""
<style>
.tree-container {
    font-family: 'Courier New', monospace;
    background: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
}

.tree-node {
    margin: 5px 0;
    padding: 8px;
    border-left: 2px solid #007bff;
    background: white;
    border-radius: 4px;
}

.tree-node:hover {
    background: #e3f2fd;
}

.tree-children {
    margin-left: 20px;
    border-left: 1px dashed #ccc;
    padding-left: 10px;
}

.timeline-tree {
    max-height: 600px;
    overflow-y: auto;
}

.event-card {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
    background: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.event-header {
    font-weight: bold;
    color: #2c3e50;
    border-bottom: 1px solid #eee;
    padding-bottom: 8px;
    margin-bottom: 8px;
}

.event-details {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}

.event-detail {
    padding: 4px 8px;
    background: #f8f9fa;
    border-radius: 4px;
    font-size: 0.9em;
}

.event-detail strong {
    color: #495057;
}
</style>
""", unsafe_allow_html=True)

def load_error_data(error_dir):
    """Load error data from the error directory"""
    data = {}
    
    # Load error card
    error_card_path = os.path.join(error_dir, "error_card.json")
    if os.path.exists(error_card_path):
        with open(error_card_path, 'r') as f:
            data['error_card'] = json.load(f)
    
    # Load correlation timeline (new format)
    corr_timeline_path = os.path.join(error_dir, "correlation_timeline.csv")
    if os.path.exists(corr_timeline_path):
        data['correlation_timeline'] = pd.read_csv(corr_timeline_path)
    else:
        # Fallback to old format
        corr_table_path = os.path.join(error_dir, "correlation_table.csv")
        if os.path.exists(corr_table_path):
            data['correlation_table'] = pd.read_csv(corr_table_path)
    
    # Load detailed RCA
    rca_path = os.path.join(error_dir, "detailed_rca.txt")
    if os.path.exists(rca_path):
        with open(rca_path, 'r', encoding='utf-8') as f:
            data['rca_content'] = f.read()
    else:
        data['rca_content'] = "RCA report not available."
    
    return data

def create_error_spike_chart(error_card):
    """Create error spike chart from error card data"""
    if 'values' not in error_card or not error_card['values']:
        return None
    
    times = [float(x[0]) for x in error_card['values']]
    counts = [float(x[1]) for x in error_card['values']]
    
    if not times or not counts:
        return None
    
    # Convert timestamps to datetime
    dt_times = [datetime.fromtimestamp(t) for t in times]
    
    # Create Plotly chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dt_times,
        y=counts,
        mode='lines+markers',
        name='Error Count',
        line=dict(color='red', width=2),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title=f"Error Spike: {error_card.get('service', 'Unknown')}",
        xaxis_title="Time",
        yaxis_title="Error Count",
        height=400,
        showlegend=False
    )
    
    return fig

def display_error_summary(error_card):
    """Display error summary in a card format"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Service", error_card.get('service', 'Unknown'))
    
    with col2:
        st.metric("Environment", error_card.get('env', 'Unknown'))
    
    with col3:
        http_code = error_card.get('http_code', 'Unknown')
        st.metric("Status Code", http_code)
    
    with col4:
        st.metric("Error Count", f"{error_card.get('count', 0):.1f}")

def display_correlation_table(data):
    """Display correlation data with improved timeline view and tree visualization"""
    
    # Check for new timeline format first
    if 'correlation_timeline' in data and not data['correlation_timeline'].empty:
        df = data['correlation_timeline']
        st.subheader("📊 Error Timeline Analysis")
        
        # Display summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            # Check if we have deduplication info in the data
            if 'original_timeline_count' in data.get('correlation_summary', {}):
                original_count = data['correlation_summary']['original_timeline_count']
                current_count = len(df)
                if original_count != current_count:
                    st.metric("Total Events", f"{current_count} unique", f"from {original_count} total")
                else:
                    st.metric("Total Events", current_count)
            else:
                st.metric("Total Events", len(df))
        with col2:
            st.metric("Unique Traces", df['trace_id'].nunique())
        with col3:
            st.metric("Unique Services", df['service_name'].nunique())
        
        # Add filters
        col1, col2 = st.columns(2)
        with col1:
            service_filter = st.selectbox(
                "Filter by Service",
                ["All"] + list(df['service_name'].unique())
            )
        with col2:
            operation_filter = st.selectbox(
                "Filter by Operation",
                ["All"] + list(df['operation_name'].unique())
            )
        
        # Apply filters
        filtered_df = df.copy()
        if service_filter != "All":
            filtered_df = filtered_df[filtered_df['service_name'] == service_filter]
        if operation_filter != "All":
            filtered_df = filtered_df[filtered_df['operation_name'] == operation_filter]
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Timeline", "JSON View", "Data Table"])
        
        with tab1:
            st.subheader("Event Timeline")
            
            # Show deduplication info
            original_count = len(df)
            filtered_count = len(filtered_df)
            if original_count != filtered_count:
                st.info(f"📊 **Timeline Summary**: Showing {filtered_count} unique events (deduplicated from {original_count} total events)")
            
            for idx, row in filtered_df.iterrows():
                with st.expander(f"Event {idx+1}: {row['timestamp']} - {row['operation_name']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**What:** {row['operation_name']}")
                        st.write(f"**Where:** {row['service_name']}")
                        st.write(f"**Duration:** {row['duration']}")
                    with col2:
                        st.write(f"**Why:** {row['why']}")
                        st.write(f"**Affected:** {row['affected']}")
                        st.write(f"**Trace ID:** {row['trace_id']}")
                    
                    if row['log_messages'] and str(row['log_messages']).strip():
                        st.write("**Log Messages:**")
                        st.code(row['log_messages'])
        
        with tab2:
            st.subheader("JSON Tree View")
            json_data = create_json_tree_view(filtered_df)
            if isinstance(json_data, dict):
                # Use st_ace for JSON editor with syntax highlighting
                json_str = json.dumps(json_data, indent=2, default=str)
                st_ace(
                    value=json_str,
                    language="json",
                    theme="monokai",
                    height=400,
                    show_gutter=True,
                    show_print_margin=False,
                    wrap=True
                )
            else:
                st.warning(json_data)
        
        with tab3:
            st.subheader("Complete Timeline Data")
            st.dataframe(filtered_df, use_container_width=True)
        
    # Fallback to old table format
    elif 'correlation_table' in data and not data['correlation_table'].empty:
        df = data['correlation_table']
        st.subheader("📊 Correlation Table")
        
        # Add filters
        col1, col2 = st.columns(2)
        with col1:
            operation_filter = st.selectbox(
                "Filter by Operation",
                ["All"] + list(df['operation_name'].unique())
            )
        with col2:
            service_filter = st.selectbox(
                "Filter by Service",
                ["All"] + list(df['process_service_name'].unique())
            )
        
        # Apply filters
        filtered_df = df.copy()
        if operation_filter != "All":
            filtered_df = filtered_df[filtered_df['operation_name'] == operation_filter]
        if service_filter != "All":
            filtered_df = filtered_df[filtered_df['process_service_name'] == service_filter]
        
        st.dataframe(filtered_df, use_container_width=True)
        
    else:
        st.warning("No correlation data available")

def display_detailed_rca(rca_content):
    """Display detailed RCA analysis with beautiful formatting"""
    st.subheader("🔍 Detailed Root Cause Analysis")
    
    # Split content to handle Mermaid diagrams separately
    lines = rca_content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this line contains Mermaid diagram start
        if '```mermaid' in line:
            # Collect the Mermaid diagram
            mermaid_code = []
            i += 1  # Skip the ```mermaid line
            while i < len(lines) and '```' not in lines[i]:
                mermaid_code.append(lines[i])
                i += 1
            
            # Render the Mermaid diagram
            if mermaid_code:
                mermaid_text = '\n'.join(mermaid_code)
                st.markdown("### 🎨 **Error Flow Visualization**")
                # Use HTML to render Mermaid diagram
                mermaid_html = f"""
                <div class="mermaid">
                {mermaid_text}
                </div>
                <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                <script>
                mermaid.initialize({{startOnLoad: true}});
                </script>
                """
                st.markdown(mermaid_html, unsafe_allow_html=True)
                st.markdown("")  # Add some spacing
        else:
            # Regular markdown content
            st.markdown(line, unsafe_allow_html=True)
        
        i += 1

def create_json_tree_view(df):
    """Create a JSON tree view of timeline data"""
    if df.empty:
        return "No timeline data available"
    timeline_data = {
        "timeline": {
            "total_events": len(df),
            "unique_traces": df['trace_id'].nunique(),
            "unique_services": df['service_name'].nunique(),
            "events": df.to_dict('records')
        }
    }
    return timeline_data

def main():
    st.markdown('<h1 class="main-header">🚨 Root Cause Analysis Portal</h1>', unsafe_allow_html=True)
    
    # Sidebar for navigation
    st.sidebar.title("📁 Reports")
    

    
    # Find all error directories
    error_outputs_dir = "error_outputs"
    if not os.path.exists(error_outputs_dir):
        st.error("No error outputs directory found. Run the RCA pipeline first.")
        return
    
    error_dirs = [d for d in os.listdir(error_outputs_dir) if d.startswith('error_')]
    error_dirs.sort(reverse=True)  # Most recent first
    
    if not error_dirs:
        st.warning("No error reports found. Run the RCA pipeline to generate reports.")
        return
    
    # Check for error_dir parameter in URL
    params = st.query_params
    error_dir_param = params.get("error_dir", None)
    
    # Select report - prioritize the one from URL parameter
    if error_dir_param and error_dir_param in error_dirs:
        selected_report = error_dir_param
        st.sidebar.success(f"📋 Viewing specific error: {error_dir_param}")
        st.sidebar.info(f"🔗 Direct access via URL parameter")
    else:
        selected_report = st.sidebar.selectbox(
            "Select Error Report",
            error_dirs,
            format_func=lambda x: f"{x.split('_')[1]} - {x.split('_')[2]}"
        )
    
    if selected_report:
        error_dir = os.path.join(error_outputs_dir, selected_report)
        data = load_error_data(error_dir)
        
        if 'error_card' not in data:
            st.error("Error card not found in selected report.")
            return
        
        error_card = data['error_card']
        
        # Dashboard access button - simple and on the right
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### 📋 Error Summary")
            display_error_summary(error_card)
        
        with col2:
            st.markdown("""
            <div style="text-align: center; margin-top: 20px;">
            <a href="http://49.36.211.68:8502" target="_blank" style="text-decoration: none;">
            <button style="background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; font-size: 14px; cursor: pointer;">
            📊 Dashboard
            </button>
            </a>
            </div>
            """, unsafe_allow_html=True)
        
        # Create tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Error Chart", "📊 Correlation Data", "🔍 RCA Analysis", "📋 Raw Data"])
        
        with tab1:
            st.subheader("📈 Error Spike Chart")
            fig = create_error_spike_chart(error_card)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No chart data available")
        
        with tab2:
            display_correlation_table(data)
        
        with tab3:
            if 'rca_content' in data:
                display_detailed_rca(data['rca_content'])
            else:
                st.warning("No RCA content available")
        
        with tab4:
            st.subheader("📋 Raw Error Data")
            st.json(error_card)

if __name__ == "__main__":
    main() 
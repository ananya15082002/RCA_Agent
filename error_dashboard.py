import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import json
import glob
from datetime import datetime, timedelta
import pytz
from collections import defaultdict, Counter
import time
import threading

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
    page_title="Error Dashboard",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for responsive theme styling
st.markdown("""
<style>
    /* Responsive theme styling */
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        text-align: left;
        margin-bottom: 1rem;
    }
    
    .metric-card {
        background: var(--background-color, #ffffff);
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem 0;
        border: 1px solid var(--border-color, #e0e0e0);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: var(--text-color, #000000);
    }
    
    .metric-label {
        font-size: 0.8rem;
        opacity: 0.8;
        color: var(--text-color, #000000);
    }
    
    .service-card {
        background: var(--background-color, #ffffff);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4299e1;
        margin: 0.5rem 0;
        border: 1px solid var(--border-color, #e0e0e0);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .error-trend {
        background: var(--background-color, #ffffff);
        border: 1px solid var(--border-color, #e0e0e0);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .new-error {
        background: #e53e3e;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
        font-weight: bold;
    }
    
    .frequent-error {
        background: #dd6b20;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
        font-weight: bold;
    }
    
    .existing-error {
        background: #3182ce;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
        font-weight: bold;
    }
    
    /* Theme-aware styling */
    [data-testid="stAppViewContainer"] {
        background-color: var(--background-color, #ffffff);
    }
    
    .stMarkdown {
        color: var(--text-color, #000000);
    }
    
    .stSubheader {
        color: var(--text-color, #000000);
    }
    
    .stCaption {
        color: var(--text-color, #666666);
    }
    
    .stInfo {
        background-color: var(--background-color, #ffffff);
        color: var(--text-color, #000000);
        border: 1px solid var(--border-color, #e0e0e0);
    }
    
    /* Dark theme overrides */
    @media (prefers-color-scheme: dark) {
        .metric-card {
            background: #2d3748;
            border-color: #4a5568;
            color: white;
        }
        
        .service-card {
            background: #2d3748;
            border-color: #4a5568;
            color: white;
        }
        
        .error-trend {
            background: #2d3748;
            border-color: #4a5568;
            color: white;
        }
        
        .main-header {
            color: white;
        }
        
        .metric-value {
            color: white;
        }
        
        .metric-label {
            color: white;
        }
    }
    
    /* Theme-specific styling based on data attribute */
    [data-theme="dark"] .metric-card {
        background: #2d3748 !important;
        border-color: #4a5568 !important;
        color: white !important;
    }
    
    [data-theme="dark"] .service-card {
        background: #2d3748 !important;
        border-color: #4a5568 !important;
        color: white !important;
    }
    
    [data-theme="dark"] .error-trend {
        background: #2d3748 !important;
        border-color: #4a5568 !important;
        color: white !important;
    }
    
    [data-theme="dark"] .main-header {
        color: white !important;
    }
    
    [data-theme="dark"] .metric-value {
        color: white !important;
    }
    
    [data-theme="dark"] .metric-label {
        color: white !important;
    }
    
    [data-theme="dark"] .stMarkdown,
    [data-theme="dark"] .stSubheader,
    [data-theme="dark"] .stCaption {
        color: white !important;
    }
    
    [data-theme="dark"] .stInfo {
        background-color: #2d3748 !important;
        color: white !important;
        border-color: #4a5568 !important;
    }
    
    /* Streamlit dark theme detection */
    .stApp[data-testid="stAppViewContainer"] {
        background-color: var(--background-color, #ffffff);
    }
    
    /* Ensure text is readable in both themes */
    .stMarkdown, .stSubheader, .stCaption {
        color: var(--text-color, #000000);
    }
    
    /* Table styling for better readability */
    .stDataFrame {
        background-color: var(--background-color, #ffffff);
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #4299e1;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background-color: #3182ce;
    }
    
    /* Link styling */
    a {
        color: #4299e1;
        text-decoration: none;
    }
    
    a:hover {
        color: #3182ce;
        text-decoration: underline;
    }
</style>

<script>
// Function to set theme based on user selection
function setTheme(themeMode) {
    const appContainer = document.querySelector('[data-testid="stAppViewContainer"]');
    if (appContainer) {
        if (themeMode === 'Dark') {
            appContainer.setAttribute('data-theme', 'dark');
        } else {
            appContainer.removeAttribute('data-theme');
        }
    }
}

// Set initial theme (this will be called when the page loads)
setTheme('Light');
</script>
""", unsafe_allow_html=True)

def load_error_data():
    """Load all error data from error_outputs directory"""
    error_data = []
    error_dirs = glob.glob("error_outputs/error_*")
    
    for error_dir in error_dirs:
        try:
            # Extract timestamp from directory name
            dir_name = os.path.basename(error_dir)
            parts = dir_name.split('_')
            if len(parts) >= 5:  # Should have: error_1_2025-08-12_155704_IST
                date_str = f"{parts[2]}_{parts[3]}"
                # Parse the timestamp - it's already in IST format from directory name
                timestamp = datetime.strptime(date_str, "%Y-%m-%d_%H%M%S")
                # Localize to IST timezone since the directory name indicates IST
                timestamp = IST.localize(timestamp)
                
                # Load error card
                error_card_path = os.path.join(error_dir, "error_card.json")
                if os.path.exists(error_card_path):
                    with open(error_card_path, 'r') as f:
                        error_card = json.load(f)
                        error_card['timestamp'] = timestamp
                        error_card['error_dir'] = error_dir
                        
                        # Extract first_encountered and last_encountered from error card if available
                        # These are the actual error occurrence times, not the window times
                        if 'first_encountered' in error_card:
                            error_card['first_encountered'] = error_card['first_encountered']
                        else:
                            # Use window_start as fallback
                            error_card['first_encountered'] = error_card.get('window_start', 'Unknown')
                        
                        if 'last_encountered' in error_card:
                            error_card['last_encountered'] = error_card['last_encountered']
                        else:
                            # Use window_end as fallback
                            error_card['last_encountered'] = error_card.get('window_end', 'Unknown')
                        
                        error_data.append(error_card)
        except Exception as e:
            print(f"Error loading data from {error_dir}: {e}")
            continue
    
    return error_data

def get_time_filtered_data(error_data, hours):
    """Filter error data by time range"""
    if not error_data:
        return []
    
    now = datetime.now(IST)  # Use IST timezone
    cutoff_time = now - timedelta(hours=hours)
    
    filtered_data = [
        error for error in error_data 
        if error.get('timestamp', datetime.min.replace(tzinfo=IST)) >= cutoff_time
    ]
    
    return filtered_data

def get_historical_data(error_data, hours):
    """Get historical data for comparison (outside the selected window)"""
    if not error_data:
        return []
    
    now = datetime.now(IST)  # Use IST timezone
    window_start = now - timedelta(hours=hours)
    historical_start = now - timedelta(hours=hours * 2)  # Double the window for historical comparison
    
    historical_data = [
        error for error in error_data 
        if historical_start <= error.get('timestamp', datetime.min.replace(tzinfo=IST)) < window_start
    ]
    
    return historical_data

def detect_new_errors(current_errors, historical_errors):
    """Detect new errors by comparing current window with historical data"""
    current_error_types = set()
    historical_error_types = set()
    
    # Extract error types from current window
    for error in current_errors:
        exception = error.get('exception', 'Unknown')
        http_code = error.get('http_code', 'Unknown')
        error_type = f"{exception} (HTTP {http_code})"
        current_error_types.add(error_type)
    
    # Extract error types from historical data
    for error in historical_errors:
        exception = error.get('exception', 'Unknown')
        http_code = error.get('http_code', 'Unknown')
        error_type = f"{exception} (HTTP {http_code})"
        historical_error_types.add(error_type)
    
    # Find new errors
    new_errors = current_error_types - historical_error_types
    return new_errors

def get_actual_error_times(error_dir):
    """Get actual first and last encountered times from correlation timeline"""
    try:
        # Load correlation timeline
        corr_timeline_path = os.path.join(error_dir, "correlation_timeline.csv")
        if not os.path.exists(corr_timeline_path):
            return "Unknown", "Unknown"
        
        # Read correlation timeline using built-in CSV module
        import csv
        timestamps = []
        
        with open(corr_timeline_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                first_enc = row.get('first_encountered', 'Unknown')
                last_enc = row.get('last_encountered', 'Unknown')
                
                if first_enc and first_enc != 'Unknown':
                    timestamps.append(first_enc)
                if last_enc and last_enc != 'Unknown':
                    timestamps.append(last_enc)
        
        if not timestamps:
            return "Unknown", "Unknown"
        
        # Parse timestamps and find min/max
        parsed_times = []
        for ts in timestamps:
            try:
                if 'IST' in ts:
                    ts_clean = ts.replace(' IST', '')
                elif 'UTC' in ts:
                    ts_clean = ts.replace(' UTC', '')
                else:
                    ts_clean = ts
                
                # Try different formats
                try:
                    dt = datetime.strptime(ts_clean, '%Y-%m-%d %H:%M:%S.%f')
                except:
                    dt = datetime.strptime(ts_clean, '%Y-%m-%d %H:%M:%S')
                
                parsed_times.append(dt)
            except Exception:
                continue
        
        if parsed_times:
            # Convert to IST and format
            try:
                first_dt = min(parsed_times)
                last_dt = max(parsed_times)
                
                # Localize to IST if no timezone info
                if first_dt.tzinfo is None:
                    first_dt = IST.localize(first_dt)
                if last_dt.tzinfo is None:
                    last_dt = IST.localize(last_dt)
                
                first_encountered = first_dt.strftime('%Y-%m-%d %H:%M:%S IST')
                last_encountered = last_dt.strftime('%Y-%m-%d %H:%M:%S IST')
                
                return first_encountered, last_encountered
            except Exception:
                # Fallback to simple formatting
                first_encountered = min(parsed_times).strftime('%Y-%m-%d %H:%M:%S')
                last_encountered = max(parsed_times).strftime('%Y-%m-%d %H:%M:%S')
                return first_encountered, last_encountered
        
        return "Unknown", "Unknown"
        
    except Exception as e:
        print(f"Error getting actual error times from {error_dir}: {e}")
        return "Unknown", "Unknown"

def create_error_summary_table(filtered_data, historical_data):
    """Create comprehensive error summary table with View Report buttons"""
    if not filtered_data:
        st.info("No errors found in the selected time range.")
        return
    
    # Group errors by type
    error_groups = defaultdict(list)
    for error in filtered_data:
        exception = error.get('exception', 'Unknown')
        http_code = error.get('http_code', 'Unknown')
        error_type = f"{exception} (HTTP {http_code})"
        error_groups[error_type].append(error)
    
    # Create summary table
    summary_data = []
    for error_type, errors in error_groups.items():
        # Calculate metrics
        total_count = sum(error.get('count', 0) for error in errors)
        
        # Get the most recent error directory for report link
        most_recent_error = max(errors, key=lambda x: x.get('timestamp', datetime.min))
        error_dir = most_recent_error.get('error_dir', '')
        
        # Try to get actual first and last encountered times from correlation timeline
        first_encountered_str, last_encountered_str = get_actual_error_times(error_dir)
        
        # If correlation timeline doesn't have the data, fall back to timestamp-based calculation
        if first_encountered_str == "Unknown" or last_encountered_str == "Unknown":
            error_timestamps = []
            
            for error in errors:
                # Get the timestamp from the error (this is the actual error occurrence time)
                timestamp = error.get('timestamp')
                if timestamp:
                    error_timestamps.append(timestamp)
            
            # Calculate first and last encountered times from actual timestamps
            if error_timestamps:
                first_encountered = min(error_timestamps)
                last_encountered = max(error_timestamps)
                
                # Convert to IST for display
                first_encountered_str = first_encountered.astimezone(IST).strftime('%Y-%m-%d %H:%M:%S IST')
                last_encountered_str = last_encountered.astimezone(IST).strftime('%Y-%m-%d %H:%M:%S IST')
            else:
                # Fallback to window times if no actual timestamps
                first_encountered_str = "Unknown"
                last_encountered_str = "Unknown"
                
                # Try to get from error card data
                for error in errors:
                    first_enc = error.get('first_encountered', 'Unknown')
                    last_enc = error.get('last_encountered', 'Unknown')
                    
                    if first_enc != 'Unknown' and first_encountered_str == "Unknown":
                        first_encountered_str = first_enc
                    if last_enc != 'Unknown' and last_encountered_str == "Unknown":
                        last_encountered_str = last_enc
        
        # Determine error category
        if total_count > 10:  # High frequency
            category = "🔴 Frequent Spike"
        elif total_count > 5:  # Medium frequency
            category = "🟠 Existing Error"
        else:
            category = "🟢 Low Frequency"
        
        summary_data.append({
            'Error Type': error_type,
            'Count': total_count,
            'First Encountered': first_encountered_str,
            'Last Encountered': last_encountered_str,
            'Category': category,
            'Error Directory': error_dir
        })
    
    # Sort by count (high frequency first)
    summary_data.sort(key=lambda x: x['Count'], reverse=True)
    
    # Detect new errors
    new_errors = detect_new_errors(filtered_data, historical_data)
    
    # Display new errors section
    if new_errors:
        st.subheader("🆕 New Errors Detected")
        st.markdown("These errors did not appear in the previous time window:")
        
        # Find the corresponding error data for new errors
        for error_type in new_errors:
            # Find the most recent occurrence of this error type
            matching_errors = [e for e in filtered_data if f"{e.get('exception', 'Unknown')} (HTTP {e.get('http_code', 'Unknown')})" == error_type]
            
            if matching_errors:
                most_recent = max(matching_errors, key=lambda x: x.get('timestamp', datetime.min))
                error_dir = most_recent.get('error_dir', '')
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"<div class='new-error'>🆕 {error_type}</div>", unsafe_allow_html=True)
                
                with col2:
                    if error_dir:
                        report_url = f"http://3.7.67.210:8501/?error_dir={error_dir}"
                        st.markdown(f"[📊 RCA Report]({report_url})")
                    else:
                        st.markdown("📊 No RCA report")
            else:
                st.markdown(f"<div class='new-error'>🆕 {error_type}</div>", unsafe_allow_html=True)
        
        st.write("---")
    
    # Display summary table
    st.subheader("📊 Error Summary Table")
    df = pd.DataFrame(summary_data)
    
    # Add search functionality
    search_term = st.text_input("Search errors by type:")
    if search_term:
        df = df[df['Error Type'].str.contains(search_term, case=False, na=False)]
    
    # Display table with styling
    st.dataframe(df, use_container_width=True, height=400)
    
    # Add View Report buttons for each error type
    st.subheader("🔍 **View Detailed Reports**")
    
    for error_info in summary_data:
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{error_info['Error Type']}** - {error_info['Count']} errors")
            st.caption(f"First: {error_info['First Encountered']} | Last: {error_info['Last Encountered']}")
            st.markdown(f"**{error_info['Category']}**")
        
        with col2:
            # Create the report URL
            error_dir = error_info['Error Directory']
            if error_dir:
                report_url = f"http://3.7.67.210:8501/?error_dir={error_dir}"
                st.markdown(f"[📊 RCA Report]({report_url})")
            else:
                st.markdown("📊 No RCA report")
        
        with col3:
            # Add status indicator based on category
            if '🔴' in error_info['Category']:
                st.markdown("🔴 **High Priority**")
            elif '🟠' in error_info['Category']:
                st.markdown("🟠 **Medium Priority**")
            else:
                st.markdown("🟢 **Low Priority**")
        
        st.markdown("---")
    
    # Show category breakdown
    col1, col2, col3 = st.columns(3)
    with col1:
        frequent_count = len([x for x in summary_data if '🔴' in x['Category']])
        st.metric("🔴 Frequent Spikes", frequent_count)
    
    with col2:
        existing_count = len([x for x in summary_data if '🟠' in x['Category']])
        st.metric("🟠 Existing Errors", existing_count)
    
    with col3:
        new_count = len(new_errors)
        st.metric("🆕 New Errors", new_count)

def create_metrics_dashboard(filtered_data, hours):
    """Create metrics dashboard"""
    if not filtered_data:
        return
    
    # Calculate metrics
    total_errors = len(filtered_data)
    unique_services = len(set(error.get('service', 'Unknown') for error in filtered_data))
    unique_error_types = len(set(f"{error.get('http_code', 'Unknown')} - {error.get('exception', 'Unknown')}" for error in filtered_data))
    
    # Service-wise breakdown
    service_counts = Counter(error.get('service', 'Unknown') for error in filtered_data)
    
    # Time distribution
    time_distribution = defaultdict(int)
    for error in filtered_data:
        timestamp = error.get('timestamp')
        if timestamp:
            hour = timestamp.strftime('%Y-%m-%d %H:00')
            time_distribution[hour] += 1
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_errors}</div>
            <div class="metric-label">Total Errors</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{unique_services}</div>
            <div class="metric-label">Unique Services</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{unique_error_types}</div>
            <div class="metric-label">Unique Error Types</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        avg_errors_per_hour = total_errors / max(hours, 1)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{avg_errors_per_hour:.1f}</div>
            <div class="metric-label">Avg/Hour</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Service-wise Error Distribution")
        if service_counts:
            service_df = pd.DataFrame(list(service_counts.items()), columns=['Service', 'Count'])
            fig = px.bar(service_df, x='Service', y='Count', 
                        title="Errors by Service",
                        color='Count', color_continuous_scale='viridis')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Error Type Distribution")
        if filtered_data:
            # Count errors by HTTP code and exception
            error_type_counts = Counter()
            for error in filtered_data:
                http_code = error.get('http_code', 'Unknown')
                exception = error.get('exception', 'Unknown')
                error_type = f"{http_code} - {exception}"
                error_type_counts[error_type] += 1
            
            if error_type_counts:
                error_type_df = pd.DataFrame(list(error_type_counts.items()), columns=['Error Type', 'Count'])
                error_type_df = error_type_df.sort_values('Count', ascending=False).head(10)
                
                fig = px.bar(error_type_df, x='Count', y='Error Type', 
                            title="Top Error Types",
                            orientation='h',
                            color='Count', color_continuous_scale='reds')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Error Timeline - Main Line Graph (similar to the image)
    st.subheader("Error Timeline")
    if filtered_data:
        # Create time series data for services
        timeline_data = []
        
        for error in filtered_data:
            timestamp = error.get('timestamp')
            if timestamp:
                service = error.get('service', 'Unknown')
                count = error.get('count', 1)
                
                # Round to nearest minute for better visualization
                rounded_time = timestamp.replace(second=0, microsecond=0)
                
                timeline_data.append({
                    'Time': rounded_time,
                    'Service': service,
                    'Count': count
                })
        
        if timeline_data:
            timeline_df = pd.DataFrame(timeline_data)
            
            # Create main line chart showing error counts over time
            fig = go.Figure()
            
            # Get top services by error count
            top_services = timeline_df.groupby('Service')['Count'].sum().sort_values(ascending=False).head(10).index
            
            # Color palette similar to the image
            colors = ['#00ff00', '#ff8c00', '#1e90ff', '#87ceeb', '#9370db', '#ff69b4', '#32cd32', '#ffd700', '#ff6347', '#40e0d0']
            
            for i, service in enumerate(top_services):
                service_data = timeline_df[timeline_df['Service'] == service]
                if not service_data.empty:
                    # Group by time and sum counts
                    time_grouped = service_data.groupby('Time')['Count'].sum().reset_index()
                    time_grouped = time_grouped.sort_values('Time')
        
                    fig.add_trace(go.Scatter(
                        x=time_grouped['Time'],
                        y=time_grouped['Count'],
                        mode='lines',
                        name=service,
                        line=dict(width=1.5, color=colors[i % len(colors)]),
                        hovertemplate='<b>%{fullData.name}</b><br>Time: %{x}<br>Count: %{y}<extra></extra>'
                    ))
            
            # Theme-aware chart styling
            theme_colors = get_theme_colors(theme_mode)
            fig.update_layout(
                title="",
                xaxis_title="",
                yaxis_title="",
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color=theme_colors['text_color']),
                xaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor=theme_colors['grid_color'],
                    showline=True,
                    linecolor=theme_colors['line_color'],
                    tickfont=dict(color=theme_colors['text_color'])
                ),
                yaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor=theme_colors['grid_color'],
                    showline=True,
                    linecolor=theme_colors['line_color'],
                    tickfont=dict(color=theme_colors['text_color'])
                ),
                legend=dict(
                    font=dict(color=theme_colors['text_color']),
                    bgcolor=theme_colors['legend_bg'],
                    bordercolor=theme_colors['legend_border']
                ),
                margin=dict(l=50, r=50, t=30, b=50)
            )
        st.plotly_chart(fig, use_container_width=True)
        
        # Show results summary
        total_results = len(filtered_data)
        st.caption(f"Showing {min(20, total_results)} out of {total_results} results. Show All")
        
        # Show common filters
        st.caption("Common: env=UNSET, service.version=UNSET, span_kind=client, status_code=ERROR")
    else:
        st.info("No error data available for timeline analysis.")

def create_error_details_table(filtered_data):
    """Create detailed error table with View Report buttons"""
    st.subheader("📋 **Error Details Table**")
    
    if not filtered_data:
        st.info("No error data available for the selected time period.")
        return
    
    # Create DataFrame for display
    error_rows = []
    for error in filtered_data:
        # Extract service name from error card
        service_name = error.get('service', 'Unknown')
        
        # Extract error count
        error_count = error.get('count', 0)
        
        # Try to get actual first and last encountered times from correlation timeline
        error_dir = error.get('error_dir', '')
        first_encountered, last_encountered = get_actual_error_times(error_dir)
        
        # If correlation timeline doesn't have the data, fall back to timestamp-based calculation
        if first_encountered == "Unknown" or last_encountered == "Unknown":
            timestamp = error.get('timestamp')
            if timestamp:
                # Use the actual error occurrence time
                first_encountered = timestamp.astimezone(IST).strftime('%Y-%m-%d %H:%M:%S IST')
                last_encountered = timestamp.astimezone(IST).strftime('%Y-%m-%d %H:%M:%S IST')
            else:
                # Fallback to stored values
                first_encountered = error.get('first_encountered', 'Unknown')
                last_encountered = error.get('last_encountered', 'Unknown')
                
                # If still not available, use window times
                if first_encountered == 'Unknown':
                    first_encountered = error.get('window_start', 'Unknown')
                if last_encountered == 'Unknown':
                    last_encountered = error.get('window_end', 'Unknown')
        
        # Extract error directory for report link
        error_dir = error.get('error_dir', '')
        
        error_rows.append({
            'Service': service_name,
            'Error Count': error_count,
            'First Encountered': first_encountered,
            'Last Encountered': last_encountered,
            'Error Directory': error_dir
        })
    
    if error_rows:
        df = pd.DataFrame(error_rows)
        
        # Display the table
        st.dataframe(df, use_container_width=True)
        
        # Add View Report buttons for each error
        st.subheader("🔍 **View Detailed Reports**")
        
        for i, error in enumerate(error_rows):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{error['Service']}** - {error['Error Count']} errors")
                st.caption(f"First: {error['First Encountered']} | Last: {error['Last Encountered']}")
            
            with col2:
                # Create the report URL
                error_dir = error['Error Directory']
                if error_dir:
                    report_url = f"http://3.7.67.210:8501/?error_dir={error_dir}"
                    st.markdown(f"[📊 RCA Report]({report_url})")
                else:
                    st.markdown("📊 No RCA report")
            
            with col3:
                # Add status indicator
                if error['Error Count'] > 10:
                    st.markdown("🔴 **High Frequency**")
                elif error['Error Count'] > 5:
                    st.markdown("🟠 **Medium Frequency**")
                else:
                    st.markdown("🟢 **Low Frequency**")
            
            st.markdown("---")
    else:
        st.info("No error details available for the selected time period.")

def create_service_analytics(filtered_data):
    """Create service-wise analytics"""
    if not filtered_data:
        return
    
    st.subheader("Service-wise Analytics")
    
    # Group by service
    service_groups = defaultdict(list)
    for error in filtered_data:
        service = error.get('service', 'Unknown')
        service_groups[service].append(error)
    
    # Create service cards
    for service, errors in service_groups.items():
        total_count = sum(error.get('count', 0) for error in errors)
        unique_exceptions = len(set(error.get('exception', 'Unknown') for error in errors))
        envs = set(error.get('env', 'Unknown') for error in errors)
        
        with st.expander(f"{service} ({len(errors)} errors, {total_count} total)"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Errors", total_count)
            
            with col2:
                st.metric("Unique Exceptions", unique_exceptions)
            
            with col3:
                st.metric("Environments", len(envs))
            
            # Show recent errors for this service
            st.write("Recent Errors:")
            recent_errors = sorted(errors, key=lambda x: x.get('timestamp', datetime.min), reverse=True)[:5]
            
            for error in recent_errors:
                st.write(f"- **{error.get('exception', 'Unknown')}** ({error.get('count', 0)} occurrences)")
                st.write(f"  Environment: {error.get('env', 'Unknown')}, HTTP: {error.get('http_code', 'Unknown')}")

def get_theme_colors(theme_mode="Light"):
    """Get theme-aware colors for charts and UI"""
    if theme_mode == "Dark":
        return {
            'text_color': '#ffffff',
            'grid_color': 'rgba(255,255,255,0.1)',
            'line_color': 'rgba(255,255,255,0.3)',
            'legend_bg': 'rgba(0,0,0,0.8)',
            'legend_border': 'rgba(255,255,255,0.2)'
        }
    else:  # Light theme (default)
        return {
            'text_color': '#000000',
            'grid_color': 'rgba(0,0,0,0.1)',
            'line_color': 'rgba(0,0,0,0.3)',
            'legend_bg': 'rgba(255,255,255,0.9)',
            'legend_border': 'rgba(0,0,0,0.2)'
        }

def main():
    st.markdown('<h1 class="main-header">Error-Dashboard</h1>', unsafe_allow_html=True)
    
    # Custom time range input
    st.sidebar.header("Time Range Configuration")
    
    # Time filter options
    time_options = {
        "Last 1 Hour": 1,
        "Last 3 Hours": 3,
        "Last 6 Hours": 6,
        "Last 12 Hours": 12,
        "Last 24 Hours": 24
    }
    
    # Add custom time range
    st.sidebar.subheader("Custom Time Range")
    custom_hours = st.sidebar.number_input(
        "Enter custom hours (e.g., 6 for last 6 hours):",
        min_value=1,
        max_value=168,  # 1 week
        value=6,
        step=1
    )
    
    # Preset options
    selected_time = st.sidebar.selectbox(
        "Or select preset:",
        list(time_options.keys()),
        index=2  # Default to 6 hours
    )
    
    # Use custom hours if user entered them, otherwise use preset
    if st.sidebar.checkbox("Use custom time range"):
        hours = custom_hours
        st.sidebar.write(f"Using custom range: Last {hours} hours")
    else:
        hours = time_options[selected_time]
        st.sidebar.write(f"Using preset: {selected_time}")
    
    # Theme toggle
    st.sidebar.subheader("Theme Settings")
    theme_mode = st.sidebar.selectbox(
        "Choose theme:",
        ["Light", "Dark", "Auto"],
        index=0
    )
    
    # Add JavaScript to update theme
    st.markdown(f"""
    <script>
        setTheme('{theme_mode}');
    </script>
    """, unsafe_allow_html=True)
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto-refresh every 30 seconds", value=True)
    
    if auto_refresh:
        st.sidebar.write("🔄 Auto-refreshing...")
    
    # Load data
    error_data = load_error_data()
    filtered_data = get_time_filtered_data(error_data, hours)
    historical_data = get_historical_data(error_data, hours)
    
    # Display last update time
    st.sidebar.write(f"Last updated: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}")
    
    # Create dashboard sections
    create_metrics_dashboard(filtered_data, hours)
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Error Summary", "Error Details", "Service Analytics", "Real-time Monitor"])
    
    with tab1:
        create_error_summary_table(filtered_data, historical_data)
    
    with tab2:
        create_error_details_table(filtered_data)
    
    with tab3:
        create_service_analytics(filtered_data)
    
    with tab4:
        st.subheader("Real-time Error Monitor")
        
        # Show recent errors
        if filtered_data:
            recent_errors = sorted(filtered_data, key=lambda x: x.get('timestamp', datetime.min), reverse=True)[:10]
            
            st.write("**Latest Errors:**")
            for error in recent_errors:
                timestamp = error.get('timestamp', datetime.now(IST))
                time_ago = datetime.now(IST) - timestamp
                
                if time_ago.total_seconds() < 300:  # Less than 5 minutes
                    status = "🟢"
                elif time_ago.total_seconds() < 1800:  # Less than 30 minutes
                    status = "🟡"
                else:
                    status = "🔴"
                
                st.write(f"{status} **{error.get('service', 'Unknown')}** - {error.get('exception', 'Unknown')}")
                st.write(f"   Time: {timestamp.strftime('%H:%M:%S')} ({time_ago.total_seconds()/60:.1f} min ago)")
                st.write(f"   Count: {error.get('count', 0)}, HTTP: {error.get('http_code', 'Unknown')}")
                st.write("---")
        else:
            st.info("No recent errors found.")
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main() 
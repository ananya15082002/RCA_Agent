import requests
import os
import json
import time
import pytz
import base64
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import shutil
import re
import socket
import threading
import subprocess
from datetime import datetime, timedelta
from collections import defaultdict
import io
import urllib.parse

def create_clean_redirect_url(target_url):
    """Create a clean redirect URL that bypasses Google's URL wrapper"""
    # Use TinyURL API to create a short URL that bypasses Google's wrapper
    try:
        import requests
        # Use TinyURL API to create a short URL
        response = requests.get(f"http://tinyurl.com/api-create.php?url={target_url}", timeout=5)
        if response.status_code == 200:
            return response.text.strip()
        else:
            # Fallback to direct URL
            return target_url
    except Exception:
        # If API fails, return direct URL
        return target_url

# --- CONFIG ---
IST = pytz.timezone('Asia/Kolkata')
METRIC_URL = 'http://observability-prod.fxtrt.io:3130/api/metrics/api/v1/query_range'
TRACE_SEARCH_URL = "https://cubeapm-newrelic-prod.fxtrt.io/api/traces/api/v1/search"
TRACE_DETAIL_URL = "http://observability-prod.fxtrt.io:3130/api/traces/api/v1/traces"
LOGS_API_URL = "http://observability-prod.fxtrt.io:3130/api/logs/select/logsql/query"
GOOGLE_CHAT_WEBHOOK = "https://chat.googleapis.com/v1/spaces/AAQAsi2-pJQ/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=kwdBqpmd8KtBvhGsWY1CmyqyPIeRHrQ0NU5RcNgDpRE"
# Note: Hugging Face LLM integration removed - system uses enhanced template-based RCA
OUTPUT_ROOT = "error_outputs"
STATE_FILE = "last_processed_epoch.txt"
PUBLIC_ROOT_URL = "file://" + os.path.abspath(OUTPUT_ROOT)

WINDOW_MINUTES = 5    # Increase time window if needed
WINDOW_SIZE = WINDOW_MINUTES * 60  # in seconds

# Target services for error monitoring - UNSET environment services
TARGET_SERVICES = [
    "prod-ucp-app-shopify",
    "prod-ucp-app-gateway",
    "prod-ucp-app-sales",
    "Ticket_Management_Mumbai",
    "prod-ucp-app-package-consumers",
    "dlv-payouts-prod",
    "Core-FAAS",
    "prod-ucp-app-hq",
    "prod-ucp-app-auth",
    "prod-ucp-app-company",
    "wms-pack",
    "cubeAPM-aws-shipper",
    "dlv-requisition-prod",
    "prod-ucp-app-tasks",
    "prod-ucp-app-callbacks",
    "wms-container",
    "prod-ucp-app-salesforce",
    "local-wms-platform-integrator",
    "prod-ucp-app-woocommerce",
    "prod-ucp-app-catalog",
    "wms-billing",
    "prod-ucp-app-cron",
    "prod-ucp-app-oracle",
    "prod-ucp-app-starfleet"
]

# UNSET is the environment name, not a service
UNSET_ENVIRONMENT = "UNSET"

os.makedirs(OUTPUT_ROOT, exist_ok=True)

# --- Utility Functions ---

def to_epoch(dt):
    return int(dt.astimezone(pytz.utc).timestamp())

def epoch_to_ist(epoch):
    return datetime.fromtimestamp(epoch, IST)

def fetch_error_metrics(start_epoch, end_epoch, start_str, end_str):
    """
    Fetch error metrics for UNSET environment services with 5xx HTTP codes and ERROR status codes.
    """
    all_error_cards = []
    
    # Create service filter for target services
    service_filter = '|'.join(TARGET_SERVICES)
    
    # Query 1: HTTP 4xx and 5xx errors
    query1 = f'''
    sum by (env,service,root_name,http_code,exception,span_kind) (
        increase(cube_apm_calls_total{{
            env="{UNSET_ENVIRONMENT}",
            service=~"({service_filter})",
            span_kind=~"server|consumer",
            http_code=~"5.."
        }}[{WINDOW_MINUTES}m])
    )
    '''
    
    # Query 2: ERROR status codes (where http_code might be NA or missing)
    query2 = f'''
    sum by (env,service,root_name,http_code,exception,span_kind) (
        increase(cube_apm_calls_total{{
            env="{UNSET_ENVIRONMENT}",
            service=~"({service_filter})",
            span_kind=~"server|consumer",
            status_code="ERROR"
        }}[{WINDOW_MINUTES}m])
    )
    '''
    
    queries = [query1, query2]
    
    for i, query in enumerate(queries):
        try:
            data = {
                "query": query,
                "start": start_epoch,
                "end": end_epoch,
                "step": "30"
            }
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            r = requests.post(METRIC_URL, data=data, headers=headers, timeout=30)
            r.raise_for_status()
            result = r.json()
            
            for m in result.get("data", {}).get("result", []):
                count = float(m["values"][-1][1])
                if count > 0:
                    # Get service and environment
                    service = m["metric"].get("service", "Unknown")
                    env = m["metric"].get("env", "Unknown")
                    
                    # Handle http_code - if it's NA or missing, set to "ERROR"
                    http_code = m["metric"].get("http_code", "ERROR")
                    if http_code in ["NA", "", None]:
                        http_code = "ERROR"
                    
                    error_card = {
                        "env": env,
                        "service": service,
            "span_kind": m["metric"].get("span_kind"),
                        "http_code": http_code,
                        "exception": m["metric"].get("exception", "Unknown Error"),
                        "root_name": m["metric"].get("root_name", "Unknown"),
                        "count": count,
            "window_start": start_str,
            "window_end": end_str,
            "values": m["values"]
        }
                    all_error_cards.append(error_card)
                    
        except Exception as e:
            print(f"[WARN] Error fetching metrics for query {i+1}: {e}")
            continue
    
    # Remove duplicates based on service, root_name, http_code, exception combination
    unique_cards = {}
    for card in all_error_cards:
        key = (card["service"], card["root_name"], card["http_code"], card["exception"])
        if key not in unique_cards:
            unique_cards[key] = card
        else:
            # If duplicate found, sum the counts
            unique_cards[key]["count"] += card["count"]
    
    return list(unique_cards.values())

def base64_to_hex(b64str):
    if not b64str:
        return None
    try:
        return base64.b64decode(b64str + "=" * ((4 - len(b64str) % 4) % 4)).hex()
    except Exception:
        return b64str

def build_trace_search_url(card, window_start, window_end):
    params = {
        "query": '"span_kind":in("server","consumer")',
        "sortBy": "",
        "index": "-",
        "env": card['env'],
        "service": card['service'],
        "host": "-",
        "version": "-",
        "category": "",
        "rootName": card.get("root_name", ""),
        "spanName": "",
        "spanKind": "-",
        "start": to_epoch(window_start),
        "end": to_epoch(window_end),
        "exception": card.get("exception", ""),
        "limit": 100
    }
    
    # Handle status_code based on http_code
    http_code = card.get("http_code", "")
    if http_code == "ERROR":
        # For ERROR status, we'll search by status_code=ERROR
        params["status_code"] = "ERROR"
    else:
        # For HTTP codes, use the http_code as status_code
        params["status_code"] = http_code
    
    query_string = '&'.join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())
    return f"{TRACE_SEARCH_URL}?{query_string}"

def fetch_trace_bundle(trace_url):
    try:
        r = requests.get(trace_url, timeout=30)
        return r.json()
    except Exception as e:
        print(f"[WARN] Trace bundle fetch failed: {e}")
        return []

def fetch_full_trace(trace_id, start_epoch, end_epoch):
    url = f"{TRACE_DETAIL_URL}/{trace_id}?start={start_epoch}&end={end_epoch}"
    try:
        r = requests.get(url, timeout=30)
        return r.json()
    except Exception as e:
        print(f"[WARN] Full trace fetch failed: {e}")
        return {}

def fetch_logs(trace_id, start_epoch, end_epoch, limit=1000):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    query_string = f'{{}} _time:[{start_epoch},{end_epoch}) (trace_id:="{trace_id}" OR trace.id:="{trace_id}")'
    payload = [("query", query_string), ("limit", str(limit))]
    try:
        resp = requests.post(LOGS_API_URL, data=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            lines = resp.text.splitlines()
            return [json.loads(line) for line in lines if line.strip()]
    except Exception as e:
        return []

def extract_unique_trace_ids_hex(trace_bundle):
    trace_ids_hex = []
    seen = set()
    for t in trace_bundle:
        trace = t.get("trace", {})
        for span in trace.get("spans", []):
            tid_b64 = span.get("trace_id")
            tid_hex = base64_to_hex(tid_b64)
            if tid_hex and tid_hex not in seen:
                seen.add(tid_hex)
                trace_ids_hex.append(tid_hex)
    return trace_ids_hex

def save_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)

def is_error_span(tags):
    # tags is a dict (from tag_dict), but sometimes it's a list in raw
    # Collect all keys and values
    possible_status_keys = [
        "http.statusCode", "http.status_code", "httpResponseCode", "response.status", "response.statusCode"
    ]
    # check all 5xx status (as str/int) in all tag fields
    for k in possible_status_keys:
        v = tags.get(k)
        if v is not None:
            try:
                v_str = str(v)
                # Check for 5xx errors only
                if v_str.startswith('5'):
                    if len(v_str) == 3:
                        return True
                if isinstance(v, (int, float)) and (500 <= int(v) <= 599):
                    return True
            except Exception:
                continue
    # Otel status
    if tags.get("otel.status_code", "").upper() == "ERROR":
        return True
    # Error tags
    if tags.get("error") is True or str(tags.get("error")).lower() == "true":
        return True
    # Special: error.expected, error.class
    if "error.class" in tags or "error.expected" in tags or "otel.status_description" in tags:
        return True
    return False

def parse_span_metadata(trace):
    result = []
    for span in trace.get("spans", []):
        # tags: both as dict and as list of dicts (raw)
        tag_dict = {t["key"]: t.get("v_str", t.get("v_bool", t.get("v_float64", t.get("v_int64", "")))) for t in span.get("tags", [])}
        # Use the new error detection function
        is_error = is_error_span(tag_dict)
        span_data = {
            "trace_id": base64_to_hex(span.get("trace_id")),
            "span_id": base64_to_hex(span.get("span_id")),
            "operation_name": span.get("operation_name"),
            "references": span.get("references"),
            "flags": span.get("flags"),
            "start_time": span.get("start_time"),
            "duration": span.get("duration"),
            "tags": tag_dict,
            "is_error": is_error,
            "process_service_name": span.get("process", {}).get("service_name", None)
        }
        result.append(span_data)
    return result

def parse_log_metadata(logs):
    log_rows = []
    for log in logs:
        if not isinstance(log, dict):
            continue
        row = {
            "timestamp": log.get("_time") or log.get("timestamp"),
            "msg": log.get("_msg") or log.get("message"),
            "trace_id": log.get("trace.id") or log.get("trace_id"),
            "span_id": log.get("span.id") or log.get("span_id"),
            "host": log.get("host.name") or log.get("host"),
            "env": log.get("env"),
            "service": log.get("service.name") or log.get("service")
        }
        log_rows.append(row)
    return log_rows

def get_first_last_times(logs, spans):
    times = []
    for row in logs:
        if row['timestamp']:
            try:
                times.append(pd.to_datetime(row['timestamp']))
            except Exception:
                pass
    for span in spans:
        if span['start_time']:
            try:
                times.append(pd.to_datetime(span['start_time']))
            except Exception:
                pass
    if not times:
        return "", ""
    times_sorted = sorted(times)
    
    # Convert to IST and format properly
    first_time = times_sorted[0].tz_localize('UTC').tz_convert(IST).strftime('%Y-%m-%d %H:%M:%S IST')
    last_time = times_sorted[-1].tz_localize('UTC').tz_convert(IST).strftime('%Y-%m-%d %H:%M:%S IST')
    
    return first_time, last_time

def extract_comprehensive_evidence(all_span_meta, all_log_meta, card):
    """Extract comprehensive evidence data with proper formatting"""
    import json
    from datetime import datetime
    
    def format_timestamp(timestamp):
        """Format timestamp properly"""
        if not timestamp:
            return "Unknown"
        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " IST"
        except:
            return str(timestamp)
    
    def format_duration(duration_ms):
        """Format duration in human readable format"""
        if not duration_ms:
            return "0ms"
        try:
            duration_ms = float(duration_ms)
            if duration_ms < 1000:
                return f"{duration_ms:.1f}ms"
            elif duration_ms < 60000:
                return f"{duration_ms/1000:.2f}s"
            else:
                return f"{duration_ms/60000:.2f}min"
        except:
            return f"{duration_ms}ms"
    
    # Extract error spans with comprehensive data
    error_spans_detailed = []
    for span in all_span_meta:
        if span.get("is_error", False):
            span_data = {
                "trace_id": span.get("trace_id", ""),
                "span_id": span.get("span_id", ""),
                "operation_name": span.get("operation_name", ""),
                "start_time": format_timestamp(span.get("start_time")),
                "duration": format_duration(span.get("duration")),
                "duration_ms": span.get("duration", 0),
                "process_service_name": span.get("process_service_name", ""),
                "is_error": span.get("is_error", False),
                "tags": span.get("tags", {}),
                "all_tags_formatted": []
            }
            
            # Format all tags properly
            tags = span.get("tags", {})
            for key, value in tags.items():
                if value is not None and str(value).strip():
                    span_data["all_tags_formatted"].append(f"{key}: {value}")
            
            error_spans_detailed.append(span_data)
    
    # Extract error logs with comprehensive data
    error_logs_detailed = []
    for log in all_log_meta:
        if any(error_word in log.get("msg", "").lower() for error_word in 
               ["error", "exception", "failed", "timeout", "5xx", "500", "crash"]):
            log_data = {
                "trace_id": log.get("trace_id", ""),
                "span_id": log.get("span_id", ""),
                "timestamp": format_timestamp(log.get("timestamp")),
                "message": log.get("msg", ""),
                "host": log.get("host", ""),
                "service": log.get("service", ""),
                "env": log.get("env", "")
            }
            error_logs_detailed.append(log_data)
    
    # Group by trace_id for better organization
    traces_summary = {}
    for span in error_spans_detailed:
        trace_id = span["trace_id"]
        if trace_id not in traces_summary:
            traces_summary[trace_id] = {
                "trace_id": trace_id,
                "error_spans": [],
                "error_logs": [],
                "total_spans": 0,
                "total_logs": 0,
                "operations": set(),
                "services": set()
            }
        
        traces_summary[trace_id]["error_spans"].append(span)
        traces_summary[trace_id]["operations"].add(span["operation_name"])
        if span["process_service_name"]:
            traces_summary[trace_id]["services"].add(span["process_service_name"])
    
    # Add logs to traces
    for log in error_logs_detailed:
        trace_id = log["trace_id"]
        if trace_id in traces_summary:
            traces_summary[trace_id]["error_logs"].append(log)
    
    # Calculate totals
    for trace_id, trace_data in traces_summary.items():
        trace_data["total_spans"] = len(trace_data["error_spans"])
        trace_data["total_logs"] = len(trace_data["error_logs"])
        trace_data["operations"] = list(trace_data["operations"])
        trace_data["services"] = list(trace_data["services"])
    
    # Create comprehensive evidence structure
    evidence = {
        "incident_summary": {
            "service": card.get("service", "Unknown"),
            "environment": card.get("env", "Unknown"),
            "error_count": card.get("count", 0),
            "http_code": card.get("http_code", "Unknown"),
            "root_name": card.get("root_name", "Unknown"),
            "exception": card.get("exception", "Unknown"),
            "window_start": card.get("window_start", "Unknown"),
            "window_end": card.get("window_end", "Unknown")
        },
        "error_analysis": {
            "total_error_spans": len(error_spans_detailed),
            "total_error_logs": len(error_logs_detailed),
            "unique_traces": len(traces_summary),
            "unique_operations": len(set(span["operation_name"] for span in error_spans_detailed)),
            "unique_services": len(set(span["process_service_name"] for span in error_spans_detailed if span["process_service_name"]))
        },
        "traces_summary": traces_summary,
        "error_spans_detailed": error_spans_detailed,
        "error_logs_detailed": error_logs_detailed
    }
    
    return evidence

def extract_top_tags(all_span_meta, wanted_tags=None, top_n=5):
    if wanted_tags is None:
        wanted_tags = ['url', 'http.url', 'user_id', 'user', 'http.method', 'component', 'resource.name', 'request.uri', 'operation_name', 'span.kind']
    tags_found = {}
    for span in all_span_meta:
        tags = span.get('tags', {})
        for k in wanted_tags:
            v = tags.get(k)
            if v and k not in tags_found:
                tags_found[k] = v
            if len(tags_found) >= top_n:
                break
        if len(tags_found) >= top_n:
            break
    return list(tags_found.items())

def format_ts(ts):
    if not ts:
        return ""
    dt = pd.to_datetime(ts, utc=True)
    # Convert UTC to IST
    ist_dt = dt + pd.Timedelta(hours=5, minutes=30)
    return ist_dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " IST"

def format_duration(duration_value):
    try:
        duration = float(duration_value)
        
        # Check if duration is in microseconds (typical for Jaeger/OpenTelemetry)
        # If duration > 1000000, it's likely in microseconds, convert to ms
        if duration > 1000000:
            duration = duration / 1000  # Convert microseconds to milliseconds
        
        # Now duration is in milliseconds
        if duration < 1000:
            return f"{duration:.0f} ms"
        elif duration < 60_000:
            return f"{duration/1000:.2f} s"
        else:
            return f"{duration/60000:.2f} min"
    except Exception:
        return str(duration_value)

def extract_rca_tags(tag_dict, wanted=None, max_items=3):
    if wanted is None:
        wanted = [
            "http.status_code", "httpResponseCode", "exception", "error.class",
            "error.message", "otel.status_code", "category", "component"
        ]
    result = []
    for key in wanted:
        v = tag_dict.get(key)
        if v and len(result) < max_items:
            result.append(f"{key}: {v}")
    return "; ".join(result)

def extract_affected_fields(tag_dict):
    fields = []
    for key in ["http.url", "request.uri", "user_id", "user"]:
        if key in tag_dict:
            fields.append(f"{key}: {tag_dict[key]}")
    return "; ".join(fields)

def deduplicate_timeline_events(timeline):
    """Deduplicate timeline events based on key fields"""
    seen_events = set()
    deduplicated_timeline = []
    
    for event in timeline:
        # Create a unique key based on key fields that should be identical for duplicates
        event_key = (
            event.get("timestamp", ""),
            event.get("operation_name", ""),
            event.get("service_name", ""),
            event.get("why", ""),
            event.get("affected", ""),
            event.get("duration", "")
        )
        
        if event_key not in seen_events:
            seen_events.add(event_key)
            deduplicated_timeline.append(event)
        else:
            # Log that we found a duplicate
            print(f"[INFO] Found duplicate event: {event.get('operation_name', 'Unknown')} at {event.get('timestamp', 'Unknown')}")
    
    print(f"[INFO] Deduplicated timeline: {len(timeline)} -> {len(deduplicated_timeline)} events")
    return deduplicated_timeline

def build_correlation_timeline(card, all_span_meta, all_log_meta, corr_dir):
    # 1. Group logs by trace_id (lower-cased for consistency)
    logs_by_trace = defaultdict(list)
    for log in all_log_meta:
        tid = (log.get("trace_id") or log.get("trace.id") or "").lower()
        logs_by_trace[tid].append(log)
    
    # 2. Compute min/max timestamp for each trace (for summary)
    trace_bounds = defaultdict(list)
    for span in all_span_meta:
        tid = span["trace_id"].lower()
        trace_bounds[tid].append(span["start_time"])
    for tid, logs in logs_by_trace.items():
        for log in logs:
            ts_str = log.get("timestamp")
            if ts_str:
                trace_bounds[tid].append(ts_str)
    trace_time_bounds = {}
    for tid, ts_list in trace_bounds.items():
        ts_parsed = [pd.to_datetime(ts, utc=True) for ts in ts_list if ts]
        if ts_parsed:
            trace_time_bounds[tid] = (min(ts_parsed), max(ts_parsed))
    
    # 3. Build timeline rows (one per error span)
    timeline = []
    for span in all_span_meta:
        tid = span["trace_id"].lower()
        tag_dict = span["tags"]
        log_msgs = "\n".join(l.get("msg", "") for l in logs_by_trace.get(tid, []))
        first_ts, last_ts = trace_time_bounds.get(tid, ("", ""))
        timeline.append({
            "timestamp": format_ts(span["start_time"]),
            "trace_id": tid,
            "span_id": span["span_id"],
            "operation_name": span["operation_name"],
            "service_name": span["process_service_name"],
            "duration": format_duration(span["duration"]),
            "why": extract_rca_tags(tag_dict),
            "affected": extract_affected_fields(tag_dict),
            "log_messages": log_msgs,
            "first_encountered": format_ts(first_ts) if first_ts else "",
            "last_encountered": format_ts(last_ts) if last_ts else ""
        })
    
    # 4. Track original count before deduplication
    original_timeline_count = len(timeline)
    
    # 5. Deduplicate timeline events
    timeline = deduplicate_timeline_events(timeline)
    
    # Sort timeline by timestamp
    timeline = sorted(timeline, key=lambda x: x["timestamp"])
    # Save to CSV for the UI
    df = pd.DataFrame(timeline)
    csv_path = os.path.join(corr_dir, "correlation_timeline.csv")
    df.to_csv(csv_path, index=False)
    print(f"[✓] RCA correlation timeline saved: {csv_path}")
    # Build summary header (not per row)
    summary = {
        "env": card.get("env"),
        "service": card.get("service"),
        "root_name": card.get("root_name"),
        "http_code": card.get("http_code"),
        "exception": card.get("exception"),
        "error_count": card.get("count"),
        "window_start": card.get("window_start"),
        "window_end": card.get("window_end"),
        "unique_traces": len(trace_time_bounds),
        "original_timeline_count": original_timeline_count,
        "deduplicated_timeline_count": len(timeline),
        "first_overall": format_ts(min((v[0] for v in trace_time_bounds.values()), default="")) if trace_time_bounds else "",
        "last_overall": format_ts(max((v[1] for v in trace_time_bounds.values()), default="")) if trace_time_bounds else ""
    }
    return summary, timeline

def plot_advanced_error_analysis(card, all_span_meta=None, all_log_meta=None):
    """Create advanced error analysis visualization"""
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import numpy as np
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(f'Advanced Error Analysis: {card.get("service", "Unknown")} [{card.get("env", "Unknown")}]', 
                 fontsize=16, fontweight='bold')
    
    # 1. Error Spike Timeline (Enhanced)
    if card.get("values"):
        times = [float(x[0]) for x in card.get("values", [])]
        counts = [float(x[1]) for x in card.get("values", [])]
        if times and counts:
            dt_times = [datetime.fromtimestamp(t, tz=IST) for t in times]
            
            # Enhanced timeline with annotations
            ax1.plot(dt_times, counts, 'r-o', linewidth=2, markersize=6, alpha=0.8)
            ax1.fill_between(dt_times, counts, alpha=0.3, color='red')
            
            # Add threshold line
            threshold = max(counts) * 0.5 if counts else 0
            ax1.axhline(y=threshold, color='orange', linestyle='--', alpha=0.7, label=f'Threshold ({threshold:.1f})')
            
            # Highlight peak
            if counts:
                peak_idx = np.argmax(counts)
                ax1.annotate(f'Peak: {counts[peak_idx]:.0f}', 
                            xy=(dt_times[peak_idx], counts[peak_idx]),
                            xytext=(10, 10), textcoords='offset points',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
            
            ax1.set_title('Error Spike Timeline', fontweight='bold')
            ax1.set_xlabel('Time')
            ax1.set_ylabel('5xx Error Count')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # Format x-axis
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax1.xaxis.set_major_locator(mdates.MinuteLocator(interval=1))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # 2. Error Distribution by HTTP Code
    if all_span_meta:
        http_codes = {}
        for span in all_span_meta:
            if span.get("is_error", False):
                tags = span.get("tags", {})
                for key in ["http.statusCode", "http.status_code", "status_code"]:
                    if key in tags:
                        code = str(tags[key])
                        http_codes[code] = http_codes.get(code, 0) + 1
                        break
        
        if http_codes:
            codes = list(http_codes.keys())
            counts = list(http_codes.values())
            colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57']
            
            bars = ax2.bar(codes, counts, color=colors[:len(codes)], alpha=0.8)
            ax2.set_title('Error Distribution by HTTP Code', fontweight='bold')
            ax2.set_xlabel('HTTP Status Code')
            ax2.set_ylabel('Error Count')
            
            # Add value labels on bars
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{count}', ha='center', va='bottom', fontweight='bold')
    
    # 3. Error Duration Analysis
    if all_span_meta:
        error_durations = [span.get("duration", 0) for span in all_span_meta if span.get("is_error", False)]
        if error_durations:
            ax3.hist(error_durations, bins=20, color='#ff6b6b', alpha=0.7, edgecolor='black')
            ax3.set_title('Error Duration Distribution', fontweight='bold')
            ax3.set_xlabel('Duration (ms)')
            ax3.set_ylabel('Frequency')
            ax3.grid(True, alpha=0.3)
            
            # Add statistics
            mean_duration = np.mean(error_durations)
            ax3.axvline(mean_duration, color='red', linestyle='--', 
                       label=f'Mean: {mean_duration:.1f}ms')
            ax3.legend()
    
    # 4. Error Pattern Analysis
    if all_log_meta:
        error_keywords = ['error', 'exception', 'failed', 'timeout', 'connection', 'database']
        keyword_counts = {}
        
        for log in all_log_meta:
            msg = log.get("msg", "").lower()
            for keyword in error_keywords:
                if keyword in msg:
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        if keyword_counts:
            keywords = list(keyword_counts.keys())
            counts = list(keyword_counts.values())
            
            # Create horizontal bar chart
            y_pos = np.arange(len(keywords))
            bars = ax4.barh(y_pos, counts, color='#4ecdc4', alpha=0.8)
            ax4.set_yticks(y_pos)
            ax4.set_yticklabels(keywords)
            ax4.set_title('Error Keyword Analysis', fontweight='bold')
            ax4.set_xlabel('Occurrence Count')
            
            # Add value labels
            for i, (bar, count) in enumerate(zip(bars, counts)):
                width = bar.get_width()
                ax4.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                        f'{count}', ha='left', va='center', fontweight='bold')
    
    # Add summary statistics
    if card.get("count"):
        summary_text = f"""
Error Summary:
• Total Errors: {card.get('count', 0)}
• HTTP Code: {card.get('http_code', 'Unknown')}
• Service: {card.get('service', 'Unknown')}
• Environment: {card.get('env', 'Unknown')}
        """
        fig.text(0.02, 0.02, summary_text, fontsize=10, 
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.8))
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.9, bottom=0.1)
    
    # Save to buffer
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=300, bbox_inches='tight')
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close()
    return img_b64



def generate_detailed_rca(card, correlation_timeline, all_span_meta, all_log_meta):
    """Generate detailed RCA using enhanced analysis with better visualizations and NLP"""
    return generate_enhanced_rca_report(card, correlation_timeline, all_span_meta, all_log_meta)

def generate_enhanced_nlp_analysis(correlation_timeline, all_span_meta, all_log_meta):
    """Generate enhanced NLP analysis with advanced techniques"""
    analysis = "## 🤖 **ADVANCED AI-DRIVEN ANALYSIS**\n\n"
    
    # Error pattern clustering
    error_clusters = {}
    for event in correlation_timeline:
        error_type = event.get('why', '').split(';')[0] if event.get('why') else 'Unknown'
        if error_type not in error_clusters:
            error_clusters[error_type] = []
        error_clusters[error_type].append(event)
    
    analysis += "### **Error Pattern Clustering**\n"
    for error_type, events in error_clusters.items():
        analysis += f"• **{error_type}**: {len(events)} occurrences\n"
    analysis += "\n"
    
    # Service dependency analysis
    service_deps = {}
    for event in correlation_timeline:
        service = event.get('service_name', 'Unknown')
        if service not in service_deps:
            service_deps[service] = {'count': 0, 'errors': set()}
        service_deps[service]['count'] += 1
        service_deps[service]['errors'].add(event.get('why', '').split(';')[0])
    
    analysis += "### **Service Impact Analysis**\n"
    for service, data in sorted(service_deps.items(), key=lambda x: x[1]['count'], reverse=True)[:5]:
        analysis += f"• **{service}**: {data['count']} errors, {len(data['errors'])} unique error types\n"
    analysis += "\n"
    
    # Temporal analysis with proper formatting
    time_distribution = {}
    for event in correlation_timeline:
        timestamp = event.get('timestamp', '')
        if timestamp:
            try:
                if ' ' in timestamp and ':' in timestamp:
                    time_part = timestamp.split(' ')[1]
                    hour = time_part.split(':')[0]
                    formatted_hour = f"{int(hour):02d}:00"
                    time_distribution[formatted_hour] = time_distribution.get(formatted_hour, 0) + 1
            except (ValueError, IndexError):
                continue
    
    if time_distribution:
        analysis += "### **Temporal Error Distribution**\n"
        peak_hours = sorted(time_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        for hour, count in peak_hours:
            analysis += f"• **{hour}**: {count} errors\n"
        analysis += "\n"
    
    return analysis

def parse_duration_for_viz(duration_str):
    """Parse duration string and return numeric value for visualization"""
    if isinstance(duration_str, (int, float)):
        return float(duration_str)
    
    if isinstance(duration_str, str):
        # Handle formats like "2495.18 min", "1.5 s", "500 ms"
        try:
            if 'min' in duration_str:
                return float(duration_str.replace(' min', '')) * 60  # Convert to seconds
            elif 's' in duration_str and 'ms' not in duration_str:
                return float(duration_str.replace(' s', ''))
            elif 'ms' in duration_str:
                return float(duration_str.replace(' ms', '')) / 1000  # Convert to seconds
            else:
                return float(duration_str)
        except (ValueError, AttributeError):
            return 0.0
    
    return 0.0

def generate_visualization_data(correlation_timeline):
    """Generate data for visualizations"""
    viz_data = {
        'timeline': [],
        'service_errors': {},
        'error_types': {},
        'time_distribution': {}
    }
    
    for event in correlation_timeline:
        # Timeline data
        viz_data['timeline'].append({
            'timestamp': event.get('timestamp', ''),
            'service': event.get('service_name', ''),
            'operation': event.get('operation_name', ''),
            'duration': parse_duration_for_viz(event.get('duration', 0)),
            'error_type': event.get('why', '').split(';')[0] if event.get('why') else 'Unknown'
        })
        
        # Service error counts
        service = event.get('service_name', 'Unknown')
        viz_data['service_errors'][service] = viz_data['service_errors'].get(service, 0) + 1
        
        # Error type counts
        error_type = event.get('why', '').split(';')[0] if event.get('why') else 'Unknown'
        viz_data['error_types'][error_type] = viz_data['error_types'].get(error_type, 0) + 1
        
        # Time distribution
        timestamp = event.get('timestamp', '')
        if timestamp and ' ' in timestamp and ':' in timestamp:
            try:
                time_part = timestamp.split(' ')[1]
                hour = time_part.split(':')[0]
                formatted_hour = f"{int(hour):02d}:00"
                viz_data['time_distribution'][formatted_hour] = viz_data['time_distribution'].get(formatted_hour, 0) + 1
            except (ValueError, IndexError):
                continue
    
    return viz_data

def generate_enhanced_rca_report(card, correlation_timeline, all_span_meta, all_log_meta):
    """Generate enhanced RCA report with better visualizations and NLP"""
    
    # Build summary with better data validation
    total_events = len(correlation_timeline) if correlation_timeline else 0
    unique_traces = len(set(event.get('trace_id', '') for event in correlation_timeline)) if correlation_timeline else 0
    

    
    # Convert window times to IST for display
    window_start_ist = card.get('window_start', 'Unknown')
    window_end_ist = card.get('window_end', 'Unknown')
    
    # Convert times to IST if they're in UTC
    if window_start_ist != 'Unknown':
        try:
            # Parse the time string
            start_dt = pd.to_datetime(window_start_ist, format='%Y-%m-%d %H:%M:%S')
            end_dt = pd.to_datetime(window_end_ist, format='%Y-%m-%d %H:%M:%S')
            
            # Check if the times are in UTC (typically 5:30 hours behind IST)
            # If the hour is < 5, it's likely UTC, convert to IST
            if start_dt.hour < 5:
                # Convert UTC to IST (IST = UTC+5:30)
                ist_start = start_dt + pd.Timedelta(hours=5, minutes=30)
                ist_end = end_dt + pd.Timedelta(hours=5, minutes=30)
                window_start_ist = ist_start.strftime('%Y-%m-%d %H:%M:%S') + ' IST'
                window_end_ist = ist_end.strftime('%Y-%m-%d %H:%M:%S') + ' IST'
            else:
                # Already in IST format, just add IST suffix
                window_start_ist = window_start_ist + ' IST'
                window_end_ist = window_end_ist + ' IST'
        except:
            # If conversion fails, keep original but add IST suffix
            window_start_ist = window_start_ist + ' IST'
            window_end_ist = window_end_ist + ' IST'
    
    # Calculate first and last encountered times from correlation timeline
    first_encountered = "Unknown"
    last_encountered = "Unknown"
    
    if correlation_timeline:
        try:
            # Extract timestamps from correlation timeline
            timestamps = []
            for event in correlation_timeline:
                if event.get('timestamp'):
                    # Parse timestamp and convert to datetime
                    ts_str = event['timestamp']
                    if 'IST' in ts_str:
                        ts_str = ts_str.replace(' IST', '')
                    elif 'UTC' in ts_str:
                        ts_str = ts_str.replace(' UTC', '')
                    
                    try:
                        dt = pd.to_datetime(ts_str, format='%Y-%m-%d %H:%M:%S.%f')
                        timestamps.append(dt)
                    except:
                        try:
                            dt = pd.to_datetime(ts_str, format='%Y-%m-%d %H:%M:%S')
                            timestamps.append(dt)
                        except:
                            continue
            
            if timestamps:
                first_encountered = min(timestamps).strftime('%Y-%m-%d %H:%M:%S') + ' IST'
                last_encountered = max(timestamps).strftime('%Y-%m-%d %H:%M:%S') + ' IST'
        except Exception as e:
            print(f"[WARN] Error calculating first/last encountered times: {e}")
    
    summary = {
        'env': card.get('env', 'Unknown'),
        'service': card.get('service', 'Unknown'),
        'root_name': card.get('root_name', 'Unknown'),
        'http_code': card.get('http_code', 'Unknown'),
        'exception': card.get('exception', 'Unknown Error'),
        'error_count': card.get('count', 0),
        'window_start': window_start_ist,
        'window_end': window_end_ist,
        'unique_traces': unique_traces,
        'total_events': total_events,
        'first_encountered': first_encountered,
        'last_encountered': last_encountered
    }
    
    # Generate visualization data
    viz_data = generate_visualization_data(correlation_timeline)
    
    # Enhanced NLP Analysis
    nlp_analysis = generate_enhanced_nlp_analysis(correlation_timeline, all_span_meta, all_log_meta)
    
    # Consolidated log contexts
    consolidated_logs = consolidate_log_contexts(correlation_timeline)
    
    # Generate enhanced RCA report
    rca_report = f"""
# 🚨 **ADVANCED ROOT CAUSE ANALYSIS REPORT**

## 🎯 **EXECUTIVE SUMMARY**

| Metric | Value |
| Service Affected | {summary['service']} |
| Environment | {summary['env']} |
| Error Type | HTTP {summary['http_code']} - {summary['exception']} |
| Root Operation | {summary['root_name']} |
| Total Events | {summary['total_events']} |
| Unique Traces | {summary['unique_traces']} |
| First Encountered | {summary['first_encountered']} |
| Latest Encountered | {summary['last_encountered']} |
| Detection Window | {summary['window_start']} to {summary['window_end']} |

{nlp_analysis}

## 📊 **VISUALIZATION INSIGHTS**

### **Service Error Distribution**
"""
    
    # Add service error distribution
    for service, count in sorted(viz_data['service_errors'].items(), key=lambda x: x[1], reverse=True)[:5]:
        rca_report += f"• **{service}**: {count} errors\n"
    
    rca_report += "\n### **Error Type Distribution**\n"
    for error_type, count in sorted(viz_data['error_types'].items(), key=lambda x: x[1], reverse=True)[:5]:
        rca_report += f"• **{error_type}**: {count} occurrences\n"
    
    rca_report += "\n## 🎯 **ERROR FLOW ANALYSIS**\n\n"
    
    # Create a beautiful error flow visualization
    if correlation_timeline:
        # Group events by service for better visualization
        service_groups = {}
        for event in correlation_timeline:
            service = event['service_name']
            if service not in service_groups:
                service_groups[service] = []
            service_groups[service].append(event)
        
        # Create service flow diagram
        rca_report += "### 🔄 **Service Error Flow**\n\n"
        rca_report += "```mermaid\ngraph TD\n"
        
        # Add nodes for each service
        for i, (service, events) in enumerate(service_groups.items(), 1):
            error_count = len(events)
            avg_duration = sum(float(str(event['duration']).replace(' min', '').replace(' s', '').replace(' ms', '')) for event in events) / len(events)
            rca_report += f"    A{i}[{service}<br/>📊 {error_count} errors<br/>⏱️ {avg_duration:.1f}s avg]\n"
        
        # Add connections between services
        for i in range(1, len(service_groups)):
            rca_report += f"    A{i} --> A{i+1}\n"
        
        rca_report += "```\n\n"
        
        # Create timeline summary
        rca_report += "### ⏰ **Timeline Summary**\n\n"
        rca_report += "| Time Range | Total Events | Services Affected | Error Types |\n"
        rca_report += "|------------|--------------|-------------------|-------------|\n"
        
        if correlation_timeline:
            start_time = correlation_timeline[0]['timestamp']
            end_time = correlation_timeline[-1]['timestamp']
            total_events = len(correlation_timeline)
            services_affected = len(set(event['service_name'] for event in correlation_timeline))
            error_types = len(set(event['why'].split(';')[0] for event in correlation_timeline if event['why']))
            
            # Check if we have deduplication info - use a default if correlation_summary is not available
            original_count = total_events  # Default to same count
            if 'correlation_summary' in locals():
                original_count = correlation_summary.get("original_timeline_count", total_events)
            
            if original_count != total_events:
                rca_report += f"| {start_time} → {end_time} | {total_events} unique (from {original_count} total) | {services_affected} | {error_types} |\n"
            else:
                rca_report += f"| {start_time} → {end_time} | {total_events} | {services_affected} | {error_types} |\n"
        
        # Create error pattern summary
        rca_report += "\n### 📊 **Error Pattern Summary**\n\n"
        
        # HTTP Status Code Distribution
        status_codes = {}
        for event in correlation_timeline:
            if 'http.status_code' in event['why']:
                status = event['why'].split('http.status_code: ')[1].split(';')[0]
                status_codes[status] = status_codes.get(status, 0) + 1
        
        if status_codes:
            rca_report += "**HTTP Status Distribution:**\n"
            for status, count in sorted(status_codes.items(), key=lambda x: x[1], reverse=True):
                rca_report += f"• **{status}**: {count} occurrences\n"
            rca_report += "\n"
        
        # Service Impact Summary
        service_impact = {}
        for event in correlation_timeline:
            service = event['service_name']
            if service not in service_impact:
                service_impact[service] = {'count': 0, 'errors': set()}
            service_impact[service]['count'] += 1
            if event['why']:
                service_impact[service]['errors'].add(event['why'].split(';')[0])
        
        rca_report += "**Service Impact:**\n"
        for service, data in sorted(service_impact.items(), key=lambda x: x[1]['count'], reverse=True)[:5]:
            rca_report += f"• **{service}**: {data['count']} errors, {len(data['errors'])} unique error types\n"
        
        # Duration Analysis
        durations = []
        for event in correlation_timeline:
            try:
                dur_str = str(event['duration'])
                if 'min' in dur_str:
                    dur_val = float(dur_str.replace(' min', '')) * 60
                elif 's' in dur_str and 'ms' not in dur_str:
                    dur_val = float(dur_str.replace(' s', ''))
                elif 'ms' in dur_str:
                    dur_val = float(dur_str.replace(' ms', '')) / 1000
                else:
                    dur_val = float(dur_str)
                durations.append(dur_val)
            except:
                continue
        
        if durations:
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            rca_report += f"\n**Duration Analysis:**\n"
            rca_report += f"• **Average Duration**: {avg_duration:.2f}s\n"
            rca_report += f"• **Longest Duration**: {max_duration:.2f}s\n"
            rca_report += f"• **Total Events**: {len(durations)}\n"
        
        # Create interactive timeline (simplified)
        rca_report += "\n### 🎯 **Key Events Timeline**\n\n"
        
        # Show only the most significant events (first, last, and a few in between)
        key_events = []
        if len(correlation_timeline) > 0:
            key_events.append(correlation_timeline[0])  # First event
        if len(correlation_timeline) > 1:
            key_events.append(correlation_timeline[-1])  # Last event
        if len(correlation_timeline) > 2:
            # Add a few events from the middle
            mid_point = len(correlation_timeline) // 2
            key_events.append(correlation_timeline[mid_point])
        
        for i, event in enumerate(key_events, 1):
            rca_report += f"""
**🎯 Event {i}** - {event['timestamp']}
- **Service**: {event['service_name']}
- **Operation**: {event['operation_name']}
- **Error**: {event['why'].split(';')[0] if event['why'] else 'Unknown'}
- **Duration**: {event['duration']}

"""
        
        # Add a note about full timeline with deduplication info
        if len(correlation_timeline) > len(key_events):
            original_count = len(correlation_timeline)  # Default to same count
            deduplicated_count = len(correlation_timeline)
            
            # Check if we have deduplication info
            if 'correlation_summary' in locals():
                original_count = correlation_summary.get("original_timeline_count", len(correlation_timeline))
                deduplicated_count = correlation_summary.get("deduplicated_timeline_count", len(correlation_timeline))
            
            if original_count != deduplicated_count:
                rca_report += f"\n> 💡 **Note**: Showing {len(key_events)} key events from {len(correlation_timeline)} unique events (deduplicated from {original_count} total events). Full timeline available in correlation data.\n"
            else:
                rca_report += f"\n> 💡 **Note**: Showing {len(key_events)} key events from {len(correlation_timeline)} total events. Full timeline available in correlation data.\n"
        
        # Create beautiful error flow visualization
        rca_report += "\n### 🎨 **Error Flow Visualization**\n\n"
        rca_report += "```mermaid\nflowchart LR\n"
        
        # Create a more visual flow
        services = list(service_groups.keys())
        for i, service in enumerate(services):
            events = service_groups[service]
            error_count = len(events)
            
            # Determine error severity color
            if error_count > 10:
                color = "red"
                severity = "🔴 Critical"
            elif error_count > 5:
                color = "orange"
                severity = "🟠 High"
            else:
                color = "yellow"
                severity = "🟡 Medium"
            
            rca_report += f"    S{i}[{service}<br/>{severity}<br/>📊 {error_count} errors]\n"
            
            if i < len(services) - 1:
                rca_report += f"    S{i} --> S{i+1}\n"
        
        rca_report += "```\n\n"
        
        # Add error propagation analysis
        rca_report += "### 🔍 **Error Propagation Analysis**\n\n"
        
        if len(services) > 1:
            rca_report += f"**Error Flow Path:**\n"
            for i, service in enumerate(services):
                arrow = "→" if i < len(services) - 1 else ""
                rca_report += f"**{service}** {arrow} "
            rca_report += "\n\n"
            
            rca_report += f"**Propagation Chain:**\n"
            rca_report += f"• **Entry Point**: {services[0]}\n"
            rca_report += f"• **Exit Point**: {services[-1]}\n"
            rca_report += f"• **Chain Length**: {len(services)} services\n"
            rca_report += f"• **Total Impact**: {len(correlation_timeline)} events\n"
        else:
            rca_report += f"**Single Service Impact:**\n"
            rca_report += f"• **Service**: {services[0]}\n"
            rca_report += f"• **Events**: {len(correlation_timeline)}\n"
            rca_report += f"• **Isolated Issue**: No cross-service propagation detected\n"
    
    # Add consolidated log contexts
    if consolidated_logs:
        rca_report += "\n## 📝 **CONSOLIDATED LOG PATTERNS**\n\n"
        for i, log_data in enumerate(consolidated_logs, 1):
            rca_report += f"""
### **Log Pattern {i}** (Occurred {log_data['count']} times)
**Services**: {log_data['services']}
**Message**: {log_data['message']}

"""
    
    rca_report += f"""
## 🎯 **ROOT CAUSE DETERMINATION**

| **Aspect** | **Details** |
|------------|-------------|
| **Primary Cause** | {determine_primary_cause(summary, viz_data['error_types'])} |
| **Contributing Factors** | {identify_contributing_factors(viz_data['error_types'], viz_data['service_errors'])} |
| **Trigger Event** | {identify_trigger_event(correlation_timeline)} |

## 🚨 **IMMEDIATE ACTIONS REQUIRED**

{generate_immediate_actions(summary, viz_data['error_types'], determine_severity_level(summary, viz_data['error_types']))}

---

*Report generated using Advanced NLP Analysis - {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}*
"""
    
    return rca_report

def generate_enhanced_pattern_analysis(error_patterns, temporal_patterns):
    """Generate enhanced pattern analysis with better visualization"""
    analysis = "## 🔍 **PATTERN ANALYSIS**\n\n"
    
    if error_patterns['error_types']:
        top_errors = sorted(error_patterns['error_types'].items(), key=lambda x: x[1], reverse=True)[:3]
        analysis += "### **Most Frequent Error Types**\n"
        for i, (error, count) in enumerate(top_errors, 1):
            analysis += f"{i}. **{error}** - {count} occurrences\n"
        analysis += "\n"
    
    if temporal_patterns.get('formatted_peak_hours'):
        analysis += "### **Peak Error Time Windows**\n"
        for hour, count in temporal_patterns['formatted_peak_hours']:
            analysis += f"• **{hour}** - {count} errors\n"
        analysis += "\n"
    
    return analysis

def generate_enhanced_dependency_analysis(service_dependencies):
    """Generate enhanced dependency analysis with better visualization"""
    analysis = "## 🔗 **SERVICE DEPENDENCY ANALYSIS**\n\n"
    
    if service_dependencies['service_calls']:
        services = list(service_dependencies['service_calls'].keys())
        analysis += "### **Affected Services**\n"
        for i, service in enumerate(services[:5], 1):
            analysis += f"{i}. **{service}**\n"
        analysis += "\n"
        
        # Find slowest operations
        all_operations = []
        for service, operations in service_dependencies['service_calls'].items():
            for op in operations:
                all_operations.append((service, op['operation'], op['duration']))
        
        if all_operations:
            slowest_ops = sorted(all_operations, key=lambda x: x[2], reverse=True)[:3]
            analysis += "### **Performance Bottlenecks**\n"
            for i, (service, op, dur) in enumerate(slowest_ops, 1):
                analysis += f"{i}. **{service}** - {op} ({dur}ms)\n"
            analysis += "\n"
    
    return analysis

def generate_enhanced_propagation_analysis(correlation_timeline, all_span_meta):
    """Generate enhanced error propagation analysis"""
    analysis = "## 🔄 **ERROR PROPAGATION ANALYSIS**\n\n"
    
    if correlation_timeline:
        services_involved = set(event['service_name'] for event in correlation_timeline)
        analysis += "### **Services in Error Chain**\n"
        for i, service in enumerate(list(services_involved)[:5], 1):
            analysis += f"{i}. **{service}**\n"
        analysis += "\n"
        
        # Analyze error flow
        if len(correlation_timeline) > 1:
            first_service = correlation_timeline[0]['service_name']
            last_service = correlation_timeline[-1]['service_name']
            analysis += "### **Error Propagation Path**\n"
            analysis += f"**{first_service}** → **{last_service}**\n\n"
    
    return analysis

def generate_enhanced_impact_analysis(summary, error_patterns, service_dependencies):
    """Generate enhanced impact analysis"""
    analysis = "## 📊 **IMPACT ASSESSMENT**\n\n"
    
    error_count = summary.get('error_count', 0)
    unique_traces = summary.get('unique_traces', 0)
    
    # Impact level determination
    if error_count > 50:
        impact_level = "🔴 **CRITICAL IMPACT**"
        impact_desc = "Large number of affected requests"
    elif error_count > 20:
        impact_level = "🟠 **HIGH IMPACT**"
        impact_desc = "Moderate number of affected requests"
    else:
        impact_level = "🟡 **MEDIUM IMPACT**"
        impact_desc = "Limited number of affected requests"
    
    analysis += f"### **Impact Level**\n{impact_level}\n{impact_desc}\n\n"
    
    # Service scope assessment
    if len(service_dependencies['service_calls']) > 3:
        scope_level = "🌐 **BROAD IMPACT**"
        scope_desc = "Multiple services affected"
    else:
        scope_level = "🎯 **FOCUSED IMPACT**"
        scope_desc = "Limited service scope"
    
    analysis += f"### **Service Scope**\n{scope_level}\n{scope_desc}\n\n"
    
    # Metrics summary
    analysis += "### **Key Metrics**\n"
    analysis += f"• **Total Errors**: {error_count}\n"
    analysis += f"• **Unique Traces**: {unique_traces}\n"
    analysis += f"• **Services Affected**: {len(service_dependencies['service_calls'])}\n\n"
    
    return analysis

def determine_severity_level(summary, error_patterns):
    """Determine severity level based on error patterns and metrics"""
    error_count = summary.get('error_count', 0)
    unique_traces = summary.get('unique_traces', 0)
    
    if error_count > 100 or unique_traces > 50:
        return "🔴 CRITICAL"
    elif error_count > 50 or unique_traces > 20:
        return "🟠 HIGH"
    elif error_count > 20 or unique_traces > 10:
        return "🟡 MEDIUM"
    else:
        return "🟢 LOW"

def categorize_root_cause(summary, error_patterns, service_dependencies):
    """Categorize root cause using pattern analysis"""
    exception = summary.get('exception', '').lower()
    
    if any(keyword in exception for keyword in ['timeout', 'deadline']):
        return "⏰ TIMEOUT/PERFORMANCE"
    elif any(keyword in exception for keyword in ['connection', 'network']):
        return "🌐 NETWORK/CONNECTIVITY"
    elif any(keyword in exception for keyword in ['database', 'sql']):
        return "🗄️ DATABASE/STORAGE"
    elif any(keyword in exception for keyword in ['authentication', 'authorization']):
        return "🔐 AUTHENTICATION/AUTHORIZATION"
    elif any(keyword in exception for keyword in ['validation', 'format']):
        return "📝 DATA/VALIDATION"
    else:
        return "❓ UNKNOWN/APPLICATION"

def calculate_confidence_score(error_patterns, service_dependencies, log_sentiment):
    """Calculate confidence score for the analysis"""
    score = 50  # Base score
    
    # Add points for clear error patterns
    if len(error_patterns['error_types']) > 0:
        score += 20
    
    # Add points for service dependency analysis
    if len(service_dependencies['service_calls']) > 0:
        score += 15
    
    # Add points for log sentiment analysis
    if len(log_sentiment['error_keywords']) > 0:
        score += 15
    
    return min(score, 95)  # Cap at 95%

def generate_pattern_analysis(error_patterns, temporal_patterns):
    """Generate pattern analysis insights - DEPRECATED: Use generate_enhanced_pattern_analysis instead"""
    # This function is kept for backward compatibility but should use generate_enhanced_pattern_analysis
    return generate_enhanced_pattern_analysis(error_patterns, temporal_patterns)

def generate_dependency_analysis(service_dependencies):
    """Generate dependency analysis insights"""
    analysis = "**Service Dependency Analysis:**\n"
    
    if service_dependencies['service_calls']:
        services = list(service_dependencies['service_calls'].keys())
        analysis += f"- Affected services: {', '.join(services[:5])}\n"
        
        # Find slowest operations
        all_operations = []
        for service, operations in service_dependencies['service_calls'].items():
            for op in operations:
                all_operations.append((service, op['operation'], op['duration']))
        
        if all_operations:
            slowest_ops = sorted(all_operations, key=lambda x: x[2], reverse=True)[:3]
            analysis += f"- Slowest operations: {', '.join([f'{service}:{op} ({dur}ms)' for service, op, dur in slowest_ops])}\n"
    
    return analysis

def generate_propagation_analysis(correlation_timeline, all_span_meta):
    """Generate error propagation analysis"""
    analysis = "**Error Propagation Analysis:**\n"
    
    if correlation_timeline:
        services_involved = set(event['service_name'] for event in correlation_timeline)
        analysis += f"- Services in error chain: {', '.join(list(services_involved)[:5])}\n"
        
        # Analyze error flow
        if len(correlation_timeline) > 1:
            first_service = correlation_timeline[0]['service_name']
            last_service = correlation_timeline[-1]['service_name']
            analysis += f"- Error propagation: {first_service} → {last_service}\n"
    
    return analysis

def generate_impact_analysis(summary, error_patterns, service_dependencies):
    """Generate impact analysis"""
    analysis = "**Impact Assessment:**\n"
    
    error_count = summary.get('error_count', 0)
    unique_traces = summary.get('unique_traces', 0)
    
    if error_count > 50:
        analysis += "- **HIGH IMPACT**: Large number of affected requests\n"
    elif error_count > 20:
        analysis += "- **MEDIUM IMPACT**: Moderate number of affected requests\n"
    else:
        analysis += "- **LOW IMPACT**: Limited number of affected requests\n"
    
    if len(service_dependencies['service_calls']) > 3:
        analysis += "- **BROAD IMPACT**: Multiple services affected\n"
    else:
        analysis += "- **FOCUSED IMPACT**: Limited service scope\n"
    
    return analysis

def determine_primary_cause(summary, error_patterns):
    """Determine the primary cause of the incident"""
    exception = summary.get('exception', '').lower()
    
    if 'timeout' in exception:
        return "Service timeout or performance degradation"
    elif 'connection' in exception:
        return "Network connectivity issues"
    elif 'database' in exception or 'sql' in exception:
        return "Database-related issues"
    elif 'authentication' in exception:
        return "Authentication or authorization failure"
    else:
        return f"Application error: {summary.get('exception', 'Unknown')}"

def identify_contributing_factors(error_patterns, service_dependencies):
    """Identify contributing factors"""
    factors = []
    
    if len(error_patterns.get('error_types', {})) > 1:
        factors.append("Multiple error types indicating complex failure")
    
    if len(service_dependencies.get('service_calls', {})) > 2:
        factors.append("Service dependency chain complexity")
    
    if error_patterns.get('temporal_patterns', {}).get('time_distribution'):
        factors.append("Temporal clustering of errors")
    
    return "; ".join(factors) if factors else "Single point of failure"

def identify_trigger_event(correlation_timeline):
    """Identify the trigger event"""
    if correlation_timeline:
        first_event = correlation_timeline[0]
        return f"{first_event.get('operation_name', 'Unknown')} at {first_event.get('timestamp', 'Unknown')}"
    return "Unknown trigger event"

def generate_immediate_actions(summary, error_patterns, severity_level):
    """Generate immediate action recommendations"""
    actions = []
    
    if "CRITICAL" in severity_level:
        actions.append("🚨 **IMMEDIATE**: Isolate affected service")
        actions.append("📞 **ESCALATE**: Notify on-call team")
    
    actions.append(f"🔍 **INVESTIGATE**: Check {summary.get('service', 'affected service')} logs")
    actions.append("�� **MONITOR**: Watch for error rate changes")
    
    if len(error_patterns.get('error_types', {})) > 1:
        actions.append("🔧 **DEBUG**: Analyze multiple error patterns")
    
    return "\n".join(actions)

def generate_long_term_recommendations(summary, error_patterns, service_dependencies):
    """Generate long-term recommendations"""
    recommendations = []
    
    recommendations.append(f"🏗️ **ARCHITECTURE**: Review {summary.get('service', 'service')} design")
    recommendations.append("📈 **MONITORING**: Implement better error tracking")
    recommendations.append("🧪 **TESTING**: Add failure scenario testing")
    
    if len(service_dependencies.get('service_calls', {})) > 3:
        recommendations.append("🔗 **DEPENDENCIES**: Simplify service dependencies")
    
    return "\n".join(recommendations)

def generate_predictive_insights(error_patterns, temporal_patterns):
    """Generate predictive insights"""
    insights = []
    
    if temporal_patterns.get('time_distribution'):
        peak_hours = sorted(temporal_patterns['time_distribution'].items(), key=lambda x: x[1], reverse=True)[:2]
        if peak_hours:
            insights.append(f"⏰ **PATTERN**: Peak errors at {peak_hours[0][0]}:00 hours")
    
    if len(error_patterns.get('error_types', {})) > 1:
        insights.append("🔄 **TREND**: Multiple error types suggest systemic issues")
    
    return "\n".join(insights) if insights else "No clear patterns detected"

def analyze_similar_incidents(summary, error_patterns):
    """Analyze similar incidents"""
    analysis = "**Similar Incident Analysis:**\n"
    
    exception = summary.get('exception', '').lower()
    service = summary.get('service', '').lower()
    
    if 'timeout' in exception:
        analysis += "- Similar to performance-related incidents\n"
    elif 'connection' in exception:
        analysis += "- Similar to network connectivity issues\n"
    elif 'database' in exception:
        analysis += "- Similar to data access problems\n"
    
    if len(error_patterns.get('error_types', {})) > 2:
        analysis += "- Complex error pattern suggests recurring issues\n"
    
    return analysis

def create_simple_error_chart(card):
    """Create a simple error spike chart for each error
    
    The graph shows the error count over time from the PromQL query:
    - X-axis: Time (IST)
    - Y-axis: Error count (number of 5xx errors in that time window)
    - The data comes from card['values'] which contains [timestamp, count] pairs
    """
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    
    if not card.get("values"):
        return None
    
    try:
        # Create chart with better quality but still small size
        plt.figure(figsize=(6, 3.5))  # Better size for clarity
        
        times = [float(x[0]) for x in card.get("values", [])]
        counts = [float(x[1]) for x in card.get("values", [])]
        
        if times and counts:
            dt_times = [datetime.fromtimestamp(t, tz=IST) for t in times]
            
            # Create clearer chart
            plt.plot(dt_times, counts, 'r-o', linewidth=2, markersize=5, alpha=0.8)
            plt.fill_between(dt_times, counts, alpha=0.2, color='red')
            
            # Better title and labels
            plt.title(f'Error Spike: {card.get("service", "Unknown")}', fontsize=10, fontweight='bold')
            plt.xlabel('Time (IST)', fontsize=8)
            plt.ylabel('Error Count', fontsize=8)
            plt.grid(True, alpha=0.3)
            
            # Better time formatting
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            plt.setp(plt.gca().xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=7)
            plt.tight_layout(pad=1.0)  # Better padding
            
            # Save to buffer with better quality
            buf = BytesIO()
            plt.savefig(buf, format="png", dpi=120, bbox_inches='tight', facecolor='white')
            buf.seek(0)
            img_b64 = base64.b64encode(buf.read()).decode("utf-8")
            plt.close()
            
            # Check if image is too large for Google Chat (should be under 20KB)
            if len(img_b64) > 20000:
                print(f"[WARN] Chart too large ({len(img_b64)} bytes), reducing quality...")
                # Try with lower quality
                plt.figure(figsize=(5, 3))
                plt.plot(dt_times, counts, 'r-o', linewidth=1.5, markersize=4, alpha=0.8)
                plt.fill_between(dt_times, counts, alpha=0.15, color='red')
                plt.title(f'Error: {card.get("service", "Unknown")}', fontsize=9)
                plt.xlabel('Time', fontsize=7)
                plt.ylabel('Count', fontsize=7)
                plt.grid(True, alpha=0.2)
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                plt.setp(plt.gca().xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=6)
                plt.tight_layout(pad=0.8)
                
                buf = BytesIO()
                plt.savefig(buf, format="png", dpi=80, bbox_inches='tight', facecolor='white')
                buf.seek(0)
                img_b64 = base64.b64encode(buf.read()).decode("utf-8")
                plt.close()
                
                if len(img_b64) > 20000:
                    print(f"[WARN] Chart still too large ({len(img_b64)} bytes), skipping")
                    return None
                
            return img_b64
            
    except Exception as e:
        print(f"[WARN] Error creating simple chart: {e}")
        return None



def send_to_google_chat(card, card_dir, first_encountered, last_encountered, tags, corr_table_path, img_b64, rca_report):
    """Send structured error alert to Google Chat with proper 32KB limit handling"""
    
    service_name = card.get("service", "Unknown Service")
    env_name = card.get("env", "Unknown Environment")
    error_count = card.get("count", 0)
    http_code = card.get("http_code", "Unknown")
    root_name = card.get("root_name", "N/A")
    exception = card.get("exception", "N/A")
    
    # Format time properly
    def format_time_for_display(time_str):
        if not time_str:
            return "Unknown"
        try:
            # If already in IST format, return as is
            if 'IST' in time_str:
                return time_str
            
            # Parse the ISO format time (UTC)
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            # Convert to IST
            ist_time = dt.astimezone(IST)
            return ist_time.strftime("%Y-%m-%d %H:%M:%S IST")
        except:
            return time_str
    
    first_time_display = format_time_for_display(first_encountered)
    last_time_display = format_time_for_display(last_encountered)
    
    # Chart creation removed - Google Chat has size/format limitations
    chart_path = None
    
    # Create compact main card with essential info and embedded chart
    main_content = f"""🚨 ERROR ALERT

Service: {service_name}
Environment: {env_name}
Root Operation: {root_name}
HTTP Status: {http_code}
Exception: {exception}
Error Count: {error_count}
First Encountered: {first_time_display}
Latest Encountered: {last_time_display}

---
"""
    
    # Create timestamp for report ID
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_id = f"{service_name}_{timestamp}"
    
    # Create Streamlit portal URL - use public IP for global access
    try:
                    # Use public IP for global access
            public_ip = "49.36.211.68"  # Your EC2 public IP
        # Create a specific URL for this error report - use Streamlit portal
        direct_url = f"http://{public_ip}:8501/?error_dir={os.path.basename(card_dir)}"
        web_url = create_clean_redirect_url(direct_url)
        is_public = True
    except Exception:
        direct_url = f"http://49.36.211.68:8501/?error_dir={os.path.basename(card_dir)}"
        web_url = create_clean_redirect_url(direct_url)
        is_public = False
    
    # Add tags to the content if available
    tags_content = ""
    if tags:
        tags_content = "\n Tags:\n" + "\n".join([f"• {k}: {v}" for k, v in tags[:3]])
    
    full_content = main_content + tags_content
    
    # Create clean text-based card (no charts due to Google Chat limitations)
    enhanced_content = full_content
    
    main_payload = {
        "cardsV2": [{
            "cardId": "errorCard",
            "card": {
                "header": {"title": "🚨 Error Alert"},
                "sections": [
                    {
                        "widgets": [
                        {"textParagraph": {"text": enhanced_content}}
                        ]
                    },
                    {
                        "widgets": [
                            {
                                "buttonList": {
                                    "buttons": [{
                                        "text": "📊 View RCA Portal",
                                        "onClick": {"openLink": {"url": web_url}}
                                    }]
                                }
                            }
                        ]
                    }
                ]
            }
        }]
    }
    
    # Send main card
    try:
        r = requests.post(GOOGLE_CHAT_WEBHOOK, json=main_payload, timeout=10)
        if r.status_code == 200:
            print(f"[✓] Sent main error alert to Google Chat for {service_name}")
        else:
            print(f"[WARN] Main card send failed: {r.status_code} {r.text}")
    except Exception as e:
        print(f"[ERR] Exception in main card send: {e}")
    
    # Create web portal report directory and save files
    try:
        # Use the same report ID created above
        # report_id is already created above
        
        # Create web portal report directory and copy files
        web_reports_dir = os.path.join(os.path.expanduser("~"), "RCA_Reports", report_id)
        os.makedirs(web_reports_dir, exist_ok=True)
        
        # Save detailed RCA to error directory for Streamlit portal
        with open(os.path.join(card_dir, "detailed_rca.txt"), "w", encoding="utf-8") as f:
            f.write(rca_report)
        
        # Copy files to web portal directory
        import shutil
        shutil.copy2(corr_table_path, os.path.join(web_reports_dir, "correlation_table.csv"))
        shutil.copy2(os.path.join(card_dir, "detailed_rca.txt"), os.path.join(web_reports_dir, "detailed_rca.txt"))
        if img_b64:
            with open(os.path.join(web_reports_dir, "error_chart.png"), "wb") as f:
                f.write(base64.b64decode(img_b64))
        
        print(f" * [REPORT] Direct URL: {direct_url}")
        print(f" * [REPORT] Clean redirect: {web_url}")
        print(f"[✓] Streamlit portal available at: {direct_url}")
        if is_public:
            print(f"[✓] Network accessible to team members")
        else:
            print(f"[INFO] For network access, ensure port 8501 is open")
    except Exception as e:
        print(f"[ERR] Exception in web portal setup: {e}")

def consolidate_log_contexts(correlation_timeline):
    """Consolidate similar log contexts to reduce repetition"""
    log_patterns = {}
    
    for event in correlation_timeline:
        log_messages = event.get('log_messages', '')
        if log_messages:
            # Clean and normalize log messages
            cleaned_msg = log_messages.strip()
            if len(cleaned_msg) > 50:  # Only process substantial messages
                # Create a pattern key based on common elements
                pattern_key = cleaned_msg[:100]  # Use first 100 chars as pattern
                if pattern_key not in log_patterns:
                    log_patterns[pattern_key] = {
                        'message': cleaned_msg,
                        'count': 1,
                        'services': [event.get('service_name', 'Unknown')]
                    }
                else:
                    log_patterns[pattern_key]['count'] += 1
                    if event.get('service_name', 'Unknown') not in log_patterns[pattern_key]['services']:
                        log_patterns[pattern_key]['services'].append(event.get('service_name', 'Unknown'))
    
    # Return consolidated logs
    consolidated = []
    for pattern_key, data in log_patterns.items():
        if data['count'] > 1:  # Only include repeated patterns
            consolidated.append({
                'message': data['message'],
                'count': data['count'],
                'services': data['services'],
                'trace_ids': ['N/A']  # Placeholder since we don't have trace IDs in this context
            })
    
    return consolidated

def get_event_related_logs(event, all_log_meta):
    """Retrieve related logs for a specific event based on trace_id and span_id."""
    trace_id = event.get('trace_id')
    span_id = event.get('span_id')
    
    if not trace_id or not span_id:
        return []
    
    # Find all logs for this specific trace_id and span_id
    related_logs = [
        log for log in all_log_meta
        if log.get("trace_id") == trace_id and log.get("span_id") == span_id
    ]
    
    # Sort logs by timestamp
    related_logs.sort(key=lambda x: x.get("timestamp"))
    
    return related_logs

def build_llm_prompt(card, corr_df):
    # Compose summary prompt
    error_msgs = "\n".join(corr_df["log_messages"].dropna().head(5))
    prompt = f"""
You are an expert Site Reliability Engineer. Here is an incident card from a production system, followed by correlation data from traces/logs.

Incident Card:
{json.dumps(card, indent=2)}

Top Error Logs:
{error_msgs}

Sample Span/Tag Data:
{corr_df[['operation_name','span_start_time','duration','tags','status_code']].head(3).to_json()}

Please write an RCA summary answering WHO, WHAT, WHERE, WHEN, WHY, and suggest next steps. 
Structure your answer with:
1. Incident Summary
2. Impact
3. Root Cause
4. Resolution
5. Timeline
6. Error Patterns / Log Insights
Keep it concise and factual.
"""
    return prompt

def run_window(window_start_dt, window_end_dt):
    start_epoch = to_epoch(window_start_dt)
    end_epoch = to_epoch(window_end_dt)
    start_str = window_start_dt.strftime("%Y-%m-%d %H:%M:%S IST")
    end_str = window_end_dt.strftime("%Y-%m-%d %H:%M:%S IST")
    print(f"\n[Cycle] Fetching 5xx error metrics for {len(TARGET_SERVICES)} UNSET environment services from {start_str} to {end_str} (IST)")

    error_cards = fetch_error_metrics(start_epoch, end_epoch, start_str, end_str)
    print(f"Found {len(error_cards)} error cards.\n")

    for idx, card in enumerate(error_cards, 1):
        card_dir = os.path.join(OUTPUT_ROOT, f"error_{idx}_{start_str.replace(' ','_').replace(':','')}")
        os.makedirs(card_dir, exist_ok=True)

        save_json(card, os.path.join(card_dir, "error_card.json"))

        # Step 1: Fetch trace bundle using card filters
        trace_url = build_trace_search_url(card, window_start_dt, window_end_dt)
        trace_bundle = fetch_trace_bundle(trace_url)
        save_json(trace_bundle, os.path.join(card_dir, "error_trace_bundle.json"))
        trace_ids_hex = extract_unique_trace_ids_hex(trace_bundle)

        # Step 2: Fetch full trace details and filter spans
        all_span_meta = []
        all_log_meta = []

        for tid in trace_ids_hex:
            trace_json_path = os.path.join(card_dir, f"{tid}.json")
            trace_data = fetch_full_trace(tid, start_epoch, end_epoch)
            save_json(trace_data, trace_json_path)

            spans = parse_span_metadata(trace_data)

            # Filter spans using improved error detection
            error_spans = []
            for s in spans:
                tags = s.get("tags", {})
                if is_error_span(tags):
                    error_spans.append(s)

            if error_spans:
                logs_json_path = os.path.join(card_dir, f"{tid}_logs.json")
                logs = fetch_logs(tid, start_epoch, end_epoch)
                save_json(logs, logs_json_path)
                log_meta = parse_log_metadata(logs)
                all_log_meta.extend(log_meta)
                all_span_meta.extend(error_spans)

        if not all_span_meta:
            print(f"[✘] Skipping card {idx} — No error spans found.\n")
            continue

        # Step 3: Correlation Table
        correlation_summary, correlation_timeline = build_correlation_timeline(card, all_span_meta, all_log_meta, card_dir)

        # Step 4: Generate Detailed RCA using Cursor as LLM
        rca_summary = generate_detailed_rca(card, correlation_timeline, all_span_meta, all_log_meta)
        
        # Save detailed RCA report to file
        with open(os.path.join(card_dir, "detailed_rca.txt"), "w", encoding="utf-8") as f:
            f.write(rca_summary)
        print(f"[✓] Advanced NLP RCA report saved: {os.path.join(card_dir, 'detailed_rca.txt')}")

        # Step 5: Create Simple Error Spike Chart
        img_b64 = create_simple_error_chart(card)

        # Step 6: Extract first/last times
        first_time, last_time = get_first_last_times(all_log_meta, all_span_meta)

        # Step 7: Extract comprehensive evidence and top tags
        evidence_data = extract_comprehensive_evidence(all_span_meta, all_log_meta, card)
        tags = extract_top_tags(all_span_meta)

        # Step 8: Google Chat alert with enhanced data
        timeline_csv_path = os.path.join(card_dir, "correlation_timeline.csv")
        send_to_google_chat(card, card_dir, first_time, last_time, tags, timeline_csv_path, img_b64, rca_summary)

def get_last_processed_time():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                return int(f.read().strip())
            except:
                return None
    return None

def save_last_processed_time(epoch_ts):
    with open(STATE_FILE, "w") as f:
        f.write(str(epoch_ts))

def main_loop():
    print("[START] Comprehensive Error RCA System - Monitoring UNSET environment services for 5xx errors")
    print(f"[INFO] Target services: {', '.join(TARGET_SERVICES[:5])}... and {len(TARGET_SERVICES)-5} more")
    
    while True:
        try:
            now = datetime.now(tz=IST)
            
            # Always fetch the most recent time window (last 5 minutes)
            start_dt = now - timedelta(seconds=WINDOW_SIZE)
            end_dt = now

            print(f"\n[START] Processing from {start_dt} to {end_dt}")
            run_window(start_dt, end_dt)

            # Save end time as last processed
            save_last_processed_time(to_epoch(end_dt))
            
            # Wait for next cycle (5 minutes)
            print(f"[WAIT] Waiting 5 minutes until next cycle...")
            time.sleep(WINDOW_SIZE)
            
        except KeyboardInterrupt:
            print("\n[STOP] Received interrupt signal, shutting down gracefully...")
            break
        except Exception as e:
            print(f"[ERROR] Unexpected error in main loop: {e}")
            print("[WAIT] Waiting 60 seconds before retrying...")
            time.sleep(60)

if __name__ == "__main__":
    main_loop() 
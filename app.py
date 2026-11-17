from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import plotly.express as px
import streamlit as st

from backend_adapter import BackendUnavailable, create_backend, load_spec, normalize_registers, require_method

st.set_page_config(
    page_title="VFD Fieldbus Test Bench",
    page_icon="⌁",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --vfd-cyan:#48d7e8; --vfd-ink:#0b1013; --vfd-panel:#11191e; --vfd-panel-2:#151f24; --vfd-line:#26353b; --vfd-copy:#e4edf0; --vfd-muted:#86969d; --vfd-green:#68d49a; --vfd-amber:#e3b968; --vfd-red:#ef7777; }
html, body, [class*="css"] { font-family:'Manrope',sans-serif; }
.stApp { background:var(--vfd-ink); color:var(--vfd-copy); }
[data-testid="stHeader"] { background:transparent; }
[data-testid="stSidebar"] { background:#0e1519; border-right:1px solid var(--vfd-line); }
[data-testid="stSidebar"] > div:first-child { padding-top:1.3rem; }
.block-container { padding-top:1.8rem; padding-bottom:2.4rem; max-width:1600px; }
.brand { display:flex; align-items:center; gap:.8rem; padding:.25rem .2rem 1.35rem; border-bottom:1px solid var(--vfd-line); margin-bottom:1.2rem; }
.brand-mark { width:2.65rem;height:2.65rem; display:grid;place-items:center; border:1px solid #347b85; color:var(--vfd-cyan); font-family:'DM Mono',monospace; font-size:1.3rem; background:#102329; }
.brand-title { font-weight:800; font-size:.91rem; line-height:1.25; }
.brand-sub { color:var(--vfd-muted); font-size:.68rem; margin-top:.28rem; font-family:'DM Mono',monospace; }
.page-kicker { color:var(--vfd-cyan); font-family:'DM Mono',monospace; font-size:.68rem; letter-spacing:.09em; text-transform:uppercase; margin-bottom:.35rem; }
h1, h2, h3 { color:var(--vfd-copy)!important; }
h1 { font-size:1.8rem!important; font-weight:700!important; margin-bottom:.18rem!important; }
.page-subtitle { color:var(--vfd-muted); font-size:.88rem; margin-bottom:1.3rem; }
.topline { display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:.65rem; padding:.8rem 1rem; border:1px solid var(--vfd-line); background:#0e161a; margin:0 0 1.35rem; }
.topline-group { display:flex; flex-wrap:wrap; gap:.5rem 1rem; align-items:center; }
.chip { display:inline-flex; align-items:center; gap:.42rem; color:#bac9ce; font-family:'DM Mono',monospace; font-size:.68rem; }
.dot { width:.46rem;height:.46rem;border-radius:50%;display:inline-block;background:var(--vfd-amber); }
.dot-ok { background:var(--vfd-green); box-shadow:0 0 9px #68d49a44; }
.dot-off { background:#708087; }
.section-label { color:var(--vfd-muted); font-family:'DM Mono',monospace; text-transform:uppercase; font-size:.68rem; margin:.25rem 0 .7rem; }
.metric-wrap { border:1px solid var(--vfd-line); background:var(--vfd-panel); padding:.8rem .95rem; min-height:6.25rem; }
[data-testid="stMetricLabel"] { color:var(--vfd-muted)!important; font-family:'DM Mono',monospace; font-size:.68rem!important; }
[data-testid="stMetricValue"] { color:var(--vfd-copy)!important; font-family:'DM Mono',monospace; font-size:1.28rem!important; }
.surface { border:1px solid var(--vfd-line); background:var(--vfd-panel); padding:1rem 1.05rem; margin:.2rem 0 .95rem; }
.surface-title { font-size:.88rem; font-weight:700; color:var(--vfd-copy); margin-bottom:.2rem; }
.surface-note { font-size:.75rem; color:var(--vfd-muted); }
.empty-state { border:1px dashed #35464d; background:#10181c; color:var(--vfd-muted); padding:1.15rem; font-size:.82rem; line-height:1.6; }
.warning-band { border-left:3px solid var(--vfd-amber); background:#211d15; color:#dfc798; padding:.78rem 1rem; font-size:.8rem; margin:.65rem 0 1rem; }
.status-ok { color:var(--vfd-green); } .status-warn { color:var(--vfd-amber); } .status-bad { color:var(--vfd-red); }
code, .stCode { font-family:'DM Mono',monospace!important; }
[data-testid="stDataFrame"] { border:1px solid var(--vfd-line); }
.stButton > button, [data-testid="stFormSubmitButton"] > button { border-radius:2px; font-weight:700; min-height:2.55rem; }
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primary"] { background:#43c9d9; color:#071114; border:1px solid #43c9d9; }
.stButton > button[kind="secondary"], [data-testid="stFormSubmitButton"] > button[kind="secondary"] { background:#151f24; color:var(--vfd-copy); border:1px solid var(--vfd-line); }
input, textarea, [data-baseweb="select"] > div { border-radius:2px!important; }
hr { border-color:var(--vfd-line)!important; }
@media (max-width: 700px) { .block-container { padding:1rem .8rem 2rem; } h1 { font-size:1.45rem!important; } .topline { align-items:flex-start; } }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

PAGES = [
    "System Overview", "VFD Simulator", "Register Monitor", "Modbus Console",
    "Test Execution", "AI Test Generator", "Traffic Analytics", "C++ RTU Diagnostics", "System Information",
]


def get_backend() -> Any | None:
    if "backend_instance" not in st.session_state:
        try:
            st.session_state.backend_instance = create_backend()
            st.session_state.backend_error = ""
        except BackendUnavailable as exc:
            st.session_state.backend_instance = None
            st.session_state.backend_error = str(exc)
    return st.session_state.backend_instance


def call_backend(method_name: str, *args: Any, **kwargs: Any) -> Any:
    backend = get_backend()
    if backend is None:
        raise BackendUnavailable(st.session_state.get("backend_error", "Backend unavailable."))
    return require_method(backend, method_name)(*args, **kwargs)


def load_current_spec(uploaded_file: Any | None = None) -> list[dict[str, Any]]:
    if uploaded_file is not None:
        try:
            return normalize_registers(json.loads(uploaded_file.getvalue().decode("utf-8")))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"Could not parse the uploaded JSON specification: {exc}") from exc
    try:
        return load_spec()
    except ValueError as exc:
        st.error(str(exc))
        return []


def render_title(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(f'<div class="page-kicker">{kicker}</div><h1>{title}</h1><div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def section(title: str) -> None:
    st.markdown(f'<div class="section-label">{title}</div>', unsafe_allow_html=True)


def empty(message: str) -> None:
    st.markdown(f'<div class="empty-state">{message}</div>', unsafe_allow_html=True)


def result_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {"result": value}


def display_backend_result(value: Any) -> None:
    data = result_dict(value)
    st.json(data, expanded=True)


def no_data(label: str) -> None:
    empty(f"No {label} returned by the connected backend yet. Charts and metrics appear only after real project data is supplied.")


def render_overview() -> None:
    render_title("CONTROL ROOM / 01", "System overview", "VFD Fieldbus Test Bench · protocol diagnostics workspace")
    backend = get_backend()
    status: dict[str, Any] = {}
    if backend is not None:
        try:
            status = result_dict(require_method(backend, "simulator_status")())
        except BackendUnavailable:
            pass
        except Exception as exc:
            st.warning(f"Simulator status could not be read: {exc}")
    connected = status.get("connected") is True
    cols = st.columns(4)
    labels = [
        ("SIMULATOR", "Connected" if connected else "Unavailable"),
        ("TCP ENDPOINT", status.get("endpoint", "—")),
        ("LATEST TEST SUITE", status.get("latest_test_result", "—")),
        ("GENERATED CASES", status.get("generated_test_count", "—")),
    ]
    for col, (label, value) in zip(cols, labels):
        with col:
            st.markdown('<div class="metric-wrap">', unsafe_allow_html=True)
            st.metric(label, str(value))
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="warning-band">Software simulation only — no physical VFD connected.</div>', unsafe_allow_html=True)
    section("OPERATING CONTEXT")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="surface"><div class="surface-title">Protocol</div><div class="surface-note">MODBUS TCP · FC03 / FC04 / FC06 / FC16</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="surface"><div class="surface-title">Operating state</div><div class="surface-note">{status.get("state", "Not reported by backend")}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="surface"><div class="surface-title">Anomaly detection</div><div class="surface-note">{status.get("anomaly_status", "No model result reported")}</div></div>', unsafe_allow_html=True)

    section("LIVE MONITORING")
    traffic = None
    if backend is not None:
        try:
            traffic = result_dict(require_method(backend, "traffic_data")())
        except (BackendUnavailable, Exception):
            traffic = None
    left, right = st.columns(2)
    chart_specs = [("frequency", "Output frequency", left), ("latency", "Communication latency", right)]
    for key, title, col in chart_specs:
        with col:
            st.markdown(f'<div class="surface-title">{title}</div>', unsafe_allow_html=True)
            series = traffic.get(key) if traffic else None
            if isinstance(series, list) and series:
                st.plotly_chart(px.line(series, x="timestamp", y="value", title=None, template="plotly_dark"), use_container_width=True)
            else:
                no_data(title.lower())
    section("REGISTER SNAPSHOT")
    spec = load_current_spec()
    if spec:
        st.dataframe([{"Address": r["address"], "Register": r["name"], "Access": r["access"], "Value": "—"} for r in spec[:8]], hide_index=True, use_container_width=True)
        st.caption("Definitions loaded from the register JSON specification. Values require the connected backend.")
    else:
        empty("No register specification found. Set VFD_REGISTER_SPEC or upload the existing JSON specification in Register Monitor.")
    section("RECENT ACTIVITY")
    events = status.get("recent_activity") if status else None
    if isinstance(events, list) and events:
        st.dataframe(events, hide_index=True, use_container_width=True)
    else:
        no_data("activity events")


def render_simulator() -> None:
    render_title("SIMULATION / 02", "VFD simulator", "Monitor the software simulator through your existing project interface.")
    st.markdown('<div class="warning-band">Software simulation only — no physical VFD connected.</div>', unsafe_allow_html=True)
    status = None
    try:
        status = result_dict(call_backend("simulator_status"))
    except BackendUnavailable as exc:
        st.info(str(exc))
    except Exception as exc:
        st.error(f"Simulator status request failed: {exc}")
    cols = st.columns(4)
    fields = [("CONNECTION", "Connected" if status and status.get("connected") is True else "—"),
              ("OPERATING STATE", status.get("state", "—") if status else "—"),
              ("OUTPUT FREQUENCY", status.get("output_frequency", "—") if status else "—"),
              ("FAULT STATE", status.get("fault", "—") if status else "—")]
    for col, (label, value) in zip(cols, fields):
        with col:
            st.markdown('<div class="metric-wrap">', unsafe_allow_html=True); st.metric(label, str(value)); st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="surface"><div class="surface-title">Control availability</div><div class="surface-note">Start, stop, and reset controls are shown only when the adapter exposes the matching existing simulator operation.</div></div>', unsafe_allow_html=True)
    actions = [("Start simulator", "start_simulator"), ("Stop simulator", "stop_simulator"), ("Reset simulator", "reset_simulator")]
    cols = st.columns(3)
    for col, (label, method) in zip(cols, actions):
        with col:
            enabled = get_backend() is not None and callable(getattr(get_backend(), method, None))
            if st.button(label, disabled=not enabled, key=f"sim_{method}"):
                try:
                    display_backend_result(call_backend(method))
                except Exception as exc:
                    st.error(f"{label} failed: {exc}")
    if not any(get_backend() is not None and callable(getattr(get_backend(), method, None)) for _, method in actions):
        st.caption("Controls remain disabled until your adapter connects them to supported simulator operations.")


def render_registers() -> None:
    render_title("REGISTERS / 03", "Register monitor", "Register definitions are read from your JSON specification; values come from the connected backend.")
    uploaded = st.file_uploader("Load register specification", type=["json"], key="spec_upload")
    spec = load_current_spec(uploaded)
    if not spec:
        empty("Choose your existing register specification JSON, or set VFD_REGISTER_SPEC to its local path. No register definitions are invented here.")
        return
    st.caption(f"{len(spec)} register definitions loaded · source: uploaded JSON" if uploaded else f"{len(spec)} register definitions loaded · source: {os.getenv('VFD_REGISTER_SPEC', 'register_spec.json')}")
    st.dataframe([{"Address": r["address"], "Name": r["name"], "Access": r["access"], "Valid range": f"{r['minimum'] if r['minimum'] is not None else '—'} … {r['maximum'] if r['maximum'] is not None else '—'}", "Description": r["description"]} for r in spec], hide_index=True, use_container_width=True)
    st.divider()
    selected_address = st.selectbox("Register", [r["address"] for r in spec], format_func=lambda address: next(f"{r['address']} · {r['name']} ({r['access']})" for r in spec if r["address"] == address))
    register = next(r for r in spec if r["address"] == selected_address)
    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("Read register", type="primary", use_container_width=True, key="read_register"):
            try:
                value = call_backend("read_register", register["address"])
                st.session_state[f"reg_value_{register['address']}"] = value
                st.success("Read completed by the connected backend.")
            except Exception as exc:
                st.error(f"Register read unavailable: {exc}")
        current = st.session_state.get(f"reg_value_{register['address']}", "Not read")
        st.metric("CURRENT VALUE", str(current))
    with c2:
        if register["access"] == "RW":
            lower = register["minimum"] if isinstance(register["minimum"], (int, float)) else 0
            upper = register["maximum"] if isinstance(register["maximum"], (int, float)) else 65535
            if lower > upper:
                st.error("The JSON specification has an invalid range for this register.")
            else:
                with st.form("write_register_form"):
                    proposed = st.number_input("Write value", min_value=int(lower), max_value=int(upper), value=int(lower), step=1)
                    submitted = st.form_submit_button("Write register", type="primary", disabled=get_backend() is None, use_container_width=True)
                if submitted:
                    try:
                        result = call_backend("write_register", register["address"], int(proposed))
                        st.success("Write response returned by the connected backend.")
                        display_backend_result(result)
                    except Exception as exc:
                        st.error(f"Register write failed: {exc}")
                if get_backend() is None:
                    st.caption("Writes are disabled until the existing Modbus client is connected.")
        else:
            st.info("This register is read-only according to the JSON specification; writing is disabled.")


def render_console() -> None:
    render_title("PROTOCOL / 04", "Modbus TCP console", "Build a request and inspect the exact response returned by your Modbus client.")
    functions = ["FC03", "FC04", "FC06", "FC16"]
    with st.form("modbus_console"):
        fc = st.selectbox("Function code", functions)
        address = st.number_input("Register address", min_value=0, max_value=65535, value=0, step=1)
        quantity_or_value = st.number_input("Quantity (FC03/FC04) or write value (FC06/FC16)", min_value=0, max_value=65535, value=1, step=1)
        submitted = st.form_submit_button("Send request", type="primary", disabled=get_backend() is None)
    if get_backend() is None:
        st.info("Modbus requests are unavailable until VFD_BACKEND_ADAPTER connects this console to the existing client.")
    if submitted:
        try:
            response = call_backend("modbus_request", function_code=fc, address=int(address), quantity_or_value=int(quantity_or_value))
            data = result_dict(response)
            st.success("Response received from the connected Modbus client.")
            for label, key in [("TRANSACTION ID", "transaction_id"), ("FUNCTION CODE", "function_code"), ("LATENCY", "latency_ms"), ("RESPONSE LENGTH", "response_length"), ("EXCEPTION CODE", "exception_code")]:
                st.metric(label, str(data.get(key, "—")))
            st.subheader("Transaction details")
            st.json(data, expanded=True)
            st.session_state.setdefault("transaction_log", []).insert(0, data)
        except Exception as exc:
            st.error(f"Request failed: {exc}")
    section("TRANSACTION LOG")
    transactions = st.session_state.get("transaction_log", [])
    if transactions:
        for index, transaction in enumerate(transactions):
            with st.expander(f"{transaction.get('timestamp', 'Request')} · {transaction.get('function_code', 'FC')} · address {transaction.get('address', '—')}"):
                st.json(transaction, expanded=True)
    else:
        empty("No requests have been recorded in this session.")


def render_tests() -> None:
    render_title("VALIDATION / 05", "Test execution", "Run the existing test suites without replacing or simulating their results.")
    st.markdown('<div class="warning-band">Test results appear only after the connected project test process returns them.</div>', unsafe_allow_html=True)
    suite = st.selectbox("Test suite", ["Python pytest", "C++ RTU", "CRC differential"])
    mode = st.radio("Mode", ["Normal validation", "Bug-injection evaluation"], horizontal=True)
    if st.button("Run selected suite", type="primary", disabled=get_backend() is None):
        try:
            with st.spinner("Waiting for the project test runner…"):
                result = call_backend("run_tests", suite=suite, mode=mode)
            st.success("Test process returned a result.")
            display_backend_result(result)
        except Exception as exc:
            st.error(f"Test execution unavailable or failed: {exc}")
    if get_backend() is None:
        st.info("No test results are displayed. Configure an adapter that invokes your existing pytest/C++ test commands.")
        st.code("pytest -q\n# Run the C++ and CRC commands already defined by your project", language="bash")


def render_generator() -> None:
    render_title("TEST DESIGN / 06", "AI test generator", "Create boundary cases from the project specification and let its oracle decide expected outcomes.")
    st.markdown('<div class="surface"><div class="surface-title">Oracle authority</div><div class="surface-note">The LLM proposes test inputs. The specification-based oracle determines the expected result.</div></div>', unsafe_allow_html=True)
    spec = load_current_spec()
    if not spec:
        empty("Load the register JSON in Register Monitor and point VFD_REGISTER_SPEC to the same file before generating cases.")
        return
    selected = st.selectbox("Register", [r["address"] for r in spec], format_func=lambda address: next(f"{r['address']} · {r['name']}" for r in spec if r["address"] == address))
    source = st.radio("Input source", ["Deterministic boundaries", "Optional LLM proposals"], horizontal=True)
    if st.button("Generate test cases", type="primary"):
        try:
            cases = call_backend("generate_tests", address=int(selected), source="llm" if source.startswith("Optional") else "deterministic")
            if not isinstance(cases, list):
                raise ValueError("generate_tests() must return a list of case dictionaries.")
            st.session_state.generated_cases = cases
            st.success(f"{len(cases)} cases returned by the project generator.")
        except Exception as exc:
            st.error(f"Test generation unavailable: {exc}")
    cases = st.session_state.get("generated_cases")
    if cases:
        st.dataframe(cases, hide_index=True, use_container_width=True)
    elif get_backend() is None:
        st.info("Connect the existing deterministic generator to enable boundary cases. LLM proposals remain optional; no key is requested or displayed here.")
    else:
        empty("Generate cases to display the backend's actual outputs.")


def render_analytics() -> None:
    render_title("TRAFFIC / 07", "Traffic analytics", "LOF anomaly monitoring for simulated Modbus traffic.")
    st.markdown('<div class="surface"><div class="surface-title">Model context</div><div class="surface-note">The anomaly detector analyses simulated Modbus traffic. Predictions and charts below require outputs from the existing model.</div></div>', unsafe_allow_html=True)
    try:
        data = result_dict(call_backend("traffic_analytics"))
    except Exception as exc:
        st.info(f"Traffic analytics unavailable: {exc}")
        return
    metrics = [("MEAN LATENCY", "mean_latency_ms"), ("P95 LATENCY", "p95_latency_ms"), ("LATENCY STD DEV", "latency_std_ms"), ("EXCEPTION RATE", "exception_rate"), ("MEAN RESPONSE LENGTH", "mean_response_length")]
    cols = st.columns(len(metrics))
    for col, (label, key) in zip(cols, metrics):
        with col:
            st.markdown('<div class="metric-wrap">', unsafe_allow_html=True); st.metric(label, str(data.get(key, "—"))); st.markdown('</div>', unsafe_allow_html=True)
    for key, title in [("latency_series", "Latency over time"), ("anomaly_predictions", "Healthy versus anomalous traffic"), ("feature_distributions", "Feature distributions")]:
        section(title.upper())
        series = data.get(key)
        if isinstance(series, list) and series:
            st.dataframe(series, hide_index=True, use_container_width=True)
        else:
            no_data(title.lower())
    st.markdown("**Model output**")
    st.json(data.get("predictions", []), expanded=False)


def parse_hex_bytes(value: str) -> bytes:
    cleaned = value.replace("0x", "").replace(",", " ").replace("-", " ")
    try:
        return bytes.fromhex(cleaned)
    except ValueError as exc:
        raise ValueError("Enter hexadecimal bytes separated by spaces, for example: 01 03 00 00") from exc


def render_rtu() -> None:
    render_title("FRAME TOOLS / 08", "C++ RTU diagnostics", "Run CRC and frame checks through the existing C++17 protocol library.")
    st.markdown('<div class="surface"><div class="surface-title">Execution source</div><div class="surface-note">This screen is an interface only. CRC results are never calculated in the browser or presented as C++ output unless the adapter returns them.</div></div>', unsafe_allow_html=True)
    frame = st.text_input("RTU frame bytes (hex)", placeholder="01 03 00 00 00 01")
    action = st.radio("Operation", ["CRC16/MODBUS", "Validate frame", "Python ↔ C++ comparison"], horizontal=True)
    if st.button("Run diagnostic", type="primary"):
        try:
            frame_bytes = parse_hex_bytes(frame)
            method = {"CRC16/MODBUS": "calculate_crc", "Validate frame": "validate_frame", "Python ↔ C++ comparison": "compare_crc"}[action]
            result = call_backend(method, frame_bytes)
            st.success("Diagnostic result returned by the connected project library.")
            display_backend_result(result)
        except Exception as exc:
            st.error(f"Diagnostic unavailable: {exc}")


def render_system_info() -> None:
    render_title("ENVIRONMENT / 09", "System information", "Local application status and integration settings.")
    python_version = sys.version.split()[0]
    values = [("PYTHON", python_version), ("BACKEND ADAPTER", os.getenv("VFD_BACKEND_ADAPTER", "Not configured")), ("REGISTER SPEC", os.getenv("VFD_REGISTER_SPEC", "register_spec.json")), ("EXECUTION MODE", "Software simulation")]
    cols = st.columns(2)
    for i, (label, value) in enumerate(values):
        with cols[i % 2]:
            st.markdown('<div class="metric-wrap">', unsafe_allow_html=True); st.metric(label, str(value)); st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="warning-band">Software simulation only — no physical VFD connected.</div>', unsafe_allow_html=True)
    st.caption("Backend connection status: " + ("configured" if get_backend() is not None else "not connected"))


with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-mark">⌁</div><div><div class="brand-title">VFD FIELDBUS<br>TEST BENCH</div><div class="brand-sub">INDUSTRIAL PROTOCOL LAB</div></div></div>', unsafe_allow_html=True)
    page = st.radio("WORKSPACE", PAGES, label_visibility="collapsed", key="active_page")
    st.divider()
    st.markdown('<div class="chip"><span class="dot dot-off"></span>SIMULATION ENVIRONMENT</div>', unsafe_allow_html=True)
    st.markdown('<div class="chip" style="margin-top:.55rem"><span class="dot dot-off"></span>NO PHYSICAL VFD</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub" style="margin-top:1.2rem">MODBUS TCP · LOCAL WORKSPACE</div>', unsafe_allow_html=True)

backend = get_backend()
status_for_header = None
if backend is not None:
    try:
        status_for_header = result_dict(require_method(backend, "simulator_status")())
    except Exception:
        status_for_header = None
is_connected = status_for_header is not None and status_for_header.get("connected") is True
st.markdown(
    '<div class="topline"><div class="topline-group">'
    f'<span class="chip"><span class="dot {"dot-ok" if is_connected else "dot-off"}"></span>{"SIMULATOR CONNECTED" if is_connected else "SIMULATOR STATUS UNAVAILABLE"}</span>'
    '<span class="chip">MODBUS TCP</span><span class="chip">SOFTWARE SIMULATION</span>'
    '</div><span class="chip">UTC SESSION · ' + datetime.now(timezone.utc).strftime("%H:%M:%S") + '</span></div>',
    unsafe_allow_html=True,
)

renderers = {
    "System Overview": render_overview,
    "VFD Simulator": render_simulator,
    "Register Monitor": render_registers,
    "Modbus Console": render_console,
    "Test Execution": render_tests,
    "AI Test Generator": render_generator,
    "Traffic Analytics": render_analytics,
    "C++ RTU Diagnostics": render_rtu,
    "System Information": render_system_info,
}
renderers[page]()

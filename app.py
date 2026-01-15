import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- IMPORT MODULES ---
try:
    import data_utils as db
    import connection_design as conn
    import calculation_report as rep
except ImportError as e:
    st.error(f"⚠️ Missing files: {e}")
    st.stop()

# ==========================================
# 1. PAGE SETUP
# ==========================================
st.set_page_config(page_title="Beam Insight V18", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Roboto+Mono:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
    .detail-card {
        background: white; border-radius: 12px; padding: 20px;
        border: 1px solid #e5e7eb; border-top: 6px solid #2563eb;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
    .status-badge {
        padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 12px;
        float: right; text-transform: uppercase;
    }
    .pass { background-color: #dcfce7; color: #166534; }
    .fail { background-color: #fee2e2; color: #991b1b; }
    .highlight-card { 
        background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%);
        padding: 25px; border-radius: 20px; border-left: 8px solid #2563eb; 
        box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08); margin-bottom: 25px; border: 1px solid #e5e7eb;
    }
    .big-num { color: #1e40af; font-size: 42px; font-weight: 800; font-family: 'Roboto Mono', monospace; }
    .sub-text { color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SIDEBAR
# ==========================================
with st.sidebar:
    st.title("🏗️ Beam Insight V18")
    method = st.radio("Design Method", ["ASD (Allowable Stress)", "LRFD (Limit State)"])
    is_lrfd = "LRFD" in method
    
    with st.expander("📋 Project Info"):
        proj_name = st.text_input("Project Name", "New Project")
        eng_name = st.text_input("Engineer Name", "Engineer")

    st.subheader("🛠️ Section Selection")
    sec_name = st.selectbox("Steel Section", list(db.STEEL_DB.keys()), index=11)
    p = db.STEEL_DB[sec_name]
    
    fy = st.number_input("Fy (kg/cm²)", value=2500)
    E_mod = 2.04e6 
    
    user_span = st.number_input("Span Length (m)", min_value=1.0, value=6.0, step=0.5)
    defl_ratio = st.selectbox("Deflection Limit", ["L/200", "L/240", "L/300", "L/360", "L/400"], index=3)
    defl_lim_val = int(defl_ratio.split("/")[1])

    design_mode = st.radio("Load Mode:", ["Automatic Max Capacity", "Manual Load Input"])
    if design_mode == "Manual Load Input":
        user_load_input = st.number_input("Custom Load (kg/m)", value=1000)

    st.subheader("🔩 Connection Type")
    conn_type = st.selectbox("Type", ["Fin Plate (Single Shear)", "End Plate (Single Shear)", "Double Angle (Double Shear)"])

# ==========================================
# 3. CALCULATIONS (AISC 360-16 Verified)
# ==========================================
L_cm = user_span * 100
Ix, Zx = p['Ix'], p['Zx']
h_cm, tw_cm = p['h']/10, p['tw']/10
Aw = h_cm * tw_cm
w_self = p['w']

# Capacity Logic
if is_lrfd:
    M_cap = 0.90 * fy * Zx
    V_cap = 1.00 * 0.60 * fy * Aw
    label_load = "Factored Load (Wu)"
else:
    M_cap = (fy * Zx) / 1.67
    V_cap = (0.60 * fy * Aw) / 1.50
    label_load = "Safe Load (w)"

def calculate_limits(L_m):
    L_c = L_m * 100
    w_v = (2 * V_cap / L_c) * 100 
    w_m = (8 * M_cap / (L_c**2)) * 100 
    w_d = ((L_c/defl_lim_val) * 384 * E_mod * Ix) / (5 * (L_c**4)) * 100 
    w_gov = min(w_v, w_m, w_d)
    cause = "Shear" if w_gov == w_v else ("Moment" if w_gov == w_m else "Deflection")
    return w_v, w_m, w_d, w_gov, cause

w_max_shear, w_max_moment, w_max_defl, w_max_gov, user_cause = calculate_limits(user_span)

# Load Selection Logic
if design_mode == "Automatic Max Capacity":
    display_load = w_max_gov - w_self
    w_check_total = w_max_gov
else:
    display_load = user_load_input
    w_check_total = user_load_input + w_self

# Actual Forces
v_act = (w_check_total/100) * L_cm / 2
m_act = (w_check_total/100) * (L_cm**2) / 8
d_act = (5 * (display_load/100) * (L_cm**4)) / (384 * E_mod * Ix)
d_all = L_cm / defl_lim_val

# Final Result Object (Fixed for Report)
is_pass = (v_act <= V_cap * 1.01) and (m_act <= M_cap * 1.01) and (d_act <= d_all * 1.01)
beam_res = {
    'pass': is_pass,
    'w_safe': display_load,
    'v_act': v_act, 'v_cap': V_cap, 'v_ratio': v_act / V_cap,
    'm_act': m_act / 100, 'm_cap': M_cap / 100, 'm_ratio': (m_act/100) / (M_cap/100),
    'd_act': d_act, 'd_all': d_all, 'd_ratio': d_act / d_all,
    'span': user_span
}

# ==========================================
# 4. UI RENDERING
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection Detail", "💾 Load Table", "📝 Report"])

with tab1:
    st.subheader(f"Engineering Analysis: {sec_name}")
    cause_color = "#dc2626" if user_cause == "Shear" else ("#d97706" if user_cause == "Moment" else "#059669")

    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><span class="sub-text">Max Allowed {label_load} (External)</span><br>
                <span class="big-num">{display_load:,.0f}</span> <span style="font-size:20px; color:#4b5563;">kg/m</span></div>
            <div style="text-align: right;"><span class="sub-text">Governing Limit</span><br>
                <span style="font-size: 22px; font-weight:bold; color:{cause_color}; background-color:{cause_color}15; padding: 8px 20px; border-radius:15px; border: 1px solid {cause_color}30;">{user_cause.upper()}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    def render_box(title, act, lim, ratio_label):
        ratio = act / lim
        status = "pass" if ratio <= 1.01 else "fail"
        color = "#10b981" if status == "pass" else "#ef4444"
        st.markdown(f"""
        <div class="detail-card" style="border-top-color: {color}">
            <span class="status-badge {status}">{status.upper()}</span>
            <h4 style="margin:0;">{title}</h4>
            <div style="margin-top:10px;">
                <small>Usage Ratio ({ratio_label}):</small>
                <div style="font-size:24px; font-weight:700; color:{color};">{ratio:.3f}</div>
                <small style="color:#6b7280;">Act: {act:,.1f} / Cap: {lim:,.1f}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: render_box("Shear Check", v_act, V_cap, "V/V_cap")
    with c2: render_box("Moment Check", m_act/100, M_cap/100, "M/M_cap")
    with c3: render_box("Deflection", d_act, d_all, "Δ/Δ_all")

    # Plot
    spans = np.linspace(2, 12, 100)
    env_y = [calculate_limits(s)[3] for s in spans]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans, y=env_y, name='Capacity Envelope', fill='tozeroy', line=dict(color='#1e40af')))
    fig.add_trace(go.Scatter(x=[user_span], y=[w_check_total], mode='markers', name='Design Point', marker=dict(color='red', size=10)))
    fig.update_layout(height=400, margin=dict(t=10, b=10, l=10, r=10), xaxis_title="Span (m)", yaxis_title="Total Load (kg/m)")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    conn_result = conn.render_connection_tab(v_act, method, is_lrfd, p, conn_type)

with tab3:
    df_tbl = pd.DataFrame([[s, calculate_limits(s)[3]-w_self, calculate_limits(s)[4]] for s in np.arange(2, 12.5, 0.5)], columns=["Span (m)", "Safe Load (kg/m)", "Limit By"])
    st.dataframe(df_tbl.style.format({"Span (m)": "{:.1f}", "Safe Load (kg/m)": "{:,.0f}"}), use_container_width=True)

with tab4:
    rep.render_report_tab({'name': proj_name, 'eng': eng_name, 'sec': sec_name, 'method': method}, beam_res, conn_result if 'conn_result' in locals() else {})

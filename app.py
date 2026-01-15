# app.py (V13.2 - Fully Integrated & Corrected Version)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- IMPORT MODULES ---
try:
    import connection_design as conn
    import report_generator as rep
except ImportError:
    st.warning("Warning: connection_design.py or report_generator.py not found. Please ensure files are in the same directory.")

# ==========================================
# 1. SETUP & STYLE (Engineering Professional)
# ==========================================
st.set_page_config(page_title="Beam Insight V13", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Roboto+Mono:wght@400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }

    /* --- Metric Card --- */
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

    /* --- Highlight Card --- */
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
# 2. FULL DATA (Steel Sections)
# ==========================================
steel_db = {
    "H 100x100x6x8":    {"h": 100, "b": 100, "tw": 6,   "tf": 8,   "Ix": 383,    "Zx": 76.5,  "w": 17.2},
    "H 125x125x6.5x9":  {"h": 125, "b": 125, "tw": 6.5, "tf": 9,   "Ix": 847,    "Zx": 136,   "w": 23.8},
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8,  "w": 14.0},
    "H 150x150x7x10":   {"h": 150, "b": 150, "tw": 7,   "tf": 10,  "Ix": 1640,   "Zx": 219,   "w": 31.5},
    "H 200x100x5.5x8":  {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "w": 21.3},
    "H 200x200x8x12":   {"h": 200, "b": 200, "tw": 8,   "tf": 12,  "Ix": 4720,   "Zx": 472,   "w": 49.9},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "w": 29.6},
    "H 250x250x9x14":   {"h": 250, "b": 250, "tw": 9,   "tf": 14,  "Ix": 10800,  "Zx": 867,   "w": 72.4},
    "H 300x150x6.5x9":  {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 300x300x10x15":  {"h": 300, "b": 300, "tw": 10,  "tf": 15,  "Ix": 20400,  "Zx": 1360,  "w": 94.0},
    "H 350x175x7x11":   {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "w": 49.6},
    "H 400x200x8x13":   {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 450x200x9x14":   {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "w": 76.0},
    "H 500x200x10x16":  {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
    "H 600x200x11x17":  {"h": 600, "b": 200, "tw": 11,  "tf": 17,  "Ix": 77600,  "Zx": 2590,  "w": 106},
}

with st.sidebar:
    st.title("🏗️ Beam Insight V13")
    st.divider()
    
    # --- 1. GLOBAL SETTINGS & LINKAGE ---
    method = st.radio("Method", ["ASD (Allowable Stress)", "LRFD (Limit State)"])
    # สร้างตัวแปร Boolean เพื่อส่งไปทุก Tab
    is_lrfd = True if "LRFD" in method else False
    
    st.subheader("🛠️ Material Grade")
    grade_opts = {"SS400 (Fy 2450)": 2450, "SM490 (Fy 3250)": 3250, "A36 (Fy 2500)": 2500, "Custom": 2400}
    grade_choice = st.selectbox("Steel Grade", list(grade_opts.keys()))
    fy = st.number_input("Fy (kg/cm²)", value=grade_opts[grade_choice])
    
    sec_name = st.selectbox("Steel Section", list(steel_db.keys()), index=11)
    user_span = st.number_input("Span Length (m)", min_value=1.0, value=6.0, step=0.5)
    defl_ratio = st.selectbox("Deflection Limit", ["L/300", "L/360", "L/400"], index=1)
    defl_lim_val = int(defl_ratio.split("/")[1])
    
    st.subheader("🔩 Connection Design")
    # ปรับชื่อตัวเลือกให้มีคำว่า "Double" และ "Beam to Beam" เพื่อให้ Logic ปลายทางทำงานถูก
    conn_type_options = [
        "Fin Plate (Single Shear) - Beam to Col",
        "End Plate (Single Shear) - Beam to Col",
        "Double Angle (Double Shear) - Beam to Col",
        "Fin Plate (Single Shear) - Beam to Beam"
    ]
    conn_type = st.selectbox("Connection Type", conn_type_options)
    
    bolt_grade_opts = ["A325 (High Strength)", "Grade 8.8 (Standard)", "A490 (Premium)"]
    bolt_grade = st.selectbox("Bolt Grade", bolt_grade_opts)
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
    
    design_mode = st.radio("Load for Connection:", ["Actual Load", "Fixed % Capacity"])
    target_pct = st.slider("Target Usage %", 50, 100, 75) if design_mode == "Fixed % Capacity" else None
    E_mod = 2.04e6 

# ==========================================
# 3. CORE CALCULATIONS
# ==========================================
p = steel_db[sec_name]
Aw = (p['h']/10) * (p['tw']/10) 
Ix, Zx = p['Ix'], p['Zx']

# --- CALCULATE CAPACITY BASED ON METHOD (ASD/LRFD) ---
if is_lrfd:
    M_cap = 0.90 * fy * Zx  # LRFD Factor
    V_cap = 1.00 * 0.6 * fy * Aw
    label_load = "Factored Load (Wu)"
else:
    M_cap = 0.60 * fy * Zx  # ASD Factor
    V_cap = 0.40 * fy * Aw
    label_load = "Safe Load (w)"

def get_capacity(L_m):
    L_cm = L_m * 100
    w_v = (2 * V_cap / L_cm) * 100 
    w_m = (8 * M_cap / (L_cm**2)) * 100 
    w_d = ((L_cm/defl_lim_val) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100 
    w_gov = min(w_v, w_m, w_d)
    cause = "Shear" if w_gov == w_v else ("Moment" if w_gov == w_m else "Deflection")
    return w_v, w_m, w_d, w_gov, cause

w_shear, w_moment, w_defl, user_safe_load, user_cause = get_capacity(user_span)

v_act = user_safe_load * user_span / 2
m_act = user_safe_load * user_span**2 / 8
d_act = (5 * (user_safe_load/100) * ((user_span*100)**4)) / (384 * E_mod * Ix)
d_all = (user_span*100) / defl_lim_val
V_design = v_act if design_mode == "Actual Load" else V_cap * (target_pct / 100)

# ==========================================
# 4. UI RENDERING
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection Detail", "💾 Load Table", "📝 Report"])

with tab1:
    st.subheader(f"Engineering Analysis: {sec_name} ({'LRFD' if is_lrfd else 'ASD'})")
    cause_color = "#dc2626" if user_cause == "Shear" else ("#d97706" if user_cause == "Moment" else "#059669")

    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><span class="sub-text">Maximum Allowed {label_load}</span><br>
                <span class="big-num">{user_safe_load:,.0f}</span> <span style="font-size:20px; color:#4b5563;">kg/m</span></div>
            <div style="text-align: right;"><span class="sub-text">Governing Limit</span><br>
                <span style="font-size: 22px; font-weight:bold; color:{cause_color}; background-color:{cause_color}15; padding: 8px 20px; border-radius:15px; border: 1px solid {cause_color}30;">{user_cause.upper()}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    def render_check_ratio_with_w(title, act, lim, ratio_label, eq_w, eq_act, eq_ratio):
        ratio = act / lim
        is_pass = ratio <= 1.01 
        status_class = "pass" if is_pass else "fail"
        border_color = "#10b981" if is_pass else "#ef4444"

        st.markdown(f"""
        <div class="detail-card" style="border-top-color: {border_color}">
            <span class="status-badge {status_class}">{'PASS' if is_pass else 'FAIL'}</span>
            <h4 style="margin:0; color:#374151;">{title}</h4>
            <div style="margin-top:10px;">
                <small style="color:#6b7280;">Usage Ratio ({ratio_label}):</small>
                <div style="font-size:24px; font-weight:700; color:{border_color};">{ratio:.3f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander(f"View {title} Step-by-Step Calculation"):
            st.info(f"**Step 1: Calculate Max Load (w) from {title}**")
            st.latex(eq_w)
            st.divider()
            st.info(f"**Step 2: Compare Actual Stress vs Capacity**")
            st.latex(eq_act)
            st.latex(eq_ratio)

    c1, c2, c3 = st.columns(3)
    L_cm_disp = user_span * 100
    
    with c1:
        render_check_ratio_with_w(
            "Shear Check", v_act, V_cap, "V/V_cap",
            fr"w_{{limit}} = \frac{{2 \cdot V_{{cap}}}}{{L}} = \frac{{2 \cdot {V_cap:,.0f}}}{{{L_cm_disp:,.0f}}} \cdot 100 = {w_shear:,.0f} \text{{ kg/m}}",
            fr"V_{{act}} = \frac{{w \cdot L}}{{2}} = \frac{{{user_safe_load:,.0f} \cdot {user_span}}}{{2}} = {v_act:,.0f} \text{{ kg}}",
            fr"Ratio = \frac{{{v_act:,.0f}}}{{{V_cap:,.0f}}} = {v_act/V_cap:.3f}"
        )
    with c2:
        render_check_ratio_with_w(
            "Moment Check", m_act, (M_cap/100), "M/M_cap",
            fr"w_{{limit}} = \frac{{8 \cdot M_{{cap}}}}{{L^2}} = \frac{{8 \cdot {M_cap:,.0f}}}{{{L_cm_disp:,.0f}^2}} \cdot 100 = {w_moment:,.0f} \text{{ kg/m}}",
            fr"M_{{act}} = \frac{{w \cdot L^2}}{{8}} = \frac{{{user_safe_load:,.0f} \cdot {user_span}^2}}{{8}} = {m_act:,.0f} \text{{ kg.m}}",
            fr"Ratio = \frac{{{m_act:,.0f}}}{{{M_cap/100:,.0f}}} = {m_act/(M_cap/100):.3f}"
        )
    with c3:
        render_check_ratio_with_w(
            "Deflection Check", d_act, d_all, "Δ/Δ_allow",
            fr"w_{{limit}} = \frac{{384 E I \Delta_{{all}}}}{{5 L^4}} = \frac{{384 \cdot 2.04 \cdot 10^6 \cdot {Ix} \cdot {d_all:.2f}}}{{5 \cdot {L_cm_disp:,.0f}^4}} \cdot 100 = {w_defl:,.0f} \text{{ kg/m}}",
            fr"\Delta_{{act}} = \frac{{5 w L^4}}{{384 E I}} = {d_act:.3f} \text{{ cm}}",
            fr"Ratio = \frac{{{d_act:.3f}}}{{{d_all:.3f}}} = {d_act/d_all:.3f}"
        )

    st.markdown("### Capacity Envelope Curve")
    spans = np.linspace(2, 12, 100)
    data_env = [get_capacity(s) for s in spans]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans, y=[d[0] for d in data_env], name='Shear Limit', line=dict(color='#ef4444', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=[d[1] for d in data_env], name='Moment Limit', line=dict(color='#f59e0b', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=[d[2] for d in data_env], name='Deflection Limit', line=dict(color='#3b82f6', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=[d[3] for d in data_env], name='Safe Envelope', fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.1)', line=dict(color='#1e40af', width=4)))
    fig.add_trace(go.Scatter(x=[user_span], y=[user_safe_load], mode='markers+text', name='Design Point', text=[f"  ({user_span}m, {user_safe_load:,.0f}kg/m)"], textposition="top right", marker=dict(color='red', size=12, symbol='diamond', line=dict(width=2, color='white'))))
    fig.update_layout(hovermode="x unified", height=450, margin=dict(t=20, b=20, l=20, r=20), plot_bgcolor='white')
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    try:
        # --- ส่งค่าเข้า Tab Connection (พร้อมตัวแปร Linkage ครบถ้วน) ---
        req_bolt, v_bolt = conn.render_connection_tab(
            V_design=V_design, 
            bolt_size=bolt_size, 
            method=method, 
            is_lrfd=is_lrfd,        # <--- ส่งสถานะ LRFD
            section_data=p, 
            conn_type=conn_type,    # <--- ส่งชื่อที่มีคำว่า Double/Single
            bolt_grade=bolt_grade
        )
    except Exception as e:
        st.error(f"⚠️ Error in Connection Tab: {e}")
        st.caption("Please check if connection_design.py is up to date.")

with tab3:
    st.subheader("Span-Load Reference Table")
    tbl_spans = np.arange(2.0, 12.5, 0.5)
    tbl_data = [get_capacity(s) for s in tbl_spans]
    df = pd.DataFrame({"Span (m)": tbl_spans, f"Max {label_load} (kg/m)": [d[3] for d in tbl_data], "Control Factor": [d[4] for d in tbl_data]})
    st.dataframe(df.style.format("{:,.0f}", subset=[f"Max {label_load} (kg/m)"]), use_container_width=True)

with tab4:
    # รวบรวมข้อมูลทั้งหมดส่งไปยัง report_generator
    full_res = {'w_safe': user_safe_load, 'cause': user_cause, 'v_cap': V_cap, 'v_act': v_act, 'm_cap': M_cap, 'm_act': m_act, 'd_all': d_all, 'd_act': d_act}
    bolt_data = {'size': bolt_size, 'qty': req_bolt if 'req_bolt' in locals() else 0, 'cap': v_bolt if 'v_bolt' in locals() else 0, 'type': conn_type, 'grade': bolt_grade}
    
    if 'rep' in locals():
        rep.render_report_tab(method, is_lrfd, sec_name, grade_choice, p, full_res, bolt_data)
    else:
        st.info("Report Generator module not loaded.")

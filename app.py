# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 0. SYSTEM PATCH
# ==========================================
_original_markdown = st.markdown
def _patched_markdown(body, unsafe_allow_html=False, **kwargs):
    return _original_markdown(body, unsafe_allow_html=True, **kwargs)
st.markdown = _patched_markdown

# ==========================================
# 1. IMPORT MODULES
# ==========================================
try:
    import steel_db             
    import connection_design    
    import report_generator     
except ImportError as e:
    st.error(f"⚠️ Modules missing: {e}")
    st.stop()

# ==========================================
# 2. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Beam Insight Hybrid", layout="wide", page_icon="🏗️")

if 'design_method' not in st.session_state:
    st.session_state.design_method = "LRFD (Limit State)"
if 'cal_success' not in st.session_state:
    st.session_state.cal_success = False

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Roboto+Mono:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
    
    .detail-card { background: white; border-radius: 12px; padding: 20px; border: 1px solid #e5e7eb; border-top: 6px solid #2563eb; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 20px; height: 100%; }
    .highlight-card { background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%); padding: 25px; border-radius: 20px; border-left: 8px solid #2563eb; box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08); margin-bottom: 25px; border: 1px solid #e5e7eb; }
    .big-num { color: #1e40af; font-size: 42px; font-weight: 800; font-family: 'Roboto Mono', monospace; }
    .sub-text { color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; }
    
    /* Calculation Sheet Style */
    .calc-sheet { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 20px; margin-top: 10px; box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.05); }
    .calc-header { border-bottom: 2px solid #334155; padding-bottom: 10px; margin-bottom: 15px; font-weight: bold; color: #1e293b; display: flex; justify-content: space-between; }
    .calc-row { display: flex; justify-content: space-between; margin-bottom: 8px; border-bottom: 1px dashed #e2e8f0; padding-bottom: 8px; font-family: 'Sarabun', sans-serif; }
    .calc-label { color: #475569; font-weight: 600; }
    .calc-val { font-family: 'Roboto Mono', monospace; color: #0f172a; font-weight: 500; }
    .calc-formula { background: #f1f5f9; padding: 8px; border-radius: 4px; font-family: 'Roboto Mono', monospace; font-size: 0.9em; color: #334155; margin: 5px 0; }
    
    /* Sidebar Info Box */
    .sidebar-info { background: #f1f5f9; padding: 10px; border-radius: 6px; font-size: 0.85em; margin-bottom: 10px; border: 1px solid #cbd5e1; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. INPUTS & PRE-CALCULATION
# ==========================================
with st.sidebar:
    st.title("🏗️ Beam Insight")
    st.caption("Hybrid Engine: LTB + Auto Capacity")
    st.divider()

    # --- Mode Selection ---
    analysis_mode = st.radio("🛠️ Operation Mode", ["Find Capacity (หาค่าน้ำหนักที่รับได้)", "Check Design (ตรวจสอบหน้าตัด)"])
    is_check_mode = "Check" in analysis_mode

    # --- Design Method ---
    method_opts = ["ASD (Allowable Stress)", "LRFD (Limit State)"]
    st.session_state.design_method = st.selectbox("Design Method", method_opts, index=1 if "LRFD" in st.session_state.design_method else 0)
    is_lrfd = "LRFD" in st.session_state.design_method

    # --- Material ---
    grade_opts = {"SS400 (Fy 2450)": 2450, "SM520 (Fy 3550)": 3550, "A36 (Fy 2500)": 2500}
    grade_choice = st.selectbox("Steel Grade", list(grade_opts.keys()))
    Fy = grade_opts[grade_choice]
    E_mod = 2.04e6  # ksc
    
    # --- Section Selection ---
    st.subheader("📦 Section Selection")
    input_type = st.radio("Source", ["📚 Standard Database", "✏️ Custom Input"], horizontal=True)
    
    if "Standard" in input_type:
        sec_list = steel_db.get_section_list()
        sec_name = st.selectbox("Size (JIS/SYS)", sec_list, index=13) 
        props = steel_db.get_properties(sec_name)
        h, b, tw, tf = float(props['h']), float(props['b']), float(props['tw']), float(props['tf'])
    else:
        h = st.number_input("Depth (mm)", 100.0, 2000.0, 400.0)
        b = st.number_input("Width (mm)", 50.0, 600.0, 200.0)
        tw = st.number_input("Web t (mm)", 3.0, 50.0, 8.0)
        tf = st.number_input("Flange t (mm)", 3.0, 50.0, 13.0)
        sec_name = f"Custom H-{int(h)}x{int(b)}"

    # --- Advanced Property Calculation ---
    h_c, b_c, tw_c, tf_c = h/10, b/10, tw/10, tf/10
    Ag = 2*b_c*tf_c + (h_c - 2*tf_c)*tw_c
    Ix = (b_c * h_c**3 - (b_c - tw_c) * (h_c - 2*tf_c)**3) / 12
    Iy = (2 * tf_c * b_c**3 + (h_c - 2*tf_c) * tw_c**3) / 12
    Zx = (b_c * tf_c * (h_c - tf_c)) + (tw_c * (h_c - 2*tf_c)**2 / 4) 
    Sx = (2 * Ix) / h_c 
    rx = math.sqrt(Ix/Ag)
    ry = math.sqrt(Iy/Ag)
    Aw = h_c * tw_c
    
    # Torsional Props
    J = (2 * b_c * tf_c**3 + (h_c - tf_c) * tw_c**3) / 3
    h0 = h_c - tf_c
    Cw = (Iy * h0**2) / 4
    r_ts = math.sqrt(math.sqrt(Iy * Cw) / Sx)

    # --- Geometry ---
    st.divider()
    st.subheader("📏 Geometry")
    col_g1, col_g2 = st.columns(2)
    with col_g1: user_span = st.number_input("Span (m)", 0.5, 30.0, 6.0, step=0.5)
    with col_g2: Lb = st.number_input("Unbraced Lb (m)", 0.0, user_span, user_span, step=0.5)
    defl_denom = int(st.selectbox("Deflection Limit", ["L/300", "L/360", "L/400"], index=1).split("/")[1])

    # -----------------------------------------------
    # PRE-CALCULATE CAPACITY (For Sidebar Display)
    # -----------------------------------------------
    if is_lrfd:
        phi_v = 1.00
        V_n_pre = 0.60 * Fy * Aw
        V_cap_disp = phi_v * V_n_pre
        v_label = "ϕVn"
    else:
        omg_v = 1.50
        V_n_pre = 0.60 * Fy * Aw
        V_cap_disp = V_n_pre / omg_v
        v_label = "Vn/Ω"

    # --- Connection Design Input (UPDATED) ---
    st.divider()
    st.subheader("🔩 Connection Design")
    
    # 1. Toggle Linkage
    link_conn = st.checkbox("🔗 Link with Beam Capacity", value=True, help="ถ้าเลือก จะคำนวณแรงจาก % ของหน้าตัดคาน")
    
    # 2. Show Info Box
    st.markdown(f"""
    <div class="sidebar-info">
        <div><b>Beam Span:</b> {user_span} m</div>
        <div><b>Max Shear ({v_label}):</b> {V_cap_disp:,.0f} kg</div>
    </div>
    """, unsafe_allow_html=True)

    if link_conn:
        conn_shear_pct = st.slider("% of Shear Capacity", 10, 100, 50, step=5)
        v_conn_design = V_cap_disp * (conn_shear_pct / 100.0)
        st.markdown(f"👉 **Design Force:** `{v_conn_design:,.0f} kg`")
    else:
        v_conn_design = st.number_input("Design Shear Force (kg)", value=float(int(V_cap_disp*0.5)), step=100.0)
        conn_shear_pct = (v_conn_design / V_cap_disp) * 100 if V_cap_disp > 0 else 0
        st.caption(f"(Equivalent to {conn_shear_pct:.1f}% of Capacity)")

    # --- Loads (Check Mode Only) ---
    w_load, p_load = 0.0, 0.0
    if is_check_mode:
        st.divider()
        st.subheader("⬇️ Loads (Service)")
        c_l1, c_l2 = st.columns(2)
        with c_l1: w_load = st.number_input("Uniform (kg/m)", 0.0, 20000.0, 1000.0)
        with c_l2: p_load = st.number_input("Point (kg)", 0.0, 50000.0, 0.0)

# ==========================================
# 4. MAIN LOGIC
# ==========================================
L_cm = user_span * 100
Lb_cm = Lb * 100
E = E_mod

# 4.1 LTB Constants
Lp_cm = 1.76 * ry * math.sqrt(E/Fy)
val_A = (J * 1.0) / (Sx * h0)
val_B = 6.76 * ((0.7 * Fy) / E)**2
Lr_cm = 1.95 * r_ts * (E / (0.7 * Fy)) * math.sqrt(val_A + math.sqrt(val_A**2 + val_B))

# 4.2 Moment Capacity (Mn)
Mp = Fy * Zx
Cb = 1.0 
if Lb_cm <= Lp_cm:
    Mn = Mp
    ltb_zone = "Zone 1 (Plastic)"
elif Lb_cm <= Lr_cm:
    term = (Mp - 0.7 * Fy * Sx) * ((Lb_cm - Lp_cm) / (Lr_cm - Lp_cm))
    Mn = min(Cb * (Mp - term), Mp)
    ltb_zone = "Zone 2 (Inelastic)"
else:
    slend = (Lb_cm / r_ts)
    Fcr = (Cb * math.pi**2 * E) / (slend**2) * math.sqrt(1 + 0.078 * val_A * slend**2)
    Mn = min(Fcr * Sx, Mp)
    ltb_zone = "Zone 3 (Elastic)"

# 4.3 Factored/Allowable Capacities
if is_lrfd:
    phi_b = 0.90
    V_cap = V_cap_disp # Already calculated
    M_cap = (phi_b * Mn) / 100 # kg-m
    
    fact_w = 1.4 * w_load
    fact_p = 1.4 * p_load
    method_str = "LRFD"
else:
    omg_b = 1.67
    V_cap = V_cap_disp # Already calculated
    M_cap = (Mn / omg_b) / 100 # kg-m
    
    fact_w = w_load
    fact_p = p_load
    method_str = "ASD"

# 4.4 Result Processing
d_allow = L_cm / defl_denom

if is_check_mode:
    # --- CHECK MODE ---
    v_act = (fact_w * user_span / 2) + (fact_p / 2)
    m_act = (fact_w * user_span**2 / 8) + (fact_p * user_span / 4)
    
    d_unif = (5 * (w_load/100) * (L_cm**4)) / (384 * E * Ix)
    d_point = (p_load * (L_cm**3)) / (48 * E * Ix)
    d_act = d_unif + d_point
    
    ratio_v = v_act / V_cap
    ratio_m = m_act / M_cap
    ratio_d = d_act / d_allow
    gov_ratio = max(ratio_v, ratio_m, ratio_d)
    
    if gov_ratio == ratio_v: gov_cause = "Shear"
    elif gov_ratio == ratio_m: gov_cause = "Moment"
    else: gov_cause = "Deflection"
    
else:
    # --- FIND CAPACITY MODE ---
    w_safe_shear = (2 * V_cap) / user_span
    w_safe_moment = (8 * M_cap) / (user_span**2)
    
    w_serv_defl = (384 * E * Ix * d_allow) / (5 * (L_cm**4)) * 100
    w_safe_defl = w_serv_defl * 1.4 if is_lrfd else w_serv_defl
    
    w_safe = min(w_safe_shear, w_safe_moment, w_safe_defl)
    
    # Back-calculate forces at this "Limit"
    v_act = (w_safe * user_span) / 2
    m_act = (w_safe * user_span**2) / 8
    
    ratio_v = w_safe / w_safe_shear
    ratio_m = w_safe / w_safe_moment
    ratio_d = w_safe / w_safe_defl
    
    w_safe_service = w_safe / 1.4 if is_lrfd else w_safe
    d_act = (5 * (w_safe_service/100) * (L_cm**4)) / (384 * E * Ix)

    gov_ratio = 1.00 
    
    if w_safe == w_safe_shear: gov_cause = "Shear Control"
    elif w_safe == w_safe_moment: gov_cause = "Moment Control"
    else: gov_cause = "Deflection Control"

# Save State
st.session_state.res_dict = {
    'w_safe': w_safe if not is_check_mode else 0, 
    'cause': gov_cause, 
    'v_cap': V_cap, 'v_act': v_act,
    'm_cap': M_cap, 'm_act': m_act, 'mn_raw': Mn,
    'd_all': d_allow, 'd_act': d_act,
    'v_conn_design': v_conn_design, 
    'ltb_info': {'Lp': Lp_cm, 'Lr': Lr_cm, 'Lb': Lb_cm, 'Zone': ltb_zone, 'Cb': Cb}
}
st.session_state.cal_success = True

# ==========================================
# 5. UI RENDERING
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Analysis & Graphs", "🔩 Connection Detail", "🛡️ LTB Insight", "📝 Report"])

with tab1:
    st.subheader(f"Results for: {sec_name}")

    # --- TOP CARD ---
    if is_check_mode:
        status_color = "#10b981" if gov_ratio <= 1.0 else "#ef4444"
        status_icon = "✅ PASS" if gov_ratio <= 1.0 else "❌ FAIL"
        st.markdown(f"""
        <div class="highlight-card" style="border-left-color: {status_color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span class="sub-text">Check Result ({method_str})</span><br>
                    <span class="big-num" style="color:{status_color}">{gov_ratio:.2f}</span> 
                    <span style="font-size:20px; font-weight:bold; color:{status_color}">{status_icon}</span>
                </div>
                <div style="text-align: right;">
                    <small><b>Load Case:</b> {w_load:,.0f} kg/m, {p_load:,.0f} kg</small><br>
                    <small><b>Control:</b> {gov_cause}</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        safe_val_show = w_safe / 1.4 if is_lrfd else w_safe
        st.markdown(f"""
        <div class="highlight-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span class="sub-text">Max Safe Service Load ({method_str})</span><br>
                    <span class="big-num">{safe_val_show:,.0f}</span> <span style="font-size:24px; color:#6b7280;">kg/m</span>
                </div>
                <div style="text-align: right;">
                    <span class="sub-text" style="color:#2563eb;">Limit: {gov_cause}</span><br>
                    <small>L={user_span}m | Lb={Lb}m</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- METRICS ROW ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="detail-card">
            <h4 style="margin:0;">Shear (V)</h4>
            <div style="font-size:24px; font-weight:700; color:{'#ef4444' if is_check_mode and ratio_v>1 else '#1f2937'}">
                {ratio_v:.2f} <small style="font-size:14px; color:#9ca3af;">(Ratio)</small>
            </div>
            <div style="margin-top:8px; font-size:14px;">
                <div>Act*: <b>{v_act:,.0f}</b> kg</div>
                <div>Cap: <b>{V_cap:,.0f}</b> kg</div>
            </div>
        </div>""", unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""<div class="detail-card">
            <h4 style="margin:0;">Moment (M)</h4>
            <div style="font-size:24px; font-weight:700; color:{'#ef4444' if is_check_mode and ratio_m>1 else '#1f2937'}">
                {ratio_m:.2f} <small style="font-size:14px; color:#9ca3af;">(Ratio)</small>
            </div>
            <div style="margin-top:8px; font-size:14px;">
                <div>Act*: <b>{m_act:,.0f}</b> kg-m</div>
                <div>Cap: <b>{M_cap:,.0f}</b> kg-m</div>
            </div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""<div class="detail-card">
            <h4 style="margin:0;">Deflection ($\Delta$)</h4>
            <div style="font-size:24px; font-weight:700; color:{'#ef4444' if is_check_mode and ratio_d>1 else '#1f2937'}">
                {ratio_d:.2f} <small style="font-size:14px; color:#9ca3af;">(Ratio)</small>
            </div>
            <div style="margin-top:8px; font-size:14px;">
                <div>Act*: <b>{d_act:.2f}</b> cm</div>
                <div>All: <b>{d_allow:.2f}</b> cm</div>
            </div>
        </div>""", unsafe_allow_html=True)
    
    if not is_check_mode:
        st.caption("*Act values in 'Find Capacity' mode represent the forces at the calculated Max Load.")

    # --- CALCULATION SHEET ---
    st.subheader("🧮 Calculation Sheet")
    with st.expander("📄 View Detailed Engineering Calculations", expanded=True):
        
        v_label_calc = "\phi V_n" if is_lrfd else "V_n / \Omega"
        m_label_calc = "\phi M_n" if is_lrfd else "M_n / \Omega"
        
        c_calc1, c_calc2 = st.columns(2)
        
        with c_calc1:
            st.markdown(f"""
            <div class="calc-sheet">
                <div class="calc-header">1. Shear Capacity ({method_str})</div>
                <div class="calc-row">
                    <span class="calc-label">Area Web ($A_w = h \cdot t_w$)</span>
                    <span class="calc-val">{Aw:.2f} cm²</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">Nominal Shear ($V_n = 0.6 F_y A_w$)</span>
                    <span class="calc-val">{0.6*Fy*Aw:,.0f} kg</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">Design Capacity ({v_label_calc})</span>
                    <span class="calc-val" style="color:#166534; font-weight:bold;">{V_cap:,.0f} kg</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">Actual Shear ($V_u$)</span>
                    <span class="calc-val" style="color:#1e40af;">{v_act:,.0f} kg</span>
                </div>
                <div class="calc-formula">
                    Ratio = {v_act:,.0f} / {V_cap:,.0f} = <b>{ratio_v:.3f}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="calc-sheet">
                <div class="calc-header">3. Serviceability (Deflection)</div>
                <div class="calc-row">
                    <span class="calc-label">Moment of Inertia ($I_x$)</span>
                    <span class="calc-val">{Ix:,.0f} cm⁴</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">Limit (L/{defl_denom})</span>
                    <span class="calc-val" style="color:#166534;">{d_allow:.2f} cm</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">Actual Deflection ($\Delta$)</span>
                    <span class="calc-val" style="color:#1e40af;">{d_act:.2f} cm</span>
                </div>
                <div class="calc-formula">
                    Ratio = {d_act:.2f} / {d_allow:.2f} = <b>{ratio_d:.3f}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c_calc2:
            st.markdown(f"""
            <div class="calc-sheet">
                <div class="calc-header">2. Flexural Capacity ({method_str})</div>
                <div class="calc-row">
                    <span class="calc-label">Unbraced Length ($L_b$)</span>
                    <span class="calc-val">{Lb:.2f} m</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">LTB Limits ($L_p$, $L_r$)</span>
                    <span class="calc-val">{Lp_cm/100:.2f} m, {Lr_cm/100:.2f} m</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">State</span>
                    <span class="calc-val" style="color:#b45309;">{ltb_zone}</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">Nominal Moment ($M_n$)</span>
                    <span class="calc-val">{Mn/100:,.0f} kg-m</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">Design Capacity ({m_label_calc})</span>
                    <span class="calc-val" style="color:#166534; font-weight:bold;">{M_cap:,.0f} kg-m</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">Actual Moment ($M_u$)</span>
                    <span class="calc-val" style="color:#1e40af;">{m_act:,.0f} kg-m</span>
                </div>
                <div class="calc-formula">
                    Ratio = {m_act:,.0f} / {M_cap:,.0f} = <b>{ratio_m:.3f}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # --- GRAPH ---
    st.markdown("### 📉 Span vs. Load Capacity Curve")
    spans = np.linspace(1.0, 12.0, 50)
    w_cap_moment, w_cap_shear, w_cap_defl = [], [], []
    factor_load = 1.4 if is_lrfd else 1.0 

    for s in spans:
        l_cm_g = s * 100
        lb_cm_g = l_cm_g 
        
        w_v = (2 * V_cap) / s
        
        if lb_cm_g <= Lp_cm: mn_g = Mp
        elif lb_cm_g <= Lr_cm:
            term_g = (Mp - 0.7*Fy*Sx) * ((lb_cm_g - Lp_cm)/(Lr_cm - Lp_cm))
            mn_g = min(Mp, Cb*(Mp - term_g))
        else:
            slend_g = lb_cm_g / r_ts
            fcr_g = (Cb * math.pi**2 * E) / (slend_g**2) * math.sqrt(1 + 0.078 * val_A * slend_g**2)
            mn_g = min(fcr_g * Sx, Mp)
            
        m_cap_g = (phi_b * mn_g)/100 if is_lrfd else (mn_g/omg_b)/100
        w_m = (8 * m_cap_g) / (s**2)
        
        d_all_g = l_cm_g / defl_denom
        w_d_serv = (d_all_g * 384 * E * Ix) / (5 * l_cm_g**4) * 100
        w_d = w_d_serv * factor_load 
        
        w_cap_moment.append(w_m / factor_load)
        w_cap_shear.append(w_v / factor_load)
        w_cap_defl.append(w_d / factor_load)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans, y=w_cap_moment, name='Moment Limit', line=dict(color='#3b82f6', width=3)))
    fig.add_trace(go.Scatter(x=spans, y=w_cap_defl, name='Deflection Limit', line=dict(color='#10b981', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=w_cap_shear, name='Shear Limit', line=dict(color='#f59e0b', dash='dot')))
    
    if is_check_mode:
        equiv_w_act = (fact_w + (2*fact_p/user_span)) / factor_load 
        fig.add_trace(go.Scatter(x=[user_span], y=[equiv_w_act], mode='markers', name='Your Load', marker=dict(color='red', size=12, symbol='x')))
    
    fig.update_layout(title="Safe Service Load vs. Span", xaxis_title="Span (m)", yaxis_title="Load (kg/m)", height=450)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    if st.session_state.cal_success:
        st.info(f"⚡ **Designing for Shear Force:** {v_conn_design:,.0f} kg")
        
        c_type = st.selectbox("Connection Type", ["Fin Plate", "End Plate", "Double Angle"])
        section_data = {"name": sec_name, "h": h, "b": b, "tw": tw, "tf": tf}
        
        connection_design.render_connection_tab(
            V_design_from_tab1=v_conn_design,
            default_bolt_size=20,
            method=st.session_state.design_method,
            is_lrfd=is_lrfd,
            section_data=section_data,
            conn_type=c_type,
            default_bolt_grade="A325",
            default_mat_grade=grade_choice
        )

with tab3:
    st.subheader("🛡️ LTB Insight")
    c_ltb1, c_ltb2 = st.columns([1, 2])
    with c_ltb1:
        st.markdown(f"""
        <div style="background:#f8fafc; padding:15px; border-radius:8px; border:1px solid #e2e8f0;">
            <b>LTB State:</b> {ltb_zone}<br>
            <b>Lb:</b> {Lb:.2f} m<br>
            <b>Lp:</b> {Lp_cm/100:.2f} m <br>
            <b>Lr:</b> {Lr_cm/100:.2f} m
        </div>""", unsafe_allow_html=True)
        
    with c_ltb2:
        lb_vals = np.linspace(0.1, max(Lr_cm*1.5, Lb_cm*1.2), 50)
        mn_vals = []
        for l_chk in lb_vals:
            if l_chk <= Lp_cm: mn_chk = Mp
            elif l_chk <= Lr_cm:
                term = (Mp - 0.7 * Fy * Sx) * ((l_chk - Lp_cm) / (Lr_cm - Lp_cm))
                mn_chk = min(Cb * (Mp - term), Mp)
            else:
                slend = (l_chk / r_ts)
                fcr_chk = (Cb * math.pi**2 * E) / (slend**2) * math.sqrt(1 + 0.078 * val_A * slend**2)
                mn_chk = min(fcr_chk * Sx, Mp)
            mn_vals.append(mn_chk/100) 

        fig_ltb = go.Figure()
        fig_ltb.add_trace(go.Scatter(x=lb_vals/100, y=mn_vals, name='Mn Capacity', line=dict(color='#2563eb')))
        curr_Mn = (M_cap * 100 / phi_b) if is_lrfd else (M_cap * 100 * omg_b)
        fig_ltb.add_trace(go.Scatter(x=[Lb], y=[curr_Mn/100], mode='markers', marker=dict(size=10, color='red')))
        fig_ltb.update_layout(height=300, margin=dict(t=20,b=20,l=20,r=20))
        st.plotly_chart(fig_ltb, use_container_width=True)

with tab4:
    report_generator.render_report_tab(
        method=st.session_state.design_method,
        is_lrfd=is_lrfd,
        sec_name=sec_name,
        steel_grade=grade_choice,
        p={'h': h, 'b': b, 'tw': tw, 'tf': tf, 'Ix': Ix, 'Zx': Zx, 'Sx': Sx},
        res=st.session_state.res_dict,
        bolt={'type': c_type if 'c_type' in locals() else "Fin Plate", 'grade': 'A325', 'size': 'M20', 'qty': 'N/A'}
    )

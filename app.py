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
    .status-pass { color: #10b981; font-weight: bold; }
    .status-fail { color: #ef4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SIDEBAR INPUTS
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

    # --- Advanced Property Calculation (For LTB) ---
    h_c, b_c, tw_c, tf_c = h/10, b/10, tw/10, tf/10
    Ag = 2*b_c*tf_c + (h_c - 2*tf_c)*tw_c
    Ix = (b_c * h_c**3 - (b_c - tw_c) * (h_c - 2*tf_c)**3) / 12
    Iy = (2 * tf_c * b_c**3 + (h_c - 2*tf_c) * tw_c**3) / 12
    Zx = (b_c * tf_c * (h_c - tf_c)) + (tw_c * (h_c - 2*tf_c)**2 / 4) 
    Sx = (2 * Ix) / h_c 
    rx = math.sqrt(Ix/Ag)
    ry = math.sqrt(Iy/Ag)
    
    # Torsional Props (Approx for I-Section)
    J = (2 * b_c * tf_c**3 + (h_c - tf_c) * tw_c**3) / 3
    h0 = h_c - tf_c
    Cw = (Iy * h0**2) / 4
    r_ts = math.sqrt(math.sqrt(Iy * Cw) / Sx)
    Aw = h_c * tw_c

    # --- Geometry & Load ---
    st.divider()
    st.subheader("📏 Geometry & Loads")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        user_span = st.number_input("Span (m)", 0.5, 30.0, 6.0, step=0.5)
    with col_g2:
        Lb = st.number_input("Unbraced Lb (m)", 0.0, user_span, user_span, step=0.5, help="ระยะค้ำยันด้านข้าง (ถ้าไม่มีใส่เท่าความยาวคาน)")
    
    defl_denom = int(st.selectbox("Deflection Limit", ["L/300", "L/360", "L/400"], index=1).split("/")[1])
    
    # Show Loads ONLY if in Check Mode
    w_load, p_load = 0.0, 0.0
    if is_check_mode:
        st.caption("Service Loads (ยังไม่คูณ Factor)")
        c_l1, c_l2 = st.columns(2)
        with c_l1: w_load = st.number_input("Uniform Load (kg/m)", 0.0, 20000.0, 1000.0)
        with c_l2: p_load = st.number_input("Point Load (kg)", 0.0, 50000.0, 0.0)

# ==========================================
# 4. CALCULATION LOGIC (HYBRID ENGINE)
# ==========================================
L_cm = user_span * 100
Lb_cm = Lb * 100
E = E_mod

# --- 4.1 LTB Constants (Engineering Depth) ---
Lp_cm = 1.76 * ry * math.sqrt(E/Fy)
val_A = (J * 1.0) / (Sx * h0)
val_B = 6.76 * ((0.7 * Fy) / E)**2
Lr_cm = 1.95 * r_ts * (E / (0.7 * Fy)) * math.sqrt(val_A + math.sqrt(val_A**2 + val_B))

# --- 4.2 Moment Capacity (Mn) Logic ---
Mp = Fy * Zx
Cb = 1.0 # Conservative

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

# --- 4.3 Factored Capacities ---
if is_lrfd:
    phi_v, phi_b = 1.00, 0.90
    V_cap = phi_v * (0.60 * Fy * Aw)
    M_cap = (phi_b * Mn) / 100 # kg-m
    
    # Load Factors
    fact_w = 1.4 * w_load
    fact_p = 1.4 * p_load
else:
    omg_v, omg_b = 1.50, 1.67
    V_cap = (0.60 * Fy * Aw) / omg_v
    M_cap = (Mn / omg_b) / 100 # kg-m
    
    # Load Factors
    fact_w = w_load
    fact_p = p_load

# --- 4.4 Result Processing based on Mode ---
if is_check_mode:
    # Check Design Mode
    v_act = (fact_w * user_span / 2) + (fact_p / 2)
    m_act = (fact_w * user_span**2 / 8) + (fact_p * user_span / 4)
    
    # Deflection (Service Load)
    d_unif = (5 * (w_load/100) * (L_cm**4)) / (384 * E * Ix)
    d_point = (p_load * (L_cm**3)) / (48 * E * Ix)
    d_act = d_unif + d_point
    d_allow = L_cm / defl_denom
    
    ratio_v = v_act / V_cap
    ratio_m = m_act / M_cap
    ratio_d = d_act / d_allow
    gov_ratio = max(ratio_v, ratio_m, ratio_d)
    
    if gov_ratio == ratio_v: gov_cause = "Shear"
    elif gov_ratio == ratio_m: gov_cause = "Moment"
    else: gov_cause = "Deflection"
    
else:
    # Find Capacity Mode (Back-Calculate)
    # Assume Uniform Load Dominant for "Safe Load" display
    w_safe_shear = (2 * V_cap) / user_span
    w_safe_moment = (8 * M_cap) / (user_span**2)
    
    # Back-calc Deflection (w_service) -> Convert to Factored for comparison if LRFD
    w_serv_defl = (384 * E * Ix * d_allow) / (5 * (L_cm**4)) * 100
    w_safe_defl = w_serv_defl * 1.4 if is_lrfd else w_serv_defl
    
    w_safe = min(w_safe_shear, w_safe_moment, w_safe_defl)
    
    # Set dummy actuals for graph/report
    v_act = V_cap * 0.1
    m_act = M_cap * 0.1
    d_act = d_allow * 0.1
    gov_ratio = 0.0 # Always PASS in capacity mode
    gov_cause = "Capacity Mode"
    
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
    'v_conn_design': V_cap * 0.75, # Default 75% for connection tab
    'ltb_info': {'Lp': Lp_cm, 'Lr': Lr_cm, 'Lb': Lb_cm, 'Zone': ltb_zone, 'Cb': Cb}
}
st.session_state.cal_success = True

# ==========================================
# 5. UI RENDERING (TAB 1: HYBRID DASHBOARD)
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Analysis & Graphs", "🔩 Connection Detail", "🛡️ LTB Insight", "📝 Report"])

with tab1:
    st.subheader(f"Results for: {sec_name}")

    # --- TOP CARD ---
    if is_check_mode:
        # Show Pass/Fail
        status_color = "#10b981" if gov_ratio <= 1.0 else "#ef4444"
        status_icon = "✅ PASS" if gov_ratio <= 1.0 else "❌ FAIL"
        st.markdown(f"""
        <div class="highlight-card" style="border-left-color: {status_color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span class="sub-text">Check Result ({gov_cause})</span><br>
                    <span class="big-num" style="color:{status_color}">{gov_ratio:.2f}</span> 
                    <span style="font-size:20px; font-weight:bold; color:{status_color}">{status_icon}</span>
                </div>
                <div style="text-align: right;">
                    <small><b>Wu:</b> {fact_w:,.0f} kg/m | <b>Pu:</b> {fact_p:,.0f} kg</small><br>
                    <small>Design: {st.session_state.design_method}</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Show Capacity
        safe_val_show = w_safe / 1.4 if is_lrfd else w_safe # Show Service Load usually preferred
        st.markdown(f"""
        <div class="highlight-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span class="sub-text">Max Safe Uniform Load (Service)</span><br>
                    <span class="big-num">{safe_val_show:,.0f}</span> <span style="font-size:24px; color:#6b7280;">kg/m</span>
                </div>
                <div style="text-align: right;">
                    <span class="sub-text" style="color:#2563eb;">Controlled by: {gov_cause}</span><br>
                    <small>Based on Span {user_span} m | Lb {Lb} m</small>
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
                <div>Act: <b>{v_act:,.0f}</b> kg</div>
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
                <div>Act: <b>{m_act:,.0f}</b> kg-m</div>
                <div>Cap: <b>{M_cap:,.0f}</b> kg-m</div>
            </div>
            <span style="background:#dbeafe; color:#1e40af; padding:2px 6px; border-radius:4px; font-size:11px;">{ltb_zone.split('(')[0]}</span>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""<div class="detail-card">
            <h4 style="margin:0;">Deflection ($\Delta$)</h4>
            <div style="font-size:24px; font-weight:700; color:{'#ef4444' if is_check_mode and ratio_d>1 else '#1f2937'}">
                {d_act/d_allow:.2f} <small style="font-size:14px; color:#9ca3af;">(Ratio)</small>
            </div>
            <div style="margin-top:8px; font-size:14px;">
                <div>Act: <b>{d_act:.2f}</b> cm</div>
                <div>All: <b>{d_allow:.2f}</b> cm</div>
            </div>
        </div>""", unsafe_allow_html=True)

    # --- GRAPH (THE CLASSIC ONE + LTB) ---
    st.markdown("### 📉 Span vs. Load Capacity Curve")
    
    # Create span range for graph
    spans = np.linspace(1.0, 12.0, 50)
    w_cap_moment = []
    w_cap_shear = []
    w_cap_defl = []

    # Pre-calc constants for loop efficiency
    factor_load = 1.4 if is_lrfd else 1.0 # To convert Cap to Service w on graph

    for s in spans:
        l_cm_g = s * 100
        # Assume Lb = Span for the graph curve (Conservative)
        lb_cm_g = l_cm_g 
        
        # 1. Shear Limit (Constant V_cap, varies w)
        # V = w*L/2 -> w = 2*V/L
        w_v = (2 * V_cap) / s
        
        # 2. Moment Limit (Calc Mn for this span as Lb)
        if lb_cm_g <= Lp_cm: mn_g = Mp
        elif lb_cm_g <= Lr_cm:
            term_g = (Mp - 0.7*Fy*Sx) * ((lb_cm_g - Lp_cm)/(Lr_cm - Lp_cm))
            mn_g = min(Mp, Cb*(Mp - term_g))
        else:
            slend_g = lb_cm_g / r_ts
            fcr_g = (Cb * math.pi**2 * E) / (slend_g**2) * math.sqrt(1 + 0.078 * val_A * slend_g**2)
            mn_g = min(fcr_g * Sx, Mp)
            
        m_cap_g = (phi_b * mn_g)/100 if is_lrfd else (mn_g/omg_b)/100
        # M = w*L^2/8 -> w = 8*M/L^2
        w_m = (8 * m_cap_g) / (s**2)
        
        # 3. Deflection Limit
        # d = 5wL^4/384EI -> w = d * 384EI / 5L^4
        d_all_g = l_cm_g / defl_denom
        w_d_serv = (d_all_g * 384 * E * Ix) / (5 * l_cm_g**4) * 100
        w_d = w_d_serv * factor_load # Scale to factored for comparison logic
        
        # Convert all to Service Load for Display
        w_cap_moment.append(w_m / factor_load)
        w_cap_shear.append(w_v / factor_load)
        w_cap_defl.append(w_d / factor_load)

    # Plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans, y=w_cap_moment, name='Moment Limit', line=dict(color='#3b82f6', width=3)))
    fig.add_trace(go.Scatter(x=spans, y=w_cap_defl, name='Deflection Limit', line=dict(color='#10b981', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=w_cap_shear, name='Shear Limit', line=dict(color='#f59e0b', dash='dot')))
    
    # Add User Point (Only if Check Mode)
    if is_check_mode:
        equiv_w_act = (fact_w + (2*fact_p/user_span)) / factor_load # Approx equivalent uniform
        fig.add_trace(go.Scatter(x=[user_span], y=[equiv_w_act], mode='markers', name='Your Load', marker=dict(color='red', size=12, symbol='x')))
    
    # Current Span Line
    fig.add_vline(x=user_span, line_dash="dash", line_color="gray", annotation_text=f"L={user_span}m")
    
    fig.update_layout(
        title="Safe Service Load (Uniform) vs. Span",
        xaxis_title="Span Length (m)",
        yaxis_title="Allowable Uniform Load (kg/m)",
        hovermode="x unified",
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    if st.session_state.cal_success:
        c_type = st.selectbox("Connection Type", ["Fin Plate", "End Plate", "Double Angle"])
        section_data = {"name": sec_name, "h": h, "b": b, "tw": tw, "tf": tf}
        
        # Use Fixed % if capacity mode, or Actual if check mode
        v_for_conn = v_act if is_check_mode else (V_cap * 0.5) 
        
        connection_design.render_connection_tab(
            V_design_from_tab1=v_for_conn,
            default_bolt_size=20,
            method=st.session_state.design_method,
            is_lrfd=is_lrfd,
            section_data=section_data,
            conn_type=c_type,
            default_bolt_grade="A325",
            default_mat_grade=grade_choice
        )

with tab3:
    st.subheader("🛡️ Lateral Torsional Buckling (LTB) Insight")
    c_ltb1, c_ltb2 = st.columns([1, 2])
    
    with c_ltb1:
        st.info(f"**Current State:** {ltb_zone}")
        st.markdown(f"""
        <div style="background:#f8fafc; padding:15px; border-radius:8px; border:1px solid #e2e8f0;">
            <b>Parameters</b><br>
            • Unbraced Length ($L_b$): <b>{Lb:.2f} m</b><br>
            • Plastic Limit ($L_p$): <b style="color:#059669">{Lp_cm/100:.2f} m</b><br>
            • Inelastic Limit ($L_r$): <b style="color:#d97706">{Lr_cm/100:.2f} m</b><br>
            • Gradient ($C_b$): <b>{Cb:.2f}</b>
        </div>
        """, unsafe_allow_html=True)
        
    with c_ltb2:
        # LTB Curve visualization code (same as before but preserved)
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
        fig_ltb.add_trace(go.Scatter(x=lb_vals/100, y=mn_vals, name='Mn Capacity', line=dict(color='#2563eb', width=3)))
        curr_Mn = (M_cap * 100 / phi_b) if is_lrfd else (M_cap * 100 * omg_b)
        fig_ltb.add_trace(go.Scatter(x=[Lb], y=[curr_Mn/100], mode='markers+text', text=["This Beam"], textposition="top right", marker=dict(size=12, color='red')))
        fig_ltb.add_vline(x=Lp_cm/100, line_dash="dash", annotation_text="Lp")
        fig_ltb.add_vline(x=Lr_cm/100, line_dash="dash", annotation_text="Lr")
        fig_ltb.update_layout(xaxis_title="Lb (m)", yaxis_title="Mn (kg-m)", height=350, margin=dict(t=20, b=20, l=20, r=20))
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

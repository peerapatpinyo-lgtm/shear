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
st.set_page_config(page_title="Beam Insight V19 (Engineering Depth)", layout="wide", page_icon="🏗️")

if 'design_method' not in st.session_state:
    st.session_state.design_method = "LRFD (Limit State)"
if 'cal_success' not in st.session_state:
    st.session_state.cal_success = False

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Roboto+Mono:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
    .detail-card { background: white; border-radius: 12px; padding: 20px; border: 1px solid #e5e7eb; border-top: 6px solid #2563eb; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .highlight-card { background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%); padding: 25px; border-radius: 20px; border-left: 8px solid #2563eb; box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08); margin-bottom: 25px; border: 1px solid #e5e7eb; }
    .big-num { color: #1e40af; font-size: 42px; font-weight: 800; font-family: 'Roboto Mono', monospace; }
    .sub-text { color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; }
    .metric-box { background: #f8fafc; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SIDEBAR INPUTS
# ==========================================
with st.sidebar:
    st.title("🏗️ Beam Insight V19")
    st.caption("Enhanced with LTB & Mixed Loads")
    st.divider()
    
    # --- Design Method ---
    method_opts = ["ASD (Allowable Stress)", "LRFD (Limit State)"]
    st.session_state.design_method = st.radio("Design Method", method_opts, index=1 if "LRFD" in st.session_state.design_method else 0)
    is_lrfd = "LRFD" in st.session_state.design_method

    # --- Material ---
    grade_opts = {"SS400 (Fy 2450)": 2450, "SM520 (Fy 3550)": 3550, "A36 (Fy 2500)": 2500}
    grade_choice = st.selectbox("Steel Grade", list(grade_opts.keys()))
    Fy = grade_opts[grade_choice]
    E_mod = 2.04e6  # ksc
    
    # --- Section Selection ---
    st.subheader("📦 Section Selection")
    input_mode = st.radio("Source", ["📚 Standard Database", "✏️ Custom Input"], horizontal=True)
    
    if "Standard" in input_mode:
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
    # Convert to cm
    h_c, b_c, tw_c, tf_c = h/10, b/10, tw/10, tf/10
    
    # Basic Props
    Ag = 2*b_c*tf_c + (h_c - 2*tf_c)*tw_c
    Ix = (b_c * h_c**3 - (b_c - tw_c) * (h_c - 2*tf_c)**3) / 12
    Iy = (2 * tf_c * b_c**3 + (h_c - 2*tf_c) * tw_c**3) / 12
    Zx = (b_c * tf_c * (h_c - tf_c)) + (tw_c * (h_c - 2*tf_c)**2 / 4) # Plastic Modulus
    Sx = (2 * Ix) / h_c  # Elastic Modulus
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
        user_span = st.number_input("Span Length (m)", 0.5, 30.0, 6.0, step=0.5)
    with col_g2:
        Lb = st.number_input("Unbraced Length Lb (m)", 0.0, user_span, user_span, step=0.5, help="Distance between lateral supports")
    
    defl_denom = int(st.selectbox("Deflection Limit", ["L/300", "L/360", "L/400"], index=1).split("/")[1])
    
    st.caption("Load Pattern (Service Load)")
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        w_load = st.number_input("Uniform Load (kg/m)", 0.0, 10000.0, 1000.0)
    with col_l2:
        p_load = st.number_input("Point Load @ Center (kg)", 0.0, 50000.0, 0.0)

    st.subheader("🔩 Connection Scope")
    design_mode = st.radio("Load Basis:", ["Actual Load (แรงจริง)", "Fixed % Capacity (% หน้าตัด)"])
    target_pct = st.slider("% of Shear Capacity", 50, 100, 75) if "Fixed" in design_mode else 0

# ==========================================
# 4. CALCULATION LOGIC (ADVANCED)
# ==========================================
L_cm = user_span * 100
Lb_cm = Lb * 100

# 4.1 Factored Loads (Demand)
if is_lrfd:
    # LRFD: 1.2D + 1.6L (สมมติเป็น Live ทั้งหมดเพื่อความปลอดภัยสูงสุด หรือ 1.4 ถ้าคิดรวมๆ)
    # เพื่อความง่ายใน App V1 นี้ ใช้ Factor เฉลี่ย 1.5 หรือรับค่าเป็น Factored Load เลย
    # แต่ User กรอก Service Load -> เราคูณ Factor ให้
    fact_w = 1.4 * w_load  # Simplified Factor
    fact_p = 1.4 * p_load
    phi_v, phi_b = 1.00, 0.90
    
    # Demand Calculation
    v_act = (fact_w * user_span / 2) + (fact_p / 2)
    m_act = (fact_w * user_span**2 / 8) + (fact_p * user_span / 4)
    label_load = "Factored Load ($W_u, P_u$)"
else:
    # ASD: No Factor
    fact_w = w_load
    fact_p = p_load
    omg_v, omg_b = 1.50, 1.67
    
    v_act = (fact_w * user_span / 2) + (fact_p / 2)
    m_act = (fact_w * user_span**2 / 8) + (fact_p * user_span / 4)
    label_load = "Service Load ($W_a, P_a$)"

# 4.2 Deflection (Service Load Check)
d_unif = (5 * (w_load/100) * (L_cm**4)) / (384 * E_mod * Ix)
d_point = (p_load * (L_cm**3)) / (48 * E_mod * Ix)
d_act = d_unif + d_point
d_allow = L_cm / defl_denom

# 4.3 Shear Capacity
if is_lrfd:
    V_n = 0.60 * Fy * Aw
    V_cap = phi_v * V_n
else:
    V_n = 0.60 * Fy * Aw
    V_cap = V_n / omg_v

# 4.4 Moment Capacity with LTB (The Core Upgrade)
# Calculate Lp and Lr
# Lp = 1.76 * ry * sqrt(E/Fy)
Lp_cm = 1.76 * ry * math.sqrt(E_mod/Fy)

# Lr needs calculation (AISC Eq. F2-6)
# rts^2 = (Iy*Cw)^0.5 / Sx ... already calc as r_ts
# X1 = (pi/Sx) * sqrt(E*G*J*A/2) ... Simplified approach:
# Using AISC F2-6 exact form:
E = E_mod
G = E_mod / 2.6 # Shear modulus approx
# Note: Full Lr formula is complex. Using the standard AISC I-beam formula:
# Lr = 1.95 * rts * (E / 0.7Fy) * sqrt( (Jc/Sxho) + sqrt( (Jc/Sxho)^2 + 6.76(0.7Fy/E)^2 ) )
# Assume c=1 for doubly symmetric
val_A = (J * 1.0) / (Sx * h0)
val_B = 6.76 * ((0.7 * Fy) / E)**2
Lr_cm = 1.95 * r_ts * (E / (0.7 * Fy)) * math.sqrt(val_A + math.sqrt(val_A**2 + val_B))

# Determine Zone & Mn
Mp = Fy * Zx
Cb = 1.0 # Conservative, or 1.32 for point load at center

if Lb_cm <= Lp_cm:
    # Zone 1: Plastic
    Mn = Mp
    ltb_zone = "Zone 1 (Plastic Yielding)"
elif Lb_cm <= Lr_cm:
    # Zone 2: Inelastic LTB
    # Mn = Cb * [Mp - (Mp - 0.7FySx)((Lb-Lp)/(Lr-Lp))] <= Mp
    term = (Mp - 0.7 * Fy * Sx) * ((Lb_cm - Lp_cm) / (Lr_cm - Lp_cm))
    Mn = Cb * (Mp - term)
    Mn = min(Mn, Mp)
    ltb_zone = "Zone 2 (Inelastic LTB)"
else:
    # Zone 3: Elastic LTB
    # Fcr = (Cb * pi^2 * E) / (Lb/rts)^2 * sqrt(1 + 0.078(Jc/Sxho)(Lb/rts)^2)
    # Mn = Fcr * Sx <= Mp
    slenderness = (Lb_cm / r_ts)
    Fcr = (Cb * math.pi**2 * E) / (slenderness**2) * math.sqrt(1 + 0.078 * val_A * slenderness**2)
    Mn = Fcr * Sx
    Mn = min(Mn, Mp)
    ltb_zone = "Zone 3 (Elastic LTB)"

# Apply Safety Factor to Moment
if is_lrfd:
    M_cap = (phi_b * Mn) / 100 # kg-m
else:
    M_cap = (Mn / omg_b) / 100 # kg-m

# 4.5 Prepare Results
w_safe_shear = (2 * V_cap - fact_p) / user_span # Back-calc allowable w if P is fixed
w_safe_moment = (8 * M_cap - 2 * fact_p * user_span) / (user_span**2) # Approx logic for display
w_safe = 0 # Placeholder, calculating ratio is more accurate now with mixed loads

ratio_v = v_act / V_cap
ratio_m = m_act / M_cap
ratio_d = d_act / d_allow

gov_ratio = max(ratio_v, ratio_m, ratio_d)
if gov_ratio == ratio_v: gov_cause = "Shear"
elif gov_ratio == ratio_m: gov_cause = "Moment (LTB)"
else: gov_cause = "Deflection"

v_conn_design = V_cap * (target_pct / 100.0) if "Fixed" in design_mode else v_act

st.session_state.res_dict = {
    'w_safe': 0, 'cause': gov_cause, 
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
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection Detail", "📋 LTB Status", "📝 Report"])

with tab1:
    st.subheader(f"Analysis Result: {sec_name}")
    
    # Status Banner
    status_color = "#10b981" if gov_ratio <= 1.0 else "#ef4444"
    status_icon = "✅ PASS" if gov_ratio <= 1.0 else "❌ FAIL"
    
    st.markdown(f"""
    <div class="highlight-card" style="border-left-color: {status_color};">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span class="sub-text">Governing Ratio ({gov_cause})</span><br>
                <span class="big-num" style="color:{status_color}">{gov_ratio:.3f}</span> 
                <span style="font-size:20px; font-weight:bold; color:{status_color}">{status_icon}</span>
            </div>
            <div style="text-align: right;">
                 <span class="sub-text">Combined Loads</span><br>
                 <small><b>Wu:</b> {fact_w:,.0f} kg/m | <b>Pu:</b> {fact_p:,.0f} kg</small><br>
                 <small><b>Design Method:</b> {st.session_state.design_method}</small>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""<div class="detail-card">
            <h4 style="margin:0;">Shear (V)</h4>
            <div style="font-size:24px; font-weight:700; color:{'#ef4444' if ratio_v>1 else '#1f2937'}">{ratio_v:.3f}</div>
            <small>Act: {v_act:,.0f} kg</small><br>
            <small>Cap: {V_cap:,.0f} kg</small>
        </div>""", unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""<div class="detail-card">
            <h4 style="margin:0;">Moment (M)</h4>
            <div style="font-size:24px; font-weight:700; color:{'#ef4444' if ratio_m>1 else '#1f2937'}">{ratio_m:.3f}</div>
            <small>Act: {m_act:,.0f} kg-m</small><br>
            <small>Cap: {M_cap:,.0f} kg-m</small><br>
            <span style="background:#e0f2fe; color:#0369a1; padding:2px 6px; border-radius:4px; font-size:12px;">{ltb_zone.split('(')[0]}</span>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""<div class="detail-card">
            <h4 style="margin:0;">Deflection ($\Delta$)</h4>
            <div style="font-size:24px; font-weight:700; color:{'#ef4444' if ratio_d>1 else '#1f2937'}">{ratio_d:.3f}</div>
            <small>Act: {d_act:.2f} cm</small><br>
            <small>Allow: {d_allow:.2f} cm</small>
        </div>""", unsafe_allow_html=True)

    # Simplified Graph (Moment Diagram Shape depends on load, just show Envelope vs Capacity)
    st.markdown("### 📉 Capacity vs Span")
    sp_graph = np.linspace(0.5, 12, 50)
    # Recalculate basic capacity for graph (assuming Uniform load dominant for curve shape)
    y_m_limit = []
    for s in sp_graph:
        # LTB Effect on graph is complex (Lb changes?), assuming Lb = Span for graph simplicity
        # This is an approximation for visualization
        y_m_limit.append(8 * M_cap / s**2) 
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sp_graph, y=y_m_limit, name='Moment Limit (Uniform)', line=dict(color='#f59e0b', dash='dash')))
    fig.add_trace(go.Scatter(x=[user_span], y=[(8*m_act/user_span**2)], mode='markers', name='Your Load', marker=dict(color='red', size=12)))
    fig.update_layout(height=400, xaxis_title="Span (m)", yaxis_title="Equivalent Uniform Load (kg/m)")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    if st.session_state.cal_success:
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
    st.subheader("🛡️ Lateral Torsional Buckling (LTB) Check")
    
    c_ltb1, c_ltb2 = st.columns([1, 2])
    
    with c_ltb1:
        st.info(f"**Current State:**\n\n{ltb_zone}")
        st.markdown(f"""
        <div class="metric-box">
            <b>Unbraced Length ($L_b$)</b><br>
            <span style="font-size:24px;">{Lb:.2f} m</span>
        </div>
        <div class="metric-box" style="margin-top:10px;">
            <b>Plastic Limit ($L_p$)</b><br>
            <span style="font-size:24px; color:#059669;">{Lp_cm/100:.2f} m</span>
        </div>
        <div class="metric-box" style="margin-top:10px;">
            <b>Inelastic Limit ($L_r$)</b><br>
            <span style="font-size:24px; color:#d97706;">{Lr_cm/100:.2f} m</span>
        </div>
        """, unsafe_allow_html=True)
        
    with c_ltb2:
        st.markdown("### LTB Capacity Curve")
        # Generate Curve Lb vs Mn
        lb_vals = np.linspace(0.1, max(Lr_cm*1.5, Lb_cm*1.2), 50)
        mn_vals = []
        for l_chk in lb_vals:
            if l_chk <= Lp_cm:
                mn_chk = Mp
            elif l_chk <= Lr_cm:
                term = (Mp - 0.7 * Fy * Sx) * ((l_chk - Lp_cm) / (Lr_cm - Lp_cm))
                mn_chk = min(Cb * (Mp - term), Mp)
            else:
                slend = (l_chk / r_ts)
                fcr_chk = (Cb * math.pi**2 * E) / (slend**2) * math.sqrt(1 + 0.078 * val_A * slend**2)
                mn_chk = min(fcr_chk * Sx, Mp)
            mn_vals.append(mn_chk/100) # to kg-m

        fig_ltb = go.Figure()
        fig_ltb.add_trace(go.Scatter(x=lb_vals/100, y=mn_vals, name='Mn Capacity', line=dict(color='#2563eb', width=3)))
        # Add Current Point
        curr_Mn = (M_cap * 100 / phi_b) if is_lrfd else (M_cap * 100 * omg_b) # Back to Nominal
        fig_ltb.add_trace(go.Scatter(x=[Lb], y=[curr_Mn/100], mode='markers+text', text=["Your Beam"], textposition="top right", marker=dict(size=12, color='red')))
        
        # Zones
        fig_ltb.add_vline(x=Lp_cm/100, line_dash="dash", annotation_text="Lp")
        fig_ltb.add_vline(x=Lr_cm/100, line_dash="dash", annotation_text="Lr")
        
        fig_ltb.update_layout(xaxis_title="Unbraced Length Lb (m)", yaxis_title="Moment Capacity Mn (kg-m)", height=400)
        st.plotly_chart(fig_ltb, use_container_width=True)
        
        st.markdown("""
        **Note:**
        - **Zone 1 ($L_b \le L_p$):** Full Plastic Moment ($M_p$).
        - **Zone 2 ($L_p < L_b \le L_r$):** Linear reduction (Inelastic Buckling).
        - **Zone 3 ($L_b > L_r$):** Elastic Buckling ($F_{cr}$).
        """)

with tab4:
    # Need to update report generator to handle mixed loads description later
    # passing res_dict is key
    report_generator.render_report_tab(
        method=st.session_state.design_method,
        is_lrfd=is_lrfd,
        sec_name=sec_name,
        steel_grade=grade_choice,
        p={'h': h, 'b': b, 'tw': tw, 'tf': tf, 'Ix': Ix, 'Zx': Zx, 'Sx': Sx},
        res=st.session_state.res_dict,
        bolt={'type': c_type if 'c_type' in locals() else "Fin Plate", 'grade': 'A325', 'size': 'M20', 'qty': 'N/A'}
    )

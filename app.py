# app.py

import streamlit as st
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
    import tab1_analysis
    import tab3_ltb
    import tab5_baseplate # เพิ่ม Module ใหม่
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
if 'conn_type' not in st.session_state:
    st.session_state.conn_type = "Fin Plate"

# CSS Styles
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Roboto+Mono:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
    
    .detail-card { background: white; border-radius: 12px; padding: 20px; border: 1px solid #e5e7eb; border-top: 6px solid #2563eb; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 20px; height: 100%; }
    .highlight-card { background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%); padding: 25px; border-radius: 20px; border-left: 8px solid #2563eb; box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08); margin-bottom: 25px; border: 1px solid #e5e7eb; }
    .big-num { color: #1e40af; font-size: 42px; font-weight: 800; font-family: 'Roboto Mono', monospace; }
    .sub-text { color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; }
    
    .calc-sheet { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 20px; margin-top: 10px; box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.05); }
    .calc-header { border-bottom: 2px solid #334155; padding-bottom: 10px; margin-bottom: 15px; font-weight: bold; color: #1e293b; display: flex; justify-content: space-between; }
    .calc-row { display: flex; justify-content: space-between; margin-bottom: 8px; border-bottom: 1px dashed #e2e8f0; padding-bottom: 8px; font-family: 'Sarabun', sans-serif; }
    .calc-label { color: #475569; font-weight: 600; }
    .calc-val { font-family: 'Roboto Mono', monospace; color: #0f172a; font-weight: 500; }
    .calc-formula { background: #f1f5f9; padding: 8px; border-radius: 4px; font-family: 'Roboto Mono', monospace; font-size: 0.9em; color: #334155; margin: 5px 0; }
    
    /* Sidebar Specific */
    .sidebar-info { background: #f8fafc; padding: 12px; border-radius: 8px; font-size: 0.9em; margin-bottom: 15px; border: 1px solid #cbd5e1; }
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
    analysis_mode = st.radio("🛠️ Operation Mode", ["Find Capacity", "Check Design"])
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
    with col_g2: Lb = st.number_input("Unbraced Length Lb (m)", 0.0, user_span, user_span, step=0.5)
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

    # --- Connection Design Input ---
    st.divider()
    st.subheader("🔩 Connection Design")
    
    # Info
    st.markdown(f"""
    <div class="sidebar-info">
        <div><b>Max Shear Capacity ({v_label}):</b> <br><span style="font-size:1.2em; color:#1e40af;">{V_cap_disp:,.0f} kg</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Inputs
    link_conn = st.checkbox("🔗 Link with Beam Capacity", value=True)
    if link_conn:
        conn_shear_pct = st.slider("% of Shear Capacity", 10, 100, 50, step=5)
        v_support_design = V_cap_disp * (conn_shear_pct / 100.0)
    else:
        v_support_design = st.number_input("Design Shear @ Support (kg)", value=float(int(V_cap_disp*0.5)), step=100.0)

    # --- ECCENTRICITY CALCULATION ---
    st.markdown("---")
    st.write("📐 **Load Position & Reductions**")
    
    ecc_e = st.number_input("Eccentricity 'e' (mm)", value=50, step=5, help="Distance from support face to bolt group centroid")
    
    # Calculate Reduction
    w_equiv_load = (2 * v_support_design) / user_span # kg/m
    v_reduction = w_equiv_load * (ecc_e / 1000.0)     # kg
    v_at_bolt = v_support_design - v_reduction

    # Display Logic
    st.markdown(f"""
    <div style="background:#fff; border:1px solid #ddd; border-radius:6px; padding:10px; margin-top:5px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
            <span style="color:#64748b;">V @ Support:</span>
            <span style="font-weight:bold;">{v_support_design:,.0f} kg</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:5px; border-bottom:1px dashed #eee; padding-bottom:5px;">
             <span style="color:#ef4444; font-size:0.9em;">- Reduction (w&times;e):</span>
             <span style="color:#ef4444; font-size:0.9em;">{v_reduction:,.0f} kg</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="color:#1e3a8a; font-weight:bold;">V @ Bolt Group:</span>
            <span style="background:#dbeafe; color:#1e40af; padding:2px 6px; border-radius:4px; font-weight:bold;">{v_at_bolt:,.0f} kg</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Final Decision for Calc
    use_reduced = st.checkbox("Use Reduced Force for Design?", value=False, help="If selected, V @ Bolt is used. Otherwise, V @ Support is used (Conservative)")
    v_conn_final = v_at_bolt if use_reduced else v_support_design

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
    V_cap = V_cap_disp 
    M_cap = (phi_b * Mn) / 100 # kg-m
    
    fact_w = 1.4 * w_load
    fact_p = 1.4 * p_load
    method_str = "LRFD"
else:
    omg_b = 1.67
    V_cap = V_cap_disp 
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

# ==========================================
# 5. PACK DATA FOR TABS
# ==========================================
results_context = {
    'is_check_mode': is_check_mode,
    'method_str': method_str,
    'is_lrfd': is_lrfd,
    'sec_name': sec_name,
    'user_span': user_span,
    'Lb': Lb,
    'Lb_cm': Lb_cm,
    'Fy': Fy,
    'E': E,
    
    'w_load': w_load,
    'p_load': p_load,
    'fact_w': fact_w,
    'fact_p': fact_p,
    
    'V_cap': V_cap,
    'M_cap': M_cap,
    'v_act': v_act,
    'm_act': m_act,
    'ratio_v': ratio_v,
    'ratio_m': ratio_m,
    'ratio_d': ratio_d,
    'gov_ratio': gov_ratio,
    'gov_cause': gov_cause,
    'w_safe': w_safe if not is_check_mode else 0,
    
    'd_act': d_act,
    'd_allow': d_allow,
    'defl_denom': defl_denom,
    
    'Aw': Aw,
    'Ix': Ix,
    'Sx': Sx,
    'Zx': Zx,
    'Mp': Mp,
    'Cb': Cb,
    'r_ts': r_ts,
    'val_A': val_A,
    'Lp_cm': Lp_cm,
    'Lr_cm': Lr_cm,
    'ltb_zone': ltb_zone,
    'Mn': Mn,
    
    'ry': ry,
    'J': J,
    'h0': h0
}

# Save simplified state for report generator
st.session_state.res_dict = {
    'w_safe': w_safe if not is_check_mode else 0, 
    'cause': gov_cause, 
    'v_cap': V_cap, 'v_act': v_act,
    'm_cap': M_cap, 'm_act': m_act, 'mn_raw': Mn,
    'd_all': d_allow, 'd_act': d_act,
    'v_conn_design': v_conn_final, 
    'ltb_info': {'Lp': Lp_cm, 'Lr': Lr_cm, 'Lb': Lb_cm, 'Zone': ltb_zone, 'Cb': Cb}
}
st.session_state.cal_success = True

# ==========================================
# 6. UI RENDERING
# ==========================================
# เพิ่ม tab5 เข้าไปในการประกาศตัวแปร
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Analysis & Graphs", 
    "🔩 Connection Detail", 
    "🛡️ LTB Insight", 
    "📝 Report", 
    "🧱 Base Plate"
])

# --- TAB 1: ANALYSIS & GRAPHS ---
with tab1:
    tab1_analysis.render(results_context)

# --- TAB 2: CONNECTION DETAIL ---
with tab2:
    if st.session_state.cal_success:
        st.info(f"⚡ **Designing for Shear Force:** {v_conn_final:,.0f} kg")
        
        c_type = st.selectbox("Connection Type", ["Fin Plate", "End Plate", "Double Angle"], key='conn_type_select')
        st.session_state.conn_type = c_type 
        
        section_data = {"name": sec_name, "h": h, "b": b, "tw": tw, "tf": tf}
        
        connection_design.render_connection_tab(
            V_design_from_tab1=v_conn_final,
            default_bolt_size=20,
            method=st.session_state.design_method,
            is_lrfd=is_lrfd,
            section_data=section_data,
            conn_type=c_type,
            default_bolt_grade="A325",
            default_mat_grade=grade_choice
        )
    else:
        st.warning("Please complete analysis in Tab 1 first.")

# --- TAB 3: LTB INSIGHT ---
with tab3:
    tab3_ltb.render(results_context)

# --- TAB 4: REPORT ---
with tab4:
    if st.session_state.cal_success:
        report_generator.render_report_tab(
            method=st.session_state.design_method,
            is_lrfd=is_lrfd,
            sec_name=sec_name,
            steel_grade=grade_choice,
            p={'h': h, 'b': b, 'tw': tw, 'tf': tf, 'Ix': Ix, 'Zx': Zx, 'Sx': Sx},
            res=st.session_state.res_dict,
            bolt={'type': st.session_state.get('conn_type', 'Fin Plate'), 'grade': 'A325', 'size': 'M20', 'qty': 'N/A'}
        )
    else:
        st.warning("Please complete analysis first.")

# --- TAB 5: BASE PLATE (แก้ไข NameError) ---
with tab5:
    if st.session_state.cal_success:
        # ส่งแรงปฏิกิริยา (v_at_bolt หรือ v_support_design) ไปคำนวณ
        tab5_baseplate.render(results_context, v_conn_final)
    else:
        st.warning("Please complete analysis first.")

# ==========================================
# 🏗️ BEAM INSIGHT HYBRID ENGINE - FULL VERSION
# ==========================================
# Filename: app.py
# Description: Structural Steel Beam Analysis with LTB, Connection, and Base Plate
# Development Year: 2026
# ==========================================

import streamlit as st
import math
import sys
import os

# ==========================================
# 0. SYSTEM PATCH & INITIALIZATION
# ==========================================
# Patching markdown to always allow HTML for custom UI components
_original_markdown = st.markdown
def _patched_markdown(body, unsafe_allow_html=False, **kwargs):
    return _original_markdown(body, unsafe_allow_html=True, **kwargs)
st.markdown = _patched_markdown

def init_session_state():
    """Initializes all required session state variables to prevent KeyErrors."""
    if 'design_method' not in st.session_state:
        st.session_state.design_method = "LRFD (Limit State)"
    if 'cal_success' not in st.session_state:
        st.session_state.cal_success = False
    if 'conn_type' not in st.session_state:
        st.session_state.conn_type = "Fin Plate"
    if 'res_dict' not in st.session_state:
        st.session_state.res_dict = {}
    # เพิ่มตัวแปรสำหรับเก็บผลออกแบบ Connection เพื่อส่งไป Report
    if 'v_design' not in st.session_state:
        st.session_state.v_design = {}

init_session_state()

# ==========================================
# 1. IMPORT MODULES WITH ERROR HANDLING
# ==========================================
try:
    import steel_db               
    import connection_design      
    import report_generator
    import tab1_analysis
    import tab3_ltb
    import tab5_baseplate # Ensuring Tab 5 is imported
except ImportError as e:
    st.error(f"❌ CRITICAL ERROR: Modules missing: {e}")
    st.info("Please ensure all helper scripts (steel_db.py, etc.) are in the same directory.")
    st.stop()

# ==========================================
# 2. UI SETUP & CSS STYLING
# ==========================================
st.set_page_config(
    page_title="Beam Insight Hybrid | Structural Design",
    layout="wide",
    page_icon="🏗️",
    initial_sidebar_state="expanded"
)

# Robust Custom CSS for Professional Engineering Look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Roboto+Mono:wght@400;700&display=swap');
    
    /* Core Typography */
    html, body, [class*="css"] { 
        font-family: 'Sarabun', sans-serif; 
    }
    
    /* Engineering Card Styles */
    .detail-card { 
        background: white; 
        border-radius: 12px; 
        padding: 20px; 
        border: 1px solid #e5e7eb; 
        border-top: 6px solid #2563eb; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); 
        margin-bottom: 20px; 
    }
    
    .highlight-card { 
        background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%); 
        padding: 25px; 
        border-radius: 20px; 
        border-left: 8px solid #2563eb; 
        box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08); 
        margin-bottom: 25px; 
        border: 1px solid #e5e7eb; 
    }
    
    /* Numeric Formatting */
    .big-num { 
        color: #1e40af; 
        font-size: 42px; 
        font-weight: 800; 
        font-family: 'Roboto Mono', monospace; 
    }
    
    .sub-text { 
        color: #6b7280; 
        font-size: 14px; 
        font-weight: 600; 
        text-transform: uppercase; 
    }
    
    /* Calculation Sheet (Blue-print style) */
    .calc-sheet { 
        background-color: #ffffff; 
        border: 1px solid #cbd5e1; 
        border-radius: 8px; 
        padding: 20px; 
        margin-top: 10px; 
        box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.05); 
    }
    
    .calc-header { 
        border-bottom: 2px solid #334155; 
        padding-bottom: 10px; 
        margin-bottom: 15px; 
        font-weight: bold; 
        color: #1e293b; 
        display: flex; 
        justify-content: space-between; 
    }
    
    .calc-row { 
        display: flex; 
        justify-content: space-between; 
        margin-bottom: 8px; 
        border-bottom: 1px dashed #e2e8f0; 
        padding-bottom: 8px; 
    }
    
    .calc-label { color: #475569; font-weight: 600; }
    .calc-val { font-family: 'Roboto Mono', monospace; color: #0f172a; font-weight: 500; }
    
    .calc-formula { 
        background: #f1f5f9; 
        padding: 10px; 
        border-radius: 6px; 
        font-family: 'Roboto Mono', monospace; 
        font-size: 0.9em; 
        color: #1e293b; 
        margin: 10px 0;
        border-left: 4px solid #94a3b8;
    }
    
    /* Sidebar Widgets */
    .sidebar-info { 
        background: #f8fafc; 
        padding: 15px; 
        border-radius: 10px; 
        font-size: 0.9em; 
        margin-bottom: 15px; 
        border: 1px solid #cbd5e1; 
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SIDEBAR: PARAMETER INPUTS
# ==========================================
with st.sidebar:
    st.markdown("## 🏗️ Structural Control")
    st.caption("AISC 360-22 Standard Hybrid Engine")
    st.divider()

    # --- Mode Selection ---
    analysis_mode = st.radio(
        "🛠️ Operation Mode", 
        ["Find Capacity", "Check Design"],
        help="Capacity: Finds max load. Check: Verifies user-defined loads."
    )
    is_check_mode = "Check" in analysis_mode

    # --- Design Method ---
    method_opts = ["ASD (Allowable Stress)", "LRFD (Limit State)"]
    st.session_state.design_method = st.selectbox(
        "Design Method", 
        method_opts, 
        index=1 if "LRFD" in st.session_state.design_method else 0
    )
    is_lrfd = "LRFD" in st.session_state.design_method

    # --- Material Properties ---
    st.markdown("### 🧬 Material Properties")
    grade_opts = {
        "SS400 (Fy 2450)": 2450, 
        "SM520 (Fy 3550)": 3550, 
        "A36 (Fy 2500)": 2500,
        "Custom Grade": 0
    }
    grade_choice = st.selectbox("Steel Grade", list(grade_opts.keys()))
    
    if grade_choice == "Custom Grade":
        Fy = st.number_input("Custom Fy (kg/cm²)", 1000, 10000, 2450)
    else:
        Fy = grade_opts[grade_choice]
        
    E_mod = 2.04e6  # Young's Modulus in ksc
    
    # --- Section Selection ---
    st.divider()
    st.subheader("📦 Section Selection")
    input_type = st.radio("Source", ["📚 Standard Database", "✏️ Custom Input"], horizontal=True)
    
    if "Standard" in input_type:
        try:
            sec_list = steel_db.get_section_list()
            sec_name = st.selectbox("Size (JIS/SYS)", sec_list, index=13) 
            props = steel_db.get_properties(sec_name)
            h, b, tw, tf = float(props['h']), float(props['b']), float(props['tw']), float(props['tf'])
        except Exception as e:
            st.error(f"Error loading database: {e}")
            h, b, tw, tf = 400, 200, 8, 13
            sec_name = "Default 400x200"
    else:
        h = st.number_input("Depth h (mm)", 100.0, 2000.0, 400.0)
        b = st.number_input("Width b (mm)", 50.0, 600.0, 200.0)
        tw = st.number_input("Web thickness tw (mm)", 3.0, 50.0, 8.0)
        tf = st.number_input("Flange thickness tf (mm)", 3.0, 50.0, 13.0)
        sec_name = f"Custom-H {int(h)}x{int(b)}"

    # --- Advanced Property Calculations (Geometric) ---
    # Conversion to cm
    h_c, b_c, tw_c, tf_c = h/10, b/10, tw/10, tf/10
    
    Ag = 2*b_c*tf_c + (h_c - 2*tf_c)*tw_c
    Ix = (b_c * h_c**3 - (b_c - tw_c) * (h_c - 2*tf_c)**3) / 12
    Iy = (2 * tf_c * b_c**3 + (h_c - 2*tf_c) * tw_c**3) / 12
    Zx = (b_c * tf_c * (h_c - tf_c)) + (tw_c * (h_c - 2*tf_c)**2 / 4) 
    Sx = (2 * Ix) / h_c 
    rx = math.sqrt(Ix/Ag)
    ry = math.sqrt(Iy/Ag)
    Aw = h_c * tw_c
    
    # Torsional Properties
    J = (2 * b_c * tf_c**3 + (h_c - tf_c) * tw_c**3) / 3
    h0 = h_c - tf_c
    Cw = (Iy * h0**2) / 4
    r_ts = math.sqrt(math.sqrt(Iy * Cw) / Sx)

    # --- Geometry Parameters ---
    st.divider()
    st.subheader("📏 Geometry")
    col_g1, col_g2 = st.columns(2)
    with col_g1: 
        user_span = st.number_input("Total Span (m)", 0.5, 30.0, 6.0, step=0.5)
    with col_g2: 
        Lb = st.number_input("Unbraced Length Lb (m)", 0.0, user_span, user_span, step=0.5)
    
    defl_denom = int(st.selectbox(
        "Serviceability Deflection Limit", 
        ["L/300", "L/360", "L/400", "L/500"], 
        index=1
    ).split("/")[1])

    # -----------------------------------------------
    # PRE-CALCULATE SHEAR CAPACITY (Sidebar Display)
    # -----------------------------------------------
    if is_lrfd:
        phi_v = 1.00
        V_n_pre = 0.60 * Fy * Aw
        V_cap_disp = phi_v * V_n_pre
        v_label = "ϕVn (LRFD)"
    else:
        omg_v = 1.50
        V_n_pre = 0.60 * Fy * Aw
        V_cap_disp = V_n_pre / omg_v
        v_label = "Vn/Ω (ASD)"

    # --- Connection Design Input Logic ---
    st.divider()
    st.subheader("🔩 Connection Settings")
    
    st.markdown(f"""
    <div class="sidebar-info">
        <div><b>Available Shear Capacity ({v_label}):</b> <br>
        <span style="font-size:1.3em; color:#1e40af; font-family:'Roboto Mono';">{V_cap_disp:,.0f} kg</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    link_conn = st.checkbox("🔗 Link with Beam Capacity", value=True, help="Automatically use a % of beam capacity for connection design.")
    if link_conn:
        conn_shear_pct = st.slider("% of Shear Capacity to Design For", 10, 100, 50, step=5)
        v_support_design = V_cap_disp * (conn_shear_pct / 100.0)
    else:
        v_support_design = st.number_input("Manual Design Shear (kg)", value=float(int(V_cap_disp*0.5)), step=100.0)

    # --- ECCENTRICITY REDUCTION CALCULATION ---
    st.markdown("---")
    st.write("📐 **Eccentric Load Adjustment**")
    
    ecc_e = st.number_input(
        "Eccentricity 'e' (mm)", 
        value=50, 
        step=5, 
        help="Distance from support face to bolt group centroid. Used to calculate torque and net force."
    )
    
    # Mathematical Model: Converting shear at support to shear at bolt group via equivalent uniform load reduction
    w_equiv_load = (2 * v_support_design) / (user_span if user_span > 0 else 1) 
    v_reduction = w_equiv_load * (ecc_e / 1000.0)
    v_at_bolt = v_support_design - v_reduction

    # Sidebar Force Visualization
    st.markdown(f"""
    <div style="background:#f1f5f9; border:1px solid #cbd5e1; border-radius:8px; padding:12px; margin-top:5px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
            <span style="color:#64748b; font-size:0.85em;">Reaction @ Support:</span>
            <span style="font-weight:700; color:#334155;">{v_support_design:,.0f} kg</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:5px; border-bottom:1px dashed #cbd5e1; padding-bottom:5px;">
             <span style="color:#ef4444; font-size:0.85em;">- Net Reduc. (w·e):</span>
             <span style="color:#ef4444; font-size:0.85em;">{v_reduction:,.0f} kg</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:5px;">
            <span style="color:#1e3a8a; font-weight:bold;">Net V @ Bolts:</span>
            <span style="background:#2563eb; color:white; padding:2px 8px; border-radius:4px; font-weight:bold; font-family:'Roboto Mono';">{v_at_bolt:,.0f} kg</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    use_reduced = st.checkbox("Apply Reduction to Design?", value=False)
    v_conn_final = v_at_bolt if use_reduced else v_support_design

    # --- Loads (Check Mode Only) ---
    w_load, p_load = 0.0, 0.0
    if is_check_mode:
        st.divider()
        st.subheader("⬇️ Design Loads")
        c_l1, c_l2 = st.columns(2)
        with c_l1: w_load = st.number_input("Uniform w (kg/m)", 0.0, 50000.0, 1000.0)
        with c_l2: p_load = st.number_input("Point P (kg)", 0.0, 100000.0, 0.0)

# ==========================================
# 4. CORE ENGINEERING LOGIC (AISC 360)
# ==========================================
# All calculations in kg and cm
L_cm = user_span * 100
Lb_cm = Lb * 100
E = E_mod

# --- 4.1 LTB LIMITS (AISC F2) ---
# Lp = 1.76 * ry * sqrt(E/Fy)
Lp_cm = 1.76 * ry * math.sqrt(E/Fy)

# Lr calculation (Complex Formula)
val_A = (J * 1.0) / (Sx * h0)
val_B = 6.76 * ((0.7 * Fy) / E)**2
Lr_cm = 1.95 * r_ts * (E / (0.7 * Fy)) * math.sqrt(val_A + math.sqrt(val_A**2 + val_B))

# --- 4.2 NOMINAL MOMENT CAPACITY (Mn) ---
Mp = Fy * Zx
Cb = 1.0 # Conservative assumption for Cb

if Lb_cm <= Lp_cm:
    Mn = Mp
    ltb_zone = "Zone 1 (Plastic)"
elif Lb_cm <= Lr_cm:
    # Inelastic LTB
    term1 = (Mp - 0.7 * Fy * Sx)
    term2 = ((Lb_cm - Lp_cm) / (Lr_cm - Lp_cm))
    Mn = min(Cb * (Mp - term1 * term2), Mp)
    ltb_zone = "Zone 2 (Inelastic)"
else:
    # Elastic LTB
    slend = (Lb_cm / r_ts)
    Fcr = (Cb * math.pi**2 * E) / (slend**2) * math.sqrt(1 + 0.078 * val_A * slend**2)
    Mn = min(Fcr * Sx, Mp)
    ltb_zone = "Zone 3 (Elastic)"

# --- 4.3 FACTORED/ALLOWABLE CAPACITIES ---
if is_lrfd:
    phi_b = 0.90
    V_cap = V_cap_disp 
    M_cap = (phi_b * Mn) / 100 # kg-m
    fact_w = 1.2 * w_load # Note: Using 1.2/1.6 simplified for tool
    fact_p = 1.6 * p_load
    method_str = "LRFD"
else:
    omg_b = 1.67
    V_cap = V_cap_disp 
    M_cap = (Mn / omg_b) / 100 # kg-m
    fact_w = w_load
    fact_p = p_load
    method_str = "ASD"

# --- 4.4 DEFLECTION LIMITS ---
d_allow = L_cm / defl_denom

# --- 4.5 DESIGN RATIO PROCESSING ---
if is_check_mode:
    # Interaction/Check Logic
    v_act = (fact_w * user_span / 2) + (fact_p / 2)
    m_act = (fact_w * user_span**2 / 8) + (fact_p * user_span / 4)
    
    # Service deflection (No load factors)
    d_unif = (5 * (w_load/100) * (L_cm**4)) / (384 * E * Ix)
    d_point = (p_load * (L_cm**3)) / (48 * E * Ix)
    d_act = d_unif + d_point
    
    ratio_v = v_act / V_cap
    ratio_m = m_act / M_cap
    ratio_d = d_act / d_allow
    gov_ratio = max(ratio_v, ratio_m, ratio_d)
    
    if gov_ratio == ratio_v: gov_cause = "Shear Strength"
    elif gov_ratio == ratio_m: gov_cause = "Flexural Strength (LTB)"
    else: gov_cause = "Deflection Serviceability"
    w_safe = 0
    
else:
    # Find Capacity Logic
    # 1. Moment limit
    w_safe_moment = (8 * M_cap) / (user_span**2 if user_span > 0 else 1)
    
    # 2. Shear limit
    w_safe_shear = (2 * V_cap) / (user_span if user_span > 0 else 1)
    
    # 3. Deflection limit
    w_serv_defl = (384 * E * Ix * d_allow) / (5 * (L_cm**4)) * 100
    w_safe_defl = w_serv_defl * 1.4 if is_lrfd else w_serv_defl
    
    w_safe = min(w_safe_shear, w_safe_moment, w_safe_defl)
    
    # Back-calculations
    v_act = (w_safe * user_span) / 2
    m_act = (w_safe * user_span**2) / 8
    
    ratio_v = w_safe / w_safe_shear
    ratio_m = w_safe / w_safe_moment
    ratio_d = w_safe / w_safe_defl
    
    w_safe_service = w_safe / 1.4 if is_lrfd else w_safe
    d_act = (5 * (w_safe_service/100) * (L_cm**4)) / (384 * E * Ix)
    gov_ratio = 1.00 
    
    if w_safe == w_safe_shear: gov_cause = "Shear Control"
    elif w_safe == w_safe_moment: gov_cause = "Flexural Control"
    else: gov_cause = "Deflection Control"

# ==========================================
# 5. DATA PACKAGING FOR TABS
# ==========================================
# Complex Context for Analysis Modules
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
    'vn': V_cap,  # Map for Report
    'mn': M_cap,  # Map for Report
    'v_act': v_act,
    'm_act': m_act,
    'ratio_v': ratio_v,
    'ratio_m': ratio_m,
    'ratio_d': ratio_d,
    'gov_ratio': gov_ratio,
    'gov_cause': gov_cause,
    'w_safe': w_safe,
    'd_act': d_act,
    'd_allow': d_allow,
    'defl_act': d_act, # Map for Report
    'defl_all': d_allow, # Map for Report
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
    'h0': h0,
    'h': h, # Adding raw dimensions
    'b': b,
    'tw': tw,
    'tf': tf
}

# Simplified Session State for Cross-Tab communication
st.session_state.res_dict = {
    'w_safe': w_safe,
    'cause': gov_cause, 
    'v_cap': V_cap, 
    'v_act': v_act,
    'm_cap': M_cap, 
    'm_act': m_act, 
    'mn_raw': Mn,
    'd_all': d_allow, 
    'd_act': d_act,
    'v_conn_design': v_conn_final, 
    'ltb_info': {
        'Lp': Lp_cm, 
        'Lr': Lr_cm, 
        'Lb': Lb_cm, 
        'Zone': ltb_zone, 
        'Cb': Cb
    }
}
st.session_state.cal_success = True

# ==========================================
# 6. TABBED UI RENDERING
# ==========================================
# Defining 5 Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Analysis & Graphs", 
    "🔩 Connection Detail", 
    "🛡️ LTB Insight", 
    "📝 Detailed Report",
    "🧱 Base Plate"
])

# --- TAB 1: PRIMARY ANALYSIS ---
with tab1:
    tab1_analysis.render(results_context)

# --- TAB 2: SHEAR CONNECTION ---
with tab2:
    if st.session_state.cal_success:
        st.info(f"⚡ **Force Vector Input:** {v_conn_final:,.0f} kg ")
        
        # User selection for connection type
        c_type = st.selectbox(
            "Connection Selection", 
            ["Fin Plate", "End Plate", "Double Angle"], 
            key='conn_type_selector_unique'
        )
        st.session_state.conn_type = c_type 
        
        section_data = {
            "name": sec_name, 
            "h": h, 
            "b": b, 
            "tw": tw, 
            "tf": tf
        }
        
        # Call External Design Module
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
        
        # บันทึกสถานะคร่าวๆ ลง Session (เพื่อส่งให้ Tab 4)
        st.session_state.v_design = {
            'type': c_type,
            'summary': f"Designed for Shear {v_conn_final:,.0f} kg ({method_str})",
            'pass': True 
        }

    else:
        st.warning("⚠️ Calculation pending. Please define section parameters.")

# --- TAB 3: LTB VISUALIZER ---
with tab3:
    tab3_ltb.render(results_context)

# --- TAB 4: CALCULATION REPORT ---
with tab4:
    if st.session_state.cal_success:
        # 🟢 แก้ไข: ส่ง dict ข้อมูล 2 ตัวตามที่ report_generator.py ต้องการ
        beam_data = results_context
        conn_data = st.session_state.get('v_design', {})
        
        # สร้าง Dummy Data กัน Error กรณี Tab 2 ยังไม่ถูกรัน
        if not conn_data:
            conn_data = {
                'type': st.session_state.conn_type,
                'summary': f"Pending design for V={v_conn_final:,.0f} kg",
                'pass': False
            }

        report_generator.render_report_tab(beam_data, conn_data)
    else:
        st.error("No data available for reporting.")

# --- TAB 5: BASE PLATE DESIGN ---
with tab5:
    if st.session_state.cal_success:
        st.markdown("### 🧱 Column Base Plate Design")
        st.markdown("""
        This module calculates the required thickness and dimensions for a base plate 
        based on the reaction forces calculated from the beam analysis.
        """)
        # Image for engineering context
        # 
        
        # Calling Tab 5 Module
        try:
            tab5_baseplate.render(results_context, v_conn_final)
        except Exception as e:
            st.error(f"Error in Base Plate Module: {e}")
            st.code(f"Debug: {results_context['h']} x {results_context['b']}")
    else:
        st.warning("Please complete the Beam Analysis in Tab 1 first.")

# ==========================================
# 7. FOOTER & METADATA
# ==========================================
st.divider()
col_f1, col_f2 = st.columns(2)
with col_f1:
    st.caption(f"Engine Status: Online | Method: {method_str} | Section: {sec_name}")
with col_f2:
    st.markdown("<div style='text-align:right;'><small>© 2026 Structural Insight Hybrid - Professional Edition</small></div>", unsafe_allow_html=True)

# End of app.py

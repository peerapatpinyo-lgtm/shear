import streamlit as st
import pandas as pd
import numpy as np
import math

# --- IMPORT MODULES ---
# ต้องมั่นใจว่ามีไฟล์ data_utils.py, connection_design.py, drawing_utils.py, calculation_report.py อยู่ในโฟลเดอร์เดียวกัน
try:
    import data_utils as db
    import connection_design as conn
    import drawing_utils as dwg
    import calculation_report as rep
except ImportError as e:
    st.error(f"⚠️ Error importing modules: {e}. Please make sure all 5 files are in the same directory.")
    st.stop()

# =============================================================================
# 1. PAGE CONFIG & STYLING
# =============================================================================
st.set_page_config(page_title="Beam Insight V14 Professional", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: #e9ecef; border-radius: 4px 4px 0 0; gap: 1px; padding-top: 10px;
    }
    .stTabs [aria-selected="true"] { background-color: #ffffff; border-top: 3px solid #007bff; color: #007bff; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; color: #333; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. SIDEBAR INPUTS
# =============================================================================
with st.sidebar:
    st.title("🏗️ Beam Insight V14")
    st.caption("Professional Structural Analysis")
    
    # 2.1 Design Method
    method = st.radio("Design Method", ["ASD (Allowable Stress)", "LRFD (Limit State)"])
    is_lrfd = "LRFD" in method
    
    st.divider()
    
    # 2.2 Project Info (for Report)
    with st.expander("📋 Project Information", expanded=False):
        proj_name = st.text_input("Project Name", "Warehouse Building A")
        eng_name = st.text_input("Engineer Name", "Eng. Somchai")
        
    # 2.3 Beam Properties
    st.subheader("1. Beam Configuration")
    sec_name = st.selectbox("Select Section", list(db.STEEL_DB.keys()), index=11) # Default H 400
    p = db.STEEL_DB[sec_name] # Load properties from DB
    
    span = st.number_input("Span Length (m)", value=6.0, step=0.5)
    
    c1, c2 = st.columns(2)
    with c1: Fy = st.number_input("Fy (ksc)", value=2500)
    with c2: E_mod = st.number_input("E (ksc)", value=2.04e6, format="%e")
    
    defl_limit = st.selectbox("Deflection Limit", [200, 240, 300, 360, 400], index=2)

    st.divider()

    # 2.4 Load Configuration
    st.subheader("2. Loading Condition")
    design_mode = st.radio("Input Mode", ["Auto (Max Capacity %)", "Manual (Input Load)"])
    
    target_pct = 0
    user_load_input = 0
    
    if design_mode == "Auto (Max Capacity %)":
        target_pct = st.slider("Target Capacity (%)", 10, 100, 80)
    else:
        user_load_input = st.number_input("Uniform Load (kg/m)", value=1000)
        
    st.divider()
    
    # 2.5 Connection Config
    st.subheader("3. Connection Type")
    conn_type = st.selectbox("Select Type", [
        "Fin Plate (Single Shear)", 
        "End Plate (Single Shear)", 
        "Double Angle (Double Shear)"
    ])

# =============================================================================
# 3. BEAM CALCULATION LOGIC (CORE ENGINE)
# =============================================================================
# Units: Length=cm, Force=kg, Stress=ksc
L_cm = span * 100

# 3.1 Properties
Ix = p['Ix']
Zx = p['Zx']
h = p['h']
tw = p['tw']
tf = p['tf']
w_self_kgm = p['w']

# 3.2 Capacities (Nominal & Allowable)
# --- Moment Capacity ---
Mn = Zx * Fy  # kg-cm (Simplified plastic moment)
if is_lrfd:
    M_cap = 0.90 * Mn  # Phi = 0.90
else:
    M_cap = Mn / 1.67  # Omega = 1.67

# --- Shear Capacity ---
Aw = h * tw
Vn = 0.60 * Fy * Aw # kg
if is_lrfd:
    V_cap = 1.00 * Vn # Phi = 1.00 for shear usually
else:
    V_cap = Vn / 1.50 # Omega = 1.50

# --- Deflection Limit ---
Delta_allow = L_cm / defl_limit

# 3.3 Find Max Safe Load (Reverse Calculation)
# Find w (kg/cm) that reaches limit
# 1. Moment Governs: M = wL^2/8 -> w = 8*M_cap / L^2
w_max_moment = (8 * M_cap) / (L_cm**2)

# 2. Shear Governs: V = wL/2 -> w = 2*V_cap / L
w_max_shear = (2 * V_cap) / L_cm

# 3. Deflection Governs: D = 5wL^4 / 384EI -> w = (D * 384EI) / 5L^4
w_max_defl = (Delta_allow * 384 * E_mod * Ix) / (5 * L_cm**4)

# Min w determines the safe load (kg/cm) -> convert to kg/m (*100)
w_safe_kgm = min(w_max_moment, w_max_shear, w_max_defl) * 100

# 3.4 Determine Actual Load to Apply
if design_mode == "Auto (Max Capacity %)":
    user_safe_load = w_safe_kgm * (target_pct / 100)
else:
    user_safe_load = user_load_input

# Include Self Weight? (Optional logic, let's assume included in user load for simplicity or add it)
total_load_kgm = user_safe_load # + w_self_kgm (Optional)

# 3.5 Calculate Actual Forces
w_apply_kg_cm = total_load_kgm / 100
m_act = (w_apply_kg_cm * L_cm**2) / 8  # kg-cm
v_act = (w_apply_kg_cm * L_cm) / 2     # kg
d_act = (5 * w_apply_kg_cm * L_cm**4) / (384 * E_mod * Ix) # cm

# 3.6 Ratios
ratio_m = m_act / M_cap
ratio_v = v_act / V_cap
ratio_d = d_act / Delta_allow
max_ratio = max(ratio_m, ratio_v, ratio_d)

# 3.7 Prepare Result Dictionary (The Source of previous Error)
beam_res = {
    'pass': max_ratio <= 1.0,
    'w_safe': total_load_kgm,
    
    'v_act': v_act, 
    'v_cap': V_cap, 
    'v_ratio': ratio_v,
    
    'm_act': m_act / 100,  # Convert to kg-m for display 
    'm_cap': M_cap / 100, 
    'm_ratio': ratio_m,
    
    'd_act': d_act, 
    'd_all': Delta_allow, 
    'd_ratio': ratio_d,
    
    'span': span
}

# Add Status Strings for Report
beam_res['v_status'] = "OK" if ratio_v <= 1 else "FAIL"
beam_res['v_class'] = "status-pass" if ratio_v <= 1 else "status-fail"
beam_res['m_status'] = "OK" if ratio_m <= 1 else "FAIL"
beam_res['m_class'] = "status-pass" if ratio_m <= 1 else "status-fail"
beam_res['d_status'] = "OK" if ratio_d <= 1 else "FAIL"
beam_res['d_class'] = "status-pass" if ratio_d <= 1 else "status-fail"

# =============================================================================
# 4. TABS & DISPLAY
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection Design", "💾 Load Table", "📝 Report"])

# --- TAB 1: BEAM ---
with tab1:
    st.markdown(f"### Analysis Result: **{sec_name}**")
    
    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Applied Load", f"{total_load_kgm:,.0f} kg/m", f"Max: {w_safe_kgm:,.0f}")
    m2.metric("Shear Ratio", f"{ratio_v:.2f}", f"{v_act:,.0f} / {V_cap:,.0f} kg", delta_color="inverse")
    m3.metric("Moment Ratio", f"{ratio_m:.2f}", f"{m_act/100:,.0f} / {M_cap/100:,.0f} kg-m", delta_color="inverse")
    m4.metric("Deflection", f"{ratio_d:.2f}", f"{d_act:.2f} / {Delta_allow:.2f} cm", delta_color="inverse")

    # Progress Bar
    st.write("#### Utilization")
    bar_color = "green" if max_ratio <= 0.8 else "orange" if max_ratio <= 1.0 else "red"
    st.markdown(f"""
        <div style="background-color:#e9ecef; border-radius:10px;">
            <div style="width:{min(max_ratio*100, 100)}%; background-color:{bar_color}; height:20px; border-radius:10px; text-align:center; color:white; font-size:12px;">
                {max_ratio*100:.1f}%
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- TAB 2: CONNECTION ---
with tab2:
    # เรียกใช้ Module Connection Design
    # ส่ง v_act (Shear Force) ไปออกแบบจุดต่อ
    conn_result = conn.render_connection_tab(
        V_design=v_act, 
        method=method, 
        is_lrfd=is_lrfd, 
        section_data=p, 
        conn_type=conn_type
    )

# --- TAB 3: LOAD TABLE ---
with tab3:
    st.markdown("### 🏗️ Load Capacity Table (Approx.)")
    # Generate simple table for varying spans
    span_ranges = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12]
    table_data = []
    
    for s_test in span_ranges:
        L_t = s_test * 100
        w_m = (8 * M_cap) / (L_t**2) * 100
        w_v = (2 * V_cap) / L_t * 100
        w_d = (Delta_allow * 384 * E_mod * Ix) / (5 * L_t**4) * 100 # Note: Delta_allow uses s_test logic if recalculated
        
        # Simplified: Use fixed Deflection limit L/360 for table
        d_limit_test = L_t / defl_limit
        w_d_test = (d_limit_test * 384 * E_mod * Ix) / (5 * L_t**4) * 100
        
        safe_w = min(w_m, w_v, w_d_test)
        table_data.append({
            "Span (m)": s_test,
            "Max Load (kg/m)": int(safe_w),
            "Control": "Moment" if safe_w==w_m else "Shear" if safe_w==w_v else "Deflection"
        })
    
    df_load = pd.DataFrame(table_data)
    st.dataframe(df_load, use_container_width=True)

# --- TAB 4: REPORT ---
with tab4:
    # เรียกใช้ Module Report Generator
    if conn_result:
        project_info = {
            'name': proj_name, 
            'eng': eng_name, 
            'sec': sec_name, 
            'method': method
        }
        rep.render_report_tab(project_info, beam_res, conn_result)
    else:
        st.warning("⚠️ Please configure the Connection Design in Tab 2 to generate the full report.")

# Footer
st.markdown("---")
st.caption("Beam Insight V14 | Built with Streamlit & Python")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================
# 1. IMPORT CUSTOM MODULES
# ==========================================
try:
    import steel_db             # ฐานข้อมูลเหล็ก
    import connection_design    # โมดูลออกแบบจุดต่อ (Tab 2)
    import calculation_report   # โมดูลสร้างรายงาน (Tab 4)
except ImportError as e:
    st.error(f"⚠️ Modules missing: {e}. Please ensure steel_db.py, connection_design.py, and calculation_report.py are in the same folder.")
    st.stop()

# ==========================================
# 2. PAGE CONFIG & SESSION STATE
# ==========================================
st.set_page_config(page_title="Beam Insight V17", layout="wide", page_icon="🏗️")

if 'cal_success' not in st.session_state:
    st.session_state.cal_success = False

# ==========================================
# 3. CSS STYLING
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Roboto+Mono:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
    
    /* Card Styles */
    .detail-card { background: white; border-radius: 12px; padding: 20px; border: 1px solid #e2e8f0; border-top: 5px solid #3b82f6; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .status-badge { padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 12px; float: right; text-transform: uppercase; }
    .pass { background-color: #dcfce7; color: #166534; }
    .fail { background-color: #fee2e2; color: #991b1b; }
    
    .highlight-card { background: linear-gradient(135deg, #f8fafc 0%, #eff6ff 100%); padding: 20px; border-radius: 15px; border: 1px solid #cbd5e1; margin-bottom: 20px; border-left: 6px solid #2563eb; }
    .big-num { color: #1e40af; font-size: 36px; font-weight: 800; font-family: 'Roboto Mono', monospace; }
    .sub-text { color: #64748b; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f1f5f9; border-radius: 8px 8px 0 0; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { background-color: #ffffff; border-bottom: 2px solid #2563eb; color: #2563eb; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SIDEBAR INPUTS
# ==========================================
with st.sidebar:
    st.title("🏗️ Beam Insight V17")
    st.caption("Integrated Beam & Connection Design")
    st.divider()
    
    # --- 4.1 Global Settings ---
    st.subheader("⚙️ Global Settings")
    method = st.radio("Design Method", ["ASD", "LRFD"])
    is_lrfd = (method == "LRFD")
    
    # --- 4.2 Material ---
    st.markdown("**Material Grade**")
    grade_map = {"SS400": 2450, "SM520": 3550, "A36": 2500}
    grade_name = st.selectbox("Steel Grade", list(grade_map.keys()))
    Fy = grade_map[grade_name]
    E_mod = 2.04e6 
    
    st.divider()

    # --- 4.3 Section Selection (From steel_db) ---
    st.subheader("📦 Beam Section")
    input_mode = st.radio("Source", ["📚 Database", "✏️ Custom"], horizontal=True, label_visibility="collapsed")
    
    if "Database" in input_mode:
        sec_list = steel_db.get_section_list()
        # Default index to H-400
        def_idx = 13 if len(sec_list) > 13 else 0
        sec_name = st.selectbox("Select Size", sec_list, index=def_idx)
        props = steel_db.get_properties(sec_name)
    else:
        st.caption("Custom Input (mm)")
        c1, c2 = st.columns(2)
        h_in = c1.number_input("Depth", 100, 2000, 400)
        b_in = c2.number_input("Width", 50, 600, 200)
        c3, c4 = st.columns(2)
        tw_in = c3.number_input("Web t", 3.0, 50.0, 8.0)
        tf_in = c4.number_input("Flange t", 3.0, 50.0, 13.0)
        sec_name = f"Custom {int(h_in)}x{int(b_in)}"
        props = {"h": h_in, "b": b_in, "tw": tw_in, "tf": tf_in, "Ix": 0, "Zx": 0} # Ix/Zx calculated later for custom

    # Prepare Data Dictionary for Tab 2
    section_data = {
        "name": sec_name,
        "h": float(props['h']),
        "b": float(props['b']),
        "tw": float(props['tw']),
        "tf": float(props['tf'])
    }

    # --- 4.4 Beam Geometry ---
    st.markdown("**Geometry**")
    L_span = st.number_input("Span Length (m)", 1.0, 20.0, 6.0, step=0.5)
    defl_limit = st.selectbox("Deflection Limit", ["L/300", "L/360", "L/400"], index=1)
    denom = int(defl_limit.split("/")[1])

    # --- 4.5 Connection Scope ---
    st.divider()
    st.subheader("🔩 Connection Scope")
    load_mode = st.radio("Load Basis", ["Actual Load (แรงจริง)", "Fixed % Capacity"])
    
    target_pct = 0
    if "Fixed" in load_mode:
        target_pct = st.slider("% of Shear Cap", 50, 100, 75)

# ==========================================
# 5. CORE CALCULATION (BEAM ANALYSIS)
# ==========================================
# Calculate Properties if Custom (Approximate)
h, b, tw, tf = section_data['h'], section_data['b'], section_data['tw'], section_data['tf']
Ix = props.get('Ix', 0)
Zx = props.get('Zx', 0)

if Ix == 0: # Custom Calc
    Ix = (b * h**3 - (b - tw) * (h - 2*tf)**3) / 120000 # cm4
    Zx = ((b * h**2) / 6000) # cm3 approx

# Capacities
Aw = (h/10) * (tw/10) # cm2
if is_lrfd:
    M_cap = 0.90 * Fy * Zx 
    V_cap = 1.00 * 0.60 * Fy * Aw
    load_label = "Factored Load (Wu)"
else:
    M_cap = 0.60 * Fy * Zx 
    V_cap = 0.40 * Fy * Aw
    load_label = "Safe Load (Wa)"

# Back-Calculate Max Distributed Load (w) from Limits
L_cm = L_span * 100
w_shear = (2 * V_cap / L_cm) * 100 # kg/m
w_moment = (8 * M_cap / (L_cm**2)) * 100 # kg/m
w_defl = ((L_cm/denom) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100 # kg/m

w_safe = min(w_shear, w_moment, w_defl)
gov_cause = "Shear" if w_safe == w_shear else ("Moment" if w_safe == w_moment else "Deflection")

# Actual Forces based on Safe Load
V_act = w_safe * L_span / 2
M_act = w_safe * L_span**2 / 8
D_act = (5 * (w_safe/100) * (L_cm**4)) / (384 * E_mod * Ix)
D_allow = L_cm / denom

# Determine Load for Connection Design
if "Fixed" in load_mode:
    V_design = V_cap * (target_pct / 100.0)
else:
    V_design = V_act

st.session_state.cal_success = True

# ==========================================
# 6. UI TABS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection Design", "💾 Load Table", "📝 Report"])

# --- TAB 1: BEAM ANALYSIS ---
with tab1:
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        st.subheader(f"Analysis Result: {sec_name}")
        
        # Highlight Card
        cause_color = "#ef4444" if gov_cause == "Shear" else ("#f59e0b" if gov_cause == "Moment" else "#3b82f6")
        st.markdown(f"""
        <div class="highlight-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div class="sub-text">Maximum Safe Load ({load_label})</div>
                    <div class="big-num">{w_safe:,.0f} <span style="font-size:20px; color:#64748b;">kg/m</span></div>
                </div>
                <div style="text-align:right;">
                    <div class="sub-text">Controlled By</div>
                    <div style="background:{cause_color}; color:white; padding:5px 15px; border-radius:20px; font-weight:bold; display:inline-block; margin-top:5px;">
                        {gov_cause}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Ratios
        c1, c2, c3 = st.columns(3)
        def check_card(title, act, cap, unit, icon):
            ratio = act/cap
            status = "pass" if ratio <= 1.0 else "fail"
            st.markdown(f"""
            <div class="detail-card">
                <span class="status-badge {status}">{status.upper()}</span>
                <div style="font-weight:bold; color:#475569;">{icon} {title}</div>
                <div style="font-size:24px; font-weight:bold; color:#1e293b; margin-top:5px;">
                    {act:,.0f} <span style="font-size:14px; color:#94a3b8;">/ {cap:,.0f} {unit}</span>
                </div>
                <div style="font-size:12px; color:#64748b; margin-top:5px;">Ratio: <b>{ratio:.2f}</b></div>
            </div>
            """, unsafe_allow_html=True)

        with c1: check_card("Shear", V_act, V_cap, "kg", "✂️")
        with c2: check_card("Moment", M_act, M_cap/100, "kg-m", "🔄")
        with c3: check_card("Deflection", D_act, D_allow, "cm", "📉")

    with col_side:
        st.markdown("**Capacity Envelope**")
        # Graph
        x_rng = np.linspace(2, 12, 50)
        y_sh = [(2*V_cap/(x*100))*100 for x in x_rng]
        y_mo = [(8*M_cap/((x*100)**2))*100 for x in x_rng]
        y_df = [((x*100/denom)*384*E_mod*Ix)/(5*((x*100)**4))*100 for x in x_rng]
        y_safe = [min(s, m, d) for s,m,d in zip(y_sh, y_mo, y_df)]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x_rng, y=y_safe, fill='tozeroy', name='Safe Zone', line=dict(color='#3b82f6')))
        fig.add_trace(go.Scatter(x=[L_span], y=[w_safe], mode='markers', marker=dict(size=10, color='red'), name='Design'))
        fig.update_layout(height=300, margin=dict(l=20,r=20,t=10,b=20), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: CONNECTION DESIGN ---
with tab2:
    if st.session_state.cal_success:
        # ส่งค่าไปให้ Module connection_design ทำงาน
        # หมายเหตุ: เราไม่ส่ง bolt inputs เพราะ Module นั้นจัดการ UI เองแล้ว
        connection_design.render_connection_tab(
            V_design_from_tab1=V_design,
            default_bolt_size="M20",
            method=method,
            is_lrfd=is_lrfd,
            section_data=section_data, # <--- ส่งข้อมูลเหล็กจาก Sidebar ไป
            conn_type="Single Plate (Shear Tab)",
            default_bolt_grade="A325",
            default_mat_grade=grade_name
        )
    else:
        st.warning("Please configure beam analysis first.")

# --- TAB 3: LOAD TABLE ---
with tab3:
    st.markdown("### 📋 Span vs Capacity Table")
    
    t_spans = np.arange(2.0, 12.5, 0.5)
    data = []
    for s in t_spans:
        l_cm = s * 100
        w_v = (2 * V_cap / l_cm) * 100
        w_m = (8 * M_cap / (l_cm**2)) * 100
        w_d = ((l_cm/denom) * 384 * E_mod * Ix) / (5 * (l_cm**4)) * 100
        w_lim = min(w_v, w_m, w_d)
        cause = "Shear" if w_lim == w_v else ("Moment" if w_lim == w_m else "Deflection")
        data.append([s, w_lim, cause])
    
    df = pd.DataFrame(data, columns=["Span (m)", f"Max Load {load_label} (kg/m)", "Control"])
    st.dataframe(df.style.format({f"Max Load {load_label} (kg/m)": "{:,.0f}", "Span (m)": "{:.1f}"}), use_container_width=True)

# --- TAB 4: REPORT ---
with tab4:
    # Dummy Bolt Data for report (Real data is inside Tab 2 logic, 
    # ideally calculation_report should be called from Tab 2, 
    # but here we generate a Beam Summary Report)
    
    st.markdown("### 📝 Beam Analysis Report")
    st.markdown(f"""
    **Project:** Steel Beam Design V17
    
    ---
    **1. Design Parameters**
    * Method: {method}
    * Material: {grade_name} (Fy = {Fy} ksc)
    * Section: **{sec_name}**
    
    **2. Analysis Results (Span = {L_span} m)**
    * Safe Load Capacity: **{w_safe:,.0f} kg/m**
    * Governing Case: **{gov_cause}**
    
    **3. Internal Forces**
    * Shear Force ($V_u$): {V_act:,.0f} kg
    * Bending Moment ($M_u$): {M_act:,.0f} kg-m
    * Deflection ($\Delta$): {D_act:.2f} cm (Allow: {D_allow:.2f} cm)
    
    ---
    *For Connection Design Report, please see the 'Full Report' sub-tab inside 'Connection Design' tab.*
    """)

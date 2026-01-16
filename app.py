import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================
# 1. IMPORT CUSTOM MODULES
# ==========================================
try:
    import steel_db             # ฐานข้อมูลเหล็ก (จากไฟล์ที่ให้ไป)
    import connection_design    # คำนวณจุดต่อ (จากไฟล์ที่ให้ไป)
    import calculation_report   # สร้างรายงาน (จากไฟล์ที่ให้ไป)
except ImportError as e:
    st.error(f"⚠️ Critical Error: Modules missing ({e}). Ensure steel_db.py, connection_design.py, calculation_report.py exist.")
    st.stop()

# ==========================================
# 2. PAGE CONFIG & SESSION STATE
# ==========================================
st.set_page_config(page_title="Beam Insight V17 (Full)", layout="wide", page_icon="🏗️")

if 'cal_success' not in st.session_state:
    st.session_state.cal_success = False
if 'res_dict' not in st.session_state:
    st.session_state.res_dict = {}

# ==========================================
# 3. CSS STYLING (V17 ORIGINAL STYLE)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Roboto+Mono:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
    
    /* Custom Card Styles */
    .detail-card { background: white; border-radius: 12px; padding: 20px; border: 1px solid #e5e7eb; border-top: 6px solid #2563eb; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .status-badge { padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 12px; float: right; text-transform: uppercase; }
    .pass { background-color: #dcfce7; color: #166534; }
    .fail { background-color: #fee2e2; color: #991b1b; }
    
    .highlight-card { background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%); padding: 25px; border-radius: 20px; border-left: 8px solid #2563eb; box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08); margin-bottom: 25px; border: 1px solid #e5e7eb; }
    .big-num { color: #1e40af; font-size: 42px; font-weight: 800; font-family: 'Roboto Mono', monospace; }
    .sub-text { color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #f8fafc; border-radius: 8px 8px 0 0; padding: 10px 20px; font-weight: 600; color: #64748b; }
    .stTabs [aria-selected="true"] { background-color: #ffffff; border-bottom: 3px solid #2563eb; color: #2563eb; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SIDEBAR INPUTS
# ==========================================
with st.sidebar:
    st.title("🏗️ Beam Insight V17")
    st.caption("Full Integrated Version")
    st.divider()
    
    # --- 4.1 Global Settings ---
    method = st.radio("Method", ["ASD (Allowable Stress)", "LRFD (Limit State)"])
    is_lrfd = True if "LRFD" in method else False
    
    st.subheader("🛠️ Material Grade")
    grade_opts = {"SS400 (Fy 2450)": 2450, "SM520 (Fy 3550)": 3550, "A36 (Fy 2500)": 2500}
    grade_choice = st.selectbox("Steel Grade", list(grade_opts.keys()))
    Fy = grade_opts[grade_choice]
    E_mod = 2.04e6 
    
    # --- 4.2 Section Selection (Integrated DB) ---
    st.subheader("📦 Section Selection")
    input_mode = st.radio("Source", ["📚 Standard Database", "✏️ Custom Input"], horizontal=True, label_visibility="collapsed")
    
    if "Standard" in input_mode:
        sec_list = steel_db.get_section_list()
        sec_name = st.selectbox("Size (JIS/SYS)", sec_list, index=13) 
        props = steel_db.get_properties(sec_name)
        h, b = float(props['h']), float(props['b'])
        tw, tf = float(props['tw']), float(props['tf'])
        
        # Calculate Prop
        Ix = (b * h**3 - (b - tw) * (h - 2*tf)**3) / 120000 
        Zx = ((b * h**2) / 6000) 
    else:
        c1, c2 = st.columns(2)
        h = c1.number_input("Depth (mm)", 100.0, 2000.0, 400.0)
        b = c2.number_input("Width (mm)", 50.0, 600.0, 200.0)
        c3, c4 = st.columns(2)
        tw = c3.number_input("Web t (mm)", 3.0, 50.0, 8.0)
        tf = c4.number_input("Flange t (mm)", 3.0, 50.0, 13.0)
        sec_name = f"Custom H-{int(h)}x{int(b)}"
        Ix = (b * h**3 - (b - tw) * (h - 2*tf)**3) / 120000 
        Zx = ((b * h**2) / 6000)

    # --- 4.3 Geometry ---
    st.divider()
    user_span = st.number_input("Span Length (m)", 1.0, 30.0, 6.0, step=0.5)
    defl_ratio = st.selectbox("Deflection Limit", ["L/300", "L/360", "L/400"], index=1)
    defl_denom = int(defl_ratio.split("/")[1])
    
    # --- 4.4 Connection Scope ---
    st.subheader("🔩 Connection Scope")
    design_mode = st.radio("Load Basis:", ["Actual Load (แรงจริง)", "Fixed % Capacity (% หน้าตัด)"])
    if "Fixed" in design_mode:
        target_pct = st.slider("% of Shear Capacity", 50, 100, 75)
    else:
        target_pct = 0

# ==========================================
# 5. CORE LOGIC (BEAM ANALYSIS)
# ==========================================
Aw = (h/10) * (tw/10) # cm2
if is_lrfd:
    M_cap = 0.90 * Fy * Zx 
    V_cap = 1.00 * 0.60 * Fy * Aw
    label_load = "Factored Load (Wu)"
else:
    M_cap = 0.60 * Fy * Zx 
    V_cap = 0.40 * Fy * Aw
    label_load = "Safe Load (Wa)"

# Back-Calculate Max Distributed Load (w)
L_cm = user_span * 100
w_shear = (2 * V_cap / L_cm) * 100
w_moment = (8 * M_cap / (L_cm**2)) * 100
w_defl = ((L_cm/defl_denom) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100

w_safe = min(w_shear, w_moment, w_defl)
gov_cause = "Shear" if w_safe == w_shear else ("Moment" if w_safe == w_moment else "Deflection")

# Actual Forces
v_act = w_safe * user_span / 2
m_act = w_safe * user_span**2 / 8
d_act = (5 * (w_safe/100) * (L_cm**4)) / (384 * E_mod * Ix)
d_allow = L_cm / defl_denom

# Connection Load
if "Fixed" in design_mode:
    v_conn_design = V_cap * (target_pct / 100.0)
else:
    v_conn_design = v_act

section_data = {"name": sec_name, "h": h, "b": b, "tw": tw, "tf": tf}
st.session_state.cal_success = True

# Store Results for Report (Tab 4)
st.session_state.res_dict = {
    'w_safe': w_safe, 'cause': gov_cause,
    'v_cap': V_cap, 'v_act': v_act,
    'm_cap': M_cap, 'm_act': m_act,
    'd_all': d_allow, 'd_act': d_act,
    'v_conn_design': v_conn_design
}

# ==========================================
# 6. UI RENDERING
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection Detail", "💾 Load Table", "📝 Report"])

# --- TAB 1: BEAM ANALYSIS (FULL RESTORATION) ---
with tab1:
    st.subheader(f"Engineering Analysis: {sec_name}")
    
    # 1. Highlight Card
    cause_color = "#dc2626" if gov_cause == "Shear" else ("#d97706" if gov_cause == "Moment" else "#059669")
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><span class="sub-text">Maximum Allowed {label_load}</span><br>
                <span class="big-num">{w_safe:,.0f}</span> <span style="font-size:20px; color:#4b5563;">kg/m</span></div>
            <div style="text-align: right;"><span class="sub-text">Governing Limit</span><br>
                <span style="font-size: 20px; font-weight:bold; color:{cause_color}; background-color:{cause_color}15; padding: 6px 15px; border-radius:15px; border: 1px solid {cause_color}30;">{gov_cause.upper()}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Detailed Checks with LaTeX (RESTORED)
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
        # EXPANDER FOR LATEX (Restore V17 Feature)
        with st.expander(f"👁️ View {title} Calculation Steps"):
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
            fr"V_{{act}} = \frac{{w \cdot L}}{{2}} = \frac{{{w_safe:,.0f} \cdot {user_span}}}{{2}} = {v_act:,.0f} \text{{ kg}}",
            fr"Ratio = \frac{{{v_act:,.0f}}}{{{V_cap:,.0f}}} = {v_act/V_cap:.3f}"
        )
    with c2:
        render_check_ratio_with_w(
            "Moment Check", m_act, (M_cap/100), "M/M_cap",
            fr"w_{{limit}} = \frac{{8 \cdot M_{{cap}}}}{{L^2}} = \frac{{8 \cdot {M_cap:,.0f}}}{{{L_cm_disp:,.0f}^2}} \cdot 100 = {w_moment:,.0f} \text{{ kg/m}}",
            fr"M_{{act}} = \frac{{w \cdot L^2}}{{8}} = \frac{{{w_safe:,.0f} \cdot {user_span}^2}}{{8}} = {m_act:,.0f} \text{{ kg.m}}",
            fr"Ratio = \frac{{{m_act:,.0f}}}{{{M_cap/100:,.0f}}} = {m_act/(M_cap/100):.3f}"
        )
    with c3:
        render_check_ratio_with_w(
            "Deflection Check", d_act, d_allow, "Δ/Δ_allow",
            fr"w_{{limit}} = \frac{{384 E I \Delta_{{all}}}}{{5 L^4}} = \frac{{384 \cdot 2.04 \cdot 10^6 \cdot {int(Ix)} \cdot {d_allow:.2f}}}{{5 \cdot {L_cm_disp:,.0f}^4}} \cdot 100 = {w_defl:,.0f} \text{{ kg/m}}",
            fr"\Delta_{{act}} = \frac{{5 w L^4}}{{384 E I}} = {d_act:.3f} \text{{ cm}}",
            fr"Ratio = \frac{{{d_act:.3f}}}{{{d_allow:.3f}}} = {d_act/d_allow:.3f}"
        )

    # 3. Envelope Graph
    st.markdown("### 📈 Capacity Envelope")
    spans = np.linspace(2, 12, 60)
    data_y = []
    for s in spans:
        l_c = s*100
        wv = (2*V_cap/l_c)*100
        wm = (8*M_cap/(l_c**2))*100
        wd = ((l_c/defl_denom)*384*E_mod*Ix)/(5*(l_c**4))*100
        data_y.append(min(wv, wm, wd))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans, y=data_y, fill='tozeroy', name='Safe Load', line=dict(color='#2563eb', width=3)))
    fig.add_trace(go.Scatter(x=[user_span], y=[w_safe], mode='markers+text', text=[f"{w_safe:,.0f}"], textposition="top right", marker=dict(color='red', size=12, symbol='star'), name='Current Design'))
    fig.update_layout(height=350, margin=dict(t=20, b=20, l=40, r=20), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: CONNECTION DETAIL (RESTORED 3 TYPES) ---
with tab2:
    if st.session_state.cal_success:
        
        # 1. Connection Type Selector (RESTORED HERE)
        st.markdown("##### ⚙️ Connection Configuration")
        c_type_col, c_dummy = st.columns([1,2])
        with c_type_col:
            conn_type_select = st.selectbox(
                "Select Connection Type", 
                ["Fin Plate (Shear Tab)", "End Plate (Coming Soon)", "Double Angle (Coming Soon)"]
            )
            
        # 2. Design Info Header
        if "Fixed" in design_mode:
            st.info(f"ℹ️ Designing **{conn_type_select}** for **{target_pct}% of Shear Capacity** = **{v_conn_design:,.0f} kg**")
        else:
            st.success(f"ℹ️ Designing **{conn_type_select}** for **Actual Shear Force** = **{v_conn_design:,.0f} kg**")
            
        # 3. Call Calculation Module
        # Note: Logic ส่วนใหญ่ใน connection_design.py รองรับ Fin Plate เป็นหลัก
        # แต่เราส่ง String ประเภทไปให้ได้
        connection_design.render_connection_tab(
            V_design_from_tab1=v_conn_design,
            default_bolt_size="M20",
            method=method,
            is_lrfd=is_lrfd,
            section_data=section_data,
            conn_type=conn_type_select,  # ส่งค่าที่เลือกไป
            default_bolt_grade="A325",
            default_mat_grade=grade_choice
        )
    else:
        st.warning("Please configure analysis first.")

# --- TAB 3: LOAD TABLE ---
with tab3:
    st.subheader("📋 Span vs Capacity Table")
    tbl_spans = np.arange(2.0, 15.0, 1.0)
    data_rows = []
    for s in tbl_spans:
        lc = s*100
        wv = (2*V_cap/lc)*100
        wm = (8*M_cap/(lc**2))*100
        wd = ((lc/defl_denom)*384*E_mod*Ix)/(5*(lc**4))*100
        w_lim = min(wv, wm, wd)
        cause = "Shear" if w_lim == wv else ("Moment" if w_lim == wm else "Deflection")
        data_rows.append([s, w_lim, cause])
    
    df = pd.DataFrame(data_rows, columns=["Span (m)", "Max Load (kg/m)", "Control"])
    st.dataframe(df.style.format({"Max Load (kg/m)": "{:,.0f}", "Span (m)": "{:.1f}"}), use_container_width=True)

# --- TAB 4: SUMMARY REPORT (FULL RESTORED) ---
with tab4:
    st.subheader("📝 Full Calculation Report")
    
    # Construct Bolt Data for Report (Mockup from Defaults if not fully set)
    # ในความเป็นจริงค่าเหล่านี้ควรดึงมาจาก state ของ Tab 2 แต่เพื่อกัน error ในการ generate report
    bolt_data_rpt = {
        'size': 'M20', 
        'qty': 'See Connection Tab', 
        'cap': 'See Connection Tab', 
        'type': 'Bearing', 
        'grade': 'A325'
    }

    # เรียกใช้ Module calculation_report เพื่อสร้าง Report เต็มรูปแบบ
    try:
        # ใช้ res_dict ที่เก็บไว้ตอนคำนวณ Tab 1
        calculation_report.render_report_tab(
            method=method,
            is_lrfd=is_lrfd,
            section_name=sec_name,
            grade=grade_choice,
            section_params={'h':h, 'b':b, 'tw':tw, 'tf':tf, 'Ix':Ix, 'Zx':Zx},
            res_dict=st.session_state.res_dict,
            bolt_data=bolt_data_rpt
        )
    except Exception as e:
        st.error(f"Error generating report: {e}")
        st.markdown("Please check if `calculation_report.py` has `render_report_tab` function.")

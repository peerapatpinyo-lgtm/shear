import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================
# 1. IMPORT CUSTOM MODULES
# ==========================================
try:
    import steel_db             # ฐานข้อมูลเหล็ก
    import connection_design    # คำนวณจุดต่อ
    import calculation_report   # สร้างรายงาน (แก้ Error Tab 4)
except ImportError as e:
    st.error(f"⚠️ Critical Error: Modules missing ({e}). Please ensure steel_db.py, connection_design.py, and calculation_report.py are in the folder.")
    st.stop()

# ==========================================
# 2. PAGE CONFIG & SESSION STATE
# ==========================================
st.set_page_config(page_title="Beam Insight V17 (Fixed)", layout="wide", page_icon="🏗️")

if 'cal_success' not in st.session_state:
    st.session_state.cal_success = False
if 'res_dict' not in st.session_state:
    st.session_state.res_dict = {}

# ==========================================
# 3. CSS STYLING (Original V17)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Roboto+Mono:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
    
    .detail-card { background: white; border-radius: 12px; padding: 20px; border: 1px solid #e5e7eb; border-top: 6px solid #2563eb; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .status-badge { padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 12px; float: right; text-transform: uppercase; }
    .pass { background-color: #dcfce7; color: #166534; }
    .fail { background-color: #fee2e2; color: #991b1b; }
    
    .highlight-card { background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%); padding: 25px; border-radius: 20px; border-left: 8px solid #2563eb; box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08); margin-bottom: 25px; border: 1px solid #e5e7eb; }
    .big-num { color: #1e40af; font-size: 42px; font-weight: 800; font-family: 'Roboto Mono', monospace; }
    .sub-text { color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; }
    
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
    st.divider()
    
    # --- Global Settings ---
    method = st.radio("Method", ["ASD (Allowable Stress)", "LRFD (Limit State)"])
    is_lrfd = True if "LRFD" in method else False
    
    st.subheader("🛠️ Material Grade")
    grade_opts = {"SS400 (Fy 2450)": 2450, "SM520 (Fy 3550)": 3550, "A36 (Fy 2500)": 2500}
    grade_choice = st.selectbox("Steel Grade", list(grade_opts.keys()))
    Fy = grade_opts[grade_choice]
    E_mod = 2.04e6 
    
    # --- Section Selection ---
    st.subheader("📦 Section Selection")
    input_mode = st.radio("Source", ["📚 Standard Database", "✏️ Custom Input"], horizontal=True, label_visibility="collapsed")
    
    if "Standard" in input_mode:
        sec_list = steel_db.get_section_list()
        sec_name = st.selectbox("Size (JIS/SYS)", sec_list, index=13) 
        props = steel_db.get_properties(sec_name)
        h, b, tw, tf = float(props['h']), float(props['b']), float(props['tw']), float(props['tf'])
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

    # --- Geometry ---
    st.divider()
    user_span = st.number_input("Span Length (m)", 1.0, 30.0, 6.0, step=0.5)
    defl_ratio = st.selectbox("Deflection Limit", ["L/300", "L/360", "L/400"], index=1)
    defl_denom = int(defl_ratio.split("/")[1])
    
    # --- Connection Scope ---
    st.subheader("🔩 Connection Scope")
    design_mode = st.radio("Load Basis:", ["Actual Load (แรงจริง)", "Fixed % Capacity (% หน้าตัด)"])
    if "Fixed" in design_mode:
        target_pct = st.slider("% of Shear Capacity", 50, 100, 75)
    else:
        target_pct = 0

# ==========================================
# 5. CORE LOGIC
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

# Back-Calculation Logic
L_cm = user_span * 100
w_shear = (2 * V_cap / L_cm) * 100
w_moment = (8 * M_cap / (L_cm**2)) * 100
w_defl = ((L_cm/defl_denom) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100

w_safe = min(w_shear, w_moment, w_defl)
gov_cause = "Shear" if w_safe == w_shear else ("Moment" if w_safe == w_moment else "Deflection")

v_act = w_safe * user_span / 2
m_act = w_safe * user_span**2 / 8
d_act = (5 * (w_safe/100) * (L_cm**4)) / (384 * E_mod * Ix)
d_allow = L_cm / defl_denom

# Connection Load
v_conn_design = V_cap * (target_pct / 100.0) if "Fixed" in design_mode else v_act

st.session_state.cal_success = True
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

# --- TAB 1: BEAM ANALYSIS (GRAPH RESTORED) ---
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

    # 2. Detailed Checks
    def render_check(title, act, lim, ratio_label, eq_w, eq_act, eq_ratio):
        ratio = act / lim
        is_pass = ratio <= 1.01 
        status = "pass" if is_pass else "fail"
        color = "#10b981" if is_pass else "#ef4444"
        st.markdown(f"""
        <div class="detail-card" style="border-top-color: {color}">
            <span class="status-badge {status}">{status.upper()}</span>
            <h4 style="margin:0; color:#374151;">{title}</h4>
            <div style="margin-top:10px;">
                <small style="color:#6b7280;">Ratio ({ratio_label}):</small>
                <div style="font-size:24px; font-weight:700; color:{color};">{ratio:.3f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander(f"View Calculation Steps"):
            st.latex(eq_w)
            st.latex(eq_act)
            st.latex(eq_ratio)

    c1, c2, c3 = st.columns(3)
    L_cm_disp = user_span * 100
    with c1: render_check("Shear Check", v_act, V_cap, "V/Vn", fr"w_{{lim}} = {w_shear:,.0f}", fr"V_{{act}} = {v_act:,.0f}", fr"Ratio = {v_act/V_cap:.3f}")
    with c2: render_check("Moment Check", m_act, M_cap/100, "M/Mn", fr"w_{{lim}} = {w_moment:,.0f}", fr"M_{{act}} = {m_act:,.0f}", fr"Ratio = {m_act/(M_cap/100):.3f}")
    with c3: render_check("Deflection Check", d_act, d_allow, "Δ/Δall", fr"w_{{lim}} = {w_defl:,.0f}", fr"\Delta_{{act}} = {d_act:.3f}", fr"Ratio = {d_act/d_allow:.3f}")

    # 3. GRAPH (RESTORED MULTI-LINE & FILL)
    st.markdown("### 📈 Capacity Envelope")
    spans = np.linspace(2, 12, 60)
    # Calculate all lines
    y_sh = [(2*V_cap/(s*100))*100 for s in spans]
    y_mo = [(8*M_cap/((s*100)**2))*100 for s in spans]
    y_df = [((s*100/defl_denom)*384*E_mod*Ix)/(5*((s*100)**4))*100 for s in spans]
    y_safe = [min(s, m, d) for s,m,d in zip(y_sh, y_mo, y_df)]

    fig = go.Figure()
    # Individual Limits (Dashed Lines) - กู้คืนเส้นประแยกสี
    fig.add_trace(go.Scatter(x=spans, y=y_sh, name='Shear Limit', line=dict(color='#ef4444', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=y_mo, name='Moment Limit', line=dict(color='#f59e0b', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=y_df, name='Deflection Limit', line=dict(color='#3b82f6', dash='dash')))
    # Safe Envelope (Filled) - พื้นที่ทึบ
    fig.add_trace(go.Scatter(x=spans, y=y_safe, name='Safe Envelope', fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.1)', line=dict(color='#1e40af', width=4)))
    # Design Point
    fig.add_trace(go.Scatter(x=[user_span], y=[w_safe], mode='markers+text', text=[f" ({user_span}m, {w_safe:,.0f}kg/m)"], textposition="top right", marker=dict(color='red', size=12, symbol='diamond', line=dict(width=2, color='white'))))
    
    fig.update_layout(height=450, margin=dict(t=20, b=20, l=20, r=20), hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: CONNECTION (RESTORED 3 TYPES) ---
with tab2:
    if st.session_state.cal_success:
        # 1. Select Box 3 Types (กู้คืนตัวเลือก 3 อัน)
        st.markdown("##### ⚙️ Connection Configuration")
        c_type = st.selectbox("Connection Type", ["Fin Plate", "End Plate", "Double Angle"])
        
        # 2. Information Header
        st.info(f"Designing **{c_type}** for Shear Load: **{v_conn_design:,.0f} kg** ({design_mode})")
        
        # 3. Call Logic
        section_data = {"name": sec_name, "h": h, "b": b, "tw": tw, "tf": tf}
        connection_design.render_connection_tab(
            V_design_from_tab1=v_conn_design,
            default_bolt_size="M20",
            method=method,
            is_lrfd=is_lrfd,
            section_data=section_data,
            conn_type=c_type, # Pass selected type
            default_bolt_grade="A325",
            default_mat_grade=grade_choice
        )
    else:
        st.warning("⚠️ Please run analysis in Tab 1 first.")

# --- TAB 3: TABLE ---
with tab3:
    st.subheader("📋 Span vs Capacity")
    t_spans = np.arange(2.0, 15.0, 1.0)
    data = []
    for s in t_spans:
        lc = s*100
        wv = (2*V_cap/lc)*100
        wm = (8*M_cap/(lc**2))*100
        wd = ((lc/defl_denom)*384*E_mod*Ix)/(5*(lc**4))*100
        safe = min(wv, wm, wd)
        cause = "Shear" if safe == wv else ("Moment" if safe == wm else "Deflection")
        data.append([s, safe, cause])
    df = pd.DataFrame(data, columns=["Span (m)", "Max Load (kg/m)", "Control"])
    st.dataframe(df.style.format({"Max Load (kg/m)": "{:,.0f}", "Span (m)": "{:.1f}"}), use_container_width=True)

# --- TAB 4: REPORT (FIX ERROR) ---
with tab4:
    # Construct Bolt Data for Report (Mockup)
    bolt_data_rpt = {'size': 'M20', 'qty': 'See Tab 2', 'cap': 'N/A', 'type': 'Bearing', 'grade': 'A325'}
    
    # Call Report Module
    calculation_report.render_report_tab(
        method=method,
        is_lrfd=is_lrfd,
        section_name=sec_name,
        grade=grade_choice,
        section_params={'h':h, 'b':b, 'tw':tw, 'tf':tf, 'Ix':Ix, 'Zx':Zx},
        res_dict=st.session_state.res_dict,
        bolt_data=bolt_data_rpt
    )

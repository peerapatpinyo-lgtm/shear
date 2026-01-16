# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

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
st.set_page_config(page_title="Beam Insight V18 (Logic Fixed)", layout="wide", page_icon="🏗️")

if 'design_method' not in st.session_state:
    st.session_state.design_method = "LRFD (Limit State)"
if 'cal_success' not in st.session_state:
    st.session_state.cal_success = False

# CSS (ห้ามย่อตามคำขอ)
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
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SIDEBAR & METHOD SELECTION (จุดสำคัญ)
# ==========================================
with st.sidebar:
    st.title("🏗️ Beam Insight V18")
    st.divider()
    
    # ดึงค่าจากวิธีก่อน เพื่อใช้ตั้ง Index
    m_idx = 1 if "LRFD" in st.session_state.design_method else 0
    chosen_method = st.radio("Method", ["ASD (Allowable Stress)", "LRFD (Limit State)"], index=m_idx)
    st.session_state.design_method = chosen_method
    
    # ตรวจสอบค่า Boolean อีกครั้งให้มั่นใจ
    is_lrfd = True if "LRFD" in chosen_method else False
    
    grade_opts = {"SS400 (Fy 2450)": 2450, "SM520 (Fy 3550)": 3550, "A36 (Fy 2500)": 2500}
    grade_choice = st.selectbox("Steel Grade", list(grade_opts.keys()))
    Fy = grade_opts[grade_choice]
    E_mod = 2.04e6 
    
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

    Ix = (b * h**3 - (b - tw) * (h - 2*tf)**3) / 120000 
    Zx = ((b * h**2) / 6000) 
    
    st.divider()
    user_span = st.number_input("Span Length (m)", 1.0, 30.0, 6.0, step=0.5)
    defl_denom = int(st.selectbox("Deflection Limit", ["L/300", "L/360", "L/400"], index=1).split("/")[1])
    
    design_mode = st.radio("Load Basis:", ["Actual Load (แรงจริง)", "Fixed % Capacity (% หน้าตัด)"])
    target_pct = st.slider("% of Shear Capacity", 50, 100, 75) if "Fixed" in design_mode else 0

# ==========================================
# 4. FIXED CALCULATION LOGIC (แยก ASD/LRFD เด็ดขาด)
# ==========================================
Aw = (h/10) * (tw/10) # cm2

# AISC 360 Section G2 (Shear) & F2 (Flexure)
if is_lrfd:
    # LRFD: phi = 0.90 สำหรับ Moment, 1.00 สำหรับ Shear (AISC)
    M_cap = 0.90 * Fy * Zx 
    V_cap = 1.00 * 0.60 * Fy * Aw
    label_load = "Factored Load (Wu)"
else:
    # ASD: Omega = 1.67 สำหรับ Moment, 1.50 สำหรับ Shear (AISC)
    # Mn/1.67 = 0.6 Mn | Vn/1.50 = 0.4 Vn
    M_cap = (Fy * Zx) / 1.67 
    V_cap = (0.60 * Fy * Aw) / 1.50
    label_load = "Allowable Load (Wa)"

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

# Connection Load: ต้องอ้างอิงกำลังตาม Method ที่เลือกด้วย
v_conn_design = V_cap * (target_pct / 100.0) if "Fixed" in design_mode else v_act

st.session_state.res_dict = {
    'w_safe': w_safe, 'cause': gov_cause, 'v_cap': V_cap, 'v_act': v_act,
    'm_cap': M_cap, 'm_act': m_act, 'd_all': d_allow, 'd_act': d_act,
    'v_conn_design': v_conn_design
}
st.session_state.cal_success = True

# ==========================================
# 5. UI RENDERING
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection Detail", "📋 Load Table", "📝 Report"])

with tab1:
    st.subheader(f"Engineering Analysis: {sec_name}")
    cause_color = "#dc2626" if gov_cause == "Shear" else ("#d97706" if gov_cause == "Moment" else "#059669")
    
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><span class="sub-text">Max Allowed {label_load}</span><br>
                <span class="big-num">{w_safe:,.0f}</span> <span style="font-size:20px; color:#4b5563;">kg/m</span></div>
            <div style="text-align: right;"><span class="sub-text">Governing Limit</span><br>
                <span style="font-size: 20px; font-weight:bold; color:{cause_color}; background-color:{cause_color}15; padding: 6px 15px; border-radius:15px; border: 1px solid {cause_color}30;">{gov_cause.upper()}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        ratio_v = v_act/V_cap
        st.markdown(f"""<div class="detail-card" style="border-top-color:{'#10b981' if ratio_v<=1 else '#ef4444'}">
            <h4 style="margin:0;">Shear Check</h4><div style="font-size:24px; font-weight:700;">{ratio_v:.3f}</div>
            <small>{v_act:,.0f} / {V_cap:,.0f} kg</small></div>""", unsafe_allow_html=True)
    with c2:
        ratio_m = m_act/M_cap
        st.markdown(f"""<div class="detail-card" style="border-top-color:{'#10b981' if ratio_m<=1 else '#ef4444'}">
            <h4 style="margin:0;">Moment Check</h4><div style="font-size:24px; font-weight:700;">{ratio_m:.3f}</div>
            <small>{m_act:,.0f} / {M_cap:,.0f} kg-m</small></div>""", unsafe_allow_html=True)
    with c3:
        ratio_d = d_act/d_allow
        st.markdown(f"""<div class="detail-card" style="border-top-color:{'#10b981' if ratio_d<=1 else '#ef4444'}">
            <h4 style="margin:0;">Deflection Check</h4><div style="font-size:24px; font-weight:700;">{ratio_d:.3f}</div>
            <small>{d_act:.2f} / {d_allow:.2f} cm</small></div>""", unsafe_allow_html=True)

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
    st.subheader("📋 Span vs Capacity")
    t_spans = np.arange(2.0, 15.0, 1.0)
    data = []
    for s in t_spans:
        lc = s*100
        wv = (2*V_cap/lc)*100
        wm = (8*M_cap/(lc**2))*100
        wd = ((lc/defl_denom)*384*E_mod*Ix)/(5*(lc**4))*100
        safe = min(wv, wm, wd)
        data.append([s, safe, "Shear" if safe == wv else ("Moment" if safe == wm else "Deflection")])
    st.dataframe(pd.DataFrame(data, columns=["Span (m)", "Max Load (kg/m)", "Control"]), use_container_width=True)

with tab4:
    report_generator.render_report_tab(
        method=st.session_state.design_method,
        is_lrfd=is_lrfd,
        sec_name=sec_name,
        steel_grade=grade_choice,
        p={'h': h, 'b': b, 'tw': tw, 'tf': tf, 'Ix': Ix, 'Zx': Zx},
        res=st.session_state.res_dict,
        bolt={'type': st.session_state.get('conn_type','Fin Plate'), 'grade': 'A325', 'size': 'M20', 'qty': 'N/A'}
    )

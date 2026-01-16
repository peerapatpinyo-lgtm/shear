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
st.set_page_config(page_title="Beam Insight V18 (Full Fixed)", layout="wide", page_icon="🏗️")

# Initialize Session State
if 'design_method' not in st.session_state:
    st.session_state.design_method = "LRFD (Limit State)"
if 'cal_success' not in st.session_state:
    st.session_state.cal_success = False

# CSS Styling (ห้ามย่อ)
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
# 3. SIDEBAR INPUTS
# ==========================================
with st.sidebar:
    st.title("🏗️ Beam Insight V18")
    st.divider()
    
    # การเลือก Method
    method_opts = ["ASD (Allowable Stress)", "LRFD (Limit State)"]
    st.session_state.design_method = st.radio("Method", method_opts, index=1 if "LRFD" in st.session_state.design_method else 0)
    is_lrfd = "LRFD" in st.session_state.design_method

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
    defl_ratio = st.selectbox("Deflection Limit", ["L/300", "L/360", "L/400"], index=1)
    defl_denom = int(defl_ratio.split("/")[1])
    
    st.subheader("🔩 Connection Scope")
    design_mode = st.radio("Load Basis:", ["Actual Load (แรงจริง)", "Fixed % Capacity (% หน้าตัด)"])
    target_pct = st.slider("% of Shear Capacity", 50, 100, 75) if "Fixed" in design_mode else 0

# ==========================================
# 4. CALCULATION LOGIC (ASD vs LRFD FIXED)
# ==========================================
Aw = (h/10) * (tw/10) # cm2

# AISC 360-16 Constants
if is_lrfd:
    # LRFD: ใช้ตัวคูณ Phi (Strength Reduction)
    M_cap = 0.90 * Fy * Zx 
    V_cap = 1.00 * 0.60 * Fy * Aw  # Cv = 1.00
    label_load = "Factored Load (Wu)"
else:
    # ASD: ใช้ตัวหาร Omega (Safety Factor) 
    # Mn/1.67 และ Vn/1.50
    M_cap = (Fy * Zx) / 1.67 
    V_cap = (0.60 * Fy * Aw) / 1.50
    label_load = "Allowable Load (Wa)"

L_cm = user_span * 100

# w = 2V/L (kg/m)
w_shear = (2 * V_cap / L_cm) * 100 
# w = 8M/L^2 (kg/m)
w_moment = (8 * M_cap / (L_cm**2)) * 100
# w = 384EI(Delta)/5L^4
w_defl = ((L_cm/defl_denom) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100

w_safe = min(w_shear, w_moment, w_defl)
gov_cause = "Shear" if w_safe == w_shear else ("Moment" if w_safe == w_moment else "Deflection")

v_act = w_safe * user_span / 2
m_act = w_safe * user_span**2 / 8
d_act = (5 * (w_safe/100) * (L_cm**4)) / (384 * E_mod * Ix)
d_allow = L_cm / defl_denom

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
            <div><span class="sub-text">Maximum Allowed {label_load}</span><br>
                <span class="big-num">{w_safe:,.0f}</span> <span style="font-size:20px; color:#4b5563;">kg/m</span></div>
            <div style="text-align: right;"><span class="sub-text">Governing Limit</span><br>
                <span style="font-size: 20px; font-weight:bold; color:{cause_color}; background-color:{cause_color}15; padding: 6px 15px; border-radius:15px; border: 1px solid {cause_color}30;">{gov_cause.upper()}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Detailed Checks
    def render_box(title, act, lim, unit, ratio_label):
        ratio = act/lim
        color = "#10b981" if ratio <= 1.01 else "#ef4444"
        st.markdown(f"""
        <div class="detail-card" style="border-top-color: {color}">
            <h4 style="margin:0; color:#374151;">{title}</h4>
            <div style="font-size:24px; font-weight:700; color:{color};">{ratio:.3f}</div>
            <small style="color:#6b7280;">{ratio_label}: {act:,.1f} / {lim:,.1f} {unit}</small>
        </div>
        """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: render_box("Shear Capacity", v_act, V_cap, "kg", "V/Vn")
    with c2: render_box("Moment Capacity", m_act, M_cap, "kg-m", "M/Mn")
    with c3: render_box("Deflection Limit", d_act, d_allow, "cm", "Δ/Δall")

    # --- กราฟเดิมกลับมาแล้ว ---
    st.markdown("### 📈 Capacity Envelope")
    spans = np.linspace(2, 12, 60)
    y_sh = [(2*V_cap/(s*100))*100 for s in spans]
    y_mo = [(8*M_cap/((s*100)**2))*100 for s in spans]
    y_df = [((s*100/defl_denom)*384*E_mod*Ix)/(5*((s*100)**4))*100 for s in spans]
    y_safe_env = [min(s, m, d) for s,m,d in zip(y_sh, y_mo, y_df)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans, y=y_sh, name='Shear Limit', line=dict(color='#ef4444', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=y_mo, name='Moment Limit', line=dict(color='#f59e0b', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=y_df, name='Deflection Limit', line=dict(color='#3b82f6', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=y_safe_env, name='Safe Envelope', fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.1)', line=dict(color='#1e40af', width=4)))
    fig.add_trace(go.Scatter(x=[user_span], y=[w_safe], mode='markers+text', text=[f" {w_safe:,.0f}"], textposition="top right", marker=dict(color='red', size=12, symbol='diamond')))
    fig.update_layout(height=450, margin=dict(t=20, b=20, l=20, r=20), hovermode="x unified", legend=dict(orientation="h", y=1.1))
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
    st.subheader("📋 Span vs Capacity")
    t_spans = np.arange(2.0, 15.0, 1.0)
    data_list = []
    for s in t_spans:
        lc = s*100
        wv = (2*V_cap/lc)*100
        wm = (8*M_cap/(lc**2))*100
        wd = ((lc/defl_denom)*384*E_mod*Ix)/(5*(lc**4))*100
        safe = min(wv, wm, wd)
        data_list.append([s, safe, "Shear" if safe == wv else ("Moment" if safe == wm else "Deflection")])
    st.dataframe(pd.DataFrame(data_list, columns=["Span (m)", f"Max {label_load} (kg/m)", "Control"]), use_container_width=True)

with tab4:
    # เรียก Report
    report_generator.render_report_tab(
        method=st.session_state.design_method,
        is_lrfd=is_lrfd,
        sec_name=sec_name,
        steel_grade=grade_choice,
        p={'h': h, 'b': b, 'tw': tw, 'tf': tf, 'Ix': Ix, 'Zx': Zx},
        res=st.session_state.res_dict,
        bolt={'type': c_type if 'c_type' in locals() else "Fin Plate", 'grade': 'A325', 'size': 'M20', 'qty': 'N/A'}
    )

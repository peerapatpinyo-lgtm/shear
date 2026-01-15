import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- IMPORT MODULES ---
try:
    import connection_design as conn
    import calculation_report as rep # เปลี่ยนกลับมาใช้ชื่อตามไฟล์ปัจจุบันของคุณ
    import data_utils as db
except ImportError:
    st.warning("Warning: connection_design.py or calculation_report.py not found.")

# ==========================================
# 1. SETUP & STYLE (Engineering V13.2 Style)
# ==========================================
st.set_page_config(page_title="Beam Insight V19", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Roboto+Mono:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
    .detail-card {
        background: white; border-radius: 12px; padding: 20px;
        border: 1px solid #e5e7eb; border-top: 6px solid #2563eb;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
    .status-badge {
        padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 12px;
        float: right; text-transform: uppercase;
    }
    .pass { background-color: #dcfce7; color: #166534; }
    .fail { background-color: #fee2e2; color: #991b1b; }
    .highlight-card { 
        background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%);
        padding: 25px; border-radius: 20px; border-left: 8px solid #2563eb; 
        box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08); margin-bottom: 25px; border: 1px solid #e5e7eb;
    }
    .big-num { color: #1e40af; font-size: 42px; font-weight: 800; font-family: 'Roboto Mono', monospace; }
    .sub-text { color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA SOURCE (Using STEEL_DB from utils)
# ==========================================
steel_db = db.STEEL_DB 

with st.sidebar:
    st.title("🏗️ Beam Insight V19")
    st.divider()
    
    method = st.radio("Method", ["ASD (Allowable Stress)", "LRFD (Limit State)"])
    is_lrfd = True if "LRFD" in method else False
    
    st.subheader("🛠️ Material Grade")
    grade_opts = {"SS400 (Fy 2450)": 2450, "SM490 (Fy 3250)": 3250, "A36 (Fy 2500)": 2500, "Custom": 2400}
    grade_choice = st.selectbox("Steel Grade", list(grade_opts.keys()))
    fy = st.number_input("Fy (kg/cm²)", value=grade_opts[grade_choice])
    
    sec_name = st.selectbox("Steel Section", list(steel_db.keys()), index=11)
    user_span = st.number_input("Span Length (m)", min_value=1.0, value=6.0, step=0.5)
    defl_ratio = st.selectbox("Deflection Limit", ["L/300", "L/360", "L/400"], index=1)
    defl_lim_val = int(defl_ratio.split("/")[1])
    
    st.subheader("🔩 Connection Design")
    conn_type = st.selectbox("Type", ["Fin Plate (Single Shear)", "End Plate (Single Shear)", "Double Angle (Double Shear)"])
    bolt_grade = st.selectbox("Bolt Grade", ["A325", "Grade 8.8", "A490"])
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
    
    E_mod = 2.04e6 

# ==========================================
# 3. CORE CALCULATIONS (V13.2 Restored)
# ==========================================
p = steel_db[sec_name]
Aw = (p['h']/10) * (p['tw']/10) 
Ix, Zx = p['Ix'], p['Zx']
w_self = p['w']

if is_lrfd:
    M_cap = 0.90 * fy * Zx 
    V_cap = 1.00 * 0.6 * fy * Aw
    label_load = "Factored Load (Wu)"
else:
    M_cap = (fy * Zx) / 1.67
    V_cap = (0.6 * fy * Aw) / 1.50
    label_load = "Safe Load (w)"

def get_capacity(L_m):
    L_cm = L_m * 100
    w_v = (2 * V_cap / L_cm) * 100 
    w_m = (8 * M_cap / (L_cm**2)) * 100 
    w_d = ((L_cm/defl_lim_val) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100 
    w_gov = min(w_v, w_m, w_d)
    cause = "Shear" if w_gov == w_v else ("Moment" if w_gov == w_m else "Deflection")
    return w_v, w_m, w_d, w_gov, cause

w_shear, w_moment, w_defl, total_safe_load, user_cause = get_capacity(user_span)

# หักน้ำหนักตัวเองเพื่อแสดงผล External Load เหมือน V13.2
display_external_load = total_safe_load - w_self
v_act = total_safe_load * user_span / 2
m_act = (total_safe_load * user_span**2 / 8) * 100 # Convert to kg-cm for ratio
d_act = (5 * (display_external_load/100) * ((user_span*100)**4)) / (384 * E_mod * Ix)
d_all = (user_span*100) / defl_lim_val

# ==========================================
# 4. UI RENDERING (TAB 1 COMPLETE RESTORE)
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection Detail", "💾 Load Table", "📝 Report"])

with tab1:
    st.subheader(f"Engineering Analysis: {sec_name} ({'LRFD' if is_lrfd else 'ASD'})")
    cause_color = "#dc2626" if user_cause == "Shear" else ("#d97706" if user_cause == "Moment" else "#059669")

    # --- Highlight Card (V13.2 Style) ---
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><span class="sub-text">Maximum Allowed {label_load} (External)</span><br>
                <span class="big-num">{display_external_load:,.0f}</span> <span style="font-size:20px; color:#4b5563;">kg/m</span></div>
            <div style="text-align: right;"><span class="sub-text">Governing Limit</span><br>
                <span style="font-size: 22px; font-weight:bold; color:{cause_color}; background-color:{cause_color}15; padding: 8px 20px; border-radius:15px; border: 1px solid {cause_color}30;">{user_cause.upper()}</span></div>
        </div>
        <div style="margin-top:10px; color:#6b7280; font-size:12px;">* Including Beam Self-weight: {w_self} kg/m (Total Capacity: {total_safe_load:,.0f} kg/m)</div>
    </div>
    """, unsafe_allow_html=True)

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
        with st.expander(f"View {title} Step-by-Step Calculation"):
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
            fr"V_{{act}} = \frac{{w_{{total}} \cdot L}}{{2}} = \frac{{{total_safe_load:,.0f} \cdot {user_span}}}{{2}} = {v_act:,.0f} \text{{ kg}}",
            fr"Ratio = \frac{{{v_act:,.0f}}}{{{V_cap:,.0f}}} = {v_act/V_cap:.3f}"
        )
    with c2:
        render_check_ratio_with_w(
            "Moment Check", m_act, M_cap, "M/M_cap",
            fr"w_{{limit}} = \frac{{8 \cdot M_{{cap}}}}{{L^2}} = \frac{{8 \cdot {M_cap:,.0f}}}{{{L_cm_disp:,.0f}^2}} \cdot 100 = {w_moment:,.0f} \text{{ kg/m}}",
            fr"M_{{act}} = \frac{{w_{{total}} \cdot L^2}}{{8}} = \frac{{{total_safe_load:,.0f} \cdot {user_span}^2}}{{8}} = {m_act/100:,.0f} \text{{ kg.m}}",
            fr"Ratio = \frac{{{m_act:,.0f}}}{{{M_cap:,.0f}}} = {m_act/M_cap:.3f}"
        )
    with c3:
        render_check_ratio_with_w(
            "Deflection Check", d_act, d_all, "Δ/Δ_allow",
            fr"w_{{limit}} = \frac{{384 E I \Delta_{{all}}}}{{5 L^4}} = \frac{{384 \cdot 2.04 \cdot 10^6 \cdot {Ix} \cdot {d_all:.2f}}}{{5 \cdot {L_cm_disp:,.0f}^4}} \cdot 100 = {w_defl:,.0f} \text{{ kg/m}}",
            fr"\Delta_{{act}} = \frac{{5 w_{{ext}} L^4}}{{384 E I}} = {d_act:.3f} \text{{ cm}}",
            fr"Ratio = \frac{{{d_act:.3f}}}{{{d_all:.3f}}} = {d_act/d_all:.3f}"
        )

    st.markdown("### Capacity Envelope Curve")
    spans = np.linspace(2, 12, 100)
    data_env = [get_capacity(s) for s in spans]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans, y=[d[3] for d in data_env], name='Safe Envelope', fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.1)', line=dict(color='#1e40af', width=4)))
    fig.add_trace(go.Scatter(x=[user_span], y=[total_safe_load], mode='markers+text', name='Design Point', text=[f"  ({user_span}m, {total_safe_load:,.0f}kg/m)"], textposition="top right", marker=dict(color='red', size=12, symbol='diamond')))
    fig.update_layout(height=450, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    conn_result = conn.render_connection_tab(v_act, method, is_lrfd, p, conn_type)

with tab3:
    st.subheader("Span-Load Reference Table")
    tbl_spans = np.arange(2.0, 12.5, 0.5)
    df = pd.DataFrame({"Span (m)": tbl_spans, f"Max {label_load} (kg/m)": [get_capacity(s)[3] for s in tbl_spans], "Control": [get_capacity(s)[4] for s in tbl_spans]})
    st.dataframe(df.style.format("{:,.0f}", subset=[f"Max {label_load} (kg/m)"]), use_container_width=True)

with tab4:
    # เตรียมข้อมูลให้ครบสำหรับ Report เพื่อกัน KeyError
    report_beam_res = {
        'pass': (v_act <= V_cap * 1.01) and (m_act <= M_cap * 1.01) and (d_act <= d_all * 1.01),
        'w_safe': display_external_load,
        'v_act': v_act, 'v_cap': V_cap, 'v_ratio': v_act / V_cap,
        'm_act': m_act / 100, 'm_cap': M_cap / 100, 'm_ratio': m_act / M_cap,
        'd_act': d_act, 'd_all': d_all, 'd_ratio': d_act / d_all,
        'span': user_span, 'cause': user_cause
    }
    rep.render_report_tab({'name': "Project", 'eng': "Engineer", 'sec': sec_name, 'method': method}, report_beam_res, conn_result if 'conn_result' in locals() else {})

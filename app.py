import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- IMPORT MODULES ---
try:
    import connection_design as conn
    import report_generator as rep
except ImportError:
    st.error("Error: ไม่พบไฟล์ connection_design.py หรือ report_generator.py กรุณาตรวจสอบชื่อไฟล์")

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Beam Insight V13.4", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Roboto+Mono:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
    .detail-card {
        background: white; border-radius: 12px; padding: 20px;
        border: 1px solid #e5e7eb; border-top: 6px solid #2563eb;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
    .highlight-card { 
        background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%);
        padding: 25px; border-radius: 20px; border-left: 8px solid #2563eb; 
        box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08); margin-bottom: 25px; border: 1px solid #e5e7eb;
    }
    .big-num { color: #1e40af; font-size: 48px; font-weight: 800; font-family: 'Roboto Mono', monospace; }
    .sub-text { color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. STEEL DATABASE
# ==========================================
steel_db = {
    "H 100x100x6x8":    {"h": 100, "b": 100, "tw": 6,   "tf": 8,   "Ix": 383,    "Zx": 76.5,  "w": 17.2},
    "H 200x100x5.5x8":  {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "w": 21.3},
    "H 300x150x6.5x9":  {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 400x200x8x13":   {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 500x200x10x16":  {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
    "H 600x200x11x17":  {"h": 600, "b": 200, "tw": 11,  "tf": 17,  "Ix": 77600,  "Zx": 2590,  "w": 106},
}

with st.sidebar:
    st.title("🏗️ Beam Insight V13.4")
    st.divider()
    method = st.radio("Calculation Method", ["ASD", "LRFD"])
    is_lrfd = (method == "LRFD")
    
    sec_name = st.selectbox("Steel Section", list(steel_db.keys()), index=3)
    user_span = st.number_input("Span Length (m)", min_value=1.0, value=6.0, step=0.5)
    
    st.subheader("Material & Limit")
    fy = st.number_input("Fy (kg/cm²)", value=2450)
    defl_lim_val = st.number_input("Deflection Limit (L/X)", value=360)
    
    st.subheader("Connection Settings")
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
    bolt_grade = st.selectbox("Bolt Grade", ["A325 (High Strength)", "Grade 8.8"])
    conn_type = st.selectbox("Connection Type", ["Fin Plate", "End Plate", "Double Angle"])

# ==========================================
# 3. CALCULATIONS ENGINE
# ==========================================
p = steel_db[sec_name]
Aw = (p['h']/10) * (p['tw']/10) # cm2
Ix, Zx = p['Ix'], p['Zx']
E_mod = 2.04e6

if is_lrfd:
    M_cap = 0.90 * fy * Zx
    V_cap = 1.00 * 0.6 * fy * Aw
    label_load = "Factored Load (Wu)"
else:
    M_cap = 0.60 * fy * Zx
    V_cap = 0.40 * fy * Aw
    label_load = "Allowable Load (w)"

def get_capacity(L_m):
    L_cm = L_m * 100
    w_v = (2 * V_cap / L_cm) * 100
    w_m = (8 * M_cap / (L_cm**2)) * 100
    w_d = ((L_cm/defl_lim_val) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100
    w_gov = min(w_v, w_m, w_d)
    cause = "Shear" if w_gov == w_v else ("Moment" if w_gov == w_m else "Deflection")
    return w_v, w_m, w_d, w_gov, cause

w_shear, w_moment, w_defl, user_safe_load, user_cause = get_capacity(user_span)

# Actual Forces at Governing Load
v_act = (user_safe_load * user_span) / 2
m_act = (user_safe_load * user_span**2) / 8
d_act = (5 * (user_safe_load/100) * ((user_span*100)**4)) / (384 * E_mod * Ix)
d_all = (user_span*100) / defl_lim_val

# ==========================================
# 4. TAB 1: BEAM ANALYSIS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection Detail", "💾 Load Table", "📝 Report"])

with tab1:
    cause_color = "#dc2626" if user_cause == "Shear" else ("#d97706" if user_cause == "Moment" else "#059669")
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><span class="sub-text">Max {label_load}</span><br><span class="big-num">{user_safe_load:,.0f}</span> <span style="font-size:20px;">kg/m</span></div>
            <div style="text-align: right;"><span class="sub-text">Governing Mode</span><br>
            <span style="font-size: 24px; font-weight:bold; color:{cause_color}; border:2px solid {cause_color}; padding:5px 15px; border-radius:10px;">{user_cause.upper()}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    
    with col1:
        v_ratio = v_act / V_cap
        st.markdown(f"""<div class="detail-card"><h4>Shear Check</h4><h2 style="color:{'#10b981' if v_ratio <= 1 else '#ef4444'}">{v_ratio:.3f}</h2><p>Ratio (V/V_cap)</p></div>""", unsafe_allow_html=True)
        with st.expander("Shear Formula"):
            st.latex(fr"V_{{cap}} = {'0.6 \cdot F_y \cdot A_w' if is_lrfd else '0.4 \cdot F_y \cdot A_w'}")
            st.write(f"Capacity: {V_cap:,.0f} kg")

    with col2:
        m_ratio = m_act / (M_cap/100)
        st.markdown(f"""<div class="detail-card"><h4>Moment Check</h4><h2 style="color:{'#10b981' if m_ratio <= 1 else '#ef4444'}">{m_ratio:.3f}</h2><p>Ratio (M/M_cap)</p></div>""", unsafe_allow_html=True)
        with st.expander("Moment Formula"):
            st.latex(fr"M_{{cap}} = {'0.9 \cdot F_y \cdot Z_x' if is_lrfd else '0.6 \cdot F_y \cdot Z_x'}")
            st.write(f"Capacity: {M_cap/100:,.0f} kg.m")

    with col3:
        d_ratio = d_act / d_all
        st.markdown(f"""<div class="detail-card"><h4>Deflection Check</h4><h2 style="color:{'#10b981' if d_ratio <= 1 else '#ef4444'}">{d_ratio:.3f}</h2><p>Ratio (Δ/Δ_all)</p></div>""", unsafe_allow_html=True)
        with st.expander("Deflection Formula"):
            st.latex(fr"\Delta_{{all}} = L / {defl_lim_val}")
            st.write(f"Limit: {d_all:.3f} cm")

    # Envelope Graph
    spans = np.linspace(2, 12, 50)
    env_data = [get_capacity(s) for s in spans]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans, y=[d[3] for d in env_data], name='Capacity Envelope', fill='tozeroy', line=dict(color='#1e40af', width=3)))
    fig.add_trace(go.Scatter(x=[user_span], y=[user_safe_load], mode='markers+text', name='Design Point', text=["Current"], textposition="top center", marker=dict(color='red', size=12)))
    fig.update_layout(title="Beam Capacity vs Span Length", xaxis_title="Span (m)", yaxis_title="Load (kg/m)", height=400)
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 5. TAB 2: CONNECTION
# ==========================================
with tab2:
    try:
        # ส่งค่าไปคำนวณที่ไฟล์ connection_design.py
        req_bolt, v_bolt_cap = conn.render_connection_tab(
            V_design=v_act, # ใช้แรงเฉือนที่เกิดขึ้นจริงจากน้ำหนักบรรทุก
            bolt_size=bolt_size,
            method=method,
            is_lrfd=is_lrfd,
            section_data=p,
            conn_type=conn_type,
            bolt_grade=bolt_grade
        )
    except Exception as e:
        st.error(f"ไม่สามารถโหลดหน้า Connection ได้: {e}")

# ==========================================
# 6. TAB 3 & 4: TABLE & REPORT
# ==========================================
with tab3:
    tbl_spans = [2, 3, 4, 5, 6, 7, 8, 9, 10]
    tbl_rows = [get_capacity(s) for s in tbl_spans]
    df_tbl = pd.DataFrame({
        "Span (m)": tbl_spans,
        f"Max {label_load} (kg/m)": [r[3] for r in tbl_rows],
        "Control Factor": [r[4] for r in tbl_rows]
    })
    st.table(df_tbl.style.format("{:,.0f}", subset=[f"Max {label_load} (kg/m)"]))

with tab4:
    res_summary = {
        'w_safe': user_safe_load, 'cause': user_cause, 
        'v_act': v_act, 'v_cap': V_cap, 
        'm_act': m_act, 'm_cap': M_cap, 
        'd_act': d_act, 'd_all': d_all
    }
    bolt_summary = {
        'size': bolt_size, 'qty': req_bolt if 'req_bolt' in locals() else 0,
        'grade': bolt_grade, 'type': conn_type
    }
    rep.render_report_tab(method, is_lrfd, sec_name, "SS400", p, res_summary, bolt_summary)

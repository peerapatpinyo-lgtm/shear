import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- IMPORT MODULES ---
# หมายเหตุ: ตรวจสอบว่ามีไฟล์ connection_design.py และ report_generator.py อยู่ในโฟลเดอร์เดียวกัน
try:
    import connection_design as conn
    import report_generator as rep
except ImportError:
    st.error("Missing module files! Please ensure connection_design.py and report_generator.py exist.")

# ==========================================
# 1. SETUP & STYLE (Professional UI)
# ==========================================
st.set_page_config(page_title="Beam Insight V12", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Roboto+Mono:wght@400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }

    /* --- Metric Card --- */
    .metric-card-final {
        background: white; border-radius: 16px; padding: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05); border: 1px solid #f0f2f6;
        height: 100%; display: flex; flex-direction: column; justify-content: space-between;
    }
    .m-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    .m-title { font-weight: 700; color: #4b5563; font-size: 15px; display: flex; align-items: center; gap: 8px; }
    .m-percent { font-family: 'Roboto Mono', monospace; font-size: 28px; font-weight: 700; }
    .m-bar-bg { background-color: #f3f4f6; height: 10px; border-radius: 5px; overflow: hidden; margin-bottom: 16px; }
    .m-bar-fill { height: 100%; border-radius: 5px; transition: width 0.8s ease; }
    .m-values { display: flex; justify-content: space-between; align-items: flex-end; font-family: 'Roboto Mono', monospace; font-size: 15px; color: #1f2937; margin-bottom: 10px; }
    .val-label { font-size: 11px; color: #9ca3af; font-weight: 600; text-transform: uppercase; margin-bottom: 4px; }
    .m-check { background-color: #f9fafb; border-radius: 8px; padding: 8px; font-size: 13px; color: #4b5563; text-align: center; border: 1px solid #f3f4f6; font-family: 'Roboto Mono', monospace; }

    /* --- Highlight Card --- */
    .highlight-card { 
        background: linear-gradient(135deg, #ffffff 0%, #f8faff 100%);
        padding: 30px; border-radius: 20px; border-left: 8px solid #2563eb; 
        box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08); margin-bottom: 30px; border: 1px solid #e5e7eb;
    }
    
    /* --- Calculation Box --- */
    .calc-box {
        background-color: #fcfcfc; border: 1px solid #e5e7eb; border-top: 4px solid #374151;
        padding: 20px; margin-bottom: 15px; border-radius: 12px; min-height: 220px;
    }
    .calc-title { font-weight: 700; color: #111827; margin-bottom: 15px; font-size: 16px; border-bottom: 1px solid #eee; padding-bottom: 8px;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA (Fixed NameError)
# ==========================================
steel_db = {
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8,  "w": 14.0},
    "H 200x100x5.5x8":  {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "w": 21.3},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "w": 29.6},
    "H 300x150x6.5x9":  {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 350x175x7x11":   {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "w": 49.6},
    "H 400x200x8x13":   {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 450x200x9x14":   {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "w": 76.0},
    "H 500x200x10x16":  {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
    "H 600x200x11x17":  {"h": 600, "b": 200, "tw": 11,  "tf": 17,  "Ix": 77600,  "Zx": 2590,  "w": 106},
}

with st.sidebar:
    st.title("Beam Insight V12")
    st.caption("Standard Calculation Edition")
    st.divider()
    method = st.radio("Standard", ["ASD (Allowable Stress)", "LRFD (Limit State)"])
    is_lrfd = "LRFD" in method
    st.divider()
    sec_name = st.selectbox("Select Section", list(steel_db.keys()), index=5)
    user_span = st.number_input("Span Length (m)", min_value=1.0, value=6.0, step=0.5)
    fy = st.number_input("Fy (ksc)", 2400)
    defl_ratio = st.selectbox("Defl. Limit", ["L/300", "L/360", "L/400"], index=1)
    st.divider()
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
    design_mode = st.radio("Connection Design:", ["Actual Load (from Span)", "Fixed % Capacity"])
    target_pct = st.slider("Target % Usage", 50, 100, 75, 5) if design_mode == "Fixed % Capacity" else None

    E_mod = 2.04e6 
    defl_lim_val = int(defl_ratio.split("/")[1])

# ==========================================
# 3. CORE LOGIC
# ==========================================
p = steel_db[sec_name]
h_cm, tw_cm = p['h']/10, p['tw']/10
Aw = h_cm * tw_cm
Ix, Zx = p['Ix'], p['Zx']

if is_lrfd:
    phi_b, phi_v = 0.90, 1.00
    M_cap, V_cap = phi_b * fy * Zx, phi_v * 0.6 * fy * Aw
    label_load = "Factored Load (Wu)"
else:
    M_cap, V_cap = 0.6 * fy * Zx, 0.4 * fy * Aw
    label_load = "Safe Load (w)"

def get_capacity(L_m):
    L_c = L_m * 100
    w_s = (2 * V_cap) / L_c * 100
    w_m = (8 * M_cap) / (L_c**2) * 100
    w_d = ((L_c/defl_lim_val) * 384 * E_mod * Ix) / (5 * (L_c**4)) * 100
    w_gv = min(w_s, w_m, w_d)
    cause = "Shear" if w_gv == w_s else ("Moment" if w_gv == w_m else "Deflection")
    return w_s, w_m, w_d, w_gv, cause

w_shear, w_moment, w_defl, user_safe_load, user_cause = get_capacity(user_span)
V_actual = user_safe_load * user_span / 2
M_actual = user_safe_load * user_span**2 / 8
delta_actual = (5 * (user_safe_load/100) * ((user_span*100)**4)) / (384 * E_mod * Ix)
delta_allow = (user_span*100) / defl_lim_val
V_design = V_actual if design_mode == "Actual Load (from Span)" else V_cap * (target_pct / 100)

# ==========================================
# 4. UI DISPLAY
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection", "💾 Load Table", "📝 Report"])

with tab1:
    st.subheader(f"Engineering Analysis: {sec_name}")
    cause_color = "#dc2626" if user_cause == "Shear" else ("#d97706" if user_cause == "Moment" else "#059669")
    
    # 1. Highlight Card
    st.markdown(f"""<div class="highlight-card"><div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <div><div style="color:#6b7280; font-size:13px; font-weight:600; text-transform:uppercase;">Max {label_load}</div>
        <div style="display:flex; align-items:baseline; gap:10px;"><span style="color:#1d4ed8; font-size:48px; font-weight:800; font-family:'Roboto Mono';">{user_safe_load:,.0f}</span><span style="font-size:22px; color:#4b5563;">kg/m</span></div></div>
        <div style="text-align:right;"><div style="color:#6b7280; font-size:13px; font-weight:600; text-transform:uppercase;">Governing Factor</div>
        <div style="font-size:20px; font-weight:800; color:{cause_color}; background:{cause_color}15; padding:8px 24px; border-radius:12px; border:1px solid {cause_color}30;">{user_cause.upper()}</div></div>
    </div></div>""", unsafe_allow_html=True)

    # 2. Calculation Details
    with st.expander("🕵️‍♂️ Calculation Details", expanded=True):
        c_cal1, c_cal2, c_cal3 = st.columns(3)
        L_cm_disp = user_span * 100
        with c_cal1:
            st.markdown('<div class="calc-box"><div class="calc-title">1. Shear Control</div>', unsafe_allow_html=True)
            st.latex(r''' w = \frac{2 \times V_{cap}}{L} \times 100 ''')
            st.latex(fr''' w = \frac{{2 \times {V_cap:,.0f}}}{{{L_cm_disp:,.0f}}} \times 100 = \mathbf{{{w_shear:,.0f}}} ''')
            st.markdown("</div>", unsafe_allow_html=True)
        with c_cal2:
            st.markdown('<div class="calc-box" style="border-top-color:#f59e0b;"><div class="calc-title">2. Moment Control</div>', unsafe_allow_html=True)
            st.latex(r''' w = \frac{8 \times M_{cap}}{L^2} \times 100 ''')
            st.latex(fr''' w = \frac{{8 \times {M_cap:,.0f}}}{{{L_cm_disp:,.0f}^2}} \times 100 = \mathbf{{{w_moment:,.0f}}} ''')
            st.markdown("</div>", unsafe_allow_html=True)
        with c_cal3:
            st.markdown('<div class="calc-box" style="border-top-color:#10b981;"><div class="calc-title">3. Deflection Control</div>', unsafe_allow_html=True)
            st.latex(r''' w = \frac{384 E I \Delta}{5 L^4} \times 100 ''')
            st.latex(fr''' w = \frac{{384 \cdot {E_mod:.1e} \cdot {Ix} \cdot {delta_allow:.2f}}}{{5 \cdot {L_cm_disp:,.0f}^4}} \times 100 = \mathbf{{{w_defl:,.0f}}} ''')
            st.markdown("</div>", unsafe_allow_html=True)

    # 3. Metrics
    cm1, cm2, cm3 = st.columns(3)
    def create_card_final(icon, title, actual, limit, unit, color_base, decimal=0):
        pct = (actual / limit) * 100
        c_status = "#ef4444" if pct > 100 else color_base
        return f"""<div class="metric-card-final" style="border-top:5px solid {c_status};">
            <div class="m-header"><div class="m-title">{icon} {title}</div><div class="m-percent" style="color:{c_status};">{pct:.1f}%</div></div>
            <div class="m-values"><div><div class="val-label">Actual</div><b>{actual:,.{decimal}f}</b></div><div style="text-align:right;"><div class="val-label">Limit ({unit})</div><b>{limit:,.{decimal}f}</b></div></div>
            <div class="m-bar-bg"><div class="m-bar-fill" style="width:{min(pct, 100):.1f}%; background:{c_status};"></div></div>
            <div class="m-check">{actual:,.{decimal}f} ÷ {limit:,.{decimal}f} = {pct:.1f}%</div>
        </div>"""
    with cm1: st.markdown(create_card_final("🛡️", "Shear Usage", V_actual, V_cap, "kg", "#10b981"), unsafe_allow_html=True)
    with cm2: st.markdown(create_card_final("🌀", "Moment Usage", M_actual, M_cap/100, "kg.m", "#f59e0b"), unsafe_allow_html=True)
    with cm3: st.markdown(create_card_final("📉", "Deflection", delta_actual, delta_allow, "cm", "#3b82f6", decimal=2), unsafe_allow_html=True)

    # 4. Graph
    st.markdown("<br>", unsafe_allow_html=True)
    g_spans = np.linspace(2, 15, 100)
    g_data = [get_capacity(l) for l in g_spans]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=g_spans, y=[x[3] for x in g_data], mode='lines', name='Max Capacity', line=dict(color='#2563eb', width=3), fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.1)'))
    fig.add_trace(go.Scatter(x=[user_span], y=[user_safe_load], mode='markers', marker=dict(color='#1e293b', size=12, symbol='star'), name='Current'))
    fig.update_layout(title="Span vs Capacity Curve", height=400, margin=dict(t=40, b=40, l=40, r=40), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# ส่วน Tab อื่นๆ เรียกใช้ function จากโมดูลของคุณ
with tab2: conn.render_connection_tab(V_design, bolt_size, method, is_lrfd, p)
with tab3: st.dataframe(pd.DataFrame([{"Span (m)": l, "Capacity": get_capacity(l)[3]} for l in np.arange(2, 16, 1)]), use_container_width=True)
with tab4: rep.render_report_tab(method, is_lrfd, sec_name, fy, p, {'M_cap': M_cap, 'V_cap': V_cap}, {'size': bolt_size, 'capacity': 0})

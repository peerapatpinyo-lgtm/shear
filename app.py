# app.py (Full Updated Version)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- IMPORT MODULES ---
try:
    import connection_design as conn
    import report_generator as rep
except ImportError:
    st.warning("Warning: connection_design.py or report_generator.py not found. Some tabs may not work.")

# ==========================================
# 1. SETUP & STYLE (Engineering Professional)
# ==========================================
st.set_page_config(page_title="Beam Insight V12", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Roboto+Mono:wght@400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }

    /* --- Metric Card (Detail Version) --- */
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

    /* --- Highlight Card --- */
    .highlight-card { 
        background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%);
        padding: 25px; border-radius: 20px; border-left: 8px solid #2563eb; 
        box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08); margin-bottom: 25px; border: 1px solid #e5e7eb;
    }
    .big-num { color: #1e40af; font-size: 42px; font-weight: 800; font-family: 'Roboto Mono', monospace; }
    .sub-text { color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; }

    /* --- Report Paper Style --- */
    .report-paper {
        background: white; padding: 40px; border: 1px solid #ddd;
        box-shadow: 0 0 15px rgba(0,0,0,0.1); color: #333; line-height: 1.6;
        max-width: 900px; margin: auto; font-family: 'Sarabun', sans-serif;
    }
    .report-header { font-size: 18px; font-weight: 700; color: #1e40af; border-bottom: 2px solid #1e40af; margin: 20px 0 10px 0; }
    .report-line { display: flex; justify-content: space-between; border-bottom: 1px dashed #eee; padding: 5px 0; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SIDEBAR INPUTS
# ==========================================
with st.sidebar:
    st.title("🏗️ Beam Insight V12")
    st.divider()
    
    st.header("1. Design Standard")
    method = st.radio("Method", ["ASD (Allowable Stress)", "LRFD (Limit State)"])
    is_lrfd = method == "LRFD"
    
    st.divider()
    st.header("2. Geometry & Material")
    from steel_data import steel_db # แนะนำให้แยกไฟล์ แต่ถ้ายังไม่แยกใช้ steel_db ด้านล่าง
    # (ใช้ steel_db เดิมที่คุณให้มา)
    steel_db = {
        "H 100x100x6x8":    {"h": 100, "b": 100, "tw": 6,   "tf": 8,   "Ix": 383,    "Zx": 76.5,  "w": 17.2},
        "H 150x150x7x10":   {"h": 150, "b": 150, "tw": 7,   "tf": 10,  "Ix": 1640,   "Zx": 219,   "w": 31.5},
        "H 200x200x8x12":   {"h": 200, "b": 200, "tw": 8,   "tf": 12,  "Ix": 4720,   "Zx": 472,   "w": 49.9},
        "H 300x150x6.5x9":  {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
        "H 400x200x8x13":   {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
        "H 500x200x10x16":  {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
        "H 600x200x11x17":  {"h": 600, "b": 200, "tw": 11,  "tf": 17,  "Ix": 77600,  "Zx": 2590,  "w": 106},
    }
    sec_name = st.selectbox("Steel Section", list(steel_db.keys()), index=4)
    user_span = st.number_input("Span Length (m)", min_value=1.0, value=6.0, step=0.5)
    fy = st.number_input("Fy (kg/cm²)", 2400)
    defl_ratio = st.selectbox("Deflection Limit", ["L/300", "L/360", "L/400"], index=1)
    defl_lim_val = int(defl_ratio.split("/")[1])
    
    st.divider()
    st.header("3. Connection Settings")
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
    design_mode = st.radio("Load for Connection:", ["Actual Load", "Fixed % Capacity"])
    target_pct = st.slider("Target Usage %", 50, 100, 75) if design_mode == "Fixed % Capacity" else None

    E_mod = 2.04e6 

# ==========================================
# 3. CORE CALCULATIONS
# ==========================================
p = steel_db[sec_name]
Aw = (p['h']/10) * (p['tw']/10) 
Ix, Zx = p['Ix'], p['Zx']

if is_lrfd:
    M_cap = 0.9 * fy * Zx
    V_cap = 1.0 * 0.6 * fy * Aw
    label_load = "Factored Load (Wu)"
else:
    M_cap = 0.6 * fy * Zx
    V_cap = 0.4 * fy * Aw
    label_load = "Safe Load (w)"

def get_capacity(L_m):
    L_cm = L_m * 100
    w_v = (2 * V_cap / L_cm) * 100 
    w_m = (8 * M_cap / (L_cm**2)) * 100 
    w_d = ((L_cm/defl_lim_val) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100 
    w_gov = min(w_v, w_m, w_d)
    cause = "Shear" if w_gov == w_v else ("Moment" if w_gov == w_m else "Deflection")
    return w_v, w_m, w_d, w_gov, cause

w_shear, w_moment, w_defl, user_safe_load, user_cause = get_capacity(user_span)

V_actual = user_safe_load * user_span / 2
M_actual = user_safe_load * user_span**2 / 8
delta_actual = (5 * (user_safe_load/100) * ((user_span*100)**4)) / (384 * E_mod * Ix)
delta_allow = (user_span*100) / defl_lim_val

V_design = V_actual if design_mode == "Actual Load" else V_cap * (target_pct / 100)

# ==========================================
# 4. UI RENDERING
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection Detail", "💾 Load Table", "📝 Report"])

with tab1:
    st.subheader(f"Engineering Analysis: {sec_name}")
    cause_color = "#dc2626" if user_cause == "Shear" else ("#d97706" if user_cause == "Moment" else "#059669")

    # --- 1. Main Highlight Card ---
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span class="sub-text">Maximum Allowed {label_load}</span><br>
                <span class="big-num">{user_safe_load:,.0f}</span> <span style="font-size:20px; color:#4b5563;">kg/m</span>
            </div>
            <div style="text-align: right;">
                <span class="sub-text">Governing Limit</span><br>
                <span style="font-size: 22px; font-weight:bold; color:{cause_color}; background-color:{cause_color}15; padding: 8px 20px; border-radius:15px; border: 1px solid {cause_color}30;">
                    {user_cause.upper()}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 2. Detailed Verification (Check Ratio Summary) ---
    st.markdown("### 🔍 Detailed Check Ratio Summary")
    
    def render_check_ratio(title, act, lim, unit, equation_act, equation_ratio):
        ratio = act / lim
        is_pass = ratio <= 1.01 # เผื่อ tolerance เล็กน้อย
        status_class = "pass" if is_pass else "fail"
        status_text = "PASS" if is_pass else "FAIL"
        border_color = "#10b981" if is_pass else "#ef4444"

        with st.container():
            st.markdown(f"""
            <div class="detail-card" style="border-top-color: {border_color}">
                <span class="status-badge {status_class}">{status_text}</span>
                <h4 style="margin:0; color:#374151;">{title}</h4>
                <div style="margin-top:10px;">
                    <small style="color:#6b7280;">Ratio: {act:,.2f} / {lim:,.2f}</small>
                    <div style="font-size:24px; font-weight:700; color:{border_color};">{ratio:.3f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            with st.expander(f"View {title} Calculation"):
                st.latex(equation_act)
                st.latex(equation_ratio)

    c1, c2, c3 = st.columns(3)
    with c1:
        render_check_ratio(
            "Shear Check", V_actual, V_cap, "kg",
            fr"V_{{act}} = \frac{{w \cdot L}}{{2}} = \frac{{{user_safe_load:,.0f} \cdot {user_span}}}{{2}} = {V_actual:,.0f} \text{{ kg}}",
            fr"Ratio = \frac{{V_{{act}}}}{{V_{{cap}}}} = \frac{{{V_actual:,.0f}}}{{{V_cap:,.0f}}} = {V_actual/V_cap:.3f}"
        )
    with c2:
        render_check_ratio(
            "Moment Check", M_actual, (M_cap/100), "kg.m",
            fr"M_{{act}} = \frac{{w \cdot L^2}}{{8}} = \frac{{{user_safe_load:,.0f} \cdot {user_span}^2}}{{8}} = {M_actual:,.0f} \text{{ kg.m}}",
            fr"Ratio = \frac{{M_{{act}}}}{{M_{{cap}}}} = \frac{{{M_actual:,.0f}}}{{{M_cap/100:,.0f}}} = {M_actual/(M_cap/100):.3f}"
        )
    with c3:
        render_check_ratio(
            "Deflection Check", delta_actual, delta_allow, "cm",
            r"\Delta_{act} = \frac{5 w L^4}{384 E I}",
            fr"Ratio = \frac{{\Delta_{{act}}}}{{\Delta_{{allow}}}} = \frac{{{delta_actual:.3f}}}{{{delta_allow:.3f}}} = {delta_actual/delta_allow:.3f}"
        )

    # --- 3. Capacity Graphic Graph ---
    st.markdown("### Capacity Envelope Curve")
    spans = np.linspace(2, 12, 100)
    data = [get_capacity(s) for s in spans]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans, y=[d[0] for d in data], name='Shear Limit', line=dict(color='#ef4444', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=[d[1] for d in data], name='Moment Limit', line=dict(color='#f59e0b', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=[d[2] for d in data], name='Deflection Limit', line=dict(color='#3b82f6', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=[d[3] for d in data], name='Safe Envelope', fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.1)', line=dict(color='#1e40af', width=4)))
    fig.update_layout(hovermode="x unified", height=400, margin=dict(t=20, b=20, l=20, r=20), plot_bgcolor='white')
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    try:
        # รับค่า req_bolt และ v_bolt กลับมาเพื่อส่งต่อให้ Report
        req_bolt, v_bolt = conn.render_connection_tab(V_design, bolt_size, method, is_lrfd, p)
    except Exception as e:
        st.info(f"Connection module is being updated... {e}")
        req_bolt, v_bolt = 0, 0

with tab3:
    st.subheader("Span-Load Reference Table")
    tbl_spans = np.arange(2.0, 12.5, 0.5)
    tbl_data = [get_capacity(s) for s in tbl_spans]
    df = pd.DataFrame({
        "Span (m)": tbl_spans,
        f"Max {label_load} (kg/m)": [d[3] for d in tbl_data],
        "Control Factor": [d[4] for d in tbl_data]
    })
    st.dataframe(df.style.format("{:,.0f}", subset=[f"Max {label_load} (kg/m)"]), use_container_width=True)

with tab4:
    try:
        caps = {'M_cap': M_cap, 'V_cap': V_cap}
        # ส่งค่า bolt_info ที่คำนวณได้จริงไปที่ Report
        bolt_info = {'size': bolt_size, 'capacity': v_bolt, 'qty': req_bolt}
        rep.render_report_tab(method, is_lrfd, sec_name, fy, p, caps, bolt_info)
    except Exception as e:
        st.info(f"Report generator is being updated... {e}")

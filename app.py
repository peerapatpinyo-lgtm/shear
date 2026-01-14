import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- IMPORT MODULES ---
import connection_design as conn
import report_generator as rep

# ==========================================
# 1. SETUP & STYLE (Enhanced UI)
# ==========================================
st.set_page_config(page_title="Beam Insight V12 (Modular)", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Roboto+Mono:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Sarabun', sans-serif; 
    }

    /* --- Metric Card Design --- */
    .metric-card-final {
        background: white; 
        border-radius: 16px; 
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.04); 
        border: 1px solid #f0f2f6;
        height: 100%; 
        display: flex; 
        flex-direction: column; 
        justify-content: space-between;
        transition: transform 0.2s ease;
    }
    .metric-card-final:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 25px rgba(0,0,0,0.07);
    }
    .m-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    .m-title { font-weight: 700; color: #4b5563; font-size: 15px; display: flex; align-items: center; gap: 10px; }
    .m-percent { font-family: 'Roboto Mono', monospace; font-size: 28px; font-weight: 700; }
    
    .m-bar-bg { background-color: #f3f4f6; height: 12px; border-radius: 6px; overflow: hidden; margin-bottom: 16px; }
    .m-bar-fill { height: 100%; border-radius: 6px; transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1); }
    
    .m-values { display: flex; justify-content: space-between; align-items: flex-end; font-family: 'Roboto Mono', monospace; font-size: 15px; color: #1f2937; margin-bottom: 10px; }
    .val-label { font-size: 11px; color: #9ca3af; font-family: 'Sarabun', sans-serif; font-weight: 600; text-transform: uppercase; margin-bottom: 4px; }
    
    .m-check { 
        background-color: #f9fafb; 
        border-radius: 8px; 
        padding: 8px 12px; 
        font-size: 13px; 
        color: #4b5563; 
        text-align: center; 
        border: 1px solid #f3f4f6; 
        font-family: 'Roboto Mono', monospace; 
    }

    /* --- Highlight Card --- */
    .highlight-card { 
        background: linear-gradient(135deg, #ffffff 0%, #f8faff 100%);
        padding: 30px; 
        border-radius: 20px; 
        border-left: 8px solid #2563eb; 
        box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08); 
        margin-bottom: 30px;
        border: 1px solid #e5e7eb;
    }
    
    /* --- Calculation Display Style --- */
    .calc-box {
        background-color: #fcfcfc;
        border: 1px solid #e5e7eb;
        border-top: 4px solid #374151;
        padding: 20px;
        margin-bottom: 15px;
        border-radius: 12px;
        min-height: 220px;
    }
    .calc-title {
        font-weight: 700;
        color: #111827;
        margin-bottom: 15px;
        font-size: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* LaTeX adjustment */
    .stLatex { font-size: 14px !important; }
</style>
""", unsafe_allow_html=True)

# ... (ส่วน INPUTS และ CORE CALCULATION คงเดิมตามโค้ดต้นฉบับของคุณ) ...
# [Copy ส่วน INPUTS และ CORE CALCULATION จากโค้ดคุณมาวางตรงนี้]

# --- ตัวอย่างการรันค่าเพื่อให้แสดงผลได้ ---
p = steel_db[sec_name]
h_cm, tw_cm = p['h']/10, p['tw']/10
Aw = h_cm * tw_cm
Ix, Zx = p['Ix'], p['Zx']

if is_lrfd:
    phi_b, phi_v = 0.90, 1.00
    M_cap = phi_b * fy * Zx
    V_cap = phi_v * 0.6 * fy * Aw
    label_load = "Factored Load (Wu)"
    label_cap_m = "Phi Mn"
    label_cap_v = "Phi Vn"
else:
    M_cap = 0.6 * fy * Zx
    V_cap = 0.4 * fy * Aw
    label_load = "Safe Load (w)"
    label_cap_m = "M allow"
    label_cap_v = "V allow"

def get_capacity(L_m):
    L_cm = L_m * 100
    w_s = (2 * V_cap) / L_cm * 100
    w_m = (8 * M_cap) / (L_cm**2) * 100
    w_d = ((L_cm/defl_lim_val) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100
    w_gov = min(w_s, w_m, w_d)
    cause = "Shear" if w_gov == w_s else ("Moment" if w_gov == w_m else "Deflection")
    return w_s, w_m, w_d, w_gov, cause

w_shear, w_moment, w_defl, user_safe_load, user_cause = get_capacity(user_span)
V_actual = user_safe_load * user_span / 2
M_actual = user_safe_load * user_span**2 / 8
delta_actual = (5 * (user_safe_load/100) * ((user_span*100)**4)) / (384 * E_mod * Ix)
delta_allow = (user_span*100) / defl_lim_val

if design_mode == "Actual Load (from Span)":
    V_design = V_actual
else:
    V_design = V_cap * (target_pct / 100)

# ==========================================
# 4. UI DISPLAY
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection Detail", "💾 Load Table", "📝 Calculation Report"])

with tab1:
    st.subheader(f"Engineering Analysis: {sec_name}")
    cause_color = "#dc2626" if user_cause == "Shear" else ("#d97706" if user_cause == "Moment" else "#059669")
    
    # --- 1. Main Highlight Card ---
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <div style="color:#6b7280; font-size:13px; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">Maximum {label_load}</div>
                <div style="display: flex; align-items: baseline; gap: 10px;">
                    <span style="color:#1d4ed8; font-size:48px; font-weight:800; font-family:'Roboto Mono';">{user_safe_load:,.0f}</span>
                    <span style="font-size:22px; color:#4b5563; font-weight:600;">kg/m</span>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="color:#6b7280; font-size:13px; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:12px;">Governing Factor</div>
                <div style="font-size: 20px; font-weight:800; color:{cause_color}; background-color:{cause_color}15; padding: 8px 24px; border-radius:12px; border: 1px solid {cause_color}30;">
                    {user_cause.upper()}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 2. Calculation Details ---
    with st.expander(f"🕵️‍♂️ Analysis Breakthrough (Detailed Steps)", expanded=True):
        c_cal1, c_cal2, c_cal3 = st.columns(3)
        L_cm_disp = user_span * 100
        
        with c_cal1:
            st.markdown(f'<div class="calc-box"><div class="calc-title">Step 1: Shear Control</div>', unsafe_allow_html=True)
            st.latex(r''' w = \frac{2 \times V_{cap}}{L} \times 100 ''')
            st.latex(fr''' w = \frac{{2 \times {V_cap:,.0f}}}{{{L_cm_disp:,.0f}}} \times 100 ''')
            st.latex(fr''' w = \mathbf{{{w_shear:,.0f}}} \; \text{{kg/m}} ''')
            st.markdown("</div>", unsafe_allow_html=True)

        with c_cal2:
            st.markdown(f'<div class="calc-box" style="border-top-color:#f59e0b;"><div class="calc-title">Step 2: Moment Control</div>', unsafe_allow_html=True)
            st.latex(r''' w = \frac{8 \times M_{cap}}{L^2} \times 100 ''')
            st.latex(fr''' w = \frac{{8 \times {M_cap:,.0f}}}{{{L_cm_disp:,.0f}^2}} \times 100 ''')
            st.latex(fr''' w = \mathbf{{{w_moment:,.0f}}} \; \text{{kg/m}} ''')
            st.markdown("</div>", unsafe_allow_html=True)

        with c_cal3:
            st.markdown(f'<div class="calc-box" style="border-top-color:#10b981;"><div class="calc-title">Step 3: Deflection Control</div>', unsafe_allow_html=True)
            st.latex(r''' w = \frac{384 E I \Delta}{5 L^4} \times 100 ''')
            st.latex(fr''' w = \frac{{384 \cdot {E_mod:.1e} \cdot {Ix} \cdot {delta_allow:.2f}}}{{5 \cdot {L_cm_disp:,.0f}^4}} \times 100 ''')
            st.latex(fr''' w = \mathbf{{{w_defl:,.0f}}} \; \text{{kg/m}} ''')
            st.markdown("</div>", unsafe_allow_html=True)
            
    st.markdown("<br>", unsafe_allow_html=True)

    # --- 3. METRICS CARDS (Enhanced CSS) ---
    cm1, cm2, cm3 = st.columns(3)
    
    def create_card_final(icon, title, actual, limit, unit, color_base, decimal=0):
        pct = (actual / limit) * 100
        width_css = f"{min(pct, 100):.1f}"
        fmt_val = f",.{decimal}f"
        c_status = "#ef4444" if pct > 100 else color_base

        return f"""
        <div class="metric-card-final" style="border-top: 5px solid {c_status};">
            <div class="m-header">
                <div class="m-title"><span>{icon}</span> {title}</div>
                <div class="m-percent" style="color:{c_status};">{pct:.1f}%</div>
            </div>
            <div class="m-values">
                <div style="text-align:left;">
                    <div class="val-label">Actual Usage</div>
                    <div><b>{actual:{fmt_val}}</b></div>
                </div>
                <div style="text-align:right;">
                    <div class="val-label">Limit ({unit})</div>
                    <div style="color:#6b7280; font-weight:700;">{limit:{fmt_val}}</div>
                </div>
            </div>
            <div class="m-bar-bg">
                <div class="m-bar-fill" style="width:{width_css}%; background-color:{c_status};"></div>
            </div>
            <div class="m-check">
                Check Ratio: {actual:{fmt_val}} / {limit:{fmt_val}} = <b>{pct:.1f}%</b>
            </div>
        </div>
        """
    
    with cm1:
        st.markdown(create_card_final("🛡️", "Shear Utilization", V_actual, V_cap, "kg", "#10b981"), unsafe_allow_html=True)
    with cm2:
        st.markdown(create_card_final("🌀", "Moment Utilization", M_actual, M_cap/100, "kg.m", "#f59e0b"), unsafe_allow_html=True)
    with cm3:
        st.markdown(create_card_final("📉", "Deflection Check", delta_actual, delta_allow, "cm", "#3b82f6", decimal=2), unsafe_allow_html=True)

    # --- 4. Graph (Clean Style) ---
    # [คงส่วน Graph เดิมของคุณไว้ แต่ปรับสีเส้นให้ Match กับ UI ใหม่]
    # ...

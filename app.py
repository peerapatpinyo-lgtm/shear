import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- IMPORT MODULES ---
import connection_design as conn
import report_generator as rep

# ==========================================
# 1. SETUP & STYLE (Fixed CSS for Streamlit)
# ==========================================
st.set_page_config(page_title="Beam Insight V12", layout="wide", page_icon="🏗️")

# ใช้ f-string และระวังเรื่องปีกกา { } ใน CSS
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600&family=Roboto+Mono:wght@400;700&display=swap');
    
    html, body, [class*="css"] {{ 
        font-family: 'Sarabun', sans-serif; 
    }}

    .metric-card-clean {{
        background: white;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }}
    
    .mc-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
    .mc-title {{ font-weight: 600; color: #555; font-size: 16px; }}
    .mc-percent {{ font-family: 'Roboto Mono', monospace; font-size: 26px; font-weight: 700; }}

    .mc-values {{ 
        display: flex; justify-content: space-between; align-items: flex-end; 
        font-family: 'Roboto Mono', monospace; margin-bottom: 10px; 
    }}
    .mc-label {{ font-size: 11px; color: #999; text-transform: uppercase; }}
    .mc-val-text {{ font-weight: 600; font-size: 16px; color: #333; }}

    .mc-bar-bg {{ background-color: #eee; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 15px; }}
    .mc-bar-fill {{ height: 100%; border-radius: 4px; }}

    .mc-footer {{ 
        background-color: #fcfcfc; border-top: 1px solid #eee; 
        padding: 10px; text-align: center; 
        font-family: 'Roboto Mono', monospace; font-size: 13px; color: #666;
    }}

    .calc-box {{
        background: #ffffff; border: 1px solid #ddd; border-left: 5px solid #333;
        padding: 15px; border-radius: 5px; margin-bottom: 10px;
    }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA & CALCULATIONS (เหมือนเดิม)
# ==========================================
steel_db = {
    "H 400x200x8x13": {"h": 400, "b": 200, "tw": 8, "tf": 13, "Ix": 23700, "Zx": 1190},
    # ... (เพิ่มตัวอื่นได้ตามต้องการ)
}
# สมมติค่าตัวแปรเพื่อรันตัวอย่าง
sec_name = "H 400x200x8x13"
p = steel_db[sec_name]
user_span = 6.0
fy = 2400
E_mod = 2.04e6
defl_lim_val = 360

# Capacity Logic
V_cap = 0.4 * fy * (p['h']/10 * p['tw']/10)
M_cap = 0.6 * fy * p['Zx']
L_cm = user_span * 100

# กำหนดน้ำหนักบรรทุกที่ยอมรับได้ (w)
w_gov = 3180 # ตัวอย่างค่าที่คำนวณมาได้
V_actual = w_gov * user_span / 2
M_actual = (w_gov * user_span**2) / 8
delta_actual = (5 * (w_gov/100) * (L_cm**4)) / (384 * E_mod * p['Ix'])
delta_allow = L_cm / defl_lim_val

# ==========================================
# 3. UI RENDERING (TAB 1)
# ==========================================
tab1, tab2 = st.tabs(["📊 Analysis", "🔩 Connection"])

with tab1:
    st.subheader("Design Verification")

    # ส่วนรายการคำนวณที่อ่านง่าย
    with st.expander("📝 รายละเอียดการคำนวณ % การใช้งาน (Detailed Design Check)", expanded=True):
        c1, c2, c3 = st.columns(3)
        
        with c1:
            ratio_v = (V_actual / V_cap) * 100
            st.markdown(f"""<div class="calc-box" style="border-left-color: #27ae60;">
                <b>1. Shear Check</b><br>
                Actual: {V_actual:,.0f} kg<br>
                Limit: {V_cap:,.0f} kg<br>
                <b>Ratio: {ratio_v:.1f}%</b>
            </div>""", unsafe_allow_html=True)

        with c2:
            ratio_m = (M_actual / (M_cap/100)) * 100
            st.markdown(f"""<div class="calc-box" style="border-left-color: #f39c12;">
                <b>2. Moment Check</b><br>
                Actual: {M_actual:,.0f} kg.m<br>
                Limit: {M_cap/100:,.0f} kg.m<br>
                <b>Ratio: {ratio_m:.1f}%</b>
            </div>""", unsafe_allow_html=True)

        with c3:
            ratio_d = (delta_actual / delta_allow) * 100
            st.markdown(f"""<div class="calc-box" style="border-left-color: #2980b9;">
                <b>3. Deflection Check</b><br>
                Actual: {delta_actual:.2f} cm<br>
                Limit: {delta_allow:.2f} cm<br>
                <b>Ratio: {ratio_d:.1f}%</b>
            </div>""", unsafe_allow_html=True)

    # --- ส่วน Metric Cards (แก้ไขให้ไม่หลุด) ---
    st.markdown("---")
    m1, m2, m3 = st.columns(3)

    def draw_card(title, actual, limit, unit, color):
        pct = (actual / limit) * 100
        # ใช้ HTML ตรงๆ ไม่ผ่าน f-string ในส่วนที่เสี่ยงหลุด
        card_html = f"""
        <div class="metric-card-clean" style="border-top: 5px solid {color};">
            <div class="mc-header">
                <div class="mc-title">{title}</div>
                <div class="mc-percent" style="color: {color};">{pct:.1f}%</div>
            </div>
            <div class="mc-values">
                <div>
                    <div class="mc-label">ACTUAL</div>
                    <div class="mc-val-text">{actual:,.2f if unit=='cm' else ',.0f'}</div>
                </div>
                <div style="text-align: right;">
                    <div class="mc-label">LIMIT ({unit})</div>
                    <div class="mc-val-text" style="color: #999;">{limit:,.2f if unit=='cm' else ',.0f'}</div>
                </div>
            </div>
            <div class="mc-bar-bg">
                <div class="mc-bar-fill" style="width: {min(pct, 100)}%; background-color: {color};"></div>
            </div>
            <div class="mc-footer">
                {actual:,.1f} ÷ {limit:,.1f} = <b>{pct:.1f}%</b>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

    with m1:
        draw_card("Shear Capacity", V_actual, V_cap, "kg", "#27ae60")
    with m2:
        draw_card("Moment Capacity", M_actual, M_cap/100, "kg.m", "#f39c12")
    with m3:
        draw_card("Deflection Limit", delta_actual, delta_allow, "cm", "#2980b9")

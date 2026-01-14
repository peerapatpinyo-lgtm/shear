import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP
# ==========================================
st.set_page_config(page_title="Structural Insight Pro", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .math-card { background-color: #f8f9fa; border-left: 5px solid #2e86c1; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .limit-label { font-weight: bold; font-size: 14px; }
    .shear-highlight { background-color: #fadbd8; border-left: 5px solid #c0392b; padding: 15px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE & INPUTS
# ==========================================
steel_db = {
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8,  "w": 14.0},
    "H 200x100x5.5x8": {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "w": 21.3},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "w": 29.6},
    "H 300x150x6.5x9": {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 350x175x7x11":  {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "w": 49.6},
    "H 400x200x8x13":  {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 450x200x9x14":  {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "w": 76.0},
    "H 500x200x10x16": {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
}

with st.sidebar:
    st.header("⚙️ Parameters")
    sec_name = st.selectbox("เลือกหน้าตัด (Section)", list(steel_db.keys()), index=3)
    p = steel_db[sec_name]
    
    st.info(f"""
    **{sec_name}** properties:
    * Depth (h): {p['h']} mm
    * Web (tw): {p['tw']} mm
    * Area Web (Aw): {p['h']*p['tw']/100:.2f} cm²
    * Ix: {p['Ix']:,} cm⁴
    * Zx: {p['Zx']:,} cm³
    """)
    
    fy = 2400
    E_mod = 2.04e6

# ==========================================
# 3. CALCULATION ENGINE
# ==========================================
# Constants
h_cm = p['h']/10
tw_cm = p['tw']/10
Aw = h_cm * tw_cm
Ix, Zx = p['Ix'], p['Zx']

# 1. Constant Capacities
V_allow_web = 0.4 * fy * Aw  # kg (Web Shear Strength)
M_allow = 0.6 * fy * Zx      # kg.cm (Bending Strength)

# 2. Curve Generation
spans = np.linspace(2, 16, 100)
curve_shear = []
curve_moment = []
curve_defl = []
curve_safe = []

for L in spans:
    L_cm = L * 100
    
    # Formula 1: Load limited by Shear
    # V = wL/2 -> w = 2V/L
    ws = (2 * V_allow_web) / L_cm * 100 # kg/m
    
    # Formula 2: Load limited by Moment
    # M = wL^2/8 -> w = 8M/L^2
    wm = (8 * M_allow) / (L_cm**2) * 100 # kg/m
    
    # Formula 3: Load limited by Deflection (L/360)
    # delta = 5wL^4 / 384EI -> w = ...
    wd = ((L_cm / 360) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100 # kg/m
    
    curve_shear.append(ws)
    curve_moment.append(wm)
    curve_defl.append(wd)
    curve_safe.append(min(ws, wm, wd))

# ==========================================
# 4. UI DISPLAY
# ==========================================
st.title("🏗️ Beam Limit Analysis: เจาะลึกที่มาของตัวเลข")

tab1, tab2 = st.tabs(["📊 กราฟวิเคราะห์ (Analysis)", "📝 รายละเอียดจุดต่อ (Detailing)"])

with tab1:
    col_chart, col_explain = st.columns([1.8, 1.2])
    
    with col_chart:
        st.subheader("📉 กราฟเส้น Limit (Shear vs Moment vs Deflection)")
        
        fig = go.Figure()
        
        # 1. Shear Limit Line (RED)
        fig.add_trace(go.Scatter(
            x=spans, y=curve_shear, mode='lines', 
            name='1. Shear Limit (Web)', 
            line=dict(color='#e74c3c', width=2, dash='dash')
        ))
        
        # 2. Moment Limit Line (ORANGE)
        fig.add_trace(go.Scatter(
            x=spans, y=curve_moment, mode='lines', 
            name='2. Moment Limit', 
            line=dict(color='#f39c12', width=2, dash='dash')
        ))
        
        # 3. Deflection Limit Line (GREEN)
        fig.add_trace(go.Scatter(
            x=spans, y=curve_defl, mode='lines', 
            name='3. Deflection Limit (L/360)', 
            line=dict(color='#27ae60', width=2, dash='dash')
        ))
        
        # 4. Safe Zone (FILLED)
        fig.add_trace(go.Scatter(
            x=spans, y=curve_safe, mode='lines', 
            name='✅ Safe Capacity', 
            fill='tozeroy', fillcolor='rgba(46, 134, 193, 0.1)',
            line=dict(color='#2E86C1', width=4)
        ))

        # Layout
        fig.update_layout(
            xaxis_title="ความยาวคาน (m)",
            yaxis_title="รับน้ำหนักปลอดภัย (kg/m)",
            hovermode="x unified",
            height=500,
            yaxis=dict(range=[0, max(curve_safe)*1.5]),
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Slider for interaction
        sel_span = st.slider("🔍 เลือก Span เพื่อดูการคำนวณด้านขวา (m)", 2.0, 15.0, 4.0, 0.5)

    with col_explain:
        # Calculate specific values for selected span
        idx = (np.abs(spans - sel_span)).argmin()
        val_s = curve_shear[idx]
        val_m = curve_moment[idx]
        val_d = curve_defl[idx]
        
        st.subheader(f"🧮 แกะสูตรที่ Span {sel_span} เมตร")
        st.write("คานตัวนี้รับน้ำหนักได้สูงสุดเท่าไร? มาดูตัวเลขจริงกัน:")
        
        # --- 1. SHEAR EXPLANATION (HIGHLIGHT) ---
        st.markdown('<div class="limit-label" style="color:#c0392b;">1. ขีดจำกัดแรงเฉือน (Shear Limit)</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="shear-highlight">
            <b>ที่มา:</b> เอวคาน (Web) ต้องไม่ขาด<br>
            <b>พื้นที่รับแรง ($A_w$):</b> {p['h']/10} cm x {p['tw']/10} cm = <b>{Aw:.2f} cm²</b><br>
            <b>แรงเฉือนสูงสุดที่รับได้ ($V_{{max}}$):</b><br>
            $0.4 \\times F_y \\times A_w = 0.4 \\times 2400 \\times {Aw:.2f}$<br>
            $= \\mathbf{{{V_allow_web:,.0f}}}$ <b>kg</b> (ค่าคงที่)<br>
            <hr style="margin:5px 0; border-top:1px solid #d98880;">
            <b>แปลงเป็น Uniform Load ($w_{{shear}}$):</b><br>
            จากสูตร $V = wL/2 \Rightarrow w = 2V/L$<br>
            $w = (2 \\times {V_allow_web:,.0f}) / {sel_span}$<br>
            $= \\mathbf{{{val_s:,.0f}}}$ <b>kg/m</b>
        </div>
        """, unsafe_allow_html=True)
        
        # --- 2. MOMENT EXPLANATION ---
        st.markdown('<div class="limit-label" style="color:#d35400;">2. ขีดจำกัดโมเมนต์ (Moment Limit)</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="math-card" style="border-left-color: #f39c12;">
            <b>ที่มา:</b> คานต้องไม่คราก (Yield) จากการดัด<br>
            <b>โมเมนต์ต้านทาน ($M_{{allow}}$):</b><br>
            $0.6 \\times 2400 \\times {Zx} = \\mathbf{{{M_allow:,.0f}}}$ <b>kg.cm</b><br>
            <b>แปลงเป็น Uniform Load ($w_{{moment}}$):</b><br>
            จากสูตร $M = wL^2/8 \Rightarrow w = 8M/L^2$<br>
            $w = (8 \\times {M_allow:,.0f}) / ({sel_span} \\times 100)^2 \\times 100$<br>
            $= \\mathbf{{{val_m:,.0f}}}$ <b>kg/m</b>
        </div>
        """, unsafe_allow_html=True)
        
        # --- 3. DEFLECTION EXPLANATION ---
        st.markdown('<div class="limit-label" style="color:#27ae60;">3. ขีดจำกัดการแอ่นตัว (Deflection Limit)</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="math-card" style="border-left-color: #27ae60;">
            <b>ที่มา:</b> แอ่นไม่เกิน L/360 ({sel_span*100/360:.2f} cm)<br>
            $= \\mathbf{{{val_d:,.0f}}}$ <b>kg/m</b>
        </div>
        """, unsafe_allow_html=True)
        
        # CONCLUSION
        final_val = min(val_s, val_m, val_d)
        gov_mode = "Shear" if final_val==val_s else ("Moment" if final_val==val_m else "Deflection")
        st.info(f"🏆 **สรุป:** ค่าน้อยที่สุดคือ **{final_val:,.0f} kg/m** (ควบคุมโดย {gov_mode})")

# ==========================================
# TAB 2: PLACEHOLDER FOR DETAILING
# ==========================================
with tab2:
    st.info("หน้านี้สำหรับออกแบบ Connection Detail (น็อต/เพลท) ตาม Reaction ที่ได้จาก Tab 1")
    st.metric("Design Reaction (V) from Tab 1", f"{final_val * sel_span / 2:,.0f} kg")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Connection Master Pro", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .big-card { background-color: #f8f9f9; padding: 20px; border-radius: 10px; border-left: 5px solid #2e86c1; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .metric-val { font-size: 26px; font-weight: bold; color: #154360; }
    .metric-lbl { font-size: 14px; color: #7f8c8d; }
    .warning-box { background-color: #fdedec; color: #943126; padding: 10px; border-radius: 5px; font-size: 13px; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE & INPUTS
# ==========================================
steel_db = {
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8,  "ry": 1.66, "w": 14.0},
    "H 200x100x5.5x8": {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "ry": 2.22, "w": 21.3},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "ry": 2.79, "w": 29.6},
    "H 300x150x6.5x9": {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "ry": 3.29, "w": 36.7},
    "H 350x175x7x11":  {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "ry": 3.86, "w": 49.6},
    "H 400x200x8x13":  {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "ry": 4.54, "w": 66.0},
    "H 450x200x9x14":  {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "ry": 4.43, "w": 76.0},
    "H 500x200x10x16": {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "ry": 4.33, "w": 89.6},
    "H 600x200x11x17": {"h": 600, "b": 200, "tw": 11,  "tf": 17,  "Ix": 77600,  "Zx": 2590,  "w": 106},
}

with st.sidebar:
    st.header("🎛️ Parameters")
    sec_name = st.selectbox("Section", list(steel_db.keys()), index=5) # Default H400
    p = steel_db[sec_name]
    
    st.divider()
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
    
    # Advanced Toggle
    show_advanced = st.checkbox("Show Advanced Check (LTB)", value=False)
    Lb = 0.0
    if show_advanced:
        bracing = st.radio("Lateral Bracing", ["Full Support", "Ends Only"])
        span_input_ref = st.number_input("Design Span (m)", 6.0)
        Lb = span_input_ref if bracing == "Ends Only" else 0.0

    fy = 2400

# ==========================================
# 3. LOGIC CORE
# ==========================================
# 3.1 Properties
h_cm, tw_cm = p['h']/10, p['tw']/10
Aw = h_cm * tw_cm
Zx = p['Zx']

# 3.2 Capacities
V_web_max = 0.4 * fy * Aw  # Max Shear Limit (Web Yield)
M_allow = 0.6 * fy * Zx    # Allowable Moment

# Check LTB Reduction (Optional Logic)
reduction = 1.0
if show_advanced and Lb > 0:
    # Simplified LTB check for reduction factor display
    Lb_cm = Lb * 100
    Lc_approx = (200 * p['b']/10) / math.sqrt(fy)
    if Lb_cm > Lc_approx:
        reduction = max(0.6, 1.0 - (0.002 * (Lb_cm/p['ry'])))
        M_allow *= reduction

# 3.3 Bolt Capacity
dia_cm = int(bolt_size[1:])/10
area = 3.14 * (dia_cm/2)**2 if bolt_size != "M16" else 2.01
phi_shear = 1000 * area # Shear
phi_bear = 1.2 * 4000 * dia_cm * tw_cm # Bearing
bolt_cap = min(phi_shear, phi_bear)

# 3.4 Generate "Efficiency Curve" Data
# Span Range: 2D to 25D
d_m = p['h']/1000
spans = np.linspace(d_m*3, d_m*30, 100)
v_design = []
limit_mode = []

for L in spans:
    L_cm = L * 100
    # 1. Shear from Moment Capacity (Uniform Load Assumption)
    # M = wL^2/8 -> w = 8M/L^2
    # V = wL/2 = (8M/L^2)*L/2 = 4M/L
    V_from_M = (4 * M_allow) / L_cm # kg
    
    # 2. Compare with Web Limit
    if V_from_M > V_web_max:
        v_design.append(V_web_max)
        limit_mode.append("Web Shear")
    else:
        v_design.append(V_from_M)
        limit_mode.append("Moment Control")

# Typical Point (10D)
L_typ = d_m * 10
V_typ = min(V_web_max, (4 * M_allow) / (L_typ * 100))
bolts_typ = math.ceil(V_typ / bolt_cap)

# ==========================================
# 4. DASHBOARD UI
# ==========================================
st.title("🔩 Connection Efficiency Master")

tab1, tab2, tab3 = st.tabs(["📈 The Efficiency Graph", "📝 Calculation Sheet", "📚 Theory"])

# --- TAB 1: THE GRAPH YOU LIKE ---
with tab1:
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    
    with col_kpi1:
        st.markdown(f"""
        <div class="big-card">
            <div class="metric-lbl">🔥 Max Web Capacity</div>
            <div class="metric-val" style="color:#c0392b;">{V_web_max/1000:,.1f} Ton</div>
            <div class="metric-lbl">ลิมิตสูงสุด (คานสั้นมาก)</div>
        </div>""", unsafe_allow_html=True)
        
    with col_kpi2:
        st.markdown(f"""
        <div class="big-card" style="border-left: 5px solid #27ae60;">
            <div class="metric-lbl">✅ Recommended (10D)</div>
            <div class="metric-val" style="color:#27ae60;">{V_typ/1000:,.1f} Ton</div>
            <div class="metric-lbl">ที่ Span {L_typ:.1f} m.</div>
        </div>""", unsafe_allow_html=True)
        
    with col_kpi3:
        st.markdown(f"""
        <div class="big-card" style="border-left: 5px solid #f39c12;">
            <div class="metric-lbl">🔩 Bolt Quantity</div>
            <div class="metric-val" style="color:#d35400;">{bolts_typ} x {bolt_size}</div>
            <div class="metric-lbl">สำหรับ Typical Span</div>
        </div>""", unsafe_allow_html=True)
        
    if reduction < 1.0:
        st.warning(f"⚠️ Warning: Moment Capacity reduced by {(1-reduction)*100:.0f}% due to Lateral Torsional Buckling (LTB).")

    st.markdown("---")
    
    # GRAPH PLOTTING (THE CLASSIC STYLE)
    c_chart, c_tbl = st.columns([2, 1])
    
    with c_chart:
        st.subheader("กราฟความสัมพันธ์ Span vs Shear Design")
        st.caption("กราฟนี้แสดงให้เห็นว่ายิ่งคานยาว แรงเฉือนที่เกิดขึ้นจริงจะลดลงตามธรรมชาติของ Moment")
        
        fig = go.Figure()
        
        # 1. Main Curve
        fig.add_trace(go.Scatter(
            x=spans, y=[v/1000 for v in v_design], 
            mode='lines', name='Design Shear Force',
            line=dict(color='#2E86C1', width=4),
            fill='tozeroy', fillcolor='rgba(46, 134, 193, 0.1)'
        ))
        
        # 2. Web Limit Line
        fig.add_trace(go.Scatter(
            x=[spans[0], spans[-1]], y=[V_web_max/1000, V_web_max/1000],
            mode='lines', name='Web Shear Limit',
            line=dict(color='red', dash='dash', width=2)
        ))
        
        # 3. Typical Point Marker
        fig.add_trace(go.Scatter(
            x=[L_typ], y=[V_typ/1000],
            mode='markers+text', name='Recommended (10D)',
            marker=dict(size=14, color='#27ae60', symbol='diamond', line=dict(color='white', width=2)),
            text=[f"{V_typ/1000:.1f}T"], textposition="top right"
        ))
        
        # Zones
        fig.add_vrect(x0=spans[0], x1=d_m*8, fillcolor="red", opacity=0.05, annotation_text="Short Span", annotation_position="top left")
        fig.add_vrect(x0=d_m*8, x1=d_m*15, fillcolor="green", opacity=0.05, annotation_text="Typical Zone", annotation_position="top")
        fig.add_vrect(x0=d_m*15, x1=spans[-1], fillcolor="blue", opacity=0.05, annotation_text="Long Span", annotation_position="top right")
        
        fig.update_layout(
            xaxis_title="Span Length (m)",
            yaxis_title="Design Shear Force (Ton)",
            hovermode="x unified",
            height=450,
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with c_tbl:
        st.subheader("💡 Decision Matrix")
        # Dynamic Table based on Graph
        steps = [0.8, 0.6, 0.5, 0.4, 0.3] # % of Max Web
        tbl_data = []
        for p_load in steps:
            load = V_web_max * p_load
            nb = math.ceil(load / bolt_cap)
            
            # Find span that matches this load
            # V = 4M/L -> L = 4M/V
            match_L = (4 * M_allow) / load / 100
            
            remark = ""
            if 0.45 <= p_load <= 0.55: remark = "⭐ Best Fit"
            
            tbl_data.append({
                "% Web": f"{p_load*100:.0f}%",
                "Shear (T)": f"{load/1000:.1f}",
                "Span ~ (m)": f"{match_L:.1f}",
                "Bolts": nb,
                "Note": remark
            })
            
        st.dataframe(pd.DataFrame(tbl_data), use_container_width=True, hide_index=True)
        st.info("ตารางนี้ช่วยให้คุณเลือก 'ความคุ้มค่า' ได้ทันที โดยไม่ต้องคำนวณใหม่")

# --- TAB 2: PRO CALCULATION ---
with tab2:
    st.subheader("📄 Auto-Generated Calculation Sheet")
    
    # Calculate values for report (based on Typical 10D or user input if advanced)
    rep_L = L_typ
    rep_V = V_typ
    if show_advanced:
        rep_L = span_input_ref
        rep_V = min(V_web_max, (4 * M_allow) / (rep_L * 100))
    
    rep_bolts = math.ceil(rep_V / bolt_cap)
    
    report = f"""
CALCULATION SHEET
SUBJECT: BEAM CONNECTION DESIGN
--------------------------------------------------
1. DESIGN DATA
   Section      : {sec_name}
   Span Length  : {rep_L:.2f} m
   Steel Grade  : SS400 (Fy = {fy} ksc)
   Bolt Grade   : A325 / F10T
   Bolt Size    : {bolt_size}

2. ALLOWABLE STRESS
   Allowable Shear (Fv) : {0.4*fy} ksc
   Allowable Bend (Fb)  : {0.6*fy*reduction:.0f} ksc (LTB Factor = {reduction:.2f})

3. LOAD ANALYSIS
   Max Web Shear Cap    : {V_web_max/1000:,.2f} Tons
   Moment Limited Shear : {(4*M_allow/rep_L/100)/1000:,.2f} Tons
   
   >> DESIGN SHEAR (V)  : {rep_V/1000:,.2f} Tons

4. CONNECTION CHECK
   Bolt Shear Capacity  : {phi_shear:,.0f} kg/bolt
   Plate Bearing Cap    : {phi_bear:,.0f} kg/bolt
   Governing Capacity   : {bolt_cap:,.0f} kg/bolt
   
   REQUIRED BOLTS       : {rep_V:,.0f} / {bolt_cap:,.0f} = {rep_V/bolt_cap:.2f}
   >> USE               : {rep_bolts} x {bolt_size}

5. DETAILING
   Pitch (3d)           : {3 * int(bolt_size[1:]):.0f} mm
   Edge (1.5d)          : {1.5 * int(bolt_size[1:]):.0f} mm
--------------------------------------------------
    """
    st.text_area("Copy for Report", report, height=500)

# --- TAB 3: THEORY ---
with tab3:
    st.markdown("### 📚 Engineering Logic (ที่มาของกราฟ)")
    st.markdown("""
    กราฟความสัมพันธ์ (Efficiency Curve) สร้างขึ้นจาก 2 เงื่อนไข:
    
    1. **Web Shear Limit (เส้นประสีแดง):** เป็นขีดจำกัดทางกายภาพของเหล็ก เอวคานรับแรงได้สูงสุดเท่านี้ไม่ว่าคานจะสั้นแค่ไหน
       $$V_{max} = 0.4 \cdot F_y \cdot A_w$$
       
    2. **Moment Control Limit (เส้นโค้งสีฟ้า):**
       เมื่อคานยาวขึ้น โมเมนต์ดัดจะเป็นตัวควบคุม ทำให้แรงเฉือนที่ปลายคาน (Reaction) ลดลงตามสมการ:
       $$V = \frac{4 \cdot M_{allow}}{L}$$
       *(สมการนี้แปลงมาจาก Uniform Load: $M = wL^2/8$ และ $V=wL/2$)*
       
    **สรุป:** เราจึงไม่จำเป็นต้องออกแบบ Connection ให้รับแรง 100% Web Limit เสมอไป หากคานมีความยาวอยู่ในช่วง Typical (โซนสีเขียว)
    """)

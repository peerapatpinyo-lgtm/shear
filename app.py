import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Structure Master Pro", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .big-card { background-color: #f0f8ff; padding: 20px; border-radius: 10px; border: 1px solid #add8e6; margin-bottom: 10px;}
    .opt-card { background-color: #d4efdf; padding: 20px; border-radius: 10px; border-left: 5px solid #27ae60; }
    .warn-card { background-color: #fdedec; padding: 20px; border-radius: 10px; border-left: 5px solid #c0392b; }
    .metric-val { font-size: 24px; font-weight: bold; color: #154360; }
    .metric-lbl { font-size: 14px; color: #566573; }
    .pass { color: green; font-weight: bold; }
    .fail { color: red; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE
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

# ==========================================
# 3. SIDEBAR (Global Inputs)
# ==========================================
with st.sidebar:
    st.header("1. เลือกหน้าตัดคาน (Main Input)")
    sec_name = st.selectbox("Section Size", list(steel_db.keys()), index=5)
    p = steel_db[sec_name]
    
    st.info(f"""
    **{sec_name}**
    * Weight: {p['w']} kg/m
    * Depth: {p['h']} mm
    * Web: {p['tw']} mm
    """)
    
    st.markdown("---")
    st.header("2. วัสดุ (Material)")
    fy = st.number_input("Fy (ksc)", 2400)
    fu = st.number_input("Fu (ksc)", 4000)
    E_mod = 2.04e6

# ==========================================
# 4. CALCULATION: BEAM CAPACITY
# ==========================================
# Properties
h_cm, tw_cm = p['h']/10, p['tw']/10
Ix, Zx = p['Ix'], p['Zx']
Aw = h_cm * tw_cm

# Limits
M_allow = 0.6 * fy * Zx
V_allow_web = 0.4 * fy * Aw

# Optimal Range (15d - 20d)
opt_min = 15 * (p['h']/1000)
opt_max = 20 * (p['h']/1000)

# Generate Curve Data
spans = np.linspace(2, 16, 100)
w_gov, gov_cause = [], []

for L in spans:
    L_cm = L * 100
    ws = (2 * V_allow_web) / L_cm * 100 # Shear Limit Load
    wm = (8 * M_allow) / (L_cm**2) * 100 # Moment Limit Load
    wd = ((L_cm / 360) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100 # Deflection Limit (L/360)
    
    min_w = min(ws, wm, wd)
    w_gov.append(min_w)
    
    if min_w == ws: gov_cause.append("Shear")
    elif min_w == wm: gov_cause.append("Moment")
    else: gov_cause.append("Deflection")

# ==========================================
# 5. UI TABS
# ==========================================
st.title("🏗️ Structural Beam & Connection Studio")

tab1, tab2 = st.tabs(["📊 1. หา Span & Load ที่เหมาะสม", "🛠️ 2. ออกแบบรายละเอียดจุดต่อ (Detailing)"])

# ==========================================
# TAB 1: BEAM SELECTION & OPTIMAL SPAN
# ==========================================
with tab1:
    st.subheader(f"วิเคราะห์ขีดความสามารถ: {sec_name}")
    
    col_main1, col_main2 = st.columns([1, 2])
    
    with col_main1:
        # Optimal Recommendation
        st.markdown(f"""
        <div class="opt-card">
            <h3 style="margin:0">✅ Optimal Span</h3>
            <div class="metric-val">{opt_min:.1f} - {opt_max:.1f} m</div>
            <div class="metric-lbl">ช่วงความยาวที่แนะนำ (L/d = 15-20)</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        # Span Slider
        st.markdown("👇 **เลือกความยาวคานที่จะใช้จริง:**")
        user_span = st.slider("Span Length (m)", 2.0, 16.0, (opt_min+opt_max)/2, 0.5)
        
        # Get Values
        idx = (np.abs(spans - user_span)).argmin()
        safe_load = w_gov[idx]
        reaction = safe_load * user_span / 2
        cause = gov_cause[idx]
        
        st.markdown(f"""
        <div class="big-card">
            <div class="metric-lbl">Safe Uniform Load</div>
            <div class="metric-val">{safe_load:,.0f} kg/m</div>
            <div class="metric-lbl">Limited by: <b>{cause}</b></div>
            <hr>
            <div class="metric-lbl">End Reaction (V)</div>
            <div class="metric-val" style="color:#d35400">{reaction:,.0f} kg</div>
            <div class="metric-lbl">ใช้ค่านี้ไปออกแบบจุดต่อใน Tab 2</div>
        </div>
        """, unsafe_allow_html=True)

    with col_main2:
        # THE GRAPH
        st.markdown("##### 📈 กราฟแสดงความสามารถรับน้ำหนัก (Safe Load Capacity)")
        fig = go.Figure()
        
        # Safe Zone
        fig.add_trace(go.Scatter(x=spans, y=w_gov, fill='tozeroy', mode='lines', 
                                 name='Safe Load', line=dict(color='#2E86C1', width=3)))
        
        # Highlight Optimal Zone
        fig.add_vrect(x0=opt_min, x1=opt_max, fillcolor="green", opacity=0.1, 
                      annotation_text="Optimal Zone", annotation_position="top")
        
        # User Point
        fig.add_trace(go.Scatter(x=[user_span], y=[safe_load], mode='markers', 
                                 marker=dict(size=12, color='red', line=dict(width=2, color='white')),
                                 name='Selected Span'))
        
        fig.update_layout(xaxis_title="Span Length (m)", yaxis_title="Safe Uniform Load (kg/m)", 
                          hovermode="x unified", height=450)
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TAB 2: DETAILED CONNECTION (THE DEEP DIVE)
# ==========================================
with tab2:
    st.subheader("🛠️ Connection Design Studio")
    
    # ดึงค่า Reaction จาก Tab 1 มาเป็นค่าตั้งต้น (แต่แก้ได้)
    col_inp1, col_inp2 = st.columns(2)
    
    with col_inp1:
        st.markdown("#### A. Load & Bolts")
        vu_input = st.number_input("Design Shear (kg) [ดึงมาจาก Tab 1]", value=float(reaction), step=100.0)
        bolt_grade = st.selectbox("Bolt Grade", ["A325 (N)", "A307", "A490"], index=0)
        bolt_dia = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
        
    with col_inp2:
        st.markdown("#### B. Plate & Geometry")
        n_rows = st.number_input("จำนวนแถวน็อต (Rows)", 2, 10, 3)
        plate_t = st.selectbox("ความหนา Plate (mm)", [6, 9, 12, 16, 20], index=1)
        # Auto calc geometry suggestion
        d_mm = int(bolt_dia[1:])
        pitch = st.number_input("ระยะห่าง (Pitch) mm", value=3*d_mm)
        edge_v = st.number_input("ระยะขอบตั้ง (Lev) mm", value=1.5*d_mm)
        edge_h = st.number_input("ระยะขอบนอน (Leh) mm", value=40)

    st.markdown("---")
    
    # --- ENGINEERING CALCULATION (Hidden Logic) ---
    # Props
    db = d_mm / 10
    dh = db + 0.2
    tp = plate_t / 10
    
    # 1. Bolt Shear
    fv = 3720 if "A325" in bolt_grade else 1900
    rn_bolt = n_rows * (3.14*(db/2)**2) * fv
    
    # 2. Bearing (Web & Plate)
    rn_bear_web = n_rows * (1.2 * fu * db * tw_cm)
    rn_bear_pl = n_rows * (1.2 * fu * db * tp)
    
    # 3. Block Shear (Web)
    s, ev, eh = pitch/10, edge_v/10, edge_h/10
    L_gv = ev + (n_rows-1)*s
    L_nv = L_gv - (n_rows-0.5)*dh
    L_nt = eh - 0.5*dh
    
    def block_shear(Fy, Fu, t, Agv, Anv, Ant):
        return min(0.6*Fu*Anv + 1.0*Fu*Ant, 0.6*Fy*Agv + 1.0*Fu*Ant)
        
    rn_bs_web = block_shear(fy, fu, tw_cm, L_gv*tw_cm, L_nv*tw_cm, L_nt*tw_cm)
    rn_bs_pl = block_shear(2400, 4000, tp, L_gv*tp, L_nv*tp, L_nt*tp) # Plate SS400
    
    # 4. Plate Yield/Rupture
    H_pl = L_gv + ev
    rn_pl_yield = 0.6 * 2400 * H_pl * tp
    rn_pl_rup = 0.6 * 4000 * (H_pl - n_rows*dh) * tp
    
    # Collect Results
    checks = {
        "Bolt Shear": rn_bolt,
        "Bearing (Web)": rn_bear_web,
        "Bearing (Plate)": rn_bear_pl,
        "Block Shear (Web)": rn_bs_web,
        "Block Shear (Plate)": rn_bs_pl,
        "Plate Yield": rn_pl_yield,
        "Plate Rupture": rn_pl_rup
    }
    min_cap = min(checks.values())
    limit_mode = min(checks, key=checks.get)
    
    # --- DISPLAY RESULTS ---
    col_res_L, col_res_R = st.columns([1.5, 1])
    
    with col_res_L:
        st.markdown("### 📋 Detailed Check List")
        
        # Loop to show bars
        for mode, cap in checks.items():
            ratio = vu_input / cap
            is_pass = ratio <= 1.0
            color = "#27ae60" if is_pass else "#c0392b"
            icon = "✅" if is_pass else "❌"
            
            st.markdown(f"""
            <div style="margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between;">
                    <span>{icon} <b>{mode}</b></span>
                    <span>Cap: {cap:,.0f} kg</span>
                </div>
                <div style="width:100%; background:#eee; height:8px; border-radius:4px;">
                    <div style="width:{min(ratio*100, 100)}%; background:{color}; height:100%; border-radius:4px;"></div>
                </div>
                <small style="color:#777">Demand: {vu_input:,.0f} kg | Ratio: {ratio:.2f}</small>
            </div>
            """, unsafe_allow_html=True)
            
    with col_res_R:
        st.markdown("### 🏁 Conclusion")
        status = "PASSED" if min_cap >= vu_input else "FAILED"
        bg_col = "#d4efdf" if status=="PASSED" else "#fadbd8"
        
        st.markdown(f"""
        <div style="background-color:{bg_col}; padding:20px; border-radius:10px; text-align:center; border: 1px solid #ccc;">
            <h2 style="margin:0; color:{'green' if status=='PASSED' else 'red'}">{status}</h2>
            <hr>
            <div class="metric-lbl">Governing Capacity</div>
            <div class="metric-val">{min_cap:,.0f} kg</div>
            <div class="metric-lbl">Controlled by: <b>{limit_mode}</b></div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("ℹ️ Help: Block Shear คือ?"):
            st.write("การวิบัติโดยที่เนื้อเหล็กฉีกหลุดออกมาเป็นก้อน (สี่เหลี่ยม) มักเกิดเมื่อใช้ Bolts หลายตัวแต่เหล็กบาง")
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Block_shear_failure.svg/300px-Block_shear_failure.svg.png", caption="Block Shear Concept")

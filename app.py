import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Ultimate Connection Analyst", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .mode-card { padding: 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #ddd; }
    .pass { background-color: #d4efdf; border-left: 5px solid #27ae60; color: #145a32; }
    .fail { background-color: #fadbd8; border-left: 5px solid #c0392b; color: #7b241c; }
    .warning { background-color: #fcf3cf; border-left: 5px solid #f1c40f; color: #7d6608; }
    .metric-val { font-size: 24px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE (Added Fu for Block Shear)
# ==========================================
# SS400 -> Fy=2400 ksc, Fu=4000 ksc
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
    st.header("⚙️ Configuration")
    sec_name = st.selectbox("Section Size", list(steel_db.keys()), index=5)
    p = steel_db[sec_name]
    
    st.divider()
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
    
    # Material Props
    fy = 2400 # ksc
    fu = 4000 # ksc (Ultimate Strength needed for Block Shear)
    
    st.info(f"**Props:** A_w={p['h']/10*p['tw']/10:.1f} cm² | Zx={p['Zx']}")

# ==========================================
# 3. ADVANCED CALCULATIONS
# ==========================================
# 3.1 Standard Props
h_cm = p['h']/10
tw_cm = p['tw']/10
Aw = h_cm * tw_cm
d_bolt = int(bolt_size[1:])/10 # cm
d_hole = d_bolt + 0.2 # Standard hole clearance

# 3.2 Basic Capacities
# Web Yielding
V_yield = 0.4 * fy * Aw 

# Shear Buckling (Simplified AISC for rolled shapes: Cv=1.0 usually)
# If h/tw > 1.1*sqrt(kv*E/Fy), reduction applies. For rolled H-Beam, usually safe.
V_buckle = V_yield # Assuming compact web for rolled sections

# Bolt Capacity (Single Bolt)
area_b = 3.14 * (d_bolt/2)**2 if bolt_size != "M16" else 2.01
phi_bolt_shear = 1000 * area_b
phi_bolt_bear  = 1.2 * fu * d_bolt * tw_cm
cap_per_bolt = min(phi_bolt_shear, phi_bolt_bear)

# 3.3 DYNAMIC BLOCK SHEAR CALCULATION
# Function to calc Block Shear based on N bolts
def calc_block_shear(n_bolts, dia_h, t_web, Fu, Fy):
    if n_bolts < 2: return V_yield # Block shear needs >1 bolt to form a block
    
    # Standard Detailing Assumption
    pitch = 3 * d_bolt # Vertical spacing
    edge_v = 1.5 * d_bolt # Top edge to first bolt
    edge_h = 1.5 * d_bolt # Side edge
    
    # 1. Shear Area (Vertical Line)
    L_gv = edge_v + (n_bolts - 1) * pitch # Gross Length Shear
    L_nv = L_gv - (n_bolts - 0.5) * dia_h # Net Length Shear
    A_gv = L_gv * t_web
    A_nv = L_nv * t_web
    
    # 2. Tension Area (Horizontal Line)
    L_gt = edge_h
    L_nt = L_gt - 0.5 * dia_h
    A_nt = L_nt * t_web
    
    # AISC Equation J4-5
    # Rbs = 0.6*Fu*Anv + Ubs*Fu*Ant <= 0.6*Fy*Agv + Ubs*Fu*Ant
    # Ubs = 1.0 for uniform stress
    term1 = 0.6 * Fu * A_nv + 1.0 * Fu * A_nt
    term2 = 0.6 * Fy * A_gv + 1.0 * Fu * A_nt
    
    return min(term1, term2)

# ==========================================
# 4. MAIN LOGIC (LOOP SPANS)
# ==========================================
spans = np.linspace(p['h']/1000*3, 15, 80)
res_shear = []
res_moment_limit = []
res_block_shear = [] # Dynamic limit curve
res_govern = []
fail_mode = []

for L in spans:
    L_cm = L * 100
    
    # 1. Demand from Moment (V = 4M/L)
    M_allow = 0.6 * fy * p['Zx']
    V_demand_curve = (4 * M_allow) / L_cm # Curve line
    
    # 2. Calculate Block Shear for this demand
    # How many bolts needed for this V?
    req_n = math.ceil(V_demand_curve / cap_per_bolt)
    req_n = max(2, req_n) # Minimum 2 bolts
    
    # Calc Block Shear Cap for THIS layout
    V_bs = calc_block_shear(req_n, d_hole, tw_cm, fu, fy)
    
    # 3. Determine Governor
    # Limits: Web Yield (Fixed), Buckling (Fixed), Block Shear (Variable with N), Moment Curve
    
    limits = {
        "Web Yield": V_yield,
        "Block Shear": V_bs,
        "Moment Limit": V_demand_curve
    }
    
    # Current governing capacity (min of physical limits)
    phy_limit = min(V_yield, V_bs) 
    
    # Design Shear is strictly limited by Moment Curve, but capped by Physical Limits
    design_shear = min(V_demand_curve, phy_limit)
    
    res_shear.append(design_shear)
    res_moment_limit.append(V_demand_curve)
    res_block_shear.append(V_bs)
    
    if design_shear == V_yield: fail_mode.append("Web Yield")
    elif design_shear == V_bs: fail_mode.append("Block Shear")
    else: fail_mode.append("Moment Control")

# ==========================================
# 5. UI DISPLAY
# ==========================================
st.title("🛡️ Advanced Shear Analysis (Block Shear Included)")

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📊 Hierarchy of Failure Modes")
    st.caption("กราฟนี้เพิ่มเส้น 'Block Shear' (เส้นสีม่วง) ซึ่งแปรผันตามจำนวนน็อตที่ต้องใช้")
    
    fig = go.Figure()
    
    # 1. Moment Curve
    fig.add_trace(go.Scatter(x=spans, y=[v/1000 for v in res_moment_limit], 
                             name="Moment Limit Curve", line=dict(color='lightblue', dash='dot')))
    
    # 2. Web Yield Limit (Constant)
    fig.add_trace(go.Scatter(x=spans, y=[V_yield/1000]*len(spans), 
                             name="Web Yield Limit", line=dict(color='red', dash='dash')))
    
    # 3. Block Shear Limit (Step Function)
    fig.add_trace(go.Scatter(x=spans, y=[v/1000 for v in res_block_shear], 
                             name="Block Shear Limit", line=dict(color='purple', shape='hv')))
    
    # 4. Actual Safe Design Zone
    fig.add_trace(go.Scatter(x=spans, y=[v/1000 for v in res_shear], 
                             name="Safe Design Shear", fill='tozeroy', line=dict(color='#2E86C1', width=4)))

    fig.update_layout(xaxis_title="Span (m)", yaxis_title="Shear (Ton)", height=500, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🔍 Spot Check")
    check_L = st.number_input("Check Span (m)", 2.0, 15.0, 4.0, 0.5)
    
    # Calc Specifics
    idx = (np.abs(spans - check_L)).argmin()
    v_dem = res_moment_limit[idx]
    v_bs = res_block_shear[idx]
    v_yld = V_yield
    
    n_bolt_req = math.ceil(v_dem / cap_per_bolt)
    
    # Logic Display
    st.write(f"**At L = {check_L} m:**")
    st.write(f"🔩 Bolts Req: **{n_bolt_req}** pcs")
    
    # 1. Web Yield Check
    st.markdown(f"""
    <div class="mode-card warning">
        <small>1. Web Yield Limit</small><br>
        <span class="metric-val">{v_yld/1000:.1f} T</span>
    </div>
    """, unsafe_allow_html=True)

    # 2. Block Shear Check
    status_bs = "pass" if v_bs >= v_dem else "fail"
    st.markdown(f"""
    <div class="mode-card {status_bs}">
        <small>2. Block Shear Limit (ที่ {n_bolt_req} bolts)</small><br>
        <span class="metric-val">{v_bs/1000:.1f} T</span><br>
        <small>มักต่ำกว่า Yield เมื่อใช้น็อตเยอะ</small>
    </div>
    """, unsafe_allow_html=True)
    
    

    # 3. Conclusion
    final_cap = min(v_yld, v_bs, v_dem)
    st.success(f"✅ Safe Design: {final_cap/1000:.2f} Ton")

st.markdown("---")
st.subheader("📚 Theory: Block Shear (อันตรายที่มองไม่เห็น)")
c1, c2 = st.columns(2)
with c1:
    st.markdown("""
    **Block Shear Rupture** คือการวิบัติที่เนื้อเหล็ก "ฉีกหลุดออกมาเป็นก้อน" ตามแนวรูเจาะ 
    
    มักเกิดขึ้นเมื่อ:
    * ปีกคานสั้น (Edge distance น้อย)
    * ใช้น็อตจำนวนมากเรียงกันเป็นแถว
    * ความหนาเอวคาน (Web) น้อย
    
    สูตรตรวจสอบ (AISC J4-5):
    $$R_{bs} = 0.6 F_u A_{nv} + U_{bs} F_u A_{nt}$$
    *(ค่าต่ำสุดระหว่าง แรงเฉือนขาด + แรงดึงขาด)*
    """)
with c2:
    st.info("""
    **สังเกตที่กราฟ:**
    คุณจะเห็น **เส้นสีม่วง (Block Shear)** เป็นขั้นบันได
    * เมื่อคานสั้นลง -> แรงเยอะขึ้น -> ใช้น็อตเยอะขึ้น -> พื้นที่หน้าตัดหายน้อยลง -> **Block Shear ต่ำลง!**
    * นี่คือเหตุผลว่าทำไมบางครั้ง **"ใส่ Bolt เพิ่ม กลับทำให้รับแรงได้น้อยลง"** (เพราะเนื้อเหล็กพรุนจนฉีกง่ายขึ้น)
    """)

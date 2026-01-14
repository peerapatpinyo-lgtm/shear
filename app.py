import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & CUSTOM STYLES
# ==========================================
st.set_page_config(page_title="ProStructure: Capacity Based Design", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .big-metric { font-size: 32px; font-weight: bold; color: #154360; }
    .sub-metric { font-size: 16px; color: #7f8c8d; }
    .card { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; border-left: 5px solid #2980b9; }
    .card-conn { background-color: #fdfefe; padding: 20px; border-radius: 10px; border: 1px solid #d5d8dc; border-left: 5px solid #e67e22; }
    .rec-box { background-color: #d4efdf; padding: 10px; border-radius: 5px; color: #1e8449; font-weight: bold; text-align: center; }
    h3 { color: #2c3e50; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA & CALCULATIONS
# ==========================================
def get_sys_data():
    # Simulated SYS Table
    data = [
        ("H 100x50x5x7", 100, 50, 5, 7, 378, 76.5),
        ("H 150x75x5x7", 150, 75, 5, 7, 666, 88.8),
        ("H 200x100x5.5x8", 200, 100, 5.5, 8, 1840, 184),
        ("H 250x125x6x9", 250, 125, 6, 9, 3690, 295),
        ("H 300x150x6.5x9", 300, 150, 6.5, 9, 7210, 481),
        ("H 350x175x7x11", 350, 175, 7, 11, 13600, 775),
        ("H 400x200x8x13", 400, 200, 8, 13, 23700, 1190),
        ("H 450x200x9x14", 450, 200, 9, 14, 33500, 1490),
        ("H 500x200x10x16", 500, 200, 10, 16, 47800, 1910),
        ("H 600x200x11x17", 600, 200, 11, 17, 77600, 2590),
        ("H 700x300x13x24", 700, 300, 13, 24, 201000, 5760),
        ("H 800x300x14x26", 800, 300, 14, 26, 292000, 7290),
        ("H 900x300x16x28", 900, 300, 16, 28, 411000, 9140)
    ]
    return pd.DataFrame(data, columns=["Section", "h", "b", "tw", "tf", "Ix", "Zx"])

# Sidebar Inputs
with st.sidebar:
    st.header("⚙️ Settings")
    df = get_sys_data()
    sec_name = st.selectbox("Select Section", df['Section'], index=6) # H400
    
    st.subheader("Material (ksc)")
    Fy = st.number_input("Yield (Fy)", value=2400)
    Fu = st.number_input("Ultimate (Fu)", value=4000)
    E = 2.04e6

    # Props
    p = df[df['Section'] == sec_name].iloc[0]
    h, tw, tf, Ix, Zx = p['h'], p['tw'], p['tf'], p['Ix'], p['Zx']
    
    st.info(f"**Props:** A={p['h']*p['tw']/100:.1f}cm², Ix={Ix:,}, Zx={Zx:,}")

# ==========================================
# 3. BEAM REVERSE ANALYSIS
# ==========================================
st.title("🏗️ Structural Capacity Dashboard")

# 1. Main Slider for Span
st.markdown("### 1️⃣ Span Configuration")
span = st.slider("Select Span Length (m)", 1.0, 20.0, 6.0, 0.5)

# 2. Calculation Core (Reverse Engineering)
L_cm = span * 100
d_m = h / 1000

# Limits Calculation
# A. Shear Yield (Constant)
Aw = (h/10) * (tw/10)
V_max_shear = 0.6 * Fy * Aw
w_max_shear = (2 * V_max_shear) / L_cm * 100 # Convert back to kg/m

# B. Bending (Allowable Moment)
M_allow = 0.6 * Fy * Zx
w_max_moment = (8 * M_allow) / (L_cm**2) * 100
V_max_moment = (w_max_moment * span) / 2

# C. Deflection (L/240)
# Delta = 5wL^4/384EI = L/240 -> w = (384EI)/(2400*L^3) * 5? No.
# w = (384 E I Delta) / (5 L^4) -> w = (384 E I (L/240)) / (5 L^4) = (384 E I) / (1200 L^3)
w_max_defl = (384 * E * Ix) / (1200 * (L_cm**3)) * 100 # kg/m
V_max_defl = (w_max_defl * span) / 2

# Find Governor
limits = {
    "Shear Limit": (w_max_shear, V_max_shear),
    "Moment Limit": (w_max_moment, V_max_moment),
    "Deflection (L/240)": (w_max_defl, V_max_defl)
}

# The SAFE Load is the minimum of all limits
safe_w = min(w_max_shear, w_max_moment, w_max_defl)
safe_v = min(V_max_shear, V_max_moment, V_max_defl)

# Identify Governor
if safe_w == w_max_shear: gov = "Shear Capacity"
elif safe_w == w_max_moment: gov = "Bending Moment"
else: gov = "Deflection (L/240)"

# ==========================================
# 4. DISPLAY DASHBOARD
# ==========================================
col_dash1, col_dash2 = st.columns([1, 2])

with col_dash1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"### 🛡️ Max Capacity at {span}m")
    
    st.markdown('<div class="sub-metric">Max Uniform Load (w)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="big-metric">{safe_w:,.0f} kg/m</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown('<div class="sub-metric">Max Reaction (V_design)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="big-metric" style="color:#d35400">{safe_v:,.0f} kg</div>', unsafe_allow_html=True)
    
    st.markdown(f"**Controlled by:** `{gov}`")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Recommendation Box
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 💡 Efficiency Guide")
    st.write("ช่วง Load ที่ใช้งานแล้วคุ้มค่า (50-70%):")
    st.markdown(f"""
    <div class="rec-box">
    {safe_w*0.5:,.0f} - {safe_w*0.7:,.0f} kg/m
    </div>
    """, unsafe_allow_html=True)
    st.caption("หาก Load จริงน้อยกว่านี้ แสดงว่าหน้าตัดใหญ่เกินความจำเป็น (Over Design)")
    st.markdown('</div>', unsafe_allow_html=True)

with col_dash2:
    # --- GRAPH LOGIC ---
    L_range = np.linspace(1, 20, 100)
    L_range_cm = L_range * 100
    
    # Calculate curves for all spans
    # 1. Shear (Constant V -> w varies)
    curve_v_shear = np.full_like(L_range, V_max_shear)
    
    # 2. Moment (V = 4M/L)
    curve_v_moment = (4 * M_allow) / L_range_cm
    
    # 3. Deflection (V = 384EI / 2400 L^2)
    curve_v_defl = (384 * E * Ix) / (2400 * (L_range_cm**2))
    
    curve_safe = np.minimum(np.minimum(curve_v_shear, curve_v_moment), curve_v_defl)
    
    fig = go.Figure()
    
    # Plot Envelope
    fig.add_trace(go.Scatter(x=L_range, y=curve_safe, fill='tozeroy', 
                             name='Safe Operation Zone', line=dict(color='#2980b9', width=3)))
    
    # Plot Limits (Dashed)
    fig.add_trace(go.Scatter(x=L_range, y=curve_v_shear, name='Shear Limit', line=dict(dash='dot', color='green')))
    fig.add_trace(go.Scatter(x=L_range, y=curve_v_moment, name='Moment Limit', line=dict(dash='dot', color='orange')))
    fig.add_trace(go.Scatter(x=L_range, y=curve_v_defl, name='Defl. Limit', line=dict(dash='dot', color='red')))
    
    # Highlight Current Point
    fig.add_trace(go.Scatter(x=[span], y=[safe_v], mode='markers+text', 
                             marker=dict(size=15, color='#c0392b'),
                             text=[f"V={safe_v/1000:.1f}t"], textposition="top right",
                             name='Current Design'))
    
    # Highlight Optimal Ratio (15d - 20d)
    opt_min, opt_max = 15*d_m, 20*d_m
    fig.add_vrect(x0=opt_min, x1=opt_max, fillcolor="green", opacity=0.1, annotation_text="Optimal Span")

    fig.update_layout(title="Reaction Capacity Envelope ($V_{max}$)", 
                      xaxis_title="Span Length (m)", yaxis_title="Max Reaction Force (kg)",
                      height=450, hovermode="x unified", xaxis=dict(rangeslider=dict(visible=True)))
    
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 5. CONNECTION DESIGN (AUTO LINKED)
# ==========================================
st.markdown("---")
st.markdown("### 2️⃣ Connection Design (Auto-Linked)")
st.markdown("ระบบดึงค่า **Max Reaction** จากด้านบนมาออกแบบจุดต่อให้อัตโนมัติ")

col_conn_setup, col_conn_res = st.columns([1, 2])

with col_conn_setup:
    st.markdown('<div class="card-conn">', unsafe_allow_html=True)
    st.markdown("#### 🔧 Bolt & Weld Config")
    
    # Input
    bolt_grade = st.selectbox("Bolt Grade", ["A325", "A307"])
    dia = st.selectbox("Diameter (mm)", [12, 16, 20, 22, 24], index=2)
    rows = st.number_input("No. of Rows", 2, 8, 3)
    t_plate = st.selectbox("Plate T (mm)", [6, 9, 12, 16], index=1)
    w_size = st.selectbox("Weld Size (mm)", [4, 6, 8, 10], index=1)
    
    st.markdown("---")
    st.caption(f"Design Load ($V_u$): {safe_v:,.0f} kg")
    st.markdown('</div>', unsafe_allow_html=True)

with col_conn_res:
    # --- CALCULATION ENGINE ---
    # Params
    db = dia/10
    Ab = math.pi * (db/2)**2
    Fv = 3720 if bolt_grade == "A325" else 1900
    
    # 1. Bolt Shear
    Rn_bolt = rows * Ab * Fv
    
    # 2. Bearing (Min of Web or Plate)
    Rn_bear_web = rows * (1.2 * Fu * db * (tw/10))
    Rn_bear_plt = rows * (1.2 * Fu * db * (t_plate/10))
    Rn_bear = min(Rn_bear_web, Rn_bear_plt)
    
    # 3. Block Shear (Auto Geometry)
    s = 3 * dia; lev = 1.5 * dia; leh = 40
    Agv = ((lev + (rows-1)*s)/10) * (t_plate/10)
    Anv = Agv - (rows-0.5)*((dia+2)/10)*(t_plate/10)
    Ant = ((leh - 0.5*(dia+2))/10) * (t_plate/10)
    
    R_bs1 = 0.6*Fy*Agv + 1.0*Fu*Ant
    R_bs2 = 0.6*Fu*Anv + 1.0*Fu*Ant
    Rn_block = min(R_bs1, R_bs2)
    
    # 4. Weld (Simplified)
    # L_weld = Plate Height -> 2 sides
    L_weld = (lev + (rows-1)*s + lev)/10
    Rn_weld = 2 * L_weld * 0.707 * (w_size/10) * (0.3 * 4900) # 0.3Fu approx for ASD
    
    # Check
    capacities = {
        "Bolt Shear": Rn_bolt,
        "Bearing Strength": Rn_bear,
        "Block Shear": Rn_block,
        "Weld Strength": Rn_weld
    }
    
    min_cap = min(capacities.values())
    ratio = safe_v / min_cap
    is_pass = safe_v <= min_cap

    # --- RENDER RESULTS ---
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Capacity Checks")
        for k, v in capacities.items():
            # Progress bar logic
            u_ratio = safe_v / v
            bar_color = "red" if u_ratio > 1.0 else ("green" if u_ratio < 0.8 else "orange")
            
            st.write(f"**{k}** : {v:,.0f} kg")
            st.progress(min(u_ratio, 1.0))
            if u_ratio > 1.0:
                st.caption(f"❌ Failed (Over by {(u_ratio-1)*100:.1f}%)")
    
    with c2:
        st.subheader("Summary")
        if is_pass:
            st.markdown(f"""
            <div style="background-color:#d4efdf; padding:20px; border-radius:10px; text-align:center; border:2px solid #27ae60;">
                <h1 style="color:#27ae60; margin:0;">PASS</h1>
                <h3>✅ Safe</h3>
                <p>Ratio: {ratio:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            fail_item = min(capacities, key=capacities.get)
            st.markdown(f"""
            <div style="background-color:#fadbd8; padding:20px; border-radius:10px; text-align:center; border:2px solid #c0392b;">
                <h1 style="color:#c0392b; margin:0;">FAIL</h1>
                <h3>❌ Unsafe</h3>
                <p>Increase {fail_item}!</p>
            </div>
            """, unsafe_allow_html=True)
            
    # Theory / Diagram Context
    with st.expander("📚 View Failure Modes & Diagrams"):
        col_img1, col_img2 = st.columns(2)
        with col_img1:
             st.markdown("**Block Shear Failure Path:**")
             st.markdown("การวิบัติแบบฉีกขาดผ่านรูเจาะ (Tension Rupture + Shear Yield)")
             st.markdown("") # Placeholder per instructions
        with col_img2:
             st.markdown("**Bolt Shear Failure:**")
             st.markdown("การวิบัติของสลักเกลียวจากการถูกตัดขาด (Single Shear)")
             st.markdown("") # Placeholder per instructions

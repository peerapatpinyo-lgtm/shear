import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================
# 1. DATABASE: H-BEAM (Wide Flange)
# ==========================================
# Units: h, b, tw, tf (mm) | Ix (cm4) | Zx (cm3) | w (kg/m)
steel_db = {
    # --- Series 100 ---
    "H 100x50x5x7":     {"h": 100, "b": 50,  "tw": 5,   "tf": 7,   "Ix": 187,    "Zx": 37.5,  "w": 9.3},
    "H 100x100x6x8":    {"h": 100, "b": 100, "tw": 6,   "tf": 8,   "Ix": 383,    "Zx": 76.5,  "w": 17.2},
    "H 125x60x6x8":     {"h": 125, "b": 60,  "tw": 6,   "tf": 8,   "Ix": 413,    "Zx": 65.9,  "w": 13.1},
    "H 125x125x6.5x9": {"h": 125, "b": 125, "tw": 6.5, "tf": 9,   "Ix": 847,    "Zx": 136,   "w": 23.8},
    "H 148x100x6x9":    {"h": 148, "b": 100, "tw": 6,   "tf": 9,   "Ix": 1020,   "Zx": 138,   "w": 21.1},
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8,  "w": 14.0},
    "H 150x150x7x10":   {"h": 150, "b": 150, "tw": 7,   "tf": 10,  "Ix": 1640,   "Zx": 219,   "w": 31.5},
    "H 175x90x5x8":     {"h": 175, "b": 90,  "tw": 5,   "tf": 8,   "Ix": 1210,   "Zx": 138,   "w": 18.1},
    "H 175x175x7.5x11":{"h": 175, "b": 175, "tw": 7.5, "tf": 11,  "Ix": 2900,   "Zx": 331,   "w": 40.2},
    "H 194x150x6x9":    {"h": 194, "b": 150, "tw": 6,   "tf": 9,   "Ix": 2690,   "Zx": 277,   "w": 29.9},
    # --- Series 200 ---
    "H 200x100x5.5x8": {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "w": 21.3},
    "H 200x200x8x12":  {"h": 200, "b": 200, "tw": 8,   "tf": 12,  "Ix": 4720,   "Zx": 472,   "w": 49.9},
    "H 244x175x7x11":  {"h": 244, "b": 175, "tw": 7,   "tf": 11,  "Ix": 5610,   "Zx": 460,   "w": 44.1},
    "H 248x124x5x8":    {"h": 248, "b": 124, "tw": 5,   "tf": 8,   "Ix": 3540,   "Zx": 285,   "w": 25.7},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "w": 29.6},
    "H 250x250x9x14":  {"h": 250, "b": 250, "tw": 9,   "tf": 14,  "Ix": 10800,  "Zx": 867,   "w": 72.4},
    "H 294x200x8x12":  {"h": 294, "b": 200, "tw": 8,   "tf": 12,  "Ix": 11300,  "Zx": 771,   "w": 56.8},
    # --- Series 300 ---
    "H 300x150x6.5x9": {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 300x300x10x15": {"h": 300, "b": 300, "tw": 10,  "tf": 15,  "Ix": 20400,  "Zx": 1360,  "w": 94.0},
    "H 340x250x9x14":  {"h": 340, "b": 250, "tw": 9,   "tf": 14,  "Ix": 21200,  "Zx": 1250,  "w": 79.7},
    "H 346x174x6x9":    {"h": 346, "b": 174, "tw": 6,   "tf": 9,   "Ix": 11100,  "Zx": 641,   "w": 41.4},
    "H 350x175x7x11":  {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "w": 49.6},
    "H 350x350x12x19": {"h": 350, "b": 350, "tw": 12,  "tf": 19,  "Ix": 40300,  "Zx": 2300,  "w": 137},
    # --- Series 400+ ---
    "H 400x200x8x13":  {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 400x400x13x21": {"h": 400, "b": 400, "tw": 13,  "tf": 21,  "Ix": 66600,  "Zx": 3330,  "w": 172},
    "H 450x200x9x14":  {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "w": 76.0},
    "H 500x200x10x16": {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
    "H 588x300x12x20": {"h": 588, "b": 300, "tw": 12,  "tf": 20,  "Ix": 118000, "Zx": 4020,  "w": 151},
    "H 600x200x11x17": {"h": 600, "b": 200, "tw": 11,  "tf": 17,  "Ix": 77600,  "Zx": 2590,  "w": 106},
    "H 700x300x13x24": {"h": 700, "b": 300, "tw": 13,  "tf": 24,  "Ix": 201000, "Zx": 5760,  "w": 185},
    "H 800x300x14x26": {"h": 800, "b": 300, "tw": 14,  "tf": 26,  "Ix": 292000, "Zx": 7300,  "w": 210},
    "H 900x300x16x28": {"h": 900, "b": 300, "tw": 16,  "tf": 28,  "Ix": 404000, "Zx": 9000,  "w": 243},
}

# ==========================================
# 2. CONFIGURATION
# ==========================================
st.set_page_config(page_title="Ultimate H-Beam Analyzer", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-left: 5px solid #ff4b4b;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .status-ok { color: green; font-weight: bold; }
    .status-warning { color: orange; font-weight: bold; }
    .status-danger { color: red; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🏗️ Ultimate H-Beam Analyzer")
st.caption("Integrated Design: Shear Check • LTB Analysis • Deflection Control • Cost Estimation")

# ==========================================
# 3. SIDEBAR INPUTS
# ==========================================
with st.sidebar:
    st.header("1. Beam Configuration")
    section_name = st.selectbox("Select Section", list(steel_db.keys()))
    props = steel_db[section_name]
    
    st.info(f"📏 **{section_name}**\n\nWeight: {props['w']} kg/m\nIx: {props['Ix']:,} cm⁴ | Zx: {props['Zx']:,} cm³")
    
    load_type = st.radio("Load Type", ["Point Load (P)", "Uniform Load (w)"])
    
    st.divider()
    st.header("2. Geometry & Bracing")
    current_L = st.number_input("Span Length (L) [m]", value=6.0, step=0.5, min_value=1.0)
    unbraced_L = st.number_input("Unbraced Length (Lb) [m]", value=0.0, step=0.5, 
                                 help="0 = Fully Braced (ค้ำยันตลอดแนว)")

    st.divider()
    st.header("3. Material & Design")
    c1, c2 = st.columns(2)
    fy = c1.number_input("Fy (ksc)", value=2400, step=100)
    E_val = c2.number_input("E (ksc)", value=2040000)
    
    Fb_ratio = st.slider("Fb Ratio", 0.4, 0.7, 0.60)
    defl_limit = st.selectbox("Deflection Limit", [200, 240, 300, 360, 400], index=2)
    unit_price = st.number_input("Steel Price (THB/kg)", value=32.0)

# ==========================================
# 4. CALCULATION CORE
# ==========================================
def analyze_beam(L_m, props, Fy, E, Fb_r, Fv_r=0.4, def_lim=300, load_mode="Point", Lb_m=0):
    # 1. Setup Units
    L_cm = L_m * 100
    h_cm, tw_cm = props['h']/10, props['tw']/10
    Ix, Zx, w_kgm = props['Ix'], props['Zx'], props['w']
    
    # 2. Allowable Stresses (Capacity)
    # Shear
    Aw = h_cm * tw_cm
    V_max_cap = (Fv_r * Fy) * Aw # kg
    
    # Moment & LTB Check
    real_Lb = min(Lb_m, L_m) if Lb_m > 0 else 0
    Lb_limit = 15 * (props['b'] / 1000) # Simple Compact Limit
    
    if real_Lb <= Lb_limit:
        Fb_use = Fb_r * Fy
        ltb_msg = "Compact (Full Strength)"
        ltb_reduc = 1.0
    else:
        # Parabolic Reduction
        reduc = (Lb_limit / real_Lb) ** 2
        Fb_use = max((Fb_r * Fy) * reduc, 0.2*Fy)
        ltb_msg = f"Slender (Reduced by {(1-reduc)*100:.1f}%)"
        ltb_reduc = reduc
        
    M_max_cap = Fb_use * Zx # kg.cm
    
    # Deflection
    Delta_allow = L_cm / def_lim # cm
    
    # 3. Self Weight Effects (Always UDL)
    V_sw = (w_kgm * L_m) / 2
    M_sw = (w_kgm * L_m**2 / 8) * 100
    w_cm = w_kgm / 100
    D_sw = (5 * w_cm * L_cm**4) / (384 * E * Ix)
    
    # 4. Solve for Net Safe Load (Back-calculate from Limits)
    if "Point" in load_mode:
        # P/2 + Vsw = Vcap
        P_shear = 2 * (V_max_cap - V_sw)
        # PL/4 + Msw = Mcap
        P_moment = 4 * (M_max_cap - M_sw) / L_cm
        # PL^3/48EI + Dsw = Dallow
        P_defl = (48 * E * Ix * (Delta_allow - D_sw)) / (L_cm**3)
    else: # Uniform Total Load W
        # W/2 = Vcap (sw included in W check later)
        W_shear = 2 * V_max_cap - (w_kgm * L_m)
        W_moment = (8 * M_max_cap / L_cm) - (w_kgm * L_m)
        W_defl = (384 * E * Ix * (Delta_allow - D_sw)) / (5 * L_cm**3)
        
        P_shear, P_moment, P_defl = W_shear, W_moment, W_defl

    # 5. Determine Governor
    safe_load = max(0, min(P_shear, P_moment, P_defl))
    
    if safe_load == P_shear: gov = "Shear (แรงเฉือน)"
    elif safe_load == P_moment: gov = "Moment (โมเมนต์ดัด)"
    else: gov = "Deflection (ระยะแอ่น)"
    
    return {
        "Safe_Load_Ton": safe_load / 1000,
        "Gov": gov,
        "Caps": {"Shear": P_shear/1000, "Moment": P_moment/1000, "Deflect": P_defl/1000},
        "LTB": {"Msg": ltb_msg, "Fb": Fb_use, "Limit": Lb_limit},
        "Self_Weight": (w_kgm * L_m),
        "Cost": (w_kgm * L_m) * unit_price
    }

# ==========================================
# 5. MAIN DASHBOARD
# ==========================================
res = analyze_beam(current_L, props, fy, E_val, Fb_ratio, 0.4, defl_limit, load_type, unbraced_L)

# --- Top Row: Big Numbers ---
c1, c2, c3 = st.columns([1.5, 1, 1])

with c1:
    st.markdown(f"""
    <div class='metric-card'>
        <h3 style='margin:0; color:#555;'>Net Safe Load (น้ำหนักปลอดภัย)</h3>
        <h1 style='margin:0; font-size:48px;'>{res['Safe_Load_Ton']:.2f} <span style='font-size:20px'>Ton</span></h1>
        <p style='margin:0; color:gray;'>Controlled by: <b>{res['Gov']}</b></p>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.metric("Total Beam Weight", f"{res['Self_Weight']:.1f} kg")
    st.metric("Est. Cost", f"{res['Cost']:,.0f} THB")

with c3:
    if "Compact" in res['LTB']['Msg']:
        st.success(f"✅ LTB Check Passed\n\nBracing OK")
    else:
        st.error(f"⚠️ LTB Warning\n\n{res['LTB']['Msg']}")
    
    st.info(f"Fb Used: {res['LTB']['Fb']:.0f} ksc")

# --- Middle Row: Utilization Bars (The "Why") ---
st.subheader("📊 Engineering Check (Utilization at Max Load)")
st.caption("กราฟแสดงอัตราส่วนความสามารถรับแรง (เมื่อรับน้ำหนักเต็มพิกัด ตัวควบคุมจะแตะ 100%)")

caps = res['Caps']
safe = res['Safe_Load_Ton']

# Calculate % utilized relative to the specific limit
# Example: If Safe Load is determined by Deflection, then Deflection Util = 100%
# But Shear Util = Safe / Shear_Cap * 100
u_shear = (safe / caps['Shear']) * 100 if caps['Shear'] > 0 else 0
u_moment = (safe / caps['Moment']) * 100 if caps['Moment'] > 0 else 0
u_defl = (safe / caps['Deflect']) * 100 if caps['Deflect'] > 0 else 0

col_u1, col_u2, col_u3 = st.columns(3)

with col_u1:
    st.write(f"**Shear Limit:** {caps['Shear']:.2f} T")
    st.progress(min(u_shear/100, 1.0))
    st.caption(f"Used: {u_shear:.1f}%")

with col_u2:
    st.write(f"**Moment Limit:** {caps['Moment']:.2f} T")
    st.progress(min(u_moment/100, 1.0))
    st.caption(f"Used: {u_moment:.1f}%")

with col_u3:
    st.write(f"**Deflection Limit:** {caps['Deflect']:.2f} T")
    st.progress(min(u_defl/100, 1.0))
    st.caption(f"Used: {u_defl:.1f}%")

st.divider()

# --- Bottom Row: Recommendation & Graph ---
r1, r2 = st.columns([1, 2])

with r1:
    st.subheader("💡 Recommendation")
    if "Deflection" in res['Gov']:
        st.warning("""
        **ปัญหา:** ถูกคุมด้วยระยะแอ่น (Deflection)
        \n**วิธีแก้:** 1. เพิ่มความลึกหน้าตัด (h) เพื่อเพิ่ม Ix
        2. การเพิ่มเกรดเหล็ก (Fy) **ไม่ช่วย**
        """)
    elif "Moment" in res['Gov']:
        if "Compact" in res['LTB']['Msg']:
            st.info("""
            **สถานะ:** ถูกคุมด้วยโมเมนต์ (ปกติ)
            \n**วิธีแก้:** หากต้องการรับแรงเพิ่ม ให้เลือกหน้าตัดที่มี Zx สูงขึ้น
            """)
        else:
            st.error("""
            **ปัญหา:** โมเมนต์ลดทอนเพราะ LTB
            \n**วิธีแก้:**
            1. เพิ่มจุดค้ำยันด้านข้าง (ลด Lb)
            2. เปลี่ยนหน้าตัดที่ปีกกว้างขึ้น (b)
            """)
    else:
        st.success("""
        **สถานะ:** ถูกคุมด้วยแรงเฉือน (Shear)
        \nแสดงว่าคานสั้นและรับแรงได้มหาศาล (Rare Case)
        """)

with r2:
    st.subheader("📈 Capacity vs Span Trend")
    # Generate Trend Data
    spans = np.linspace(2, 12, 20)
    trend_data = []
    for s in spans:
        r = analyze_beam(s, props, fy, E_val, Fb_ratio, 0.4, defl_limit, load_type, unbraced_L)
        trend_data.append(r['Safe_Load_Ton'])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans, y=trend_data, mode='lines', name='Safe Load', line=dict(color='black', width=3)))
    fig.add_trace(go.Scatter(x=[current_L], y=[res['Safe_Load_Ton']], mode='markers', name='Current Design', marker=dict(size=12, color='red')))
    fig.update_layout(xaxis_title="Span (m)", yaxis_title="Safe Load (Ton)", height=350, margin=dict(t=10,b=10))
    st.plotly_chart(fig, use_container_width=True)

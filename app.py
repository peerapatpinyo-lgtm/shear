import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================
# 1. DATABASE & CONFIG
# ==========================================
steel_db = {
    # --- Series 100 ---
    "H 100x50x5x7":     {"h": 100, "b": 50,  "tw": 5,   "tf": 7,   "Ix": 187,    "Zx": 37.5,  "w": 9.3},
    "H 100x100x6x8":    {"h": 100, "b": 100, "tw": 6,   "tf": 8,   "Ix": 383,    "Zx": 76.5,  "w": 17.2},
    "H 125x60x6x8":     {"h": 125, "b": 60,  "tw": 6,   "tf": 8,   "Ix": 413,    "Zx": 65.9,  "w": 13.1},
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8,  "w": 14.0},
    "H 150x150x7x10":   {"h": 150, "b": 150, "tw": 7,   "tf": 10,  "Ix": 1640,   "Zx": 219,   "w": 31.5},
    "H 175x90x5x8":     {"h": 175, "b": 90,  "tw": 5,   "tf": 8,   "Ix": 1210,   "Zx": 138,   "w": 18.1},
    # --- Series 200 ---
    "H 200x100x5.5x8": {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "w": 21.3},
    "H 200x200x8x12":  {"h": 200, "b": 200, "tw": 8,   "tf": 12,  "Ix": 4720,   "Zx": 472,   "w": 49.9},
    "H 244x175x7x11":  {"h": 244, "b": 175, "tw": 7,   "tf": 11,  "Ix": 5610,   "Zx": 460,   "w": 44.1},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "w": 29.6},
    "H 294x200x8x12":  {"h": 294, "b": 200, "tw": 8,   "tf": 12,  "Ix": 11300,  "Zx": 771,   "w": 56.8},
    # --- Series 300 ---
    "H 300x150x6.5x9": {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 300x300x10x15": {"h": 300, "b": 300, "tw": 10,  "tf": 15,  "Ix": 20400,  "Zx": 1360,  "w": 94.0},
    "H 350x175x7x11":  {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "w": 49.6},
    "H 350x350x12x19": {"h": 350, "b": 350, "tw": 12,  "tf": 19,  "Ix": 40300,  "Zx": 2300,  "w": 137},
    # --- Series 400+ ---
    "H 400x200x8x13":  {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 450x200x9x14":  {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "w": 76.0},
    "H 500x200x10x16": {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
    "H 588x300x12x20": {"h": 588, "b": 300, "tw": 12,  "tf": 20,  "Ix": 118000, "Zx": 4020,  "w": 151},
    "H 600x200x11x17": {"h": 600, "b": 200, "tw": 11,  "tf": 17,  "Ix": 77600,  "Zx": 2590,  "w": 106},
    "H 700x300x13x24": {"h": 700, "b": 300, "tw": 13,  "tf": 24,  "Ix": 201000, "Zx": 5760,  "w": 185},
    "H 800x300x14x26": {"h": 800, "b": 300, "tw": 14,  "tf": 26,  "Ix": 292000, "Zx": 7300,  "w": 210},
    "H 900x300x16x28": {"h": 900, "b": 300, "tw": 16,  "tf": 28,  "Ix": 404000, "Zx": 9000,  "w": 243},
}

st.set_page_config(page_title="H-Beam Analyzer", layout="wide", page_icon="🏗️")
st.markdown("""<style>.metric-card {background-color: #f0f2f6; border-left: 5px solid #ff4b4b; padding: 15px; border-radius: 5px; margin-bottom: 10px;}</style>""", unsafe_allow_html=True)

# ==========================================
# 2. INPUT SIDEBAR
# ==========================================
with st.sidebar:
    st.header("1. Beam Configuration")
    section_name = st.selectbox("Select Section", list(steel_db.keys()))
    props = steel_db[section_name]
    st.info(f"📏 **{section_name}**\n\nWeight: {props['w']} kg/m\nIx: {props['Ix']:,} | Zx: {props['Zx']:,}")
    
    load_type = st.radio("Load Type", ["Point Load (P)", "Uniform Load (w)"])
    
    st.divider()
    st.header("2. Geometry & Bracing")
    current_L = st.number_input("Span Length (L) [m]", value=6.0, step=0.5, min_value=1.0)
    unbraced_L = st.number_input("Unbraced Length (Lb) [m]", value=0.0, step=0.5, help="0 = Fully Braced")

    st.divider()
    st.header("3. Material & Design")
    fy = st.number_input("Fy (ksc)", value=2400)
    E_val = st.number_input("E (ksc)", value=2040000)
    Fb_ratio = st.slider("Fb Ratio", 0.4, 0.7, 0.60)
    defl_limit = st.selectbox("Deflection Limit", [200, 240, 300, 360, 400], index=2)
    unit_price = st.number_input("Price (THB/kg)", value=32.0)

# ==========================================
# 3. CALCULATION ENGINE
# ==========================================
def analyze_beam(L_m, props, Fy, E, Fb_r, Fv_r=0.4, def_lim=300, load_mode="Point", Lb_m=0):
    L_cm = L_m * 100
    h_cm, tw_cm = props['h']/10, props['tw']/10
    Ix, Zx, w_kgm = props['Ix'], props['Zx'], props['w']
    
    # --- Capacities ---
    Aw = h_cm * tw_cm
    V_max_cap = (Fv_r * Fy) * Aw 
    
    real_Lb = min(Lb_m, L_m) if Lb_m > 0 else 0
    Lb_limit = 15 * (props['b'] / 1000)
    
    if real_Lb <= Lb_limit:
        Fb_use = Fb_r * Fy
        ltb_msg = "Compact (OK)"
    else:
        reduc = (Lb_limit / real_Lb) ** 2
        Fb_use = max((Fb_r * Fy) * reduc, 0.2*Fy)
        ltb_msg = f"Slender (Reduc. {(1-reduc)*100:.0f}%)"
        
    M_max_cap = Fb_use * Zx 
    Delta_allow = L_cm / def_lim 
    
    # --- Self Weight ---
    V_sw = (w_kgm * L_m) / 2
    M_sw = (w_kgm * L_m**2 / 8) * 100
    w_cm = w_kgm / 100
    D_sw = (5 * w_cm * L_cm**4) / (384 * E * Ix)
    
    # --- Solve Net Load ---
    if "Point" in load_mode:
        P_shear = 2 * (V_max_cap - V_sw)
        P_moment = 4 * (M_max_cap - M_sw) / L_cm
        P_defl = (48 * E * Ix * (Delta_allow - D_sw)) / (L_cm**3)
    else: 
        P_shear = (2 * V_max_cap) - (w_kgm * L_m)
        P_moment = ((8 * M_max_cap) / L_cm) - (w_kgm * L_m)
        P_defl = ((384 * E * Ix * (Delta_allow - D_sw)) * 5) / (5 * L_cm**3) # Simplified algebra

    safe_load = max(0, min(P_shear, P_moment, P_defl))
    
    if safe_load == P_shear: gov = "Shear"
    elif safe_load == P_moment: gov = "Moment"
    else: gov = "Deflection"
    
    return {
        "Safe_Load": safe_load / 1000,
        "Gov": gov,
        "Caps": {"Shear": P_shear/1000, "Moment": P_moment/1000, "Deflect": P_defl/1000},
        "LTB_Msg": ltb_msg,
        "Self_Weight": (w_kgm * L_m),
        "Cost": (w_kgm * L_m) * unit_price
    }

# ==========================================
# 4. MAIN DISPLAY (TABS)
# ==========================================
res = analyze_beam(current_L, props, fy, E_val, Fb_ratio, 0.4, defl_limit, load_type, unbraced_L)

st.title("🏗️ Ultimate H-Beam Analyzer")

# --- Tabs Setup ---
tab1, tab2 = st.tabs(["📊 Dashboard & Recommendation", "📈 Compare 3 Cases (Graphs)"])

# --- TAB 1: SUMMARY ---
with tab1:
    # Big Metrics
    c1, c2, c3 = st.columns([1.5, 1, 1])
    with c1:
        st.markdown(f"""
        <div class='metric-card'>
            <h3 style='margin:0; color:#555;'>Net Safe Load</h3>
            <h1 style='margin:0; font-size:48px; color:#ff4b4b'>{res['Safe_Load']:.2f} <span style='font-size:20px'>Ton</span></h1>
            <p style='margin:0; color:gray;'>Limit by: <b>{res['Gov']}</b></p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.metric("Total Weight", f"{res['Self_Weight']:.1f} kg")
        st.metric("Est. Cost", f"{res['Cost']:,.0f} THB")
    with c3:
        if "Compact" in res['LTB_Msg']:
            st.success(f"✅ LTB Check\n\n{res['LTB_Msg']}")
        else:
            st.error(f"⚠️ LTB Check\n\n{res['LTB_Msg']}")

    # Utilization Bars
    st.subheader("Utilization Check")
    caps = res['Caps']
    safe = res['Safe_Load']
    
    u_sh = (safe/caps['Shear'])*100 if caps['Shear']>0 else 0
    u_mo = (safe/caps['Moment'])*100 if caps['Moment']>0 else 0
    u_de = (safe/caps['Deflect'])*100 if caps['Deflect']>0 else 0
    
    uc1, uc2, uc3 = st.columns(3)
    uc1.progress(min(u_sh/100, 1.0), text=f"Shear Limit: {caps['Shear']:.2f} T ({u_sh:.0f}%)")
    uc2.progress(min(u_mo/100, 1.0), text=f"Moment Limit: {caps['Moment']:.2f} T ({u_mo:.0f}%)")
    uc3.progress(min(u_de/100, 1.0), text=f"Deflection Limit: {caps['Deflect']:.2f} T ({u_de:.0f}%)")
    
    st.divider()
    
    # Recommendation
    st.subheader("💡 Engineer's Recommendation")
    if "Deflection" in res['Gov']:
        st.warning(f"**ปัญหา:** คานแอ่นตัวมากเกินไป (Deflection Controlled) ที่ระยะ {current_L}m\n\n**วิธีแก้:** 1. เพิ่มความลึกหน้าตัด (h) เท่านั้น \n2. การเพิ่มเกรดเหล็ก (Fy) ไม่ช่วย")
    elif "Moment" in res['Gov']:
        st.info(f"**สถานะ:** คานรับแรงดัดเต็มพิกัด (Moment Controlled)\n\n**วิธีแก้:** เพิ่มหน้าตัดที่มี Zx สูงขึ้น หรือลดระยะค้ำยัน (Lb)")
    else:
        st.success("**สถานะ:** คานรับแรงเฉือนเต็มพิกัด (Shear Controlled) \n\n**Note:** แสดงว่าคานสั้นมากและรับแรงกดมหาศาล")

# --- TAB 2: COMPARE 3 CASES ---
with tab2:
    st.subheader(f"📉 Comparative Analysis: {section_name}")
    st.markdown("กราฟนี้ช่วยให้คุณเห็น **'จุดตัด' (Crossover Points)** ว่าที่ความยาวเท่าไหร่ ระบบจะเปลี่ยนจากการพังแบบหนึ่ง ไปเป็นอีกแบบหนึ่ง")
    
    # Generate Data Range
    spans = np.linspace(1, 15, 50)
    data_points = []
    
    for s in spans:
        r = analyze_beam(s, props, fy, E_val, Fb_ratio, 0.4, defl_limit, load_type, unbraced_L)
        data_points.append({
            "Span": s,
            "Shear": r['Caps']['Shear'],
            "Moment": r['Caps']['Moment'],
            "Deflect": r['Caps']['Deflect'],
            "Safe": r['Safe_Load']
        })
    
    df_graph = pd.DataFrame(data_points)
    
    # Plotly Graph
    fig = go.Figure()
    
    # 1. Shear Line (Red Dashed)
    fig.add_trace(go.Scatter(x=df_graph.Span, y=df_graph.Shear, name="Shear Limit (ขาด)", 
                             line=dict(color='red', dash='dash', width=1)))
    
    # 2. Moment Line (Green Dashed)
    fig.add_trace(go.Scatter(x=df_graph.Span, y=df_graph.Moment, name="Moment Limit (หัก/งอ)", 
                             line=dict(color='green', dash='dash', width=1)))
    
    # 3. Deflection Line (Blue Dashed)
    fig.add_trace(go.Scatter(x=df_graph.Span, y=df_graph.Deflect, name="Deflection Limit (แอ่น)", 
                             line=dict(color='blue', dash='dash', width=1)))
    
    # 4. Net Safe Load (Black Solid - The Real Capacity)
    fig.add_trace(go.Scatter(x=df_graph.Span, y=df_graph.Safe, name="Net Safe Load (รับได้จริง)", 
                             line=dict(color='black', width=4)))
    
    # 5. Current Point Marker
    fig.add_trace(go.Scatter(x=[current_L], y=[res['Safe_Load']], mode='markers', name='Current Design',
                             marker=dict(size=15, color='orange', symbol='diamond', line=dict(color='white', width=2))))
    
    fig.update_layout(
        xaxis_title="Span Length (m)",
        yaxis_title="Load Capacity (Ton)",
        hovermode="x unified",
        height=500,
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Explanation
    st.info("""
    **วิธีอ่านกราฟ:**
    * เส้นทึบสีดำ คือน้ำหนักที่รับได้จริง (วิ่งตามเส้นที่ต่ำที่สุดเสมอ)
    * **ช่วงสั้น (ซ้าย):** มักจะถูกคุมด้วย :red[**Shear**] หรือ :green[**Moment**]
    * **ช่วงยาว (ขวา):** กราฟ :blue[**Deflection**] จะดิ่งลงเหวอย่างรวดเร็วและกลายเป็นตัวควบคุมหลัก
    """)

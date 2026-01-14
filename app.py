import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

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

st.set_page_config(page_title="Smart Beam & Connection Designer", layout="wide", page_icon="🏗️")
st.markdown("""<style>.metric-card {background-color: #f8f9fa; border: 1px solid #ddd; padding: 15px; border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);}</style>""", unsafe_allow_html=True)

# ==========================================
# 2. CALCULATION ENGINES
# ==========================================
def analyze_mixed_load(L_m, props, Fy, E, Fb_r, Fv_r, def_lim, P_load, U_load, Lb_m):
    L_cm = L_m * 100
    h_cm, tw_cm = props['h']/10, props['tw']/10
    Ix, Zx, w_kgm = props['Ix'], props['Zx'], props['w']
    
    # --- Capacities ---
    Aw = h_cm * tw_cm
    V_allow = (Fv_r * Fy) * Aw 
    
    real_Lb = min(Lb_m, L_m) if Lb_m > 0 else 0
    Lb_limit = 15 * (props['b'] / 1000)
    
    if real_Lb <= Lb_limit:
        Fb_use = Fb_r * Fy
        ltb_msg = "Compact"
    else:
        reduc = (Lb_limit / real_Lb) ** 2
        Fb_use = max((Fb_r * Fy) * reduc, 0.2*Fy)
        ltb_msg = "Slender"
        
    M_allow = Fb_use * Zx 
    Delta_allow = L_cm / def_lim 
    
    # --- Demand ---
    w_total_kgm = U_load + w_kgm 
    V_actual = (P_load / 2) + (w_total_kgm * L_m / 2) # Reaction
    
    M_point = (P_load * L_m) / 4
    M_udl = (w_total_kgm * L_m**2) / 8
    M_actual_kgm = M_point + M_udl
    M_actual_kgcm = M_actual_kgm * 100
    
    D_point = (P_load * (L_cm**3)) / (48 * E * Ix)
    w_total_kgcm = w_total_kgm / 100
    D_udl = (5 * w_total_kgcm * (L_cm**4)) / (384 * E * Ix)
    D_actual = D_point + D_udl
    
    ratio_shear = V_actual / V_allow
    ratio_moment = M_actual_kgcm / M_allow
    ratio_defl = D_actual / Delta_allow
    max_ratio = max(ratio_shear, ratio_moment, ratio_defl)
    is_pass = max_ratio <= 1.0
    
    if max_ratio == ratio_shear: gov = "Shear"
    elif max_ratio == ratio_moment: gov = "Moment"
    else: gov = "Deflection"
    
    return {
        "Pass": is_pass, "Max_Ratio": max_ratio, "Gov": gov,
        "V_act": V_actual, "V_all": V_allow,
        "M_act": M_actual_kgcm/100, "M_all": M_allow/100, "M_cap_max": (0.6*Fy*Zx)/100,
        "D_act": D_actual, "D_all": Delta_allow,
        "LTB": ltb_msg, "Weight": w_kgm * L_m, "Depth": props['h']
    }

def calculate_bolt_connection(V_demand, tw_mm, bolt_size, bolt_grade="A325/F10T"):
    # Constants
    Fu_plate = 4000 # SS400 ksc
    
    # Bolt Properties (ASD Approx)
    bolts = {
        "M12": {"area": 1.13, "shear_str": 1.0},
        "M16": {"area": 2.01, "shear_str": 2.2}, # ~1.1 t/cm2
        "M20": {"area": 3.14, "shear_str": 3.4},
        "M22": {"area": 3.80, "shear_str": 4.1},
        "M24": {"area": 4.52, "shear_str": 4.9}
    }
    
    b_prop = bolts[bolt_size]
    
    # 1. Double Shear Strength (Single Bolt) - Assuming Double Plate
    # But usually simple connection is Single Plate (Single Shear) or Double Angle (Double Shear)
    # Let's assume Single Shear for Safety (or simple shear tab)
    phi_shear = b_prop['shear_str'] * 1000 # kg per bolt (Single Shear)
    
    # 2. Bearing Strength (on Web)
    # Rb = 1.2 * Fu * d * t (ASD)
    d_cm = float(bolt_size[1:]) / 10
    t_cm = tw_mm / 10
    phi_bearing = 1.2 * Fu_plate * d_cm * t_cm 
    
    # Governing Strength per Bolt
    capacity_per_bolt = min(phi_shear, phi_bearing)
    gov_mode = "Shear" if phi_shear < phi_bearing else "Bearing (Web)"
    
    # Number of bolts
    n_required = math.ceil(V_demand / capacity_per_bolt)
    
    return {
        "Cap_Per_Bolt": capacity_per_bolt,
        "Gov_Mode": gov_mode,
        "N_Req": n_required,
        "Bearing_Cap": phi_bearing,
        "Shear_Cap": phi_shear
    }

# ==========================================
# 3. SIDEBAR & INPUTS
# ==========================================
with st.sidebar:
    st.title("⚙️ Design Inputs")
    st.subheader("1. Load Configuration")
    P_input = st.number_input("Point Load (kg)", value=1000.0, step=100.0)
    U_input = st.number_input("Superimposed UDL (kg/m)", value=500.0, step=50.0)
    L_input = st.number_input("Span Length (m)", value=6.0, step=0.5)
    Lb_input = st.number_input("Unbraced Length (Lb)", value=0.0)
    
    st.subheader("2. Parameters")
    fy = st.number_input("Fy (ksc)", value=2400)
    E_val = 2040000
    def_lim = st.selectbox("Deflection Limit", [200, 240, 300, 360, 400], index=2)
    
    st.markdown("---")
    mode = st.radio("Mode", ["Manual Check", "🤖 Auto-Optimizer"])

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
st.title("🏗️ Smart Beam & Connection Designer")

if mode == "Manual Check":
    # --- Beam Section ---
    col_sel, col_info = st.columns([1, 2])
    with col_sel:
        section_name = st.selectbox("Select Section", list(steel_db.keys()))
    with col_info:
        props = steel_db[section_name]
        st.info(f"Checking: **{section_name}** (W={props['w']} kg/m)")
        
    res = analyze_mixed_load(L_input, props, fy, E_val, 0.6, 0.4, def_lim, P_input, U_input, Lb_input)
    
    # --- Tabs ---
    tab_beam, tab_conn = st.tabs(["📊 Beam Analysis", "🔩 Connection Design"])
    
    with tab_beam:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Status", "✅ PASS" if res['Pass'] else "❌ FAIL", delta_color="normal" if res['Pass'] else "inverse")
        c2.metric("Utility", f"{res['Max_Ratio']*100:.1f}%", f"Gov: {res['Gov']}")
        c3.metric("Reaction (R)", f"{res['V_act']:.0f} kg")
        c4.metric("Deflection", f"{res['D_act']:.2f} cm")
        
        # Details
        s_rat = res['V_act']/res['V_all']
        st.markdown(f"**Shear** ({s_rat:.0%})")
        st.progress(min(s_rat, 1.0))
        
        m_rat = res['M_act']/res['M_all']
        st.markdown(f"**Moment** ({m_rat:.0%})")
        st.progress(min(m_rat, 1.0))
        
        d_rat = res['D_act']/res['D_all']
        st.markdown(f"**Deflection** ({d_rat:.0%})")
        st.progress(min(d_rat, 1.0))

    with tab_conn:
        st.markdown("### 🔩 Typical Shear Connection Design")
        st.info("ออกแบบจุดต่อรับแรงเฉือนตามหลักการ **Typical Detail** (Span 10D) หรือแรงจริง")
        
        # 1. Determine Design Load
        # Typical 10D Logic
        depth_m = res['Depth'] / 1000
        span_10d = 10 * depth_m
        
        # Calculate V_max at 10D (Typical Capacity)
        # V = 4 * M_allow / L (Derived from WL/4 = M)
        V_typical = (4 * res['M_cap_max'] * 1000) / span_10d # kg
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            design_basis = st.radio("Select Design Load Basis:", 
                                    ["Actual Reaction (แรงจริง)", "Typical Capacity (Span 10D)"])
        with col_c2:
            bolt_size = st.selectbox("Bolt Size", ["M12", "M16", "M20", "M22", "M24"], index=2)
            
        if "Actual" in design_basis:
            V_design = res['V_act']
            st.write(f"Using Actual Load V = **{V_design:,.0f} kg**")
        else:
            V_design = V_typical
            st.markdown(f"""
            Using **Typical Capacity (10D Rule)**
            - Depth: {depth_m} m -> Typical Span: {span_10d} m
            - Moment Cap: {res['M_cap_max']:.1f} ton-m
            - **Calculated Typical V = {V_design:,.0f} kg**
            """)

        # 2. Calculate Bolts
        conn_res = calculate_bolt_connection(V_design, props['tw'], bolt_size)
        
        st.divider()
        cc1, cc2, cc3 = st.columns(3)
        cc1.metric("Design Shear (V)", f"{V_design/1000:.1f} Ton")
        cc2.metric("Bolt Capacity (1-Bolt)", f"{conn_res['Cap_Per_Bolt']:.0f} kg", f"Gov: {conn_res['Gov_Mode']}")
        cc3.metric("Required Bolts", f"{conn_res['N_Req']} ตัว", delta_color="off")
        
        # 3. Recommendation Visualization
        st.markdown(f"""
        #### 👷‍♂️ Recommendation for Typical Detail
        สำหรับหน้าตัด **{section_name}** ({props['w']} kg/m)
        * **Plate:** หนาอย่างน้อย **{max(6, math.ceil(props['tw']))} mm** (Material SS400)
        * **Bolts:** ใช้ **{conn_res['N_Req']} - {bolt_size}** (Grade A325/F10T)
        * **Bearing Check:** Web หนา {props['tw']} mm -> รับแรงแบกทานได้ {conn_res['Bearing_Cap']:.0f} kg/ตัว
        """)
        
        # Visual Grid of Bolts
        if conn_res['N_Req'] > 0:
            st.markdown("##### 📐 Bolt Layout Concept:")
            rows = math.ceil(conn_res['N_Req'] / 2) if conn_res['N_Req'] > 3 else conn_res['N_Req']
            cols = 2 if conn_res['N_Req'] > 3 else 1
            st.code(f"Layout: {rows} Rows x {cols} Columns (Approx.)", language="text")

elif mode == "🤖 Auto-Optimizer":
    st.markdown("### 🤖 ระบบค้นหาหน้าตัดที่คุ้มค่าที่สุด")
    
    if st.button("🚀 Start Optimization"):
        candidates = []
        progress_bar = st.progress(0)
        total_items = len(steel_db)
        
        for i, (name, p) in enumerate(steel_db.items()):
            r = analyze_mixed_load(L_input, p, fy, E_val, 0.6, 0.4, def_lim, P_input, U_input, Lb_input)
            if r['Pass']:
                candidates.append({
                    "Section": name,
                    "Total Weight (kg)": r['Weight'],
                    "Util %": r['Max_Ratio']*100,
                    "Deflect (cm)": r['D_act']
                })
            progress_bar.progress((i+1)/total_items)
            
        if not candidates:
            st.error("❌ ไม่พบหน้าตัดที่ผ่านเกณฑ์")
        else:
            df_opt = pd.DataFrame(candidates).sort_values(by="Total Weight (kg)")
            best = df_opt.iloc[0]
            st.success(f"🏆 Winner: **{best['Section']}**")
            
            st.dataframe(df_opt.head(5).style.format("{:.1f}", subset=["Total Weight (kg)", "Util %"]))
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_opt['Total Weight (kg)'],
                y=df_opt['Util %'],
                mode='markers+text',
                text=df_opt['Section'],
                textposition="top right",
                marker=dict(size=10, color=df_opt['Util %'], colorscale='RdYlGn_r')
            ))
            st.plotly_chart(fig, use_container_width=True)

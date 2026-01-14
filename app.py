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

st.set_page_config(page_title="Smart Beam Designer", layout="wide", page_icon="🏗️")
st.markdown("""<style>.metric-card {background-color: #f8f9fa; border: 1px solid #ddd; padding: 15px; border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);}</style>""", unsafe_allow_html=True)

# ==========================================
# 2. CORE CALCULATION ENGINE (Combined Load)
# ==========================================
def analyze_mixed_load(L_m, props, Fy, E, Fb_r, Fv_r, def_lim, P_load, U_load, Lb_m):
    """
    Calculates actual stress ratios (Demand/Capacity) for mixed loads (Point + UDL + Self-Weight)
    """
    L_cm = L_m * 100
    h_cm, tw_cm = props['h']/10, props['tw']/10
    Ix, Zx, w_kgm = props['Ix'], props['Zx'], props['w']
    
    # --- 1. Capacities ---
    # Shear Cap
    Aw = h_cm * tw_cm
    V_allow = (Fv_r * Fy) * Aw 
    
    # Moment Cap (LTB Included)
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
    
    # --- 2. Demand (Load Calculation) ---
    # Self-Weight is added to U_load
    w_total_kgm = U_load + w_kgm 
    
    # Max Shear (V) - at supports
    V_actual = (P_load / 2) + (w_total_kgm * L_m / 2)
    
    # Max Moment (M) - at center (Superposition)
    M_point = (P_load * L_m) / 4
    M_udl = (w_total_kgm * L_m**2) / 8
    M_actual_kgm = M_point + M_udl
    M_actual_kgcm = M_actual_kgm * 100
    
    # Max Deflection (D) - Superposition
    # Point Load Deflection
    D_point = (P_load * (L_cm**3)) / (48 * E * Ix)
    # UDL Deflection (convert w to kg/cm)
    w_total_kgcm = w_total_kgm / 100
    D_udl = (5 * w_total_kgcm * (L_cm**4)) / (384 * E * Ix)
    D_actual = D_point + D_udl
    
    # --- 3. Ratios & Result ---
    ratio_shear = V_actual / V_allow
    ratio_moment = M_actual_kgcm / M_allow
    ratio_defl = D_actual / Delta_allow
    
    max_ratio = max(ratio_shear, ratio_moment, ratio_defl)
    is_pass = max_ratio <= 1.0
    
    if max_ratio == ratio_shear: gov = "Shear"
    elif max_ratio == ratio_moment: gov = "Moment"
    else: gov = "Deflection"
    
    return {
        "Pass": is_pass,
        "Max_Ratio": max_ratio,
        "Gov": gov,
        "V_act": V_actual, "V_all": V_allow,
        "M_act": M_actual_kgcm/100, "M_all": M_allow/100, # Show in kg.m
        "D_act": D_actual, "D_all": Delta_allow,
        "LTB": ltb_msg,
        "Weight": w_kgm * L_m
    }

# ==========================================
# 3. SIDEBAR & INPUTS
# ==========================================
with st.sidebar:
    st.title("⚙️ Design Inputs")
    
    st.subheader("1. Load Configuration")
    P_input = st.number_input("Point Load (kg)", value=1000.0, step=100.0)
    U_input = st.number_input("Superimposed UDL (kg/m)", value=500.0, step=50.0, help="ไม่รวมน้ำหนักคาน (โปรแกรมคิดให้)")
    L_input = st.number_input("Span Length (m)", value=6.0, step=0.5)
    Lb_input = st.number_input("Unbraced Length (Lb)", value=0.0, help="0 = Fully Braced")
    
    st.subheader("2. Parameters")
    fy = st.number_input("Fy (ksc)", value=2400)
    E_val = 2040000
    def_lim = st.selectbox("Deflection Limit", [200, 240, 300, 360, 400], index=2)
    
    st.markdown("---")
    st.subheader("3. Select Check Mode")
    mode = st.radio("Mode", ["Manual Check", "🤖 Auto-Optimizer"])

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
st.title("🏗️ Smart Beam Designer")

if mode == "Manual Check":
    # --- Manual Section Selection ---
    col_sel, col_info = st.columns([1, 2])
    with col_sel:
        section_name = st.selectbox("Select Section to Check", list(steel_db.keys()))
    with col_info:
        props = steel_db[section_name]
        st.info(f"Checking: **{section_name}** (W={props['w']} kg/m)")
        
    res = analyze_mixed_load(L_input, props, fy, E_val, 0.6, 0.4, def_lim, P_input, U_input, Lb_input)
    
    # --- Result Cards ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Status", "✅ PASS" if res['Pass'] else "❌ FAIL", delta_color="normal" if res['Pass'] else "inverse")
    c2.metric("Utility Ratio", f"{res['Max_Ratio']*100:.1f}%", f"Gov: {res['Gov']}")
    c3.metric("Reaction (R)", f"{res['V_act']:.0f} kg")
    c4.metric("Total Deflection", f"{res['D_act']:.2f} cm", help=f"Allow: {res['D_all']:.2f} cm")
    
    # --- Detailed Progress Bars ---
    st.markdown("### 📊 Check Details")
    
    # Shear
    s_rat = res['V_act']/res['V_all']
    col_s1, col_s2 = st.columns([1,3])
    col_s1.markdown(f"**Shear** ({s_rat:.0%})")
    col_s2.progress(min(s_rat, 1.0), text=f"{res['V_act']:.0f} / {res['V_all']:.0f} kg")
    
    # Moment
    m_rat = res['M_act']/res['M_all']
    col_m1, col_m2 = st.columns([1,3])
    col_m1.markdown(f"**Moment** ({m_rat:.0%})")
    col_m2.progress(min(m_rat, 1.0), text=f"{res['M_act']:.0f} / {res['M_all']:.0f} kg.m ({res['LTB']})")
    
    # Deflection
    d_rat = res['D_act']/res['D_all']
    col_d1, col_d2 = st.columns([1,3])
    col_d1.markdown(f"**Deflection** ({d_rat:.0%})")
    col_d2.progress(min(d_rat, 1.0), text=f"{res['D_act']:.2f} / {res['D_all']:.2f} cm")

    # --- Calculation Report Text ---
    with st.expander("📝 Show Calculation Sheet (Copy to Report)"):
        report_text = f"""
        CALCULATION SHEET
        ------------------------------------------------
        Section: {section_name}
        Span: {L_input} m | Unbraced Lb: {Lb_input} m
        Loads: Point = {P_input} kg, UDL = {U_input} kg/m
        
        PROPERTIES:
        Ix = {props['Ix']} cm4, Zx = {props['Zx']} cm3
        Weight = {props['w']} kg/m
        
        RESULTS:
        1. SHEAR CHECK:
           V_actual = {res['V_act']:.2f} kg
           V_allow  = {res['V_all']:.2f} kg
           Ratio    = {s_rat:.3f} [{"OK" if s_rat<=1 else "FAIL"}]
           
        2. MOMENT CHECK:
           M_actual = {res['M_act']:.2f} kg.m
           M_allow  = {res['M_all']:.2f} kg.m
           LTB Mode = {res['LTB']}
           Ratio    = {m_rat:.3f} [{"OK" if m_rat<=1 else "FAIL"}]
           
        3. DEFLECTION CHECK:
           D_actual = {res['D_act']:.3f} cm
           D_allow  = {res['D_all']:.3f} cm
           Ratio    = {d_rat:.3f} [{"OK" if d_rat<=1 else "FAIL"}]
           
        CONCLUSION: {"DESIGN OK ✅" if res['Pass'] else "DESIGN FAILED ❌"}
        ------------------------------------------------
        """
        st.code(report_text, language="text")

elif mode == "🤖 Auto-Optimizer":
    st.markdown("### 🤖 ระบบค้นหาหน้าตัดที่คุ้มค่าที่สุด (Best Value Selector)")
    st.info("ระบบจะตรวจสอบหน้าตัดทั้งหมดในฐานข้อมูล และเรียงลำดับตาม **น้ำหนัก (Cost)** จากน้อยไปมาก")
    
    if st.button("🚀 Start Optimization"):
        candidates = []
        
        # Loop check all
        progress_bar = st.progress(0)
        total_items = len(steel_db)
        
        for i, (name, p) in enumerate(steel_db.items()):
            r = analyze_mixed_load(L_input, p, fy, E_val, 0.6, 0.4, def_lim, P_input, U_input, Lb_input)
            if r['Pass']:
                candidates.append({
                    "Section": name,
                    "Weight (kg/m)": p['w'],
                    "Total Weight (kg)": r['Weight'],
                    "Util %": r['Max_Ratio']*100,
                    "Gov Case": r['Gov'],
                    "Deflect (cm)": r['D_act']
                })
            progress_bar.progress((i+1)/total_items)
            
        if not candidates:
            st.error("❌ ไม่พบหน้าตัดที่ผ่านเกณฑ์เลย! กรุณาลดน้ำหนักบรรทุก หรือเพิ่มความยาว Lb")
        else:
            # Sort by Weight
            df_opt = pd.DataFrame(candidates).sort_values(by="Total Weight (kg)")
            
            # Show Winner
            best = df_opt.iloc[0]
            st.success(f"🏆 Winner: **{best['Section']}** ({best['Weight (kg/m)']} kg/m)")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Steel Weight", f"{best['Total Weight (kg)']:.1f} kg")
            c2.metric("Utilization", f"{best['Util %']:.1f}%")
            c3.metric("Cost Est. (@32B)", f"{best['Total Weight (kg)']*32:,.0f} THB")
            
            # Show Table
            st.markdown("#### 📋 Top 5 Candidates (Lighter is Better)")
            st.dataframe(df_opt.head(5).style.format({"Util %": "{:.1f}", "Total Weight (kg)": "{:.1f}", "Deflect (cm)": "{:.2f}"}))
            
            # Visualization
            st.markdown("#### 📉 Comparison: Weight vs Utilization")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_opt['Total Weight (kg)'],
                y=df_opt['Util %'],
                mode='markers+text',
                text=df_opt['Section'],
                textposition="top right",
                marker=dict(size=10, color=df_opt['Util %'], colorscale='RdYlGn_r')
            ))
            fig.update_layout(xaxis_title="Total Weight (kg) [Cost]", yaxis_title="Utilization % [Efficiency]", height=400)
            st.plotly_chart(fig, use_container_width=True)

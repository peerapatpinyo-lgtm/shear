import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================
# 1. DATABASE: H-BEAM (TIS/SYS Standard)
# ==========================================
# Units: h, b, tw, tf (mm) | Ix (cm4) | Zx (cm3) | w (kg/m)
steel_db = {
    "H 100x50x5x7":    {"h": 100, "b": 50,  "tw": 5,   "tf": 7,   "Ix": 187,    "Zx": 37.5,  "w": 9.3},
    "H 100x100x6x8":   {"h": 100, "b": 100, "tw": 6,   "tf": 8,   "Ix": 383,    "Zx": 76.5,  "w": 17.2},
    "H 125x60x6x8":    {"h": 125, "b": 60,  "tw": 6,   "tf": 8,   "Ix": 413,    "Zx": 65.9,  "w": 13.1},
    "H 125x125x6.5x9": {"h": 125, "b": 125, "tw": 6.5, "tf": 9,   "Ix": 847,    "Zx": 136,   "w": 23.8},
    "H 150x75x5x7":    {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8,  "w": 14.0},
    "H 150x150x7x10":  {"h": 150, "b": 150, "tw": 7,   "tf": 10,  "Ix": 1640,   "Zx": 219,   "w": 31.5},
    "H 175x90x5x8":    {"h": 175, "b": 90,  "tw": 5,   "tf": 8,   "Ix": 1210,   "Zx": 138,   "w": 18.1},
    "H 194x150x6x9":   {"h": 194, "b": 150, "tw": 6,   "tf": 9,   "Ix": 2690,   "Zx": 277,   "w": 29.9},
    "H 200x100x5.5x8": {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "w": 21.3},
    "H 200x200x8x12":  {"h": 200, "b": 200, "tw": 8,   "tf": 12,  "Ix": 4720,   "Zx": 472,   "w": 49.9},
    "H 244x175x7x11":  {"h": 244, "b": 175, "tw": 7,   "tf": 11,  "Ix": 5610,   "Zx": 460,   "w": 44.1},
    "H 250x125x6x9":   {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "w": 29.6},
    "H 300x150x6.5x9": {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 350x175x7x11":  {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "w": 49.6},
    "H 400x200x8x13":  {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 450x200x9x14":  {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "w": 76.0},
    "H 500x200x10x16": {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
    "H 600x200x11x17": {"h": 600, "b": 200, "tw": 11,  "tf": 17,  "Ix": 77600,  "Zx": 2590,  "w": 106},
    "H 700x300x13x24": {"h": 700, "b": 300, "tw": 13,  "tf": 24,  "Ix": 201000, "Zx": 5760,  "w": 185},
    "H 800x300x14x26": {"h": 800, "b": 300, "tw": 14,  "tf": 26,  "Ix": 292000, "Zx": 7300,  "w": 210},
    "H 900x300x16x28": {"h": 900, "b": 300, "tw": 16,  "tf": 28,  "Ix": 404000, "Zx": 9000,  "w": 243},
}

# ==========================================
# 2. CONFIG & STYLE
# ==========================================
st.set_page_config(page_title="H-Beam Master Analysis", layout="wide", page_icon="📐")
st.markdown("""
<style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .success-box { padding: 10px; background-color: #d4edda; color: #155724; border-radius: 5px; }
    .warning-box { padding: 10px; background-color: #fff3cd; color: #856404; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

st.title("📐 Professional H-Beam Analyzer")
st.caption("Design Check • LTB Analysis • Formula Reference • Shear Optimization")

# ==========================================
# 3. INPUT SIDEBAR
# ==========================================
with st.sidebar:
    st.header("1. Beam & Load Config")
    section_name = st.selectbox("เลือกหน้าตัด (Section)", list(steel_db.keys()))
    props = steel_db[section_name]
    
    load_type = st.radio("รูปแบบแรง (Load Type)", ["Point Load (P)", "Uniform Load (w)"])
    
    st.divider()
    st.header("2. Geometry")
    current_L = st.number_input("ความยาวคาน (L) [m]", value=6.0, step=0.5, min_value=1.0)
    unbraced_L = st.number_input("ระยะค้ำยันด้านข้าง (Lb) [m]", value=0.0, step=0.5, help="0 = Fully Braced")
    
    st.divider()
    st.header("3. Material Properties")
    fy = st.number_input("Yield Strength (Fy) [ksc]", value=2400)
    E_val = st.number_input("Modulus Elasticity (E) [ksc]", value=2040000)
    
    col_mat1, col_mat2 = st.columns(2)
    with col_mat1:
        Fb_ratio = st.number_input("Fb Ratio", value=0.6, step=0.01)
    with col_mat2:
        Fv_ratio = st.number_input("Fv Ratio", value=0.4, step=0.01)
        
    defl_limit = st.selectbox("Deflection Limit", [200, 240, 300, 360, 400], index=2)

# ==========================================
# 4. CALCULATION ENGINE
# ==========================================
def perform_analysis(L_m, props, Fy, E, Fb_r, Fv_r, def_lim, load_type_mode, Lb_input_m):
    # --- A. Unit Setup (kg, cm) ---
    L_cm = L_m * 100
    h_cm = props['h']/10; tw_cm = props['tw']/10; b_mm = props['b']; b_cm = b_mm/10
    Ix = props['Ix']; Zx = props['Zx']
    w_kg_m = props['w']
    
    # --- B. Allowable Limits ---
    # 1. Shear (Fv)
    Aw = h_cm * tw_cm
    Fv_allow = Fv_r * Fy
    V_max_capacity = Fv_allow * Aw # kg
    
    # 2. Moment (Fb) with LTB Check
    # Rule: If Lb < 15*b (approx compact limit) -> Full Fb
    real_Lb_m = min(Lb_input_m, L_m) if Lb_input_m > 0 else 0
    limit_Lb_m = 15 * (b_mm / 1000)
    
    if real_Lb_m <= limit_Lb_m:
        Fb_final = Fb_r * Fy
        ltb_status = "Compact (OK)"
        ltb_reduction = 1.0
    else:
        # Simplified Reduction Formula (Parabolic)
        # Fb' = Fb * (Limit/Lb)^2
        reduction = (limit_Lb_m / real_Lb_m) ** 2
        Fb_final = max((Fb_r * Fy) * reduction, 0.2*Fy) # Floor at 20%
        ltb_status = "Slender (Reduced)"
        ltb_reduction = reduction
        
    M_max_capacity = Fb_final * Zx # kg.cm
    
    # 3. Deflection
    Delta_allow = L_cm / def_lim # cm
    
    # --- C. Self Weight Calculation ---
    V_self = w_kg_m * L_m / 2
    M_self = (w_kg_m * L_m**2 / 8) * 100
    w_cm = w_kg_m / 100
    Delta_self = (5 * w_cm * L_cm**4) / (384 * E * Ix)
    
    # --- D. Net Safe Load Calculation ---
    if "Point" in load_type_mode:
        # Based on Shear: P/2 + Vsw <= Vcap
        P_shear = 2 * (V_max_capacity - V_self)
        # Based on Moment: PL/4 + Msw <= Mcap
        P_moment = 4 * (M_max_capacity - M_self) / L_cm
        # Based on Defl: PL^3/48EI + Dsw <= Dallow
        P_deflect = (48 * E * Ix * (Delta_allow - Delta_self)) / (L_cm**3)
    else: # Uniform Load (UDL)
        # W_total/2 <= Vcap
        W_shear = 2 * V_max_capacity - (w_kg_m * L_m)
        # W_total*L/8 <= Mcap
        W_moment = (8 * M_max_capacity / L_cm) - (w_kg_m * L_m)
        # 5*W_total*L^3/384EI <= Dallow
        W_deflect = (384 * E * Ix * (Delta_allow - Delta_self)) / (5 * L_cm**3)
        
        P_shear = W_shear; P_moment = W_moment; P_deflect = W_deflect

    safe_load_kg = max(0, min(P_shear, P_moment, P_deflect))
    
    # --- E. Percent Utilization at Safe Load ---
    if "Point" in load_type_mode:
        V_actual = (safe_load_kg/2) + V_self
        M_actual = ((safe_load_kg * L_cm)/4) + M_self
    else:
        total_load = safe_load_kg + (w_kg_m * L_m)
        V_actual = total_load / 2
        M_actual = (total_load * L_cm) / 8
        
    v_percent = (V_actual / V_max_capacity) * 100
    m_percent = (M_actual / M_max_capacity) * 100
    
    # Identify Governor
    if safe_load_kg == P_shear: gov = "Shear (แรงเฉือน)"
    elif safe_load_kg == P_moment: gov = "Moment (โมเมนต์)"
    else: gov = "Deflection (ระยะแอ่น)"
    
    return {
        "Safe_Load_Ton": safe_load_kg/1000,
        "Gov": gov,
        "V_Percent": v_percent, "M_Percent": m_percent,
        "V_Cap": V_max_capacity, "M_Cap": M_max_capacity,
        "V_Self": V_self, "M_Self": M_self,
        "Fb_Used": Fb_final, "LTB_Status": ltb_status, "Lb_Limit": limit_Lb_m,
        "Aw": Aw, "Zx": Zx, "Ix": Ix
    }

# ==========================================
# 5. UI LAYOUT
# ==========================================
res = perform_analysis(current_L, props, fy, E_val, Fb_ratio, Fv_ratio, defl_limit, load_type, unbraced_L)

# Create Tabs
tab1, tab2, tab3 = st.tabs(["📊 Dashboard ผลลัพธ์", "📈 กราฟแนวโน้ม (Trend)", "📘 ที่มาสูตร (Formula)"])

# --- TAB 1: DASHBOARD ---
with tab1:
    c1, c2, c3 = st.columns([1.5, 1, 1])
    
    with c1:
        st.subheader("ผลการตรวจสอบรับน้ำหนัก")
        st.metric(label="Net Safe Load (น้ำหนักใช้งานปลอดภัย)", 
                  value=f"{res['Safe_Load_Ton']:.2f} Ton", 
                  delta=f"Control by: {res['Gov']}", delta_color="inverse")
        
        if "Reduced" in res['LTB_Status']:
            st.error(f"⚠️ **LTB Warning:** โมเมนต์ลดทอนเนื่องจากค้ำยันห่างเกิน {res['Lb_Limit']:.2f} ม.")
        else:
            st.success(f"✅ **LTB Status:** Compact (ค้ำยันเพียงพอ รับแรงได้เต็มที่)")

    with c2:
        st.write("**Moment Utilization**")
        st.progress(res['M_Percent']/100)
        st.caption(f"ใช้โมเมนต์ไป {res['M_Percent']:.1f}% ของหน้าตัด")

    with c3:
        st.write("**Shear Utilization**")
        color_bar = "green" if res['V_Percent'] < 50 else "orange" if res['V_Percent'] < 70 else "red"
        st.progress(res['V_Percent']/100)
        
        if 50 <= res['V_Percent'] <= 70:
            st.markdown(f":green[**Optimal Zone ({res['V_Percent']:.1f}%)**]")
        elif res['V_Percent'] > 70:
            st.markdown(f":red[**High Shear ({res['V_Percent']:.1f}%)**]")
        else:
            st.markdown(f":blue[**Low Shear ({res['V_Percent']:.1f}%)**]")

    st.markdown("---")
    
    # Recommendation Section
    st.info("💡 **Engineer's Insight:** หาก Shear Utilization ต่ำมาก (< 30%) แสดงว่าคานถูกควบคุมด้วยโมเมนต์หรือระยะแอ่น (Span ยาว) แต่ถ้า Shear Utilization สูง (50-70%) แสดงว่าเป็นคานช่วงสั้นรับแรงหนัก (Short Span, Heavy Load)")

# --- TAB 2: GRAPHS ---
with tab2:
    st.subheader(f"ความสามารถรับน้ำหนัก vs ความยาวคาน ({section_name})")
    
    L_range = np.arange(1.0, 12.0, 0.5)
    shear_vals = []
    moment_vals = []
    defl_vals = []
    safe_vals = []
    
    for l in L_range:
        r = perform_analysis(l, props, fy, E_val, Fb_ratio, Fv_ratio, defl_limit, load_type, unbraced_L)
        if "Point" in load_type:
             # Just simplified plotting logic extraction
             # Re-running full function is safer but slightly slower. For 20 points it's fine.
             pass
        # Extract tons
        safe_vals.append(r['Safe_Load_Ton'])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=L_range, y=safe_vals, mode='lines+markers', name='Net Safe Load', line=dict(color='black', width=3)))
    
    # Highlight current point
    fig.add_trace(go.Scatter(x=[current_L], y=[res['Safe_Load_Ton']], mode='markers', marker=dict(size=12, color='red'), name='Current Design'))

    fig.update_layout(xaxis_title="Span (m)", yaxis_title="Safe Load (Ton)", height=450)
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 3: FORMULA EXPLANATION (Highlights) ---
with tab3:
    st.header("📘 เอกสารอ้างอิงสูตรคำนวณ (Calculation Reference)")
    st.markdown("โปรแกรมใช้หลักการคำนวณตามมาตรฐานวิศวกรรม (Allowable Stress Design) ดังนี้:")

    # 1. SHEAR
    with st.expander("1. การคำนวณแรงเฉือน (Shear Calculation)", expanded=True):
        st.markdown("แรงเฉือนที่ยอมให้ ($V_{allow}$) คำนวณจากพื้นที่เอวคาน ($A_w$) คูณด้วยหน่วยแรงเฉือนที่ยอมให้ ($F_v$):")
        st.latex(r"V_{allow} = F_v \times A_w = (0.40 F_y) \times (h \cdot t_w)")
        st.markdown(f"""
        **แทนค่าจริง:**
        * $F_y = {fy}$ ksc
        * $A_w = {props['h']/10} \\times {props['tw']/10} = {res['Aw']:.2f}$ $cm^2$
        * $V_{{capacity}} = {res['V_Cap']:.0f}$ kg
        """)

    # 2. MOMENT & LTB
    with st.expander("2. การคำนวณโมเมนต์และ LTB (Moment & Buckling)", expanded=True):
        st.markdown("โมเมนต์ที่ยอมให้ ($M_{allow}$) ขึ้นอยู่กับหน้าตัด ($Z_x$) และหน่วยแรงดัด ($F_b$) ซึ่งแปรผันตามระยะค้ำยัน ($L_b$):")
        st.latex(r"M_{allow} = F_b \times Z_x")
        
        st.markdown("### การตรวจสอบ LTB (Lateral Torsional Buckling)")
        
        st.markdown("ใช้เกณฑ์อย่างง่าย (Simplified Rule) เพื่อตรวจสอบความชะลูด:")
        st.latex(r"L_{limit} \approx 15 \times b_{flange}")
        
        c_ltb1, c_ltb2 = st.columns(2)
        with c_ltb1:
            st.info(f"**Limit ($15b$):** {res['Lb_Limit']:.2f} m")
        with c_ltb2:
            st.warning(f"**Actual ($L_b$):** {unbraced_L if unbraced_L > 0 else 'Full Braced'} m")
            
        if "Reduced" in res['LTB_Status']:
            st.latex(r"F_{b,reduced} = F_b \times \left(\frac{L_{limit}}{L_b}\right)^2")
            st.write(f"ดังนั้น $F_b$ ลดลงเหลือ **{res['Fb_Used']:.0f} ksc**")
        else:
            st.write(f"Condition OK ($L_b \le Limit$) ดังนั้นใช้ $F_b$ ได้เต็มที่ = **{res['Fb_Used']:.0f} ksc**")

    # 3. DEFLECTION
    with st.expander("3. การคำนวณระยะแอ่น (Deflection Formulas)"):
        st.write(f"ตรวจสอบระยะแอ่นที่ยอมให้: $\Delta_{{allow}} = L/{defl_limit} = {current_L*100}/{defl_limit} = {(current_L*100)/defl_limit:.2f}$ cm")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown("**กรณี Point Load:**")
            st.latex(r"\Delta = \frac{P L^3}{48 E I_x}")
        with col_d2:
            st.markdown("**กรณี Uniform Load:**")
            st.latex(r"\Delta = \frac{5 w L^4}{384 E I_x}")
            
        st.markdown(f"**ค่า Properties ที่ใช้:** $E = {E_val:,}$ ksc, $I_x = {res['Ix']:,}$ $cm^4$")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================
# 1. DATABASE: H-BEAM (TIS/SYS Standard)
# ==========================================
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
# 2. CONFIG
# ==========================================
st.set_page_config(page_title="H-Beam Analysis + Vmax Check", layout="wide", page_icon="🏗️")
st.title("🏗️ H-Beam Design & Shear Analysis")

# ==========================================
# 3. SIDEBAR INPUTS
# ==========================================
st.sidebar.header("1. เลือกหน้าตัด")
section_name = st.sidebar.selectbox("ขนาดหน้าตัด (Section)", list(steel_db.keys()))
props = steel_db[section_name]

load_type = st.sidebar.radio("รูปแบบแรง (Load Type)", ["Point Load", "Uniform Load"])

st.sidebar.markdown("---")
st.sidebar.header("2. Material & Criteria")
fy = st.sidebar.number_input("Fy [ksc]", value=2400)
E_val = st.sidebar.number_input("E [ksc]", value=2040000)
Fb_ratio = st.sidebar.slider("Allowable Bending (Fb/Fy)", 0.4, 0.7, 0.60, 0.01)
Fv_ratio = st.sidebar.slider("Allowable Shear (Fv/Fy)", 0.3, 0.5, 0.40, 0.01)
defl_limit = st.sidebar.selectbox("Deflection Limit", [200, 240, 300, 360, 400], index=1)

st.sidebar.markdown("---")
st.sidebar.header("3. Parameters")
unbraced_L = st.sidebar.number_input("ระยะค้ำยัน Lb [m]", value=0.0, step=0.5)
current_L = st.sidebar.number_input("ความยาวคาน (Span) [m]", value=6.0, step=0.5, min_value=1.0)

# ==========================================
# 4. ENGINE (Calculation)
# ==========================================
def calculate_beam(L_m, props, Fy, E, Fb_r, Fv_r, def_lim, load_type_mode, Lb_m):
    # Conversions
    L_cm = L_m * 100
    h_cm = props['h']/10; tw_cm = props['tw']/10; b = props['b']
    Ix = props['Ix']; Zx = props['Zx']; w_kg_m = props['w']
    
    # --- Allowable Limits ---
    # Shear
    V_allow = (Fv_r * Fy) * (h_cm * tw_cm) # kg
    
    # Moment (with simplified LTB)
    real_Lb_m = min(Lb_m, L_m) if Lb_m > 0 else 0
    limit_Lb_m = 15 * (b / 1000)
    if real_Lb_m <= limit_Lb_m:
        Fb_final = Fb_r * Fy
    else:
        Fb_final = max((Fb_r * Fy) * ((limit_Lb_m/real_Lb_m)**2), 0.2*Fy)
    M_allow = Fb_final * Zx # kg.cm
    
    # Deflection
    Delta_allow = L_cm / def_lim # cm
    
    # --- Self Weight ---
    V_self = w_kg_m * L_m / 2
    M_self = (w_kg_m * L_m**2 / 8) * 100
    w_cm = w_kg_m / 100
    Delta_self = (5 * w_cm * L_cm**4) / (384 * E * Ix)
    
    # --- Solve for Net Load ---
    if "Point" in load_type_mode:
        P_shear = 2 * (V_allow - V_self)
        P_moment = 4 * (M_allow - M_self) / L_cm
        P_deflect = (48 * E * Ix * (Delta_allow - Delta_self)) / (L_cm**3)
    else: # UDL
        W_shear = 2 * V_allow - (w_kg_m * L_m)
        W_moment = (8 * M_allow / L_cm) - (w_kg_m * L_m)
        W_deflect = (384 * E * Ix * (Delta_allow - Delta_self)) / (5 * L_cm**3)
        P_shear = W_shear; P_moment = W_moment; P_deflect = W_deflect

    # Safe Load is the Minimum
    safe_load_kg = max(0, min(P_shear, P_moment, P_deflect))
    
    # --- Calculate % Utilization at Safe Load ---
    # เราจะคำนวณย้อนกลับว่า ถ้าใส่ Load เท่ากับ Safe Load แล้ว แต่ละตัวรับภาระไปกี่ %
    
    if "Point" in load_type_mode:
        V_actual = (safe_load_kg / 2) + V_self
        M_actual = ((safe_load_kg * L_cm) / 4) + M_self
        # Deflect actual is complex to back-calc linearly due to self weight but approx:
        # Delta_actual = Delta_allow (if governed by defl) or less
    else: # UDL (Total Load)
        V_actual = (safe_load_kg + (w_kg_m * L_m)) / 2
        M_actual = ((safe_load_kg + (w_kg_m * L_m)) * L_cm) / 8
        
    shear_percent = (V_actual / V_allow) * 100
    moment_percent = (M_actual / M_allow) * 100
    # Note: Deflection % is omitted for simplicity in gauge, usually follows moment.

    return {
        "Safe_Load_Ton": safe_load_kg / 1000,
        "V_Percent": shear_percent,
        "M_Percent": moment_percent,
        "Gov_Case": "Shear" if safe_load_kg == P_shear else "Moment" if safe_load_kg == P_moment else "Deflection",
        "V_Allow_Ton": V_allow/1000,
        "M_Allow_Ton_m": M_allow/100/1000
    }

# ==========================================
# 5. UI DISPLAY
# ==========================================
col1, col2 = st.columns([1, 1.5])

# --- Run Calc for Current L ---
res = calculate_beam(current_L, props, fy, E_val, Fb_ratio, Fv_ratio, defl_limit, load_type, unbraced_L)

with col1:
    st.subheader(f"ผลลัพธ์ที่ {current_L} m")
    
    # Display Safe Load
    st.metric("Net Safe Load", f"{res['Safe_Load_Ton']:.2f} Ton", delta=f"Control: {res['Gov_Case']}")
    
    st.write("### 📊 Status Check (Utilization)")
    
    # Shear Progress Bar
    v_color = "red" if res['V_Percent'] > 99 else "orange" if res['V_Percent'] > 50 else "green"
    st.write(f"**Shear Usage:** {res['V_Percent']:.1f}%")
    st.progress(min(res['V_Percent']/100, 1.0), text=f"Shear: {res['V_Percent']:.1f}%")
    
    if 50 <= res['V_Percent'] <= 70:
        st.success("✅ Shear อยู่ในช่วง 50-70% (Optimal Shear Zone)")
    elif res['V_Percent'] < 50:
        st.info("ℹ️ Shear ต่ำกว่า 50% (คานยังรับแรงเฉือนได้อีกเยอะ แต่ติดที่โมเมนต์)")
    else:
        st.warning("⚠️ Shear สูงกว่า 70% (คานสั้น รับแรงเฉือนหนัก)")

    # Moment Progress Bar
    st.write(f"**Moment Usage:** {res['M_Percent']:.1f}%")
    st.progress(min(res['M_Percent']/100, 1.0))

with col2:
    st.subheader("💡 คำแนะนำ Span ที่เหมาะสม (Vmax 50-70%)")
    
    # --- Reverse Engineer Logic ---
    # หา Span ที่ทำให้ Shear Ratio = 60% (ค่ากลางของ 50-70)
    # สมมติว่า Governing Load คือ Moment (ซึ่งปกติ H-Beam เป็นแบบนั้น)
    # P_safe(Moment) -> ทำให้เกิด V_actual = 0.6 * V_allow
    
    # สมการ: (4 * M_allow / L) / 2 = 0.6 * V_allow  [สำหรับ Point Load โดยประมาณ ตัด self-weight ออกก่อน]
    # 2 * M_allow / L = 0.6 V_allow
    # L_target = (2 * M_allow) / (0.6 * V_allow)
    
    # ดึงค่า Allowable มาคำนวณ
    V_all_kg = res['V_Allow_Ton'] * 1000
    M_all_kgcm = res['M_Allow_Ton_m'] * 1000 * 100
    
    target_ratio = 0.60
    
    if "Point" in load_type:
        # V ≈ P/2, P ≈ 4M/L => V ≈ 2M/L
        # Target: 2M/L = target_ratio * V_allow
        optimal_L_cm = (2 * M_all_kgcm) / (target_ratio * V_all_kg)
    else:
        # V ≈ wL/2 = W/2, W ≈ 8M/L => V ≈ 4M/L
        # Target: 4M/L = target_ratio * V_allow
        optimal_L_cm = (4 * M_all_kgcm) / (target_ratio * V_all_kg)
        
    optimal_L_m = optimal_L_cm / 100
    
    st.markdown(f"""
    เพื่อให้ **Shear Utilization** อยู่ในช่วง **50-70%**:
    > **Span ที่เหมาะสมคือประมาณ: `{optimal_L_m:.2f} - {optimal_L_m*1.4:.2f}` เมตร**
    """)
    st.caption("*คำนวณโดยสมมติว่าโมเมนต์เป็นตัวควบคุมหลักและต้องการใช้ Shear ให้คุ้มค่า (60%)")
    
    # --- Graph ---
    L_range = np.arange(1.0, 10.0, 0.5)
    shear_utils = []
    
    for l in L_range:
        r = calculate_beam(l, props, fy, E_val, Fb_ratio, Fv_ratio, defl_limit, load_type, unbraced_L)
        shear_utils.append(r['V_Percent'])
        
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=L_range, y=shear_utils, mode='lines+markers', name='Shear %'))
    
    # Add Zone 50-70%
    fig.add_hrect(y0=50, y1=70, line_width=0, fillcolor="green", opacity=0.2, annotation_text="Target 50-70%")
    
    fig.update_layout(
        title="ความสัมพันธ์ Span vs %Shear Usage",
        xaxis_title="ความยาว Span (m)",
        yaxis_title="Shear Utilization (%)",
        yaxis_range=[0, 110]
    )
    st.plotly_chart(fig, use_container_width=True)

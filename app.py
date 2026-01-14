import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================
# 1. DATABASE: H-BEAM (TIS/SYS Standard)
# ==========================================
# Units: h, b, tw, tf (mm) | Ix (cm4) | Zx (cm3) | w (kg/m)
steel_db = {
    # --- Series 100 (Small) ---
    "H 100x50x5x7":    {"h": 100, "b": 50,  "tw": 5,   "tf": 7,   "Ix": 187,    "Zx": 37.5,  "w": 9.3},
    "H 100x100x6x8":   {"h": 100, "b": 100, "tw": 6,   "tf": 8,   "Ix": 383,    "Zx": 76.5,  "w": 17.2},
    "H 125x60x6x8":    {"h": 125, "b": 60,  "tw": 6,   "tf": 8,   "Ix": 413,    "Zx": 65.9,  "w": 13.1},
    "H 125x125x6.5x9": {"h": 125, "b": 125, "tw": 6.5, "tf": 9,   "Ix": 847,    "Zx": 136,   "w": 23.8},
    "H 148x100x6x9":   {"h": 148, "b": 100, "tw": 6,   "tf": 9,   "Ix": 1020,   "Zx": 138,   "w": 21.1},
    "H 150x75x5x7":    {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8,  "w": 14.0},
    "H 150x150x7x10":  {"h": 150, "b": 150, "tw": 7,   "tf": 10,  "Ix": 1640,   "Zx": 219,   "w": 31.5},
    "H 175x90x5x8":    {"h": 175, "b": 90,  "tw": 5,   "tf": 8,   "Ix": 1210,   "Zx": 138,   "w": 18.1},
    "H 175x175x7.5x11":{"h": 175, "b": 175, "tw": 7.5, "tf": 11,  "Ix": 2900,   "Zx": 331,   "w": 40.2},
    "H 194x150x6x9":   {"h": 194, "b": 150, "tw": 6,   "tf": 9,   "Ix": 2690,   "Zx": 277,   "w": 29.9},

    # --- Series 200 (Medium) ---
    "H 200x100x5.5x8": {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "w": 21.3},
    "H 200x200x8x12":  {"h": 200, "b": 200, "tw": 8,   "tf": 12,  "Ix": 4720,   "Zx": 472,   "w": 49.9},
    "H 244x175x7x11":  {"h": 244, "b": 175, "tw": 7,   "tf": 11,  "Ix": 5610,   "Zx": 460,   "w": 44.1},
    "H 248x124x5x8":   {"h": 248, "b": 124, "tw": 5,   "tf": 8,   "Ix": 3540,   "Zx": 285,   "w": 25.7},
    "H 250x125x6x9":   {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "w": 29.6},
    "H 250x250x9x14":  {"h": 250, "b": 250, "tw": 9,   "tf": 14,  "Ix": 10800,  "Zx": 867,   "w": 72.4},
    "H 294x200x8x12":  {"h": 294, "b": 200, "tw": 8,   "tf": 12,  "Ix": 11300,  "Zx": 771,   "w": 56.8},

    # --- Series 300 (Large) ---
    "H 300x150x6.5x9": {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 300x300x10x15": {"h": 300, "b": 300, "tw": 10,  "tf": 15,  "Ix": 20400,  "Zx": 1360,  "w": 94.0},
    "H 340x250x9x14":  {"h": 340, "b": 250, "tw": 9,   "tf": 14,  "Ix": 21200,  "Zx": 1250,  "w": 79.7},
    "H 346x174x6x9":   {"h": 346, "b": 174, "tw": 6,   "tf": 9,   "Ix": 11100,  "Zx": 641,   "w": 41.4},
    "H 350x175x7x11":  {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "w": 49.6},
    "H 350x350x12x19": {"h": 350, "b": 350, "tw": 12,  "tf": 19,  "Ix": 40300,  "Zx": 2300,  "w": 137},
    "H 390x300x10x16": {"h": 390, "b": 300, "tw": 10,  "tf": 16,  "Ix": 38700,  "Zx": 1980,  "w": 107},

    # --- Series 400-600 ---
    "H 400x200x8x13":  {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 400x400x13x21": {"h": 400, "b": 400, "tw": 13,  "tf": 21,  "Ix": 66600,  "Zx": 3330,  "w": 172},
    "H 440x300x11x18": {"h": 440, "b": 300, "tw": 11,  "tf": 18,  "Ix": 56100,  "Zx": 2550,  "w": 124},
    "H 450x200x9x14":  {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "w": 76.0},
    "H 500x200x10x16": {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
    "H 500x300x11x18": {"h": 488, "b": 300, "tw": 11,  "tf": 18,  "Ix": 71000,  "Zx": 2910,  "w": 128},
    "H 588x300x12x20": {"h": 588, "b": 300, "tw": 12,  "tf": 20,  "Ix": 118000, "Zx": 4020,  "w": 151},
    "H 600x200x11x17": {"h": 600, "b": 200, "tw": 11,  "tf": 17,  "Ix": 77600,  "Zx": 2590,  "w": 106},
    
    # --- Series 700-900 (Extra Large) ---
    "H 700x300x13x24": {"h": 700, "b": 300, "tw": 13,  "tf": 24,  "Ix": 201000, "Zx": 5760,  "w": 185},
    "H 800x300x14x26": {"h": 800, "b": 300, "tw": 14,  "tf": 26,  "Ix": 292000, "Zx": 7300,  "w": 210},
    "H 900x300x16x28": {"h": 900, "b": 300, "tw": 16,  "tf": 28,  "Ix": 404000, "Zx": 9000,  "w": 243},
}

# ==========================================
# 2. APP CONFIGURATION
# ==========================================
st.set_page_config(page_title="H-Beam Master Calculator", layout="wide", page_icon="🏗️")

st.title("🏗️ H-Beam Professional Design Tool")
st.markdown("""
**โปรแกรมคำนวณความสามารถรับน้ำหนัก H-Beam (มาตรฐาน SYS/TIS)**
* คำนวณ **Net Safe Load** (หักน้ำหนักตัวเองอัตโนมัติ)
* ตรวจสอบ **Shear**, **Moment**, และ **Deflection**
* มีระบบตรวจสอบ **LTB (Lateral Torsional Buckling)** หากค้ำยันไม่เพียงพอ
""")

# ==========================================
# 3. SIDEBAR: INPUTS
# ==========================================
st.sidebar.header("1. เลือกหน้าตัด & รูปแบบแรง")
section_name = st.sidebar.selectbox("ขนาดหน้าตัด (Section)", list(steel_db.keys()))
props = steel_db[section_name]

# Load Type
load_type = st.sidebar.radio("รูปแบบแรงกระทำ (Load Type)", 
                             ["Point Load (แรงจุดกึ่งกลาง)", "Uniform Load (แรงแผ่สม่ำเสมอ)"])

st.sidebar.info(f"📏 Weight: **{props['w']}** kg/m\n\n📐 Ix: **{props['Ix']:,}** cm⁴ | Zx: **{props['Zx']:,}** cm³")

st.sidebar.markdown("---")
st.sidebar.header("2. คุณสมบัติวัสดุ (Material)")
fy = st.sidebar.number_input("Yield Strength (Fy) [ksc]", value=2400, step=100, help="SS400=2400, SM520=3600")
E_val = st.sidebar.number_input("Modulus of Elasticity (E) [ksc]", value=2040000)
Fb_ratio = st.sidebar.slider("Allowable Bending (Fb/Fy)", 0.4, 0.7, 0.60, 0.01)
Fv_ratio = st.sidebar.slider("Allowable Shear (Fv/Fy)", 0.3, 0.5, 0.40, 0.01)
defl_limit = st.sidebar.selectbox("Deflection Limit (L/x)", [200, 240, 300, 360, 400, 500], index=2)

st.sidebar.markdown("---")
st.sidebar.header("3. การค้ำยัน (LTB Check)")
unbraced_L = st.sidebar.number_input("ระยะห่างจุดค้ำยัน (Lb) [m]", 
                                     value=0.0, step=0.5, 
                                     help="ใส่ 0.0 หากมีการค้ำยันตลอดแนว หรือระบุระยะห่างคานซอย")

st.sidebar.markdown("---")
st.sidebar.header("4. พารามิเตอร์อื่นๆ")
current_L = st.sidebar.number_input("ระบุความยาวช่วงคาน (Span) [m]", value=6.0, step=0.5, min_value=1.0)
unit_price = st.sidebar.number_input("ราคาเหล็กประเมิน (บาท/กก.)", value=32.0, step=0.5)

# ==========================================
# 4. CALCULATION ENGINE (With LTB & Self-Weight)
# ==========================================
def calculate_net_capacity(L_m, props, Fy, E, Fb_r, Fv_r, def_lim, load_type_mode, Lb_input_m):
    """
    คำนวณ Net Safe Load (Ton) โดยพิจารณา LTB และหักน้ำหนักตัวเอง
    """
    # 1. Unit Conversions
    L_cm = L_m * 100
    h = props['h']; b = props['b']; tw = props['tw']; tf = props['tf']
    h_cm = h / 10; tw_cm = tw / 10
    Ix = props['Ix']; Zx = props['Zx']
    w_beam_kg_m = props['w']
    
    # 2. Determine Effective Unbraced Length (Lb)
    # ถ้า User ใส่ 0 คือ Fully Braced (Lb=0), ถ้าใส่ค่าอื่นให้ใช้ค่านั้น (แต่ไม่เกิน Span)
    real_Lb_m = min(Lb_input_m, L_m) if Lb_input_m > 0 else 0
    
    # 3. Calculate Allowable Stresses
    
    # --- Shear (Fv) ---
    Aw = h_cm * tw_cm
    V_allow_gross = (Fv_r * Fy) * Aw  # kg

    # --- Moment (Fb) with LTB Check ---
    # Simplified LTB Rule: 
    # If Lb < 15*b -> Compact (Full Fb)
    # If Lb > 15*b -> Reduce Fb (Simplified Quadratic Reduction for Safety)
    
    limit_Lb_m = 15 * (b / 1000) # b is mm -> m
    
    if real_Lb_m <= limit_Lb_m:
        Fb_final = Fb_r * Fy
        ltb_status = "Compact (OK)"
    else:
        # LTB Occurs: Reduce Fb
        # สูตรลดทอนแบบ Simplified (Conservative)
        reduction_factor = (limit_Lb_m / real_Lb_m) ** 2
        Fb_final = (Fb_r * Fy) * reduction_factor
        # กันค่าต่ำเกินไป (Floor at 20% of Fy)
        Fb_final = max(Fb_final, 0.2 * Fy)
        ltb_status = "Slender (Reduced Fb)"

    M_allow_gross = Fb_final * Zx  # kg.cm

    # --- Deflection ---
    Delta_allow_total = L_cm / def_lim  # cm

    # 4. Calculate Self-Weight Effects (Always UDL)
    V_self = (w_beam_kg_m * L_m) / 2
    M_self_kgcm = (w_beam_kg_m * (L_m**2) / 8) * 100
    
    w_beam_kg_cm = w_beam_kg_m / 100
    Delta_self = (5 * w_beam_kg_cm * (L_cm**4)) / (384 * E * Ix)

    # 5. Calculate Net Capacity based on Load Type
    
    if "Point Load" in load_type_mode:
        # Shear Check
        P_shear_kg = 2 * (V_allow_gross - V_self)
        
        # Moment Check
        P_moment_kg = 4 * (M_allow_gross - M_self_kgcm) / L_cm
        
        # Deflection Check
        Delta_remaining = Delta_allow_total - Delta_self
        P_deflect_kg = (48 * E * Ix * Delta_remaining) / (L_cm**3)
        
    else: # Uniform Load (UDL)
        # Solve for Total Load W_total then subtract beam weight
        
        # Shear
        W_total_shear = 2 * V_allow_gross
        P_shear_kg = W_total_shear - (w_beam_kg_m * L_m)
        
        # Moment
        W_total_moment = (8 * M_allow_gross) / L_cm # Result is Total Load in kg
        P_moment_kg = W_total_moment - (w_beam_kg_m * L_m)
        
        # Deflection (Std Formula adjusted for Total Load W)
        Delta_remaining = Delta_allow_total - Delta_self
        P_deflect_kg = (384 * E * Ix * Delta_remaining) / (5 * (L_cm**3))

    # 6. Return Results (Handle negative capacities)
    return {
        "Span_m": L_m,
        "Shear_Ton": max(0, P_shear_kg / 1000),
        "Moment_Ton": max(0, P_moment_kg / 1000),
        "Deflect_Ton": max(0, P_deflect_kg / 1000),
        "Self_Weight_Ton": (w_beam_kg_m * L_m) / 1000,
        "Fb_Used": Fb_final,
        "LTB_Status": ltb_status,
        "Lb_m": real_Lb_m
    }

# ==========================================
# 5. MAIN LOGIC & UI DISPLAY
# ==========================================

# --- Calculate Specific Point ---
res = calculate_net_capacity(current_L, props, fy, E_val, Fb_ratio, Fv_ratio, defl_limit, load_type, unbraced_L)
safe_load = min(res["Shear_Ton"], res["Moment_Ton"], res["Deflect_Ton"])

# Determine Governing Case
if safe_load == res["Shear_Ton"]:
    gov_case = "Shear (แรงเฉือน)"
    gov_color = "red"
elif safe_load == res["Moment_Ton"]:
    gov_case = "Moment (โมเมนต์ดัด)"
    gov_color = "green"
else:
    gov_case = "Deflection (ระยะแอ่น)"
    gov_color = "blue"

# Calculate Cost
total_weight_kg = props['w'] * current_L
total_cost = total_weight_kg * unit_price

# --- Layout Columns ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader(f"📌 ผลลัพธ์ที่ระยะ {current_L} m")
    
    # Big Number Card
    st.markdown(f"""
    <div style="text-align: center; border: 2px solid #e6e9ef; padding: 20px; border-radius: 10px; background-color: #f9f9f9;">
        <h3 style="margin:0; color: #555;">Net Safe Load</h3>
        <h1 style="margin:0; color: #ff4b4b; font-size: 56px;">{safe_load:.2f} <span style="font-size: 24px;">Ton</span></h1>
        <p style="color: grey; margin-top: 5px;">(น้ำหนักใช้งานจริง ปลอดภัย)</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    st.markdown(f"**Controlled by:** :{gov_color}[**{gov_case}**]")
    
    # LTB Warning
    if "Reduced" in res['LTB_Status']:
        st.warning(f"⚠️ **LTB Alert:** หน้าตัดเกิดการโก่งเดาะ (Lb={res['Lb_m']}m) ค่ารับโมเมนต์ถูกลดลงเหลือ Fb = {res['Fb_Used']:.0f} ksc")
    else:
        st.success(f"✅ **LTB Status:** Compact (ปลอดภัย) Fb = {res['Fb_Used']:.0f} ksc")

    with st.expander("📊 ดูรายละเอียดการคำนวณ", expanded=True):
        st.write(f"🔹 **Shear Cap:** {res['Shear_Ton']:.2f} Ton")
        st.write(f"🔹 **Moment Cap:** {res['Moment_Ton']:.2f} Ton")
        st.write(f"🔹 **Deflection Limit:** {res['Deflect_Ton']:.2f} Ton")
        st.divider()
        st.write(f"⚖️ **น้ำหนักคาน:** {res['Self_Weight_Ton']*1000:.1f} kg")
        st.write(f"💰 **ราคาเหล็ก (Est.):** {total_cost:,.0f} บาท")

# --- Generate Graph Data ---
# Logic: Graph shows capacity vs Span based on the *User's Bracing Input*
# If user sets Lb=0, graph assumes fully braced everywhere.
# If user sets Lb=2, graph assumes Lb=2 for all spans > 2.

L_range = np.arange(1.0, 16.0, 0.25)
data_list = []

for L in L_range:
    # Pass the user's unbraced_L setting to the loop
    r = calculate_net_capacity(L, props, fy, E_val, Fb_ratio, Fv_ratio, defl_limit, load_type, unbraced_L)
    min_val = min(r["Shear_Ton"], r["Moment_Ton"], r["Deflect_Ton"])
    r["Safe_Load"] = min_val
    data_list.append(r)

df = pd.DataFrame(data_list)

with col2:
    st.subheader(f"📈 Load Capacity Chart: {section_name}")
    st.caption(f"Mode: {load_type} | Bracing Lb: {unbraced_L if unbraced_L>0 else 'Auto/Full'} m")
    
    fig = go.Figure()
    
    # Capacity Lines
    fig.add_trace(go.Scatter(x=df['Span_m'], y=df['Shear_Ton'], mode='lines', name='Shear Limit', line=dict(color='red', dash='dash', width=1)))
    fig.add_trace(go.Scatter(x=df['Span_m'], y=df['Moment_Ton'], mode='lines', name='Moment Limit', line=dict(color='green', dash='dot', width=1)))
    fig.add_trace(go.Scatter(x=df['Span_m'], y=df['Deflect_Ton'], mode='lines', name='Deflection Limit', line=dict(color='blue', dash='dot', width=1)))
    
    # Safe Load Line (Thick Black)
    fig.add_trace(go.Scatter(x=df['Span_m'], y=df['Safe_Load'], mode='lines', name='Safe Net Load', line=dict(color='black', width=3)))

    # Current Point Marker
    fig.add_trace(go.Scatter(x=[current_L], y=[safe_load], mode='markers',
                             marker=dict(size=15, color='orange', symbol='diamond', line=dict(width=2, color='white')), 
                             name='Selected Span'))

    fig.update_layout(
        xaxis_title="Span Length (m)",
        yaxis_title="Net Safe Load (Ton)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=20, b=20),
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 6. EXPORT DATA
# ==========================================
st.markdown("### 📋 ตารางข้อมูล (Export Data)")

cols_show = ["Span_m", "Shear_Ton", "Moment_Ton", "Deflect_Ton", "Safe_Load", "Self_Weight_Ton"]
st.dataframe(df[cols_show].style.format("{:.2f}"))

csv = df.to_csv(index=False).encode('utf-8')
file_name_clean = section_name.replace(" ", "_").replace(".", "")
st.download_button(
    label="📥 Download CSV Report",
    data=csv,
    file_name=f'Capacity_{file_name_clean}.csv',
    mime='text/csv',
)

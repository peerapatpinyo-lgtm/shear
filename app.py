import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 1. Database: ข้อมูลหน้าตัด H-Beam (SYS Reference) ---
# หน่วย: h, b, tw, tf (mm) | Ix (cm4) | Zx (cm3) | w (kg/m)
# อ้างอิง: SYS Steel Table
steel_db = {
    "H 100x50x5x7":   {"h": 100, "b": 50,  "tw": 5,   "tf": 7,  "Ix": 187,   "Zx": 37.5, "w": 9.3},
    "H 125x60x6x8":   {"h": 125, "b": 60,  "tw": 6,   "tf": 8,  "Ix": 413,   "Zx": 65.9, "w": 13.1},
    "H 150x75x5x7":   {"h": 150, "b": 75,  "tw": 5,   "tf": 7,  "Ix": 666,   "Zx": 88.8, "w": 14.0},
    "H 175x90x5x8":   {"h": 175, "b": 90,  "tw": 5,   "tf": 8,  "Ix": 1210,  "Zx": 138,  "w": 18.1},
    "H 194x150x6x9":  {"h": 194, "b": 150, "tw": 6,   "tf": 9,  "Ix": 2690,  "Zx": 277,  "w": 29.9},
    "H 200x100x5.5x8":{"h": 200, "b": 100, "tw": 5.5, "tf": 8,  "Ix": 1840,  "Zx": 184,  "w": 21.3},
    "H 200x200x8x12": {"h": 200, "b": 200, "tw": 8,   "tf": 12, "Ix": 4720,  "Zx": 472,  "w": 49.9},
    "H 250x125x6x9":  {"h": 250, "b": 125, "tw": 6,   "tf": 9,  "Ix": 3690,  "Zx": 295,  "w": 29.6},
    "H 300x150x6.5x9":{"h": 300, "b": 150, "tw": 6.5, "tf": 9,  "Ix": 7210,  "Zx": 481,  "w": 36.7},
    "H 350x175x7x11": {"h": 350, "b": 175, "tw": 7,   "tf": 11, "Ix": 13600, "Zx": 775,  "w": 49.6},
    "H 400x200x8x13": {"h": 400, "b": 200, "tw": 8,   "tf": 13, "Ix": 23700, "Zx": 1190, "w": 66.0},
}

# --- 2. Configuration & Constants ---
st.set_page_config(page_title="H-Beam Master Calculator", layout="wide", page_icon="🏗️")
st.title("🏗️ H-Beam Design Calculator (SYS Reference)")
st.markdown("""
เครื่องมือคำนวณน้ำหนักบรรทุกปลอดภัย (Safe Load) โดยพิจารณา **Shear**, **Moment**, และ **Deflection**
* ข้อมูลอ้างอิง: **Siam Yamato Steel (SYS)**
* หักลบน้ำหนักตัวเองของคาน (Self-weight) เรียบร้อยแล้ว
""")

# --- Sidebar Inputs ---
st.sidebar.header("1. เลือกหน้าตัด & รูปแบบแรง")
section_name = st.sidebar.selectbox("ขนาดหน้าตัด (Section)", list(steel_db.keys()))
props = steel_db[section_name]

# Load Type Selection
load_type = st.sidebar.radio("รูปแบบแรงกระทำ (Load Type)", 
                             ["Point Load (แรงจุดกึ่งกลาง)", "Uniform Load (แรงแผ่สม่ำเสมอ)"])

st.sidebar.info(f"น้ำหนักเหล็ก: **{props['w']}** kg/m")

st.sidebar.markdown("---")
st.sidebar.header("2. คุณสมบัติวัสดุ (Design Criteria)")
fy = st.sidebar.number_input("Yield Strength (Fy) [ksc]", value=2400, step=100)
E_val = st.sidebar.number_input("Modulus of Elasticity (E) [ksc]", value=2040000)
Fb_ratio = st.sidebar.slider("Allowable Bending (Fb/Fy)", 0.4, 0.7, 0.60, 0.01)
Fv_ratio = st.sidebar.slider("Allowable Shear (Fv/Fy)", 0.3, 0.5, 0.40, 0.01)
defl_limit = st.sidebar.selectbox("Deflection Limit (L/x)", [200, 240, 300, 360, 400, 500], index=1)

st.sidebar.markdown("---")
st.sidebar.header("3. พารามิเตอร์อื่นๆ")
current_L = st.sidebar.number_input("ระบุความยาวที่ต้องการตรวจสอบ (m)", value=5.0, step=0.5, min_value=1.0)
unit_price = st.sidebar.number_input("ราคาเหล็กประเมิน (บาท/กก.)", value=32.0, step=0.5)

# --- 3. Calculation Engine (Updated for UDL & Self-Weight) ---
def calculate_net_capacity(L_m, props, Fy, E, Fb_r, Fv_r, def_lim, load_type_mode):
    """
    คืนค่า Net Capacity (Ton) ที่หักน้ำหนักคานออกแล้ว
    """
    # Convert Units
    L_cm = L_m * 100
    h_cm = props['h'] / 10
    tw_cm = props['tw'] / 10
    Ix = props['Ix']
    Zx = props['Zx']
    w_beam_kg_m = props['w'] 
    
    # 1. Allowable Forces (Gross)
    # Shear
    Aw = h_cm * tw_cm
    V_allow_gross = (Fv_r * Fy) * Aw
    
    # Moment
    M_allow_gross = (Fb_r * Fy) * Zx
    
    # Deflection Allowed
    Delta_allow_total = L_cm / def_lim

    # 2. Self-Weight Effects
    # Moment & Shear from Self-weight (Always UDL)
    V_self = (w_beam_kg_m * L_m) / 2
    M_self_kgcm = (w_beam_kg_m * (L_m**2) / 8) * 100
    
    # Deflection from Self-weight (5wL^4 / 384EI)
    # w for deflect formula need to be kg/cm -> w_kg_m / 100
    w_beam_kg_cm = w_beam_kg_m / 100
    Delta_self = (5 * w_beam_kg_cm * (L_cm**4)) / (384 * E * Ix)

    # 3. Calculate Net Capacity based on Load Type
    
    if "Point Load" in load_type_mode:
        # P_shear: V_max = P/2 + V_self <= V_allow
        P_shear_kg = 2 * (V_allow_gross - V_self)
        
        # P_moment: M_max = PL/4 + M_self <= M_allow
        P_moment_kg = 4 * (M_allow_gross - M_self_kgcm) / L_cm
        
        # P_deflect: Delta_P + Delta_self <= Delta_allow
        Delta_remaining = Delta_allow_total - Delta_self
        P_deflect_kg = (48 * E * Ix * Delta_remaining) / (L_cm**3)
        
    else: # Uniform Load (UDL)
        # We calculate Total Load (W_total) then subtract Beam Weight
        
        # Shear: V_max = W_total/2 <= V_allow
        W_total_shear = 2 * V_allow_gross
        P_shear_kg = W_total_shear - (w_beam_kg_m * L_m)
        
        # Moment: M_max = W_total*L/8 <= M_allow
        W_total_moment = (8 * M_allow_gross) / L_cm # Result is Total Load in kg
        P_moment_kg = W_total_moment - (w_beam_kg_m * L_m)
        
        # Deflection: Delta = 5*W_total*L^3 / 384EI (Note formula adjustment for Total Load W)
        # Standard UDL formula with w (load/length): 5wL^4/384EI
        # If using Total Load (W = wL): 5WL^3/384EI
        Delta_remaining = Delta_allow_total - Delta_self
        P_deflect_kg = (384 * E * Ix * Delta_remaining) / (5 * (L_cm**3))

    # Return results (Prevent negative values if self-weight fails)
    return {
        "Span_m": L_m,
        "Shear_Ton": max(0, P_shear_kg / 1000),
        "Moment_Ton": max(0, P_moment_kg / 1000),
        "Deflect_Ton": max(0, P_deflect_kg / 1000),
        "Self_Weight_Ton": (w_beam_kg_m * L_m) / 1000
    }

# --- 4. Main Processing ---

# Calculate Specific Point
res = calculate_net_capacity(current_L, props, fy, E_val, Fb_ratio, Fv_ratio, defl_limit, load_type)
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

# --- 5. Display UI ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader(f"📌 ผลลัพธ์ที่ระยะ {current_L} m")
    
    # Big Number Display
    st.markdown(f"""
    <div style="text-align: center; border: 2px solid #f0f2f6; padding: 20px; border-radius: 10px;">
        <h3 style="margin:0; color: #555;">Net Safe Load</h3>
        <h1 style="margin:0; color: #ff4b4b; font-size: 48px;">{safe_load:.2f} <span style="font-size: 20px;">Ton</span></h1>
        <p style="color: grey;">(น้ำหนักบรรทุกปลอดภัยที่รับได้จริง)</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"**ควบคุมโดย:** :{gov_color}[{gov_case}]")
    
    with st.expander("📊 ดูรายละเอียดการคำนวณ"):
        st.write(f"🔹 **Shear Cap:** {res['Shear_Ton']:.2f} Ton")
        st.write(f"🔹 **Moment Cap:** {res['Moment_Ton']:.2f} Ton")
        st.write(f"🔹 **Deflection Limit:** {res['Deflect_Ton']:.2f} Ton")
        st.divider()
        st.write(f"⚖️ **น้ำหนักคาน:** {res['Self_Weight_Ton']*1000:.1f} kg")
        st.write(f"💰 **ราคาประเมิน:** {total_cost:,.0f} บาท")

# --- 6. Graph Generation ---
L_range = np.arange(1.0, 15.1, 0.2)
data_list = []

for L in L_range:
    r = calculate_net_capacity(L, props, fy, E_val, Fb_ratio, Fv_ratio, defl_limit, load_type)
    min_val = min(r["Shear_Ton"], r["Moment_Ton"], r["Deflect_Ton"])
    r["Safe_Load"] = min_val
    data_list.append(r)

df = pd.DataFrame(data_list)

with col2:
    st.subheader(f"📈 กราฟความสามารถรับน้ำหนัก: {section_name}")
    st.caption(f"Load Type: {load_type} (หักน้ำหนักคานแล้ว)")
    
    fig = go.Figure()
    
    # Plot Lines
    fig.add_trace(go.Scatter(x=df['Span_m'], y=df['Shear_Ton'], mode='lines', name='Shear', line=dict(color='red', dash='dash', width=1)))
    fig.add_trace(go.Scatter(x=df['Span_m'], y=df['Moment_Ton'], mode='lines', name='Moment', line=dict(color='green', dash='dot', width=1)))
    fig.add_trace(go.Scatter(x=df['Span_m'], y=df['Deflect_Ton'], mode='lines', name='Deflection', line=dict(color='blue', dash='dot', width=1)))
    
    # Main Safe Load Line
    fig.add_trace(go.Scatter(x=df['Span_m'], y=df['Safe_Load'], mode='lines', name='Safe Design Load', line=dict(color='black', width=3)))

    # Point Marker
    fig.add_trace(go.Scatter(x=[current_L], y=[safe_load], mode='markers+text',
                             text=[f"{safe_load:.2f} T"], textposition="top right",
                             marker=dict(size=12, color='orange', symbol='diamond'), name='จุดที่เลือก'))

    fig.update_layout(
        xaxis_title="ความยาวคาน (เมตร)",
        yaxis_title="น้ำหนักบรรทุกปลอดภัยสุทธิ (ตัน)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

# --- 7. Data Table & Export ---
st.markdown("### 📋 ตารางข้อมูล (Export)")
cols_show = ["Span_m", "Shear_Ton", "Moment_Ton", "Deflect_Ton", "Safe_Load", "Self_Weight_Ton"]
st.dataframe(df[cols_show].style.format("{:.2f}"))

csv = df.to_csv(index=False).encode('utf-8')
file_name_clean = section_name.replace(" ", "_").replace(".", "")
st.download_button(
    label="📥 Download CSV",
    data=csv,
    file_name=f'Capacity_{file_name_clean}.csv',
    mime='text/csv',
)

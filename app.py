import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 1. Database: ข้อมูลหน้าตัด H-Beam (SYS Reference) ---
# หน่วย: h, b, tw, tf (mm) | Ix (cm4) | Zx (cm3)
steel_db = {
    "H 100x50x5x7":   {"h": 100, "b": 50,  "tw": 5, "tf": 7,  "Ix": 187,   "Zx": 37.5},
    "H 125x60x6x8":   {"h": 125, "b": 60,  "tw": 6, "tf": 8,  "Ix": 413,   "Zx": 65.9},
    "H 150x75x5x7":   {"h": 150, "b": 75,  "tw": 5, "tf": 7,  "Ix": 666,   "Zx": 88.8},
    "H 175x90x5x8":   {"h": 175, "b": 90,  "tw": 5, "tf": 8,  "Ix": 1210,  "Zx": 138},
    "H 194x150x6x9":  {"h": 194, "b": 150, "tw": 6, "tf": 9,  "Ix": 2690,  "Zx": 277},
    "H 200x100x5.5x8":{"h": 200, "b": 100, "tw": 5.5,"tf":8,  "Ix": 1840,  "Zx": 184},
    "H 200x200x8x12": {"h": 200, "b": 200, "tw": 8, "tf": 12, "Ix": 4720,  "Zx": 472},
    "H 250x125x6x9":  {"h": 250, "b": 125, "tw": 6, "tf": 9,  "Ix": 3690,  "Zx": 295},
    "H 300x150x6.5x9":{"h": 300, "b": 150, "tw": 6.5,"tf":9,  "Ix": 7210,  "Zx": 481},
    "H 350x175x7x11": {"h": 350, "b": 175, "tw": 7, "tf": 11, "Ix": 13600, "Zx": 775},
    "H 400x200x8x13": {"h": 400, "b": 200, "tw": 8, "tf": 13, "Ix": 23700, "Zx": 1190},
}

# --- 2. Configuration & Constants ---
st.set_page_config(page_title="H-Beam Capacity Calculator", layout="wide")
st.title("🏗️ H-Beam Load Capacity Calculator (Point Load)")
st.markdown("""
โปรแกรมคำนวณความสามารถในการรับน้ำหนัก (Point Load ที่กึ่งกลางคาน) 
โดยเปรียบเทียบ 3 เงื่อนไข: **แรงเฉือน (Shear)**, **โมเมนต์ (Moment)**, และ **การแอ่นตัว (Deflection)**
""")

# Sidebar Inputs
st.sidebar.header("⚙️ Design Parameters")

section_name = st.sidebar.selectbox("เลือกขนาดหน้าตัด (Section)", list(steel_db.keys()))
props = steel_db[section_name]

# Material Properties
st.sidebar.markdown("---")
st.sidebar.subheader("คุณสมบัติวัสดุ")
fy = st.sidebar.number_input("Yield Strength (Fy) [ksc]", value=2400, step=100)
E_val = st.sidebar.number_input("Modulus of Elasticity (E) [ksc]", value=2040000)

# Allowable Factors (ASD)
st.sidebar.markdown("---")
st.sidebar.subheader("Design Criteria")
Fb_ratio = st.sidebar.slider("Allowable Bending Stress (Fb/Fy)", 0.4, 0.7, 0.60, 0.01)
Fv_ratio = st.sidebar.slider("Allowable Shear Stress (Fv/Fy)", 0.3, 0.5, 0.40, 0.01)
defl_limit = st.sidebar.selectbox("Deflection Limit (L/x)", [240, 300, 360, 400, 500], index=0)

# Span Input for Specific Calculation
st.sidebar.markdown("---")
current_L = st.sidebar.number_input("ระบุความยาวที่ต้องการตรวจสอบ (m)", value=4.0, step=0.5, min_value=0.5)

# --- 3. Calculation Engine ---
def calculate_capacity(L_m, props, Fy, E, Fb_r, Fv_r, def_lim):
    """
    คืนค่า P_allow (Ton) สำหรับทั้ง 3 Cases (Point Load at Center)
    L_m: Length in meters
    """
    # Convert units to cm/kg
    L_cm = L_m * 100
    h_cm = props['h'] / 10
    tw_cm = props['tw'] / 10
    Ix = props['Ix']
    Zx = props['Zx']
    
    # 1. Shear Capacity (Vn) -> Control by Web Area
    # V_allow = Fv * Aw
    # Point Load Max Shear = P/2 -> P_shear = 2 * V_allow
    Aw = h_cm * tw_cm 
    Fv = Fv_r * Fy
    V_allow = Fv * Aw
    P_shear_kg = 2 * V_allow
    
    # 2. Moment Capacity (Vm) -> Control by Section Modulus
    # M_max = PL/4 -> P = 4*M_allow / L
    Fb = Fb_r * Fy
    M_allow_kgcm = Fb * Zx
    P_moment_kg = (4 * M_allow_kgcm) / L_cm
    
    # 3. Deflection Limit (Vd) -> Control by Moment of Inertia
    # Delta_allow = L / def_lim
    # Delta_max = (P * L^3) / (48 * E * I)
    # P = (48 * E * I) / (def_lim * L^2)
    P_deflect_kg = (48 * E * Ix) / (def_lim * (L_cm**2))
    
    return {
        "Span_m": L_m,
        "Shear_Ton": P_shear_kg / 1000,
        "Moment_Ton": P_moment_kg / 1000,
        "Deflect_Ton": P_deflect_kg / 1000
    }

# --- 4. Main Process ---

# Calculate for the specific point selected in sidebar
res_point = calculate_capacity(current_L, props, fy, E_val, Fb_ratio, Fv_ratio, defl_limit)
design_load = min(res_point["Shear_Ton"], res_point["Moment_Ton"], res_point["Deflect_Ton"])

# Determine Governing Case
if design_load == res_point["Shear_Ton"]:
    gov_case = "Shear (แรงเฉือน)"
    gov_color = "red"
elif design_load == res_point["Moment_Ton"]:
    gov_case = "Moment (โมเมนต์ดัด)"
    gov_color = "green"
else:
    gov_case = "Deflection (การแอ่นตัว)"
    gov_color = "blue"

# --- 5. Display Specific Result ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader(f"📌 ผลลัพธ์ที่ความยาว {current_L} m")
    st.info(f"Design Load (ปลอดภัย): **{design_load:.2f} Ton**")
    st.write(f"ควบคุมโดย: **:{gov_color}[{gov_case}]**")
    
    st.markdown("---")
    st.caption("รายละเอียดแต่ละ Case:")
    st.write(f"🔹 Shear Cap: **{res_point['Shear_Ton']:.2f}** Ton")
    st.write(f"🔹 Moment Cap: **{res_point['Moment_Ton']:.2f}** Ton")
    st.write(f"🔹 Deflection Limit: **{res_point['Deflect_Ton']:.2f}** Ton")

# --- 6. Generate Data for Graph ---
L_range = np.arange(1.0, 15.1, 0.1) # คำนวณตั้งแต่ 1m ถึง 15m
data_list = []

for L in L_range:
    res = calculate_capacity(L, props, fy, E_val, Fb_ratio, Fv_ratio, defl_limit)
    
    # หาค่าต่ำสุด
    min_val = min(res["Shear_Ton"], res["Moment_Ton"], res["Deflect_Ton"])
    
    # หาว่า case ไหน control
    if min_val == res["Shear_Ton"]: case_txt = "Shear"
    elif min_val == res["Moment_Ton"]: case_txt = "Moment"
    else: case_txt = "Deflection"
    
    res["Design_Load"] = min_val
    res["Control_Case"] = case_txt
    data_list.append(res)

df = pd.DataFrame(data_list)

# --- 7. Plot Graph using Plotly ---
with col2:
    st.subheader(f"📈 กราฟเปรียบเทียบ: {section_name}")
    
    fig = go.Figure()

    # Plot Shear
    fig.add_trace(go.Scatter(x=df['Span_m'], y=df['Shear_Ton'], mode='lines', 
                             name='Shear Capacity', line=dict(color='red', dash='dash')))

    # Plot Moment
    fig.add_trace(go.Scatter(x=df['Span_m'], y=df['Moment_Ton'], mode='lines', 
                             name='Moment Capacity', line=dict(color='green', dash='dot')))

    # Plot Deflection
    fig.add_trace(go.Scatter(x=df['Span_m'], y=df['Deflect_Ton'], mode='lines', 
                             name='Deflection Limit', line=dict(color='blue', dash='dot')))
    
    # Plot Design Load (The governing line)
    fig.add_trace(go.Scatter(x=df['Span_m'], y=df['Design_Load'], mode='lines', 
                             name='Safe Design Load', line=dict(color='black', width=4)))

    # Highlight Selected Point
    fig.add_trace(go.Scatter(x=[current_L], y=[design_load], mode='markers',
                             marker=dict(size=12, color='orange'), name='จุดที่เลือก'))

    fig.update_layout(
        xaxis_title="ความยาวคาน (เมตร)",
        yaxis_title="น้ำหนักบรรทุกปลอดภัย (Point Load: ตัน)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)

# --- 8. Data Table & Export ---
st.markdown("### 📋 ตารางข้อมูล CSV")

# Define columns to format as numbers
numeric_cols = ["Span_m", "Shear_Ton", "Moment_Ton", "Deflect_Ton", "Design_Load"]

# ใช้ subset เพื่อ Format เฉพาะคอลัมน์ตัวเลข (ป้องกัน Error กับคอลัมน์ string)
st.dataframe(df.style.format(subset=numeric_cols, formatter="{:.2f}"))

# CSV Download
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download CSV",
    data=csv,
    file_name=f'capacity_{section_name.replace(" ", "_")}.csv',
    mime='text/csv',
)

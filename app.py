import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================
# 1. SYS STEEL DATABASE (FULL TABLE)
# ==========================================
def load_sys_data():
    # ข้อมูลจำลองจากตาราง SYS (Siam Yamato Steel)
    # Units: mm for dimensions, cm2 for Area, cm4 for Ix, cm3 for Zx
    data = [
        # Name, h, b, tw, tf, Ix, Zx
        ("H 100x50x5x7", 100, 50, 5, 7, 378, 76.5),
        ("H 150x75x5x7", 150, 75, 5, 7, 666, 88.8),
        ("H 150x100x6x9", 150, 100, 6, 9, 1020, 136),
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
    df = pd.DataFrame(data, columns=["Section", "h", "b", "tw", "tf", "Ix", "Zx"])
    return df

# ==========================================
# 2. SETUP PAGE
# ==========================================
st.set_page_config(page_title="SYS Beam Capacity Analyzer", layout="wide", page_icon="🏗️")
st.title("🏗️ Beam Reaction Capacity ($V_{max}$) Analyzer")
st.markdown("""
โปรแกรมคำนวณหาค่า **Max Shear Force ($V_{max}$)** ที่จุดรองรับ (Reaction) โดยพิจารณา 3 เงื่อนไขวิบัติ เพื่อนำค่านี้ไปออกแบบจุดต่อ (Connection Design)
""")

# ==========================================
# 3. SIDEBAR INPUTS
# ==========================================
with st.sidebar:
    st.header("⚙️ Design Parameters")
    
    # 3.1 Material
    st.subheader("Material Properties")
    Fy = st.number_input("Yield Strength ($F_y$) [ksc]", value=2400)
    E_mod = st.number_input("Elastic Modulus ($E$) [ksc]", value=2040000)
    
    # 3.2 Section Selection
    st.subheader("Section Selection")
    df_sys = load_sys_data()
    sec_name = st.selectbox("Select SYS H-Beam", df_sys["Section"], index=5)
    
    # Get Section Properties
    prop = df_sys[df_sys["Section"] == sec_name].iloc[0]
    h, b, tw, tf = prop['h'], prop['b'], prop['tw'], prop['tf']
    Ix, Zx = prop['Ix'], prop['Zx']
    
    st.info(f"""
    **Properties:**
    * $h = {h}$ mm, $t_w = {tw}$ mm
    * $I_x = {Ix:,}$ cm⁴
    * $Z_x = {Zx:,}$ cm³
    """)

# ==========================================
# 4. CALCULATION LOGIC (VECTORIZED)
# ==========================================
# Generate Spans from 0.1 to 15.0 meters
L_m = np.linspace(0.1, 15.0, 200) 
L_cm = L_m * 100

# CASE 1: Web Shear Capacity (Constant)
# V_n = 0.6 * Fy * Aw (Aw = h * tw)
Aw = (h/10) * (tw/10) # cm2
V_case1_shear = np.full_like(L_m, 0.6 * Fy * Aw) # Constant value across length

# CASE 2: Bending Moment Control
# M_cap = 0.6 * Fy * Zx (Using Allowable Stress Design assumption for simplicity)
# Concept: M_max = VL/4 (derived from wL^2/8 where V=wL/2)
# Therefore: V = 4 * M_cap / L
M_cap = 0.6 * Fy * Zx # kg.cm
V_case2_moment = (4 * M_cap) / L_cm # kg

# CASE 3: Deflection Control (L/240)
# Delta_allow = L/240
# Formula: Delta = (5 w L^4) / (384 E I)
# Substitute w = 2V/L -> Delta = (5 (2V/L) L^4) / (384 E I) = (10 V L^3) / (384 E I)
# V = (Delta_allow * 384 * E * I) / (10 * L^3)
# V = ( (L/240) * 384 * E * I ) / (10 * L^3)
# V = (384 * E * I) / (2400 * L^2)
V_case3_defl = (384 * E_mod * Ix) / (2400 * (L_cm**2)) # kg

# Governing V (The lowest of 3 cases)
V_governing = np.minimum(np.minimum(V_case1_shear, V_case2_moment), V_case3_defl)

# ==========================================
# 5. MAIN DISPLAY & INTERACTION
# ==========================================
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader(f"📊 Capacity Envelope for {sec_name}")
    
    # PLOTLY GRAPH
    fig = go.Figure()

    # Plot Lines
    fig.add_trace(go.Scatter(x=L_m, y=V_case1_shear/1000, mode='lines', 
                             name='Case 3: Web Shear (Constant)', 
                             line=dict(color='green', width=2, dash='dash')))
    
    fig.add_trace(go.Scatter(x=L_m, y=V_case2_moment/1000, mode='lines', 
                             name='Case 1: Bending Limit', 
                             line=dict(color='orange', width=2, dash='dash')))
    
    fig.add_trace(go.Scatter(x=L_m, y=V_case3_defl/1000, mode='lines', 
                             name='Case 2: Deflection (L/240)', 
                             line=dict(color='red', width=2, dash='dash')))

    # Plot Safe Zone (Governing)
    fig.add_trace(go.Scatter(x=L_m, y=V_governing/1000, mode='lines', 
                             name='GOVERNING Vmax (Design)', 
                             fill='tozeroy', 
                             line=dict(color='#2E86C1', width=4)))

    fig.update_layout(
        xaxis_title="Span Length (m)",
        yaxis_title="Max End Reaction V (Ton)",
        legend=dict(orientation="h", y=1.1),
        hovermode="x unified",
        height=500,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("🔍 Check Specific Span")
    
    target_span = st.slider("Select Span (m)", 0.1, 15.0, 6.0, 0.1)
    L_target_cm = target_span * 100
    
    # Calculate scalar values for selected span
    v1 = 0.6 * Fy * Aw
    v2 = (4 * M_cap) / L_target_cm
    v3 = (384 * E_mod * Ix) / (2400 * (L_target_cm**2))
    v_final = min(v1, v2, v3)
    
    # Determine Governor
    if v_final == v1: gov = "Web Shear Strength"
    elif v_final == v2: gov = "Bending Moment"
    else: gov = "Deflection (L/240)"
    
    st.markdown(f"""
    <div style="background-color:#f4f6f7; padding:15px; border-radius:10px; border-left:5px solid #2e86c1;">
        <h3 style="margin:0; color:#2e86c1;">Vmax = {v_final/1000:,.2f} Tons</h3>
        <p style="margin:0;">Controlled by: <b>{gov}</b></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("**Detailed Breakdown:**")
    
    st.markdown("**1. Bending Control ($V_{bend}$)**")
    st.latex(r"V = \frac{4 \cdot 0.6 F_y Z_x}{L}")
    st.write(f"= {v2:,.0f} kg")
    
    st.markdown("**2. Deflection Control ($V_{defl}$)**")
    st.latex(r"V = \frac{384 E I}{2400 L^2}")
    st.write(f"= {v3:,.0f} kg")
    
    st.markdown("**3. Web Shear Strength ($V_n$)**")
    st.latex(r"V_n = 0.6 F_y A_w")
    st.write(f"= {v1:,.0f} kg")

# ==========================================
# 6. EXPLANATION SECTION
# ==========================================
st.markdown("---")
with st.expander("📚 Theory & Derivation (ที่มาของสูตร)", expanded=True):
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("#### Case 1: Bending Moment")
        st.write("คานช่วงเดียวรับ Uniform Load ($w$)")
        st.latex(r"M_{max} = \frac{w L^2}{8}, \quad V_{end} = \frac{w L}{2}")
        st.write("จัดรูปสมการหาความสัมพันธ์ $V$ กับ $M$:")
        st.latex(r"M_{max} = \frac{V L}{4} \rightarrow V_{max} = \frac{4 M_{allow}}{L}")
        
    with c2:
        st.markdown("#### Case 2: Deflection (L/240)")
        st.write("สูตรระยะแอ่นตัวสูงสุด:")
        st.latex(r"\Delta = \frac{5 w L^4}{384 E I} = \frac{L}{240}")
        st.write("แทนค่า $w = 2V/L$ ลงไป:")
        st.latex(r"V_{max} = \frac{384 E I}{2400 L^2}")
        st.caption("ถ้า L เพิ่มขึ้น 2 เท่า, รับแรงได้ลดลง 4 เท่า")
        
    with c3:
        st.markdown("#### Case 3: Web Shear")
        st.write("ความสามารถในการรับแรงเฉือนของหน้าตัดโดยตรง (Shear Yielding):")
        st.latex(r"V_n = 0.6 F_y A_w")
        st.write("โดยที่ $A_w = d \times t_w$")
        st.caption("เป็นค่าคงที่ ไม่ขึ้นกับความยาวคาน (Constant)")

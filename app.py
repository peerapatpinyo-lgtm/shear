import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. PROFESSIONAL UI STYLE
# ==========================================
st.set_page_config(page_title="ProStructure: Insight & Report", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    /* Main Layout */
    .main-header {
        font-family: 'Helvetica Neue', sans-serif;
        color: #154360;
        border-left: 6px solid #d35400;
        padding-left: 15px;
        margin-bottom: 20px;
    }
    .card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
        margin-bottom: 15px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #2c3e50;
    }
    .metric-label {
        font-size: 14px;
        color: #7f8c8d;
    }
    /* Status Badges */
    .status-optimal { background-color: #d4efdf; color: #1e8449; padding: 4px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; }
    .status-warn { background-color: #fcf3cf; color: #b7950b; padding: 4px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; }
    .status-crit { background-color: #fadbd8; color: #943126; padding: 4px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; }
    
    /* Progress Bar Custom */
    .stProgress > div > div > div > div {
        background-color: #2980b9;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA & LOGIC ENGINE
# ==========================================
def get_sys_data():
    data = [
        ("H 100x50x5x7", 100, 50, 5, 7, 378, 76.5),
        ("H 150x75x5x7", 150, 75, 5, 7, 666, 88.8),
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
    return pd.DataFrame(data, columns=["Section", "h", "b", "tw", "tf", "Ix", "Zx"])

# --- SIDEBAR INPUTS ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=50)
    st.markdown("### ⚙️ Engineer Control")
    
    df = get_sys_data()
    sec_name = st.selectbox("Select Section", df['Section'], index=6)
    
    st.markdown("---")
    st.caption("Material (ksc)")
    col_mat1, col_mat2 = st.columns(2)
    Fy = col_mat1.number_input("Fy", value=2400, label_visibility="collapsed")
    Fu = col_mat2.number_input("Fu", value=4000, label_visibility="collapsed")
    E_val = 2.04e6
    
    # Props extraction
    p = df[df['Section'] == sec_name].iloc[0]
    h, tw, tf, Ix, Zx = p['h'], p['tw'], p['tf'], p['Ix'], p['Zx']
    
    st.info(f"Depth (d): {h} mm\nWeight: Check Table")

# --- MAIN CALCULATION LOGIC ---
st.markdown(f"<h1 class='main-header'>Structural Capacity Insight: {sec_name}</h1>", unsafe_allow_html=True)

# 1. Define Span & Calculate Limits
col_slider, col_opt = st.columns([2, 1])
with col_slider:
    span = st.slider("Select Span Length (m)", 1.0, 25.0, 6.0, 0.5)

# 2. Optimal Span Logic (L/d Ratio)
d_m = h / 1000
ratio_L_d = span / d_m
opt_min, opt_max = 15, 20
range_min, range_max = opt_min * d_m, opt_max * d_m

# Determine Status
if ratio_L_d < 15:
    span_status = "Deep / Short Span"
    span_color = "status-warn"
    span_desc = "คานลึกเกินไปสำหรับช่วงนี้ (Shear อาจจะคุม แต่น้ำหนักมากเกินจำเป็น)"
elif 15 <= ratio_L_d <= 20:
    span_status = "✨ Optimal Span"
    span_color = "status-optimal"
    span_desc = "ช่วงความยาวเหมาะสม (สมดุลระหว่าง Strength และ Stiffness)"
else:
    span_status = "Slender / Long Span"
    span_color = "status-crit"
    span_desc = "คานชะลูดเกินไป (Deflection จะเป็นตัวควบคุมหลัก)"

with col_opt:
    st.markdown(f"""
    <div class='card' style='text-align:center; padding:10px;'>
        <div style='font-size:12px; color:#7f8c8d;'>Current L/d Ratio</div>
        <div style='font-size:24px; font-weight:bold;'>{ratio_L_d:.1f}</div>
        <span class='{span_color}'>{span_status}</span>
    </div>
    """, unsafe_allow_html=True)

# 3. Reverse Calculate Capacity
L_cm = span * 100
Aw = (h/10)*(tw/10)

# Limit 1: Shear
V_shear = 0.6 * Fy * Aw

# Limit 2: Moment
M_all = 0.6 * Fy * Zx
V_moment = (4 * M_all) / L_cm

# Limit 3: Deflection
V_defl = (384 * E_val * Ix) / (2400 * (L_cm**2))

# Governing
V_design = min(V_shear, V_moment, V_defl)
if V_design == V_shear: gov_mode = "Shear"
elif V_design == V_moment: gov_mode = "Moment"
else: gov_mode = "Deflection"

w_equivalent = (2 * V_design) / span

# ==========================================
# 3. INSIGHT DASHBOARD
# ==========================================
col_d1, col_d2 = st.columns([1, 1.5])

with col_d1:
    st.markdown("### 📊 Capacity Breakdown")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    
    # Logic to show % used relative to the Governing Load
    # หมายความว่า ถ้าเราใส่ Load เท่ากับ V_design ตัวที่คุมจะ = 100% ตัวอื่นจะ < 100%
    per_shear = (V_design / V_shear) * 100
    per_moment = (V_design / V_moment) * 100
    per_defl = (V_design / V_defl) * 100
    
    st.write(f"**1. Shear Limit:** {V_shear:,.0f} kg")
    st.progress(per_shear/100)
    st.caption(f"Utilization: {per_shear:.1f}%")
    
    st.write(f"**2. Moment Limit:** {V_moment:,.0f} kg")
    st.progress(per_moment/100)
    st.caption(f"Utilization: {per_moment:.1f}%")
    
    st.write(f"**3. Deflection Limit:** {V_defl:,.0f} kg")
    st.progress(per_defl/100)
    st.caption(f"Utilization: {per_defl:.1f}%")
    
    st.markdown("---")
    st.markdown(f"**Governing Mode:** <span style='color:#d35400; font-weight:bold'>{gov_mode}</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_d2:
    st.markdown("### 🧠 Smart Analysis: Why this Span?")
    st.markdown(f"""
    <div class='card'>
        <p><b>ช่วงความยาวแนะนำ (Economical Range):</b> {range_min:.2f} - {range_max:.2f} m</p>
        <p style='font-size:14px;'>
        วิศวกรโครงสร้างใช้กฎ <b>Rule of Thumb (L/d = 15-20)</b> ในการเลือกหน้าตัดเบื้องต้น:
        </p>
        <ul>
            <li><b>ถ้า Span < {range_min:.2f} m:</b> หน้าตัดจะใหญ่เกินความจำเป็น (Waste) เพราะแรงเฉือนรับได้สบาย แต่ไม่ได้ใช้ศักยภาพการดัดเต็มที่</li>
            <li><b>ถ้า Span > {range_max:.2f} m:</b> หน้าตัดจะเริ่ม "ตกท้องช้าง" (Deflection) เป็นตัวคุม ทำให้ต้องเผื่อขนาดเหล็กใหญ่ขึ้นมากเพื่อแก้เรื่องการแอ่นตัว ทั้งที่รับแรงได้อยู่</li>
        </ul>
        <div style='background-color:#eaf2f8; padding:10px; border-radius:5px; border-left:4px solid #2980b9;'>
            <b>คำแนะนำสำหรับ {sec_name} @ {span} m:</b><br>
            {span_desc}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. CONNECTION DESIGN (INTERACTIVE)
# ==========================================
st.markdown("---")
st.subheader("🔩 Connection Design & Status")

c1, c2, c3 = st.columns([1, 2, 1])

with c1:
    st.markdown("**Bolt Config**")
    dia = st.selectbox("Diameter", [12, 16, 20, 22, 24], index=2)
    rows = st.number_input("Rows", 2, 8, 3)
    grade = st.selectbox("Grade", ["A325", "A307"])
    
with c2:
    st.markdown("**Plate & Weld**")
    pl_t = st.selectbox("Plate T (mm)", [6, 9, 10, 12, 16], index=1)
    w_sz = st.selectbox("Weld (mm)", [4, 6, 8], index=1)
    
    # Calc Logic
    db = dia/10; Ab = math.pi*(db/2)**2
    Fv = 3720 if grade == "A325" else 1900
    
    # 1. Bolt Shear
    Rn_bolt = rows * Ab * Fv
    # 2. Bearing (Simplified min)
    Rn_bear = rows * 1.2 * Fu * db * min(tw/10, pl_t/10)
    # 3. Weld
    # Assume 2 lines of weld length 1.5d + (n-1)3d + 1.5d approx plate height
    L_weld = (1.5*dia + (rows-1)*3*dia + 1.5*dia)/10
    Rn_weld = 2 * L_weld * 0.707 * (w_sz/10) * (0.3 * 4900)
    
    min_conn = min(Rn_bolt, Rn_bear, Rn_weld)
    conn_ratio = (V_design / min_conn) * 100
    
    # Display Result as Bar
    st.write(f"**Load ($V_u$):** {V_design:,.0f} kg vs **Capacity:** {min_conn:,.0f} kg")
    
    bar_color = "red" if conn_ratio > 100 else ("orange" if conn_ratio > 80 else "green")
    st.markdown(f"""
    <div style="width:100%; background-color:#e0e0e0; border-radius:10px;">
        <div style="width:{min(conn_ratio, 100)}%; background-color:{bar_color}; height:20px; border-radius:10px; text-align:right; padding-right:5px; color:white; font-size:12px; font-weight:bold;">
            {conn_ratio:.1f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    if conn_ratio <= 100:
        st.success("✅ PASS")
    else:
        st.error("❌ FAIL")
    st.caption("Controlling: " + ("Bolt Shear" if min_conn == Rn_bolt else ("Bearing" if min_conn == Rn_bear else "Weld")))

# ==========================================
# 5. DETAILED REPORT (Expandable)
# ==========================================
with st.expander("📄 Click to View Detailed Calculation Sheet (รายการคำนวณละเอียด)"):
    col_sheet_l, col_sheet_r = st.columns(2)
    
    with col_sheet_l:
        st.markdown("**1. Beam Limits Analysis**")
        st.latex(rf"V_{{shear}} = 0.6 F_y A_w = {V_shear:,.0f} \ kg")
        st.latex(rf"V_{{moment}} = \frac{{4 M_{{all}}}}{{L}} = {V_moment:,.0f} \ kg")
        st.latex(rf"V_{{defl}} = \frac{{384 E I}}{{2400 L^2}} = {V_defl:,.0f} \ kg")
        st.markdown(f"**Governing Load:** {V_design:,.0f} kg")
        st.markdown("")
        
    with col_sheet_r:
        st.markdown("**2. Connection Limits**")
        st.latex(rf"\phi R_{{bolt}} = {Rn_bolt:,.0f} \ kg \ ({(V_design/Rn_bolt)*100:.1f}\%)")
        st.latex(rf"\phi R_{{bearing}} = {Rn_bear:,.0f} \ kg \ ({(V_design/Rn_bear)*100:.1f}\%)")
        st.latex(rf"\phi R_{{weld}} = {Rn_weld:,.0f} \ kg \ ({(V_design/Rn_weld)*100:.1f}\%)")
        st.markdown("")

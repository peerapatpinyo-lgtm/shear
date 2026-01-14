import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. STYLE CONFIGURATION
# ==========================================
st.set_page_config(page_title="ProStructure: Ultimate Report", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    /* Paper Style for Calculation Sheet */
    .calc-sheet {
        background-color: #ffffff;
        padding: 30px;
        border: 1px solid #dcdcdc;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-radius: 5px;
        font-family: 'Sarabun', sans-serif;
        margin-bottom: 20px;
    }
    .topic-header {
        color: #154360;
        border-bottom: 2px solid #154360;
        padding-bottom: 5px;
        margin-bottom: 15px;
        font-weight: bold;
        font-size: 20px;
    }
    .sub-header {
        color: #2980b9;
        font-weight: bold;
        margin-top: 15px;
        font-size: 16px;
    }
    .highlight-box {
        background-color: #eaf2f8;
        padding: 15px;
        border-left: 5px solid #2980b9;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. INPUT DATA
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

with st.sidebar:
    st.header("⚙️ Project Parameters")
    df = get_sys_data()
    sec_name = st.selectbox("Select Section", df['Section'], index=6)
    
    st.subheader("Material (ksc)")
    Fy = st.number_input("Yield (Fy)", value=2400)
    Fu = st.number_input("Ultimate (Fu)", value=4000)
    E_val = 2.04e6
    
    st.subheader("Geometry")
    span = st.slider("Span Length (m)", 1.0, 25.0, 6.0, 0.5)

    # Props
    p = df[df['Section'] == sec_name].iloc[0]
    h, tw, tf, Ix, Zx = p['h'], p['tw'], p['tf'], p['Ix'], p['Zx']

# ==========================================
# 3. CALCULATION CORE
# ==========================================
L_cm = span * 100
d_m = h / 1000
ratio_L_d = span / d_m

# 1. Shear
Aw = (h/10) * (tw/10)
V_shear = 0.6 * Fy * Aw

# 2. Moment
M_allow = 0.6 * Fy * Zx
V_moment = (4 * M_allow) / L_cm

# 3. Deflection
V_defl = (384 * E_val * Ix) / (2400 * (L_cm**2))

# Governing
V_design = min(V_shear, V_moment, V_defl)
if V_design == V_shear: gov = "Shear (แรงเฉือนคุม)"
elif V_design == V_moment: gov = "Moment (โมเมนต์คุม)"
else: gov = "Deflection (ระยะแอ่นคุม)"

# ==========================================
# 4. DASHBOARD & GRAPH
# ==========================================
st.title(f"🏗️ Design Analysis: {sec_name}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Max Reaction (V)", f"{V_design:,.0f} kg")
c2.metric("Span Length", f"{span} m")
c3.metric("L/d Ratio", f"{ratio_L_d:.1f}", delta="Optimal: 15-20" if 15<=ratio_L_d<=20 else "Check Span")
c4.metric("Governing Mode", gov)

col_graph, col_insight = st.columns([2, 1])

with col_graph:
    st.subheader("📈 Load Capacity Envelope (กราฟแสดงการรับแรง)")
    L_vals = np.linspace(1, 25, 100)
    L_cm_vals = L_vals * 100
    
    v1 = np.full_like(L_vals, V_shear)
    v2 = (4 * M_allow) / L_cm_vals
    v3 = (384 * E_val * Ix) / (2400 * (L_cm_vals**2))
    v_min = np.minimum(np.minimum(v1, v2), v3)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=L_vals, y=v1, name='Shear Limit', line=dict(dash='dot', color='green')))
    fig.add_trace(go.Scatter(x=L_vals, y=v2, name='Moment Limit', line=dict(dash='dot', color='orange')))
    fig.add_trace(go.Scatter(x=L_vals, y=v3, name='Deflection Limit', line=dict(dash='dot', color='red')))
    fig.add_trace(go.Scatter(x=L_vals, y=v_min, name='Design Capacity', fill='tozeroy', line=dict(color='#154360', width=3)))
    
    fig.add_trace(go.Scatter(x=[span], y=[V_design], mode='markers', marker=dict(size=12, color='red'), name='Current Selection'))
    fig.update_layout(height=400, hovermode="x unified", xaxis_title="Span (m)", yaxis_title="Max Load (kg)", margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig, use_container_width=True)

with col_insight:
    st.subheader("📊 % Utilization")
    
    p_shear = V_design / V_shear
    p_moment = V_design / V_moment
    p_defl = V_design / V_defl
    
    st.write(f"**Shear:** {(p_shear*100):.1f}%")
    st.progress(min(p_shear, 1.0))
    
    st.write(f"**Moment:** {(p_moment*100):.1f}%")
    st.progress(min(p_moment, 1.0))
    
    st.write(f"**Deflection:** {(p_defl*100):.1f}%")
    st.progress(min(p_defl, 1.0))
    
    if ratio_L_d > 20:
        st.warning("⚠️ **Slender:** คานยาวเกินไป Deflection คุม")
    elif ratio_L_d < 15:
        st.info("ℹ️ **Deep:** คานสั้น Shear รับได้สบาย")
    else:
        st.success("✅ **Optimal:** ช่วงความยาวเหมาะสม")

# ==========================================
# 5. DETAILED CALCULATION REPORT
# ==========================================
st.markdown("---")
tab1, tab2 = st.tabs(["📄 1. Detailed Calculation Sheet", "🔩 2. Connection Design"])

with tab1:
    st.markdown('<div class="calc-sheet">', unsafe_allow_html=True)
    st.markdown('<div class="topic-header">CALCULATION REPORT: BEAM CAPACITY</div>', unsafe_allow_html=True)
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**1. Properties**")
        st.write(f"Section: {sec_name}")
        st.latex(rf"d={h}mm, t_w={tw}mm, I_x={Ix:,}cm^4, Z_x={Zx:,}cm^3")
        st.markdown("")

    with col_r:
         st.markdown(f"**Governing Load: {V_design:,.0f} kg**")
         st.caption(f"Controlled by: {gov}")
    
    st.markdown("---")
    
    st.markdown('<div class="sub-header">2. Shear Capacity (แรงเฉือน)</div>', unsafe_allow_html=True)
    st.latex(rf"A_w = {h/10} \times {tw/10} = {Aw:.2f} \ cm^2")
    st.latex(rf"V_{{shear}} = 0.6 \times {Fy} \times {Aw:.2f} = \mathbf{{{V_shear:,.0f}}} \ kg")
    
    st.markdown('<div class="sub-header">3. Moment Capacity (โมเมนต์ดัด)</div>', unsafe_allow_html=True)
    st.latex(rf"M_{{all}} = 0.6 \times {Fy} \times {Zx} = {M_allow:,.0f} \ kg \cdot cm")
    st.latex(rf"V_{{moment}} = \frac{{4 \times {M_allow:,.0f}}}{{{L_cm}}} = \mathbf{{{V_moment:,.0f}}} \ kg")
    st.markdown("

[Image of bending moment diagram simply supported beam]
")
    
    st.markdown('<div class="sub-header">4. Deflection Limit (ระยะแอ่นตัว)</div>', unsafe_allow_html=True)
    st.latex(rf"V_{{defl}} = \frac{{384 \times {E_val:.0f} \times {Ix}}}{{2400 \times {L_cm}^2}} = \mathbf{{{V_defl:,.0f}}} \ kg")
    
    st.markdown('<div class="highlight-box">', unsafe_allow_html=True)
    st.markdown(f"**CONCLUSION:** Limited by **{gov}**")
    st.markdown(f"**Max Reaction = {V_design:,.0f} kg**")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 6. CONNECTION DESIGN
# ==========================================
with tab2:
    st.markdown('<div class="calc-sheet">', unsafe_allow_html=True)
    st.markdown('<div class="topic-header">CONNECTION DESIGN: SHEAR TAB</div>', unsafe_allow_html=True)
    
    c_in, c_cal = st.columns([1, 2])
    
    with c_in:
        st.info(f"**Load ($V_u$):** {V_design:,.0f} kg")
        dia = st.selectbox("Bolt Dia (mm)", [12, 16, 20, 22, 24], index=2)
        rows = st.number_input("Rows (n)", 2, 8, 3)
        tp = st.selectbox("Plate Thick (mm)", [6, 9, 12, 16], index=1)
        weld = st.selectbox("Weld Size (mm)", [4, 6, 8], index=1)
    
    with c_cal:
        db = dia/10
        Ab = math.pi*(db/2)**2
        Fv = 3720 
        
        Rn_bolt = rows * Ab * Fv
        Rn_bear = min(rows*1.2*Fu*db*(tw/10), rows*1.2*Fu*db*(tp/10))
        L_w = (1.5*dia + (rows-1)*3*dia + 1.5*dia)/10
        Rn_weld = 2 * L_w * 0.707 * (weld/10) * (0.3*4900)
        
        min_conn = min(Rn_bolt, Rn_bear, Rn_weld)
        status = "PASSED" if min_conn >= V_design else "FAILED"
        color = "green" if status == "PASSED" else "red"
        
        # FIX: ใช้ Triple Quotes (""") เพื่อรองรับ HTML หลายบรรทัด
        st.markdown(f"""
        ### Status: <span style='color:{color}'>{status}</span>
        """, unsafe_allow_html=True)
        
        st.write(f"**Capacity: {min_conn:,.0f} kg** (Ratio: {V_design/min_conn:.2f})")
        
        st.markdown("**Calculation Breakdown:**")
        st.latex(rf"1. \ Bolt \ Shear: {rows} \times {Ab:.2f} \times {Fv} = {Rn_bolt:,.0f} \ kg")
        st.markdown("")
        st.latex(rf"2. \ Bearing: min(Web, Plt) = {Rn_bear:,.0f} \ kg")
        st.latex(rf"3. \ Weld: 2 \times {L_w:.1f} \times 0.707 \times {weld/10} \times 1470 = {Rn_weld:,.0f} \ kg")
        
    st.markdown('</div>', unsafe_allow_html=True)

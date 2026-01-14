import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & CONFIG
# ==========================================
st.set_page_config(page_title="ProStructure: Ultimate Report", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .calc-sheet {
        background-color: #ffffff;
        padding: 25px;
        border: 1px solid #dcdcdc;
        border-radius: 5px;
        font-family: sans-serif;
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
    .result-box {
        padding: 15px;
        border-radius: 5px;
        margin-top: 10px;
        border: 1px solid #ccc;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA & INPUTS
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

    p = df[df['Section'] == sec_name].iloc[0]
    h, tw, tf, Ix, Zx = p['h'], p['tw'], p['tf'], p['Ix'], p['Zx']

# ==========================================
# 3. CALCULATION
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

# Design Control
V_design = min(V_shear, V_moment, V_defl)
if V_design == V_shear: gov = "Shear"
elif V_design == V_moment: gov = "Moment"
else: gov = "Deflection"

# ==========================================
# 4. DASHBOARD
# ==========================================
st.title(f"🏗️ Design Analysis: {sec_name}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Max Reaction", f"{V_design:,.0f} kg")
c2.metric("Span", f"{span} m")
c3.metric("L/d Ratio", f"{ratio_L_d:.1f}")
c4.metric("Governing", gov)

col_graph, col_insight = st.columns([2, 1])

with col_graph:
    st.subheader("📈 Capacity Envelope")
    L_vals = np.linspace(1, 25, 100)
    L_cm_vals = L_vals * 100
    
    v1 = np.full_like(L_vals, V_shear)
    v2 = (4 * M_allow) / L_cm_vals
    v3 = (384 * E_val * Ix) / (2400 * (L_cm_vals**2))
    v_min = np.minimum(np.minimum(v1, v2), v3)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=L_vals, y=v1, name='Shear', line=dict(dash='dot', color='green')))
    fig.add_trace(go.Scatter(x=L_vals, y=v2, name='Moment', line=dict(dash='dot', color='orange')))
    fig.add_trace(go.Scatter(x=L_vals, y=v3, name='Deflection', line=dict(dash='dot', color='red')))
    fig.add_trace(go.Scatter(x=L_vals, y=v_min, name='Capacity', fill='tozeroy', line=dict(color='#154360', width=3)))
    fig.add_trace(go.Scatter(x=[span], y=[V_design], mode='markers', marker=dict(size=12, color='red'), name='Selected'))
    
    fig.update_layout(height=400, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig, use_container_width=True)

with col_insight:
    st.subheader("📊 Utilization")
    st.write(f"Shear: {(V_design/V_shear*100):.1f}%")
    st.progress(min(V_design/V_shear, 1.0))
    st.write(f"Moment: {(V_design/V_moment*100):.1f}%")
    st.progress(min(V_design/V_moment, 1.0))

# ==========================================
# 5. DETAILED REPORT
# ==========================================
st.markdown("---")
tab1, tab2 = st.tabs(["📄 Calculation", "🔩 Connection"])

with tab1:
    st.markdown("""<div class="calc-sheet">""", unsafe_allow_html=True)
    st.markdown("""<div class="topic-header">CALCULATION REPORT</div>""", unsafe_allow_html=True)
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**Properties:**")
        st.write(f"Section: {sec_name}")
        st.latex(rf"d={h}, t_w={tw}, I_x={Ix:,}, Z_x={Zx:,}")
        st.caption("Standard Section Properties")

    with col_r:
         st.markdown(f"**Limit State: {gov}**")
         st.markdown(f"**Capacity: {V_design:,.0f} kg**")
    
    st.markdown("---")
    
    st.markdown("**1. Shear Capacity:**")
    st.latex(rf"V_{{n}} = 0.6 F_y A_w = \mathbf{{{V_shear:,.0f}}} \ kg")
    
    st.markdown("**2. Moment Capacity:**")
    st.latex(rf"M_{{n}} = 0.6 F_y Z_x = {M_allow:,.0f} \ kg \cdot cm")
    st.latex(rf"V_{{moment}} = \frac{{4 M}}{{L}} = \mathbf{{{V_moment:,.0f}}} \ kg")
    st.write("*(Ref: Simply Supported Beam Diagram)*")
    
    st.markdown("**3. Deflection Limit:**")
    st.latex(rf"V_{{defl}} = \frac{{384 E I}}{{2400 L^2}} = \mathbf{{{V_defl:,.0f}}} \ kg")
    
    st.markdown("""</div>""", unsafe_allow_html=True)

# ==========================================
# 6. CONNECTION DESIGN (FIXED)
# ==========================================
with tab2:
    st.markdown("""<div class="calc-sheet">""", unsafe_allow_html=True)
    st.markdown("""<div class="topic-header">CONNECTION CHECK</div>""", unsafe_allow_html=True)
    
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
        passed = min_conn >= V_design
        
        # --- SAFE STRING CONSTRUCTION ---
        status_text = "PASSED" if passed else "FAILED"
        color = "#155724" if passed else "#721c24"
        bg_color = "#d4edda" if passed else "#f8d7da"
        
        st.markdown(f"""
        <div class="result-box" style="background-color: {bg_color}; color: {color};">
            <h3 style="margin:0;">Status: {status_text}</h3>
            <p>Capacity: <b>{min_conn:,.0f} kg</b> (Ratio: {V_design/min_conn:.2f})</p>
        </div>
        """, unsafe_allow_html=True)
        # --------------------------------
        
        st.markdown("**Checklist:**")
        st.latex(rf"1. \ Bolt \ Shear: {Rn_bolt:,.0f} \ kg")
        st.caption("*(Check: Single Shear Plane)*") 
        
        st.latex(rf"2. \ Bearing: {Rn_bear:,.0f} \ kg")
        st.latex(rf"3. \ Weld: {Rn_weld:,.0f} \ kg")
        
    st.markdown("""</div>""", unsafe_allow_html=True)

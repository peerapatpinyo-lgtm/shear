import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. PAGE SETUP & STYLE
# ==========================================
st.set_page_config(page_title="SYS Beam & Connection Master", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .main-header { font-size: 20px; font-weight: bold; color: #1a5276; margin-bottom: 10px; border-bottom: 2px solid #a9cce3; padding-bottom: 5px; }
    .optimal-box { background-color: #d4efdf; border-left: 5px solid #27ae60; padding: 15px; border-radius: 5px; margin-bottom: 15px; }
    .status-pass { background-color: #e8f8f5; color: #1e8449; padding: 10px; border-radius: 5px; font-weight: bold; border: 1px solid #2ecc71; }
    .status-fail { background-color: #fdedec; color: #c0392b; padding: 10px; border-radius: 5px; font-weight: bold; border: 1px solid #e74c3c; }
    .calc-box { background-color: #f8f9f9; padding: 15px; border-radius: 5px; border: 1px solid #e5e8e8; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SYS DATABASE & INPUTS
# ==========================================
def get_sys_data():
    # ตัวอย่างข้อมูล (ใช้งานจริงสามารถเพิ่มได้ครบทุก size)
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
    st.title("⚙️ Design Parameters")
    
    st.markdown("### 1. Material Properties")
    Fy = st.number_input("Yield Strength (Fy) [ksc]", value=2400)
    Fu = st.number_input("Ultimate Strength (Fu) [ksc]", value=4000)
    E = st.number_input("Elastic Modulus (E) [ksc]", value=2040000)
    
    st.markdown("### 2. Section Selection")
    df = get_sys_data()
    sec_name = st.selectbox("Select H-Beam", df['Section'], index=6) # Default H400
    
    # Get props
    p = df[df['Section'] == sec_name].iloc[0]
    h, tw, tf, Ix, Zx = p['h'], p['tw'], p['tf'], p['Ix'], p['Zx']
    
    st.info(f"""
    **{sec_name}**
    h={h}, tw={tw}, tf={tf} mm
    Ix={Ix:,} cm⁴, Zx={Zx:,} cm³
    """)

# ==========================================
# 3. BEAM CALCULATION LOGIC
# ==========================================
# Constants
h_cm, tw_cm = h/10, tw/10
Aw = h_cm * tw_cm

# Limits
V_allow_web = 0.6 * Fy * Aw # Case 3: Web Shear Capacity (Using 0.6Fy as per AISC Shear Yield)
M_allow = 0.6 * Fy * Zx     # Moment Capacity

# Optimal Span Range (15d - 20d)
d_m = h / 1000
L_opt_min = 15 * d_m
L_opt_max = 20 * d_m

# Generate Data (0.5m to 20m)
L_vals = np.linspace(0.5, 20.0, 200)
L_cm_vals = L_vals * 100

# 1. Web Shear Limit (Constant)
v1_web = np.full_like(L_vals, V_allow_web)

# 2. Bending Moment Limit (V = 4M/L)
v2_moment = (4 * M_allow) / L_cm_vals

# 3. Deflection Limit (L/240) -> V = (384EI)/(2400 L^2)
v3_defl = (384 * E * Ix) / (2400 * (L_cm_vals**2))

# Governing V
v_safe = np.minimum(np.minimum(v1_web, v2_moment), v3_defl)

# ==========================================
# 4. UI: TABS
# ==========================================
st.title("🏗️ SYS Beam & Connection Design Suite")
tab1, tab2 = st.tabs(["📊 1. Beam & Span Analysis", "🔩 2. Connection Design"])

# ==========================================
# TAB 1: BEAM ANALYSIS
# ==========================================
with tab1:
    col_g1, col_g2 = st.columns([3, 1])
    
    with col_g2:
        st.markdown('<div class="main-header">🎯 Optimal Span</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="optimal-box">
            <b>ช่วงความยาวที่เหมาะสม ($L/d \\approx 15-20$)</b><br>
            สำหรับหน้าตัด {sec_name} (d={d_m:.2f} m):
            <h3>{L_opt_min:.1f} - {L_opt_max:.1f} เมตร</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        st.markdown("**เลือก Span ที่จะใช้ออกแบบ:**")
        user_span = st.number_input("Design Span Length (m)", 
                                    min_value=0.5, max_value=20.0, 
                                    value=float((L_opt_min+L_opt_max)/2), step=0.5)
        
        # Calculate Single Point
        L_target = user_span * 100
        val_shear = V_allow_web
        val_moment = (4 * M_allow) / L_target
        val_defl = (384 * E * Ix) / (2400 * (L_target**2))
        
        final_v = min(val_shear, val_moment, val_defl)
        
        # Determine Governor
        if final_v == val_shear: gov = "Web Shear"
        elif final_v == val_moment: gov = "Bending Moment"
        else: gov = "Deflection (L/240)"
        
        st.metric("Max End Reaction (Vmax)", f"{final_v:,.0f} kg")
        st.caption(f"Controlled by: {gov}")
        
    with col_g1:
        st.markdown('<div class="main-header">📈 Vmax Envelope Graph</div>', unsafe_allow_html=True)
        
        fig = go.Figure()
        
        # 3 Cases
        fig.add_trace(go.Scatter(x=L_vals, y=v1_web, name='Case 3: Web Shear', line=dict(color='green', dash='dash')))
        fig.add_trace(go.Scatter(x=L_vals, y=v2_moment, name='Case 1: Bending', line=dict(color='orange', dash='dash')))
        fig.add_trace(go.Scatter(x=L_vals, y=v3_defl, name='Case 2: Deflection', line=dict(color='red', dash='dash')))
        
        # Safe Zone
        fig.add_trace(go.Scatter(x=L_vals, y=v_safe, name='Safe Vmax (Design)', 
                                 fill='tozeroy', line=dict(color='#2E86C1', width=4)))
        
        # Optimal Zone Highlight
        fig.add_vrect(x0=L_opt_min, x1=L_opt_max, fillcolor="green", opacity=0.1, 
                      annotation_text="Optimal Span", annotation_position="top")
        
        # User Point
        fig.add_trace(go.Scatter(x=[user_span], y=[final_v], mode='markers', 
                                 marker=dict(size=12, color='red', symbol='x'), name='Your Design Span'))

        # ZOOM & LAYOUT settings
        fig.update_layout(
            xaxis_title="Span Length (m)",
            yaxis_title="Max End Reaction V (kg)",
            hovermode="x unified",
            height=500,
            xaxis=dict(rangeslider=dict(visible=True)), # Slider ด้านล่างเพื่อซูมแกน X
            dragmode="zoom" # ให้เมาส์เป็นแว่นขยายโดย default
        )
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TAB 2: CONNECTION DESIGN (RESTORED!)
# ==========================================
with tab2:
    st.markdown('<div class="main-header">🔩 Shear Connection Design (Shear Tab)</div>', unsafe_allow_html=True)
    
    col_c1, col_c2 = st.columns([1, 1.5])
    
    with col_c1:
        st.info(f"Design Load ($V_u$) ดึงมาจาก Tab 1: **{final_v:,.0f} kg**")
        vu_input = st.number_input("Design Shear Force (kg)", value=float(final_v), step=100.0)
        
        st.markdown("---")
        st.subheader("1. Bolt & Plate Config")
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            bolt_grade = st.selectbox("Bolt Grade", ["A325", "A307", "A490"])
            d_mm = st.selectbox("Dia (mm)", [12, 16, 20, 22, 24], index=2)
            n_rows = st.number_input("Rows", 2, 10, 3)
        with col_b2:
            t_plate = st.selectbox("Plate Thick (mm)", [6, 9, 12, 16, 20], index=1)
            weld_sz = st.selectbox("Weld Size (mm)", [4, 6, 8, 10], index=1)

        st.subheader("2. Geometry (Auto)")
        # Auto calc standard AISC geometry
        pitch = 3 * d_mm
        lev = 1.5 * d_mm # Vertical Edge
        leh = 40 # Horizontal Edge
        
        st.write(f"Pitch = {pitch} mm")
        st.write(f"Edge V = {lev} mm")
        st.write(f"Edge H = {leh} mm")

    with col_c2:
        # --- CALCULATION CORE ---
        # Props
        db = d_mm/10
        dh = db + 0.2
        tp = t_plate/10
        
        # 1. Bolt Shear
        Fv = 3720 if "A325" in bolt_grade else (1900 if "A307" in bolt_grade else 4760)
        Ab = math.pi * (db/2)**2
        Rn_bolt = n_rows * Ab * Fv
        
        # 2. Bearing (Web & Plate)
        Rn_bear_w = n_rows * (1.2 * Fu * db * tw_cm)
        Rn_bear_p = n_rows * (1.2 * Fu * db * tp)
        
        # 3. Block Shear (Plate)
        # Areas
        L_gv = (lev/10) + (n_rows-1)*(pitch/10)
        L_nv = L_gv - (n_rows-0.5)*dh
        L_nt = (leh/10) - 0.5*dh
        
        Agv = L_gv * tp
        Anv = L_nv * tp
        Ant = L_nt * tp
        
        # Formula: Min(0.6Fu Anv + Ubs Fu Ant, 0.6Fy Agv + Ubs Fu Ant)
        term1 = 0.6 * Fu * Anv + 1.0 * Fu * Ant
        term2 = 0.6 * Fy * Agv + 1.0 * Fu * Ant
        Rn_block = min(term1, term2)
        
        # 4. Plate Yield / Rupture
        Rn_yld = 0.6 * Fy * (L_gv + lev/10) * tp
        Rn_rup = 0.6 * Fu * ((L_gv + lev/10) - n_rows*dh) * tp
        
        # 5. Weld Capacity (Double Fillet)
        # Fw = 0.60 * Fexx (Approx E70xx -> 4900 ksc * 0.3 allowable) -> Simplified logic
        # Allowable force per cm = 0.707 * size * 0.3 * Fu_weld * 2 sides
        L_weld = (L_gv + lev/10)
        Rn_weld = 2 * (0.707 * (weld_sz/10) * 0.3 * 4900) * L_weld 

        # Summary
        checks = {
            "Bolt Shear": Rn_bolt,
            "Bearing (Web)": Rn_bear_w,
            "Bearing (Plate)": Rn_bear_p,
            "Block Shear": Rn_block,
            "Plate Yield": Rn_yld,
            "Plate Rupture": Rn_rup,
            "Weld Strength": Rn_weld
        }
        
        min_cap = min(checks.values())
        status = "PASS" if min_cap >= vu_input else "FAIL"
        
        # --- DISPLAY RESULTS ---
        st.markdown(f"### 📋 Analysis Result")
        
        if status == "PASS":
            st.markdown(f'<div class="status-pass">✅ PASSED (Ratio: {vu_input/min_cap:.2f})</div>', unsafe_allow_html=True)
        else:
            fail_mode = min(checks, key=checks.get)
            st.markdown(f'<div class="status-fail">❌ FAILED (Controlled by {fail_mode})</div>', unsafe_allow_html=True)
            
        st.write("")
        st.markdown("**Detailed Capacity Check (kg):**")
        
        # Bar Charts
        for k, v in checks.items():
            ratio = vu_input / v
            color = "#27ae60" if ratio <= 1.0 else "#c0392b"
            st.write(f"**{k}**: {v:,.0f} kg")
            st.progress(min(ratio, 1.0))
            
        with st.expander("Show Calculation Formula"):
            st.latex(r"R_{bolt} = n \cdot A_b \cdot F_v")
            st.latex(r"R_{block} = \min(0.6F_u A_{nv} + U_{bs}F_u A_{nt}, 0.6F_y A_{gv} + U_{bs}F_u A_{nt})")
            st.latex(r"R_{bearing} = 1.2 F_u d t")

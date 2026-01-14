import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. PAGE SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Ultimate Structural Suite", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .header-box { border-bottom: 2px solid #2980b9; padding-bottom: 10px; margin-bottom: 20px; color: #2980b9; font-size: 20px; font-weight: bold; }
    .ratio-box-good { background-color: #d4efdf; border: 1px solid #27ae60; color: #1e8449; padding: 15px; border-radius: 8px; text-align: center; }
    .ratio-box-warn { background-color: #fcf3cf; border: 1px solid #f1c40f; color: #9a7d0a; padding: 15px; border-radius: 8px; text-align: center; }
    .ratio-box-bad { background-color: #fadbd8; border: 1px solid #e74c3c; color: #943126; padding: 15px; border-radius: 8px; text-align: center; }
    .report-card { background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SYS DATABASE & INPUTS
# ==========================================
def get_sys_data():
    data = [
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
    return pd.DataFrame(data, columns=["Section", "h", "b", "tw", "tf", "Ix", "Zx"])

with st.sidebar:
    st.title("⚙️ Parameter Setup")
    
    st.subheader("1. Material")
    Fy = st.number_input("Yield (Fy) ksc", value=2400)
    Fu = st.number_input("Ultimate (Fu) ksc", value=4000)
    E = st.number_input("E Modulus ksc", value=2040000)
    
    st.subheader("2. Section")
    df = get_sys_data()
    sec_name = st.selectbox("Select H-Beam", df['Section'], index=7) # H400 default
    
    p = df[df['Section'] == sec_name].iloc[0]
    h, tw, tf, Ix, Zx = p['h'], p['tw'], p['tf'], p['Ix'], p['Zx']
    
    st.info(f"""
    **{sec_name}**
    h={h} mm, tw={tw} mm
    Ix={Ix:,} cm⁴, Zx={Zx:,} cm³
    """)

# ==========================================
# 3. BEAM CALCULATION ENGINE
# ==========================================
# Constants
h_cm, tw_cm = h/10, tw/10
Aw = h_cm * tw_cm

# Capacities
V_allow_web = 0.6 * Fy * Aw # Shear Yield
M_allow = 0.6 * Fy * Zx     # Moment (ASD)

# Optimal Span Logic
d_m = h / 1000
opt_min = 15 * d_m
opt_max = 20 * d_m

# Vectorized Calculation for Graph
L_vals = np.linspace(0.5, 18.0, 200) # Span 0.5 - 18m
L_cm = L_vals * 100

v1_shear = np.full_like(L_vals, V_allow_web)          # Case 3: Constant
v2_moment = (4 * M_allow) / L_cm                      # Case 1: Bending Control
v3_defl = (384 * E * Ix) / (2400 * (L_cm**2))         # Case 2: Deflection Control (L/240)
v_capacity = np.minimum(np.minimum(v1_shear, v2_moment), v3_defl) # Envelope

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
st.title("🏗️ Ultimate Structural Design Studio")
st.caption("Integrated Module: Beam Efficiency Check + Detailed Connection Design")

tab_beam, tab_conn = st.tabs(["📊 1. Beam Efficiency & Check", "🔩 2. Connection Detail"])

# ------------------------------------------
# TAB 1: BEAM ANALYSIS & UTILIZATION CHECK
# ------------------------------------------
with tab_beam:
    c_graph, c_check = st.columns([2, 1])
    
    with c_graph:
        st.markdown('<div class="header-box">📈 Capacity Envelope & Optimal Zone</div>', unsafe_allow_html=True)
        
        fig = go.Figure()
        
        # Plot Limits
        fig.add_trace(go.Scatter(x=L_vals, y=v1_shear, name='Shear Limit', line=dict(color='green', dash='dash')))
        fig.add_trace(go.Scatter(x=L_vals, y=v2_moment, name='Moment Limit', line=dict(color='orange', dash='dash')))
        fig.add_trace(go.Scatter(x=L_vals, y=v3_defl, name='Deflection Limit', line=dict(color='red', dash='dash')))
        
        # Plot Envelope
        fig.add_trace(go.Scatter(x=L_vals, y=v_capacity, name='Max Safe V (Capacity)', 
                                 fill='tozeroy', line=dict(color='#2980b9', width=4)))
        
        # Highlight Optimal Zone
        fig.add_vrect(x0=opt_min, x1=opt_max, fillcolor="green", opacity=0.1, 
                      annotation_text="Optimal Span (15-20d)", annotation_position="top right")
        
        fig.update_layout(
            xaxis_title="Span Length (m)",
            yaxis_title="Max End Reaction V (kg)",
            height=500,
            hovermode="x unified",
            xaxis=dict(rangeslider=dict(visible=True)), # ZOOMABLE
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with c_check:
        st.markdown('<div class="header-box">🎯 Efficiency Check</div>', unsafe_allow_html=True)
        
        # 1. Select Span
        user_span = st.number_input("Design Span (m)", 1.0, 18.0, 6.0, step=0.5)
        
        # Calculate Capacity at Span
        L_target = user_span * 100
        cap_shear = V_allow_web
        cap_moment = (4 * M_allow) / L_target
        cap_defl = (384 * E * Ix) / (2400 * (L_target**2))
        max_v_capacity = min(cap_shear, cap_moment, cap_defl)
        
        st.info(f"Max Capacity ($V_{{max}}$) at {user_span}m = **{max_v_capacity:,.0f} kg**")
        
        # 2. Input Actual Load
        st.markdown("---")
        st.write("**Check Utilization Ratio:**")
        actual_w = st.number_input("Your Uniform Load (kg/m)", value=1000.0, step=100.0)
        actual_v = actual_w * user_span / 2
        
        # 3. Calculate Ratio
        ratio = actual_v / max_v_capacity
        pct = ratio * 100
        
        st.write(f"Actual Reaction ($V_{{act}}$) = {actual_v:,.0f} kg")
        
        # 4. Display Result (50-70% Logic)
        if pct > 100:
            st.markdown(f"""
            <div class="ratio-box-bad">
                <h1>{pct:.1f}%</h1>
                <h3>❌ OVERLOADED!</h3>
                หน้าตัดรับไม่ไหว อันตรายครับ
            </div>
            """, unsafe_allow_html=True)
        elif 50 <= pct <= 70:
            st.markdown(f"""
            <div class="ratio-box-good">
                <h1>{pct:.1f}%</h1>
                <h3>✅ PERFECT ZONE</h3>
                คุ้มค่าและปลอดภัย (อยู่ในช่วง 50-70%)
            </div>
            """, unsafe_allow_html=True)
        elif pct < 50:
            st.markdown(f"""
            <div class="ratio-box-warn">
                <h1>{pct:.1f}%</h1>
                <h3>⚠️ WASTEFUL</h3>
                เผื่อเยอะเกินไป (Over Design) เปลืองเหล็ก
            </div>
            """, unsafe_allow_html=True)
        else: # 71 - 99%
             st.markdown(f"""
            <div class="ratio-box-good" style="border-color:#2980b9; color:#2980b9; background-color:#eaf2f8;">
                <h1>{pct:.1f}%</h1>
                <h3>🆗 PASS</h3>
                ผ่าน (ค่อนข้างตึงมือ แต่ยังปลอดภัย)
            </div>
            """, unsafe_allow_html=True)

# ------------------------------------------
# TAB 2: CONNECTION DETAIL (FULL)
# ------------------------------------------
with tab_conn:
    st.markdown('<div class="header-box">🔩 Connection Design Report</div>', unsafe_allow_html=True)
    
    col_in, col_calc = st.columns([1, 1.5])
    
    with col_in:
        st.markdown("**1. Loads**")
        # Link from Tab 1 (Use Max Capacity or Actual Load? usually Design for Capacity to be safe)
        design_v = st.number_input("Design Shear ($V_u$) [kg]", value=float(max_v_capacity))
        st.caption(f"Default is Max Capacity at {user_span}m. You can change it.")
        
        st.markdown("**2. Components**")
        bolt_grade = st.selectbox("Bolt Grade", ["A325", "A307"])
        d_mm = st.selectbox("Bolt Dia (mm)", [12, 16, 20, 22, 24], index=1)
        rows = st.number_input("Rows (n)", 2, 8, 3)
        tp_mm = st.selectbox("Plate Thick (mm)", [6, 9, 12, 16], index=1)
        weld_s = st.selectbox("Weld Size (mm)", [4, 6, 8, 10], index=1)
        
        # Geometry
        s = 3 * d_mm
        lev = 1.5 * d_mm
        leh = 40
        st.markdown(f"**Geometry:** Pitch={s}, Lev={lev}, Leh={leh}")

    with col_calc:
        # Calc logic
        db = d_mm/10
        dh = db + 0.2
        tp = tp_mm/10
        fv = 3720 if "A325" in bolt_grade else 1900
        
        # Areas
        L_gv = (lev/10) + (rows-1)*(s/10)
        L_nv = L_gv - (rows-0.5)*dh
        L_nt = (leh/10) - 0.5*dh
        
        Agv, Anv, Ant = L_gv*tp, L_nv*tp, L_nt*tp
        
        # Capacities
        # 1. Bolt Shear
        Rn_bolt = rows * (math.pi*(db/2)**2) * fv
        
        # 2. Bearing
        Rn_bear = min(rows*(1.2*Fu*db*tw_cm), rows*(1.2*Fu*db*tp))
        
        # 3. Block Shear
        R_bs1 = 0.6*Fy*Agv + 1.0*Fu*Ant
        R_bs2 = 0.6*Fu*Anv + 1.0*Fu*Ant
        Rn_block = min(R_bs1, R_bs2)
        
        # 4. Weld (Simplified E70xx)
        # 0.707 * size * 0.6Fexx(approx 0.3Fu_weld for allowable) * 2 sides
        # Using ASD Allowable unit stress ~ 900-1100 ksc per cm of weld leg? 
        # Let's use AISC: Fn = 0.60Fexx. Omega=2.0 -> Fw = 0.3Fexx. Fexx=4900ksc
        Rn_weld = 2 * (L_gv + lev/10) * 0.707 * (weld_s/10) * (0.3 * 4900)
        
        # Summary
        caps = {
            "Bolt Shear": Rn_bolt, "Bearing": Rn_bear, 
            "Block Shear": Rn_block, "Weld Strength": Rn_weld
        }
        min_cap = min(caps.values())
        passed = min_cap >= design_v

        # --- REPORT CARD ---
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        if passed:
            st.markdown(f'<h3 style="color:#27ae60">✅ PASSED (Cap: {min_cap:,.0f} kg)</h3>', unsafe_allow_html=True)
        else:
            st.markdown(f'<h3 style="color:#c0392b">❌ FAILED (Cap: {min_cap:,.0f} kg)</h3>', unsafe_allow_html=True)
            
        st.table(pd.DataFrame.from_dict(caps, orient='index', columns=['Capacity (kg)']))
        
        st.markdown("**Check Formulas:**")
        
        st.latex(r"R_{block} = \min(0.6F_u A_{nv} + U_{bs}F_u A_{nt}, \ 0.6F_y A_{gv} + U_{bs}F_u A_{nt})")
        st.write(f"Block Shear Values: Agv={Agv:.2f}, Anv={Anv:.2f}, Ant={Ant:.2f} cm²")
        st.markdown('</div>', unsafe_allow_html=True)

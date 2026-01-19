import streamlit as st
import plotly.graph_objects as go
import numpy as np
import math

def render(data):
    """
    Render Tab 3: LTB Insight + Interactive Calculation
    data: Context dictionary from app.py
    """
    # --- 1. UNPACK DATA ---
    Lb_real = data['Lb']
    Lp_cm = data['Lp_cm']
    Lr_cm = data['Lr_cm']
    Mp = data['Mp']
    Fy = data['Fy']
    Sx = data['Sx']
    E = data['E']
    Cb = data['Cb']
    r_ts = data['r_ts']
    val_A = data['val_A']
    user_span = data['user_span']
    is_lrfd = data['is_lrfd']
    
    # Unit Conversion for Display
    Lp_m = Lp_cm / 100
    Lr_m = Lr_cm / 100
    Mp_kgm = Mp / 100
    
    st.subheader("🛡️ LTB Stability Analysis")

    # --- PART 2: SIMULATION & GRAPH ---
    col_sim, col_graph = st.columns([1, 2])
    
    with col_sim:
        st.markdown("#### 🎮 Simulator")
        st.info("ปรับระยะค้ำยัน ($L_b$) เพื่อดูพฤติกรรมและการคำนวณ")
        
        # SLIDER
        lb_sim = st.slider("Simulate Lb (m)", 
                           min_value=0.5, 
                           max_value=float(user_span), 
                           value=float(Lb_real),
                           step=0.1)
        
        # CALCULATE STATE BASED ON SLIDER
        lb_sim_cm = lb_sim * 100
        mn_sim = 0
        zone_sim = ""
        zone_color = ""
        
        if lb_sim_cm <= Lp_cm:
            mn_sim = Mp
            zone_sim = "Zone 1: Plastic"
            zone_color = "#10b981" # Green
        elif lb_sim_cm <= Lr_cm:
            term = (Mp - 0.7 * Fy * Sx) * ((lb_sim_cm - Lp_cm) / (Lr_cm - Lp_cm))
            mn_sim = min(Cb * (Mp - term), Mp)
            zone_sim = "Zone 2: Inelastic"
            zone_color = "#f59e0b" # Orange
        else:
            slend = (lb_sim_cm / r_ts)
            fcr = (Cb * math.pi**2 * E) / (slend**2) * math.sqrt(1 + 0.078 * val_A * slend**2)
            mn_sim = min(fcr * Sx, Mp)
            zone_sim = "Zone 3: Elastic"
            zone_color = "#ef4444" # Red
            
        mn_sim_kgm = mn_sim / 100
        
        # SHOW MINI RESULT CARD
        st.markdown(f"""
        <div style="text-align:center; padding:15px; background:{zone_color}15; border-radius:10px; border:2px solid {zone_color}; margin-top:10px;">
            <div style="font-size:14px; color:{zone_color}; font-weight:bold;">{zone_sim}</div>
            <div style="font-size:32px; font-weight:800; color:#1e293b;">{mn_sim_kgm:,.0f}</div>
            <div style="font-size:14px; color:#64748b;">kg-m (Nominal)</div>
        </div>
        """, unsafe_allow_html=True)

    with col_graph:
        # PLOT GRAPH
        max_len = max(Lr_m * 1.5, user_span)
        x_vals = np.linspace(0.1, max_len, 100)
        y_vals = []
        
        for l in x_vals:
            l_cm = l * 100
            if l_cm <= Lp_cm: m = Mp
            elif l_cm <= Lr_cm:
                term = (Mp - 0.7 * Fy * Sx) * ((l_cm - Lp_cm) / (Lr_cm - Lp_cm))
                m = min(Cb * (Mp - term), Mp)
            else:
                slend = (l_cm / r_ts)
                fcr = (Cb * math.pi**2 * E) / (slend**2) * math.sqrt(1 + 0.078 * val_A * slend**2)
                m = min(fcr * Sx, Mp)
            y_vals.append(m/100)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name='Mn Curve', line=dict(color='#334155', width=3)))
        
        # Simulation Point
        fig.add_trace(go.Scatter(x=[lb_sim], y=[mn_sim_kgm], mode='markers', name='Sim Point', 
                                 marker=dict(size=14, color=zone_color, symbol='diamond', line=dict(width=2, color='white'))))
        
        # Real Design Point (Ghost)
        if abs(lb_sim - Lb_real) > 0.1:
             fig.add_vline(x=Lb_real, line_dash="dot", line_color="gray", annotation_text="Actual Lb")

        # Zones Background
        fig.add_vrect(x0=0, x1=Lp_m, fillcolor="green", opacity=0.1, layer="below", annotation_text="Plastic")
        fig.add_vrect(x0=Lp_m, x1=Lr_m, fillcolor="orange", opacity=0.1, layer="below", annotation_text="Inelastic")
        fig.add_vrect(x0=Lr_m, x1=max_len, fillcolor="red", opacity=0.1, layer="below", annotation_text="Elastic")

        fig.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=300, 
                          xaxis_title="Lb (m)", yaxis_title="Mn (kg-m)", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # --- PART 3: LIVE CALCULATION SHEET ---
    st.divider()
    st.subheader(f"🧮 Live Calculation: {zone_sim}")
    
    with st.expander("แสดงวิธีทำ (Calculation Steps)", expanded=True):
        
        # 3.1 Show Constants
        st.markdown(f"""
        **Parameters:** $L_b = {lb_sim:.2f}$ m | $L_p = {Lp_m:.2f}$ m | $L_r = {Lr_m:.2f}$ m | $C_b = {Cb}$
        """)
        
        # 3.2 Dynamic Formula based on Zone
        if lb_sim_cm <= Lp_cm:
            # ZONE 1
            st.markdown("##### 1. Condition Check")
            st.latex(r"L_b \le L_p \rightarrow " + f"{lb_sim:.2f} \le {Lp_m:.2f} \quad \\text{{(Zone 1: Plastic)}}")
            
            st.markdown("##### 2. Calculation")
            st.write("ในโซนนี้หน้าตัดสามารถรับโมเมนต์ได้เต็มพิกัด ($M_p$)")
            st.latex(r"M_n = M_p = F_y Z_x")
            st.markdown(f"Substituting values: $M_n = {Mp/100:,.0f}$ kg-m")
            
        elif lb_sim_cm <= Lr_cm:
            # ZONE 2
            st.markdown("##### 1. Condition Check")
            st.latex(r"L_p < L_b \le L_r \rightarrow " + f"{Lp_m:.2f} < {lb_sim:.2f} \le {Lr_m:.2f} \quad \\text{{(Zone 2: Inelastic)}}")
            
            st.markdown("##### 2. Calculation")
            st.write("คำนวณโดยการ Interpolate ค่าระหว่าง $M_p$ และ $0.7F_y S_x$")
            st.latex(r"M_n = C_b \left[ M_p - (M_p - 0.7 F_y S_x) \left( \frac{L_b - L_p}{L_r - L_p} \right) \right] \le M_p")
            
            # Show substitution
            mr = 0.7 * Fy * Sx
            ratio = (lb_sim_cm - Lp_cm) / (Lr_cm - Lp_cm)
            st.markdown(f"""
            - $M_p = {Mp:,.0f}$ kg-cm
            - $0.7 F_y S_x = {mr:,.0f}$ kg-cm
            - Fraction Term = $({lb_sim:.2f} - {Lp_m:.2f}) / ({Lr_m:.2f} - {Lp_m:.2f}) = {ratio:.3f}$
            """)
            st.markdown(f"**Result:** $M_n = {mn_sim_kgm:,.0f}$ kg-m")
            
        else:
            # ZONE 3
            st.markdown("##### 1. Condition Check")
            st.latex(r"L_b > L_r \rightarrow " + f"{lb_sim:.2f} > {Lr_m:.2f} \quad \\text{{(Zone 3: Elastic)}}")
            
            st.markdown("##### 2. Calculation")
            st.write("คำนวณโดยใช้ Critical Stress ($F_{cr}$) เนื่องจากเกิด Elastic Buckling")
            st.latex(r"F_{cr} = \frac{C_b \pi^2 E}{(L_b/r_{ts})^2} \sqrt{1 + 0.078 \frac{J c}{S_x h_0} (L_b/r_{ts})^2}")
            
            slenderness = lb_sim_cm / r_ts
            st.markdown(f"Slenderness $(L_b / r_{{ts}}) = {slenderness:.2f}$")
            
            st.latex(r"M_n = F_{cr} S_x \le M_p")
            st.markdown(f"**Result:** $M_n = {mn_sim_kgm:,.0f}$ kg-m")

        # 3.3 Final Design Capacity
        st.markdown("---")
        c_final1, c_final2 = st.columns(2)
        with c_final1:
            st.write("**Nominal Capacity ($M_n$):**")
            st.markdown(f"<h3 style='color:#334155'>{mn_sim_kgm:,.0f} kg-m</h3>", unsafe_allow_html=True)
        with c_final2:
            if is_lrfd:
                phi = 0.90
                m_design = phi * mn_sim_kgm
                st.write(f"**Design Capacity ($\phi M_n$) - LRFD:**")
                st.markdown(f"<h3 style='color:#1e40af'>{m_design:,.0f} kg-m</h3>", unsafe_allow_html=True)
                st.caption(f"Apply $\phi = {phi}$")
            else:
                omega = 1.67
                m_design = mn_sim_kgm / omega
                st.write(f"**Allowable Capacity ($M_n / \Omega$) - ASD:**")
                st.markdown(f"<h3 style='color:#1e40af'>{m_design:,.0f} kg-m</h3>", unsafe_allow_html=True)
                st.caption(f"Apply $\Omega = {omega}$")

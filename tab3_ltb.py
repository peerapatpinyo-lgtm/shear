#tab3_ltb.py
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import math

def render(data):
    """
    Render Tab 3: LTB Insight + Derivation
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
    val_A = data['val_A'] # (J / Sx h0)
    user_span = data['user_span']
    is_lrfd = data['is_lrfd']
    
    # Extract additional values for formula display
    ry = data.get('ry', 0) 
    J = data.get('J', 0)
    h0 = data.get('h0', 1)

    # Unit Conversion
    Lp_m = Lp_cm / 100
    Lr_m = Lr_cm / 100
    Mp_kgm = Mp / 100
    
    st.subheader("🛡️ LTB Stability Analysis")
    # Visual context for the physical phenomenon
    st.markdown("")

    # --- PART 2: SIMULATION & GRAPH ---
    col_sim, col_graph = st.columns([1, 2])
    
    with col_sim:
        st.markdown("#### 🎮 Simulator")
        st.caption("Adjust unbraced length ($L_b$) to observe changes in capacity.")
        
        lb_sim = st.slider("Simulate Lb (m)", 
                           min_value=0.5, 
                           max_value=float(user_span), 
                           value=float(Lb_real),
                           step=0.1)
        
        # Calculate State
        lb_sim_cm = lb_sim * 100
        if lb_sim_cm <= Lp_cm:
            mn_sim = Mp
            zone_sim = "Zone 1: Plastic"
            zone_color = "#10b981"
        elif lb_sim_cm <= Lr_cm:
            term = (Mp - 0.7 * Fy * Sx) * ((lb_sim_cm - Lp_cm) / (Lr_cm - Lp_cm))
            mn_sim = min(Cb * (Mp - term), Mp)
            zone_sim = "Zone 2: Inelastic"
            zone_color = "#f59e0b"
        else:
            slend = (lb_sim_cm / r_ts)
            fcr = (Cb * math.pi**2 * E) / (slend**2) * math.sqrt(1 + 0.078 * val_A * slend**2)
            mn_sim = min(fcr * Sx, Mp)
            zone_sim = "Zone 3: Elastic"
            zone_color = "#ef4444"
            
        mn_sim_kgm = mn_sim / 100
        
        st.markdown(f"""
        <div style="text-align:center; padding:15px; background:{zone_color}15; border-radius:10px; border:2px solid {zone_color}; margin-top:10px;">
            <div style="font-size:14px; color:{zone_color}; font-weight:bold;">{zone_sim}</div>
            <div style="font-size:32px; font-weight:800; color:#1e293b;">{mn_sim_kgm:,.0f}</div>
            <div style="font-size:14px; color:#64748b;">kg-m (Nominal)</div>
        </div>
        """, unsafe_allow_html=True)

    with col_graph:
        # Plot Logic
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
        fig.add_trace(go.Scatter(x=[lb_sim], y=[mn_sim_kgm], mode='markers', name='Sim Point', marker=dict(size=14, color=zone_color, symbol='diamond', line=dict(width=2, color='white'))))
        if abs(lb_sim - Lb_real) > 0.1:
             fig.add_vline(x=Lb_real, line_dash="dot", line_color="gray", annotation_text="Actual")
        
        # Add background zones
        fig.add_vrect(x0=0, x1=Lp_m, fillcolor="green", opacity=0.1, layer="below")
        fig.add_vrect(x0=Lp_m, x1=Lr_m, fillcolor="orange", opacity=0.1, layer="below")
        fig.add_vrect(x0=Lr_m, x1=max_len, fillcolor="red", opacity=0.1, layer="below")
        
        fig.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=300, xaxis_title="Lb (m)", yaxis_title="Mn (kg-m)", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # --- PART 3: DEFINITIONS ---
    st.divider()
    
    with st.expander("📘 Reference: Derivation of Lp and Lr", expanded=False):
        c_def1, c_def2 = st.columns(2)
        
        # --- Lp Derivation ---
        with c_def1:
            st.markdown("#### 1. Limit $L_p$ (Plastic Limit)")
            st.caption("End of Zone 1: Beam can reach full plastic moment without buckling.")
            
            st.latex(r"L_p = 1.76 r_y \sqrt{\frac{E}{F_y}}")
            
            st.markdown("**Substituting values:**")
            st.markdown(f"""
            - $r_y = {ry:.2f}$ cm
            - $E = {E:,.0f}$ ksc
            - $F_y = {Fy:,.0f}$ ksc
            """)
            st.info(f"👉 **Calculated:** {Lp_cm:.2f} cm ({Lp_m:.2f} m)")

        # --- Lr Derivation ---
        with c_def2:
            st.markdown("#### 2. Limit $L_r$ (Elastic Limit)")
            st.caption("End of Zone 2: Beam transitions into elastic buckling behavior.")
            
            st.latex(r"L_r = 1.95 r_{ts} \frac{E}{0.7F_y} \sqrt{\frac{J c}{S_x h_0} + \sqrt{\left(\frac{J c}{S_x h_0}\right)^2 + 6.76\left(\frac{0.7F_y}{E}\right)^2}}")
            
            st.markdown("**Key Parameters:**")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.write(f"- $r_{{ts}} = {r_ts:.2f}$ cm")
                st.write(f"- $J = {J:.2f}$ cm⁴")
            with col_p2:
                st.write(f"- $S_x = {Sx:,.0f}$ cm³")
                st.write(f"- $h_0 = {h0:.1f}$ cm")
            
            st.info(f"👉 **Calculated:** {Lr_cm:.2f} cm ({Lr_m:.2f} m)")

    # --- PART 4: LIVE CALCULATION ---
    st.subheader(f"🧮 Live Calculation: {zone_sim}")
    with st.expander("Mn Calculation Steps", expanded=True):
        
        st.markdown(f"**Current State:** $L_b = {lb_sim:.2f}$ m")

        if lb_sim_cm <= Lp_cm:
            # ZONE 1
            st.markdown("##### Case: Plastic Moment ($L_b \le L_p$)")
            st.latex(r"M_n = M_p = F_y Z_x")
            st.write(f"Result: $M_n = {Mp/100:,.0f}$ kg-m")
            
        elif lb_sim_cm <= Lr_cm:
            # ZONE 2
            st.markdown("##### Case: Inelastic Buckling ($L_p < L_b \le L_r$)")
            st.write("Using Linear Interpolation Formula:")
            st.latex(r"M_n = C_b \left[ M_p - (M_p - 0.7 F_y S_x) \left( \frac{L_b - L_p}{L_r - L_p} \right) \right]")
            
            mr = 0.7 * Fy * Sx
            ratio = (lb_sim_cm - Lp_cm) / (Lr_cm - Lp_cm)
            
            st.code(f"""
Interpolation Factor = ({lb_sim_cm:.1f} - {Lp_cm:.1f}) / ({Lr_cm:.1f} - {Lp_cm:.1f}) = {ratio:.3f}
Mp = {Mp:,.0f}
Mr = {mr:,.0f}
            """)
            st.write(f"Result: $M_n = {mn_sim_kgm:,.0f}$ kg-m")
            
        else:
            # ZONE 3
            st.markdown("##### Case: Elastic Buckling ($L_b > L_r$)")
            st.write("Using Critical Stress ($F_{cr}$) Formula:")
            st.latex(r"F_{cr} = \frac{C_b \pi^2 E}{(L_b/r_{ts})^2} \sqrt{1 + 0.078 \frac{J}{S_x h_0} (L_b/r_{ts})^2}")
            
            slenderness = lb_sim_cm / r_ts
            st.write(f"Slenderness $(L_b / r_{{ts}}) = {slenderness:.2f}$")
            st.write(f"Result: $M_n = {mn_sim_kgm:,.0f}$ kg-m")

        st.divider()
        # Final Design Value
        if is_lrfd:
             st.success(f"**Design Capacity ($\phi M_n$): {0.90 * mn_sim_kgm:,.0f} kg-m** (LRFD, $\phi=0.9$)")
        else:
             st.success(f"**Allowable Capacity ($M_n/\Omega$): {mn_sim_kgm/1.67:,.0f} kg-m** (ASD, $\Omega=1.67$)")

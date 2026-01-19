# tab3_ltb.py
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import math

def render(data):
    """
    Render Tab 3: LTB Insight
    data: Dictionary containing LTB parameters and material props
    """
    # Unpack necessary data
    ltb_zone = data['ltb_zone']
    Lb = data['Lb']
    Lb_cm = data['Lb_cm']
    Lp_cm = data['Lp_cm']
    Lr_cm = data['Lr_cm']
    Mp = data['Mp']
    Fy = data['Fy']
    Sx = data['Sx']
    E = data['E']
    Cb = data['Cb']
    r_ts = data['r_ts']
    val_A = data['val_A']
    M_cap = data['M_cap']
    is_lrfd = data['is_lrfd']
    
    st.subheader("🛡️ LTB Insight")
    c_ltb1, c_ltb2 = st.columns([1, 2])
    with c_ltb1:
        st.markdown(f"""
        <div style="background:#f8fafc; padding:15px; border-radius:8px; border:1px solid #e2e8f0;">
            <b>LTB State:</b> {ltb_zone}<br>
            <b>Lb:</b> {Lb:.2f} m<br>
            <b>Lp:</b> {Lp_cm/100:.2f} m <br>
            <b>Lr:</b> {Lr_cm/100:.2f} m
        </div>""", unsafe_allow_html=True)
        
    with c_ltb2:
        lb_vals = np.linspace(0.1, max(Lr_cm*1.5, Lb_cm*1.2), 50)
        mn_vals = []
        for l_chk in lb_vals:
            if l_chk <= Lp_cm: mn_chk = Mp
            elif l_chk <= Lr_cm:
                term = (Mp - 0.7 * Fy * Sx) * ((l_chk - Lp_cm) / (Lr_cm - Lp_cm))
                mn_chk = min(Cb * (Mp - term), Mp)
            else:
                slend = (l_chk / r_ts)
                fcr_chk = (Cb * math.pi**2 * E) / (slend**2) * math.sqrt(1 + 0.078 * val_A * slend**2)
                mn_chk = min(fcr_chk * Sx, Mp)
            mn_vals.append(mn_chk/100) 

        fig_ltb = go.Figure()
        fig_ltb.add_trace(go.Scatter(x=lb_vals/100, y=mn_vals, name='Mn Capacity', line=dict(color='#2563eb')))
        
        # Design Capacity marker calculation
        phi_b = 0.90
        omg_b = 1.67
        curr_Mn = (M_cap * 100 / phi_b) if is_lrfd else (M_cap * 100 * omg_b)
        
        fig_ltb.add_trace(go.Scatter(x=[Lb], y=[curr_Mn/100], mode='markers', marker=dict(size=10, color='red'), name='Current Design'))
        
        # Add Zone Annotations
        fig_ltb.add_vline(x=Lp_cm/100, line_dash="dash", line_color="green", annotation_text="Lp")
        fig_ltb.add_vline(x=Lr_cm/100, line_dash="dash", line_color="orange", annotation_text="Lr")
        
        fig_ltb.update_layout(height=350, margin=dict(t=20,b=20,l=20,r=20), xaxis_title="Unbraced Length (m)", yaxis_title="Moment Capacity (kg-m)")
        st.plotly_chart(fig_ltb, use_container_width=True)

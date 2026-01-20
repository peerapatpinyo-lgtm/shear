import streamlit as st
import math
import numpy as np

def render(data, v_design):
    """
    Render Tab 5: Base Plate Design (AISC Design Guide 1)
    v_design: คือแรงปฏิกิริยา (Reaction) ที่ส่งมาจากคาน/เสา
    """
    st.subheader("🧱 Base Plate Design (Axial Compression)")
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.markdown("#### ⚙️ Input Parameters")
        fc = st.number_input("Concrete Strength, f'c (ksc)", 100, 500, 240)
        tp_guess = st.slider("Trial Plate Thickness (mm)", 10, 50, 20)
        
        st.markdown("**Plate Dimensions**")
        N = st.number_input("Plate Depth, N (mm)", 100, 1000, 400)
        B = st.number_input("Plate Width, B (mm)", 100, 1000, 400)
        
        fy_plate = 2450 # SS400
        
    # --- CALCULATION LOGIC ---
    # 1. Area calculation
    A1 = B * N / 100 # cm2
    Pu = v_design # kg (Assume Reaction from beam is Axial Load for this simplified case)
    
    # 2. Bearing Strength (Simplified: A2/A1 = 1.0 for conservative)
    phi_c = 0.65
    Pp = 0.85 * fc * A1
    bearing_ratio = (Pu) / (phi_c * Pp) if Pp > 0 else 0
    
    # 3. Plate Thickness (Cantilever parts m, n)
    h, b = data['h'], data['b']
    m = (N - 0.95*h) / 2
    n = (B - 0.80*b) / 2
    # Lambda n prime calculation (Simplified)
    X = (4*h*b / (h+b)**2) * Pu / (phi_c * Pp) if Pp > 0 else 0
    # For conservative, we use l = max(m, n)
    l_max = max(m, n) / 10 # convert to cm
    
    # Thickness Required (tp = l * sqrt(2Pu / (0.9 * Fy * B * N)))
    if Pu > 0:
        tp_req_cm = l_max * math.sqrt((2 * Pu) / (0.9 * fy_plate * A1))
        tp_req_mm = tp_req_cm * 10
    else:
        tp_req_mm = 0

    with col2:
        st.markdown("#### 📊 Capacity Check")
        
        # Display Metric
        c1, c2 = st.columns(2)
        with c1:
            color = "red" if bearing_ratio > 1 else "green"
            st.metric("Bearing Ratio (P/φPp)", f"{bearing_ratio:.2f}", delta_color="inverse")
        with c2:
            status = "PASS" if tp_guess >= tp_req_mm else "FAIL"
            st.metric("Required Thickness", f"{tp_req_mm:.1f} mm", status)

        # Drawing Reference Image Tag
        
        
        st.info(f"**Engineering Note:** Based on AISC Design Guide 1. Critical cantilever length (l) is {l_max*10:.1f} mm.")

    # --- SHOW FORMULA ---
    with st.expander("📝 View Calculation Steps"):
        st.latex(rf"f'_c = {fc} \; ksc, \; \phi_c = 0.65")
        st.latex(rf"P_p = 0.85 \cdot f'_c \cdot A_1 = {Pp:,.0f} \; kg")
        st.latex(rf"t_{{req}} = l \sqrt{{\frac{{2P_u}}{{0.9 F_y B N}}}} = {tp_req_mm:.1f} \; mm")

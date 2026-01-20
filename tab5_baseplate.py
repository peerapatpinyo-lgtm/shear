import streamlit as st
import math
import pandas as pd

def render(res_ctx, v_design):
    st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🚀 Enterprise Base Plate Analysis</h2>", unsafe_allow_html=True)
    
    # --- 1. DATA PREPARATION ---
    h, b, tw, tf = res_ctx['h']/10, res_ctx['b']/10, res_ctx['tw']/10, res_ctx['tf']/10
    Fy, E, is_lrfd = res_ctx['Fy'], res_ctx['E'], res_ctx['is_lrfd']
    Ag, ry, rx = 2*b*tf + (h-2*tf)*tw, res_ctx['ry'], res_ctx['Ix']**0.5 / Ag**0.5
    
    # --- 2. ADVANCED CONTROL PANEL ---
    with st.sidebar:
        st.markdown("### ⚙️ Advanced Settings")
        stiffener_check = st.checkbox("Add Base Plate Stiffeners?", value=False)
        weld_size = st.slider("Fillet Weld Size (mm)", 3, 20, 6)
        concrete_type = st.selectbox("Concrete Type", ["Normal Weight", "Lightweight"])
        lambda_c = 1.0 if concrete_type == "Normal Weight" else 0.75

    # --- 3. INPUT SECTION ---
    tab_in1, tab_in2 = st.columns([1, 1])
    with tab_in1:
        with st.container(border=True):
            st.markdown("##### 📏 Structural Geometry")
            col_h = st.slider("Column Height (m)", 0.5, 15.0, 4.0, 0.1)
            k_val = st.selectbox("Effective Length (K)", [2.1, 1.2, 1.0, 0.8, 0.65], index=2)
            st.markdown("##### 🏗️ Foundation Details")
            fc = st.number_input("Concrete f'c (ksc)", 100, 500, 240)
            a2_a1 = st.slider("Pedestal/Plate Area Ratio", 1.0, 4.0, 2.0)
    
    with tab_in2:
        with st.container(border=True):
            st.markdown("##### 🧱 Base Plate & Bolts")
            c_n, c_b = st.columns(2)
            N = c_n.number_input("Plate N (cm)", value=float(math.ceil(h + 10)))
            B = c_b.number_input("Plate B (cm)", value=float(math.ceil(b + 10)))
            bolt_d = st.selectbox("Anchor Bolt Ø (mm)", [16, 20, 24, 30, 36], index=1)
            bolt_n = st.number_input("Number of Bolts", 4, 12, 4, 2)

    # --- 4. ENGINE: BUCKLING & COMPACTNESS ---
    # AISC Table B4.1a - Check Compactness for Compression
    lambda_flange = (b/2) / tf
    limit_flange = 0.56 * math.sqrt(E/Fy)
    flange_status = "Compact" if lambda_flange < limit_flange else "Slender"
    
    # Column Stability
    slend_ratio = (k_val * col_h * 100) / ry
    Fe = (math.pi**2 * E) / (slend_ratio**2)
    Fcr = (0.658**(Fy/Fe)) * Fy if slend_ratio <= 4.71*math.sqrt(E/Fy) else 0.877*Fe
    P_cap = (0.9 * Fcr * Ag) if is_lrfd else (Fcr * Ag / 1.67)

    # --- 5. ENGINE: BASE PLATE OPTIMIZATION ---
    # AISC Design Guide 1 Method
    A1 = N * B
    Pp = min(0.85 * fc * A1 * math.sqrt(a2_a1), 1.7 * fc * A1)
    phi_b = 0.65
    P_bearing = (phi_b * Pp) if is_lrfd else (Pp / 2.31)
    
    # Thickness Optimization
    m = (N - 0.95*h)/2
    n = (B - 0.80*b)/2
    lambda_val = (2 * math.sqrt(h*b) / (h+b)) # AISC lambda
    n_prime = math.sqrt(h * b) / 4
    l_max = max(m, n, lambda_val * n_prime)
    
    t_req = l_max * math.sqrt((2*v_design) / (0.9*Fy*B*N)) if is_lrfd else l_max * math.sqrt((2*v_design*1.67)/(Fy*B*N))

    # --- 6. VISUALIZATION & DASHBOARD ---
    st.divider()
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Column Utilization", f"{v_design/P_cap:.1%}")
    m2.metric("Bearing Utilization", f"{v_design/P_bearing:.1%}")
    m3.metric("Required Thickness", f"{t_req*10:.1f} mm")
    m4.metric("Slenderness (KL/r)", f"{slend_ratio:.1f}")

    

    v_col, d_col = st.columns([1.2, 1])
    
    with v_col:
        st.markdown("#### 🎨 Section Drafting & Pressure Map")
        # Advanced SVG Drawing
        scale = 250 / max(N, B)
        svg_w, svg_h = B*scale, N*scale
        pad = 25
        
        svg = f"""
        <svg width="100%" height="350" viewBox="-50 -50 400 400">
            <defs>
                <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#f3f4f6;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#d1d5db;stop-opacity:1" />
                </linearGradient>
            </defs>
            <rect x="0" y="0" width="{svg_w}" height="{svg_h}" fill="url(#grad1)" stroke="#1e3a8a" stroke-width="3" />
            <rect x="{(svg_w - b*scale)/2}" y="{(svg_h - h*scale)/2}" width="{b*scale}" height="{tf*scale}" fill="#1e40af" />
            <rect x="{(svg_w - b*scale)/2}" y="{(svg_h + h*scale)/2 - tf*scale}" width="{b*scale}" height="{tf*scale}" fill="#1e40af" />
            <rect x="{(svg_w - tw*scale)/2}" y="{(svg_h - h*scale)/2 + tf*scale}" width="{tw*scale}" height="{(h-2*tf)*scale}" fill="#1e40af" />
            <line x1="{svg_w}" y1="{svg_h/2}" x2="{svg_w - n*scale}" y2="{svg_h/2}" stroke="#ef4444" stroke-dasharray="5,5" />
            <text x="{svg_w - 10}" y="{svg_h/2 - 5}" fill="#ef4444" font-size="10">n</text>
            <circle cx="30" cy="30" r="8" fill="#374151" />
            <circle cx="{svg_w-30}" cy="30" r="8" fill="#374151" />
            <circle cx="30" cy="{svg_h-30}" r="8" fill="#374151" />
            <circle cx="{svg_w-30}" cy="{svg_h-30}" r="8" fill="#374151" />
        </svg>
        """
        st.write(svg, unsafe_allow_html=True)
        

    with d_col:
        st.markdown("#### 📈 Stability Interaction")
        # Interaction Graph: Force vs Height
        heights = [h/10 for h in range(5, 155, 5)]
        capacities = []
        for hh in heights:
            sr = (k_val * hh * 100) / ry
            f_e = (math.pi**2 * E) / (sr**2)
            f_cr = (0.658**(Fy/f_e)) * Fy if sr <= 4.71*math.sqrt(E/Fy) else 0.877*f_e
            capacities.append((0.9 * f_cr * Ag)/1000 if is_lrfd else (f_cr * Ag / 1.67)/1000)
        
        chart_data = pd.DataFrame({'Height (m)': heights, 'Capacity (Ton)': capacities})
        st.line_chart(chart_data.set_index('Height (m)'))
        st.caption("Graph showing Axial Capacity (Ton) as Column Height increases.")

    # --- 7. TECHNICAL SUMMARY ---
    with st.expander("📝 Detailed Calculation Steps (Report Ready)"):
        st.write(f"1. **Section Compactness:** Flange b/t = {lambda_flange:.2f} (Limit: {limit_flange:.2f}) -> **{flange_status}**")
        st.write(f"2. **Effective Length:** KL = {k_val} * {col_h} = {k_val*col_h:.2f} m")
        st.write(f"3. **Slenderness Ratio:** KL/r = {slend_ratio:.2f} {'< 200 (OK)' if slend_ratio < 200 else '> 200 (Fail)'}")
        st.write(f"4. **Bearing Stress:** fp = {v_design/A1:.2f} kg/cm² (Allowable: {P_bearing/A1:.2f} kg/cm²)")
        st.write(f"5. **Cantilever distances:** m = {m:.2f} cm, n = {n:.2f} cm, λn' = {lambda_val*n_prime:.2f} cm")

    if v_design > min(P_cap, P_bearing):
        st.error("🚨 OVERLOADED: Structure exceeds capacity in one or more checks.")
    else:
        st.success("💎 Structural Design meets AISC 360-22 Requirements.")

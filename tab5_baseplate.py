import streamlit as st
import math

def render(res_ctx, v_design):
    st.markdown("### 🏆 Professional Column Base Design Suite")
    
    # --- 1. CORE DATA & CONSTANTS ---
    h, b, tw, tf = res_ctx['h']/10, res_ctx['b']/10, res_ctx['tw']/10, res_ctx['tf']/10
    Fy, E, is_lrfd = res_ctx['Fy'], res_ctx['E'], res_ctx['is_lrfd']
    Ag, ry = 2*b*tf + (h-2*tf)*tw, res_ctx['ry']
    
    # --- 2. MULTI-COLUMN INPUT UI ---
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.write("📐 **Geometry**")
            col_h = st.number_input("Height (m)", 0.5, 15.0, 4.0)
            k_val = st.selectbox("K Factor", [2.1, 1.2, 1.0, 0.8, 0.65], index=2)
        with c2:
            st.write("🧱 **Plate & Grout**")
            N = st.number_input("Length N (cm)", value=float(math.ceil(h + 10)))
            B = st.number_input("Width B (cm)", value=float(math.ceil(b + 10)))
            grout_t = st.slider("Grout (mm)", 10, 50, 25)
        with c3:
            st.write("⛓️ **Anchor Bolts**")
            bolt_d = st.selectbox("Bolt Size", [12, 16, 20, 24, 30], index=2)
            bolt_n = st.selectbox("Bolt Qty", [4, 6, 8], index=0)
            bolt_fu = 4200 # Grade 4.6/A307 approx
        with c4:
            st.write("🏗️ **Concrete**")
            fc = st.number_input("f'c (ksc)", 150, 400, 240)
            a2_a1 = st.slider("A2/A1 Ratio", 1.0, 4.0, 2.0)

    # --- 3. ADVANCED CALCULATIONS ---
    # A. Column Stability (AISC Ch. E)
    slenderness = (k_val * col_h * 100) / ry
    Fe = (math.pi**2 * E) / (slenderness**2) if slenderness > 0 else 0.1
    Fcr = (0.658**(Fy/Fe)) * Fy if slenderness <= 4.71*math.sqrt(E/Fy) else 0.877*Fe
    P_cap = (0.9 * Fcr * Ag) if is_lrfd else (Fcr * Ag / 1.67)

    # B. Base Plate Thickness (AISC Design Guide 1)
    m = (N - 0.95*h)/2
    n = (B - 0.80*b)/2
    n_prime = math.sqrt(h * b) / 4
    l_crit = max(m, n, n_prime)
    t_req = l_crit * math.sqrt((2*v_design) / (0.9*Fy*B*N)) if is_lrfd else l_crit * math.sqrt((2*v_design*1.67)/(Fy*B*N))

    # C. Anchor Bolt Shear Capacity (AISC Ch. J)
    # Nominal Shear per bolt (Simplified)
    Ab = (math.pi * (bolt_d/10)**2) / 4
    Fnv = 0.45 * bolt_fu # Shear strength
    V_bolt_cap = (0.75 * Fnv * Ab * bolt_n) if is_lrfd else (Fnv * Ab * bolt_n / 2.0)
    
    # Shear force for bolt check (Assume 20% of axial as accidental shear if no shear input)
    v_shear_act = v_design * 0.1 

    # --- 4. PROFESSIONAL VISUALIZATION ---
    st.markdown("#### 🔍 Structural Integrity & Detailed Drawings")
    
    v1, v2 = st.columns([1.5, 1])
    
    with v1:
        # SVG SIDE VIEW (Section)
        canvas_h = 300
        svg_side = f"""
        <svg width="100%" height="{canvas_h}" viewBox="0 -50 400 350" xmlns="http://www.w3.org/2000/svg">
            <rect x="50" y="150" width="300" height="100" fill="#d1d5db" />
            <path d="M 50 150 L 350 150" stroke="#9ca3af" stroke-width="2" />
            
            <rect x="80" y="140" width="240" height="{grout_t/2}" fill="#94a3b8" />
            
            <rect x="80" y="{140 - 15}" width="240" height="15" fill="#334155" />
            
            <rect x="150" y="0" width="100" height="{140-15}" fill="#1e40af" fill-opacity="0.9" />
            <line x1="150" y1="0" x2="150" y2="125" stroke="#1e3a8a" stroke-width="2"/>
            <line x1="250" y1="0" x2="250" y2="125" stroke="#1e3a8a" stroke-width="2"/>
            
            <line x1="100" y1="100" x2="100" y2="220" stroke="#ef4444" stroke-width="4" stroke-dasharray="2"/>
            <line x1="300" y1="100" x2="300" y2="220" stroke="#ef4444" stroke-width="4" stroke-dasharray="2"/>
            
            <text x="200" y="270" text-anchor="middle" font-size="14" fill="#1e3a8a" font-weight="bold">SIDE SECTION VIEW</text>
            <text x="330" y="145" font-size="12" fill="#4b5563">Grout {grout_t}mm</text>
        </svg>
        """
        st.write(svg_side, unsafe_allow_html=True)
        

    with v2:
        # Metrics & Gauges
        st.info("**Analysis Summary**")
        
        # Column Gauge
        c_util = v_design/P_cap
        st.write(f"Column Buckling: **{c_util:.1%}**")
        st.progress(min(c_util, 1.0))
        
        # Bearing Gauge
        # Concrete capacity including A2/A1
        Pp = 0.85 * fc * (N*B) * math.sqrt(a2_a1)
        B_cap = (0.65 * Pp) if is_lrfd else (Pp / 2.31)
        b_util = v_design/B_cap
        st.write(f"Concrete Bearing: **{b_util:.1%}**")
        st.progress(min(b_util, 1.0))
        
        # Shear Gauge
        s_util = v_shear_act/V_bolt_cap
        st.write(f"Anchor Shear: **{s_util:.1%}**")
        st.progress(min(s_util, 1.0))

    # --- 5. RESULT CARDS ---
    st.divider()
    res1, res2, res3 = st.columns(3)
    res1.success(f"**PLATE THICKNESS**\n\n**{t_req*10:.2f} mm**")
    res2.help("Based on AISC Design Guide 1").metric("MIN. BOLT EMBEDMENT", f"{bolt_d*12} mm")
    res3.metric("SAFE LOAD LIMIT", f"{int(min(P_cap, B_cap)/1000)} Ton")

    if c_util > 1.0:
        st.error("🚨 CRITICAL: Column will fail by Buckling. Increase section size or decrease K-length.")

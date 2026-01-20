import streamlit as st
import math
import pandas as pd

def render(res_ctx, v_design):
    st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🏗️ 3D Advanced Base Plate Engine</h2>", unsafe_allow_html=True)
    
    # --- 1. DATA EXTRACTION ---
    try:
        h, b = res_ctx['h']/10, res_ctx['b']/10
        tw, tf = res_ctx['tw']/10, res_ctx['tf']/10
        Ag = (2 * b * tf) + ((h - 2 * tf) * tw)
        ry, Fy, E = res_ctx['ry'], res_ctx['Fy'], res_ctx['E']
        is_lrfd = res_ctx['is_lrfd']
    except:
        st.error("Data connection failed. Please check Tab 1.")
        return

    # --- 2. INPUT INTERFACE ---
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("##### 📏 Column")
            col_h = st.slider("Height (m)", 1.0, 12.0, 4.0)
            k_val = st.selectbox("K Factor", [2.1, 1.2, 1.0, 0.8], index=2)
        with c2:
            st.markdown("##### 🧱 Plate")
            N = st.number_input("Length N (cm)", value=float(math.ceil(h + 10)))
            B = st.number_input("Width B (cm)", value=float(math.ceil(b + 10)))
        with c3:
            st.markdown("##### 🏗️ Foundation")
            fc = st.number_input("Concrete f'c (ksc)", 150, 450, 240)
            a2_a1 = st.slider("A2/A1 Ratio", 1.0, 4.0, 2.0)

    # --- 3. CALCULATIONS ---
    # Column Cap
    slend = (k_val * col_h * 100) / ry
    Fe = (math.pi**2 * E) / (slend**2)
    Fcr = (0.658**(Fy/Fe)) * Fy if slend <= 4.71*math.sqrt(E/Fy) else 0.877*Fe
    P_cap = (0.9 * Fcr * Ag) if is_lrfd else (Fcr * Ag / 1.67)
    
    # Plate Thickness
    m, n = (N - 0.95*h)/2, (B - 0.80*b)/2
    l_crit = max(m, n, (math.sqrt(h*b)/4))
    t_req = l_crit * math.sqrt((2*v_design)/(0.9*Fy*B*N)) if is_lrfd else l_crit * math.sqrt((2*v_design*1.67)/(Fy*B*N))
    t_disp = max(t_req, 1.2) # Minimum display thickness 12mm

    # --- 4. 3D ISOMETRIC DRAWING (SVG) ---
    st.markdown("#### 💎 3D Structural Preview")
    
    # Isometric Projection Logic
    # (x, y, z) -> ( x*cos(30) - y*cos(30), x*sin(30) + y*sin(30) - z )
    def iso(x, y, z):
        curr_x = (x - y) * math.cos(math.radians(30))
        curr_y = (x + y) * math.sin(math.radians(30)) - z
        return curr_x + 200, curr_y + 150

    # Scale to fit
    sc = 150 / max(N, B)
    tp_sc = t_disp * sc * 2 # Exaggerate thickness for visibility
    
    # Points for Base Plate (N x B x thickness)
    p1 = iso(0, 0, 0)
    p2 = iso(B*sc, 0, 0)
    p3 = iso(B*sc, N*sc, 0)
    p4 = iso(0, N*sc, 0)
    p1t = iso(0, 0, tp_sc)
    p2t = iso(B*sc, 0, tp_sc)
    p3t = iso(B*sc, N*sc, tp_sc)
    p4t = iso(0, N*sc, tp_sc)

    # Points for Column (Centered)
    off_b, off_n = (B-b)*sc/2, (N-h)*sc/2
    c1 = iso(off_b, off_n, tp_sc)
    c2 = iso(off_b+b*sc, off_n, tp_sc)
    c3 = iso(off_b+b*sc, off_n+h*sc, tp_sc)
    c4 = iso(off_b, off_n+h*sc, tp_sc)
    c1h = iso(off_b, off_n, tp_sc + 100) # Column height 100px for preview
    c2h = iso(off_b+b*sc, off_n, tp_sc + 100)
    c3h = iso(off_b+b*sc, off_n+h*sc, tp_sc + 100)
    c4h = iso(off_b, off_n+h*sc, tp_sc + 100)

    svg_code = f"""
    <svg width="100%" height="400" viewBox="0 0 450 350">
        <polygon points="{p1[0]},{p1[1]} {p2[0]},{p2[1]} {p3[0]},{p3[1]} {p4[0]},{p4[1]}" fill="#94a3b8" />
        <polygon points="{p2[0]},{p2[1]} {p3[0]},{p3[1]} {p3t[0]},{p3t[1]} {p2t[0]},{p2t[1]}" fill="#64748b" />
        <polygon points="{p3[0]},{p3[1]} {p4[0]},{p4[1]} {p4t[0]},{p4t[1]} {p3t[0]},{p3t[1]}" fill="#475569" />
        <polygon points="{p1t[0]},{p1t[1]} {p2t[0]},{p2t[1]} {p3t[0]},{p3t[1]} {p4t[0]},{p4t[1]}" fill="#cbd5e1" stroke="#1e293b" />
        
        <polygon points="{c1[0]},{c1[1]} {c2[0]},{c2[1]} {c2h[0]},{c2h[1]} {c1h[0]},{c1h[1]}" fill="#1e40af" stroke="#1e3a8a"/>
        <polygon points="{c2[0]},{c2[1]} {c3[0]},{c3[1]} {c3h[0]},{c3h[1]} {c2h[0]},{c2h[1]}" fill="#3b82f6" stroke="#1e3a8a"/>
        <polygon points="{c1h[0]},{c1h[1]} {c2h[0]},{c2h[1]} {c3h[0]},{c3h[1]} {c4h[0]},{c4h[1]}" fill="#60a5fa" stroke="#1e3a8a"/>
        
        <text x="{p2[0]+10}" y="{p2[1]}" font-size="12" fill="#475569">B={B} cm</text>
        <text x="{p4[0]-40}" y="{p4[1]}" font-size="12" fill="#475569">N={N} cm</text>
    </svg>
    """
    
    col_vis, col_res = st.columns([1.5, 1])
    with col_vis:
        st.write(svg_code, unsafe_allow_html=True)
        
        
    with col_res:
        st.info("📊 Analysis")
        st.metric("Required Thickness", f"{t_req*10:.2f} mm")
        st.metric("Concrete Bearing", f"{(v_design/P_cap)*100:.1f} %")
        if v_design > P_cap:
            st.error("🚨 Overloaded")
        else:
            st.success("✅ Design Safe")

    # --- 5. INTERACTION CHART ---
    st.markdown("#### 📈 Column Capacity vs Height")
    h_range = [i/10 for i in range(10, 155, 5)]
    caps = []
    for hr in h_range:
        sr = (k_val * hr * 100) / ry
        fe_r = (math.pi**2 * E) / (sr**2)
        fcr_r = (0.658**(Fy/fe_r)) * Fy if sr <= 4.71*math.sqrt(E/Fy) else 0.877 * fe_r
        caps.append((0.9 * fcr_r * Ag)/1000 if is_lrfd else (fcr_r * Ag / 1.67)/1000)
    
    st.line_chart(pd.DataFrame({"Height (m)": h_range, "Capacity (Ton)": caps}).set_index("Height (m)"))

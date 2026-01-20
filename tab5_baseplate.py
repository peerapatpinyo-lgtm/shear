import streamlit as st
import math

def render(res_ctx, v_design):
    st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🏗️ Base Plate Engineering Detail</h2>", unsafe_allow_html=True)

    # --- 1. GET DATA & CONSTANTS ---
    h, b, tw, tf = res_ctx['h']/10, res_ctx['b']/10, res_ctx['tw']/10, res_ctx['tf']/10
    Fy, E, is_lrfd = res_ctx['Fy'], res_ctx['E'], res_ctx['is_lrfd']

    # --- 2. INPUT PANEL ---
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("##### 📏 Plate Dimensions")
            N = st.number_input("Length N (cm)", value=float(math.ceil(h + 10)))
            B = st.number_input("Width B (cm)", value=float(math.ceil(b + 10)))
        with c2:
            st.markdown("##### 🧱 Material & Grout")
            tp = st.number_input("Trial Plate Thickness (mm)", 10, 100, 25)
            grout_t = st.slider("Grout Thickness (mm)", 20, 50, 30)
        with c3:
            st.markdown("##### ⛓️ Anchor Setting")
            bolt_d = st.selectbox("Bolt Size (mm)", [16, 20, 24, 30])
            edge_d = st.slider("Edge Distance (mm)", 35, 100, 50)

    # --- 3. AISC DESIGN LOGIC (DG1) ---
    m = (N - 0.95*h)/2
    n = (B - 0.80*b)/2
    n_prime = math.sqrt(h * b) / 4
    l_crit = max(m, n, n_prime) # Critical cantilever distance
    
    t_req = l_crit * math.sqrt((2*v_design)/(0.9*Fy*B*N)) if is_lrfd else l_crit * math.sqrt((2*v_design*1.67)/(Fy*B*N))

    # --- 4. MULTI-VIEW DRAWING (SVG) ---
    # เราจะวาดรูป 2 วิว: 1. Top View แสดงระยะ m, n และ 2. Side Section แสดงชั้นวัสดุ
    st.markdown("#### 📐 Construction Details (Scale Drawing)")
    
    scale = 200 / max(N, B)
    canvas_w, canvas_h = 600, 350
    
    # Coordinates calculation
    plate_w, plate_h = B*scale, N*scale
    col_w, col_h = b*scale, h*scale
    center_x, center_y = 150, 175 # Top View Center
    
    svg = f"""
    <svg width="100%" height="{canvas_h}" viewBox="0 0 {canvas_w} {canvas_h}" xmlns="http://www.w3.org/2000/svg">
        <text x="{center_x}" y="30" text-anchor="middle" font-weight="bold" font-size="14">TOP VIEW</text>
        <rect x="{center_x - plate_w/2}" y="{center_y - plate_h/2}" width="{plate_w}" height="{plate_h}" fill="#f1f5f9" stroke="#1e293b" stroke-width="2"/>
        
        <g transform="translate({center_x}, {center_y})">
            <rect x="{-col_w/2}" y="{-col_h/2}" width="{col_w}" height="{tf*scale}" fill="#334155"/>
            <rect x="{-col_w/2}" y="{col_h/2 - tf*scale}" width="{col_w}" height="{tf*scale}" fill="#334155"/>
            <rect x="{-tw*scale/2}" y="{-col_h/2 + tf*scale}" width="{tw*scale}" height="{(h-2*tf)*scale}" fill="#334155"/>
        </g>

        <line x1="{center_x - plate_w/2}" y1="{center_y + h*scale/2*0.95}" x2="{center_x + plate_w/2}" y2="{center_y + h*scale/2*0.95}" stroke="#ef4444" stroke-dasharray="4" />
        <text x="{center_x + plate_w/2 + 5}" y="{center_y + h*scale/2*0.95 + 15}" fill="#ef4444" font-size="10">Plastic Hinge Line</text>

        <text x="450" y="30" text-anchor="middle" font-weight="bold" font-size="14">SIDE SECTION</text>
        <g transform="translate(350, 0)">
            <rect x="75" y="50" width="50" height="150" fill="#1e40af"/>
            <rect x="0" y="200" width="200" height="{tp/10*scale*2}" fill="#334155"/>
            <rect x="0" y="{200 + tp/10*scale*2}" width="200" height="{grout_t/10*scale*2}" fill="#94a3b8" opacity="0.5"/>
            <rect x="-20" y="{200 + tp/10*scale*2 + grout_t/10*scale*2}" width="240" height="80" fill="#e5e7eb" stroke="#9ca3af"/>
            
            <line x1="30" y1="180" x2="30" y2="300" stroke="#dc2626" stroke-width="3" stroke-dasharray="2"/>
            <line x1="170" y1="180" x2="170" y2="300" stroke="#dc2626" stroke-width="3" stroke-dasharray="2"/>
        </g>
        
        <text x="350" y="215" font-size="10" fill="#1e293b">Plate t = {tp} mm</text>
        <text x="350" y="{235 + grout_t/10*scale*2}" font-size="10" fill="#4b5563">Grout {grout_t} mm</text>
    </svg>
    """
    st.write(svg, unsafe_allow_html=True)
    
    

    # --- 5. TECHNICAL SUMMARY ---
    st.divider()
    res1, res2, res3 = st.columns(3)
    
    with res1:
        st.info("**Design Parameters**")
        st.write(f"Critical distance $l$: `{l_crit:.2f}` cm")
        st.write(f"Bending dist $m$: `{m:.2f}` cm")
        st.write(f"Bending dist $n$: `{n:.2f}` cm")
    
    with res2:
        st.info("**Check Status**")
        ratio = t_req / (tp/10)
        st.write(f"Thickness Ratio: `{ratio:.1%}`")
        if ratio > 1.0:
            st.error("NG: Plate is too thin")
        else:
            st.success("OK: Thickness safe")
            
    with res3:
        st.info("**Recommendation**")
        st.markdown(f"""
        - Min Thickness: **{t_req*10:.1f} mm**
        - Weld Size: **{w_size} mm (E70XX)**
        - Min Bolt Embed: **{bolt_d*12} mm**
        """)

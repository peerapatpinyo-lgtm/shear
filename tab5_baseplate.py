import streamlit as st
import math

def render(res_ctx, v_design):
    # --- 1. ENGINEERING LOGIC & DATA ---
    h, b, tw, tf = res_ctx['h']/10, res_ctx['b']/10, res_ctx['tw']/10, res_ctx['tf']/10
    Fy, is_lrfd = res_ctx['Fy'], res_ctx['is_lrfd']

    # --- 2. PROFESSIONAL INPUT PANEL ---
    with st.container(border=True):
        st.markdown("##### 🛠️ Design Configuration")
        c1, c2, c3, c4 = st.columns(4)
        N = c1.number_input("N (Length) cm", value=float(math.ceil(h + 15)))
        B = c2.number_input("B (Width) cm", value=float(math.ceil(b + 15)))
        tp = c3.number_input("t (Plate) mm", value=25.0)
        gt = c4.number_input("Grout (mm)", value=30.0)

    # --- 3. AISC DG1 CALCULATIONS ---
    m = (N - 0.95*h)/2
    n = (B - 0.80*b)/2
    l_crit = max(m, n, (math.sqrt(h*b)/4))
    t_req = l_crit * math.sqrt((2*v_design)/(0.9*Fy*B*N)) if is_lrfd else l_crit * math.sqrt((2*v_design*1.67)/(Fy*B*N))

    # --- 4. THE BLUEPRINT DRAWING (SVG PRECISION) ---
    st.markdown("#### 📐 Structural Design Drawing")
    
    # Scale calculation to fit both views in 800px width
    sc = 180 / max(N, B)
    canvas_w, canvas_h = 850, 450
    
    # Coordinates
    plan_cx, plan_cy = 220, 220  # Plan View Center
    sec_x, sec_y = 550, 100      # Section View Start
    
    svg = f"""
    <svg width="100%" height="{canvas_h}" viewBox="0 0 {canvas_w} {canvas_h}" style="background-color: #fcfcfc; border: 1px solid #d1d5db;">
        <defs>
            <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e5e7eb" stroke-width="0.5"/>
            </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />

        <text x="{plan_cx}" y="40" text-anchor="middle" font-weight="bold" font-family="monospace">TOP VIEW (PLAN)</text>
        
        <rect x="{plan_cx - B*sc/2}" y="{plan_cy - N*sc/2}" width="{B*sc}" height="{N*sc}" fill="none" stroke="#1e293b" stroke-width="2.5"/>
        
        <g transform="translate({plan_cx}, {plan_cy})">
            <rect x="{-b*sc/2}" y="{-h*sc/2}" width="{b*sc}" height="{tf*sc}" fill="#64748b" stroke="#000" stroke-width="0.5"/>
            <rect x="{-b*sc/2}" y="{h*sc/2 - tf*sc}" width="{b*sc}" height="{tf*sc}" fill="#64748b" stroke="#000" stroke-width="0.5"/>
            <rect x="{-tw*sc/2}" y="{-h*sc/2 + tf*sc}" width="{tw*sc}" height="{(h-2*tf)*sc}" fill="#64748b" stroke="#000" stroke-width="0.5"/>
        </g>

        <g stroke="#94a3b8" stroke-width="1">
            <line x1="{plan_cx - B*sc/2}" y1="{plan_cy + N*sc/2 + 30}" x2="{plan_cx + B*sc/2}" y2="{plan_cy + N*sc/2 + 30}"/>
            <text x="{plan_cx}" y="{plan_cy + N*sc/2 + 45}" text-anchor="middle" font-size="12" fill="#1e293b">B = {B} cm</text>
            
            <line x1="{plan_cx - B*sc/2 - 30}" y1="{plan_cy - N*sc/2}" x2="{plan_cx - B*sc/2 - 30}" y2="{plan_cy + N*sc/2}"/>
            <text x="{plan_cx - B*sc/2 - 45}" y="{plan_cy}" text-anchor="middle" font-size="12" fill="#1e293b" transform="rotate(-90 {plan_cx - B*sc/2 - 45} {plan_cy})">N = {N} cm</text>
        </g>

        <line x1="{plan_cx + B*sc/2}" y1="{plan_cy}" x2="{plan_cx + B*sc/2 - n*sc}" y2="{plan_cy}" stroke="#ef4444" stroke-width="2" marker-end="url(#arrow)"/>
        <text x="{plan_cx + B*sc/2 - n*sc/2}" y="{plan_cy - 5}" fill="#ef4444" font-size="11" font-weight="bold">n={n:.1f}</text>

        <g transform="translate({sec_x}, {sec_y})">
            <text x="80" y="-40" text-anchor="middle" font-weight="bold" font-family="monospace">SECTION A-A</text>
            
            <rect x="55" y="0" width="50" height="150" fill="#cbd5e1" stroke="#1e293b"/>
            
            <rect x="0" y="150" width="160" height="{(tp/10)*sc*3}" fill="#1e293b" stroke="#000"/>
            <text x="170" y="{150 + (tp/20)*sc*3}" font-size="11" alignment-baseline="middle">PL {tp}mm</text>
            
            <rect x="0" y="{150 + (tp/10)*sc*3}" width="160" height="{(gt/10)*sc*3}" fill="#94a3b8" opacity="0.4"/>
            <text x="170" y="{155 + (tp/10 + gt/20)*sc*3}" font-size="10" fill="#64748b">Grout {gt}mm</text>
            
            <rect x="-20" y="{150 + (tp/10 + gt/10)*sc*3}" width="200" height="60" fill="none" stroke="#94a3b8" stroke-dasharray="4,2"/>
            <text x="80" y="{230 + (tp/10 + gt/10)*sc*3}" text-anchor="middle" font-size="10" fill="#94a3b8">CONCRETE PEDESTAL</text>
            
            <path d="M 105 150 L 125 130 h 20" fill="none" stroke="#ef4444" stroke-width="1.5"/>
            <text x="127" y="125" font-size="10" fill="#ef4444" font-weight="bold">E70XX</text>
        </g>
        
        <defs>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orientation="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L9,3 z" fill="#ef4444" />
            </marker>
        </defs>
    </svg>
    """
    st.write(svg, unsafe_allow_html=True)

    # --- 5. RESULT & VALIDATION DASHBOARD ---
    st.divider()
    res1, res2 = st.columns([1, 1.2])
    with res1:
        st.markdown("##### 📥 Load & Performance")
        st.write(f"Design Load: **{v_design/1000:,.2f} Ton**")
        st.write(f"Critical Lever Arm ($l$): **{l_crit:.2f} cm**")
        
    with res2:
        st.markdown("##### ✅ Final Status")
        if tp >= t_req*10:
            st.success(f"PASS: Required {t_req*10:.2f} mm | Provided {tp} mm")
        else:
            st.error(f"FAIL: Required {t_req*10:.2f} mm | Provided {tp} mm")
            st.warning("Action: Increase Plate Thickness or Plate Dimensions (N, B).")

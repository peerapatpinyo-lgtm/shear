import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    # --- 1. PHYSICAL DIMENSIONS (mm) ---
    h_mm, b_mm = res_ctx['h'], res_ctx['b']
    
    # --- 2. INPUT INTERFACE ---
    with st.container(border=True):
        st.markdown("##### 📏 Base Plate & Bolt Grid Alignment")
        c1, c2, c3 = st.columns(3)
        N_mm = c1.number_input("Plate Height N (mm)", value=float(math.ceil(h_mm + 150)))
        B_mm = c2.number_input("Plate Width B (mm)", value=float(math.ceil(b_mm + 150)))
        tp_mm = c3.number_input("Plate Thick (mm)", value=25.0)
        
        c4, c5, c6 = st.columns(3)
        # ระยะจาก CL ถึงกึ่งกลาง Bolt (หน้างานชอบแบบนี้ เพราะดึงตลับเมตรจากสายแกน)
        dist_cl_x = c4.number_input("Half Spacing X (From CL) mm", value=(b_mm/2)+50)
        dist_cl_y = c5.number_input("Half Spacing Y (From CL) mm", value=(h_mm/2)+50)
        bolt_dia = c6.selectbox("Bolt Dia (mm)", [16, 20, 24, 30], index=1)

    # --- 3. CRITICAL CLEARANCE CHECK ---
    # ระยะห่างจากขอบปีกเสาถึงกึ่งกลาง Bolt
    clearance_x = dist_cl_x - (b_mm / 2)
    # ระยะห่างจากขอบเพลทถึงกึ่งกลาง Bolt (Edge Distance)
    edge_x = (B_mm / 2) - dist_cl_x
    edge_y = (N_mm / 2) - dist_cl_y

    # --- 4. HIGH-PRECISION BLUEPRINT (SVG) ---
    sc = 350 / max(N_mm, B_mm)
    cv_w, cv_h = 850, 650
    cx, cy = 350, 325 # Center point of the drawing
    
    svg = f"""
    <div style="display:flex; justify-content:center; background:#ffffff; padding:20px; border:1px solid #1e293b;">
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <text x="20" y="35" font-family="monospace" font-size="18" font-weight="bold">SETTING OUT PLAN: BOLT GROUP & AXIS</text>
        <line x1="20" y1="45" x2="500" y2="45" stroke="#1e293b" stroke-width="2"/>

        <g stroke="#94a3b8" stroke-width="1" stroke-dasharray="10,5,2,5">
            <line x1="{cx - B_mm*sc/2 - 50}" y1="{cy}" x2="{cx + B_mm*sc/2 + 50}" y2="{cy}"/> <line x1="{cx}" y1="{cy - N_mm*sc/2 - 50}" x2="{cx}" y2="{cy + N_mm*sc/2 + 50}"/> </g>
        <text x="{cx + B_mm*sc/2 + 60}" y="{cy+4}" font-size="12" font-weight="bold">CL</text>
        <text x="{cx}" y="{cy - N_mm*sc/2 - 60}" text-anchor="middle" font-size="12" font-weight="bold">CL</text>

        <rect x="{cx - B_mm*sc/2}" y="{cy - N_mm*sc/2}" width="{B_mm*sc}" height="{N_mm*sc}" fill="none" stroke="#000" stroke-width="2"/>
        
        <g transform="translate({cx}, {cy})" fill="#cbd5e1" stroke="#000" stroke-width="1.2">
            <rect x="{-b_mm*sc/2}" y="{-h_mm*sc/2}" width="{b_mm*sc}" height="{res_ctx['tf']*sc}"/>
            <rect x="{-b_mm*sc/2}" y="{(h_mm/2 - res_ctx['tf'])*sc}" width="{b_mm*sc}" height="{res_ctx['tf']*sc}"/>
            <rect x="{-res_ctx['tw']*sc/2}" y="{-h_mm*sc/2 + res_ctx['tf']*sc}" width="{res_ctx['tw']*sc}" height="{(h_mm-2*res_ctx['tf'])*sc}"/>
        </g>

        <g stroke="#3b82f6" stroke-width="2">
            <circle cx="{cx - dist_cl_x*sc}" cy="{cy - dist_cl_y*sc}" r="8" fill="none"/>
            <circle cx="{cx + dist_cl_x*sc}" cy="{cy - dist_cl_y*sc}" r="8" fill="none"/>
            <circle cx="{cx - dist_cl_x*sc}" cy="{cy + dist_cl_y*sc}" r="8" fill="none"/>
            <circle cx="{cx + dist_cl_x*sc}" cy="{cy + dist_cl_y*sc}" r="8" fill="none"/>
        </g>

        <g stroke="#000" stroke-width="1" font-family="monospace" font-size="11">
            <line x1="{cx}" y1="{cy - N_mm*sc/2 - 30}" x2="{cx + dist_cl_x*sc}" y2="{cy - N_mm*sc/2 - 30}"/>
            <path d="M {cx} {cy-N_mm*sc/2-35} v 10 M {cx+dist_cl_x*sc} {cy-N_mm*sc/2-35} v 10" fill="none" stroke="#000"/>
            <text x="{cx + dist_cl_x*sc/2}" y="{cy - N_mm*sc/2 - 40}" text-anchor="middle">{dist_cl_x} mm</text>
            
            <line x1="{cx + b_mm*sc/2}" y1="{cy + 20}" x2="{cx + dist_cl_x*sc}" y2="{cy + 20}" stroke="#ef4444" stroke-width="1.5"/>
            <text x="{cx + (b_mm/2 + clearance_x/2)*sc}" y="{cy + 15}" fill="#ef4444" text-anchor="middle" font-weight="bold">Clr={clearance_x} mm</text>
            
            <line x1="{cx + B_mm*sc/2}" y1="{cy + dist_cl_y*sc}" x2="{cx + dist_cl_x*sc}" y2="{cy + dist_cl_y*sc}" stroke="#16a34a"/>
            <text x="{cx + dist_cl_x*sc + edge_x*sc/2}" y="{cy + dist_cl_y*sc - 5}" fill="#16a34a" text-anchor="middle">e={edge_x} mm</text>
        </g>
    </svg>
    </div>
    """
    components.html(svg, height=650)

    # --- 5. VERDICT DASHBOARD ---
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Wrench Clearance", f"{clearance_x} mm", delta="OK" if clearance_x >= 40 else "CRITICAL")
    c2.metric("Min. Edge Dist.", f"{edge_x} mm", delta="OK" if edge_x >= (bolt_dia*1.5) else "LOW")
    c3.metric("Overall Bolt Spacing", f"{dist_cl_x*2} mm")
    
    if clearance_x < 40:
        st.error(f"🚨 **Installation Warning:** ระยะ Clearance X ({clearance_x}mm) ต่ำกว่า 40mm ช่างจะขันน็อตลำบากมาก แนะนำให้ขยายระยะ Bolt ออกไปอีก")

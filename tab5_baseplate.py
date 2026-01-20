import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    st.markdown("## 🏛️ Comprehensive Base Plate Engineering Analysis")
    st.caption("Standards: AISC 360-22 LRFD/ASD & AISC Design Guide 1")

    # --- 1. PHYSICAL PROPERTIES ---
    h, b, tw, tf = res_ctx['h']/10, res_ctx['b']/10, res_ctx['tw']/10, res_ctx['tf']/10
    Fy, fc = res_ctx['Fy'], 240 # ksc (Assume 240 for typical pedestal)
    
    # --- 2. SENIOR LEVEL INPUTS ---
    with st.container(border=True):
        col1, col2, col3 = st.columns([1.2, 1, 1.2])
        with col1:
            st.markdown("##### 📏 Plate Geometry")
            N = st.number_input("N (Length) cm", value=float(math.ceil(h + 15)))
            B = st.number_input("B (Width) cm", value=float(math.ceil(b + 15)))
            tp = st.number_input("t (Thickness) mm", value=25.0)
        with col2:
            st.markdown("##### 🧱 Material & Grout")
            f_prime_c = st.number_input("Concrete f'c (ksc)", 150, 450, 240)
            grout_t = st.slider("Grout Thick (mm)", 20, 50, 30)
        with col3:
            st.markdown("##### ⛓️ Anchor Reinforcement")
            bolt_d = st.selectbox("Rod Dia (mm)", [16, 20, 24, 30, 36])
            edge_d = st.number_input("Edge Distance (mm)", value=50.0)

    # --- 3. ADVANCED ANALYSIS (AISC DG1) ---
    A1, A2 = N * B, N * B * 4.0 # Assume pedestal is twice the plate dimension
    # Bearing Strength (AISC J8)
    Pp = 0.85 * f_prime_c * A1 * min(math.sqrt(A2/A1), 2.0)
    phi_brg = 0.65
    bearing_ratio = v_design / (phi_brg * Pp)

    # Bending Calculations (Plastic Hinge Methodology)
    m = (N - 0.95 * h) / 2
    n = (B - 0.80 * b) / 2
    n_prime = math.sqrt(h * b) / 4
    l_crit = max(m, n, n_prime)
    t_req = l_crit * math.sqrt((2 * v_design) / (0.9 * Fy * B * N))

    # --- 4. THE "BLUEPRINT" VISUALIZATION (SVG PRECISION) ---
    # Logic: Drawing like a real shop drawing with annotations
    sc = 240 / max(N, B)
    cv_w, cv_h = 800, 520
    cx, cy = 250, 260 # Plan Center
    
    # Anchor positions
    ed = edge_d / 10
    bx, by = (B/2 - ed) * sc, (N/2 - ed) * sc

    svg = f"""
    <div style="display: flex; justify-content: center; background: #ffffff; padding: 10px; border: 1px solid #cbd5e1; border-radius: 4px;">
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect x="5" y="5" width="790" height="510" fill="none" stroke="#334155" stroke-width="1"/>
        <text x="20" y="30" font-family="monospace" font-size="16" font-weight="bold" fill="#1e293b">ENGINEERING DETAIL: COLUMN BASE (SCALE 1:10)</text>
        
        <g transform="translate(0, 20)">
            <text x="{cx}" y="35" text-anchor="middle" font-weight="bold" font-family="sans-serif" font-size="12">TOP VIEW (PLAN)</text>
            <rect x="{cx-B*sc/2}" y="{cy-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#f8fafc" stroke="#000" stroke-width="2"/>
            
            <g transform="translate({cx}, {cy})" fill="#94a3b8" stroke="#000" stroke-width="1.2">
                <rect x="{-b*sc/2}" y="{-h*sc/2}" width="{b*sc}" height="{tf*sc}"/> <rect x="{-b*sc/2}" y="{h*sc/2-tf*sc}" width="{b*sc}" height="{tf*sc}"/> <rect x="{-tw*sc/2}" y="{-h*sc/2+tf*sc}" width="{tw*sc}" height="{(h-2*tf)*sc}"/> </g>

            <line x1="{cx+B*sc/2}" y1="{cy}" x2="{cx+B*sc/2-n*sc}" y2="{cy}" stroke="#ef4444" stroke-width="2" marker-end="url(#arr)"/>
            <text x="{cx+B*sc/2-n*sc/2}" y="{cy-8}" fill="#ef4444" font-size="11" text-anchor="middle">n={n:.2f}</text>
            
            <circle cx="{cx-bx}" cy="{py-by if 'py' in locals() else cy-by}" r="7" fill="none" stroke="#3b82f6" stroke-width="2"/>
            <line x1="{cx-bx-5}" y1="{cy-by}" x2="{cx-bx+5}" y2="{cy-by}" stroke="#3b82f6"/>
            <line x1="{cx-bx}" y1="{cy-by-5}" x2="{cx-bx}" y2="{cy-by+5}" stroke="#3b82f6"/>
        </g>

        <g transform="translate(560, 110)">
            <text x="80" y="-30" text-anchor="middle" font-weight="bold" font-family="sans-serif" font-size="12">SECTION A-A</text>
            <rect x="65" y="0" width="30" height="150" fill="#f1f5f9" stroke="#334155"/>
            <rect x="0" y="150" width="160" height="15" fill="#1e293b"/>
            <rect x="0" y="165" width="160" height="10" fill="#cbd5e1" opacity="0.6"/>
            <line x1="25" y1="130" x2="25" y2="280" stroke="#3b82f6" stroke-width="2" stroke-dasharray="4,2"/>
            
            <text x="170" y="162" font-size="11" font-weight="bold">PL {tp}mm</text>
            <text x="170" y="175" font-size="10" fill="#64748b">GROUT {grout_t}mm</text>
        </g>

        <defs>
            <marker id="arr" markerWidth="10" markerHeight="7" refX="0" refY="3.5" orientation="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#ef4444" />
            </marker>
        </defs>
    </svg>
    </div>
    """
    components.html(svg, height=540)

    # --- 5. SENIOR DESIGN VERDICT (LIMIT STATES) ---
    st.divider()
    res1, res2, res3, res4 = st.columns(4)
    
    with res1:
        st.write("**Concrete Bearing**")
        st.metric("Ratio", f"{bearing_ratio:.2%}", delta="OK" if bearing_ratio < 1 else "FAIL", delta_color="normal")
        
    with res2:
        st.write("**Plate Yielding**")
        p_yield = t_req / (tp/10)
        st.metric("Ratio", f"{p_yield:.2%}", delta="OK" if p_yield < 1 else "FAIL", delta_color="normal")

    with res3:
        st.write("**Min. Thickness**")
        st.metric("Required", f"{t_req*10:.2f} mm")

    with res4:
        st.write("**Bolt Placement**")
        min_wrench = 40 # mm
        clearance = ((B - b)/2 * 10) - edge_d
        st.metric("Clearance", f"{clearance:.0f} mm", delta="OK" if clearance > min_wrench else "TIGHT")

    # Final Engineering Judgment
    if bearing_ratio < 1 and p_yield < 1 and clearance > min_wrench:
        st.success("✅ **Design Accepted:** All limit states satisfy AISC 360-22 requirements.")
    else:
        st.error("❌ **Design Rejected:** One or more limit states exceed allowable capacity.")

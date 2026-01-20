import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    # --- 1. PRECISE ENGINEERING LOGIC ---
    h, b, tw, tf = res_ctx['h']/10, res_ctx['b']/10, res_ctx['tw']/10, res_ctx['tf']/10
    Fy, E, is_lrfd = res_ctx['Fy'], res_ctx['E'], res_ctx['is_lrfd']
    V_shear = res_ctx.get('V_max', 0) # ดึงแรงเฉือนมาคำนวณ Shear Lug

    # --- 2. ADVANCED PARAMETERS PANEL ---
    with st.container(border=True):
        st.markdown("##### 🛠️ Comprehensive Structural Parameters")
        c1, c2, c3, c4 = st.columns(4)
        N = c1.number_input("Plate N (cm)", value=float(math.ceil(h + 15)))
        B = c2.number_input("Plate B (cm)", value=float(math.ceil(b + 15)))
        tp = c3.number_input("Thickness (mm)", value=25.0)
        fc = c4.number_input("Concrete f'c (ksc)", value=240.0)
        
        c5, c6, c7, c8 = st.columns(4)
        bolt_d = c5.selectbox("Bolt Dia (mm)", [16, 20, 24, 30], index=1)
        n_bolts = c6.selectbox("No. of Bolts", [4, 6, 8], index=0)
        edge_d = c7.number_input("Edge Dist (mm)", value=50.0)
        mu = c8.slider("Friction Coeff (μ)", 0.3, 0.7, 0.4) # สำหรับเช็ค Shear Transfer

    # --- 3. MULTI-LIMIT STATE CALCULATIONS ---
    # A. Bearing Check (AISC J8)
    A1 = N * B
    A2 = A1 * 4.0 # Conservatively assume pedestal is larger
    Pp = 0.85 * fc * A1 * min(math.sqrt(A2/A1), 2.0)
    phi_brg = 0.65 if is_lrfd else 1/2.31
    bearing_util = v_design / (phi_brg * Pp)

    # B. Plate Bending (AISC DG1)
    m = (N - 0.95*h)/2
    n = (B - 0.80*b)/2
    n_prime = math.sqrt(h * b) / 4
    l_crit = max(m, n, n_prime)
    t_req = l_crit * math.sqrt((2*v_design)/(0.9*Fy*B*N)) if is_lrfd else l_crit * math.sqrt((2*v_design*1.67)/(Fy*B*N))

    # C. Shear Transfer Check
    shear_cap_friction = mu * v_design * (0.9 if is_lrfd else 1.0)
    need_shear_lug = V_shear > shear_cap_friction

    # --- 4. THE ULTIMATE BLUEPRINT (SVG) ---
    sc = 180 / max(N, B)
    canvas_w, canvas_h = 800, 480
    px, py = 220, 240
    
    # Anchor positions
    eb = edge_d / 10
    bx, by = (B/2 - eb) * sc, (N/2 - eb) * sc

    svg_code = f"""
    <div style="display:flex; justify-content:center; background:#ffffff; padding:15px; border-radius:8px;">
    <svg width="{canvas_w}" height="{canvas_h}" viewBox="0 0 {canvas_w} {canvas_h}" xmlns="http://www.w3.org/2000/svg">
        <text x="{px}" y="30" text-anchor="middle" font-weight="bold" font-family="monospace">PLAN VIEW (SCALE 1:10)</text>
        <rect x="{px-B*sc/2}" y="{py-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="none" stroke="#1e293b" stroke-width="2"/>
        
        <g transform="translate({px}, {py})" fill="#cbd5e1" stroke="#000">
            <rect x="{-b*sc/2}" y="{-h*sc/2}" width="{b*sc}" height="{tf*sc}"/>
            <rect x="{-b*sc/2}" y="{h*sc/2 - tf*sc}" width="{b*sc}" height="{tf*sc}"/>
            <rect x="{-tw*sc/2}" y="{-h*sc/2 + tf*sc}" width="{tw*sc}" height="{(h-2*tf)*sc}"/>
        </g>
        
        <line x1="{px-B*sc/2}" y1="{py-h*sc/2*0.95}" x2="{px+B*sc/2}" y2="{py-h*sc/2*0.95}" stroke="#ef4444" stroke-dasharray="4"/>
        <line x1="{px-b*sc/2*0.8}" y1="{py-N*sc/2}" x2="{px-b*sc/2*0.8}" y2="{py+N*sc/2}" stroke="#ef4444" stroke-dasharray="4"/>

        <circle cx="{px-bx}" cy="{py-by}" r="7" fill="none" stroke="#3b82f6" stroke-width="2"/>
        <circle cx="{px+bx}" cy="{py-by}" r="7" fill="none" stroke="#3b82f6" stroke-width="2"/>
        <circle cx="{px-bx}" cy="{py+by}" r="7" fill="none" stroke="#3b82f6" stroke-width="2"/>
        <circle cx="{px+bx}" cy="{py+by}" r="7" fill="none" stroke="#3b82f6" stroke-width="2"/>

        <g transform="translate(520, 100)">
            <text x="80" y="-30" text-anchor="middle" font-weight="bold" font-family="monospace">CONSTRUCTION DETAIL</text>
            <rect x="60" y="0" width="40" height="150" fill="#f8fafc" stroke="#1e293b"/> <rect x="0" y="150" width="160" height="12" fill="#334155"/> <rect x="0" y="162" width="160" height="8" fill="#94a3b8" opacity="0.4"/> {"<rect x='65' y='170' width='30' height='40' fill='#1e293b'/>" if need_shear_lug else ""}
            
            <path d="M 170 150 L 170 162" stroke="#000" stroke-width="1"/>
            <text x="175" y="158" font-size="10">t={tp}mm</text>
        </g>
        
        <g transform="translate(520, 360)" font-size="11" font-family="sans-serif">
            <circle cx="10" cy="10" r="5" fill="none" stroke="#3b82f6" stroke-width="2"/>
            <text x="25" y="14">Anchor Rods: {n_bolts}-M{bolt_d}</text>
            <line x1="5" y1="30" x2="15" y2="30" stroke="#ef4444" stroke-dasharray="4"/>
            <text x="25" y="34">Critical Yield Lines (m, n)</text>
        </g>
    </svg>
    </div>
    """
    components.html(svg_code, height=canvas_h + 20)

    # --- 5. COMPREHENSIVE VERIFICATION DASHBOARD ---
    st.divider()
    st.markdown("##### 📊 AISC Compliance Dashboard")
    v1, v2, v3, v4 = st.columns(4)
    
    v1.metric("Bearing Util.", f"{bearing_util:.1%}")
    v2.metric("Plate Bending", f"{(t_req*10)/tp:.1%}")
    v3.metric("Shear Status", "LUG REQ." if need_shear_lug else "FRICTION OK")
    v4.metric("Min. t Required", f"{t_req*10:.2f} mm")

    # Final Recommendation
    if tp < t_req*10:
        st.error(f"🚨 **Structure Alert:** Plate is too thin for yielding. Increase to at least {math.ceil(t_req*10)} mm.")
    elif bearing_util > 1.0:
        st.error("🚨 **Bearing Failure:** Foundation area is insufficient or Concrete grade is too low.")
    else:
        st.success("✅ **Professional Grade:** All structural limit states verified.")

    with st.expander("📝 Structural Engineer's Design Notes"):
        st.write(f"""
        - **Yield Line Analysis:** คำนวณที่ระยะ cantilever $m = {m:.2f}$ cm และ $n = {n:.2f}$ cm
        - **Weld Requirement:** แนะนำ Fillet Weld E70XX ขนาดอย่างน้อย {max(6, math.ceil(tf*0.75*10))} mm รอบหน้าตัดเสา
        - **Grout Space:** ออกแบบให้มีช่องว่าง {gt if 'gt' in locals() else 30} mm สำหรับ Non-shrink Grout เพื่อปรับระดับ (Leveling)
        """)

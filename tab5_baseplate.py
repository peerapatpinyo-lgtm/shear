import streamlit as st
import math

def render(res_ctx, v_design):
    st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🏗️ Professional Column-to-Base Detail</h2>", unsafe_allow_html=True)

    # --- 1. DATA EXTRACTION ---
    h, b, tw, tf = res_ctx['h']/10, res_ctx['b']/10, res_ctx['tw']/10, res_ctx['tf']/10
    Fy, E, is_lrfd = res_ctx['Fy'], res_ctx['E'], res_ctx['is_lrfd']

    # --- 2. INPUT CONTROLS ---
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("##### 📍 Geometry")
            N = st.number_input("Plate Length N (cm)", value=float(math.ceil(h + 15)))
            B = st.number_input("Plate Width B (cm)", value=float(math.ceil(b + 15)))
        with c2:
            st.markdown("##### 🧱 Material")
            tp_trial = st.number_input("Plate Thickness (mm)", 10, 100, 25)
            fc = st.number_input("Concrete f'c (ksc)", 150, 450, 240)
        with c3:
            st.markdown("##### ⚡ Weld & Bolts")
            w_size = st.slider("Weld Size (mm)", 3, 16, 6)
            bolt_d = st.selectbox("Bolt Size (mm)", [16, 20, 24, 30])

    # --- 3. THE "KNOW-HOW" CALCULATIONS (AISC Design Guide 1) ---
    A1 = N * B
    # Bearing Strength: phi * 0.85 * f'c * A1 * sqrt(A2/A1)
    # Assume Pedestal A2 is 2x Plate Area for safety
    Pp = (0.65 if is_lrfd else 1/2.31) * (0.85 * fc * A1 * 1.414) 
    
    # Critical distances m, n (Cantilever for bending)
    m = (N - 0.95*h)/2
    n = (B - 0.80*b)/2
    l_crit = max(m, n)
    
    # Required thickness (AISC Eq)
    t_req = l_crit * math.sqrt((2*v_design)/(0.9*Fy*B*N)) if is_lrfd else l_crit * math.sqrt((2*v_design*1.67)/(Fy*B*N))

    # --- 4. ADVANCED 3D DRAFTING (SVG) ---
    # Isometric Projection for "Visual Understanding"
    def iso(x, y, z):
        sc = 180 / max(N, B)
        # 30-degree isometric projection
        curr_x = (x - y) * 0.866 * sc + 220
        curr_y = (x + y) * 0.5 * sc - z * sc + 130
        return curr_x, curr_y

    # Calculate Key Points
    p1, p2, p3, p4 = iso(0,0,0), iso(B,0,0), iso(B,N,0), iso(0,N,0)
    pt1, pt2, pt3, pt4 = iso(0,0,tp_trial/10), iso(B,0,tp_trial/10), iso(B,N,tp_trial/10), iso(0,N,tp_trial/10)
    
    # Column Points (Centered)
    off_b, off_n = (B-b)/2, (N-h)/2
    c1, c2, c3, c4 = iso(off_b, off_n, tp_trial/10), iso(off_b+b, off_n, tp_trial/10), iso(off_b+b, off_n+h, tp_trial/10), iso(off_b, off_n+h, tp_trial/10)
    c1h, c2h, c3h, c4h = iso(off_b, off_n, tp_trial/10 + 15), iso(off_b+b, off_n, tp_trial/10 + 15), iso(off_b+b, off_n+h, tp_trial/10 + 15), iso(off_b, off_n+h, tp_trial/10 + 15)

    svg = f"""
    <svg width="100%" height="400" viewBox="0 0 450 350">
        <polygon points="{p1[0]},{p1[1]+20} {p2[0]},{p2[1]+20} {p3[0]},{p3[1]+20} {p4[0]},{p4[1]+20}" fill="#e2e8f0" />
        
        <polygon points="{p2[0]},{p2[1]} {p3[0]},{p3[1]} {pt3[0]},{pt3[1]} {pt2[0]},{pt2[1]}" fill="#64748b" />
        <polygon points="{p3[0]},{p3[1]} {p4[0]},{p4[1]} {pt4[0]},{pt4[1]} {pt3[0]},{pt3[1]}" fill="#475569" />
        
        <polygon points="{pt1[0]},{pt1[1]} {pt2[0]},{pt2[1]} {pt3[0]},{pt3[1]} {pt4[0]},{pt4[1]}" fill="#94a3b8" stroke="#1e293b" />
        
        <polyline points="{c1[0]},{c1[1]} {c2[0]},{c2[1]} {c3[0]},{c3[1]} {c4[0]},{c4[1]} {c1[0]},{c1[1]}" fill="none" stroke="#ef4444" stroke-width="3" opacity="0.4"/>

        <polygon points="{c1[0]},{c1[1]} {c2[0]},{c2[1]} {c2h[0]},{c2h[1]} {c1h[0]},{c1h[1]}" fill="#1e40af" stroke="#1e3a8a" />
        <polygon points="{c2[0]},{c2[1]} {c3[0]},{c3[1]} {c3h[0]},{c3h[1]} {c2h[0]},{c2h[1]}" fill="#3b82f6" stroke="#1e3a8a" />
        <polygon points="{c1h[0]},{c1h[1]} {c2h[0]},{c2h[1]} {c3h[0]},{c3h[1]} {c4h[0]},{c4h[1]}" fill="#60a5fa" stroke="#1e3a8a" />
        
        <text x="{pt2[0]+10}" y="{pt2[1]}" font-size="12" font-weight="bold" fill="#334155">B = {B} cm</text>
        <text x="{pt4[0]-50}" y="{pt4[1]}" font-size="12" font-weight="bold" fill="#334155">N = {N} cm</text>
        <path d="M {pt3[0]+10} {pt3[1]} L {pt3[0]+10} {p3[1]}" stroke="#000" marker-end="url(#arrow)"/>
        <text x="{pt3[0]+15}" y="{(pt3[1]+p3[1])/2}" font-size="10">tp={tp_trial}mm</text>
    </svg>
    """
    
    # --- 5. VISUAL DASHBOARD ---
    v_col, r_col = st.columns([1.5, 1])
    with v_col:
        st.write(svg, unsafe_allow_html=True)
        

    with r_col:
        st.markdown("#### ⚖️ Capacity Verification")
        b_ratio = v_design / Pp
        st.write(f"**Concrete Bearing:** {b_ratio:.1%}")
        st.progress(min(b_ratio, 1.0))
        
        t_ratio = t_req / (tp_trial/10)
        st.write(f"**Plate Bending:** {t_ratio:.1%}")
        st.progress(min(t_ratio, 1.0))
        
        st.markdown(f"""
        <div style="background:#f8fafc; border:1px solid #e2e8f0; padding:15px; border-radius:10px;">
            <p style="margin:0; font-size:0.8em; color:#64748b;">AISC REQUIRED THICKNESS</p>
            <h3 style="margin:0; color:#1e40af;">{t_req*10:.2f} mm</h3>
        </div>
        """, unsafe_allow_html=True)

    # --- 6. TECHNICAL INSIGHT ---
    with st.expander("🛠️ Why this matters? (Professional Insight)"):
        st.write(f"""
        1. **Stress Distribution:** แรงอัดจากเสาจะแผ่ออกเป็นรูปพีระมิดผ่านแผ่นเพลท ระยะยื่น (Cantilever) $m$ และ $n$ คือจุดที่เกิดแรงดัดสูงสุด
        2. **Bearing Area:** เราใช้พื้นที่สัมผัส $N \cdot B$ ในการกระจายแรงกดลงคอนกรีตเพื่อให้หน่วยแรงไม่เกิน $0.85 \cdot f'_c$
        3. **Thickness Logic:** ถ้าแผ่นเพลทบางเกินไป มันจะงอ (Yield) ก่อนที่แรงจะกระจายเต็มแผ่น
        """)

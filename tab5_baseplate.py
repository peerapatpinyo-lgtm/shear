import streamlit as st
import math
import pandas as pd

def render(res_ctx, v_design):
    st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🚀 Enterprise Base Plate Analysis</h2>", unsafe_allow_html=True)
    
    # --- 1. SAFE DATA EXTRACTION & VALIDATION ---
    # ดึงค่าจาก res_ctx และแปลงหน่วยเป็น cm ให้เรียบร้อยก่อนใช้งาน
    try:
        h_mm = res_ctx.get('h', 0)
        b_mm = res_ctx.get('b', 0)
        tw_mm = res_ctx.get('tw', 0)
        tf_mm = res_ctx.get('tf', 0)
        
        h, b = h_mm / 10, b_mm / 10
        tw, tf = tw_mm / 10, tf_mm / 10
        
        # คำนวณ Ag ใหม่จากหน้าตัดจริงเพื่อความแม่นยำ (cm2)
        Ag = (2 * b * tf) + ((h - 2 * tf) * tw)
        
        # ดึงค่าทางวิศวกรรมอื่นๆ
        ry = res_ctx.get('ry', 1.0)
        Fy = res_ctx.get('Fy', 2500)
        E = res_ctx.get('E', 2040000)
        is_lrfd = res_ctx.get('is_lrfd', True)
        sec_name = res_ctx.get('sec_name', "Unknown")
        
    except Exception as e:
        st.error(f"❌ Data Error: {str(e)}")
        return

    # --- 2. ADVANCED CONTROL PANEL ---
    with st.container(border=True):
        c_in1, c_in2, c_in3 = st.columns(3)
        with c_in1:
            st.markdown("##### 📏 Column Geometry")
            col_h = st.slider("Column Height (m)", 0.5, 15.0, 4.0, 0.1)
            k_val = st.selectbox("Effective Length Factor (K)", 
                               options=[2.1, 1.2, 1.0, 0.8, 0.65], 
                               index=2, help="K=1.0 for Pinned, K=2.1 for Cantilever")
        with c_in2:
            st.markdown("##### 🏗️ Foundation & Plate")
            N = st.number_input("Plate Length N (cm)", value=float(math.ceil(h + 10)))
            B = st.number_input("Plate Width B (cm)", value=float(math.ceil(b + 10)))
            fc = st.number_input("Concrete f'c (ksc)", 100, 500, 240)
        with c_in3:
            st.markdown("##### ⛓️ Anchor Details")
            bolt_d = st.selectbox("Bolt Size (mm)", [16, 20, 24, 30], index=1)
            a2_a1 = st.slider("Pedestal/Plate Ratio", 1.0, 4.0, 2.0)

    # --- 3. ENGINEERING CALCULATIONS ---
    # A. Column Stability Check (AISC 360-22 Chapter E)
    slend_ratio = (k_val * col_h * 100) / ry
    Fe = (math.pi**2 * E) / (slend_ratio**2) if slend_ratio > 0 else 0.1
    
    # Critical Stress Fcr
    limit_state = 4.71 * math.sqrt(E/Fy)
    if slend_ratio <= limit_state:
        Fcr = (0.658**(Fy/Fe)) * Fy
    else:
        Fcr = 0.877 * Fe
    
    Pn = Fcr * Ag
    P_cap = (0.9 * Pn) if is_lrfd else (Pn / 1.67)

    # B. Base Plate Thickness (AISC Design Guide 1)
    A1 = N * B
    # Bearing Capacity
    Pp = min(0.85 * fc * A1 * math.sqrt(a2_a1), 1.7 * fc * A1)
    P_bearing_cap = (0.65 * Pp) if is_lrfd else (Pp / 2.31)
    
    # Critical distances m, n, lambda*n'
    m_dist = (N - 0.95 * h) / 2
    n_dist = (B - 0.80 * b) / 2
    lambda_val = (2 * math.sqrt(h * b) / (h + b))
    n_prime = math.sqrt(h * b) / 4
    l_crit = max(m_dist, n_dist, lambda_val * n_prime)
    
    # Required thickness (cm)
    if is_lrfd:
        t_req = l_crit * math.sqrt((2 * v_design) / (0.9 * Fy * B * N)) if A1 > 0 else 0
    else:
        t_req = l_crit * math.sqrt((2 * v_design * 1.67) / (Fy * B * N)) if A1 > 0 else 0

    # --- 4. DASHBOARD & VISUALS ---
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Column Ratio", f"{v_design/P_cap:.1%}")
    m2.metric("Bearing Ratio", f"{v_design/P_bearing_cap:.1%}")
    m3.metric("Min. Thickness", f"{t_req*10:.1f} mm")
    m4.metric("Slenderness", f"{slend_ratio:.1f}")

    

    v_col, d_col = st.columns([1.2, 1])
    with v_col:
        st.markdown(f"#### 🎨 Drafting: {sec_name}")
        scale = 260 / max(N, B)
        sw, sh = b * scale, h * scale
        dw, dh = B * scale, N * scale
        
        svg = f"""
        <svg width="100%" height="320" viewBox="-40 -40 340 340">
            <rect x="0" y="0" width="{dw}" height="{dh}" fill="#f8fafc" stroke="#1e293b" stroke-width="2"/>
            <g transform="translate({(dw-sw)/2}, {(dh-sh)/2})">
                <rect x="0" y="0" width="{sw}" height="{tf*scale}" fill="#3b82f6" />
                <rect x="0" y="{sh - tf*scale}" width="{sw}" height="{tf*scale}" fill="#3b82f6" />
                <rect x="{(sw - tw*scale)/2}" y="{tf*scale}" width="{tw*scale}" height="{sh - 2*tf*scale}" fill="#3b82f6" />
            </g>
            <circle cx="20" cy="20" r="6" fill="#ef4444" />
            <circle cx="{dw-20}" cy="20" r="6" fill="#ef4444" />
            <circle cx="20" cy="{dh-20}" r="6" fill="#ef4444" />
            <circle cx="{dw-20}" cy="{dh-20}" r="6" fill="#ef4444" />
            <text x="{dw/2}" y="-10" text-anchor="middle" font-size="12" fill="#64748b">B = {B} cm</text>
            <text x="-15" y="{dh/2}" text-anchor="middle" font-size="12" fill="#64748b" transform="rotate(-90 -15 {dh/2})">N = {N} cm</text>
        </svg>
        """
        st.write(svg, unsafe_allow_html=True)
        

    with d_col:
        st.markdown("#### 📈 Capacity Curve")
        # Generate Chart Data
        h_range = [i/10 for i in range(10, 155, 5)]
        caps = []
        for hr in h_range:
            sr = (k_val * hr * 100) / ry
            fe_r = (math.pi**2 * E) / (sr**2)
            fcr_r = (0.658**(Fy/fe_r)) * Fy if sr <= limit_state else 0.877 * fe_r
            caps.append((0.9 * fcr_r * Ag)/1000 if is_lrfd else (fcr_r * Ag / 1.67)/1000)
        
        df_chart = pd.DataFrame({"Height (m)": h_range, "Capacity (Ton)": caps})
        st.line_chart(df_chart.set_index("Height (m)"))

    # --- 5. FINAL VERDICT ---
    if slend_ratio > 200:
        st.error("⚠️ เสาชะลูดเกินไป (KL/r > 200) ตามมาตรฐาน AISC ไม่แนะนำให้ใช้งาน")
    elif v_design > P_cap:
        st.error("❌ ขนาดหน้าตัดเหล็กไม่เพียงพอต่อแรงกด (Column Buckling Failure)")
    elif v_design > P_bearing_cap:
        st.error("❌ กำลังแบกทานของคอนกรีตไม่เพียงพอ (Concrete Bearing Failure)")
    else:
        st.success(f"✅ การออกแบบสมบูรณ์: ใช้แผ่นเหล็กหนาอย่างน้อย {math.ceil(t_req*10)} mm")

import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    # ==========================================
    # 1. PARSE & SETUP
    # ==========================================
    is_double_shear = "Double" in conn_type
    shear_planes = 2.0 if is_double_shear else 1.0
    is_beam_to_beam = "Beam to Beam" in conn_type
    support_label = "Primary Beam" if is_beam_to_beam else "Column"

    # Bolt Data
    d_mm = int(bolt_size[1:]) # 16, 20, 24
    d_cm = d_mm / 10
    Ab = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}.get(bolt_size, 3.14)
    
    # Beam Data (Dimensions for checking fit)
    h_beam = float(section_data.get('h', 300))
    tf_beam = float(section_data.get('tf', 10))  # Flange thickness
    tw_beam = float(section_data.get('tw', 8))
    
    # Calculate Clear Web Depth (พื้นที่ว่างที่ใส่ Bolt ได้จริง ไม่ชนปีก)
    # k_detailing = tf + fillet (approx 2*tf for conservative clearance)
    clear_web_h = h_beam - 2*(tf_beam * 1.5) 

    # ==========================================
    # 2. INPUTS & STANDARD CHECK
    # ==========================================
    st.markdown(f"### 📏 Geometry & Fit Check: **{conn_type}**")
    
    # Suggestion Values (Standard Practice)
    min_pitch = 3 * d_mm        # ระยะห่างระหว่างน็อต (Standard 3d)
    min_edge = 1.5 * d_mm       # ระยะขอบ (Standard ~1.5d)
    rec_plate_t = d_mm / 2      # ความหนาเพลทแนะนำ (ครึ่งหนึ่งของน็อต)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"**🔩 Bolt: {bolt_size}**")
        st.caption(f"Min Pitch: {min_pitch:.0f} mm | Min Edge: {min_edge:.0f} mm")
        n_rows = st.number_input("Bolt Rows (V)", 2, 12, 3)
        n_cols = st.number_input("Bolt Cols (H)", 1, 2, 1)
        
    with c2:
        st.markdown("**↔️ Spacing (mm)**")
        s_v = st.number_input("Vertical Pitch (Sv)", 0.0, 300.0, float(max(75, min_pitch)), help=f"Recommended >= {min_pitch} mm")
        s_h = st.number_input("Horiz. Pitch (Sh)", 0.0, 150.0, float(max(50, min_pitch))) if n_cols > 1 else 0
        l_edge_v = st.number_input("Vert. Edge (Lv)", 0.0, 100.0, float(max(40, min_edge)), help="Distance from plate top/bottom to bolt center")

    with c3:
        st.markdown("**📐 Plate & Margin**")
        t_plate_mm = st.number_input("Plate Thickness", 6.0, 50.0, 10.0)
        e1_mm = st.number_input("Weld-to-Bolt (e1)", 30.0, 200.0, 60.0)
        l_side = st.number_input("Side Edge (Ls)", 20.0, 100.0, 40.0)

    # --- GEOMETRY VALIDATION ---
    warnings = []
    
    # 1. Spacing Check
    if s_v < 2.67 * d_mm: warnings.append(f"⚠️ Vertical Pitch ({s_v}) is too close (Code Min: {2.67*d_mm:.0f} mm)")
    if n_cols > 1 and s_h < 2.67 * d_mm: warnings.append(f"⚠️ Horiz. Pitch ({s_h}) is too close")
    if l_edge_v < d_mm: warnings.append(f"⚠️ Vertical Edge ({l_edge_v}) is too short (Risk of tearout)")

    # 2. Plate Size Calculation
    plate_h = (n_rows - 1) * s_v + (2 * l_edge_v)
    plate_w = e1_mm + (n_cols - 1) * s_h + l_side if n_cols > 1 else e1_mm + l_side

    # 3. Fit Check (สำคัญ: เช็คว่ายัดลงคานได้ไหม)
    # Check 1: Plate สูงเกิน Clear Web Height หรือไม่?
    fit_status = "OK"
    fit_color = "green"
    
    if plate_h > clear_web_h:
        fit_status = "CLASH"
        fit_color = "red"
        warnings.append(f"⛔ **CRITICAL:** Plate height ({plate_h} mm) exceeds clear web height ({clear_web_h:.0f} mm). Bolts will hit flanges!")
    elif plate_h > (h_beam - 2*tf_beam):
        fit_status = "TIGHT"
        fit_color = "orange"
        warnings.append(f"⚠️ **Warning:** Plate fits but very tight. Check fillet/weld access.")

    # ==========================================
    # 3. ANALYSIS CALCULATION
    # ==========================================
    # ... (Calculation Logic เหมือนเดิม) ...
    # Pre-calc constants
    dh_cm = (d_mm + 2) / 10
    
    # Elastic Method
    n_total = n_rows * n_cols
    e_total_cm = (e1_mm + (n_cols-1)*s_h/2) / 10
    
    y_coords = [(r - (n_rows-1)/2) * (s_v/10) for r in range(n_rows)]
    x_coords = [(c - (n_cols-1)/2) * (s_h/10) for c in range(n_cols)]
    Ip = (sum([y**2 for y in y_coords]) * n_cols) + (sum([x**2 for x in x_coords]) * n_rows)
    
    V_dir = V_design / n_total
    V_ecc_x = (V_design * e_total_cm * max([abs(y) for y in y_coords])) / Ip if Ip > 0 else 0
    V_ecc_y = (V_design * e_total_cm * max([abs(x) for x in x_coords])) / Ip if Ip > 0 else 0
    V_res = math.sqrt((V_dir + V_ecc_y)**2 + V_ecc_x**2)

    # Capacities
    bolt_db = {"Grade 8.8 (Standard)": {"N": 3200, "X": 4000}, "A325 (High Strength)": {"N": 3795, "X": 4780}, "A490 (Premium)": {"N": 4920, "X": 6200}}
    th_cond = "X" # Assume Excluded for conservative
    if "8.8" in bolt_grade: Fnv = bolt_db["Grade 8.8 (Standard)"][th_cond]
    elif "A325" in bolt_grade: Fnv = bolt_db["A325 (High Strength)"][th_cond]
    else: Fnv = bolt_db["Grade 8.8 (Standard)"][th_cond]

    Rn_shear = n_total * Fnv * Ab * shear_planes
    
    # Bearing
    t_crit_cm = min(t_plate_mm/10, tw_beam/10)
    lc_edge = (l_edge_v/10) - (dh_cm/2)
    lc_inner = (s_v/10) - dh_cm
    Rn_bear_unit_edge = min(1.2*lc_edge*t_crit_cm*4000, 2.4*d_cm*t_crit_cm*4000)
    Rn_bear_unit_inner = min(1.2*lc_inner*t_crit_cm*4000, 2.4*d_cm*t_crit_cm*4000)
    Rn_bear = (n_cols * 2 * Rn_bear_unit_edge) + (n_cols * (n_rows-2) * Rn_bear_unit_inner) if n_rows > 2 else n_total * Rn_bear_unit_edge

    # LRFD/ASD Factors
    phi_omega_shear = 0.75 if is_lrfd else (1/2.00)
    phi_omega_bear = 0.75 if is_lrfd else (1/2.00)
    
    Design_Shear = Rn_shear * phi_omega_shear
    Design_Bear = Rn_bear * phi_omega_bear

    # ==========================================
    # 4. VISUALIZATION (Fit Check)
    # ==========================================
    st.divider()
    
    # Show Warnings first
    if warnings:
        for w in warnings:
            st.warning(w)
    else:
        st.success(f"✅ Geometry Check Passed! Plate fits within {section_data.get('name', 'Beam')}.")

    c_draw, c_calc = st.columns([1, 1.3])
    
    with c_draw:
        st.subheader("📐 Connection Detail")
        fig = go.Figure()
        
        # --- DRAW BEAM LIMITS (The Fit Check) ---
        # 0,0 is center of bolt group vertically
        # Plate Top = plate_h/2, Plate Bottom = -plate_h/2
        
        beam_top = h_beam/2
        beam_bot = -h_beam/2
        flange_thick = tf_beam
        
        # 1. Draw Beam Flanges (Limits)
        # Top Flange
        fig.add_shape(type="rect", x0=-50, y0=beam_top - flange_thick, x1=plate_w+50, y1=beam_top,
                      fillcolor="#71717a", line_color="black", opacity=0.5)
        fig.add_annotation(x=plate_w/2, y=beam_top - flange_thick/2, text="Top Flange", showarrow=False, font=dict(color="white", size=10))

        # Bottom Flange
        fig.add_shape(type="rect", x0=-50, y0=beam_bot, x1=plate_w+50, y1=beam_bot + flange_thick,
                      fillcolor="#71717a", line_color="black", opacity=0.5)
        fig.add_annotation(x=plate_w/2, y=beam_bot + flange_thick/2, text="Bot Flange", showarrow=False, font=dict(color="white", size=10))

        # 2. Draw Support (Left Side)
        support_col = "#8e44ad" if is_beam_to_beam else "#2c3e50"
        fig.add_shape(type="rect", x0=-40, y0=beam_bot-20, x1=0, y1=beam_top+20, fillcolor=support_col, line_color="black")
        
        # 3. Draw Plate
        # Center the plate vertically
        p_top = plate_h/2
        p_bot = -plate_h/2
        
        # Check collision for color
        plate_color = "rgba(239, 68, 68, 0.6)" if fit_status == "CLASH" else "rgba(41, 128, 185, 0.4)"
        
        fig.add_shape(type="rect", x0=0, y0=p_bot, x1=plate_w, y1=p_top, fillcolor=plate_color, line_color="#2980b9")
        
        # 4. Draw Bolts
        # Recalculate coordinates relative to center (0,0)
        start_y = p_top - l_edge_v
        start_x = e1_mm
        
        for r in range(n_rows):
            for c in range(n_cols):
                bx = start_x + c*s_h
                by = start_y - r*s_v
                fig.add_trace(go.Scatter(x=[bx], y=[by], mode='markers', marker=dict(size=10, color='#c0392b')))

        # Set Layout
        # Ensure aspect ratio is roughly equal so it looks real
        max_dim = max(h_beam, plate_w + 50)
        fig.update_layout(
            height=400, 
            margin=dict(l=10,r=10,t=20,b=20),
            xaxis=dict(visible=False, range=[-50, max_dim]),
            yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Gray Areas = Beam Flanges (Do not overlap!)")

    with c_calc:
        st.subheader("📝 Calculation Report")
        
        # 1. Fit & Geometry Status
        fit_icon = "✅" if fit_status == "OK" else "❌"
        with st.expander(f"1. Geometry & Fit Check {fit_icon}", expanded=True):
            st.write(f"**Beam Height (h):** {h_beam} mm")
            st.write(f"**Clear Web Height:** {clear_web_h:.1f} mm (Available)")
            st.write(f"**Plate Height:** {plate_h:.1f} mm (Required)")
            
            if fit_status == "CLASH":
                st.error(f"OVERLAP: {plate_h - clear_web_h:.1f} mm")
            else:
                st.write(f"**Clearance:** {(clear_web_h - plate_h)/2:.1f} mm (Top/Bottom)")
                
            st.markdown("---")
            st.markdown(f"**Pitch Check (Sv):** {s_v} mm " + ("✅" if s_v >= 3*d_mm else "⚠️ Low"))
            st.markdown(f"**Edge Check (Lv):** {l_edge_v} mm " + ("✅" if l_edge_v >= 1.5*d_mm else "⚠️ Low"))

        # 2. Shear Check
        pass_s = (V_res * n_total) <= Design_Shear
        with st.expander(f"2. Bolt Shear {'✅' if pass_s else '❌'}", expanded=True):
            st.metric("Design Capacity", f"{Design_Shear:,.0f} kg")
            st.metric("Bolt Force (Res)", f"{V_res * n_total:,.0f} kg")
            st.progress(min(1.0, (V_res * n_total)/Design_Shear))

        # 3. Bearing Check
        pass_b = V_design <= Design_Bear
        with st.expander(f"3. Plate Bearing {'✅' if pass_b else '❌'}", expanded=True):
             st.metric("Bearing Capacity", f"{Design_Bear:,.0f} kg")
             st.metric("Demand", f"{V_design:,.0f} kg")

    return n_total, Design_Shear

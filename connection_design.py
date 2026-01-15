import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    # ==========================================
    # 1. SETUP & CONSTANTS
    # ==========================================
    is_double_shear = "Double" in conn_type
    shear_planes = 2.0 if is_double_shear else 1.0
    is_beam_to_beam = "Beam to Beam" in conn_type
    
    # Bolt Properties
    d_mm = int(bolt_size[1:]) 
    d_cm = d_mm / 10
    Ab = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}.get(bolt_size, 3.14)
    
    # Beam Geometry
    h_beam = float(section_data.get('h', 300))
    tf_beam = float(section_data.get('tf', 10))
    tw_beam = float(section_data.get('tw', 8))
    clear_web_h = h_beam - 2*(tf_beam * 1.5) # Usable space

    # ==========================================
    # 2. INPUTS (LAYOUT IMPROVED)
    # ==========================================
    st.markdown(f"### 📐 Connection Design & Detailing: **{conn_type}**")

    # --- Suggestion Values ---
    min_pitch = 3 * d_mm
    min_edge = 1.5 * d_mm

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"**🔩 Bolt Config ({bolt_size})**")
        n_rows = st.number_input("Rows (Vertical)", 2, 12, 3)
        n_cols = st.number_input("Cols (Horizontal)", 1, 3, 1)
        s_v = st.number_input("Vert. Pitch (Sv)", 0.0, 300.0, float(max(75, min_pitch)))
        s_h = st.number_input("Horiz. Pitch (Sh)", 0.0, 150.0, float(max(50, min_pitch))) if n_cols > 1 else 0

    with col2:
        st.warning("**📏 Plate Geometry**")
        # --- NEW: CUSTOM PLATE SIZE LOGIC ---
        size_mode = st.radio("Plate Size Mode", ["Auto (Fit Bolts)", "Custom (Manual)"], horizontal=True)
        
        # Calculate Minimum Required Size based on bolts
        min_req_h = (n_rows - 1) * s_v + (2 * min_edge) # Minimum possible
        min_req_w_val = (n_cols - 1) * s_h + 2 * min_edge # Approx min width
        
        l_edge_v = st.number_input("Vert. Edge (Lv)", 0.0, 100.0, float(max(40, min_edge)))
        e1_mm = st.number_input("Gap from Support (e1)", 10.0, 200.0, 10.0) # Gap between plate edge and bolt
        
        # Auto-calculated dimensions based on edge inputs
        auto_h = (n_rows - 1) * s_v + (2 * l_edge_v)
        
        if size_mode == "Custom (Manual)":
            plate_h = st.number_input("Plate Height (H)", min_value=float(min_req_h), max_value=float(h_beam), value=float(auto_h))
            # For width, we define it roughly. Let's stick to standard margins for calculation
            # But let user define "Total Width" or "Side Margin"
            l_side = st.number_input("Side Margin (Ls)", 20.0, 100.0, 40.0)
            plate_w = e1_mm + (n_cols - 1) * s_h + l_side
        else:
            # Auto Mode
            plate_h = auto_h
            l_side = st.number_input("Side Margin (Ls)", 20.0, 100.0, 40.0)
            plate_w = e1_mm + (n_cols - 1) * s_h + l_side

    with col3:
        st.success("**🧱 Material & Weld**")
        t_plate_mm = st.number_input("Plate Thickness (t)", 6.0, 50.0, 10.0)
        # Check Custom Height Validity
        if plate_h < ((n_rows - 1) * s_v + 2*d_mm):
            st.error(f"❌ Plate Height {plate_h} is too small for bolts!")
        
        # Calculate actual vertical edge distance if Custom
        real_lv = (plate_h - (n_rows-1)*s_v) / 2
        
        st.write(f"**Actual Lv:** {real_lv:.1f} mm")
        st.caption(f"Min Req Lv: {min_edge:.1f} mm")

    # ==========================================
    # 3. GEOMETRY CHECK (FIT & CLASH)
    # ==========================================
    warnings = []
    fit_status = "OK"
    
    # Check if plate fits in beam web
    if plate_h > clear_web_h:
        fit_status = "CLASH"
        warnings.append(f"⛔ **Plate Clash:** Plate height ({plate_h} mm) hits beam flanges/fillet!")
    
    # Check if bolts fit in plate
    if real_lv < d_mm:
        warnings.append(f"⚠️ **Edge Distance Low:** Top/Bottom edge ({real_lv:.1f} mm) is too small.")

    # ==========================================
    # 4. CALCULATION LOGIC
    # ==========================================
    # Use real_lv for calculation
    n_total = n_rows * n_cols
    
    # Eccentricity
    e_total_cm = (e1_mm + (n_cols-1)*s_h/2) / 10
    
    # Inertia
    y_coords = [(r - (n_rows-1)/2) * (s_v/10) for r in range(n_rows)]
    x_coords = [(c - (n_cols-1)/2) * (s_h/10) for c in range(n_cols)]
    Ip = (sum([y**2 for y in y_coords]) * n_cols) + (sum([x**2 for x in x_coords]) * n_rows)
    
    V_dir = V_design / n_total
    V_ecc_x = (V_design * e_total_cm * max([abs(y) for y in y_coords])) / Ip if Ip > 0 else 0
    V_ecc_y = (V_design * e_total_cm * max([abs(x) for x in x_coords])) / Ip if Ip > 0 else 0
    V_res = math.sqrt((V_dir + V_ecc_y)**2 + V_ecc_x**2)

    # Capacities
    bolt_db = {"Grade 8.8 (Standard)": 4000, "A325 (High Strength)": 4780, "A490 (Premium)": 6200}
    Fnv = 3200 if "8.8" in bolt_grade and "N" in bolt_grade else bolt_db.get(bolt_grade.split(" (")[0], 3200)
    # Simplified logic for demo
    if "8.8" in bolt_grade: Fnv = 3200
    elif "A325" in bolt_grade: Fnv = 3795
    
    Rn_shear = n_total * Fnv * Ab * shear_planes
    
    # Bearing Check
    t_crit_cm = min(t_plate_mm/10, tw_beam/10)
    dh_cm = (d_mm + 2) / 10
    lc_edge = (real_lv/10) - (dh_cm/2)
    lc_inner = (s_v/10) - dh_cm
    
    Rn_bear_unit_edge = max(0, min(1.2*lc_edge*t_crit_cm*4000, 2.4*d_cm*t_crit_cm*4000))
    Rn_bear_unit_inner = max(0, min(1.2*lc_inner*t_crit_cm*4000, 2.4*d_cm*t_crit_cm*4000))
    
    if n_rows > 2:
        Rn_bear = (n_cols * 2 * Rn_bear_unit_edge) + (n_cols * (n_rows-2) * Rn_bear_unit_inner)
    else:
        Rn_bear = n_total * Rn_bear_unit_edge

    # Factors
    phi = 0.75 if is_lrfd else (1/2.00)
    Design_Shear = Rn_shear * phi
    Design_Bear = Rn_bear * phi

    # ==========================================
    # 5. VISUALIZATION (ANNOTATED DRAWING)
    # ==========================================
    st.divider()
    c_draw, c_calc = st.columns([1.5, 1]) # ให้พื้นที่รูปเยอะขึ้น
    
    with c_draw:
        st.subheader("📐 Shop Drawing & Dimensions")
        fig = go.Figure()
        
        # --- Coordinates ---
        beam_top = h_beam/2
        beam_bot = -h_beam/2
        plate_top = plate_h/2
        plate_bot = -plate_h/2
        
        # 1. BEAM FLANGES (Limits)
        fig.add_shape(type="rect", x0=-20, y0=beam_top-tf_beam, x1=plate_w+40, y1=beam_top, fillcolor="#71717a", line_width=0, opacity=0.3)
        fig.add_shape(type="rect", x0=-20, y0=beam_bot, x1=plate_w+40, y1=beam_bot+tf_beam, fillcolor="#71717a", line_width=0, opacity=0.3)
        
        # Label Beam
        fig.add_annotation(x=plate_w/2, y=beam_top-tf_beam/2, text="Top Flange", showarrow=False, font=dict(size=10, color="white"))
        
        # 2. SUPPORT COLUMN/GIRDER
        supp_col = "#6b21a8" if is_beam_to_beam else "#1e293b"
        fig.add_shape(type="rect", x0=-30, y0=beam_bot-10, x1=0, y1=beam_top+10, fillcolor=supp_col, line_color="black")
        fig.add_annotation(x=-15, y=0, text="Support", textangle=-90, showarrow=False, font=dict(color="white"))

        # 3. PLATE
        p_color = "rgba(239, 68, 68, 0.5)" if fit_status == "CLASH" else "rgba(59, 130, 246, 0.3)"
        p_line = "#dc2626" if fit_status == "CLASH" else "#2563eb"
        fig.add_shape(type="rect", x0=0, y0=plate_bot, x1=plate_w, y1=plate_top, fillcolor=p_color, line=dict(color=p_line, width=2))
        
        # 4. BOLTS & DIMENSIONS
        bolt_x_start = e1_mm
        bolt_y_start = plate_top - real_lv
        
        # Draw Bolts
        for r in range(n_rows):
            for c in range(n_cols):
                bx = bolt_x_start + c*s_h
                by = bolt_y_start - r*s_v
                fig.add_trace(go.Scatter(x=[bx], y=[by], mode='markers', marker=dict(size=8, color='#b91c1c', line=dict(width=1, color='white')), showlegend=False))

        # --- SMART DIMENSIONS (ANNOTATIONS) ---
        
        # A. Plate Height Dimension (Right Side)
        fig.add_shape(type="line", x0=plate_w+10, y0=plate_bot, x1=plate_w+10, y1=plate_top, line=dict(color="black", width=1))
        # Arrow heads (manual simulation or use annotation)
        fig.add_annotation(x=plate_w+10, y=0, text=f"H = {plate_h:.0f}", showarrow=False, xanchor="left", font=dict(size=12, color="blue"))
        fig.add_annotation(x=plate_w+10, y=plate_top, ax=0, ay=5, arrowcolor="black", arrowsize=1, arrowwidth=1)
        fig.add_annotation(x=plate_w+10, y=plate_bot, ax=0, ay=-5, arrowcolor="black", arrowsize=1, arrowwidth=1)

        # B. Pitch Dimension (Between first two rows)
        if n_rows > 1:
            mid_x = bolt_x_start
            y1 = bolt_y_start
            y2 = bolt_y_start - s_v
            fig.add_annotation(x=mid_x - 15, y=(y1+y2)/2, text=f"{s_v:.0f}", showarrow=False, font=dict(size=10, color="red"))
            # Small dimension line
            fig.add_shape(type="line", x0=mid_x-5, y0=y1, x1=mid_x-5, y1=y2, line=dict(color="red", width=1))

        # C. Edge Distance (Top)
        fig.add_annotation(x=bolt_x_start + 15, y=plate_top - real_lv/2, text=f"Lv={real_lv:.0f}", showarrow=False, font=dict(size=10, color="green"))
        
        # D. Width Dimension (Bottom)
        fig.add_shape(type="line", x0=0, y0=plate_bot-10, x1=plate_w, y1=plate_bot-10, line=dict(color="black", width=1))
        fig.add_annotation(x=plate_w/2, y=plate_bot-20, text=f"W = {plate_w:.0f}", showarrow=False, font=dict(size=12, color="blue"))

        # E. Clash Warning on Drawing
        if fit_status == "CLASH":
            fig.add_annotation(x=plate_w/2, y=0, text="❌ CLASH!", showarrow=False, font=dict(size=20, color="red", weight="bold"), bgcolor="rgba(255,255,255,0.8)")

        # Update Layout
        max_h = max(h_beam, plate_h) + 50
        max_w = max(plate_w, 150) + 50
        fig.update_layout(
            height=450,
            xaxis=dict(visible=False, range=[-40, max_w], fixedrange=True),
            yaxis=dict(visible=False, range=[-max_h/2, max_h/2], scaleanchor="x", scaleratio=1, fixedrange=True),
            margin=dict(l=0, r=0, t=10, b=10),
            paper_bgcolor="white",
            plot_bgcolor="white"
        )
        st.plotly_chart(fig, use_container_width=True)

    with c_calc:
        st.subheader("📝 Check Results")
        
        # Status Box
        if fit_status == "OK":
            st.success("✅ Geometry OK: Plate fits within beam.")
        else:
            st.error("❌ Geometry Fail: Plate is too large for the beam web.")
        
        # Check List
        with st.expander("Capacity Checks", expanded=True):
            # Shear
            ratio_s = (V_res * n_total) / Design_Shear
            st.write(f"**Bolt Shear:** {ratio_s:.2f}")
            st.progress(min(1.0, ratio_s))
            if ratio_s > 1.0: st.error("Shear Failed")
            
            # Bearing
            ratio_b = V_design / Design_Bear
            st.write(f"**Plate Bearing:** {ratio_b:.2f}")
            st.progress(min(1.0, ratio_b))
            if ratio_b > 1.0: st.error("Bearing Failed")
            
        st.caption(f"Design Load: {V_design:,.0f} kg")

    return n_total, Design_Shear

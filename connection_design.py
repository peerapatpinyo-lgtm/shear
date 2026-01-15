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
    
    d_mm = int(bolt_size[1:]) 
    d_cm = d_mm / 10
    Ab = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}.get(bolt_size, 3.14)
    
    h_beam = float(section_data.get('h', 300))
    tf_beam = float(section_data.get('tf', 10))
    tw_beam = float(section_data.get('tw', 8))
    clear_web_h = h_beam - 2*(tf_beam * 1.5) 

    # ==========================================
    # 2. INPUTS
    # ==========================================
    st.markdown(f"### 📐 Connection Design: **{conn_type}**")

    min_pitch = 3 * d_mm
    min_edge = 1.5 * d_mm

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"**🔩 Bolt Config ({bolt_size})**")
        n_rows = st.number_input("Rows (V)", 2, 12, 3)
        n_cols = st.number_input("Cols (H)", 1, 3, 2)
        s_v = st.number_input("Vert. Pitch (sv)", 0.0, 300.0, float(max(75, min_pitch)))
        s_h = st.number_input("Horiz. Pitch (sh)", 0.0, 150.0, float(max(60, min_pitch))) if n_cols > 1 else 0

    with col2:
        st.warning("**📏 Plate Geometry**")
        size_mode = st.radio("Size Mode", ["Auto", "Custom"], horizontal=True, label_visibility="collapsed")
        
        min_req_h = (n_rows - 1) * s_v + (2 * min_edge)
        l_edge_v_input = st.number_input("Vert. Edge Input (Lv)", 0.0, 100.0, float(max(40, min_edge)))
        e1_mm = st.number_input("Gap from Support (e1)", 10.0, 200.0, 50.0)
        
        auto_h = (n_rows - 1) * s_v + (2 * l_edge_v_input)
        
        if size_mode == "Custom":
            plate_h = st.number_input("Plate Height (H)", min_value=float(min_req_h), max_value=float(h_beam), value=float(auto_h))
            l_side = st.number_input("Side Margin (Ls)", 20.0, 100.0, 40.0)
        else:
            plate_h = auto_h
            l_side = st.number_input("Side Margin (Ls)", 20.0, 100.0, 40.0)

    with col3:
        st.success("**🧱 Material**")
        t_plate_mm = st.number_input("Plate Thickness (t)", 6.0, 50.0, 10.0)
        
        # Calculate real dimensions used for drawing
        real_lv = (plate_h - (n_rows-1)*s_v) / 2
        plate_w = e1_mm + (n_cols - 1) * s_h + l_side
        
        st.write(f"**Actual Lv:** {real_lv:.1f} mm")
        st.write(f"**Total W:** {plate_w:.0f} mm")

    # ==========================================
    # 3. GEOMETRY CHECK
    # ==========================================
    fit_status = "OK"
    if plate_h > clear_web_h: fit_status = "CLASH"
    
    # ==========================================
    # 4. CALCULATION (Simplified)
    # ==========================================
    n_total = n_rows * n_cols
    # Eccentricity
    e_total_cm = (e1_mm + (n_cols-1)*s_h/2) / 10
    y_coords = [(r - (n_rows-1)/2) * (s_v/10) for r in range(n_rows)]
    x_coords = [(c - (n_cols-1)/2) * (s_h/10) for c in range(n_cols)]
    Ip = (sum([y**2 for y in y_coords]) * n_cols) + (sum([x**2 for x in x_coords]) * n_rows)
    
    V_dir = V_design / n_total
    if Ip == 0: V_ecc_x, V_ecc_y = 0, 0
    else:
        V_ecc_x = (V_design * e_total_cm * max([abs(y) for y in y_coords])) / Ip
        V_ecc_y = (V_design * e_total_cm * max([abs(x) for x in x_coords])) / Ip
    V_res = math.sqrt((V_dir + V_ecc_y)**2 + V_ecc_x**2)

    # Capacities
    Fnv = 3200 
    Rn_shear = n_total * Fnv * Ab * shear_planes
    
    t_crit_cm = min(t_plate_mm/10, tw_beam/10)
    dh_cm = (d_mm + 2) / 10
    lc_edge = (real_lv/10) - (dh_cm/2)
    lc_inner = (s_v/10) - dh_cm
    Rn_bear_unit_edge = max(0, min(1.2*lc_edge*t_crit_cm*4000, 2.4*d_cm*t_crit_cm*4000))
    Rn_bear_unit_inner = max(0, min(1.2*lc_inner*t_crit_cm*4000, 2.4*d_cm*t_crit_cm*4000))
    Rn_bear = (n_cols * 2 * Rn_bear_unit_edge) + (n_cols * (n_rows-2) * Rn_bear_unit_inner) if n_rows > 2 else n_total * Rn_bear_unit_edge

    phi = 0.75 if is_lrfd else (1/2.00)
    Design_Shear = Rn_shear * phi
    Design_Bear = Rn_bear * phi

    # ==========================================
    # 5. VISUALIZATION (FULL CLEAR DIMENSIONS)
    # ==========================================
    st.divider()
    c_draw, c_calc = st.columns([2, 1]) # เพิ่มพื้นที่รูปอีกนิด
    
    with c_draw:
        st.subheader("📐 Fully Dimensioned Drawing")
        fig = go.Figure()
        
        # --- Coordinates ---
        beam_top, beam_bot = h_beam/2, -h_beam/2
        plate_top, plate_bot = plate_h/2, -plate_h/2
        bolt_x_start = e1_mm
        bolt_y_start = plate_top - real_lv
        
        # 1. DRAW OBJECTS
        # Beam Flanges
        fig.add_shape(type="rect", x0=-50, y0=beam_top-tf_beam, x1=plate_w+60, y1=beam_top, fillcolor="#71717a", opacity=0.3, line_width=0)
        fig.add_shape(type="rect", x0=-50, y0=beam_bot, x1=plate_w+60, y1=beam_bot+tf_beam, fillcolor="#71717a", opacity=0.3, line_width=0)
        # Support
        supp_col = "#6b21a8" if is_beam_to_beam else "#1e293b"
        fig.add_shape(type="rect", x0=-40, y0=beam_bot-30, x1=0, y1=beam_top+30, fillcolor=supp_col, line_color="black", line_width=2)
        # Plate
        p_color = "rgba(239, 68, 68, 0.5)" if fit_status == "CLASH" else "rgba(59, 130, 246, 0.3)"
        fig.add_shape(type="rect", x0=0, y0=plate_bot, x1=plate_w, y1=plate_top, fillcolor=p_color, line=dict(color="#2563eb", width=2))
        # Bolts
        for r in range(n_rows):
            for c in range(n_cols):
                fig.add_trace(go.Scatter(x=[bolt_x_start + c*s_h], y=[bolt_y_start - r*s_v], mode='markers', marker=dict(size=9, color='#b91c1c', line=dict(width=1, color='white')), showlegend=False))

        # ==================================================
        # --- ENHANCED DIMENSION FUNCTION ---
        # ==================================================
        def add_dim_line(fig, x0, y0, x1, y1, text, color="black", offset=0, type="horiz", font_size=12, bold=False):
            """วาดเส้นบอกระยะแบบชัดเจน พร้อมพื้นหลังข้อความ"""
            arrow_len = 10
            arrow_wid = 1.2
            text_bg = "rgba(255, 255, 255, 0.95)" # พื้นหลังขาวจางๆ ให้อ่านง่าย
            font_weight = "bold" if bold else "normal"

            if type == "horiz":
                y_pos = y0 + offset
                # Extension lines (เส้นประช่วยบอกแนว)
                fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos, line=dict(color=color, width=0.5, dash="dot"))
                fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos, line=dict(color=color, width=0.5, dash="dot"))
                # Main line & Arrows
                fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=color, width=1.2))
                fig.add_annotation(x=x0, y=y_pos, ax=arrow_len, ay=0, arrowcolor=color, arrowwidth=arrow_wid, arrowhead=2, text="")
                fig.add_annotation(x=x1, y=y_pos, ax=-arrow_len, ay=0, arrowcolor=color, arrowwidth=arrow_wid, arrowhead=2, text="")
                # Text label
                fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=text, showarrow=False, yshift=12 if offset>0 else -12, 
                                   font=dict(color=color, size=font_size, weight=font_weight), bgcolor=text_bg)

            elif type == "vert":
                x_pos = x0 + offset
                # Extension lines
                fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos, y1=y0, line=dict(color=color, width=0.5, dash="dot"))
                fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos, y1=y1, line=dict(color=color, width=0.5, dash="dot"))
                # Main line & Arrows
                fig.add_shape(type="line", x0=x_pos, y0=y0, x1=x_pos, y1=y1, line=dict(color=color, width=1.2))
                fig.add_annotation(x=x_pos, y=y0, ax=0, ay=-arrow_len, arrowcolor=color, arrowwidth=arrow_wid, arrowhead=2, text="")
                fig.add_annotation(x=x_pos, y=y1, ax=0, ay=arrow_len, arrowcolor=color, arrowwidth=arrow_wid, arrowhead=2, text="")
                # Text label
                fig.add_annotation(x=x_pos, y=(y0+y1)/2, text=text, showarrow=False, xshift=18 if offset>0 else -18, 
                                   font=dict(color=color, size=font_size, weight=font_weight), textangle=-90, bgcolor=text_bg)

        # ==================================================
        # --- ADDING ALL DIMENSIONS (CLEAR & ORGANIZED) ---
        # ==================================================
        
        # --- 1. BEAM & SUPPORT DIMENSIONS (NEW! - Far Left) ---
        # Beam Height
        add_dim_line(fig, 0, beam_bot, 0, beam_top, f"h_beam = {h_beam:.0f}", color="black", offset=-60, type="vert", font_size=13, bold=True)
        # Support Face Label
        fig.add_annotation(x=0, y=beam_bot-40, text="SUPPORT FACE (X=0)", showarrow=False, font=dict(color="black", size=11, weight="bold"))
        fig.add_shape(type="line", x0=0, y0=beam_bot-30, x1=0, y1=beam_top+30, line=dict(color="black", width=2, dash="dashdot")) # เน้นแนวแกน 0

        # --- 2. PLATE HORIZONTAL DIMENSIONS ---
        # Top Tier 1: e1 (Gap) & sh (Pitch)
        off_h1 = 40 
        add_dim_line(fig, 0, plate_top, e1_mm, plate_top, f"e1={e1_mm:.0f}", color="#d97706", offset=off_h1, type="horiz")
        if n_cols > 1:
             last_bolt_x = bolt_x_start + (n_cols-1)*s_h
             add_dim_line(fig, bolt_x_start, plate_top, last_bolt_x, plate_top, f"({n_cols-1})@sh={s_h:.0f}", color="#c0392b", offset=off_h1, type="horiz")

        # Top Tier 2: Ls (Side Margin)
        off_h2 = 70
        last_bolt_x = bolt_x_start + (n_cols-1)*s_h
        add_dim_line(fig, last_bolt_x, plate_top, plate_w, plate_top, f"Ls={l_side:.0f}", color="#16a34a", offset=off_h2, type="horiz")

        # Bottom: Total Width
        add_dim_line(fig, 0, plate_bot, plate_w, plate_bot, f"W_plate = {plate_w:.0f}", color="#1e40af", offset=-40, type="horiz", font_size=14, bold=True)

        # --- 3. PLATE VERTICAL DIMENSIONS (Right Side) ---
        # Right Tier 1: Lv (Edge Dist)
        off_v1 = 40
        add_dim_line(fig, plate_w, plate_top, plate_w, bolt_y_start, f"Lv={real_lv:.0f}", color="#16a34a", offset=off_v1, type="vert")

        # Right Tier 2: sv (Pitch)
        if n_rows > 1:
             off_v2 = 70
             last_bolt_y = bolt_y_start - (n_rows-1)*s_v
             add_dim_line(fig, plate_w, bolt_y_start, plate_w, last_bolt_y, f"({n_rows-1})@sv={s_v:.0f}", color="#c0392b", offset=off_v2, type="vert")

        # Right Tier 3: Total Height
        off_v3 = 110
        add_dim_line(fig, plate_w, plate_top, plate_w, plate_bot, f"H_plate = {plate_h:.0f}", color="#1e40af", offset=off_v3, type="vert", font_size=14, bold=True)

        # --- Layout Adjustments ---
        max_h = max(h_beam, plate_h) + 150
        max_w = plate_w + 150
        fig.update_layout(
            height=600, # เพิ่มความสูงรูป
            xaxis=dict(visible=False, range=[-80, max_w], fixedrange=True), # ขยายแกน X ทางซ้ายรับ dimension คาน
            yaxis=dict(visible=False, range=[-max_h/2, max_h/2], scaleanchor="x", scaleratio=1, fixedrange=True),
            margin=dict(l=10, r=10, t=30, b=30),
            paper_bgcolor="white", plot_bgcolor="white"
        )
        st.plotly_chart(fig, use_container_width=True)

    with c_calc:
        st.subheader("📝 Check Results")
        if fit_status == "CLASH":
            st.error(f"❌ Plate Clash! (H={plate_h:.0f} > Clear={clear_web_h:.0f})")
        
        with st.expander("Analysis Results", expanded=True):
            st.metric("Bolt Shear Ratio", f"{(V_res*n_total)/Design_Shear:.2f}", delta_color="inverse" if (V_res*n_total)>Design_Shear else "normal")
            st.metric("Bearing Ratio", f"{V_design/Design_Bear:.2f}", delta_color="inverse" if V_design>Design_Bear else "normal")
            st.caption(f"Design Load: {V_design:,.0f} kg")

    return n_total, Design_Shear

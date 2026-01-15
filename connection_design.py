import streamlit as st
import math
import plotly.graph_objects as go

# ==========================================
# HELPER: DRAWING DIMENSIONS
# ==========================================
def add_dim_line(fig, x0, y0, x1, y1, text, color="black", offset=0, type="horiz", font_size=12, bold=False):
    """วาดเส้นบอกระยะ (ปรับให้เส้นหนาและชัด)"""
    arrow_len = 10 # หัวลูกศรใหญ่ขึ้น
    arrow_wid = 1.5
    text_bg = "rgba(255, 255, 255, 0.8)"
    font_weight = "bold" if bold else "normal"

    if type == "horiz":
        y_pos = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos, line=dict(color=color, width=0.5, dash="dot"))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos, line=dict(color=color, width=0.5, dash="dot"))
        fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=color, width=1.5))
        fig.add_annotation(x=x0, y=y_pos, ax=arrow_len, ay=0, arrowcolor=color, arrowwidth=arrow_wid, arrowhead=2, text="")
        fig.add_annotation(x=x1, y=y_pos, ax=-arrow_len, ay=0, arrowcolor=color, arrowwidth=arrow_wid, arrowhead=2, text="")
        fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=text, showarrow=False, yshift=15 if offset>=0 else -15, 
                            font=dict(color=color, size=font_size, weight=font_weight), bgcolor=text_bg)
    elif type == "vert":
        x_pos = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos, y1=y0, line=dict(color=color, width=0.5, dash="dot"))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos, y1=y1, line=dict(color=color, width=0.5, dash="dot"))
        fig.add_shape(type="line", x0=x_pos, y0=y0, x1=x_pos, y1=y1, line=dict(color=color, width=1.5))
        fig.add_annotation(x=x_pos, y=y0, ax=0, ay=-arrow_len, arrowcolor=color, arrowwidth=arrow_wid, arrowhead=2, text="")
        fig.add_annotation(x=x_pos, y=y1, ax=0, ay=arrow_len, arrowcolor=color, arrowwidth=arrow_wid, arrowhead=2, text="")
        fig.add_annotation(x=x_pos, y=(y0+y1)/2, text=text, showarrow=False, xshift=15 if offset>=0 else -15, 
                            font=dict(color=color, size=font_size, weight=font_weight), textangle=-90, bgcolor=text_bg)

# ==========================================
# MAIN FUNCTION
# ==========================================
def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    # 1. SETUP
    is_beam_to_beam = "Beam to Beam" in conn_type
    d_mm = int(bolt_size[1:]) 
    
    # Secondary Beam Data
    h_beam = float(section_data.get('h', 300))
    b_beam = float(section_data.get('b', 150))
    tf_beam = float(section_data.get('tf', 10))
    tw_beam = float(section_data.get('tw', 8))

    # 2. INPUTS (Compact Layout)
    st.markdown(f"### 📐 Connection Design: **{conn_type}**")
    min_pitch, min_edge = 3 * d_mm, 1.5 * d_mm
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info(f"**🔩 Bolt Config ({bolt_size})**")
        n_rows = st.number_input("Rows (V)", 2, 12, 3)
        n_cols = st.number_input("Cols (H)", 1, 3, 2)
        s_v = st.number_input("Vert. Pitch (sv)", 0.0, 300.0, float(max(75, min_pitch)))
        s_h = st.number_input("Horiz. Pitch (sh)", 0.0, 150.0, float(max(60, min_pitch))) if n_cols > 1 else 0
    with c2:
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
            plate_h, l_side = auto_h, st.number_input("Side Margin (Ls)", 20.0, 100.0, 40.0)
    with c3:
        st.success("**🧱 Material**")
        t_plate_mm = st.number_input("Plate Thickness (t_pl)", 6.0, 50.0, 10.0)
        real_lv = (plate_h - (n_rows-1)*s_v) / 2
        plate_w = e1_mm + (n_cols - 1) * s_h + l_side

    # 3. CALCS & CHECK
    clear_web_h = h_beam - 2*(tf_beam * 1.5) 
    fit_status = "CLASH" if plate_h > clear_web_h else "OK"
    n_total = n_rows * n_cols
    V_res, Design_Shear, Design_Bear = V_design/n_total, 10000, 15000 

    # ==========================================
    # 5. VISUALIZATION (SMART SCALING)
    # ==========================================
    st.divider()
    st.subheader("📐 Structural Shop Drawings")
    
    col_sec, col_elev, col_res = st.columns([1.3, 1.3, 0.4])
    
    # Colors
    c_supp = "#475569"  # Support (Dark Slate)
    c_beam = "#e2e8f0"  # Beam (Light Gray)
    c_plate = "rgba(59, 130, 246, 0.8)" # Plate (Blue)
    c_bolt = "#b91c1c"  # Bolt (Red)

    # --- VIEW 1: SECTION A-A ---
    with col_sec:
        st.markdown("**SECTION A-A** (Cross Section)")
        fig_sec = go.Figure()
        
        # Coordinates Setup
        plate_x0, plate_x1 = 0, t_plate_mm
        beam_web_x0, beam_web_x1 = plate_x1, plate_x1 + tw_beam
        beam_center_x = (beam_web_x0 + beam_web_x1) / 2
        flange_x0, flange_x1 = beam_center_x - b_beam/2, beam_center_x + b_beam/2
        
        # === 1. DRAW SUPPORT ===
        supp_x_min = 0 # Track visuals boundary
        if is_beam_to_beam:
            # Main Girder (I-Shape)
            h_m, b_m = h_beam*1.2, b_beam*1.2
            tf_m, tw_m = tf_beam*1.2, max(tw_beam*1.2, 12) # Ensure visible thickness
            
            # Web
            fig_sec.add_shape(type="rect", x0=-tw_m, y0=-h_m/2+tf_m, x1=0, y1=h_m/2-tf_m, fillcolor=c_supp, line_color="black")
            # Flanges
            c_m = -tw_m/2
            fig_sec.add_shape(type="rect", x0=c_m-b_m/2, y0=h_m/2-tf_m, x1=c_m+b_m/2, y1=h_m/2, fillcolor=c_supp, line_color="black")
            fig_sec.add_shape(type="rect", x0=c_m-b_m/2, y0=-h_m/2, x1=c_m+b_m/2, y1=-h_m/2+tf_m, fillcolor=c_supp, line_color="black")
            supp_x_min = c_m - b_m/2
            supp_label = "MAIN GIRDER"
        else:
            # Column (T-Shape)
            c_tf, c_tw = 20.0, 12.0 # Fixed visual size for clarity
            col_h = h_beam * 1.1
            # Flange
            fig_sec.add_shape(type="rect", x0=-c_tf, y0=-col_h/2, x1=0, y1=col_h/2, fillcolor=c_supp, line_color="black")
            # Web
            fig_sec.add_shape(type="rect", x0=-c_tf-60, y0=-c_tw/2, x1=-c_tf, y1=c_tw/2, fillcolor="#64748b", line=dict(color="black", dash="dot"))
            supp_x_min = -c_tf - 60
            supp_label = "COLUMN FLANGE"

        # === 2. BEAM & PLATE ===
        # Plate
        fig_sec.add_shape(type="rect", x0=plate_x0, y0=-plate_h/2, x1=plate_x1, y1=plate_h/2, fillcolor=c_plate, line_color="black")
        # Beam Web (Secondary)
        fig_sec.add_shape(type="rect", x0=beam_web_x0, y0=-h_beam/2 + tf_beam, x1=beam_web_x1, y1=h_beam/2 - tf_beam, fillcolor=c_beam, line_color="black")
        # Beam Flanges
        fig_sec.add_shape(type="rect", x0=flange_x0, y0=h_beam/2 - tf_beam, x1=flange_x1, y1=h_beam/2, fillcolor="#cbd5e1", line_color="black")
        fig_sec.add_shape(type="rect", x0=flange_x0, y0=-h_beam/2, x1=flange_x1, y1=-h_beam/2 + tf_beam, fillcolor="#cbd5e1", line_color="black")

        # === 3. BOLTS ===
        bolt_y_start = plate_h/2 - real_lv
        for r in range(n_rows):
            by = bolt_y_start - r*s_v
            # Shank
            fig_sec.add_shape(type="rect", x0=plate_x0-5, y0=by-d_mm/2, x1=beam_web_x1+5, y1=by+d_mm/2, fillcolor=c_bolt, line_width=0)
            # Head/Nut
            fig_sec.add_shape(type="rect", x0=plate_x0-d_mm, y0=by-d_mm*0.8, x1=plate_x0, y1=by+d_mm*0.8, fillcolor="#7f1d1d", line_width=1)
            fig_sec.add_shape(type="rect", x0=beam_web_x1, y0=by-d_mm*0.8, x1=beam_web_x1+d_mm, y1=by+d_mm*0.8, fillcolor="#7f1d1d", line_width=1)
            # CL
            fig_sec.add_shape(type="line", x0=supp_x_min, y0=by, x1=flange_x1+20, y1=by, line=dict(color="black", width=0.5, dash="dashdot"))

        # === 4. DIMS & ZOOM LOGIC (KEY FIX) ===
        dim_y_top = h_beam/2 + 30
        add_dim_line(fig_sec, plate_x0, dim_y_top, plate_x1, dim_y_top, f"tpl", offset=15)
        add_dim_line(fig_sec, beam_web_x0, dim_y_top, beam_web_x1, dim_y_top, f"tw", offset=35)
        
        dim_x_right = flange_x1 + 30
        add_dim_line(fig_sec, dim_x_right, plate_h/2, dim_x_right, bolt_y_start, f"Lv", color="#16a34a", offset=0, type="vert")
        add_dim_line(fig_sec, dim_x_right, -h_beam/2, dim_x_right, h_beam/2, f"H={h_beam:.0f}", color="#1e40af", offset=60, type="vert", bold=True)
        
        # Label
        fig_sec.add_annotation(x=supp_x_min, y=-h_beam/2-20, text=supp_label, showarrow=False, xanchor="left", font=dict(weight="bold"))

        # *** SMART SCALE CALCULATION ***
        # หาขนาดสูงสุดของวัตถุในแนวตั้งและแนวนอน
        total_obj_h = h_beam * 1.4  # ความสูงเผื่อ dimension
        total_obj_w = (dim_x_right - supp_x_min) * 1.4 # ความกว้างเผื่อ dimension
        
        # ใช้ค่าที่มากที่สุดมาทำเป็น "กรอบสี่เหลี่ยมจัตุรัส" เพื่อให้ Scale 1:1 ไม่เพี้ยน
        max_dim = max(total_obj_h, total_obj_w) / 2 
        
        # Center Point ประมาณๆ ตรงกลางหน้าตัด
        center_x = (supp_x_min + dim_x_right) / 2
        center_y = 0
        
        fig_sec.update_layout(
            height=500,
            # Force scale 1:1
            yaxis=dict(range=[center_y - max_dim, center_y + max_dim], scaleanchor="x", scaleratio=1, visible=False),
            # Set X range explicitly to match the Y range aspect
            xaxis=dict(range=[center_x - max_dim, center_x + max_dim], visible=False),
            margin=dict(l=10, r=10, t=30, b=30),
            plot_bgcolor="white",
            title=dict(text="SECTION A-A", x=0.5),
            dragmode="pan" # Allow user to pan/zoom if needed
        )
        st.plotly_chart(fig_sec, use_container_width=True)

    # --- VIEW 2: ELEVATION ---
    with col_elev:
        st.markdown("**ELEVATION** (Side View)")
        fig_elev = go.Figure()
        
        beam_top, beam_bot = h_beam/2, -h_beam/2
        plate_top, plate_bot = plate_h/2, -plate_h/2
        bolt_x_start, bolt_y_start = e1_mm, plate_top - real_lv
        
        # Support
        fig_elev.add_shape(type="rect", x0=-40, y0=beam_bot-20, x1=0, y1=beam_top+20, fillcolor=c_supp, line_color="black")
        # Beam Ghost
        fig_elev.add_shape(type="rect", x0=0, y0=beam_top-tf_beam, x1=plate_w+50, y1=beam_top, fillcolor="#f1f5f9", line_width=0)
        fig_elev.add_shape(type="rect", x0=0, y0=beam_bot, x1=plate_w+50, y1=beam_bot+tf_beam, fillcolor="#f1f5f9", line_width=0)
        # Lines
        fig_elev.add_shape(type="line", x0=0, y0=beam_top, x1=plate_w+50, y1=beam_top, line=dict(color="black", width=1))
        fig_elev.add_shape(type="line", x0=0, y0=beam_bot, x1=plate_w+50, y1=beam_bot, line=dict(color="black", width=1))

        # Plate
        fig_elev.add_shape(type="rect", x0=0, y0=plate_bot, x1=plate_w, y1=plate_top, fillcolor=c_plate, line=dict(color="#1d4ed8", width=2))

        # Bolts
        for r in range(n_rows):
            for c in range(n_cols):
                bx, by = bolt_x_start + c*s_h, bolt_y_start - r*s_v
                fig_elev.add_trace(go.Scatter(x=[bx], y=[by], mode='markers', marker=dict(size=10, color=c_bolt, line=dict(width=1, color="black")), showlegend=False))
                # Crosshair
                fig_elev.add_shape(type="line", x0=bx-8, y0=by, x1=bx+8, y1=by, line=dict(color="black", width=0.5))
                fig_elev.add_shape(type="line", x0=bx, y0=by-8, x1=bx, y1=by+8, line=dict(color="black", width=0.5))

        # Dims
        add_dim_line(fig_elev, 0, plate_top, e1_mm, plate_top, "e1", color="#d97706", offset=25)
        if n_cols > 1: 
            add_dim_line(fig_elev, bolt_x_start, plate_top, bolt_x_start+(n_cols-1)*s_h, plate_top, f"{n_cols-1}@sh", color="#c0392b", offset=25)
        add_dim_line(fig_elev, 0, plate_bot, plate_w, plate_bot, f"W={plate_w:.0f}", color="#1e40af", offset=-25, bold=True)
        
        dim_x_R = plate_w + 25
        add_dim_line(fig_elev, dim_x_R, plate_top, dim_x_R, bolt_y_start, "Lv", color="#16a34a", type="vert")
        if n_rows > 1:
            add_dim_line(fig_elev, dim_x_R, bolt_y_start, dim_x_R, bolt_y_start-(n_rows-1)*s_v, f"{n_rows-1}@sv", color="#c0392b", offset=25, type="vert")
        add_dim_line(fig_elev, dim_x_R, plate_top, dim_x_R, plate_bot, f"H={plate_h:.0f}", color="#1e40af", offset=60, type="vert", bold=True)

        # Smart Scale for Elevation
        max_h_elev = h_beam * 1.2
        max_w_elev = (plate_w + 100)
        range_elev = max(max_h_elev, max_w_elev)/2
        center_x_elev = (plate_w)/2
        
        fig_elev.update_layout(
            height=500,
            yaxis=dict(range=[-range_elev, range_elev], scaleanchor="x", scaleratio=1, visible=False),
            xaxis=dict(range=[center_x_elev - range_elev, center_x_elev + range_elev], visible=False),
            margin=dict(l=10, r=10, t=30, b=30), plot_bgcolor="white", title=dict(text="ELEVATION VIEW", x=0.5)
        )
        st.plotly_chart(fig_elev, use_container_width=True)

    with col_res:
        st.subheader("📝 Check")
        if fit_status == "CLASH": st.error("❌ CLASH")
        else: st.success("✅ Geometry OK")
        st.metric("Bolt Shear", f"{(V_res*n_total)/Design_Shear:.2f}")
        st.metric("Bearing", f"{V_design/Design_Bear:.2f}")

    return n_total, Design_Shear

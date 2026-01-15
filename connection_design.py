import streamlit as st
import math
import plotly.graph_objects as go

# ==========================================
# HELPER: DRAWING DIMENSIONS
# ==========================================
def add_dim_line(fig, x0, y0, x1, y1, text, color="black", offset=0, type="horiz", font_size=12, bold=False):
    """วาดเส้นบอกระยะ Engineering Standard (รองรับ Offset และสี)"""
    arrow_len = 8
    arrow_wid = 1.0
    text_bg = "rgba(255, 255, 255, 0.95)" # พื้นหลังขาวทึบขึ้นนิดนึงเพื่อให้อ่านง่าย
    font_weight = "bold" if bold else "normal"

    if type == "horiz":
        y_pos = y0 + offset
        # เส้น Extension lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos, line=dict(color=color, width=0.5, dash="dot"))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos, line=dict(color=color, width=0.5, dash="dot"))
        # เส้น Dimension line
        fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=color, width=1.2))
        # หัวลูกศร
        fig.add_annotation(x=x0, y=y_pos, ax=arrow_len, ay=0, arrowcolor=color, arrowwidth=arrow_wid, arrowhead=2, text="")
        fig.add_annotation(x=x1, y=y_pos, ax=-arrow_len, ay=0, arrowcolor=color, arrowwidth=arrow_wid, arrowhead=2, text="")
        # ข้อความ
        fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=text, showarrow=False, yshift=12 if offset>=0 else -12, 
                            font=dict(color=color, size=font_size, weight=font_weight), bgcolor=text_bg)
    elif type == "vert":
        x_pos = x0 + offset
        # เส้น Extension lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos, y1=y0, line=dict(color=color, width=0.5, dash="dot"))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos, y1=y1, line=dict(color=color, width=0.5, dash="dot"))
        # เส้น Dimension line
        fig.add_shape(type="line", x0=x_pos, y0=y0, x1=x_pos, y1=y1, line=dict(color=color, width=1.2))
        # หัวลูกศร
        fig.add_annotation(x=x_pos, y=y0, ax=0, ay=-arrow_len, arrowcolor=color, arrowwidth=arrow_wid, arrowhead=2, text="")
        fig.add_annotation(x=x_pos, y=y1, ax=0, ay=arrow_len, arrowcolor=color, arrowwidth=arrow_wid, arrowhead=2, text="")
        # ข้อความ (หมุน 90 องศา)
        fig.add_annotation(x=x_pos, y=(y0+y1)/2, text=text, showarrow=False, xshift=18 if offset>=0 else -18, 
                            font=dict(color=color, size=font_size, weight=font_weight), textangle=-90, bgcolor=text_bg)

# ==========================================
# MAIN FUNCTION
# ==========================================
def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    # 1. SETUP
    is_beam_to_beam = "Beam to Beam" in conn_type
    
    d_mm = int(bolt_size[1:]) 
    d_cm = d_mm / 10
    
    # Beam Data
    h_beam = float(section_data.get('h', 300))
    b_beam = float(section_data.get('b', 150))
    tf_beam = float(section_data.get('tf', 10))
    tw_beam = float(section_data.get('tw', 8))
    clear_web_h = h_beam - 2*(tf_beam * 1.5) 

    # 2. INPUTS
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
        st.write(f"**Actual Lv:** {real_lv:.1f} mm")
        st.write(f"**Total W:** {plate_w:.0f} mm")

    # 3. GEOMETRY CHECK
    fit_status = "CLASH" if plate_h > clear_web_h else "OK"
    n_total = n_rows * n_cols
    V_res, Design_Shear, Design_Bear = V_design/n_total, 10000, 15000 # Dummy calc

    # ==========================================
    # 5. VISUALIZATION (MATCHING STYLES)
    # ==========================================
    st.divider()
    st.subheader("📐 Structural Shop Drawings")
    
    col_sec, col_elev, col_res = st.columns([1.1, 1.1, 0.8])
    supp_col = "#334155"
    
    # --- VIEW 1: SECTION A-A (With Matching Dims) ---
    with col_sec:
        st.markdown("**SECTION A-A** (Cross Section)")
        fig_sec = go.Figure()
        
        # Coordinates
        supp_width = 40
        plate_x0, plate_x1 = 0, t_plate_mm
        beam_web_x0, beam_web_x1 = plate_x1, plate_x1 + tw_beam
        beam_center_x = (beam_web_x0 + beam_web_x1) / 2
        flange_x0, flange_x1 = beam_center_x - b_beam/2, beam_center_x + b_beam/2
        
        # Draw Parts
        fig_sec.add_shape(type="rect", x0=-supp_width, y0=-h_beam/2 - 50, x1=0, y1=h_beam/2 + 50, fillcolor=supp_col, line_color="black") # Support
        fig_sec.add_shape(type="rect", x0=plate_x0, y0=-plate_h/2, x1=plate_x1, y1=plate_h/2, fillcolor="#3b82f6", line_color="black", opacity=0.9) # Plate
        fig_sec.add_shape(type="rect", x0=beam_web_x0, y0=-h_beam/2 + tf_beam, x1=beam_web_x1, y1=h_beam/2 - tf_beam, fillcolor="#d4d4d8", line_color="black") # Web
        fig_sec.add_shape(type="rect", x0=flange_x0, y0=h_beam/2 - tf_beam, x1=flange_x1, y1=h_beam/2, fillcolor="#a1a1aa", line_color="black") # Top Flange
        fig_sec.add_shape(type="rect", x0=flange_x0, y0=-h_beam/2, x1=flange_x1, y1=-h_beam/2 + tf_beam, fillcolor="#a1a1aa", line_color="black") # Bot Flange

        # Bolts & Weld
        bolt_y_start_coord = plate_h/2 - real_lv
        for r in range(n_rows):
            by = bolt_y_start_coord - r*s_v
            fig_sec.add_shape(type="rect", x0=plate_x0-5, y0=by-d_mm/2, x1=beam_web_x1+5, y1=by+d_mm/2, fillcolor="#b91c1c", line_width=0)
            fig_sec.add_shape(type="rect", x0=plate_x0 - d_mm*0.6, y0=by-d_mm*0.8, x1=plate_x0, y1=by+d_mm*0.8, fillcolor="#7f1d1d", line_color="black")
            fig_sec.add_shape(type="rect", x0=beam_web_x1, y0=by-d_mm*0.8, x1=beam_web_x1 + d_mm*0.8, y1=by+d_mm*0.8, fillcolor="#7f1d1d", line_color="black")
            fig_sec.add_shape(type="line", x0=-20, y0=by, x1=flange_x1+20, y1=by, line=dict(color="black", width=0.5, dash="dashdot"))

        # --- DIMENSIONS (MATCHING STYLE) ---
        # 1. Horizontal (Thickness) - Top side
        dim_y_top = h_beam/2 + 20
        add_dim_line(fig_sec, plate_x0, dim_y_top, plate_x1, dim_y_top, f"t={t_plate_mm:.0f}", color="black", offset=20, type="horiz")
        add_dim_line(fig_sec, beam_web_x0, dim_y_top, beam_web_x1, dim_y_top, f"tw={tw_beam:.0f}", color="black", offset=45, type="horiz")

        # 2. Vertical (Right Side of Flange) - Same logic as Elevation
        dim_x_anchor = flange_x1 + 10 # Start dimensions to the right of the beam flange
        
        # Level 1 (Green): Edge Distance (Lv)
        # Note: Lv is from Plate Top to First Bolt
        add_dim_line(fig_sec, dim_x_anchor, plate_h/2, dim_x_anchor, bolt_y_start_coord, f"Lv={real_lv:.0f}", color="#16a34a", offset=40, type="vert")
        
        # Level 2 (Red): Pitch (sv)
        if n_rows > 1:
            last_bolt_y = bolt_y_start_coord - (n_rows-1)*s_v
            add_dim_line(fig_sec, dim_x_anchor, bolt_y_start_coord, dim_x_anchor, last_bolt_y, f"{n_rows-1}@sv={s_v:.0f}", color="#c0392b", offset=70, type="vert")
            
        # Level 3 (Blue): Overall Beam Height (h)
        add_dim_line(fig_sec, dim_x_anchor, -h_beam/2, dim_x_anchor, h_beam/2, f"h_beam={h_beam:.0f}", color="#1e40af", offset=110, type="vert", bold=True)

        fig_sec.update_layout(
            height=550, 
            xaxis=dict(visible=False, fixedrange=True, range=[-40, flange_x1+150]), # ขยายแกน X ขวาให้พอสำหรับเส้น Dimension
            yaxis=dict(visible=False, scaleanchor="x", scaleratio=1, fixedrange=True),
            margin=dict(l=10, r=10, t=30, b=30), 
            plot_bgcolor="white", 
            title=dict(text="SECTION A-A", x=0.5, y=0.02)
        )
        st.plotly_chart(fig_sec, use_container_width=True)

    # --- VIEW 2: ELEVATION (ORIGINAL STYLE) ---
    with col_elev:
        st.markdown("**ELEVATION** (Side View)")
        fig_elev = go.Figure()
        
        beam_top, beam_bot = h_beam/2, -h_beam/2
        plate_top, plate_bot = plate_h/2, -plate_h/2
        bolt_x_start, bolt_y_start = e1_mm, plate_top - real_lv
        
        # Drawing Parts
        fig_elev.add_shape(type="rect", x0=-40, y0=beam_bot-20, x1=0, y1=beam_top+20, fillcolor=supp_col, line_color="black")
        fig_elev.add_shape(type="rect", x0=-20, y0=beam_top-tf_beam, x1=plate_w+50, y1=beam_top, fillcolor="#e4e4e7", opacity=0.5, line_width=0)
        fig_elev.add_shape(type="rect", x0=-20, y0=beam_bot, x1=plate_w+50, y1=beam_bot+tf_beam, fillcolor="#e4e4e7", opacity=0.5, line_width=0)
        fig_elev.add_shape(type="rect", x0=0, y0=plate_bot, x1=plate_w, y1=plate_top, fillcolor="rgba(59, 130, 246, 0.2)", line=dict(color="#2563eb", width=2))
        
        for r in range(n_rows):
            for c in range(n_cols):
                bx, by = bolt_x_start + c*s_h, bolt_y_start - r*s_v
                fig_elev.add_trace(go.Scatter(x=[bx], y=[by], mode='markers', marker=dict(size=9, color='#b91c1c'), showlegend=False))
                fig_elev.add_shape(type="line", x0=bx-6, y0=by, x1=bx+6, y1=by, line=dict(color="black", width=0.5))
                fig_elev.add_shape(type="line", x0=bx, y0=by-6, x1=bx, y1=by+6, line=dict(color="black", width=0.5))

        # --- DIMENSIONS (STANDARD) ---
        # Horizontal
        add_dim_line(fig_elev, 0, plate_top, e1_mm, plate_top, f"e1={e1_mm:.0f}", color="#d97706", offset=40, type="horiz")
        if n_cols > 1: add_dim_line(fig_elev, bolt_x_start, plate_top, bolt_x_start + (n_cols-1)*s_h, plate_top, f"{n_cols-1}@sh", color="#c0392b", offset=40, type="horiz")
        add_dim_line(fig_elev, 0, plate_bot, plate_w, plate_bot, f"W={plate_w:.0f}", color="#1e40af", offset=-40, type="horiz", bold=True)
        
        # Vertical
        add_dim_line(fig_elev, plate_w, plate_top, plate_w, bolt_y_start, f"Lv={real_lv:.0f}", color="#16a34a", offset=40, type="vert")
        if n_rows > 1: add_dim_line(fig_elev, plate_w, bolt_y_start, plate_w, bolt_y_start - (n_rows-1)*s_v, f"{n_rows-1}@sv", color="#c0392b", offset=70, type="vert")
        add_dim_line(fig_elev, plate_w, plate_top, plate_w, plate_bot, f"H_pl={plate_h:.0f}", color="#1e40af", offset=110, type="vert", bold=True)

        fig_elev.update_layout(height=550, xaxis=dict(visible=False, range=[-50, plate_w+120], fixedrange=True), yaxis=dict(visible=False, range=[-h_beam/2-50, h_beam/2+50], scaleanchor="x", scaleratio=1, fixedrange=True),
                            margin=dict(l=10, r=10, t=30, b=30), plot_bgcolor="white", title=dict(text="ELEVATION VIEW", x=0.5, y=0.02))
        st.plotly_chart(fig_elev, use_container_width=True)

    with col_res:
        st.subheader("📝 Check Results")
        if fit_status == "CLASH": st.error(f"❌ CLASH!")
        with st.expander("Ratio Check", expanded=True):
            st.metric("Bolt Shear", f"{(V_res*n_total)/Design_Shear:.2f}")
            st.metric("Bearing", f"{V_design/Design_Bear:.2f}")

    return n_total, Design_Shear

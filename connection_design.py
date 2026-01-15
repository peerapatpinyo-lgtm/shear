import streamlit as st
import math
import plotly.graph_objects as go

# ==========================================
# HELPER: DRAWING UTILS
# ==========================================
def add_dim_line(fig, x0, y0, x1, y1, text, color="black", offset=0, type="horiz", font_size=12, bold=False):
    """วาดเส้นบอกระยะ Dimension Line"""
    arrow_len = 8
    arrow_wid = 1.2
    text_bg = "rgba(255, 255, 255, 0.85)"
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

def create_ishape_polygon(h, b, tw, tf, r, cx=0, cy=0):
    """สร้าง Polygon จุดพิกัด (x, y) สำหรับรูปตัว I แบบมีมุมโค้ง (Fillet)"""
    # r = radius approximation (usually 1.5*tf for visuals)
    x_coords = []
    y_coords = []
    
    # Top Right Flange
    x_coords.extend([cx + tw/2 + r, cx + b/2,     cx + b/2,     cx + tw/2 + r]) # web-fillet start -> flange tip -> flange top -> top-web fillet
    y_coords.extend([cy + h/2 - tf, cy + h/2 - tf, cy + h/2,     cy + h/2])

    # Top Left Flange
    x_coords.extend([cx - tw/2 - r, cx - b/2,     cx - b/2,     cx - tw/2 - r])
    y_coords.extend([cy + h/2,     cy + h/2,     cy + h/2 - tf, cy + h/2 - tf])

    # Bottom Left Flange
    x_coords.extend([cx - tw/2 - r, cx - b/2,     cx - b/2,     cx - tw/2 - r])
    y_coords.extend([cy - h/2 + tf, cy - h/2 + tf, cy - h/2,     cy - h/2])

    # Bottom Right Flange
    x_coords.extend([cx + tw/2 + r, cx + b/2,     cx + b/2,     cx + tw/2 + r])
    y_coords.extend([cy - h/2,     cy - h/2,     cy - h/2 + tf, cy - h/2 + tf])
    
    # Close Loop manually for filling logic in Plotly usually works, 
    # but for accurate "I" shape with fillet, we need a continuous path.
    # Let's use a simplified path: TopFlange -> Web -> BotFlange
    
    # Re-generating ordered path (Clockwise)
    # 1. Top Right Corner
    X = [cx+tw/2, cx+tw/2+r, cx+b/2, cx+b/2, cx-b/2, cx-b/2, cx-tw/2-r, cx-tw/2] # Top part
    Y = [cy+h/2-tf-r, cy+h/2-tf, cy+h/2-tf, cy+h/2, cy+h/2, cy+h/2-tf, cy+h/2-tf, cy+h/2-tf-r]
    
    # 2. Web Down
    X.extend([cx-tw/2, cx-tw/2-r, cx-b/2, cx-b/2, cx+b/2, cx+b/2, cx+tw/2+r, cx+tw/2]) # Bottom part
    Y.extend([cy-h/2+tf+r, cy-h/2+tf, cy-h/2+tf, cy-h/2, cy-h/2, cy-h/2+tf, cy-h/2+tf, cy-h/2+tf+r])
    
    # Close
    X.append(X[0])
    Y.append(Y[0])
    
    return X, Y

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
    r_beam = tf_beam * 1.5 # Approximate fillet radius for visual

    # 2. INPUTS (Compact)
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
        plate_h = st.number_input("Plate Height (H)", min_value=float(min_req_h), max_value=float(h_beam), value=float(auto_h)) if size_mode == "Custom" else auto_h
        l_side = st.number_input("Side Margin (Ls)", 20.0, 100.0, 40.0)
    with c3:
        st.success("**🧱 Material**")
        t_plate_mm = st.number_input("Plate Thickness (t_pl)", 6.0, 50.0, 10.0)
        real_lv = (plate_h - (n_rows-1)*s_v) / 2
        plate_w = e1_mm + (n_cols - 1) * s_h + l_side

    # 3. CHECK
    clear_web_h = h_beam - 2*(tf_beam + r_beam) # Check against Fillet Start
    fit_status = "CLASH" if plate_h > clear_web_h else "OK"
    n_total = n_rows * n_cols
    V_res, Design_Shear, Design_Bear = V_design/n_total, 10000, 15000 

    # ==========================================
    # 5. VISUALIZATION (REALISTIC & CENTERED)
    # ==========================================
    st.divider()
    st.subheader("📐 Structural Shop Drawings")
    col_sec, col_elev, col_res = st.columns([1.3, 1.3, 0.4])
    
    c_supp, c_beam, c_plate, c_bolt = "#475569", "#cbd5e1", "rgba(59, 130, 246, 0.9)", "#b91c1c"

    # --- VIEW 1: SECTION A-A (Re-Centered) ---
    with col_sec:
        st.markdown("**SECTION A-A** (Cross Section)")
        fig_sec = go.Figure()
        
        # === NEW COORDINATE SYSTEM: BEAM CENTER = 0 ===
        # Secondary Beam is at X=0
        # Plate is attached to Web Left Side -> X = [-tw/2 - t_plate, -tw/2]
        # Support is at X < -tw/2 - t_plate
        
        beam_cx = 0
        plate_x1 = -tw_beam/2
        plate_x0 = plate_x1 - t_plate_mm
        
        # 1. DRAW BEAM (With Fillets)
        bx, by = create_ishape_polygon(h_beam, b_beam, tw_beam, tf_beam, r_beam, cx=beam_cx, cy=0)
        fig_sec.add_trace(go.Scatter(x=bx, y=by, fill="toself", fillcolor=c_beam, line=dict(color="black", width=1.5), showlegend=False, hoverinfo="skip"))
        
        # 2. DRAW PLATE
        fig_sec.add_shape(type="rect", x0=plate_x0, y0=-plate_h/2, x1=plate_x1, y1=plate_h/2, fillcolor=c_plate, line=dict(color="black", width=1.5))
        
        # 3. DRAW SUPPORT
        supp_x_min = -150 # Default boundary
        if is_beam_to_beam:
            # Support = Main Girder (Left Side)
            h_m, b_m = h_beam*1.2, b_beam*1.2
            tf_m, tw_m = tf_beam*1.2, max(tw_beam*1.2, 12)
            supp_face_x = plate_x0
            
            # Main Web (Left of Plate)
            fig_sec.add_shape(type="rect", x0=supp_face_x-tw_m, y0=-h_m/2+tf_m, x1=supp_face_x, y1=h_m/2-tf_m, fillcolor=c_supp, line_color="black")
            # Main Flanges
            c_m = supp_face_x - tw_m/2
            fig_sec.add_shape(type="rect", x0=c_m-b_m/2, y0=h_m/2-tf_m, x1=c_m+b_m/2, y1=h_m/2, fillcolor=c_supp, line_color="black")
            fig_sec.add_shape(type="rect", x0=c_m-b_m/2, y0=-h_m/2, x1=c_m+b_m/2, y1=-h_m/2+tf_m, fillcolor=c_supp, line_color="black")
            
            supp_label = "MAIN GIRDER"
            supp_x_min = c_m - b_m/2
        else:
            # Support = Column Flange
            col_tf = 20.0
            col_h = h_beam * 1.1
            supp_face_x = plate_x0
            
            # Flange
            fig_sec.add_shape(type="rect", x0=supp_face_x-col_tf, y0=-col_h/2, x1=supp_face_x, y1=col_h/2, fillcolor=c_supp, line_color="black")
            # Web
            fig_sec.add_shape(type="rect", x0=supp_face_x-col_tf-60, y0=-10, x1=supp_face_x-col_tf, y1=10, fillcolor="#64748b", line=dict(color="black", dash="dot"))
            
            supp_label = "COLUMN FLANGE"
            supp_x_min = supp_face_x - col_tf - 60

        # 4. DRAW BOLTS (High Detail)
        bolt_y_start = plate_h/2 - real_lv
        for r in range(n_rows):
            by = bolt_y_start - r*s_v
            # Shank (Through Plate + Web)
            fig_sec.add_shape(type="rect", x0=plate_x0-5, y0=by-d_mm/2, x1=tw_beam/2+5, y1=by+d_mm/2, fillcolor=c_bolt, line_width=0)
            # Head (Plate Side)
            fig_sec.add_shape(type="rect", x0=plate_x0-d_mm*0.8, y0=by-d_mm*0.8, x1=plate_x0, y1=by+d_mm*0.8, fillcolor="#7f1d1d", line_width=1)
            # Nut (Web Side)
            fig_sec.add_shape(type="rect", x0=tw_beam/2, y0=by-d_mm*0.8, x1=tw_beam/2+d_mm*0.8, y1=by+d_mm*0.8, fillcolor="#7f1d1d", line_width=1)
            # Centerline
            fig_sec.add_shape(type="line", x0=supp_x_min, y0=by, x1=b_beam/2+20, y1=by, line=dict(color="black", width=0.5, dash="dashdot"))

        # 5. DIMS & LABELS
        # Show "T" (Flat Web Height) to indicate K-area safety
        t_dist = h_beam - 2*(tf_beam+r_beam)
        fig_sec.add_shape(type="line", x0=0, y0=t_dist/2, x1=b_beam/2, y1=t_dist/2, line=dict(color="red", width=0.5, dash="dot"))
        fig_sec.add_shape(type="line", x0=0, y0=-t_dist/2, x1=b_beam/2, y1=-t_dist/2, line=dict(color="red", width=0.5, dash="dot"))
        
        dim_y_top = h_beam/2 + 25
        add_dim_line(fig_sec, plate_x0, dim_y_top, plate_x1, dim_y_top, f"tpl", offset=15)
        add_dim_line(fig_sec, -tw_beam/2, dim_y_top, tw_beam/2, dim_y_top, f"tw", offset=35)
        
        dim_x_R = b_beam/2 + 25
        add_dim_line(fig_sec, dim_x_R, plate_h/2, dim_x_R, bolt_y_start, "Lv", color="#16a34a", offset=0, type="vert")
        add_dim_line(fig_sec, dim_x_R, -h_beam/2, dim_x_R, h_beam/2, f"H={h_beam:.0f}", color="#1e40af", offset=60, type="vert", bold=True)
        
        # Labeling
        fig_sec.add_annotation(x=supp_x_min, y=-h_beam/2-20, text=supp_label, showarrow=False, xanchor="left", font=dict(weight="bold", color=c_supp))
        fig_sec.add_annotation(x=0, y=0, text="CL Beam", showarrow=False, font=dict(size=10, color="gray"), opacity=0.5)

        # Smart Scaling
        max_h = h_beam * 1.5
        max_w = (dim_x_R - supp_x_min) * 1.3
        limit = max(max_h, max_w) / 2
        center_x_view = (supp_x_min + dim_x_R)/2

        fig_sec.update_layout(
            height=500,
            yaxis=dict(range=[-limit, limit], scaleanchor="x", scaleratio=1, visible=False),
            xaxis=dict(range=[center_x_view - limit, center_x_view + limit], visible=False),
            margin=dict(l=10, r=10, t=30, b=30), plot_bgcolor="white", title=dict(text="SECTION A-A (Centered)", x=0.5), dragmode="pan"
        )
        st.plotly_chart(fig_sec, use_container_width=True)

    # --- VIEW 2: ELEVATION (Same logic, slightly cleaner) ---
    with col_elev:
        st.markdown("**ELEVATION** (Side View)")
        fig_elev = go.Figure()
        
        beam_top, beam_bot = h_beam/2, -h_beam/2
        plate_top, plate_bot = plate_h/2, -plate_h/2
        bolt_x_start, bolt_y_start = e1_mm, plate_top - real_lv
        
        # Support Block
        fig_elev.add_shape(type="rect", x0=-40, y0=beam_bot-20, x1=0, y1=beam_top+20, fillcolor=c_supp, line_color="black")
        
        # Beam (Ghosted) - show Fillet lines visually
        fig_elev.add_shape(type="rect", x0=0, y0=beam_bot, x1=plate_w+50, y1=beam_top, fillcolor="#f8fafc", line_width=0)
        # Flange Lines (Outer)
        fig_elev.add_shape(type="line", x0=0, y0=beam_top, x1=plate_w+50, y1=beam_top, line=dict(color="black", width=1))
        fig_elev.add_shape(type="line", x0=0, y0=beam_bot, x1=plate_w+50, y1=beam_bot, line=dict(color="black", width=1))
        # Fillet Lines (Inner K-area limit)
        k_line_top = beam_top - (tf_beam + r_beam)
        k_line_bot = beam_bot + (tf_beam + r_beam)
        fig_elev.add_shape(type="line", x0=0, y0=k_line_top, x1=plate_w+50, y1=k_line_top, line=dict(color="gray", width=0.5, dash="dot")) # K-line
        fig_elev.add_shape(type="line", x0=0, y0=k_line_bot, x1=plate_w+50, y1=k_line_bot, line=dict(color="gray", width=0.5, dash="dot")) # K-line
        
        # Plate
        fig_elev.add_shape(type="rect", x0=0, y0=plate_bot, x1=plate_w, y1=plate_top, fillcolor=c_plate, line=dict(color="#1d4ed8", width=1.5))

        # Bolts
        for r in range(n_rows):
            for c in range(n_cols):
                bx, by = bolt_x_start + c*s_h, bolt_y_start - r*s_v
                fig_elev.add_trace(go.Scatter(x=[bx], y=[by], mode='markers', marker=dict(size=9, color=c_bolt, line=dict(width=1, color="black")), showlegend=False))
                fig_elev.add_shape(type="line", x0=bx-6, y0=by, x1=bx+6, y1=by, line=dict(color="black", width=0.5))
                fig_elev.add_shape(type="line", x0=bx, y0=by-6, x1=bx, y1=by+6, line=dict(color="black", width=0.5))

        # Dims
        add_dim_line(fig_elev, 0, plate_top, e1_mm, plate_top, "e1", color="#d97706", offset=25)
        add_dim_line(fig_elev, 0, plate_bot, plate_w, plate_bot, f"W={plate_w:.0f}", color="#1e40af", offset=-25, bold=True)
        
        dim_x_R = plate_w + 25
        add_dim_line(fig_elev, dim_x_R, plate_top, dim_x_R, bolt_y_start, "Lv", color="#16a34a", type="vert")
        add_dim_line(fig_elev, dim_x_R, plate_top, dim_x_R, plate_bot, f"H={plate_h:.0f}", color="#1e40af", offset=60, type="vert", bold=True)

        # Smart Scale Elev
        limit_el = max(h_beam*1.2, plate_w+80) / 2
        cx_el = plate_w/2
        fig_elev.update_layout(
            height=500,
            yaxis=dict(range=[-limit_el, limit_el], scaleanchor="x", scaleratio=1, visible=False),
            xaxis=dict(range=[cx_el - limit_el, cx_el + limit_el], visible=False),
            margin=dict(l=10, r=10, t=30, b=30), plot_bgcolor="white", title=dict(text="ELEVATION VIEW", x=0.5)
        )
        st.plotly_chart(fig_elev, use_container_width=True)

    with col_res:
        st.subheader("📝 Check")
        if fit_status == "CLASH": 
            st.error("❌ CLASH: Plate Hits Fillet!")
            st.caption("Plate height exceeds flat web area (T).")
        else: 
            st.success("✅ Geometry OK")
        st.metric("Bolt Shear", f"{(V_res*n_total)/Design_Shear:.2f}")

    return n_total, Design_Shear

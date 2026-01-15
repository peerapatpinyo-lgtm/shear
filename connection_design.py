import streamlit as st
import math
import plotly.graph_objects as go

# ==========================================
# 1. HELPER: DRAWING UTILS
# ==========================================
def add_dim_line(fig, x0, y0, x1, y1, text, color="black", offset=0, type="horiz", font_size=12, bold=False):
    """วาดเส้น Dimension แบบปรับปรุงใหม่ให้ไม่บังกัน"""
    arrow_len = 8
    arrow_wid = 1.2
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

def create_ishape(h, b, tw, tf, r, cx=0, cy=0):
    """สร้าง Shape สำหรับ I-Beam (ใช้ list of dict เพื่อความชัวร์ในการ render)"""
    shapes = []
    # Web (Center)
    shapes.append(dict(type="rect", x0=cx-tw/2, y0=-h/2+tf, x1=cx+tw/2, y1=h/2-tf, fillcolor="#cbd5e1", line=dict(width=0)))
    # Top Flange
    shapes.append(dict(type="rect", x0=cx-b/2, y0=h/2-tf, x1=cx+b/2, y1=h/2, fillcolor="#cbd5e1", line=dict(color="black", width=1.5)))
    # Bottom Flange
    shapes.append(dict(type="rect", x0=cx-b/2, y0=-h/2, x1=cx+b/2, y1=-h/2+tf, fillcolor="#cbd5e1", line=dict(color="black", width=1.5)))
    # Web Vertical Lines (Bold) -> ช่วยให้เห็น Web ชัดขึ้นแม้ tw=1
    shapes.append(dict(type="line", x0=cx-tw/2, y0=-h/2+tf, x1=cx-tw/2, y1=h/2-tf, line=dict(color="black", width=2))) # Left Web
    shapes.append(dict(type="line", x0=cx+tw/2, y0=-h/2+tf, x1=cx+tw/2, y1=h/2-tf, line=dict(color="black", width=2))) # Right Web
    return shapes

# ==========================================
# MAIN FUNCTION
# ==========================================
def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    # 1. SETUP & INPUTS
    is_beam_to_beam = "Beam to Beam" in conn_type
    d_mm = int(bolt_size[1:]) 
    
    # Section Data (Handle extreme cases like tw=1)
    h_beam = float(section_data.get('h', 300))
    b_beam = float(section_data.get('b', 150))
    tf_beam = float(section_data.get('tf', 10))
    tw_beam = float(section_data.get('tw', 8)) 
    r_beam = tf_beam * 1.5 

    st.markdown(f"### 📐 Connection Design: **{conn_type}**")
    
    # Layout Inputs
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info(f"**🔩 Bolt Config ({bolt_size})**")
        n_rows = st.number_input("Rows (V)", 2, 12, 3)
        n_cols = st.number_input("Cols (H)", 1, 3, 2)
        s_v = st.number_input("Vert. Pitch (sv)", 0.0, 300.0, float(max(75, 3*d_mm)))
        s_h = st.number_input("Horiz. Pitch (sh)", 0.0, 150.0, float(max(60, 3*d_mm))) if n_cols > 1 else 0
    with c2:
        st.warning("**📏 Plate Geometry**")
        min_req_h = (n_rows - 1) * s_v + (2 * 1.5 * d_mm)
        l_edge_v_input = st.number_input("Vert. Edge Input (Lv)", 0.0, 100.0, 40.0)
        auto_h = (n_rows - 1) * s_v + (2 * l_edge_v_input)
        plate_h = st.number_input("Plate Height (H)", min_value=10.0, max_value=float(h_beam), value=float(auto_h))
        e1_mm = st.number_input("Gap (e1)", 10.0, 200.0, 50.0)
        l_side = st.number_input("Side Margin (Ls)", 20.0, 100.0, 40.0)
    with c3:
        st.success("**🧱 Material**")
        t_plate_mm = st.number_input("Plate Thickness (t_pl)", 6.0, 50.0, 10.0)
        plate_w = e1_mm + (n_cols - 1) * s_h + l_side
        real_lv = (plate_h - (n_rows-1)*s_v) / 2

    n_total = n_rows * n_cols
    
    # ==========================================
    # VISUALIZATION CONTROLS (THE FIX)
    # ==========================================
    st.divider()
    col_ctrl, _ = st.columns([0.5, 0.5])
    with col_ctrl:
        # Checkbox นี้คือพระเอก: ถ้าไม่ติ๊ก จะปล่อยสเกลให้ยืดหดตามจอ (เห็นชัด)
        # ถ้าติ๊ก จะล็อก 1:1 (สมจริงแต่เล็ก)
        use_true_scale = st.checkbox("🔒 Fix Aspect Ratio (1:1) - Uncheck to fit screen", value=False)

    col_sec, col_elev = st.columns([1, 1])
    
    # Colors
    c_supp = "#334155"
    c_plate = "rgba(59, 130, 246, 0.6)"
    c_bolt = "#b91c1c"

    # --- VIEW 1: SECTION A-A ---
    with col_sec:
        st.subheader("SECTION A-A")
        fig_sec = go.Figure()
        
        # Coordinates
        beam_cx = 0
        plate_x_right = -tw_beam/2 
        plate_x_left = plate_x_right - t_plate_mm
        
        # Draw Beam
        beam_shapes = create_ishape(h_beam, b_beam, tw_beam, tf_beam, r_beam, cx=beam_cx)
        for shape in beam_shapes: fig_sec.add_shape(shape)
            
        # Draw Plate
        fig_sec.add_shape(type="rect", x0=plate_x_left, y0=-plate_h/2, x1=plate_x_right, y1=plate_h/2, 
                          fillcolor=c_plate, line=dict(color="black", width=1.5))
        
        # Support
        supp_x_face = plate_x_left
        fig_sec.add_shape(type="rect", x0=supp_x_face-80, y0=-h_beam/1.8, x1=supp_x_face, y1=h_beam/1.8, 
                          fillcolor=c_supp, line=dict(color="black", width=1.5))
        
        # Bolts
        bolt_y_start = plate_h/2 - real_lv
        for r in range(n_rows):
            by = bolt_y_start - r*s_v
            # Shank
            fig_sec.add_shape(type="rect", x0=plate_x_left-5, y0=by-d_mm/2, x1=tw_beam/2+5, y1=by+d_mm/2, fillcolor=c_bolt, line_width=0)
            # Head/Nut
            fig_sec.add_shape(type="rect", x0=plate_x_left-d_mm, y0=by-d_mm*0.8, x1=plate_x_left, y1=by+d_mm*0.8, fillcolor="#7f1d1d", line_width=1)
            fig_sec.add_shape(type="rect", x0=tw_beam/2, y0=by-d_mm*0.8, x1=tw_beam/2+d_mm, y1=by+d_mm*0.8, fillcolor="#7f1d1d", line_width=1)
            # Centerline
            fig_sec.add_shape(type="line", x0=supp_x_face-10, y0=by, x1=b_beam/2+10, y1=by, line=dict(color="black", width=0.5, dash="dashdot"))

        # Dimensions
        dim_y = plate_h/2 + 30
        add_dim_line(fig_sec, plate_x_left, dim_y, plate_x_right, dim_y, f"tp={t_plate_mm:.0f}", offset=10)
        add_dim_line(fig_sec, -tw_beam/2, dim_y, tw_beam/2, dim_y, f"tw={tw_beam:.0f}", offset=25)
        
        dim_x_R = b_beam/2 + 20
        add_dim_line(fig_sec, dim_x_R, plate_h/2, dim_x_R, -plate_h/2, f"H_pl={plate_h:.0f}", color="blue", offset=10, type="vert")

        # ** LAYOUT CONFIG (THE FIX) **
        layout_args = dict(
            height=500,
            plot_bgcolor="white",
            margin=dict(l=10, r=10, t=40, b=10),
            dragmode="pan",
            title=dict(text="SECTION A-A", x=0.5)
        )
        
        # ถ้า True Scale: บังคับ aspect ratio = 1 (ภาพอาจจะเล็ก หรือ เป็นเส้น ถ้าค่าต่างกันมาก)
        # ถ้า False (Default): ปล่อยอิสระ แกน X ขยายเต็มที่ แกน Y ขยายเต็มที่ (เห็นชัดแน่นอน)
        if use_true_scale:
            limit_h = max(plate_h*1.2, h_beam*0.6)
            limit_w = max(b_beam*1.2, 200)
            layout_args['yaxis'] = dict(range=[-limit_h, limit_h], scaleanchor="x", scaleratio=1, visible=False)
            layout_args['xaxis'] = dict(range=[-limit_w/2, limit_w/2], visible=False)
        else:
            # Fit to View (Distorted but Visible)
            # ไม่ตั้ง range fix ให้ plotly auto-scale ให้เต็มกล่อง
            # ซ่อนแกนแต่ปล่อย range อิสระ
            layout_args['yaxis'] = dict(visible=False, fixedrange=False) # Allow zoom
            layout_args['xaxis'] = dict(visible=False, fixedrange=False) 

        fig_sec.update_layout(**layout_args)
        st.plotly_chart(fig_sec, use_container_width=True)

    # --- VIEW 2: ELEVATION ---
    with col_elev:
        st.subheader("ELEVATION VIEW")
        fig_elev = go.Figure()
        
        # Draw Objects
        beam_top, beam_bot = h_beam/2, -h_beam/2
        
        # Support
        fig_elev.add_shape(type="rect", x0=-40, y0=beam_bot-20, x1=0, y1=beam_top+20, fillcolor=c_supp, line_color="black")
        # Beam Lines
        fig_elev.add_shape(type="line", x0=0, y0=beam_top, x1=plate_w+50, y1=beam_top, line=dict(color="black", width=1))
        fig_elev.add_shape(type="line", x0=0, y0=beam_bot, x1=plate_w+50, y1=beam_bot, line=dict(color="black", width=1))
        fig_elev.add_shape(type="rect", x0=0, y0=beam_bot, x1=plate_w+50, y1=beam_top, fillcolor="#f8fafc", opacity=0.5, line_width=0)
        
        # Plate
        fig_elev.add_shape(type="rect", x0=0, y0=-plate_h/2, x1=plate_w, y1=plate_h/2, fillcolor=c_plate, line=dict(color="blue", width=1.5))
        
        # Bolts
        bolt_x_start, bolt_y_start = e1_mm, plate_h/2 - real_lv
        for r in range(n_rows):
            for c in range(n_cols):
                bx, by = bolt_x_start + c*s_h, bolt_y_start - r*s_v
                fig_elev.add_trace(go.Scatter(x=[bx], y=[by], mode='markers', marker=dict(size=10, color=c_bolt, line=dict(width=1, color="black")), showlegend=False))

        # Dims
        add_dim_line(fig_elev, 0, plate_h/2, plate_w, plate_h/2, f"W={plate_w:.0f}", color="blue", offset=15)
        add_dim_line(fig_elev, plate_w+20, plate_h/2, plate_w+20, -plate_h/2, f"H={plate_h:.0f}", color="blue", offset=0, type="vert")

        # Config Layout
        if use_true_scale:
             limit_el_h = max(plate_h*1.2, 200)
             limit_el_w = max(plate_w*1.5, 200)
             layout_args['yaxis'] = dict(range=[-limit_el_h, limit_el_h], scaleanchor="x", scaleratio=1, visible=False)
             layout_args['xaxis'] = dict(range=[-20, limit_el_w], visible=False)
        else:
             # Auto fit
             layout_args['yaxis'] = dict(visible=False, fixedrange=False)
             layout_args['xaxis'] = dict(visible=False, fixedrange=False)

        fig_elev.update_layout(**layout_args)
        st.plotly_chart(fig_elev, use_container_width=True)

    return n_total

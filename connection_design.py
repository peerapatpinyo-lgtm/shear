import streamlit as st
import math
import plotly.graph_objects as go

# ==========================================
# 1. HELPER FUNCTIONS
# ==========================================
def add_dim_line(fig, x0, y0, x1, y1, text, color="black", offset=0, type="horiz", font_size=12, bold=False):
    """ฟังก์ชันวาดเส้นบอกระยะ (Dimension Line) แบบมืออาชีพ"""
    arrow_len = 8
    arrow_wid = 1.2
    text_bg = "rgba(255, 255, 255, 0.9)"
    font_weight = "bold" if bold else "normal"

    # คำนวณตำแหน่งเส้น
    if type == "horiz":
        y_pos = y0 + offset
        # เส้นร่าง (Extension lines)
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos, line=dict(color=color, width=0.5, dash="dot"))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos, line=dict(color=color, width=0.5, dash="dot"))
        # เส้นหลัก (Dimension line)
        fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=color, width=1.5))
        # หัวลูกศร
        fig.add_annotation(x=x0, y=y_pos, ax=arrow_len, ay=0, arrowcolor=color, arrowwidth=arrow_wid, arrowhead=2, text="")
        fig.add_annotation(x=x1, y=y_pos, ax=-arrow_len, ay=0, arrowcolor=color, arrowwidth=arrow_wid, arrowhead=2, text="")
        # ตัวหนังสือ
        fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=text, showarrow=False, yshift=15 if offset>=0 else -15, 
                            font=dict(color=color, size=font_size, weight=font_weight), bgcolor=text_bg)
    elif type == "vert":
        x_pos = x0 + offset
        # เส้นร่าง
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos, y1=y0, line=dict(color=color, width=0.5, dash="dot"))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos, y1=y1, line=dict(color=color, width=0.5, dash="dot"))
        # เส้นหลัก
        fig.add_shape(type="line", x0=x_pos, y0=y0, x1=x_pos, y1=y1, line=dict(color=color, width=1.5))
        # หัวลูกศร
        fig.add_annotation(x=x_pos, y=y0, ax=0, ay=-arrow_len, arrowcolor=color, arrowwidth=arrow_wid, arrowhead=2, text="")
        fig.add_annotation(x=x_pos, y=y1, ax=0, ay=arrow_len, arrowcolor=color, arrowwidth=arrow_wid, arrowhead=2, text="")
        # ตัวหนังสือ
        fig.add_annotation(x=x_pos, y=(y0+y1)/2, text=text, showarrow=False, xshift=15 if offset>=0 else -15, 
                            font=dict(color=color, size=font_size, weight=font_weight), textangle=-90, bgcolor=text_bg)

def create_ishape(h, b, tw, tf, r, cx=0, cy=0):
    """สร้างพิกัดรูปตัว I แบบมี Fillet (มุมโค้ง)"""
    # Simplified logic for robust plotting
    # วาดแบบ Polygon 12 จุด (ไม่รวมส่วนโค้งละเอียดมาก เพื่อประสิทธิภาพ) แต่ให้เห็น Chamfer
    
    # 1. Web Center Rect
    # 2. Flanges
    # เพื่อความง่ายและไม่ error ใช้ Rectangles พื้นฐานแต่ซ้อนกันให้ดูเหมือนมี fillet หรือใช้ path
    # ในที่นี้ใช้วิธีวาด Polygon แบบ Manual coordinates
    
    X = [
        cx - tw/2, cx - b/2, cx - b/2, cx - tw/2, # Top Left Flange inside
        cx - tw/2, cx - b/2, cx - b/2, cx - tw/2, # Bottom Left Flange inside
        cx + tw/2, cx + b/2, cx + b/2, cx + tw/2, # Bottom Right
        cx + tw/2, cx + b/2, cx + b/2, cx + tw/2  # Top Right
    ]
    # ปรับปรุง: ใช้ Shape พื้นฐานวาดทับกันจะจัดการง่ายกว่าสำหรับ Plotly
    # คืนค่าเป็น list ของ dict shapes จะดีกว่า
    shapes = []
    # Web
    shapes.append(dict(type="rect", x0=cx-tw/2, y0=-h/2+tf, x1=cx+tw/2, y1=h/2-tf, fillcolor="#cbd5e1", line=dict(width=0)))
    # Top Flange
    shapes.append(dict(type="rect", x0=cx-b/2, y0=h/2-tf, x1=cx+b/2, y1=h/2, fillcolor="#cbd5e1", line=dict(color="black", width=1.5)))
    # Bottom Flange
    shapes.append(dict(type="rect", x0=cx-b/2, y0=-h/2, x1=cx+b/2, y1=-h/2+tf, fillcolor="#cbd5e1", line=dict(color="black", width=1.5)))
    # Web Lines (Vertical)
    shapes.append(dict(type="line", x0=cx-tw/2, y0=-h/2+tf, x1=cx-tw/2, y1=h/2-tf, line=dict(color="black", width=1.5)))
    shapes.append(dict(type="line", x0=cx+tw/2, y0=-h/2+tf, x1=cx+tw/2, y1=h/2-tf, line=dict(color="black", width=1.5)))
    
    return shapes

# ==========================================
# 2. MAIN RENDER FUNCTION
# ==========================================
def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    # --- SETUP PARAMETERS ---
    is_beam_to_beam = "Beam to Beam" in conn_type
    d_mm = int(bolt_size[1:]) 
    
    # Dimensions (Handle Default/Missing)
    h_beam = float(section_data.get('h', 300))
    b_beam = float(section_data.get('b', 150))
    tf_beam = float(section_data.get('tf', 10))
    tw_beam = float(section_data.get('tw', 8)) # User case: might be 1.0
    r_beam = tf_beam * 1.5 

    # --- UI INPUTS (Compact) ---
    st.markdown(f"### 📐 Connection Design: **{conn_type}**")
    min_pitch = 3 * d_mm
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info(f"**🔩 Bolt Config ({bolt_size})**")
        n_rows = st.number_input("Rows (V)", 2, 12, 3)
        n_cols = st.number_input("Cols (H)", 1, 3, 2)
        s_v = st.number_input("Vert. Pitch (sv)", 0.0, 300.0, float(max(75, min_pitch)))
        s_h = st.number_input("Horiz. Pitch (sh)", 0.0, 150.0, float(max(60, min_pitch))) if n_cols > 1 else 0
        
    with c2:
        st.warning("**📏 Plate Geometry**")
        l_edge_v_input = st.number_input("Vert. Edge Input (Lv)", 0.0, 100.0, 40.0)
        auto_h = (n_rows - 1) * s_v + (2 * l_edge_v_input)
        plate_h = st.number_input("Plate Height (H)", min_value=10.0, max_value=float(h_beam), value=float(auto_h))
        e1_mm = st.number_input("Gap from Support (e1)", 10.0, 200.0, 50.0)
        l_side = st.number_input("Side Margin (Ls)", 20.0, 100.0, 40.0)
        
    with c3:
        st.success("**🧱 Material**")
        t_plate_mm = st.number_input("Plate Thickness (t_pl)", 6.0, 50.0, 10.0)
        plate_w = e1_mm + (n_cols - 1) * s_h + l_side
        real_lv = (plate_h - (n_rows-1)*s_v) / 2

    # --- CALCS ---
    n_total = n_rows * n_cols
    # Simple Check
    fit_status = "OK" if plate_h <= (h_beam - 2*tf_beam) else "CLASH"
    
    # ==========================================
    # 3. DRAWING LOGIC (THE FIX)
    # ==========================================
    st.divider()
    col_sec, col_elev = st.columns([1, 1])
    
    # Colors
    c_supp = "#334155" # Dark Slate
    c_plate = "rgba(59, 130, 246, 0.7)" # Blue Translucent
    c_bolt = "#b91c1c" # Red
    
    # --- VIEW 1: SECTION A-A (SMART ZOOM) ---
    with col_sec:
        st.subheader("SECTION A-A")
        fig_sec = go.Figure()
        
        # 1. Define Coordinates (Beam Center at 0,0)
        beam_cx = 0
        plate_x_right = -tw_beam/2 # Plate touches web left face
        plate_x_left = plate_x_right - t_plate_mm
        
        # 2. Draw Beam (Use Helper Shapes)
        beam_shapes = create_ishape(h_beam, b_beam, tw_beam, tf_beam, r_beam, cx=beam_cx)
        for shape in beam_shapes:
            fig_sec.add_shape(shape)
            
        # 3. Draw Plate
        fig_sec.add_shape(type="rect", x0=plate_x_left, y0=-plate_h/2, x1=plate_x_right, y1=plate_h/2, 
                          fillcolor=c_plate, line=dict(color="black", width=1.5))
        
        # 4. Draw Support (Left Side)
        supp_x_face = plate_x_left
        supp_x_back = supp_x_face - 20 # Visual thickness
        supp_h_draw = h_beam * 1.1 
        
        # Support Block
        fig_sec.add_shape(type="rect", x0=supp_x_back-100, y0=-supp_h_draw/2, x1=supp_x_face, y1=supp_h_draw/2, 
                          fillcolor=c_supp, line=dict(color="black", width=1.5))
        
        # 5. Draw Bolts
        bolt_y_start = plate_h/2 - real_lv
        for r in range(n_rows):
            by = bolt_y_start - r*s_v
            # Shank
            fig_sec.add_shape(type="rect", x0=plate_x_left-5, y0=by-d_mm/2, x1=tw_beam/2+5, y1=by+d_mm/2, fillcolor=c_bolt, line_width=0)
            # Head (Plate side)
            fig_sec.add_shape(type="rect", x0=plate_x_left-d_mm, y0=by-d_mm, x1=plate_x_left, y1=by+d_mm, fillcolor="#7f1d1d", line_width=1)
            # Nut (Web side)
            fig_sec.add_shape(type="rect", x0=tw_beam/2, y0=by-d_mm, x1=tw_beam/2+d_mm, y1=by+d_mm, fillcolor="#7f1d1d", line_width=1)
            # Centerline
            fig_sec.add_shape(type="line", x0=supp_x_back-20, y0=by, x1=b_beam/2+20, y1=by, line=dict(color="black", width=0.5, dash="dashdot"))

        # 6. Dimensions
        dim_y_top = plate_h/2 + 40 # Place dims relative to PLATE, not BEAM HEIGHT
        add_dim_line(fig_sec, plate_x_left, dim_y_top, plate_x_right, dim_y_top, f"tpl={t_plate_mm:.0f}", offset=10)
        add_dim_line(fig_sec, -tw_beam/2, dim_y_top, tw_beam/2, dim_y_top, f"tw={tw_beam:.0f}", offset=25)
        
        dim_x_R = b_beam/2 + 30
        add_dim_line(fig_sec, dim_x_R, plate_h/2, dim_x_R, -plate_h/2, f"H_pl={plate_h:.0f}", color="blue", offset=20, type="vert")
        
        # *** KEY FIX: CAMERA ZOOM CONTROL ***
        # แทนที่จะใช้ h_beam เราจะใช้ plate_h เป็นตัวตั้ง เพื่อให้ซูมเข้าที่ Connection
        # ถ้า h_beam สูงมาก มันจะทะลุขอบบนล่างไป (Clip) ซึ่งถูกต้องแล้วสำหรับ Section Detail
        
        view_h = max(plate_h * 1.4, 250) # ดูพื้นที่อย่างน้อย 250mm หรือ 1.4 เท่าของเพลท
        view_w = max(b_beam, 200) * 1.5  # เผื่อที่ซ้ายขวา
        
        fig_sec.update_layout(
            height=500,
            # Force Aspect Ratio 1:1 but limit Range
            yaxis=dict(range=[-view_h/2, view_h/2], scaleanchor="x", scaleratio=1, visible=False, fixedrange=False),
            xaxis=dict(range=[-view_w/2, view_w/2], visible=False, fixedrange=False),
            plot_bgcolor="white",
            margin=dict(l=10, r=10, t=30, b=10),
            title=dict(text="SECTION A-A (Zoomed at Connection)", x=0.5, font=dict(size=14)),
            dragmode="pan" # ให้ user เลื่อนดูได้
        )
        # Add Label for Beam if top is cut off
        if h_beam > view_h:
            fig_sec.add_annotation(x=0, y=view_h/2-20, text="Beam Continues...", showarrow=False, font=dict(color="gray", size=10))

        st.plotly_chart(fig_sec, use_container_width=True)

    # --- VIEW 2: ELEVATION (Side View) ---
    with col_elev:
        st.subheader("ELEVATION VIEW")
        fig_elev = go.Figure()
        
        # Centering Logic for Elevation: Plate Center X
        cx_elev = plate_w / 2
        cy_elev = 0 # Beam Center Y
        
        beam_top = h_beam/2
        beam_bot = -h_beam/2
        
        # Draw Support (Left Limit)
        supp_x = 0 # Let's say connection starts at x=0 relative to support face
        fig_elev.add_shape(type="rect", x0=-40, y0=beam_bot-50, x1=0, y1=beam_top+50, fillcolor=c_supp, line_color="black")
        
        # Draw Beam Lines (Ghost)
        fig_elev.add_shape(type="rect", x0=0, y0=beam_bot, x1=plate_w+50, y1=beam_top, fillcolor="#f8fafc", line_width=0)
        fig_elev.add_shape(type="line", x0=0, y0=beam_top, x1=plate_w+50, y1=beam_top, line=dict(color="black", width=1))
        fig_elev.add_shape(type="line", x0=0, y0=beam_bot, x1=plate_w+50, y1=beam_bot, line=dict(color="black", width=1))
        
        # Draw Plate
        # Plate is positioned e1 from support.
        # But wait, diagram shows plate starts at x=0?? No, usually plate is welded to support.
        # Let's assume End Plate / Shear Tab is welded to support at x=0.
        
        plate_x0_el = 0
        plate_x1_el = plate_w
        plate_y0_el = -plate_h/2
        plate_y1_el = plate_h/2
        
        fig_elev.add_shape(type="rect", x0=plate_x0_el, y0=plate_y0_el, x1=plate_x1_el, y1=plate_y1_el, 
                           fillcolor=c_plate, line=dict(color="#1e3a8a", width=2))
        
        # Draw Bolts
        bolt_start_x = e1_mm
        bolt_start_y = plate_h/2 - real_lv
        
        for r in range(n_rows):
            for c in range(n_cols):
                bx = bolt_start_x + c*s_h
                by = bolt_start_y - r*s_v
                fig_elev.add_trace(go.Scatter(x=[bx], y=[by], mode='markers', marker=dict(size=10, color=c_bolt, line=dict(width=1, color="black")), showlegend=False))
                
        # Dimensions
        add_dim_line(fig_elev, 0, plate_y1_el, e1_mm, plate_y1_el, "e1", color="#d97706", offset=25)
        add_dim_line(fig_elev, 0, plate_y0_el, plate_w, plate_y0_el, f"W={plate_w:.0f}", color="blue", offset=-25, bold=True)
        
        dim_x_R_el = plate_w + 30
        add_dim_line(fig_elev, dim_x_R_el, plate_y1_el, dim_x_R_el, plate_y0_el, f"H={plate_h:.0f}", color="blue", offset=20, type="vert", bold=True)
        
        # *** KEY FIX: ELEVATION ZOOM ***
        # เหมือนกันครับ ซูมที่เพลทเป็นหลัก
        view_h_el = max(plate_h * 1.4, 250)
        view_w_el = max(plate_w * 1.5, 200)
        
        fig_elev.update_layout(
            height=500,
            yaxis=dict(range=[-view_h_el/2, view_h_el/2], scaleanchor="x", scaleratio=1, visible=False, fixedrange=False),
            xaxis=dict(range=[-40, view_w_el], visible=False, fixedrange=False),
            plot_bgcolor="white",
            margin=dict(l=10, r=10, t=30, b=10),
            title=dict(text="ELEVATION VIEW", x=0.5, font=dict(size=14)),
            dragmode="pan"
        )
        st.plotly_chart(fig_elev, use_container_width=True)

    # Return for calculation check if needed
    return n_total

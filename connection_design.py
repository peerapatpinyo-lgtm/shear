import streamlit as st
import math
import plotly.graph_objects as go

# ==========================================
# HELPER: DRAWING DIMENSIONS & SHAPES (Original Code)
# ==========================================
def add_dim_line(fig, x0, y0, x1, y1, text, color="black", offset=0, type="horiz", font_size=12, bold=False):
    arrow_len = 8
    text_bg = "rgba(255, 255, 255, 0.9)" 
    font_weight = "bold" if bold else "normal"

    if type == "horiz":
        y_pos = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos, line=dict(color=color, width=0.5, dash="dot"))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos, line=dict(color=color, width=0.5, dash="dot"))
        fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=color, width=1.2))
        fig.add_annotation(x=x1, y=y_pos, ax=-arrow_len, ay=0, arrowcolor=color, arrowhead=2, text="")
        fig.add_annotation(x=x0, y=y_pos, ax=arrow_len, ay=0, arrowcolor=color, arrowhead=2, text="")
        fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=text, showarrow=False, yshift=12 if offset>0 else -12, 
                            font=dict(color=color, size=font_size, weight=font_weight), bgcolor=text_bg)
    elif type == "vert":
        x_pos = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos, y1=y0, line=dict(color=color, width=0.5, dash="dot"))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos, y1=y1, line=dict(color=color, width=0.5, dash="dot"))
        fig.add_shape(type="line", x0=x_pos, y0=y0, x1=x_pos, y1=y1, line=dict(color=color, width=1.2))
        fig.add_annotation(x=x_pos, y=y1, ax=0, ay=arrow_len, arrowcolor=color, arrowhead=2, text="")
        fig.add_annotation(x=x_pos, y=y0, ax=0, ay=-arrow_len, arrowcolor=color, arrowhead=2, text="")
        fig.add_annotation(x=x_pos, y=(y0+y1)/2, text=text, showarrow=False, xshift=18 if offset>0 else -18, 
                            font=dict(color=color, size=font_size, weight=font_weight), textangle=-90, bgcolor=text_bg)

def create_ishape(h, b, tw, tf, cx=0, cy=0, fill_col="#cbd5e1", line_col="black"):
    shapes = []
    shapes.append(dict(type="rect", x0=cx-tw/2, y0=cy-h/2+tf, x1=cx+tw/2, y1=cy+h/2-tf, fillcolor=fill_col, line_width=0))
    shapes.append(dict(type="rect", x0=cx-b/2, y0=cy+h/2-tf, x1=cx+b/2, y1=cy+h/2, fillcolor=fill_col, line=dict(color=line_col, width=1.5)))
    shapes.append(dict(type="rect", x0=cx-b/2, y0=cy-h/2, x1=cx+b/2, y1=cy-h/2+tf, fillcolor=fill_col, line=dict(color=line_col, width=1.5)))
    shapes.append(dict(type="line", x0=cx-tw/2, y0=cy-h/2+tf, x1=cx-tw/2, y1=cy+h/2-tf, line=dict(color=line_col, width=1.5)))
    shapes.append(dict(type="line", x0=cx+tw/2, y0=cy-h/2+tf, x1=cx+tw/2, y1=cy+h/2-tf, line=dict(color=line_col, width=1.5)))
    return shapes

# ==========================================
# MAIN FUNCTION (COMPACT LAYOUT & AUTO-ZOOM FIXED)
# ==========================================
def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    # 1. SETUP
    is_beam_to_beam = "Beam to Beam" in conn_type
    d_mm = int(bolt_size[1:]) 
    
    # Beam Dimensions
    h_beam = float(section_data.get('h', 300))
    b_beam = float(section_data.get('b', 150))
    tf_beam = float(section_data.get('tf', 10))
    tw_beam = float(section_data.get('tw', 8))
    clear_web_h = h_beam - 2*(tf_beam * 1.5) 

    st.markdown(f"### 📐 Connection Design: **{conn_type}**")

    # --- CREATE TABS ---
    tab1, tab2 = st.tabs(["📝 Design Inputs & Check", "✏️ Shop Drawing (Section A-A)"])

    # ==========================================
    # TAB 1: INPUTS
    # ==========================================
    with tab1:
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

        fit_status = "CLASH" if plate_h > clear_web_h else "OK"
        n_total = n_rows * n_cols
        V_res, Design_Shear, Design_Bear = V_design/n_total, 10000, 15000 
        
        st.divider()
        c_res1, c_res2 = st.columns(2)
        with c_res1:
            if fit_status == "CLASH": st.error(f"❌ Geometry CLASH! (Plate too high)")
            else: st.success("✅ Geometry OK")
        with c_res2:
            st.metric("Bolt Shear Ratio", f"{(V_res*n_total)/Design_Shear:.2f}")

    # ==========================================
    # TAB 2: SHOP DRAWING (COMPACT VERSION)
    # ==========================================
    with tab2:
        st.markdown("#### 📍 Installation Layout")
        
        c_ctrl1, c_ctrl2 = st.columns(2)
        with c_ctrl1:
            plate_side = st.radio("ตำแหน่งเพลท", ["Right of Web", "Left of Web"], horizontal=True, label_visibility="collapsed")
        with c_ctrl2:
            eccentricity = st.slider("เยื้องศูนย์ (Eccentricity)", -50, 50, 0, 5)

        st.divider()
        # ปรับสัดส่วนคอลัมน์ให้รูปไม่เบียดกันเกินไป
        col_sec, col_elev = st.columns([1.2, 1])
        supp_col = "#334155" 
        
        # --- VIEW 1: SECTION A-A (TOP VIEW) ---
        with col_sec:
            st.markdown("**SECTION A-A (Top)**")
            fig_sec = go.Figure()
            
            # --- CALCULATE VIEW LIMITS (ZOOM) ---
            # กำหนดขอบเขตการมองเห็นให้พอดีกับวัตถุ ไม่เผื่อเยอะ
            zoom_y = max(b_beam, 150) * 0.8  # Zoom แกน Y ให้เห็นแค่ปีกคาน
            zoom_x_start = -50
            zoom_x_end = plate_w + 100 # Zoom แกน X ให้เห็นเลยเพลทไปนิดเดียว
            
            # 1. COLUMN (Fixed at 0,0)
            fig_sec.add_shape(type="rect", x0=-20, y0=-zoom_y, x1=0, y1=zoom_y, fillcolor=supp_col, line_color="black")
            
            # 2. BEAM
            beam_cy = eccentricity
            beam_x_end = zoom_x_end - 20 
            
            # Beam Web
            fig_sec.add_shape(type="rect", x0=10, y0=beam_cy-tw_beam/2, x1=beam_x_end, y1=beam_cy+tw_beam/2, fillcolor="#d4d4d8", line_color="black")
            # Beam Flanges (Outline)
            fig_sec.add_shape(type="rect", x0=10, y0=beam_cy-b_beam/2, x1=beam_x_end, y1=beam_cy+b_beam/2, line=dict(color="gray", dash="dot"))
            # Centerline
            fig_sec.add_shape(type="line", x0=-30, y0=beam_cy, x1=beam_x_end, y1=beam_cy, line=dict(color="#b91c1c", width=1, dash="dashdot"))

            # 3. PLATE & BOLTS
            # Side Logic
            if plate_side == "Right of Web":
                py_min, py_max = beam_cy + tw_beam/2, beam_cy + tw_beam/2 + t_plate_mm
            else:
                py_min, py_max = beam_cy - tw_beam/2 - t_plate_mm, beam_cy - tw_beam/2
            
            # Draw Plate
            fig_sec.add_shape(type="rect", x0=0, y0=py_min, x1=plate_w, y1=py_max, fillcolor="#3b82f6", line_color="black", opacity=0.9)
            
            # Weld
            weld_y = py_max if plate_side == "Right of Web" else py_min
            fig_sec.add_annotation(x=5, y=weld_y, text="Weld", showarrow=True, arrowhead=2, ay=-20 if plate_side=="Right of Web" else 20, font=dict(size=9))

            # Bolts
            b_start_x = e1_mm
            for c in range(n_cols):
                bx = b_start_x + c*s_h
                # Shank
                fig_sec.add_shape(type="rect", x0=bx-d_mm/2, y0=min(py_min, beam_cy-tw_beam/2), x1=bx+d_mm/2, y1=max(py_max, beam_cy+tw_beam/2), fillcolor="#b91c1c", line_width=0)
                # Heads
                head_h = d_mm * 0.6
                fig_sec.add_shape(type="rect", x0=bx-d_mm, y0=py_max, x1=bx+d_mm, y1=py_max+head_h, fillcolor="#7f1d1d")
                fig_sec.add_shape(type="rect", x0=bx-d_mm, y0=py_min-head_h, x1=bx+d_mm, y1=py_min, fillcolor="#7f1d1d")
                
                # Check 2nd side for web
                web_face_y = beam_cy - tw_beam/2 if plate_side == "Right of Web" else beam_cy + tw_beam/2
                # (Simplified Bolt drawing for clarity - assume nut on one side)

            # Dimensions
            dim_y = zoom_y - 10
            add_dim_line(fig_sec, 0, dim_y, plate_w, dim_y, f"W={plate_w:.0f}", offset=0)

            # --- COMPACT LAYOUT SETTINGS ---
            layout_sec = dict(
                height=350, # ⚡ ลดความสูงลง
                margin=dict(l=10, r=10, t=30, b=10), # ⚡ ลดขอบขาว
                plot_bgcolor="white",
                xaxis=dict(visible=False, range=[zoom_x_start, zoom_x_end], fixedrange=True), # ⚡ Lock Range X
                yaxis=dict(visible=False, range=[-zoom_y, zoom_y], scaleanchor="x", scaleratio=1, fixedrange=True), # ⚡ Lock Range Y
                dragmode="pan"
            )
            fig_sec.update_layout(**layout_sec)
            st.plotly_chart(fig_sec, use_container_width=True)

        # --- VIEW 2: ELEVATION (SIDE VIEW) ---
        with col_elev:
            st.markdown("**ELEVATION (Side)**")
            fig_elev = go.Figure()
            
            # --- CALCULATE VIEW LIMITS ---
            elev_zoom_y = h_beam * 0.7 
            elev_zoom_x = plate_w + 80
            
            # Beam & Plate
            fig_elev.add_shape(type="rect", x0=0, y0=-h_beam/2, x1=elev_zoom_x, y1=h_beam/2, line_color="gray", fillcolor="white") # Beam Body
            fig_elev.add_shape(type="line", x0=0, y0=-h_beam/2+tf_beam, x1=elev_zoom_x, y1=-h_beam/2+tf_beam, line_color="gray") # Flange
            fig_elev.add_shape(type="line", x0=0, y0=h_beam/2-tf_beam, x1=elev_zoom_x, y1=h_beam/2-tf_beam, line_color="gray") # Flange
            
            fig_elev.add_shape(type="rect", x0=0, y0=-plate_h/2, x1=plate_w, y1=plate_h/2, line_color="#3b82f6", fillcolor="rgba(59, 130, 246, 0.2)", line_width=2) # Plate
            fig_elev.add_shape(type="rect", x0=-20, y0=-elev_zoom_y, x1=0, y1=elev_zoom_y, fillcolor=supp_col, line_color="black") # Column
            
            # Bolts
            b_start_y = (plate_h/2) - real_lv 
            for r in range(n_rows):
                for c in range(n_cols):
                    bx = e1_mm + c*s_h
                    by = b_start_y - r*s_v
                    fig_elev.add_trace(go.Scatter(x=[bx], y=[by], mode='markers', marker=dict(size=8, color='#b91c1c'), showlegend=False))

            # Dimensions
            add_dim_line(fig_elev, plate_w+10, -plate_h/2, plate_w+10, plate_h/2, f"H={plate_h:.0f}", type="vert", color="#1e40af")

            # --- COMPACT LAYOUT SETTINGS ---
            layout_elev = dict(
                height=350, # ⚡ ลดความสูงลง
                margin=dict(l=10, r=10, t=30, b=10), # ⚡ ลดขอบขาว
                plot_bgcolor="white",
                xaxis=dict(visible=False, range=[-30, elev_zoom_x], fixedrange=True),
                yaxis=dict(visible=False, range=[-elev_zoom_y, elev_zoom_y], scaleanchor="x", scaleratio=1, fixedrange=True),
                dragmode="pan"
            )
            fig_elev.update_layout(**layout_elev)
            st.plotly_chart(fig_elev, use_container_width=True)

    return n_total, Design_Shear

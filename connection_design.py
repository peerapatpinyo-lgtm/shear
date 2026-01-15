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
# MAIN FUNCTION (UPDATED LOGIC: CENTER ALIGNMENT & CORRECT BOLTING)
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
    # TAB 1: INPUTS & CALCULATIONS
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
            e1_mm = st.number_input("Gap from Support (e1)", 10.0, 200.0, 50.0) # ระยะห่างจากผิวเสาถึง Bolt แถวแรก
            
            auto_h = (n_rows - 1) * s_v + (2 * l_edge_v_input)
            
            if size_mode == "Custom":
                plate_h = st.number_input("Plate Height (H)", min_value=float(min_req_h), max_value=float(h_beam), value=float(auto_h))
                l_side = st.number_input("Side Margin (Ls)", 20.0, 100.0, 40.0) # ระยะจาก Bolt ตัวสุดท้ายถึงปลาย Plate
            else:
                plate_h, l_side = auto_h, st.number_input("Side Margin (Ls)", 20.0, 100.0, 40.0)
        with c3:
            st.success("**🧱 Material**")
            t_plate_mm = st.number_input("Plate Thickness (t_pl)", 6.0, 50.0, 10.0)
            
            # Calculations
            real_lv = (plate_h - (n_rows-1)*s_v) / 2
            # Plate Width (แนวนอน) = Gap(e1) + ระยะระหว่าง Bolt + ปลาย(Side Margin)
            plate_w = e1_mm + (n_cols - 1) * s_h + l_side
            
            st.write(f"**Actual Lv:** {real_lv:.1f} mm")
            st.write(f"**Total Plate Width (W):** {plate_w:.0f} mm")

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
    # TAB 2: SHOP DRAWING (CORRECTED LOGIC)
    # ==========================================
    with tab2:
        st.markdown("#### 📍 Installation Alignment")
        # Slider for Eccentricity (Offset Y) - เลื่อนคานออกจากกึ่งกลางเสา (ถ้าจำเป็น)
        eccentricity = st.slider("Eccentricity (เยื้องศูนย์)", -50, 50, 0, 5, help="ขยับแนวคานออกจากกึ่งกลางเสา (ปกติเป็น 0)")
        st.divider()
        
        col_sec, col_elev = st.columns([1.2, 1])
        supp_col = "#334155" 
        
        # --- VIEW 1: SECTION A-A (TOP VIEW) ---
        # มุมมองจากด้านบน ตัดผ่านคานและเสา
        with col_sec:
            st.markdown("**SECTION A-A (Top/Plan View)**")
            fig_sec = go.Figure()
            
            view_w_limit = b_beam * 2 # ขอบเขตการมองเห็นในแกน Y

            if is_beam_to_beam:
                # (Logic Beam-to-Beam ยังคงไว้ตามเดิม หรือปรับปรุงได้ตามต้องการ)
                st.warning("Beam-to-Beam Drawing not fully updated in this snippet.")
                start_x = 0
            else:
                # =========================================
                # LOGIC: BEAM TO COLUMN (CENTER ALIGNED)
                # =========================================
                
                # 1. COLUMN (FIXED AT 0,0)
                # วาดเสาทางด้านซ้าย (X < 0)
                # ให้ Center ของเสาอยู่ที่ Y = 0
                
                col_face_x = 0 # ผิวเสาอยู่ที่ X=0
                
                # Column Flange (สี่เหลี่ยมยาวๆ แทนปีกเสา)
                fig_sec.add_shape(type="rect", 
                                  x0=col_face_x - 20, y0=-view_w_limit/2, 
                                  x1=col_face_x, y1=view_w_limit/2, 
                                  fillcolor=supp_col, line_color="black")
                
                # Column Centerline (เส้นแกนเสา)
                fig_sec.add_shape(type="line", x0=col_face_x-50, y0=0, x1=col_face_x+plate_w+100, y1=0, 
                                  line=dict(color="gray", width=1, dash="dashdot"))
                fig_sec.add_annotation(x=col_face_x-10, y=-view_w_limit/2+20, text="COLUMN", showarrow=False, font=dict(weight="bold", color="white"), textangle=-90)

                # 2. BEAM & PLATE GROUP (Center at Y = 0 + Eccentricity)
                # ถ้า eccentricity = 0 คือ Web ของคานอยู่ตรง Center เสาเป๊ะ
                
                group_cy = eccentricity
                
                # [A] BEAM (Secondary Beam)
                # Web ของคานจะวางอยู่ที่ Center Line (group_cy)
                beam_start_x = col_face_x + 10 # เว้น Gap จากเสานิดหน่อย (Clearance ~10mm)
                beam_len = plate_w + 120 
                
                # พิกัด Y ของ Beam Web
                web_y0 = group_cy - (tw_beam / 2)
                web_y1 = group_cy + (tw_beam / 2)
                
                # วาด Beam Web
                fig_sec.add_shape(type="rect", x0=beam_start_x, y0=web_y0, x1=beam_start_x + beam_len, y1=web_y1, 
                                  fillcolor="#d4d4d8", line_color="black")
                
                # วาด Beam Flanges (Top View เห็นเป็นเส้นขอบกว้างๆ)
                flange_y0 = group_cy - (b_beam / 2)
                flange_y1 = group_cy + (b_beam / 2)
                
                # Flange บน/ล่าง (โปร่งแสง หรือเส้นประ)
                fig_sec.add_shape(type="line", x0=beam_start_x, y0=flange_y1, x1=beam_start_x+beam_len, y1=flange_y1, line=dict(color="gray"))
                fig_sec.add_shape(type="line", x0=beam_start_x, y0=flange_y0, x1=beam_start_x+beam_len, y1=flange_y0, line=dict(color="gray"))
                
                fig_sec.add_annotation(x=beam_start_x+plate_w+20, y=group_cy, text="BEAM CL", font=dict(color="#b91c1c", size=10), yshift=10)

                # [B] FIN PLATE
                # Plate จะถูกเชื่อมติดกับผิวเสา (X=0)
                # และวางแนบข้าง Beam Web
                # ปกติวางด้านใดด้านหนึ่ง (สมมติวางด้านบนของ Web ใน Top View)
                
                p_x0 = col_face_x
                p_x1 = col_face_x + plate_w
                
                # Plate Y Start = ผิวของ Web (web_y1)
                p_y0 = web_y1 
                p_y1 = web_y1 + t_plate_mm
                
                # วาด Plate
                fig_sec.add_shape(type="rect", x0=p_x0, y0=p_y0, x1=p_x1, y1=p_y1, 
                                  fillcolor="#3b82f6", line_color="black", opacity=0.9)
                
                # Weld (เชื่อม Plate ติดเสา)
                weld_s = 6
                fig_sec.add_shape(type="path", path=f"M {p_x0},{p_y0} L {p_x0+weld_s},{p_y0} L {p_x0},{p_y1} Z", fillcolor="black") 
                fig_sec.add_annotation(x=p_x0, y=p_y1+5, text="Weld", showarrow=True, arrowhead=2, ax=15, ay=-15, font=dict(size=9))

                # [C] BOLTS
                # Bolt ยึดระหว่าง Plate และ Web เท่านั้น (ไม่ทะลุเสา)
                # แกน Bolt (Shank) ทะลุผ่าน Web (web_y0) ถึง Plate (p_y1)
                
                bolt_start_x = col_face_x + e1_mm
                
                for c in range(n_cols):
                    bx = bolt_start_x + c*s_h
                    
                    # 1. Bolt Shank (ตัวสกรู) 
                    fig_sec.add_shape(type="rect", x0=bx-d_mm/2, y0=web_y0, x1=bx+d_mm/2, y1=p_y1, 
                                      fillcolor="#b91c1c", line_width=0)
                    
                    # 2. Heads & Nuts (หัวน็อต)
                    head_h = d_mm * 0.6
                    # หัวบน (ฝั่ง Plate)
                    fig_sec.add_shape(type="rect", x0=bx-d_mm, y0=p_y1, x1=bx+d_mm, y1=p_y1+head_h, fillcolor="#7f1d1d", line_color="black")
                    # หัวล่าง (ฝั่ง Web)
                    fig_sec.add_shape(type="rect", x0=bx-d_mm, y0=web_y0-head_h, x1=bx+d_mm, y1=web_y0, fillcolor="#7f1d1d", line_color="black")
                    
                    # Centerline ผ่าน Bolt
                    fig_sec.add_shape(type="line", x0=bx, y0=flange_y0, x1=bx, y1=flange_y1, line=dict(color="black", width=0.5, dash="dot"))

                # DIMENSIONS
                dim_y_top = view_w_limit/2 + 10
                
                # Plate Width (W)
                add_dim_line(fig_sec, col_face_x, dim_y_top, col_face_x+plate_w, dim_y_top, f"W={plate_w:.0f}", offset=0)
                
                # Gap (e1)
                add_dim_line(fig_sec, col_face_x, dim_y_top-25, col_face_x+e1_mm, dim_y_top-25, f"e1", color="orange", offset=0)
                
                # Thickness (Web & Plate)
                thk_x_pos = beam_start_x + beam_len + 10
                add_dim_line(fig_sec, thk_x_pos, web_y0, thk_x_pos, web_y1, f"tw", type="vert", offset=0)
                add_dim_line(fig_sec, thk_x_pos, p_y0, thk_x_pos, p_y1, f"tpl", type="vert", offset=0)
                
                # Center Check visual
                if eccentricity == 0:
                     fig_sec.add_annotation(x=col_face_x-30, y=0, text="CENTERED", font=dict(color="green", size=10, weight="bold"), showarrow=False, bgcolor="rgba(255,255,255,0.8)")

            layout_sec = dict(height=450, plot_bgcolor="white", 
                              margin=dict(l=20, r=20, t=40, b=20), 
                              title=dict(text="SECTION A-A (TOP VIEW)", x=0.5),
                              xaxis=dict(visible=False, fixedrange=False),
                              yaxis=dict(visible=False, fixedrange=False, scaleanchor="x", scaleratio=1))
            
            fig_sec.update_layout(**layout_sec)
            st.plotly_chart(fig_sec, use_container_width=True)

        # --- VIEW 2: ELEVATION (SIDE VIEW) ---
        with col_elev:
            st.markdown("**ELEVATION (Side View)**")
            fig_elev = go.Figure()
            
            # Beam Profile (Side)
            fig_elev.add_shape(type="rect", x0=0, y0=-h_beam/2, x1=plate_w+100, y1=h_beam/2, line_color="gray", fillcolor="white")
            # Flanges
            fig_elev.add_shape(type="line", x0=0, y0=-h_beam/2+tf_beam, x1=plate_w+100, y1=-h_beam/2+tf_beam, line_color="gray")
            fig_elev.add_shape(type="line", x0=0, y0=h_beam/2-tf_beam, x1=plate_w+100, y1=h_beam/2-tf_beam, line_color="gray")
            
            # Plate Profile
            fig_elev.add_shape(type="rect", x0=0, y0=-plate_h/2, x1=plate_w, y1=plate_h/2, line_color="#3b82f6", fillcolor="rgba(59, 130, 246, 0.2)", line_width=2)
            
            # Support Column (Side edge)
            fig_elev.add_shape(type="rect", x0=-20, y0=-h_beam/2-20, x1=0, y1=h_beam/2+20, fillcolor=supp_col, line_color="black")

            # Bolts (Calculated positions)
            b_start_x = e1_mm
            b_start_y = (plate_h/2) - real_lv # Top bolt position
            
            for r in range(n_rows):
                for c in range(n_cols):
                    bx = b_start_x + c*s_h
                    by = b_start_y - r*s_v
                    fig_elev.add_trace(go.Scatter(x=[bx], y=[by], mode='markers', marker=dict(size=8, color='#b91c1c'), showlegend=False))
                    # Cross hair
                    fig_elev.add_shape(type="line", x0=bx-5, y0=by, x1=bx+5, y1=by, line_width=1)
                    fig_elev.add_shape(type="line", x0=bx, y0=by-5, x1=bx, y1=by+5, line_width=1)

            # Dimensions
            add_dim_line(fig_elev, plate_w+20, -plate_h/2, plate_w+20, plate_h/2, f"H={plate_h:.0f}", type="vert", color="#1e40af")
            add_dim_line(fig_elev, 0, -h_beam/2-20, plate_w, -h_beam/2-20, f"W={plate_w:.0f}", type="horiz", color="#1e40af")
            add_dim_line(fig_elev, plate_w+50, -h_beam/2, plate_w+50, h_beam/2, f"Beam H={h_beam:.0f}", type="vert", color="gray")

            fig_elev.update_layout(height=450, plot_bgcolor="white", 
                                   xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
                                   title=dict(text="ELEVATION VIEW", x=0.5))
            st.plotly_chart(fig_elev, use_container_width=True)

    return n_total, Design_Shear

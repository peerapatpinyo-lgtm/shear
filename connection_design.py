import streamlit as st
import plotly.graph_objects as go

# ==========================================
# HELPER: DRAWING SHAPES (เหมือนเดิม)
# ==========================================
def create_ishape(h, b, tw, tf, cx=0, cy=0, fill_col="#cbd5e1", line_col="black", opacity=1.0):
    shapes = []
    # Top Flange
    shapes.append(dict(type="rect", x0=cx-b/2, y0=cy+h/2-tf, x1=cx+b/2, y1=cy+h/2, fillcolor=fill_col, line=dict(color=line_col, width=1.5), opacity=opacity))
    # Bottom Flange
    shapes.append(dict(type="rect", x0=cx-b/2, y0=cy-h/2, x1=cx+b/2, y1=cy-h/2+tf, fillcolor=fill_col, line=dict(color=line_col, width=1.5), opacity=opacity))
    # Web
    shapes.append(dict(type="rect", x0=cx-tw/2, y0=cy-h/2+tf, x1=cx+tw/2, y1=cy+h/2-tf, fillcolor=fill_col, line_width=0, opacity=opacity))
    # Web Lines
    shapes.append(dict(type="line", x0=cx-tw/2, y0=cy-h/2+tf, x1=cx-tw/2, y1=cy+h/2-tf, line=dict(color=line_col, width=1.5)))
    shapes.append(dict(type="line", x0=cx+tw/2, y0=cy-h/2+tf, x1=cx+tw/2, y1=cy+h/2-tf, line=dict(color=line_col, width=1.5)))
    return shapes

def add_dim_line(fig, x0, y0, x1, y1, text, color="black", offset=0, type="horiz", font_size=12, bold=False):
    arrow_len = 8
    font_weight = "bold" if bold else "normal"
    if type == "horiz":
        y_pos = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=color, width=1.2))
        fig.add_annotation(x=x1, y=y_pos, ax=-arrow_len, ay=0, arrowcolor=color, arrowhead=2, text="")
        fig.add_annotation(x=x0, y=y_pos, ax=arrow_len, ay=0, arrowcolor=color, arrowhead=2, text="")
        fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=text, showarrow=False, yshift=12 if offset>0 else -12, font=dict(color=color, size=font_size, weight=font_weight))

# ==========================================
# MAIN RENDERING FUNCTION
# ==========================================
def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    # 1. SETUP PARAMETERS (เหมือนเดิม)
    h_beam = float(section_data.get('h', 300))
    b_beam = float(section_data.get('b', 150))
    tf_beam = float(section_data.get('tf', 10))
    tw_beam = float(section_data.get('tw', 8))
    
    d_mm = int(bolt_size[1:]) 
    n_rows = 3
    s_v = 75.0
    plate_h = (n_rows-1)*s_v + 80
    plate_w = 120
    t_plate = 10.0
    
    # Column Dimensions
    col_width = b_beam * 2.0 
    col_height_viz = h_beam * 1.2

    # UI INPUTS (แสดงผลด้านบน ก่อนเข้า Tab)
    st.markdown(f"### 📐 Connection Design: **{conn_type}**")
    
    # --------------------------------------------------------
    # [NEW] สร้าง Tabs เพื่อแยกข้อมูลกับรูปวาด
    # --------------------------------------------------------
    tab1, tab2 = st.tabs(["📝 Design Data & Checks", "✏️ Shop Drawing (Section A-A)"])

    # === TAB 1: ข้อมูลการออกแบบและการตรวจสอบ ===
    with tab1:
        st.info("Input Parameters & Code Checks")
        c1, c2, c3 = st.columns(3)
        with c1: st.write(f"**Bolt:** {bolt_size} ({bolt_grade})")
        with c2: st.write(f"**Plate Size:** {plate_w} x {plate_h} x {t_plate} mm")
        with c3: st.write(f"**Beam:** H-{h_beam:.0f}x{b_beam:.0f}")
        
        # แสดงผลการคำนวณเบื้องต้น (Mockup)
        st.success("✅ Geometry Check: OK")
        st.metric("Shear Capacity", "Start Calculation...")

    # === TAB 2: รูปวาด SHOP DRAWING (ตามที่คุณต้องการ) ===
    with tab2:
        # 🎯 CUSTOM OFFSET CONTROL (อยู่ใน Tab 2 เพื่อปรับแล้วเห็นภาพเลย)
        st.markdown("#### 📍 Adjust Installation Position")
        c_ctrl, c_info = st.columns([2, 1])
        with c_ctrl:
            offset_val = st.slider("ระยะหนีศูนย์ (Offset from CL)", min_value=-100, max_value=100, value=30, step=5, help="เลื่อนซ้าย-ขวา ตามหน้างานจริง")
        with c_info:
            st.info(f"Offset: **{offset_val} mm**")

        st.divider()
        c_sec, c_elev = st.columns([1.2, 1])

        # ==========================================
        # VIEW 1: SECTION A-A (CROSS SECTION VIEW)
        # ==========================================
        with c_sec:
            st.subheader("SECTION A-A")
            st.caption(f"Offset: {offset_val} mm from Column Center")
            fig_sec = go.Figure()

            # 1. COLUMN FLANGE (Fixed at Center 0,0) - โครงสร้างเดิม (เสา) ไม่ขยับ
            fig_sec.add_shape(type="rect", 
                              x0=-col_width/2, y0=-col_height_viz/2, 
                              x1=col_width/2, y1=col_height_viz/2, 
                              fillcolor="#334155", line_color="black")
            
            # Centerline of Column
            fig_sec.add_shape(type="line", x0=0, y0=-col_height_viz/2-20, x1=0, y1=col_height_viz/2+60, 
                              line=dict(color="black", width=1, dash="dash"))
            fig_sec.add_annotation(x=0, y=-col_height_viz/2-30, text="Column CL", showarrow=False, font=dict(color="black"))

            # 2. BEAM & PLATE GROUP (Move by Offset)
            # โครงสร้างเดิม (คาน+เพลท) เลื่อนตามค่า Offset ที่ตั้งไว้
            gap = 1 
            group_center_x = offset_val 
            
            plate_x_center = group_center_x - (t_plate/2 + gap)
            web_x_center = group_center_x + (tw_beam/2 + gap)
            
            # Draw Plate
            fig_sec.add_shape(type="rect", 
                              x0=plate_x_center - t_plate/2, y0=-plate_h/2, 
                              x1=plate_x_center + t_plate/2, y1=plate_h/2, 
                              fillcolor="#3b82f6", line_color="black")
            
            # Draw Beam (I-Shape)
            beam_shapes = create_ishape(h_beam, b_beam, tw_beam, tf_beam, cx=web_x_center, cy=0, fill_col="#d4d4d8")
            for s in beam_shapes: fig_sec.add_shape(s)
            
            # Draw Bolts
            for r in [-1, 0, 1]: 
                by = r * s_v
                # Body
                fig_sec.add_shape(type="rect", x0=plate_x_center - t_plate, y0=by-6, x1=web_x_center + tw_beam + 8, y1=by+6, fillcolor="#b91c1c", line_width=0)
                # Head
                fig_sec.add_shape(type="rect", x0=plate_x_center - t_plate - 12, y0=by-10, x1=plate_x_center - t_plate, y1=by+10, fillcolor="#7f1d1d", line_color="black")
                # Nut
                fig_sec.add_shape(type="rect", x0=web_x_center + tw_beam + 8, y0=by-10, x1=web_x_center + tw_beam + 20, y1=by+10, fillcolor="#7f1d1d", line_color="black")

            # Dimensions & Labels
            add_dim_line(fig_sec, -col_width/2, col_height_viz/2, col_width/2, col_height_viz/2, "Col. Width", offset=40, type="horiz", color="#b91c1c", bold=True)
            
            # Show Offset Dimension if offset is not 0
            if abs(offset_val) > 5:
                fig_sec.add_annotation(x=group_center_x, y=0, ax=0, ay=-40, text=f"Offset {offset_val}", showarrow=True, arrowcolor="red")
                fig_sec.add_shape(type="line", x0=0, y0=0, x1=group_center_x, y1=0, line=dict(color="red", width=2, dash="dot"))

            fig_sec.update_layout(height=500, plot_bgcolor="white", 
                                  xaxis=dict(visible=False, range=[-col_width/2-50, col_width/2+50]),
                                  yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
                                  margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_sec, use_container_width=True)

        # ==========================================
        # VIEW 2: ELEVATION (SIDE VIEW)
        # ==========================================
        with c_elev:
            st.subheader("ELEVATION VIEW")
            fig_elev = go.Figure()
            
            # Column Strip
            fig_elev.add_shape(type="rect", x0=-40, y0=-h_beam/2-50, x1=0, y1=h_beam/2+50, fillcolor="#334155", line_color="black")
            # Beam Ghost
            fig_elev.add_shape(type="rect", x0=0, y0=-h_beam/2, x1=300, y1=h_beam/2, fillcolor="#f1f5f9", line=dict(color="gray", dash="dot"))
            # Plate
            fig_elev.add_shape(type="rect", x0=0, y0=-plate_h/2, x1=plate_w, y1=plate_h/2, fillcolor="rgba(59, 130, 246, 0.5)", line=dict(color="#1d4ed8", width=2))
            
            bolt_x_start = 50
            for r in range(n_rows):
                by = (plate_h/2 - 40) - r*s_v
                fig_elev.add_trace(go.Scatter(x=[bolt_x_start], y=[by], mode='markers', marker=dict(size=10, color='#b91c1c'), showlegend=False))
                
            fig_elev.update_layout(height=500, plot_bgcolor="white", 
                                   xaxis=dict(visible=False),
                                   yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
                                   margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_elev, use_container_width=True)

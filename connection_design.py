import streamlit as st
import plotly.graph_objects as go

# ==========================================
# HELPER: DRAWING SHAPES
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
    
    # 1. SETUP PARAMETERS
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
    
    # Column Dimensions (Assumed bigger than beam)
    col_width = b_beam * 1.5 
    col_height_viz = h_beam * 1.2
    
    # Layout Columns
    st.divider()
    c_sec, c_elev = st.columns([1.2, 1])

    # ==========================================
    # VIEW 1: SECTION A-A (CROSS SECTION VIEW)
    # มุมมอง: มองย้อนจากปลายคาน เข้าหาเสา (เห็นหน้าตัด I)
    # ==========================================
    with c_sec:
        st.subheader("SECTION A-A")
        st.caption("View Looking at Column Flange Face")
        fig_sec = go.Figure()

        # 1. COLUMN FLANGE (Background)
        # วาดเป็นแผ่นสี่เหลี่ยมด้านหลังสุด
        fig_sec.add_shape(type="rect", 
                          x0=-col_width/2, y0=-col_height_viz/2, 
                          x1=col_width/2, y1=col_height_viz/2, 
                          fillcolor="#334155", line_color="black")
        fig_sec.add_annotation(x=0, y=col_height_viz/2+20, text="COLUMN FLANGE", showarrow=False, font=dict(weight="bold", color="#334155"))
        
        # Dimension: Column Width
        add_dim_line(fig_sec, -col_width/2, col_height_viz/2, col_width/2, col_height_viz/2, "Col. Width", offset=40, type="horiz", color="#b91c1c", bold=True)
        
        # Centerline (CL) - The most important line!
        fig_sec.add_shape(type="line", x0=0, y0=-col_height_viz/2-20, x1=0, y1=col_height_viz/2+60, 
                          line=dict(color="#b91c1c", width=2, dash="dashdot"))
        fig_sec.add_annotation(x=0, y=-col_height_viz/2-30, text="CL (Center)", showarrow=False, font=dict(color="#b91c1c", weight="bold"))

        # 2. FIN PLATE (Welded to Column)
        # ปกติ Plate จะเชื่อมติดเสา แล้วคานมาประกบ
        # สมมติจัดวางแบบ Center Group: Plate อยู่ข้างนึง, Web อยู่ข้างนึง ให้ Centerline อยู่กลางรอยต่อ
        gap = 1 # gap for visualization
        plate_x_center = - (t_plate/2 + gap)
        web_x_center = (tw_beam/2 + gap)
        
        # Draw Plate (Edge View / Cross Section of vertical plate)
        # Plate สูง plate_h, หนา t_plate
        fig_sec.add_shape(type="rect", 
                          x0=plate_x_center - t_plate/2, y0=-plate_h/2, 
                          x1=plate_x_center + t_plate/2, y1=plate_h/2, 
                          fillcolor="#3b82f6", line_color="black") # Blue Plate
        
        # 3. BEAM (I-Shape)
        # วาด Beam เป็นรูปตัว I
        beam_shapes = create_ishape(h_beam, b_beam, tw_beam, tf_beam, cx=web_x_center, cy=0, fill_col="#d4d4d8")
        for s in beam_shapes: fig_sec.add_shape(s)
        
        # 4. BOLT (Connection)
        # Bolt ร้อยผ่าน Plate และ Web (สีแดง)
        # ในมุมนี้จะเห็น Bolt เป็นแท่งแนวนอนทะลุ
        for r in [-1, 0, 1]: # 3 rows example
            by = r * s_v
            # Bolt Body
            fig_sec.add_shape(type="rect", 
                              x0=plate_x_center - t_plate, y0=by-6, 
                              x1=web_x_center + tw_beam + 8, y1=by+6, 
                              fillcolor="#b91c1c", line_width=0)
            # Bolt Head (Left)
            fig_sec.add_shape(type="rect", 
                              x0=plate_x_center - t_plate - 12, y0=by-10, 
                              x1=plate_x_center - t_plate, y1=by+10, 
                              fillcolor="#7f1d1d", line_color="black")
            # Nut (Right)
            fig_sec.add_shape(type="rect", 
                              x0=web_x_center + tw_beam + 8, y0=by-10, 
                              x1=web_x_center + tw_beam + 20, y1=by+10, 
                              fillcolor="#7f1d1d", line_color="black")

        # Labels
        fig_sec.add_annotation(x=plate_x_center, y=plate_h/2, text="Plate", ax=-40, ay=-40, showarrow=True, arrowhead=2)
        fig_sec.add_annotation(x=web_x_center, y=h_beam/2, text="Beam (I)", ax=40, ay=-40, showarrow=True, arrowhead=2)

        fig_sec.update_layout(height=500, plot_bgcolor="white", 
                              xaxis=dict(visible=False, range=[-col_width/2-20, col_width/2+20]),
                              yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
                              margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_sec, use_container_width=True)

    # ==========================================
    # VIEW 2: ELEVATION (SIDE VIEW)
    # มุมมอง: มองด้านข้าง เห็น Plate แปะที่เสา
    # ==========================================
    with c_elev:
        st.subheader("ELEVATION VIEW")
        st.caption("Side View of Connection")
        fig_elev = go.Figure()
        
        # 1. COLUMN (Side view is a strip)
        fig_elev.add_shape(type="rect", x0=-40, y0=-h_beam/2-50, x1=0, y1=h_beam/2+50, fillcolor="#334155", line_color="black")
        
        # 2. BEAM (Transparent/Outline)
        fig_elev.add_shape(type="rect", x0=0, y0=-h_beam/2, x1=300, y1=h_beam/2, fillcolor="#f1f5f9", line=dict(color="gray", dash="dot"))
        
        # 3. PLATE (Blue)
        fig_elev.add_shape(type="rect", x0=0, y0=-plate_h/2, x1=plate_w, y1=plate_h/2, fillcolor="rgba(59, 130, 246, 0.5)", line=dict(color="#1d4ed8", width=2))
        
        # 4. BOLTS (Dots)
        bolt_x_start = 50
        for r in range(n_rows):
            by = (plate_h/2 - 40) - r*s_v
            fig_elev.add_trace(go.Scatter(x=[bolt_x_start], y=[by], mode='markers', marker=dict(size=10, color='#b91c1c'), showlegend=False))
            
        # 5. EYE SYMBOL (User Reference)
        # วาดรูปตาเพื่อให้รู้ว่ามองจากทางนี้
        eye_x, eye_y = 250, 0
        fig_elev.add_trace(go.Scatter(x=[eye_x], y=[eye_y], mode="text", text="👁️<br>Look", textfont=dict(size=20)))
        fig_elev.add_annotation(x=eye_x-20, y=eye_y, ax=40, ay=0, arrowcolor="black", arrowhead=2)
        fig_elev.add_annotation(x=eye_x-80, y=eye_y-30, text="To see Section A-A", showarrow=False)

        fig_elev.update_layout(height=500, plot_bgcolor="white", 
                               xaxis=dict(visible=False),
                               yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
                               margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_elev, use_container_width=True)

# Call the function (Mock data for demo)
render_connection_tab(50000, "M20", "LRFD", True, {'h':400, 'b':200, 'tw':8, 'tf':12}, "Beam to Column", "A325")

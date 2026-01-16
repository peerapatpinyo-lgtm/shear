import plotly.graph_objects as go

# =============================================================================
# 🎨 ENGINEERING STYLE GUIDE
# =============================================================================
C_STEEL_OUT = "#0f172a"    # ขอบเหล็กเข้ม (Midnight)
C_BEAM_WEB = "#f1f5f9"     # เนื้อเหล็ก
C_PLATE = "#0ea5e9"        # Shear Plate (Sky Blue)
C_BOLT = "#be123c"         # Bolt (Crimson)
C_DIM_LINE = "#475569"     # เส้น Dimension (Slate)
C_YELLOW_COL = "#eab308"   # ขอบเขตเสา (Yellow Line)
C_CL = "#ef4444"           # Centerline

# =============================================================================
# 📏 ADVANCED DIMENSIONING SYSTEM
# =============================================================================
def add_eng_dim(fig, x0, y0, x1, y1, text, mode="h", offset=25):
    """ เส้นบอกระยะมาตรฐานวิศวกรรม พร้อมหัวลูกศรคมชัด """
    if mode == "h":
        y_loc = y0 + offset
        # Extension Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_loc+5, line=dict(color=C_DIM_LINE, width=0.8))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_loc+5, line=dict(color=C_DIM_LINE, width=0.8))
        # Dimension Line
        fig.add_annotation(x=x0, y=y_loc, ax=x1, ay=y_loc, xref="x", yref="y", axref="x", ayref="y",
                           text="", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=C_DIM_LINE)
        fig.add_annotation(x=x1, y=y_loc, ax=x0, ay=y_loc, xref="x", yref="y", axref="x", ayref="y",
                           text="", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=C_DIM_LINE)
        # Text
        fig.add_annotation(x=(x0+x1)/2, y=y_loc, text=f"{text}", showarrow=False, yshift=10,
                           font=dict(size=11, color="black", family="Courier New, monospace"), bgcolor="rgba(255,255,255,0.8)")
    else:
        x_loc = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_loc+5, y1=y0, line=dict(color=C_DIM_LINE, width=0.8))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_loc+5, y1=y1, line=dict(color=C_DIM_LINE, width=0.8))
        fig.add_annotation(x=x_loc, y=y0, ax=x_loc, ay=y_loc, xref="x", yref="y", axref="x", ayref="y", text="", showarrow=False) # Dummy
        fig.add_annotation(x=x_loc, y=y0, ax=x_loc, ay=y1, xref="x", yref="y", axref="x", ayref="y",
                           text="", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=C_DIM_LINE)
        fig.add_annotation(x=x_loc, y=y1, ax=x_loc, ay=y0, xref="x", yref="y", axref="x", ayref="y",
                           text="", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=C_DIM_LINE)
        fig.add_annotation(x=x_loc, y=(y0+y1)/2, text=f"{text}", showarrow=False, xshift=15, textangle=-90,
                           font=dict(size=11, color="black", family="Courier New, monospace"), bgcolor="rgba(255,255,255,0.8)")

# =============================================================================
# 1. PLAN VIEW (TOP)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, b, w_pl, t_pl = beam['tw'], beam['b'], plate['w'], plate['t']
    e1 = plate.get('e1', 40)
    
    # Column Ref
    fig.add_shape(type="rect", x0=-20, y0=-b/2, x1=0, y1=b/2, fillcolor="#f1f5f9", line=dict(color=C_YELLOW_COL, dash="dash"))
    # Beam & Plate
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+20, y1=tw/2, fillcolor=C_BEAM_WEB, line=dict(color=C_STEEL_OUT))
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    
    # Dimensions
    add_eng_dim(fig, 0, tw/2+t_pl, w_pl, tw/2+t_pl, f"W_pl={w_pl}", "h", 30)
    add_eng_dim(fig, 0, 0, e1, 0, f"e1={e1}", "h", -40)

    fig.update_layout(title="<b>PLAN VIEW</b>", plot_bgcolor="white", margin=dict(l=10,r=10,t=40,b=10), height=300,
                      xaxis=dict(visible=False, range=[-40, w_pl+40]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig

# =============================================================================
# 2. ELEVATION VIEW (Front)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_b, h_pl, w_pl = beam['h'], plate['h'], plate['w']
    lv, s_v, n_rows = plate.get('lv', 35), bolts['s_v'], bolts['rows']
    
    # Column Side
    fig.add_shape(type="rect", x0=-20, y0=-h_b/2, x1=0, y1=h_b/2, fillcolor="#e2e8f0", line=dict(color=C_YELLOW_COL, dash="dash"))
    # Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    
    # Bolts & Pitch Dim
    for i in range(n_rows):
        y_bolt = h_pl/2 - lv - (i * s_v)
        fig.add_shape(type="circle", x0=w_pl/2-5, y0=y_bolt-5, x1=w_pl/2+5, y1=y_bolt+5, fillcolor=C_BOLT)
        if i < n_rows - 1:
            add_eng_dim(fig, w_pl/2, y_bolt, w_pl/2, y_bolt-s_v, f"{s_v}", "v", 30)

    add_eng_dim(fig, w_pl, h_pl/2, w_pl, -h_pl/2, f"H_pl={h_pl}", "v", 60)
    
    fig.update_layout(title="<b>ELEVATION VIEW</b>", plot_bgcolor="white", margin=dict(l=10,r=10,t=40,b=10), height=350,
                      xaxis=dict(visible=False, range=[-40, w_pl+80]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig

# =============================================================================
# 3. SIDE VIEW (Detailed Section)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl, t_pl = plate['h'], plate['t']
    lv, s_v, n_rows = plate.get('lv', 35), bolts['s_v'], bolts['rows']

    # 1. Column Reference (Yellow boundary) - สเกลเหมาะสม ไม่ใหญ่เกิน
    fig.add_shape(type="rect", x0=-b/2-20, y0=-h/2-20, x1=b/2+20, y1=h/2+20, 
                  line=dict(color=C_YELLOW_COL, width=2, dash="dash"), fillcolor="rgba(241,245,249,0.3)")

    # 2. I-Beam Section (Correct Scale)
    # Flanges
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, line=dict(color=C_STEEL_OUT, width=1.5), fillcolor=C_BEAM_WEB)
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, line=dict(color=C_STEEL_OUT, width=1.5), fillcolor=C_BEAM_WEB)
    # Web
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, line=dict(color=C_STEEL_OUT, width=1.2), fillcolor=C_BEAM_WEB)

    # 3. Shear Plate & Bolt Details
    p_x0, p_x1 = tw/2, tw/2 + t_pl
    fig.add_shape(type="rect", x0=p_x0, y0=-h_pl/2, x1=p_x1, y1=h_pl/2, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    
    for i in range(n_rows):
        y_bolt = h_pl/2 - lv - (i * s_v)
        # Bolt Head/Nut Detail
        fig.add_shape(type="rect", x0=p_x1, y0=y_bolt-4, x1=p_x1+12, y1=y_bolt+4, fillcolor=C_BOLT, line_width=0)
    
    # 4. Engineering Dimensions (ครบถ้วน & ชัดเจน)
    add_eng_dim(fig, -b/2, h/2, b/2, h/2, f"B={b}", "h", 30)
    add_eng_dim(fig, b/2, h/2, b/2, -h/2, f"H={h}", "v", 30)
    add_eng_dim(fig, tw/2, -h_pl/2, tw/2+t_pl, -h_pl/2, f"t={t_pl}", "h", -30)

    fig.update_layout(title="<b>SIDE SECTION VIEW</b>", plot_bgcolor="white", margin=dict(l=10,r=10,t=40,b=10), height=450,
                      xaxis=dict(visible=False, range=[-b, b+50]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig

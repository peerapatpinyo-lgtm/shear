import plotly.graph_objects as go

# =============================================================================
# 🎨 PROFESSIONAL COLOR PALETTE & STYLES
# =============================================================================
C_COL_OUTLINE = "#eab308"  # สีเหลือง (Boundary เสา)
C_COL_FILL = "#f8fafc"     # สีพื้นเสา
C_BEAM_FILL = "#f1f5f9"    # สีเนื้อคาน (Light Slate)
C_BEAM_OUT = "#1e293b"     # สีขอบเหล็ก (Dark Slate)
C_PLATE_FILL = "#0ea5e9"   # สี Plate (Sky Blue)
C_BOLT_FILL = "#be123c"    # สี Bolt (Crimson)
C_DIM = "#475569"          # สีเส้นบอกระยะ
C_CL = "#ef4444"           # สีเส้น Centerline

# =============================================================================
# 🛠️ HELPER TOOLS (CAD Standard)
# =============================================================================
def add_cad_dim(fig, x0, y0, x1, y1, text, type="horiz", offset=0):
    arrow_head_style = 2  
    arrow_scale = 1.0     
    arrow_width = 0.8     
    if type == "horiz":
        y_dim = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_dim, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_dim, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x0, y0=y_dim, x1=x1, y1=y_dim, line=dict(color=C_DIM, width=1))
        fig.add_annotation(x=(x0+x1)/2, y=y_dim, text=f"<b>{text}</b>", showarrow=False, yshift=10, font=dict(size=10, color=C_DIM), bgcolor="white")
    elif type == "vert":
        x_dim = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_dim, y1=y0, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_dim, y1=y1, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x_dim, y0=y0, x1=x_dim, y1=y1, line=dict(color=C_DIM, width=1))
        fig.add_annotation(x=x_dim, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=-15, textangle=-90, font=dict(size=10, color=C_DIM), bgcolor="white")

def add_centerline(fig, x0, y0, x1, y1):
    fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color=C_CL, width=1, dash="dashdot"), opacity=0.6)

def get_i_section_path(x_center, y_center, h, b, tf, tw, r=10):
    """ สร้างเส้นรอบรูป I-Section แบบมี Root Radius เพื่อความละเอียด """
    return (f"M {x_center-b/2},{y_center-h/2} L {x_center+b/2},{y_center-h/2} "
            f"L {x_center+b/2},{y_center-h/2+tf} L {x_center+tw/2+r},{y_center-h/2+tf} "
            f"Q {x_center+tw/2},{y_center-h/2+tf} {x_center+tw/2},{y_center-h/2+tf+r} "
            f"L {x_center+tw/2},{y_center+h/2-tf-r} "
            f"Q {x_center+tw/2},{y_center+h/2-tf} {x_center+tw/2+r},{y_center+h/2-tf} "
            f"L {x_center+b/2},{y_center+h/2-tf} L {x_center+b/2},{y_center+h/2} "
            f"L {x_center-b/2},{y_center+h/2} L {x_center-b/2},{y_center+h/2-tf} "
            f"L {x_center-tw/2-r},{y_center+h/2-tf} "
            f"Q {x_center-tw/2},{y_center+h/2-tf} {x_center-tw/2},{y_center+h/2-tf-r} "
            f"L {x_center-tw/2},{y_center-h/2+tf+r} "
            f"Q {x_center-tw/2},{y_center-h/2+tf} {x_center-tw/2-r},{y_center-h/2+tf} "
            f"L {x_center-b/2},{y_center-h/2+tf} Z")

# =============================================================================
# 1. PLAN VIEW
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, b, w_pl, t_pl = beam['tw'], beam['b'], plate['w'], plate['t']
    fig.add_shape(type="rect", x0=-30, y0=-b/2-20, x1=0, y1=b/2+20, fillcolor="#e2e8f0", line_width=0)
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+40, y1=tw/2, fillcolor=C_BEAM_FILL, line=dict(color=C_BEAM_OUT))
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE_FILL, line=dict(color=C_BEAM_OUT))
    add_centerline(fig, -40, 0, w_pl+50, 0)
    fig.update_layout(title="<b>PLAN VIEW</b>", plot_bgcolor="white", height=300, showlegend=False,
                      xaxis=dict(visible=False, range=[-50, 150]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig

# =============================================================================
# 2. ELEVATION VIEW (Front)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_beam, h_pl, w_pl = beam['h'], plate['h'], plate['w']
    lv = plate.get('lv', bolts.get('lv', 35))
    n_rows, s_v = bolts['rows'], bolts['s_v']
    fig.add_shape(type="rect", x0=-40, y0=-h_beam/2-20, x1=0, y1=h_beam/2+20, fillcolor="#cbd5e1", line_width=0)
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor=C_PLATE_FILL, opacity=0.8, line=dict(color=C_BEAM_OUT))
    for i in range(n_rows):
        y_pos = h_pl/2 - lv - (i * s_v)
        fig.add_shape(type="circle", x0=w_pl/2-6, y0=y_pos-6, x1=w_pl/2+6, y1=y_pos+6, fillcolor=C_BOLT_FILL, line_width=0.5)
    add_cad_dim(fig, w_pl+15, h_pl/2, w_pl+15, -h_pl/2, f"H_PL={h_pl}", "vert")
    fig.update_layout(title="<b>ELEVATION VIEW</b>", plot_bgcolor="white", height=350, showlegend=False,
                      xaxis=dict(visible=False, range=[-60, 100]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig

# =============================================================================
# 3. SIDE VIEW (Detailed Section)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl, t_pl = plate['h'], plate['t']
    lv = plate.get('lv', bolts.get('lv', 35))
    n_rows, s_v = bolts['rows'], bolts['s_v']

    # 1. COLUMN BOUNDARY (Yellow Line)
    b_col = b + 40
    fig.add_shape(type="rect", x0=-b_col/2, y0=-h/2-50, x1=b_col/2, y1=h/2+50, 
                  line=dict(color=C_COL_OUTLINE, width=2.5, dash="dash"), fillcolor=C_COL_FILL)

    # 2. BEAM SECTION (With Root Radius)
    path = get_i_section_path(0, 0, h, b, tf, tw, r=12)
    fig.add_shape(type="path", path=path, fillcolor=C_BEAM_FILL, line=dict(color=C_BEAM_OUT, width=1.5))

    # 3. PLATE & BOLTS
    p_x1 = tw/2 + t_pl
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=p_x1, y1=h_pl/2, fillcolor=C_PLATE_FILL, line=dict(color=C_BEAM_OUT))
    for i in range(n_rows):
        y_bolt = h_pl/2 - lv - (i * s_v)
        fig.add_shape(type="rect", x0=p_x1, y0=y_bolt-5, x1=p_x1+15, y1=y_bolt+5, fillcolor=C_BOLT_FILL, line_width=0)

    # 4. DIMENSIONS (No Vertical Red Line)
    add_centerline(fig, -b/2-20, 0, b/2+20, 0)
    add_cad_dim(fig, -b/2, h/2+15, b/2, h/2+15, f"B={int(b)}", offset=25)
    add_cad_dim(fig, b/2+30, h/2, b/2+30, -h/2, f"H={int(h)}", "vert")

    fig.update_layout(title="<b>SIDE VIEW (SECTION)</b>", plot_bgcolor="white", height=450, showlegend=False,
                      xaxis=dict(visible=False, range=[-b_col, b_col]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig

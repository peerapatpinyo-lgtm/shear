import plotly.graph_objects as go

# --- Global Style Config ---
C_COL = "#263238"   # Column (Steel Dark)
C_BEAM = "#F5F5F5"  # Beam (Light Grey)
C_PLATE = "#1976D2" # Plate (Blue)
C_BOLT = "#D32F2F"  # Bolt (Red)
C_DIM = "#37474F"   # Dimension Line

def add_break_line(fig, x, y_top, y_bot):
    """วาดเส้นหยัก (Break Line) แสดงความยาวต่อเนื่องของชิ้นส่วน"""
    mid_y = (y_top + y_bot) / 2
    offset = 12
    path = f"M {x},{y_top} L {x},{mid_y+15} L {x-offset},{mid_y+5} L {x+offset},{mid_y-5} L {x},{mid_y-15} L {x},{y_bot}"
    fig.add_shape(type="path", path=path, line=dict(color=C_COL, width=2))

def add_dim(fig, x0, y0, x1, y1, text, axis="H", offset=60):
    """ฟังก์ชันให้ระยะมาตรฐานวิศวกรรมพร้อม Tick Marks"""
    if axis == "H":
        y_d = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_d+10, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_d+10, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x0, y0=y_d, x1=x1, y1=y_d, line=dict(color=C_DIM, width=1.5))
        for x in [x0, x1]:
            fig.add_shape(type="line", x0=x-4, y0=y_d-4, x1=x+4, y1=y_d+4, line=dict(color=C_DIM, width=2))
        fig.add_annotation(x=(x0+x1)/2, y=y_d, text=text, showarrow=False, yshift=15, font=dict(size=11))
    else:
        x_d = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_d+10, y1=y0, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_d+10, y1=y1, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x_d, y0=y0, x1=x_d, y1=y1, line=dict(color=C_DIM, width=1.5))
        for y in [y0, y1]:
            fig.add_shape(type="line", x0=x_d-4, y0=y-4, x1=x_d+4, y1=y+4, line=dict(color=C_DIM, width=2))
        fig.add_annotation(x=x_d, y=(y0+y1)/2, text=text, showarrow=False, xshift=20, textangle=-90, font=dict(size=11))

# 1. PLAN VIEW (Fixed Error)
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf, w_pl, t_pl = beam['tw'], beam['b'], plate['w'], plate['t']
    # Column Section
    fig.add_shape(type="rect", x0=-40, y0=-bf/2, x1=0, y1=bf/2, fillcolor=C_COL, line_width=0)
    # Beam Web
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+100, y1=tw/2, fillcolor=C_BEAM, line=dict(color=C_COL, width=2))
    # Plate
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE, line_width=0)
    
    add_dim(fig, 0, -bf/2, w_pl, -bf/2, f"W_PL={w_pl}", "H", -50)
    fig.update_layout(xaxis=dict(visible=False, range=[-100, w_pl+200]), yaxis=dict(visible=False, scaleanchor="x"), plot_bgcolor="white", height=400)
    return fig

# 2. ELEVATION VIEW (Fixed Bolt Spacing)
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_b, h_pl, w_pl = beam['h'], plate['h'], plate['w']
    s_v, rows, e1 = bolts['s_v'], bolts['rows'], plate['e1']
    
    # Safe Edge Distance Calculation
    edge_v = (h_pl - (rows - 1) * s_v) / 2 

    # Column
    fig.add_shape(type="rect", x0=-40, y0=-h_b/2-50, x1=0, y1=h_b/2+50, fillcolor=C_COL, line_width=0)
    # Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor="rgba(25,118,210,0.1)", line=dict(color=C_PLATE, width=2))

    # Bolts (Centered)
    for r in range(rows):
        by = (h_pl/2 - edge_v) - r*s_v
        fig.add_shape(type="circle", x0=e1-8, y0=by-8, x1=e1+8, y1=by+8, fillcolor=C_BOLT, line_width=0)

    add_dim(fig, w_pl, h_pl/2, w_pl, -h_pl/2, f"H_PL={h_pl}", "V", 50)
    fig.update_layout(xaxis=dict(visible=False, range=[-100, w_pl+150]), yaxis=dict(visible=False, scaleanchor="x"), plot_bgcolor="white", height=400)
    return fig

# 3. SECTION VIEW (Added Column Flange Lines & Break Line)
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw, t_pl, h_pl = beam['h'], beam['b'], beam['tf'], beam['tw'], plate['t'], plate['h']

    # Column Flange (4 lines to show thickness correctly)
    col_x = -b/2 - 60
    fig.add_shape(type="line", x0=col_x, y0=-h/2-100, x1=col_x, y1=h/2+100, line=dict(color=C_COL, width=3)) # Out-flange
    fig.add_shape(type="line", x0=col_x+12, y0=-h/2-100, x1=col_x+12, y1=h/2+100, line=dict(color=C_COL, width=1.5)) # In-flange

    # I-Beam Section
    p = f"M {-b/2},{-h/2} L {b/2},{-h/2} L {b/2},{-h/2+tf} L {tw/2},{-h/2+tf} L {tw/2},{h/2-tf} L {b/2},{h/2-tf} L {b/2},{h/2} L {-b/2},{h/2} L {-b/2},{h/2-tf} L {-tw/2},{h/2-tf} L {-tw/2},{-h/2+tf} L {-b/2},{-h/2+tf} Z"
    fig.add_shape(type="path", path=p, fillcolor=C_BEAM, line=dict(color=C_COL, width=2.5))
    
    # Shear Plate
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=C_PLATE, line_width=0)

    # Break Line at the end of the beam (ตามที่คุณร่างมา)
    add_break_line(fig, b/2 + 20, h/2, -h/2)

    add_dim(fig, -b/2, h/2, b/2, h/2, f"B={b}", "H", 60)
    fig.update_layout(xaxis=dict(visible=False, range=[col_x-50, b/2+100]), yaxis=dict(visible=False, scaleanchor="x"), plot_bgcolor="white", height=400)
    return fig

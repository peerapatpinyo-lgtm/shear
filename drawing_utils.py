import plotly.graph_objects as go

# --- Global Style Configuration ---
C_STEEL_LINE = "#212121"
C_STEEL_FILL = "#FDFDFD"
C_PLATE_FILL = "rgba(25, 118, 210, 0.12)"
C_BOLT = "#D32F2F"
C_DIM = "#455A64"

def draw_break_line(fig, x, y_top, y_bot):
    """วาดเส้นหยัก (Break Line) สื่อความหมายถึงชิ้นส่วนที่ยาวต่อเนื่อง"""
    mid_y = (y_top + y_bot) / 2
    gap = 12
    # เส้นหยักสไตล์ Z-break
    path = f"M {x},{y_top} L {x},{mid_y+15} L {x-gap},{mid_y+5} L {x+gap},{mid_y-5} L {x},{mid_y-15} L {x},{y_bot}"
    fig.add_shape(type="path", path=path, line=dict(color=C_STEEL_LINE, width=2))

def add_standard_dim(fig, x0, y0, x1, y1, text, axis="H", offset=70):
    """เส้นบอกขนาดแบบ Professional พร้อม Tick Marks"""
    if axis == "H":
        y_pos = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos + (10 if offset>0 else -10), line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos + (10 if offset>0 else -10), line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=C_DIM, width=1.5))
        for x in [x0, x1]:
            fig.add_shape(type="line", x0=x-5, y0=y_pos-5, x1=x+5, y1=y_pos+5, line=dict(color=C_DIM, width=2.5))
        fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=f"<b>{text}</b>", showarrow=False, yshift=18 if offset>0 else -18, font=dict(size=13, color="black"))
    else:
        x_pos = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos + (10 if offset>0 else -10), y1=y0, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos + (10 if offset>0 else -10), y1=y1, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x_pos, y0=y0, x1=x_pos, y1=y1, line=dict(color=C_DIM, width=1.5))
        for y in [y0, y1]:
            fig.add_shape(type="line", x0=x_pos-5, y0=y-5, x1=x_pos+5, y1=y+5, line=dict(color=C_DIM, width=2.5))
        fig.add_annotation(x=x_pos, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=25 if offset>0 else -25, textangle=-90, font=dict(size=13, color="black"))

# 1. PLAN VIEW
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf, w_pl, t_pl = beam['tw'], beam['b'], plate['w'], plate['t']
    # Column
    fig.add_shape(type="rect", x0=-40, y0=-bf/2, x1=0, y1=bf/2, fillcolor=C_STEEL_LINE, line_width=0)
    # Beam
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+150, y1=tw/2, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_LINE, width=2))
    # Plate
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor="#1976D2", line_width=0)
    
    add_standard_dim(fig, 0, -bf/2, w_pl, -bf/2, f"W_PL={w_pl}", "H", -60)
    fig.update_layout(xaxis=dict(visible=False, range=[-100, w_pl+200]), yaxis=dict(visible=False, scaleanchor="x"), plot_bgcolor="white", margin=dict(l=20, r=20, t=50, b=20))
    return fig

# 2. ELEVATION VIEW (Centered Bolts)
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_b, h_pl, w_pl = beam['h'], plate['h'], plate['w']
    s_v, rows, e1 = bolts['s_v'], bolts['rows'], plate['e1']
    # Logic: หาจุดเริ่มต้นเพื่อให้ Bolt อยู่กึ่งกลางความสูง Plate เสมอ
    edge_v = (h_pl - (rows - 1) * s_v) / 2 

    # Column
    fig.add_shape(type="rect", x0=-45, y0=-h_b/2-100, x1=0, y1=h_b/2+100, fillcolor=C_STEEL_LINE, line_width=0)
    # Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor=C_PLATE_FILL, line=dict(color="#1976D2", width=2.5))

    # Bolts (Draw centered)
    for r in range(rows):
        by = (h_pl/2 - edge_v) - r*s_v
        fig.add_shape(type="circle", x0=e1-12, y0=by-12, x1=e1+12, y1=by+12, fillcolor=C_BOLT, line_width=0)

    add_standard_dim(fig, w_pl, h_pl/2, w_pl, -h_pl/2, f"H_PL={h_pl}", "V", 70)
    fig.update_layout(xaxis=dict(visible=False, range=[-100, w_pl+200]), yaxis=dict(visible=False, scaleanchor="x"), plot_bgcolor="white", margin=dict(l=20, r=20, t=50, b=20))
    return fig

# 3. SECTION VIEW (Double Lines & Break Line)
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw, t_pl, h_pl = beam['h'], beam['b'], beam['tf'], beam['tw'], plate['t'], plate['h']

    # --- เส้นคู่บอกความหนาปีกเสา (Column Flange) ---
    c_x = -b/2 - 60
    fig.add_shape(type="line", x0=c_x, y0=-h/2-120, x1=c_x, y1=h/2+120, line=dict(color=C_STEEL_LINE, width=3))
    fig.add_shape(type="line", x0=c_x+18, y0=-h/2-120, x1=c_x+18, y1=h/2+120, line=dict(color=C_STEEL_LINE, width=1.5))

    # I-Beam Section
    p = f"M {-b/2},{-h/2} L {b/2},{-h/2} L {b/2},{-h/2+tf} L {tw/2},{-h/2+tf} L {tw/2},{h/2-tf} L {b/2},{h/2-tf} L {b/2},{h/2} L {-b/2},{h/2} L {-b/2},{h/2-tf} L {-tw/2},{h/2-tf} L {-tw/2},{-h/2+tf} L {-b/2},{-h/2+tf} Z"
    fig.add_shape(type="path", path=p, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_LINE, width=2.5))
    
    # Shear Plate
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor="#1976D2", line_width=0)

    # --- เส้นหยัก Break Line ---
    draw_break_line(fig, b/2 + 30, h/2, -h/2)

    add_standard_dim(fig, -b/2, h/2, b/2, h/2, f"B={b}", "H", 80)
    add_standard_dim(fig, -b/2, h/2, -b/2, -h/2, f"H={h}", "V", -100)

    fig.update_layout(xaxis=dict(visible=False, range=[c_x-100, b/2+200]), yaxis=dict(visible=False, scaleanchor="x"), plot_bgcolor="white", margin=dict(l=20, r=20, t=50, b=20))
    return fig

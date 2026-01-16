import plotly.graph_objects as go

# --- Professional Styling ---
C_STEEL = "#263238"
C_PLATE = "#1976D2"
C_BOLT = "#D32F2F"
C_DIM = "#546E7A"

def add_compact_dim(fig, x0, y0, x1, y1, text, axis="H", offset=40):
    """เส้นบอกขนาดแบบกระชับ ไม่ดึง Viewport ให้กว้างเกินไป"""
    p_off = offset
    if axis == "H":
        y_d = y0 + p_off
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_d+5, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_d+5, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x0, y0=y_d, x1=x1, y1=y_d, line=dict(color=C_DIM, width=1.5))
        for x in [x0, x1]:
            fig.add_shape(type="line", x0=x-3, y0=y_d-3, x1=x+3, y1=y_d+3, line=dict(color=C_DIM, width=2))
        fig.add_annotation(x=(x0+x1)/2, y=y_d, text=f"<b>{text}</b>", showarrow=False, yshift=12, font=dict(size=11))
    else:
        x_d = x0 + p_off
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_d+5, y1=y0, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_d+5, y1=y1, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x_d, y0=y0, x1=x_d, y1=y1, line=dict(color=C_DIM, width=1.5))
        for y in [y0, y1]:
            fig.add_shape(type="line", x0=x_d-3, y0=y-3, x1=x_d+3, y1=y+3, line=dict(color=C_DIM, width=2))
        fig.add_annotation(x=x_d, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=18, textangle=-90, font=dict(size=11))

# 1. PLAN VIEW (Zoomed)
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf, w_pl, t_pl = beam['tw'], beam['b'], plate['w'], plate['t']
    # ชิ้นงาน
    fig.add_shape(type="rect", x0=-20, y0=-bf/2, x1=0, y1=bf/2, fillcolor=C_STEEL, line_width=0)
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+50, y1=tw/2, fillcolor="#F5F5F5", line=dict(color=C_STEEL, width=2))
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE, line_width=0)
    # ขนาด
    add_compact_dim(fig, 0, -bf/2, w_pl, -bf/2, f"W={w_pl}", "H", -40)
    # บีบ Viewport ให้เห็นงานชัดๆ
    fig.update_layout(xaxis=dict(visible=False, range=[-50, w_pl+80]), yaxis=dict(visible=False, range=[-bf/2-60, bf/2+60], scaleanchor="x"), margin=dict(l=5,r=5,t=5,b=5), plot_bgcolor="white")
    return fig

# 2. ELEVATION VIEW (Zoomed)
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_pl, w_pl, s_v, rows, e1 = plate['h'], plate['w'], bolts['s_v'], bolts['rows'], plate['e1']
    edge_v = (h_pl - (rows - 1) * s_v) / 2 

    # Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor="rgba(25,118,210,0.05)", line=dict(color=C_PLATE, width=2))
    # Bolts
    for r in range(rows):
        by = (h_pl/2 - edge_v) - r*s_v
        fig.add_shape(type="circle", x0=e1-8, y0=by-8, x1=e1+8, y1=by+8, fillcolor=C_BOLT, line_width=0)

    add_compact_dim(fig, w_pl, h_pl/2, w_pl, -h_pl/2, f"H_PL={h_pl}", "V", 40)
    # บีบ Viewport เน้นที่แผ่น Plate
    fig.update_layout(xaxis=dict(visible=False, range=[-20, w_pl+100]), yaxis=dict(visible=False, range=[-h_pl/2-50, h_pl/2+50], scaleanchor="x"), margin=dict(l=5,r=5,t=5,b=5), plot_bgcolor="white")
    return fig

# 3. SECTION VIEW (Focus on Connection)
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw, t_pl, h_pl = beam['h'], beam['b'], beam['tf'], beam['tw'], plate['t'], plate['h']

    # Column Flange (เส้นคู่)
    fig.add_shape(type="line", x0=-b/2-15, y0=-h/2-20, x1=-b/2-15, y1=h/2+20, line=dict(color=C_STEEL, width=3))
    fig.add_shape(type="line", x0=-b/2, y0=-h/2-20, x1=-b/2, y1=h/2+20, line=dict(color=C_STEEL, width=1))

    # I-Beam
    p = f"M {-b/2},{-h/2} L {b/2},{-h/2} L {b/2},{-h/2+tf} L {tw/2},{-h/2+tf} L {tw/2},{h/2-tf} L {b/2},{h/2-tf} L {b/2},{h/2} L {-b/2},{h/2} L {-b/2},{h/2-tf} L {-tw/2},{h/2-tf} L {-tw/2},{-h/2+tf} L {-b/2},{-h/2+tf} Z"
    fig.add_shape(type="path", path=p, fillcolor="#F5F5F5", line=dict(color=C_STEEL, width=2))
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=C_PLATE, line_width=0)

    add_compact_dim(fig, -b/2, h/2, b/2, h/2, f"B={b}", "H", 30)
    # บีบ Viewport เน้นหน้าตัดคาน
    fig.update_layout(xaxis=dict(visible=False, range=[-b/2-60, b/2+60]), yaxis=dict(visible=False, range=[-h/2-80, h/2+80], scaleanchor="x"), margin=dict(l=5,r=5,t=5,b=5), plot_bgcolor="white")
    return fig

import plotly.graph_objects as go

# --- Professional Standards Theme ---
C_STEEL_DARK = "#263238"  # สีเสา/ขอบเหล็ก
C_STEEL_LIGHT = "#F5F5F5" # สีเนื้อเหล็กคาน
C_PLATE = "#1976D2"      # สี Plate
C_BOLT = "#D32F2F"       # สีโบลท์
C_DIM = "#37474F"        # สีเส้นบอกขนาด

def add_break_line(fig, x, y_top, y_bot):
    """วาดเส้นหยัก (Break Line) สัญลักษณ์สากลตามที่คุณแนะนำ"""
    mid_y = (y_top + y_bot) / 2
    gap = 12
    path = f"M {x},{y_top} L {x},{mid_y+15} L {x-gap},{mid_y+5} L {x+gap},{mid_y-5} L {x},{mid_y-15} L {x},{y_bot}"
    fig.add_shape(type="path", path=path, line=dict(color=C_STEEL_DARK, width=2))

def add_pro_dim(fig, x0, y0, x1, y1, text, axis="H", offset=60):
    """เส้นบอกขนาดระดับสากลพร้อม Tick Marks"""
    p_off = offset
    if axis == "H":
        y_d = y0 + p_off
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_d+(10 if p_off>0 else -10), line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_d+(10 if p_off>0 else -10), line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x0, y0=y_d, x1=x1, y1=y_d, line=dict(color=C_DIM, width=1.5))
        for x in [x0, x1]:
            fig.add_shape(type="line", x0=x-4, y0=y_d-4, x1=x+4, y1=y_d+4, line=dict(color=C_DIM, width=2))
        fig.add_annotation(x=(x0+x1)/2, y=y_d, text=text, showarrow=False, yshift=15 if p_off>0 else -15, font=dict(size=12, color="black", family="Arial Black"))
    else:
        x_d = x0 + p_off
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_d+(10 if p_off>0 else -10), y1=y0, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_d+(10 if p_off>0 else -10), y1=y1, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x_d, y0=y0, x1=x_d, y1=y1, line=dict(color=C_DIM, width=1.5))
        for y in [y0, y1]:
            fig.add_shape(type="line", x0=x_d-4, y0=y-4, x1=x_d+4, y1=y+4, line=dict(color=C_DIM, width=2))
        fig.add_annotation(x=x_d, y=(y0+y1)/2, text=text, showarrow=False, xshift=20 if p_off>0 else -20, textangle=-90, font=dict(size=12, color="black", family="Arial Black"))

# 1. PLAN VIEW
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf, w_pl, t_pl = beam['tw'], beam['b'], plate['w'], plate['t']
    fig.add_shape(type="rect", x0=-40, y0=-bf/2, x1=0, y1=bf/2, fillcolor=C_STEEL_DARK, line_width=0)
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+150, y1=tw/2, fillcolor=C_STEEL_LIGHT, line=dict(color=C_STEEL_DARK, width=2))
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE, line_width=0)
    add_pro_dim(fig, 0, -bf/2, w_pl, -bf/2, f"W_PL={w_pl}", "H", -60)
    fig.update_layout(xaxis=dict(visible=False, range=[-100, w_pl+200]), yaxis=dict(visible=False, scaleanchor="x"), plot_bgcolor="white", margin=dict(l=10, r=10, t=40, b=10))
    return fig

# 2. ELEVATION VIEW (Front)
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_b, h_pl, w_pl = beam['h'], plate['h'], plate['w']
    s_v, rows, e1 = bolts['s_v'], bolts['rows'], plate['e1']
    edge_v = (h_pl - (rows - 1) * s_v) / 2 # คำนวณระยะขอบให้อยู่กึ่งกลางพอดี

    fig.add_shape(type="rect", x0=-40, y0=-h_b/2-80, x1=0, y1=h_b/2+80, fillcolor=C_STEEL_DARK, line_width=0)
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor="rgba(25,118,210,0.1)", line=dict(color=C_PLATE, width=2.5))

    for r in range(rows):
        by = (h_pl/2 - edge_v) - r*s_v
        fig.add_shape(type="circle", x0=e1-10, y0=by-10, x1=e1+10, y1=by+10, fillcolor=C_BOLT, line_width=0)

    add_pro_dim(fig, w_pl, h_pl/2, w_pl, -h_pl/2, f"H_PL={h_pl}", "V", 60)
    fig.update_layout(xaxis=dict(visible=False, range=[-100, w_pl+200]), yaxis=dict(visible=False, scaleanchor="x"), plot_bgcolor="white", margin=dict(l=10, r=10, t=40, b=10))
    return fig

# 3. SECTION VIEW (Side)
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw, t_pl, h_pl = beam['h'], beam['b'], beam['tf'], beam['tw'], plate['t'], plate['h']

    # --- เส้นคู่ปีกเสา (4 เส้น - แสดงความหนาจริง) ---
    col_x = -b/2 - 50
    fig.add_shape(type="line", x0=col_x, y0=-h/2-100, x1=col_x, y1=h/2+100, line=dict(color=C_STEEL_DARK, width=3))
    fig.add_shape(type="line", x0=col_x+15, y0=-h/2-100, x1=col_x+15, y1=h/2+100, line=dict(color=C_STEEL_DARK, width=1.5))

    # หน้าตัด I-Beam
    p = f"M {-b/2},{-h/2} L {b/2},{-h/2} L {b/2},{-h/2+tf} L {tw/2},{-h/2+tf} L {tw/2},{h/2-tf} L {b/2},{h/2-tf} L {b/2},{h/2} L {-b/2},{h/2} L {-b/2},{h/2-tf} L {-tw/2},{h/2-tf} L {-tw/2},{-h/2+tf} L {-b/2},{-h/2+tf} Z"
    fig.add_shape(type="path", path=p, fillcolor=C_STEEL_LIGHT, line=dict(color=C_STEEL_DARK, width=2.5))
    
    # Plate แปะข้าง Web
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=C_PLATE, line_width=0)

    # --- เส้นหยัก (Break Line) ที่ปลายคานด้านขวา ---
    add_break_line(fig, b/2 + 25, h/2, -h/2)

    add_pro_dim(fig, -b/2, h/2, b/2, h/2, f"B={b}", "H", 70)
    add_pro_dim(fig, -b/2, h/2, -b/2, -h/2, f"H={h}", "V", -80)

    fig.update_layout(xaxis=dict(visible=False, range=[col_x-100, b/2+150]), yaxis=dict(visible=False, scaleanchor="x"), plot_bgcolor="white", margin=dict(l=10, r=10, t=40, b=10))
    return fig

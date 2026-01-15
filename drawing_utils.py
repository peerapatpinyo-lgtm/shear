import plotly.graph_objects as go
import numpy as np

# =============================================================================
# 🛠️ HELPER: CAD STYLES
# =============================================================================
def get_hatch_pattern(color="black", bg_color="white"):
    """ คืนค่า config สำหรับลาย Hatching (ลายตัดขวาง) """
    return dict(shape="/", solidity=0.3, size=10, fgcolor=color, bgcolor=bg_color)

def add_cad_dim(fig, x0, y0, x1, y1, text, type="horiz", offset=0, color="black", is_error=False):
    """ เส้นบอกระยะ Dimension (ถ้า Error จะเป็นสีแดง) """
    final_color = "red" if is_error else color
    arrow_size = 5
    
    # Line Style
    line_dict = dict(color=final_color, width=1)
    ext_dict = dict(color=final_color, width=0.5)

    if type == "horiz":
        y_dim = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_dim, line=ext_dict)
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_dim, line=ext_dict)
        fig.add_shape(type="line", x0=x0, y0=y_dim, x1=x1, y1=y_dim, line=line_dict)
        # Arrows
        fig.add_annotation(x=x0, y=y_dim, ax=arrow_size, ay=0, arrowhead=2, arrowsize=1.5, arrowcolor=final_color, text="")
        fig.add_annotation(x=x1, y=y_dim, ax=-arrow_size, ay=0, arrowhead=2, arrowsize=1.5, arrowcolor=final_color, text="")
        # Text
        fig.add_annotation(x=(x0+x1)/2, y=y_dim, text=f"<b>{text}</b>", showarrow=False, yshift=7 if offset>0 else -7,
                           font=dict(size=10, color=final_color), bgcolor="white")

    elif type == "vert":
        x_dim = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_dim, y1=y0, line=ext_dict)
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_dim, y1=y1, line=ext_dict)
        fig.add_shape(type="line", x0=x_dim, y0=y0, x1=x_dim, y1=y1, line=line_dict)
        # Arrows
        fig.add_annotation(x=x_dim, y=y0, ax=0, ay=-arrow_size, arrowhead=2, arrowsize=1.5, arrowcolor=final_color, text="")
        fig.add_annotation(x=x_dim, y=y1, ax=0, ay=arrow_size, arrowhead=2, arrowsize=1.5, arrowcolor=final_color, text="")
        # Text
        fig.add_annotation(x=x_dim, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=10 if offset>0 else -10,
                           font=dict(size=10, color=final_color), textangle=-90, bgcolor="white")

def add_weld_symbol(fig, x, y, size=6, ax=40, ay=-40):
    """ สัญลักษณ์การเชื่อม (Weld Symbol) """
    # Leader line
    fig.add_annotation(x=x, y=y, ax=ax, ay=ay, arrowhead=2, arrowsize=1, arrowwidth=1.5, text="", arrowcolor="black")
    # Reference Line (Horizontal)
    end_x = x + (ax if ax!=0 else 40)
    end_y = y + (ay if ay!=0 else -40)
    ref_len = 30
    
    # Draw Reference line tail
    fig.add_shape(type="line", x0=end_x, y0=end_y, x1=end_x + ref_len, y1=end_y, line=dict(color="black", width=1.5))
    
    # Triangle (Fillet Weld Symbol) - Below line
    tri_x = end_x + 10
    fig.add_shape(type="path", path=f"M {tri_x} {end_y} L {tri_x} {end_y+8} L {tri_x+8} {end_y} Z", line_width=1, line_color="black", fillcolor="white")
    
    # Size Text
    fig.add_annotation(x=tri_x-5, y=end_y+4, text=f"<b>{size}</b>", showarrow=False, font=dict(size=10))

def add_centerline(fig, x0, y0, x1, y1):
    fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color="#d55", width=1, dash="dashdot"), opacity=0.7)

# =============================================================================
# 📐 VIEW 1: PLAN VIEW (HATCHED)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf = beam['tw'], beam['b']
    w_pl, t_pl, e1, l_side = plate['w'], plate['t'], plate['e1'], plate['l_side']
    d_bolt, n_cols, s_h = bolts['d'], bolts['cols'], bolts['s_h']
    
    zoom_y = max(bf, 160) * 0.7
    zoom_x = w_pl + 80

    # 1. Column Cut (Hatch Pattern)
    fig.add_trace(go.Scatter(
        x=[-20, 0, 0, -20, -20], y=[-zoom_y, -zoom_y, zoom_y, zoom_y, -zoom_y],
        fill="toself", fillpattern=get_hatch_pattern(), mode='lines', line=dict(color="black", width=2),
        hoverinfo='skip', showlegend=False
    ))
    
    # 2. Beam Web Cut (Hatch Pattern)
    fig.add_trace(go.Scatter(
        x=[10, zoom_x, zoom_x, 10, 10], y=[-tw/2, -tw/2, tw/2, tw/2, -tw/2],
        fill="toself", fillpattern=get_hatch_pattern(), mode='lines', line=dict(color="black", width=1.5),
        hoverinfo='skip', showlegend=False
    ))
    
    # CL
    add_centerline(fig, -30, 0, zoom_x, 0)

    # 3. Fin Plate (Solid White)
    py_max = tw/2 + t_pl
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=py_max, line=dict(color="black", width=1.5), fillcolor="white")
    
    # 4. Weld Symbol
    add_weld_symbol(fig, 0, py_max, size=6, ax=-20, ay=-40)

    # 5. Bolts
    bx_start = e1
    for i in range(n_cols):
        bx = bx_start + i*s_h
        # Shank & Head
        fig.add_shape(type="rect", x0=bx-d_bolt/2, y0=-tw/2, x1=bx+d_bolt/2, y1=py_max, line_width=1, fillcolor="#f0f0f0")
        fig.add_shape(type="rect", x0=bx-d_bolt, y0=py_max, x1=bx+d_bolt, y1=py_max+(d_bolt*0.6), line_width=1, fillcolor="white")
        add_centerline(fig, bx, -zoom_y+15, bx, zoom_y-15)

    # Dimensions with Error Check
    dim_y = -zoom_y + 25
    curr_x = 0
    err_e1 = e1 < 1.5*d_bolt
    add_cad_dim(fig, curr_x, dim_y, curr_x+e1, dim_y, f"e1={e1:.0f}", is_error=err_e1)
    
    curr_x += e1
    if n_cols > 1:
        err_sh = s_h < 3*d_bolt
        for _ in range(n_cols-1):
            add_cad_dim(fig, curr_x, dim_y, curr_x+s_h, dim_y, f"sh={s_h:.0f}", is_error=err_sh)
            curr_x += s_h
            
    err_ls = l_side < 1.5*d_bolt
    add_cad_dim(fig, curr_x, dim_y, w_pl, dim_y, f"Ls={l_side:.0f}", is_error=err_ls)

    fig.update_layout(title="<b>PLAN VIEW</b> (Section Cut)", plot_bgcolor="white", margin=dict(l=10,r=10,t=40,b=10), height=300,
                      xaxis=dict(visible=False, range=[-30, zoom_x], fixedrange=True),
                      yaxis=dict(visible=False, range=[-zoom_y, zoom_y], scaleanchor="x", scaleratio=1, fixedrange=True), showlegend=False)
    return fig

# =============================================================================
# 📐 VIEW 2: ELEVATION (CLEAN)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    # Unpack...
    h_beam, tf = beam['h'], beam['tf']
    h_pl, w_pl, lv, e1 = plate['h'], plate['w'], plate['lv'], plate['e1']
    s_v, s_h = bolts['s_v'], bolts['s_h']
    d_bolt, n_rows, n_cols = bolts['d'], bolts['rows'], bolts['cols']

    # 1. Beam Ghost
    fig.add_shape(type="rect", x0=0, y0=-h_beam/2, x1=w_pl+50, y1=h_beam/2, line=dict(color="#bbb", width=1, dash="dash"))
    
    # 2. Column Face (Hatch)
    fig.add_trace(go.Scatter(
        x=[-20, 0, 0, -20, -20], y=[-h_beam/2-20, -h_beam/2-20, h_beam/2+20, h_beam/2+20, -h_beam/2-20],
        fill="toself", fillpattern=get_hatch_pattern(), mode='lines', line=dict(color="black", width=2),
        hoverinfo='skip', showlegend=False
    ))

    # 3. Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, line=dict(color="black", width=1.5), fillcolor="white")

    # 4. Bolts with Cross
    by_start = h_pl/2 - lv
    for r in range(n_rows):
        for c in range(n_cols):
            bx = e1 + c*s_h
            by = by_start - r*s_v
            # Hole Circle
            fig.add_shape(type="circle", x0=bx-d_bolt/2, y0=by-d_bolt/2, x1=bx+d_bolt/2, y1=by+d_bolt/2, line_color="black", fillcolor="white")
            # Center Mark
            fig.add_shape(type="line", x0=bx-d_bolt/2-2, y0=by, x1=bx+d_bolt/2+2, y1=by, line_width=0.5)
            fig.add_shape(type="line", x0=bx, y0=by-d_bolt/2-2, x1=bx, y1=by+d_bolt/2+2, line_width=0.5)

    # CL
    add_centerline(fig, -10, 0, w_pl+20, 0) 

    # Dimensions
    dim_x = w_pl + 15
    curr_y = h_pl/2
    err_lv = lv < 1.5*d_bolt
    add_cad_dim(fig, dim_x, curr_y, dim_x, curr_y-lv, f"{lv:.0f}", "vert", is_error=err_lv)
    curr_y -= lv
    
    if n_rows > 1:
        err_sv = s_v < 3*d_bolt
        for _ in range(n_rows-1):
            add_cad_dim(fig, dim_x, curr_y, dim_x, curr_y-s_v, f"{s_v:.0f}", "vert", is_error=err_sv)
            curr_y -= s_v
            
    add_cad_dim(fig, dim_x, curr_y, dim_x, -h_pl/2, f"{lv:.0f}", "vert", is_error=err_lv)

    fig.update_layout(title="<b>ELEVATION</b> (Front View)", plot_bgcolor="white", margin=dict(l=10,r=30,t=40,b=10), height=300,
                      xaxis=dict(visible=False, range=[-30, w_pl+70], fixedrange=True),
                      yaxis=dict(visible=False, range=[-h_beam/2-30, h_beam/2+30], scaleanchor="x", scaleratio=1, fixedrange=True), showlegend=False)
    return fig

# =============================================================================
# 📐 VIEW 3: SIDE VIEW (REALISTIC I-BEAM)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    t_pl, h_pl, lv = plate['t'], plate['h'], plate['lv']
    d_bolt, n_rows, s_v = bolts['d'], bolts['rows'], bolts['s_v']

    # 1. Column Face
    fig.add_shape(type="line", x0=-b/2, y0=-h/2-20, x1=-b/2, y1=h/2+20, line=dict(color="black", width=2))
    # Hatching for column
    fig.add_trace(go.Scatter(
        x=[-b/2-20, -b/2, -b/2, -b/2-20, -b/2-20], y=[-h/2-20, -h/2-20, h/2+20, h/2+20, -h/2-20],
        fill="toself", fillpattern=get_hatch_pattern(), mode='lines', line_width=0, hoverinfo='skip', showlegend=False
    ))

    # 2. I-Beam Section (Detailed with Fillet simulation using simple shapes)
    # Flanges
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, line=dict(color="black", width=1.5), fillcolor="white")
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, line=dict(color="black", width=1.5), fillcolor="white")
    # Web
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, line=dict(color="black", width=1.5), fillcolor="white")
    # Fillet (Circle overlay to simulate curve) - Cosmetic
    r = 8
    # Top Left Fillet
    fig.add_shape(type="path", path=f"M {-tw/2} {h/2-tf-r} Q {-tw/2} {h/2-tf} {-tw/2-r} {h/2-tf} L {-tw/2} {h/2-tf} Z", fillcolor="black")
    # (ทำแค่พอสังเขปเพื่อให้ดูมีความเป็น I-Beam จริง)

    # 3. Plate
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, line=dict(color="black", width=1.5), fillcolor="#ddd")

    # 4. Bolts (Hex Head Side View simulation)
    bolt_x = tw/2 + t_pl
    by_start = h_pl/2 - lv
    for r in range(n_rows):
        by = by_start - r*s_v
        # Washer
        fig.add_shape(type="rect", x0=bolt_x, y0=by-d_bolt/2-2, x1=bolt_x+2, y1=by+d_bolt/2+2, fillcolor="black", line_width=0)
        # Head
        fig.add_shape(type="rect", x0=bolt_x+2, y0=by-d_bolt/2, x1=bolt_x+(d_bolt*0.6), y1=by+d_bolt/2, line=dict(color="black", width=1), fillcolor="white")
        add_centerline(fig, -b/2, by, b/2, by)

    add_centerline(fig, 0, -h/2-30, 0, h/2+30)

    fig.update_layout(title="<b>SIDE VIEW</b> (Section)", plot_bgcolor="white", margin=dict(l=10,r=10,t=40,b=10), height=300,
                      xaxis=dict(visible=False, range=[-b/2-30, b/2+40], fixedrange=True),
                      yaxis=dict(visible=False, range=[-h/2-30, h/2+30], scaleanchor="x", scaleratio=1, fixedrange=True), showlegend=False)
    return fig

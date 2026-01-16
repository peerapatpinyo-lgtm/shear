# drawing_utils.py (V13 - Professional Edition)
import plotly.graph_objects as go
import numpy as np

# =============================================================================
# 🎨 CAD STYLE CONFIGURATION (Standard Engineering Styles)
# =============================================================================
STYLE = {
    "STEEL_CUT":   dict(fillcolor="rgba(200, 200, 200, 0.3)", line=dict(color="black", width=2), fillpattern=dict(shape="/", fgcolor="black", size=5, solidity=0.3)),
    "STEEL_SOLID": dict(fillcolor="#F0F2F5", line=dict(color="#333333", width=2)),
    "PLATE":       dict(fillcolor="#E3F2FD", line=dict(color="#0277BD", width=2)),
    "BOLT":        dict(fillcolor="#455A64", line=dict(color="black", width=1)),
    "HIDDEN":      dict(line=dict(color="#777777", width=1, dash="dash")),
    "CENTER":      dict(line=dict(color="#DC2626", width=1, dash="dashdot")),
    "WELD":        dict(line=dict(color="#000000", width=0), fillcolor="#000000"),
    "DIM":         dict(color="#1E3A8A", width=1, arrow_size=1.5)
}

# =============================================================================
# 🛠️ HELPER FUNCTIONS (CAD TOOLS)
# =============================================================================

def add_dimension(fig, x0, y0, x1, y1, text, offset=30, type="h"):
    """
    ฟังก์ชันเขียน Dimension แบบมืออาชีพ (มีหัวลูกศร, Extension Lines)
    """
    # คำนวณตำแหน่งเส้น Dimension
    if type == "h": # Horizontal
        dy = offset
        dx = 0
        txt_x, txt_y = (x0 + x1) / 2, y0 + dy + 5
        # Extension Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y0+dy+2, line=dict(color=STYLE['DIM']['color'], width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y1+dy+2, line=dict(color=STYLE['DIM']['color'], width=0.5))
    else: # Vertical
        dx = offset
        dy = 0
        txt_x, txt_y = x0 + dx + 10, (y0 + y1) / 2
        # Extension Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0+dx+2, y1=y0, line=dict(color=STYLE['DIM']['color'], width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1+dx+2, y1=y1, line=dict(color=STYLE['DIM']['color'], width=0.5))

    # เส้นหลัก (Dimension Line) พร้อมหัวลูกศรใช้ Annotation
    fig.add_annotation(
        x=x1, y=y1+dy if type=="h" else y1,
        ax=x0, ay=y0+dy if type=="h" else y0,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=2, arrowsize=1.5, arrowwidth=1, arrowcolor=STYLE['DIM']['color'],
        text=""
    )
    
    # Text Label
    fig.add_annotation(
        x=txt_x, y=txt_y, text=f"<b>{text}</b>",
        showarrow=False, font=dict(size=12, color=STYLE['DIM']['color'], family="Arial"),
        textangle=0 if type == "h" else -90
    )

def draw_break_line(fig, x, y_start, y_end, width=10, orientation="v"):
    """วาดเส้น Break Line (ZigZag) เพื่อแสดงว่าชิ้นงานมีความยาวต่อเนื่อง"""
    zigzag = 5
    if orientation == "v":
        path = f"M {x} {y_start} L {x-zigzag} {y_start + (y_end-y_start)*0.25} L {x+zigzag} {y_start + (y_end-y_start)*0.75} L {x} {y_end}"
    else:
        path = f"M {x} {y_start} L {x + (width)*0.25} {y_start-zigzag} L {x + (width)*0.75} {y_start+zigzag} L {x+width} {y_start}"
    
    fig.add_shape(type="path", path=path, line=dict(color="black", width=1))

def draw_bolt_head(fig, x, y, d, type="top"):
    """วาดน็อตให้ดูเหมือนจริง (Hexagon Head หรือ Circle with Crosshair)"""
    r = d/2 * 1.5 # Nut size approx 1.5d
    
    if type == "top": # Plan/Elev View (Circle + Cross)
        fig.add_shape(type="circle", x0=x-r, y0=y-r, x1=x+r, y1=y+r, 
                      fillcolor="white", line=dict(color="black", width=1))
        fig.add_shape(type="circle", x0=x-d/2, y0=y-d/2, x1=x+d/2, y1=y+d/2, 
                      line=dict(color="black", width=1))
        # Crosshair (Center line)
        fig.add_shape(type="line", x0=x-r*1.2, y0=y, x1=x+r*1.2, y1=y, line=STYLE['CENTER']['line'])
        fig.add_shape(type="line", x0=x, y0=y-r*1.2, x1=x, y1=y+r*1.2, line=STYLE['CENTER']['line'])
    
    elif type == "side": # Side View (Hex Head)
        h_nut = d * 0.8
        w_nut = d * 1.6
        # Nut
        fig.add_shape(type="rect", x0=x, y0=y-w_nut/2, x1=x+h_nut, y1=y+w_nut/2, 
                      fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black", width=1))
        # Washer
        fig.add_shape(type="rect", x0=x, y0=y-w_nut/2-2, x1=x+3, y1=y+w_nut/2+2, 
                      fillcolor="white", line=dict(color="black", width=1))

# =============================================================================
# 1. PLAN VIEW (TOP DOWN)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    
    # Parameters
    tw, bf = beam['tw'], beam['b']
    tp, wp, e1 = plate['t'], plate['w'], plate['e1']
    
    # 1. Column Face (Reference)
    fig.add_shape(type="line", x0=0, y0=-bf/2-20, x1=0, y1=bf/2+20, line=dict(color="black", width=3))
    
    # 2. Beam (Top Flange - Visible)
    fig.add_trace(go.Scatter(
        x=[0, wp+50, wp+50, 0, 0], 
        y=[-tw/2, -tw/2, tw/2, tw/2, -tw/2],
        fill="toself", mode="lines", name="Beam Web (Cut)",
        line=dict(color="black", width=0), fillpattern=STYLE['STEEL_CUT']['fillpattern']
    ))
    
    # 3. Plate (Visible)
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=wp, y1=tw/2+tp, 
                  fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
    
    # 4. Weld Symbol (Fillet at junction)
    weld_s = 5
    path_weld = f"M 0 {tw/2} L {weld_s} {tw/2} L 0 {tw/2+weld_s} Z"
    fig.add_shape(type="path", path=path_weld, fillcolor="black", line_width=0)
    
    # 5. Bolts (Top View - Indication)
    # แสดงแนว Bolt row แรก
    bolt_x = e1
    draw_bolt_head(fig, bolt_x, tw/2+tp+5, bolts['d'], "top") # Just a representative bolt line
    
    # 6. Centerline
    fig.add_shape(type="line", x0=-10, y0=0, x1=wp+60, y1=0, line=STYLE['CENTER']['line'])
    
    # Dimensions
    add_dimension(fig, 0, tw/2+tp, wp, tw/2+tp, f"W_pl = {wp}", 40, "h")
    add_dimension(fig, wp, tw/2, wp, tw/2+tp, f"t_pl={tp}", 20, "v")

    fig.update_layout(title="<b>PLAN VIEW</b> (Top Down)", plot_bgcolor="white", height=300, 
                      showlegend=False, xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

# =============================================================================
# 2. ELEVATION VIEW (FRONT)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    
    # Params
    h_beam = beam['h']
    h_pl, w_pl = plate['h'], plate['w']
    lv, sv, rows, cols, sh = plate['lv'], bolts['s_v'], bolts['rows'], bolts['cols'], bolts['s_h']
    e1 = plate['e1']

    # 1. Column Limit Line
    fig.add_shape(type="line", x0=0, y0=-h_beam/2-20, x1=0, y1=h_beam/2+20, line=dict(color="black", width=4))
    
    # 2. Beam Web (Background)
    fig.add_shape(type="rect", x0=0, y0=-h_beam/2, x1=w_pl+100, y1=h_beam/2, 
                  fillcolor="white", line=dict(color="#555", width=2))
    # Break Line for Beam
    draw_break_line(fig, w_pl+100, -h_beam/2, h_beam/2)
    
    # 3. Connection Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, 
                  fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
    
    # 4. Bolts Pattern (Loop)
    start_y = h_pl/2 - lv
    start_x = e1
    
    for c in range(cols):
        current_x = start_x + (c * sh)
        for r in range(rows):
            current_y = start_y - (r * sv)
            draw_bolt_head(fig, current_x, current_y, bolts['d'], "top")
    
    # 5. Dimensions
    add_dimension(fig, w_pl+10, h_pl/2, w_pl+10, -h_pl/2, f"H_pl = {h_pl}", 30, "v")
    add_dimension(fig, 0, -h_pl/2, w_pl, -h_pl/2, f"W_pl = {w_pl}", 30, "h")
    
    # Detail Dimensions (Spacing)
    if rows > 1:
        add_dimension(fig, start_x, start_y, start_x, start_y-sv, f"s={sv}", 50, "v")
    
    # 6. Centerlines
    fig.add_shape(type="line", x0=-20, y0=0, x1=w_pl+120, y1=0, line=STYLE['CENTER']['line'])

    fig.update_layout(title="<b>ELEVATION VIEW</b> (Front)", plot_bgcolor="white", height=400,
                      showlegend=False, xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

# =============================================================================
# 3. SIDE VIEW (SECTION A-A)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl, t_pl = plate['h'], plate['t']
    lv, s_v, rows = plate['lv'], bolts['s_v'], bolts['rows']
    d_bolt = bolts['d']

    # 1. Column Section (Left & Right - Ghosted)
    # Left Col Flange
    fig.add_trace(go.Scatter(
        x=[-b/2, -b/2, -b/2-tf, -b/2-tf], y=[-h/2-50, h/2+50, h/2+50, -h/2-50],
        fill="toself", mode="lines", line=dict(color="black"), fillpattern=STYLE['STEEL_CUT']['fillpattern'], name="Column"
    ))
    # Right Col Flange
    fig.add_trace(go.Scatter(
        x=[b/2, b/2, b/2+tf, b/2+tf], y=[-h/2-50, h/2+50, h/2+50, -h/2-50],
        fill="toself", mode="lines", line=dict(color="black"), fillpattern=STYLE['STEEL_CUT']['fillpattern'], showlegend=False
    ))

    # 2. I-Beam Cross Section (The Main Actor)
    # Web
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, 
                  fillcolor=STYLE['STEEL_SOLID']['fillcolor'], line=dict(color="black", width=2))
    # Flanges
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, 
                  fillcolor=STYLE['STEEL_SOLID']['fillcolor'], line=dict(color="black", width=2))
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, 
                  fillcolor=STYLE['STEEL_SOLID']['fillcolor'], line=dict(color="black", width=2))
    
    # Fillets (Radius at k-distance) - The Professional Touch
    k = tf + 10 # approximate k
    # Top Right
    fig.add_shape(type="path", path=f"M {tw/2} {h/2-tf} Q {tw/2+5} {h/2-tf-5} {tw/2+5} {h/2-tf-5} L {tw/2} {h/2-tf}", fillcolor="black")
    
    # 3. Connection Plate (Side Profile)
    # Plate sits on the Web
    p_x_start = tw/2
    p_x_end = tw/2 + t_pl
    fig.add_trace(go.Scatter(
        x=[p_x_start, p_x_end, p_x_end, p_x_start], 
        y=[h_pl/2, h_pl/2, -h_pl/2, -h_pl/2],
        fill="toself", mode="lines", line=dict(color="#01579B", width=2), 
        fillpattern=dict(shape="x", fgcolor="#0288D1", size=5, solidity=0.2), name="Shear Plate"
    ))

    # 4. Bolts (Side View - Shank & Head)
    start_y = h_pl/2 - lv
    for r in range(rows):
        y_bolt = start_y - (r * s_v)
        # Bolt Shank (Passes through Web + Plate)
        fig.add_shape(type="rect", x0=-tw/2-15, y0=y_bolt-d_bolt/2, x1=p_x_end+15, y1=y_bolt+d_bolt/2,
                      fillcolor="#90A4AE", line=dict(width=0))
        # Bolt Head (Right side - Nut)
        draw_bolt_head(fig, p_x_end, y_bolt, d_bolt, "side")
        # Bolt Head (Left side - Head)
        draw_bolt_head(fig, -tw/2-d_bolt*0.8, y_bolt, d_bolt, "side")
        # Centerline for bolt
        fig.add_shape(type="line", x0=-b/2-20, y0=y_bolt, x1=b/2+20, y1=y_bolt, line=STYLE['CENTER']['line'])

    # 5. Dimensions
    add_dimension(fig, -b/2, h/2, b/2, h/2, f"b={b}", 40, "h")
    add_dimension(fig, b/2, h/2, b/2, -h/2, f"d={h}", 60, "v")
    add_dimension(fig, p_x_start, -h_pl/2, p_x_end, -h_pl/2, f"t={t_pl}", 20, "h")

    fig.update_layout(title="<b>SECTION VIEW</b> (Detailed)", plot_bgcolor="white", height=500,
                      showlegend=False, xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

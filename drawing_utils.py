import plotly.graph_objects as go

# ==========================================
# 🎨 STYLES
# ==========================================
STYLE = {
    'STEEL_CUT':   dict(fillcolor="#D1D5DB", line=dict(color="black", width=2)),
    'STEEL_FACE':  dict(fillcolor="#F3F4F6", line=dict(color="#6B7280", width=1)),
    'PLATE':       dict(fillcolor="#BFDBFE", line=dict(color="#1E3A8A", width=2)),
    'ANGLE':       dict(fillcolor="#C7D2FE", line=dict(color="#312E81", width=2)),
    'BOLT':        dict(fillcolor="#374151", line=dict(color="black", width=1)),
    'CL':          dict(color="#DC2626", width=1, dash="dashdot"),
    'DIM':         dict(color="#1D4ED8", family="Arial", size=11),
    'ERROR':       dict(color="#EF4444", width=2, dash="dash")
}

# ==========================================
# 🛠️ HELPER FUNCTIONS
# ==========================================
def add_dim(fig, x0, y0, x1, y1, text, offset=30, type="h"):
    c = STYLE['DIM']['color']
    if type == "h": 
        y_pos = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=c, width=1))
        dir = 1 if offset >= 0 else -1
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos+(5*dir), line=dict(color=c, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos+(5*dir), line=dict(color=c, width=0.5))
        fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=f"<b>{text}</b>", showarrow=False, yshift=10*dir, font=dict(size=11, color=c))
    else:
        x_pos = x0 + offset
        dir = 1 if offset >= 0 else -1
        fig.add_shape(type="line", x0=x_pos, y0=y0, x1=x_pos, y1=y1, line=dict(color=c, width=1))
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos+(5*dir), y1=y0, line=dict(color=c, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos+(5*dir), y1=y1, line=dict(color=c, width=0.5))
        fig.add_annotation(x=x_pos, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=15*dir, textangle=-90, font=dict(size=11, color=c))

def add_leader(fig, x, y, text, ax=40, ay=-40, align="left"):
    fig.add_annotation(x=x, y=y, ax=ax, ay=ay, axref="pixel", ayref="pixel", text=f"<b>{text}</b>", showarrow=True, arrowhead=2, arrowsize=1, font=dict(size=11), align=align, bgcolor="rgba(255,255,255,0.8)")

def draw_h_section(fig, x, y, h, b, tf, tw, style, view="I"):
    if view == "I":
        fig.add_shape(type="path", path=f"M {x-tw/2} {y-h/2+tf} L {x-tw/2} {y+h/2-tf} L {x+tw/2} {y+h/2-tf} L {x+tw/2} {y-h/2+tf} Z", fillcolor=style['fillcolor'], line=dict(width=0))
        fig.add_shape(type="rect", x0=x-b/2, y0=y+h/2-tf, x1=x+b/2, y1=y+h/2, fillcolor=style['fillcolor'], line=style['line'])
        fig.add_shape(type="rect", x0=x-b/2, y0=y-h/2, x1=x+b/2, y1=y-h/2+tf, fillcolor=style['fillcolor'], line=style['line'])
    else: # H shape (Top view)
        fig.add_shape(type="rect", x0=x-h/2, y0=y-b/2, x1=x-h/2+tf, y1=y+b/2, fillcolor=style['fillcolor'], line=style['line'])
        fig.add_shape(type="rect", x0=x+h/2-tf, y0=y-b/2, x1=x+h/2, y1=y+b/2, fillcolor=style['fillcolor'], line=style['line'])
        fig.add_shape(type="rect", x0=x-h/2+tf, y0=y-tw/2, x1=x+h/2-tf, y1=y+tw/2, fillcolor=style['fillcolor'], line=style['line'])

def force_range(fig, limit):
    fig.update_layout(xaxis=dict(range=[-limit, limit], visible=False, scaleanchor="y", scaleratio=1), 
                      yaxis=dict(range=[-limit, limit], visible=False), 
                      height=500, margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor="white")

# ==========================================
# 1. FRONT VIEW
# ==========================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    ctype = plate['type']
    h_pl, w_pl = plate['h'], plate['w']
    lv, sv, rows = plate['lv'], bolts['s_v'], bolts['rows']
    e1, cols, sh = plate['e1'], bolts['cols'], bolts['s_h']
    d = bolts['d']

    # Draw Beam Web
    fig.add_shape(type="rect", x0=plate['setback'], y0=-beam['h']/2, x1=w_pl+200, y1=beam['h']/2, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(width=0))
    fig.add_shape(type="line", x0=0, y0=-beam['h']/2-50, x1=0, y1=beam['h']/2+50, line=dict(color="black", width=2)) # Column Line

    y_top = h_pl/2
    y_bot = -h_pl/2
    start_y = y_top - lv

    if "End" in ctype:
        # End Plate
        dw = max(beam['b'], w_pl)
        fig.add_shape(type="rect", x0=-dw/2, y0=y_bot, x1=dw/2, y1=y_top, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        g = sh # Gauge
        for s in [-1, 1]:
            bx = s*g/2
            for r in range(rows):
                by = start_y - (r*sv)
                fig.add_shape(type="circle", x0=bx-d/2, y0=by-d/2, x1=bx+d/2, y1=by+d/2, fillcolor="white", line=dict(color="black", width=1))
        add_dim(fig, dw/2+20, y_top, dw/2+20, y_bot, f"H={h_pl}", 20, "v")
        
    else:
        # Fin / Angle (Side connection)
        fig.add_shape(type="rect", x0=0, y0=y_bot, x1=w_pl, y1=y_top, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        for c in range(cols):
            cx = e1 + (c * sh)
            for r in range(rows):
                cy = start_y - (r * sv)
                fig.add_shape(type="circle", x0=cx-d/2, y0=cy-d/2, x1=cx+d/2, y1=cy+d/2, fillcolor="white", line=dict(color="black", width=1))
        
        add_dim(fig, w_pl+20, y_top, w_pl+20, start_y, f"{lv}", 10, "v")
        if rows > 1:
            add_dim(fig, w_pl+20, start_y, w_pl+20, start_y-((rows-1)*sv), f"{rows-1}@{sv}", 10, "v")
        add_dim(fig, 0, y_bot-20, w_pl, y_bot-20, f"W={w_pl}", -20, "h")

    force_range(fig, max(h_pl, beam['h'])/1.5)
    fig.update_layout(title=f"<b>ELEVATION</b> : {ctype}")
    return fig

# ==========================================
# 2. SIDE VIEW
# ==========================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    ctype = plate['type']
    h, b, tw = beam['h'], beam['b'], beam['tw']
    hp, tp = plate['h'], plate['t']
    rows, sv, lv = bolts['rows'], bolts['s_v'], plate['lv']
    d = bolts['d']

    # Column Background
    fig.add_shape(type="rect", x0=-b/2-20, y0=-h/2-50, x1=b/2+20, y1=h/2+50, fillcolor="#E5E7EB", line=dict(width=0))
    
    if "End" in ctype:
        # End Plate Side
        fig.add_shape(type="rect", x0=0, y0=-hp/2, x1=tp, y1=hp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        draw_h_section(fig, tp+150, 0, h, b, beam['tf'], tw, STYLE['STEEL_CUT'], "I")
        # Bolt
        start_y = hp/2 - lv
        for r in range(rows):
            y = start_y - (r*sv)
            fig.add_shape(type="rect", x0=-15, y0=y-d/2, x1=tp+10, y1=y+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            
    else:
        # Fin / Angle Side
        draw_h_section(fig, 0, 0, h, b, beam['tf'], tw, STYLE['STEEL_CUT'], "I")
        if "Double" in ctype:
             # Angle L & R
            fig.add_shape(type="rect", x0=-tw/2-tp, y0=-hp/2, x1=-tw/2, y1=hp/2, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
            fig.add_shape(type="rect", x0=tw/2, y0=-hp/2, x1=tw/2+tp, y1=hp/2, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
        else:
            # Single Fin
            fig.add_shape(type="rect", x0=tw/2, y0=-hp/2, x1=tw/2+tp, y1=hp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
            
        # Bolts through web
        start_y = hp/2 - lv
        for r in range(rows):
            y = start_y - (r*sv)
            fig.add_shape(type="rect", x0=-tw/2-tp-10, y0=y-d/2, x1=tw/2+tp+10, y1=y+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))

    force_range(fig, h/1.5)
    fig.update_layout(title=f"<b>SECTION</b> : {ctype}")
    return fig

# ==========================================
# 3. PLAN VIEW
# ==========================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    ctype = plate['type']
    b, tw, tf = beam['b'], beam['tw'], beam['tf']
    wp, tp = plate['w'], plate['t']
    d = bolts['d']
    sb = plate['setback']

    # Column Top View
    col_d = max(300, b+50)
    draw_h_section(fig, -col_d/2, 0, col_d, col_d, 16, 12, STYLE['STEEL_CUT'], "H")

    if "End" in ctype:
        # End Plate Plan
        fig.add_shape(type="rect", x0=0, y0=-wp/2, x1=tp, y1=wp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        # Beam Web
        fig.add_shape(type="rect", x0=tp, y0=-tw/2, x1=tp+300, y1=tw/2, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(width=1))
        # Flanges
        fig.add_shape(type="rect", x0=tp, y0=-b/2, x1=tp+300, y1=-b/2+tf, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(width=1))
        fig.add_shape(type="rect", x0=tp, y0=b/2-tf, x1=tp+300, y1=b/2, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(width=1))
        
        # Bolts
        g = bolts['s_h']
        for s in [-1, 1]:
            y_b = s*g/2
            fig.add_shape(type="rect", x0=-15, y0=y_b-d/2, x1=tp+15, y1=y_b+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            
    else:
        # Fin / Angle Plan
        fig.add_shape(type="rect", x0=0, y0=-tp/2, x1=wp, y1=tp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        
        # Beam Web (with setback)
        fig.add_shape(type="rect", x0=sb, y0=tp/2, x1=wp+50, y1=tp/2+tw, fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
        
        # Bolt
        bx = plate['e1']
        fig.add_shape(type="rect", x0=bx-d/2, y0=-tp/2-10, x1=bx+d/2, y1=tp/2+tw+10, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
        
        add_dim(fig, 0, 0, sb, 0, f"{sb}", -20, "h")
        add_dim(fig, 0, tp/2+tw+30, bx, tp/2+tw+30, f"e1={plate['e1']}", 20, "h")

    force_range(fig, 250)
    fig.update_layout(title=f"<b>PLAN VIEW</b> : {ctype}")
    return fig

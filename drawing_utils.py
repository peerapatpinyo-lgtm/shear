import plotly.graph_objects as go
import numpy as np

# =============================================================================
# 🎨 STYLES & CONFIG (รูปแบบเดิม)
# =============================================================================
STYLE = {
    'STEEL_CUT':   dict(fillcolor="#D1D5DB", line=dict(color="black", width=2)),
    'STEEL_FACE':  dict(fillcolor="#F3F4F6", line=dict(color="#6B7280", width=1)),
    'PLATE':       dict(fillcolor="#BFDBFE", line=dict(color="#1E3A8A", width=2)),
    'ANGLE':       dict(fillcolor="#C7D2FE", line=dict(color="#312E81", width=2)),
    'BOLT':        dict(fillcolor="#374151", line=dict(color="black", width=1)),
    'CL':          dict(color="#DC2626", width=1, dash="dashdot"),
    'DIM':         dict(color="#1D4ED8", family="Arial", size=11), # สีน้ำเงินแบบเดิม
}

# =============================================================================
# 🛠️ HELPER FUNCTIONS (กลับไปใช้แบบมีหัวลูกศร)
# =============================================================================
def add_dim(fig, x0, y0, x1, y1, text, offset=30, type="h"):
    """เขียน Dimension แบบมีหัวลูกศร (Arrow Style - แบบเดิมที่ต้องการ)"""
    c = STYLE['DIM']['color']
    if type == "h": 
        y_pos = y0 + offset
        # เส้นหลัก
        fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=c, width=1))
        # ขาหยั่ง
        dir = 1 if offset >= 0 else -1
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos+(5*dir), line=dict(color=c, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos+(5*dir), line=dict(color=c, width=0.5))
        # หัวลูกศร
        fig.add_annotation(x=x0, y=y_pos, ax=15, ay=0, axref="pixel", ayref="pixel", arrowhead=2, arrowsize=1, arrowcolor=c, text="")
        fig.add_annotation(x=x1, y=y_pos, ax=-15, ay=0, axref="pixel", ayref="pixel", arrowhead=2, arrowsize=1, arrowcolor=c, text="")
        # ข้อความ
        fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=f"<b>{text}</b>", showarrow=False, yshift=10*dir, font=dict(size=11, color=c))
    else: # Vertical
        x_pos = x0 + offset
        dir = 1 if offset >= 0 else -1
        # เส้นหลัก
        fig.add_shape(type="line", x0=x_pos, y0=y0, x1=x_pos, y1=y1, line=dict(color=c, width=1))
        # ขาหยั่ง
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos+(5*dir), y1=y0, line=dict(color=c, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos+(5*dir), y1=y1, line=dict(color=c, width=0.5))
        # หัวลูกศร
        fig.add_annotation(x=x_pos, y=y0, ax=0, ay=15, axref="pixel", ayref="pixel", arrowhead=2, arrowsize=1, arrowcolor=c, text="")
        fig.add_annotation(x=x_pos, y=y1, ax=0, ay=-15, axref="pixel", ayref="pixel", arrowhead=2, arrowsize=1, arrowcolor=c, text="")
        # ข้อความ
        fig.add_annotation(x=x_pos, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=15*dir, textangle=-90, font=dict(size=11, color=c))

def add_leader(fig, x, y, text, ax=40, ay=-40, align="left"):
    fig.add_annotation(x=x, y=y, ax=ax, ay=ay, axref="pixel", ayref="pixel", text=f"<b>{text}</b>", showarrow=True, arrowhead=2, arrowsize=1, font=dict(size=11), align=align, bgcolor="rgba(255,255,255,0.8)")

def draw_h_beam_section(fig, x_cen, y_cen, h, b, tf, tw, style, orientation="I"):
    if orientation == "I":
        fig.add_shape(type="path", path=f"M {x_cen-tw/2} {y_cen-h/2+tf} L {x_cen-tw/2} {y_cen+h/2-tf} L {x_cen+tw/2} {y_cen+h/2-tf} L {x_cen+tw/2} {y_cen-h/2+tf} Z", fillcolor=style['fillcolor'], line=dict(width=0))
        fig.add_shape(type="rect", x0=x_cen-b/2, y0=y_cen+h/2-tf, x1=x_cen+b/2, y1=y_cen+h/2, fillcolor=style['fillcolor'], line=style['line'])
        fig.add_shape(type="rect", x0=x_cen-b/2, y0=y_cen-h/2, x1=x_cen+b/2, y1=y_cen-h/2+tf, fillcolor=style['fillcolor'], line=style['line'])
        fig.add_shape(type="line", x0=x_cen-tw/2, y0=y_cen-h/2+tf, x1=x_cen-tw/2, y1=y_cen+h/2-tf, line=style['line'])
        fig.add_shape(type="line", x0=x_cen+tw/2, y0=y_cen-h/2+tf, x1=x_cen+tw/2, y1=y_cen+h/2-tf, line=style['line'])
    else: 
        fig.add_shape(type="rect", x0=x_cen-h/2, y0=y_cen-b/2, x1=x_cen-h/2+tf, y1=y_cen+b/2, fillcolor=style['fillcolor'], line=style['line'])
        fig.add_shape(type="rect", x0=x_cen+h/2-tf, y0=y_cen-b/2, x1=x_cen+h/2, y1=y_cen+b/2, fillcolor=style['fillcolor'], line=style['line'])
        fig.add_shape(type="rect", x0=x_cen-h/2+tf, y0=y_cen-tw/2, x1=x_cen+h/2-tf, y1=y_cen+tw/2, fillcolor=style['fillcolor'], line=dict(width=0))
        fig.add_shape(type="line", x0=x_cen-h/2+tf, y0=y_cen-tw/2, x1=x_cen+h/2-tf, y1=y_cen-tw/2, line=style['line'])
        fig.add_shape(type="line", x0=x_cen-h/2+tf, y0=y_cen+tw/2, x1=x_cen+h/2-tf, y1=y_cen+tw/2, line=style['line'])

def force_range(fig, limit):
    fig.update_layout(xaxis=dict(range=[-limit, limit], visible=False, scaleanchor="y", scaleratio=1, fixedrange=True), yaxis=dict(range=[-limit, limit], visible=False, fixedrange=True), height=500, margin=dict(l=20, r=20, t=50, b=20), plot_bgcolor="white", showlegend=False)

# =============================================================================
# 3. FRONT VIEW (ELEVATION) - ใส่ระยะครบ
# =============================================================================
def create_front_view(beam, plate, inp):
    fig = go.Figure()
    ctype = plate.get('type', 'Fin Plate')
    h_b = beam['h']
    h_pl, w_pl = plate['h'], plate['w']
    lv, sv, rows = inp['lv'], inp['s_v'], inp['rows']
    leh, cols, sh = inp['leh'], inp['cols'], inp['s_h']
    d = inp['d']
    sb = inp['setback']

    # Context elements (Cleaner style)
    fig.add_shape(type="line", x0=0, y0=-h_b/2-50, x1=0, y1=h_b/2+50, line=dict(color="black", width=2)) # Col CL
    
    if "End" in ctype:
        # --- END PLATE ---
        draw_w = max(beam['b'], w_pl)
        y_top, y_bot = h_pl/2, -h_pl/2
        fig.add_shape(type="rect", x0=-draw_w/2, y0=y_bot, x1=draw_w/2, y1=y_top, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        
        g = sh # Gauge
        start_y = y_top - lv
        for s in [-1, 1]:
            bx = s*g/2
            for r in range(rows):
                by = start_y - (r*sv)
                fig.add_shape(type="circle", x0=bx-d/2, y0=by-d/2, x1=bx+d/2, y1=by+d/2, fillcolor="white", line=dict(color="black", width=1))
        
        add_leader(fig, -draw_w/2, y_top, "End Plate", ax=-40, ay=-40)
        # Dimensions (Full set)
        dim_x = draw_w/2 + 20
        add_dim(fig, dim_x, y_top, dim_x, y_top-lv, f"lv={lv}", 20, "v") # Top edge
        if rows > 1:
            add_dim(fig, dim_x, y_top-lv, dim_x, y_top-lv-((rows-1)*sv), f"{rows-1}@{sv}", 20, "v") # Pitch
        add_dim(fig, dim_x+30, y_top, dim_x+30, y_bot, f"H={h_pl}", 20, "v") # Total Height
        add_dim(fig, -g/2, y_bot-30, g/2, y_bot-30, f"Gauge={g}", -20, "h") # Gauge
        draw_h_final = h_pl

    else:
        # --- FIN / ANGLE ---
        # Beam ghost
        fig.add_shape(type="rect", x0=sb, y0=-h_b/2, x1=w_pl+100, y1=h_b/2, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(color="gray", width=1, dash="dot"))
        
        y_top, y_bot = h_pl/2, -h_pl/2
        style = STYLE['ANGLE'] if "Double" in ctype else STYLE['PLATE']
        fig.add_shape(type="rect", x0=0, y0=y_bot, x1=w_pl, y1=y_top, fillcolor=style['fillcolor'], line=style['line'])

        # Calculate bolt starting position relative to Plate Right Edge
        # Plate Width = Setback + e1 + BoltGroup + leh
        # First bolt X (from col center) = Setback + e1
        first_bolt_x = sb + inp['e1']
        start_y = y_top - lv
        
        bolt_count = 0
        for c in range(cols):
            cx = first_bolt_x + (c * sh)
            for r in range(rows):
                cy = start_y - (r * sv)
                fig.add_shape(type="circle", x0=cx-d/2, y0=cy-d/2, x1=cx+d/2, y1=cy+d/2, fillcolor="white", line=dict(color="black", width=1))
                bolt_count += 1
        
        lbl = "2L-Angle" if "Double" in ctype else "Fin Plate"
        add_leader(fig, w_pl, y_top, lbl, ax=40, ay=-40)
        
        # Dimensions (Full set)
        # Vertical
        dim_x_v = w_pl + 20
        add_dim(fig, dim_x_v, y_top, dim_x_v, y_top-lv, f"lv={lv}", 20, "v") # Top edge
        if rows > 1:
            add_dim(fig, dim_x_v, y_top-lv, dim_x_v, y_top-lv-((rows-1)*sv), f"{rows-1}@{sv}", 20, "v") # Pitch
        add_dim(fig, dim_x_v+30, y_top, dim_x_v+30, y_bot, f"H={h_pl}", 20, "v") # Total Height
        
        # Horizontal
        last_bolt_x = first_bolt_x + ((cols-1)*sh)
        dim_y_h = y_bot - 20
        add_dim(fig, last_bolt_x, dim_y_h, w_pl, dim_y_h, f"leh={leh}", -20, "h") # Edge Horiz
        if cols > 1:
             add_dim(fig, first_bolt_x, dim_y_h, last_bolt_x, dim_y_h, f"{cols-1}@{sh}", -20, "h") # Spacing Horiz
        add_dim(fig, 0, dim_y_h-30, w_pl, dim_y_h-30, f"W={w_pl}", -20, "h") # Total Width

        draw_h_final = h_pl

    limit = max(h_b, draw_h_final) + 100
    force_range(fig, limit/2)
    fig.update_layout(title_text=f"<b>ELEVATION VIEW</b> : {ctype}")
    return fig

# =============================================================================
# 4. SIDE VIEW (SECTION)
# =============================================================================
def create_side_view(beam, plate, inp):
    fig = go.Figure()
    ctype = plate.get('type', 'Fin Plate')
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    hp, tp = plate['h'], inp['t']
    rows, sv, lv = inp['rows'], inp['s_v'], inp['lv']
    d = inp['d']

    # Column (Background)
    col_w, col_h = b + 50, h + 150
    fig.add_shape(type="rect", x0=-col_w/2, y0=-col_h/2, x1=col_w/2, y1=col_h/2, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(color="black", width=2))
    fig.add_trace(go.Scatter(x=[-col_w/2, col_w/2, col_w/2, -col_w/2], y=[-col_h/2, -col_h/2, col_h/2, col_h/2], mode='lines', line=dict(width=0), hoverinfo='skip', fillpattern=dict(shape="/", size=10, solidity=0.2, fgcolor="#D1D5DB"), fill='toself'))

    if "End" in ctype:
        # End Plate Side
        fig.add_shape(type="rect", x0=0, y0=-hp/2, x1=tp, y1=hp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        L=250
        fig.add_shape(type="rect", x0=tp, y0=-h/2, x1=tp+L, y1=h/2, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(width=0))
        fig.add_shape(type="line", x0=tp, y0=h/2, x1=tp+L, y1=h/2, line=dict(color="black", width=2))
        fig.add_shape(type="line", x0=tp, y0=-h/2, x1=tp+L, y1=-h/2, line=dict(color="black", width=2))
        start_y = hp/2 - lv
        for r in range(rows):
            y = start_y - (r*sv)
            fig.add_shape(type="rect", x0=-20, y0=y-d/2, x1=tp+15, y1=y+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tp, y0=y-d, x1=tp+10, y1=y+d, fillcolor="black", line=dict(width=0))
        add_leader(fig, tp, hp/2, "End Plate", ax=40, ay=-40)

    elif "Double" in ctype:
        # Double Angle Side
        draw_h_beam_section(fig, 0, 0, h, b, tf, tw, STYLE['STEEL_CUT'], "I")
        fig.add_shape(type="rect", x0=-tw/2-tp, y0=-hp/2, x1=-tw/2, y1=hp/2, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
        fig.add_shape(type="rect", x0=tw/2, y0=-hp/2, x1=tw/2+tp, y1=hp/2, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
        start_y = hp/2 - lv
        for r in range(rows):
            y = start_y - (r*sv)
            fig.add_shape(type="rect", x0=-tw/2-tp-15, y0=y-d/2, x1=tw/2+tp+15, y1=y+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
        add_leader(fig, tw/2+tp, 0, "2L-Angle", ax=40, ay=-40)

    else:
        # Fin Plate Side
        draw_h_beam_section(fig, 0, 0, h, b, tf, tw, STYLE['STEEL_CUT'], "I")
        fig.add_shape(type="rect", x0=tw/2, y0=-hp/2, x1=tw/2+tp, y1=hp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        y_start = hp/2 - lv
        for r in range(rows):
            y = y_start - (r * sv)
            fig.add_shape(type="line", x0=-col_w/2, y0=y, x1=col_w/2, y1=y, line=STYLE['CL'])
            fig.add_shape(type="rect", x0=-tw/2-15, y0=y-d/2, x1=tw/2+tp+15, y1=y+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tw/2+tp, y0=y-d, x1=tw/2+tp+10, y1=y+d, fillcolor="black", line=dict(width=0))
            fig.add_shape(type="rect", x0=-tw/2-12, y0=y-d, x1=-tw/2, y1=y+d, fillcolor="black", line=dict(width=0))
        add_dim(fig, -b/2-30, h/2, -b/2-30, -h/2, f"Beam H={h}", 30, "v") # Added Beam Depth
        add_leader(fig, tw/2+tp, 0, "Fin Plate", ax=40, ay=-30)

    limit = max(h, hp) + 100
    force_range(fig, limit/2)
    fig.update_layout(title_text=f"<b>SECTION A-A</b> : {ctype}")
    return fig

# =============================================================================
# 5. PLAN VIEW (TOP)
# =============================================================================
def create_plan_view(beam, plate, inp):
    fig = go.Figure()
    ctype = plate.get('type', 'Fin Plate')
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    wp, tp = plate['w'], inp['t']
    d = inp['d']
    sb = inp['setback']
    
    # Column Section
    col_h, col_b = max(300, b+50), max(300, b+50)
    draw_h_beam_section(fig, -col_h/2, 0, col_h, col_b, 16, 12, STYLE['STEEL_CUT'], "H")

    if "End" in ctype:
        # End Plate Plan
        fig.add_shape(type="rect", x0=0, y0=-wp/2, x1=tp, y1=wp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        fig.add_shape(type="rect", x0=tp, y0=-b/2, x1=tp+250, y1=b/2, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=STYLE['STEEL_FACE']['line'])
        fig.add_shape(type="line", x0=tp, y0=0, x1=tp+250, y1=0, line=STYLE['CL'])
        g = inp['s_h']
        for s in [-1, 1]:
            y_b = s*g/2
            fig.add_shape(type="rect", x0=-20, y0=y_b-d/2, x1=tp+15, y1=y_b+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tp, y0=y_b-d, x1=tp+10, y1=y_b+d, fillcolor="black", line=dict(width=0))
        add_leader(fig, tp, wp/2, "End Plate", ax=40, ay=-40)
        add_dim(fig, 0, -wp/2-30, tp, -wp/2-30, f"t={tp}", -20, "h")

    elif "Double" in ctype:
        # Double Angle Plan
        beam_len = wp + 60
        fig.add_shape(type="rect", x0=sb, y0=-tw/2, x1=beam_len, y1=tw/2, fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
        leg_L = 100
        for s in [-1, 1]:
            y_in = s*tw/2
            y_out = s*(tw/2+tp)
            fig.add_shape(type="rect", x0=sb, y0=y_in, x1=sb+wp, y1=y_out, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
            fig.add_shape(type="rect", x0=sb, y0=y_in, x1=sb+tp, y1=y_in+(s*leg_L), fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
        bx = sb + inp['e1']
        full_t = tw + 2*tp
        fig.add_shape(type="rect", x0=bx-d/2, y0=-full_t/2-15, x1=bx+d/2, y1=full_t/2+15, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
        add_leader(fig, sb, tw/2+tp, "2L-Angle", ax=40, ay=-40)
        add_dim(fig, 0, 0, sb, 0, f"Gap={sb}", -30, "h") # Added Setback
        add_dim(fig, sb, full_t/2+30, bx, full_t/2+30, f"e1={inp['e1']}", 20, "h") # Added e1

    else:
        # Fin Plate Plan
        fig.add_shape(type="rect", x0=0, y0=-tp/2, x1=wp, y1=tp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        beam_len = wp + 60
        fig.add_shape(type="rect", x0=sb, y0=tp/2, x1=beam_len, y1=tp/2+tw, fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
        bolt_x = sb + inp['e1']
        y_head_out = -tp/2 - 8
        y_nut_out = tp/2 + tw + 10
        fig.add_shape(type="rect", x0=bolt_x-d/2, y0=y_head_out, x1=bolt_x+d/2, y1=y_nut_out, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
        fig.add_shape(type="rect", x0=bolt_x-d, y0=y_head_out-6, x1=bolt_x+d, y1=y_head_out, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black", width=1))
        fig.add_shape(type="rect", x0=bolt_x-d, y0=y_nut_out, x1=bolt_x+d, y1=y_nut_out+10, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black", width=1))
        ws = inp.get('weld_size', 5)
        fig.add_shape(type="path", path=f"M 0 {-tp/2} L {ws} {-tp/2} L 0 {-tp/2-ws} Z", fillcolor="black", line_width=0)
        fig.add_shape(type="path", path=f"M 0 {tp/2} L {ws} {tp/2} L 0 {tp/2+ws} Z", fillcolor="black", line_width=0)
        add_leader(fig, 0, -tp/2-ws, f"Weld {ws}mm", ax=-40, ay=-30, align="right")
        
        # Dimensions (Setback & e1)
        add_dim(fig, 0, 0, sb, 0, f"Gap={sb}", -30, "h") 
        add_dim(fig, sb, tp/2+tw+30, bolt_x, tp/2+tw+30, f"e1={inp['e1']}", 20, "h")
        add_leader(fig, wp, 0, "Fin Plate", ax=40, ay=-30)

    force_range(fig, 250)
    fig.update_layout(title_text=f"<b>PLAN VIEW</b> : {ctype}")
    return fig

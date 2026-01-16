import plotly.graph_objects as go
import numpy as np

# =============================================================================
# 🏗️ ENGINEER'S STANDARD STYLES (KEEP ORIGINAL)
# =============================================================================
STYLE = {
    'STEEL_CUT':   dict(fillcolor="#D1D5DB", line=dict(color="black", width=2)),
    'STEEL_FACE':  dict(fillcolor="#F3F4F6", line=dict(color="#6B7280", width=1)),
    'PLATE':       dict(fillcolor="#BFDBFE", line=dict(color="#1E3A8A", width=2)),
    'ANGLE':       dict(fillcolor="#C7D2FE", line=dict(color="#312E81", width=2)), # เพิ่มสี Angle
    'BOLT':        dict(fillcolor="#374151", line=dict(color="black", width=1)),
    'WASHER':      dict(fillcolor="#9CA3AF", line=dict(color="black", width=1)),
    'CL':          dict(color="#DC2626", width=1, dash="dashdot"),
    'DIM':         dict(color="#1D4ED8", family="Arial", size=11),
    'LEADER':      dict(color="#000000", width=1.5),
    'WELD':        dict(fillcolor="black", line=dict(width=0)),
    'ERROR':       dict(color="#EF4444", width=2, dash="dash")
}

SETBACK = 15

# =============================================================================
# 🛠️ UTILITY FUNCTIONS (KEEP ORIGINAL)
# =============================================================================
def add_dim(fig, x0, y0, x1, y1, text, offset=30, type="h", color=STYLE['DIM']['color'], is_err=False):
    col = "#EF4444" if is_err else color
    ext = 5 * np.sign(offset)
    if type == "h": 
        y_pos = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos+ext, line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos+ext, line=dict(color=col, width=0.5))
        fig.add_annotation(x=x0, y=y_pos, ax=x1, ay=y_pos, arrowcolor=col, arrowhead=2, arrowsize=1, text="")
        fig.add_annotation(x=x1, y=y_pos, ax=x0, ay=y_pos, arrowcolor=col, arrowhead=2, arrowsize=1, text="")
        fig.add_annotation(x=(x0+x1)/2, y=y_pos+(10 if offset>0 else -15), text=f"<b>{text}</b>", showarrow=False, font=dict(size=11, color=col))
    else: 
        x_pos = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos+ext, y1=y0, line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos+ext, y1=y1, line=dict(color=col, width=0.5))
        fig.add_annotation(x=x_pos, y=y0, ax=x_pos, ay=y1, arrowcolor=col, arrowhead=2, arrowsize=1, text="")
        fig.add_annotation(x=x_pos, y=y1, ax=x_pos, ay=y0, arrowcolor=col, arrowhead=2, arrowsize=1, text="")
        fig.add_annotation(x=x_pos+(15 if offset>0 else -15), y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, textangle=-90, font=dict(size=11, color=col))

def add_leader(fig, x, y, ax, ay, text, align="left"):
    fig.add_annotation(x=x, y=y, ax=ax, ay=ay, text=f"<b>{text}</b>", showarrow=True, arrowhead=2, arrowsize=1, 
                       font=dict(size=11, color="black"), align=align, bgcolor="rgba(255,255,255,0.7)")

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

# =============================================================================
# 1. PLAN VIEW (UPDATED)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    conn_type = plate.get('type', 'Fin Plate') # Check Type
    
    # Common Column
    col_h, col_b = max(300, beam['b']+50), max(300, beam['b']+50)
    col_tf, col_tw = 16, 12
    draw_h_beam_section(fig, -col_h/2, 0, col_h, col_b, col_tf, col_tw, STYLE['STEEL_CUT'], orientation="H")
    
    tp, wp = plate['t'], plate['w']
    d = bolts['d']

    # --- LOGIC BRANCHING ---
    if "End Plate" in conn_type:
        # 1. End Plate (Flat against Col)
        fig.add_shape(type="rect", x0=0, y0=-wp/2, x1=tp, y1=wp/2, 
                      fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        # 2. Beam (Starts after Plate)
        beam_len = 200
        fig.add_shape(type="rect", x0=tp, y0=-beam['b']/2, x1=tp+beam_len, y1=beam['b']/2,
                      fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=STYLE['STEEL_FACE']['line'])
        # 3. Bolts (Through Col Flange + Plate)
        g_bolt = 100 # Gauge
        for sign in [-1, 1]:
            y_b = sign * g_bolt / 2
            # Draw Bolt Head (Outside Plate) & Nut (Inside Col - usually)
            fig.add_shape(type="rect", x0=-20, y0=y_b-d/2, x1=tp+15, y1=y_b+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tp, y0=y_b-d, x1=tp+10, y1=y_b+d, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black", width=1)) # Head
        
        add_leader(fig, tp, wp/2, tp+50, wp/2+50, "End Plate")
        add_dim(fig, 0, -wp/2-20, tp, -wp/2-20, f"tp={tp}", -20, "h")

    elif "Double" in conn_type:
        # 1. Beam Web (Center)
        beam_len = wp + 60
        fig.add_shape(type="rect", x0=SETBACK, y0=-beam['tw']/2, x1=beam_len, y1=beam['tw']/2,
                      fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
        
        # 2. Double Angles (L-Shapes)
        leg_web = wp  # Length on web
        leg_col = 100 # Length on column
        t_ang = tp
        
        for sign in [-1, 1]:
            # Angle on Web
            y_web_face = sign * beam['tw']/2
            y_ang_outer = sign * (beam['tw']/2 + t_ang)
            
            # Draw L-Shape using 2 rects
            # Leg 1 (Along Web)
            fig.add_shape(type="rect", x0=SETBACK, y0=y_web_face, x1=SETBACK+leg_web, y1=y_ang_outer, 
                          fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
            # Leg 2 (Along Col)
            fig.add_shape(type="rect", x0=SETBACK, y0=y_web_face, x1=SETBACK+t_ang, y1=y_web_face + (sign*leg_col), 
                          fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])

        # 3. Bolt (Through Angle-Web-Angle)
        bx = SETBACK + plate['e1']
        full_thk = beam['tw'] + 2*t_ang
        fig.add_shape(type="rect", x0=bx-d/2, y0=-full_thk/2-10, x1=bx+d/2, y1=full_thk/2+10, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
        # Heads/Nuts
        fig.add_shape(type="rect", x0=bx-d, y0=full_thk/2+10, x1=bx+d, y1=full_thk/2+18, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black", width=1))
        fig.add_shape(type="rect", x0=bx-d, y0=-full_thk/2-18, x1=bx+d, y1=-full_thk/2-10, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black", width=1))

        add_leader(fig, SETBACK, beam['tw']/2+t_ang, SETBACK+40, beam['tw']/2+t_ang+40, "2L-Angles")

    else:
        # === YOUR ORIGINAL FIN PLATE LOGIC ===
        # 2. Fin Plate
        fig.add_shape(type="rect", x0=0, y0=-tp/2, x1=wp, y1=tp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        # 3. Beam Web
        beam_len = wp + 60
        fig.add_shape(type="rect", x0=SETBACK, y0=tp/2, x1=beam_len, y1=tp/2+beam['tw'], fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
        # 4. Bolt
        bolt_x = plate['e1']
        y_head_out, y_nut_out = -tp/2 - 8, tp/2 + beam['tw'] + 10
        fig.add_shape(type="rect", x0=bolt_x-d/2, y0=y_head_out, x1=bolt_x+d/2, y1=y_nut_out, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
        fig.add_shape(type="rect", x0=bolt_x-d, y0=y_head_out-6, x1=bolt_x+d, y1=y_head_out, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black", width=1)) # Head
        fig.add_shape(type="rect", x0=bolt_x-d, y0=y_nut_out, x1=bolt_x+d, y1=y_nut_out+10, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black", width=1)) # Nut
        # Weld
        ws = plate['weld_size']
        fig.add_shape(type="path", path=f"M 0 {-tp/2} L {ws} {-tp/2} L 0 {-tp/2-ws} Z", fillcolor="black", line_width=0)
        fig.add_shape(type="path", path=f"M 0 {tp/2} L {ws} {tp/2} L 0 {tp/2+ws} Z", fillcolor="black", line_width=0)
        add_leader(fig, 0, -tp/2-ws, -40, -tp/2-40, f"Fillet Weld {ws}mm", align="right")
        add_dim(fig, 0, tp/2+beam['tw']+40, bolt_x, tp/2+beam['tw']+40, f"e1={plate['e1']}", 20, "h")
        add_leader(fig, wp, tp/2, wp+40, tp/2+40, "Fin Plate")

    # Common Annotations
    fig.add_dim = add_dim # attach function
    if "Fin" in conn_type or "Double" in conn_type:
        add_dim(fig, 0, 0, SETBACK, 0, f"Setback {SETBACK}", -30, "h")

    fig.update_layout(title="<b>PLAN VIEW</b> (Fabrication Detail)", height=500, plot_bgcolor="white",
                      margin=dict(l=60, r=60, t=80, b=60), xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

# =============================================================================
# 2. ELEVATION VIEW (UPDATED)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    conn_type = plate.get('type', 'Fin Plate')

    h_b = beam['h']
    h_pl_input, w_pl = plate['h'], plate['w']
    lv, sv, rows = plate['lv'], bolts['s_v'], bolts['rows']
    e1, cols, sh = plate['e1'], bolts['cols'], bolts['s_h']
    
    # Calc Height Logic (Same as yours)
    min_edge = 1.5 * bolts['d']
    req_h = lv + ((rows-1)*sv) + min_edge
    is_short = h_pl_input < req_h
    draw_h_pl = req_h + 20 if is_short else h_pl_input
    y_top, y_bot = draw_h_pl/2, -draw_h_pl/2

    # 1. Column Ref
    fig.add_shape(type="line", x0=0, y0=-h_b/2-50, x1=0, y1=h_b/2+50, line=dict(color="black", width=2))
    
    # 2. Beam Ghost
    fig.add_shape(type="rect", x0=SETBACK if "End" not in conn_type else 0, y0=-h_b/2, x1=w_pl+100, y1=h_b/2, 
                  fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(color="gray", width=1, dash="dot"))

    # --- LOGIC BRANCHING ---
    if "End Plate" in conn_type:
        # End Plate Face
        # Assuming w_pl is width of plate, centered on beam/col
        plate_width_real = max(beam['b'], w_pl) # Ensure wide enough
        draw_width = plate_width_real
        
        # Draw Plate Centered
        fig.add_shape(type="rect", x0=-draw_width/2, y0=y_bot, x1=draw_width/2, y1=y_top, 
                      fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        
        # Bolts (Assume 2 columns symmetric about center)
        g_bolt = 100 # Standard Gauge
        start_y = y_top - lv
        for sign in [-1, 1]:
            bx = sign * g_bolt / 2
            for r in range(rows):
                by = start_y - (r * sv)
                # Bolt Crosshair
                fig.add_shape(type="circle", x0=bx-bolts['d']/2, y0=by-bolts['d']/2, x1=bx+bolts['d']/2, y1=by+bolts['d']/2, fillcolor="white", line=dict(color="black", width=1))
        
        add_leader(fig, -draw_width/2, y_top, -draw_width/2-40, y_top+40, "End Plate Face")
        add_dim(fig, -draw_width/2, y_bot-20, draw_width/2, y_bot-20, f"W={draw_width}", -20, "h")

    else:
        # Fin Plate & Double Angle (Similar View)
        style = STYLE['ANGLE'] if "Double" in conn_type else STYLE['PLATE']
        fig.add_shape(type="rect", x0=0, y0=y_bot, x1=w_pl, y1=y_top, fillcolor=style['fillcolor'], line=style['line'])
        
        # Bolts
        start_y = y_top - lv
        for c in range(cols):
            cx = e1 + (c * sh)
            for r in range(rows):
                cy = start_y - (r * sv)
                fig.add_shape(type="circle", x0=cx-bolts['d']/2, y0=cy-bolts['d']/2, x1=cx+bolts['d']/2, y1=cy+bolts['d']/2, fillcolor="white", line=dict(color="black", width=1))
                fig.add_shape(type="line", x0=cx-bolts['d'], y0=cy, x1=cx+bolts['d'], y1=cy, line=dict(color="black", width=0.5))
                fig.add_shape(type="line", x0=cx, y0=cy-bolts['d'], x1=cx, y1=cy+bolts['d'], line=dict(color="black", width=0.5))
        
        lbl = "Double Angle" if "Double" in conn_type else "Fin Plate"
        add_leader(fig, w_pl, y_top, w_pl+40, y_top+50, lbl)
        add_dim(fig, 0, y_bot-30, w_pl, y_bot-30, f"{w_pl}", -20, "h")

    # Common Dims
    x_dim = (w_pl if "End" not in conn_type else beam['b']/2) + 30
    add_dim(fig, x_dim, y_top, x_dim, y_top-lv, f"{lv}", 10, "v")
    if rows > 1:
        add_dim(fig, x_dim, y_top-lv, x_dim, y_top-lv-((rows-1)*sv), f"{rows-1}@{sv}", 10, "v")

    fig.update_layout(title="<b>ELEVATION VIEW</b> (Connection Detail)", height=600, plot_bgcolor="white",
                      margin=dict(l=100, r=100, t=80, b=80), xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

# =============================================================================
# 3. SECTION A-A (UPDATED)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    conn_type = plate.get('type', 'Fin Plate')
    
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl_input = plate['h']
    rows, sv, lv = bolts['rows'], bolts['s_v'], plate['lv']
    tp = plate['t']
    d = bolts['d']

    # Auto-Height Logic
    min_edge = 1.5 * d
    req_h = lv + ((rows-1)*sv) + min_edge
    draw_h_pl = req_h + 20 if h_pl_input < req_h else h_pl_input
    
    # 1. Column (Background)
    col_w = b + 50
    col_h = h + 150
    fig.add_shape(type="rect", x0=-col_w/2, y0=-col_h/2, x1=col_w/2, y1=col_h/2, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(color="black", width=2))
    
    # --- LOGIC BRANCHING ---
    if "End Plate" in conn_type:
        # Side Profile View for End Plate (Beam Side + Plate Side)
        # 1. End Plate (Side View - Vertical Rect)
        fig.add_shape(type="rect", x0=0, y0=-draw_h_pl/2, x1=tp, y1=draw_h_pl/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        # 2. Beam Side Profile (Not Cross Section)
        fig.add_shape(type="rect", x0=tp, y0=-h/2, x1=tp+200, y1=h/2, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(color="black", width=1))
        fig.add_shape(type="line", x0=tp, y0=h/2-tf, x1=tp+200, y1=h/2-tf, line=dict(dash="dot", color="gray")) # Flange hidden
        fig.add_shape(type="line", x0=tp, y0=-h/2+tf, x1=tp+200, y1=-h/2+tf, line=dict(dash="dot", color="gray"))
        
        # 3. Bolts (Side View)
        y_start = (draw_h_pl/2) - lv
        for r in range(rows):
            y = y_start - (r * sv)
            # Bolt Head (Plate Side) & Nut (Col Side - hidden/dashed or just shown)
            fig.add_shape(type="rect", x0=-20, y0=y-d/2, x1=tp+15, y1=y+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tp, y0=y-d, x1=tp+10, y1=y+d, fillcolor="black", line=dict(width=0)) # Head
        
        add_leader(fig, tp/2, draw_h_pl/2, tp/2+40, draw_h_pl/2+40, "End Plate (Side)")

    elif "Double" in conn_type:
        # Cross Section View
        # 1. Beam Section
        draw_h_beam_section(fig, 0, 0, h, b, tf, tw, STYLE['STEEL_CUT'], orientation="I")
        
        # 2. Double Angles (Left & Right)
        # Left Angle
        fig.add_shape(type="rect", x0=-tw/2-tp, y0=-draw_h_pl/2, x1=-tw/2, y1=draw_h_pl/2, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
        # Right Angle
        fig.add_shape(type="rect", x0=tw/2, y0=-draw_h_pl/2, x1=tw/2+tp, y1=draw_h_pl/2, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
        
        # 3. Bolt (Through all)
        y_start = (draw_h_pl/2) - lv
        for r in range(rows):
            y = y_start - (r * sv)
            fig.add_shape(type="rect", x0=-tw/2-tp-15, y0=y-d/2, x1=tw/2+tp+15, y1=y+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            # Head & Nut
            fig.add_shape(type="rect", x0=tw/2+tp, y0=y-d, x1=tw/2+tp+10, y1=y+d, fillcolor="black", line=dict(width=0))
            fig.add_shape(type="rect", x0=-tw/2-tp-10, y0=y-d, x1=-tw/2-tp, y1=y+d, fillcolor="black", line=dict(width=0))

        add_leader(fig, tw/2+tp, 0, tw/2+tp+60, 30, "Double Angle")

    else:
        # === YOUR ORIGINAL FIN PLATE LOGIC ===
        draw_h_beam_section(fig, 0, 0, h, b, tf, tw, STYLE['STEEL_CUT'], orientation="I")
        tp = plate['t']
        fig.add_shape(type="rect", x0=tw/2, y0=-draw_h_pl/2, x1=tw/2+tp, y1=draw_h_pl/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        y_start = (draw_h_pl/2) - lv
        for r in range(rows):
            y = y_start - (r * sv)
            fig.add_shape(type="line", x0=-col_w/2, y0=y, x1=col_w/2, y1=y, line=STYLE['CL'])
            fig.add_shape(type="rect", x0=-tw/2-15, y0=y-d/2, x1=tw/2+tp+15, y1=y+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tw/2+tp, y0=y-d, x1=tw/2+tp+10, y1=y+d, fillcolor="black", line=dict(width=0))
            fig.add_shape(type="rect", x0=tw/2+tp, y0=y-d, x1=tw/2+tp+2, y1=y+d, fillcolor="gray", line=dict(width=1))
            fig.add_shape(type="rect", x0=-tw/2-12, y0=y-d, x1=-tw/2, y1=y+d, fillcolor="black", line=dict(width=0))
            fig.add_shape(type="rect", x0=-tw/2-2, y0=y-d, x1=-tw/2, y1=y+d, fillcolor="gray", line=dict(width=1))

        add_leader(fig, tw/2+tp, 0, tw/2+tp+60, 30, "Fin Plate (Single Shear)")

    fig.update_layout(title="<b>SECTION A-A</b> (Assembly Detail)", height=600, plot_bgcolor="white",
                      margin=dict(l=100, r=100, t=80, b=80), xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

# drawing_utils.py
import plotly.graph_objects as go
import numpy as np

# =============================================================================
# 🏗️ ENGINEER'S STANDARD STYLES
# =============================================================================
STYLE = {
    'STEEL_CUT':   dict(fillcolor="#D1D5DB", line=dict(color="black", width=2)),       
    'STEEL_FACE':  dict(fillcolor="#F3F4F6", line=dict(color="#6B7280", width=1)),     
    'PLATE':       dict(fillcolor="#BFDBFE", line=dict(color="#1E3A8A", width=2)),     
    'ANGLE':       dict(fillcolor="#C7D2FE", line=dict(color="#312E81", width=2)), # สีสำหรับ Angle
    'BOLT':        dict(fillcolor="#374151", line=dict(color="black", width=1)),       
    'CL':          dict(color="#DC2626", width=1, dash="dashdot"),                     
    'DIM':         dict(color="#1D4ED8", family="Arial", size=11),                     
    'ERROR':       dict(color="#EF4444", width=2, dash="dash")                         
}

SETBACK = 15  # Default Setback

# =============================================================================
# 🛠️ HELPER FUNCTIONS
# =============================================================================
def add_dim(fig, x0, y0, x1, y1, text, offset=30, type="h", color=STYLE['DIM']['color']):
    col = color
    ext = 5 * np.sign(offset)
    if type == "h": 
        y_pos = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos+ext, line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos+ext, line=dict(color=col, width=0.5))
        fig.add_annotation(x=x0, y=y_pos, ax=x1, ay=y_pos, arrowhead=2, arrowcolor=col, text="")
        fig.add_annotation(x=x1, y=y_pos, ax=x0, ay=y_pos, arrowhead=2, arrowcolor=col, text="")
        fig.add_annotation(x=(x0+x1)/2, y=y_pos+(10 if offset>0 else -15), text=f"<b>{text}</b>", showarrow=False, font=dict(size=11, color=col))
    else: 
        x_pos = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos+ext, y1=y0, line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos+ext, y1=y1, line=dict(color=col, width=0.5))
        fig.add_annotation(x=x_pos, y=y0, ax=x_pos, ay=y1, arrowhead=2, arrowcolor=col, text="")
        fig.add_annotation(x=x_pos, y=y1, ax=x_pos, ay=y0, arrowhead=2, arrowcolor=col, text="")
        fig.add_annotation(x=x_pos+(15 if offset>0 else -15), y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, textangle=-90, font=dict(size=11, color=col))

def add_leader(fig, x, y, ax, ay, text, align="left"):
    fig.add_annotation(x=x, y=y, ax=ax, ay=ay, text=f"<b>{text}</b>", showarrow=True, arrowhead=2, 
                       font=dict(size=11, color="black"), align=align, bgcolor="rgba(255,255,255,0.7)")

def draw_rect(fig, x0, y0, x1, y1, style):
    fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, fillcolor=style.get('fillcolor'), line=style.get('line'))

def draw_h_beam_section(fig, x_cen, y_cen, h, b, tf, tw, style, orientation="I"):
    if orientation == "I":
        fig.add_shape(type="path", path=f"M {x_cen-tw/2} {y_cen-h/2+tf} L {x_cen-tw/2} {y_cen+h/2-tf} L {x_cen+tw/2} {y_cen+h/2-tf} L {x_cen+tw/2} {y_cen-h/2+tf} Z", fillcolor=style['fillcolor'], line_width=0)
        draw_rect(fig, x_cen-b/2, y_cen+h/2-tf, x_cen+b/2, y_cen+h/2, style)
        draw_rect(fig, x_cen-b/2, y_cen-h/2, x_cen+b/2, y_cen-h/2+tf, style)
        fig.add_shape(type="line", x0=x_cen-tw/2, y0=y_cen-h/2+tf, x1=x_cen-tw/2, y1=y_cen+h/2-tf, line=style['line'])
        fig.add_shape(type="line", x0=x_cen+tw/2, y0=y_cen-h/2+tf, x1=x_cen+tw/2, y1=y_cen+h/2-tf, line=style['line'])
    else: # H Shape
        draw_rect(fig, x_cen-h/2, y_cen-b/2, x_cen-h/2+tf, y_cen+b/2, style) # Flange Left
        draw_rect(fig, x_cen+h/2-tf, y_cen-b/2, x_cen+h/2, y_cen+b/2, style) # Flange Right
        fig.add_shape(type="rect", x0=x_cen-h/2+tf, y0=y_cen-tw/2, x1=x_cen+h/2-tf, y1=y_cen+tw/2, fillcolor=style['fillcolor'], line_width=0)
        fig.add_shape(type="line", x0=x_cen-h/2+tf, y0=y_cen-tw/2, x1=x_cen+h/2-tf, y1=y_cen-tw/2, line=style['line'])
        fig.add_shape(type="line", x0=x_cen-h/2+tf, y0=y_cen+tw/2, x1=x_cen+h/2-tf, y1=y_cen+tw/2, line=style['line'])

# =============================================================================
# 1. PLAN VIEW (TOP VIEW)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    conn_type = plate.get('type', 'Fin Plate')
    
    col_h, col_b = max(300, beam['b']+50), max(300, beam['b']+50)
    col_tf, col_tw = 16, 12
    draw_h_beam_section(fig, -col_h/2, 0, col_h, col_b, col_tf, col_tw, STYLE['STEEL_CUT'], orientation="H")
    
    tp, wp = plate['t'], plate['w']
    tw = beam['tw']
    bolt_x = plate['e1']
    
    # --- LOGIC SEPARATION ---
    if "End Plate" in conn_type:
        # End Plate: Attached to Col Flange Face (x=0)
        # Plate is perpendicular to beam web
        draw_rect(fig, 0, -wp/2, tp, wp/2, STYLE['PLATE']) # Plate Thickness vertical
        
        # Beam starts AFTER plate
        beam_start_x = tp
        beam_len = 150
        draw_rect(fig, beam_start_x, -tw/2, beam_start_x+beam_len, tw/2, STYLE['STEEL_CUT'])
        
        # Bolts (Attach Plate to Col Flange)
        # Usually bolts are outside web, let's assume standard gauge
        g_bolt = 100 # mm gauge
        d = bolts['d']
        for sign in [-1, 1]:
            y_b = sign * g_bolt / 2
            # Bolt through Col Flange + Plate
            draw_rect(fig, -col_tf-10, y_b-d/2, tp+10, y_b+d/2, STYLE['BOLT'])
        
        add_leader(fig, tp, -wp/2, tp+40, -wp/2-40, "End Plate")

    elif "Double" in conn_type:
        # Double Angle
        angle_leg_web = wp  # Length along web
        angle_leg_col = 100 # Assume 100mm leg on column
        t_ang = tp
        
        # Draw 2 Angles (L-shape)
        for sign in [-1, 1]:
            y_base = sign * (tw/2)
            y_outer = sign * (tw/2 + t_ang)
            # Leg on Web
            draw_rect(fig, SETBACK, y_base, SETBACK+angle_leg_web, y_outer, STYLE['ANGLE'])
            # Leg on Column (Outstanding leg)
            draw_rect(fig, SETBACK, y_base, SETBACK+t_ang, y_base + (sign*angle_leg_col), STYLE['ANGLE'])
            
        # Beam Web (Sandwiched)
        beam_len = SETBACK + angle_leg_web + 50
        draw_rect(fig, SETBACK, -tw/2, beam_len, tw/2, STYLE['STEEL_CUT'])
        
        # Bolts (Through Angle-Web-Angle)
        d = bolts['d']
        cx = SETBACK + bolt_x
        draw_rect(fig, cx-d/2, -tw/2-t_ang-5, cx+d/2, tw/2+t_ang+5, STYLE['BOLT'])
        add_leader(fig, cx, tw/2+t_ang, cx+40, tw/2+t_ang+40, "Double Angle")
        
    else:
        # Fin Plate (Standard)
        draw_rect(fig, 0, -tp/2, wp, tp/2, STYLE['PLATE'])
        beam_len = wp + 60
        draw_rect(fig, SETBACK, tp/2, beam_len, tp/2+tw, STYLE['STEEL_CUT'])
        
        # Bolt
        d = bolts['d']
        cx = bolt_x
        y_head = -tp/2 - 8
        y_nut = tp/2 + tw + 10
        draw_rect(fig, cx-d/2, y_head, cx+d/2, y_nut, STYLE['BOLT'])
        
        add_leader(fig, wp, 0, wp+40, -40, "Fin Plate")

    # Common Annotations
    fig.add_annotation(x=beam_len+20, y=0, text="<b>SEC A-A</b>", showarrow=False, font=dict(color="red"))
    fig.update_layout(title="<b>PLAN VIEW</b>", height=400, plot_bgcolor="white", margin=dict(l=50, r=50, t=50, b=50), xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

# =============================================================================
# 2. ELEVATION VIEW (FRONT)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    conn_type = plate.get('type', 'Fin Plate')
    
    h_b, b_b = beam['h'], beam['b']
    h_pl, w_pl = plate['h'], plate['w']
    lv, sv, rows = plate['lv'], bolts['s_v'], bolts['rows']
    e1, cols, sh = plate['e1'], bolts['cols'], bolts['s_h']
    
    # 1. Column Ref
    fig.add_shape(type="line", x0=0, y0=-h_b/2-100, x1=0, y1=h_b/2+100, line=dict(color="black", width=2))
    
    # 2. Beam Ghost
    start_x = 0 if "End" in conn_type else SETBACK
    fig.add_shape(type="rect", x0=start_x, y0=-h_b/2, x1=w_pl+200, y1=h_b/2, 
                  fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(color="gray", width=1, dash="dot"))

    # 3. Connection Element & Bolts
    y_top = h_pl/2
    
    if "End Plate" in conn_type:
        # End Plate: Usually wider than beam, centered
        # w_pl input is likely Plate Width (horizontal)
        # h_pl input is Plate Height
        draw_rect(fig, -10, -h_pl/2, 10, h_pl/2, STYLE['PLATE']) # Side view of plate thickness? No this is Front View
        # Front view of End Plate: We see the face of the plate
        # Since we are looking from Side of connection? No, Front view usually means Web view.
        # For End Plate, "Front View" is looking at the Web. The End Plate is a line at the end.
        # But usually we want to see the Bolt Layout. Let's assume Front View = Looking at Plate Face.
        
        # Draw Plate Face
        draw_rect(fig, 0, -h_pl/2, w_pl, h_pl/2, STYLE['PLATE'])
        
        # Beam Profile behind (Ghost)
        # Bolts (Usually 2 columns)
        g_bolt = 100 # Gauge
        for r in range(rows):
            cy = (h_pl/2) - lv - (r * sv)
            # Left and Right of Beam Web
            cx_left = (w_pl/2) - (g_bolt/2)
            cx_right = (w_pl/2) + (g_bolt/2)
            
            for cx in [cx_left, cx_right]:
                d = bolts['d']
                fig.add_shape(type="circle", x0=cx-d/2, y0=cy-d/2, x1=cx+d/2, y1=cy+d/2, fillcolor="white", line=dict(color="black"))
        
        add_leader(fig, w_pl, h_pl/2, w_pl+50, h_pl/2+50, "End Plate Face")

    else:
        # Fin Plate & Double Angle (Similar geometry in this view)
        style_ele = STYLE['ANGLE'] if "Double" in conn_type else STYLE['PLATE']
        draw_rect(fig, 0, -h_pl/2, w_pl, h_pl/2, style_ele)
        
        # Bolts
        start_y = (h_pl/2) - lv
        for c in range(cols):
            cx = e1 + (c * sh)
            for r in range(rows):
                cy = start_y - (r * sv)
                d = bolts['d']
                fig.add_shape(type="circle", x0=cx-d/2, y0=cy-d/2, x1=cx+d/2, y1=cy+d/2, fillcolor="white", line=dict(color="black"))
        
        desc = "Double Angle" if "Double" in conn_type else "Fin Plate"
        add_leader(fig, w_pl/2, h_pl/2, w_pl/2+40, h_pl/2+50, desc)

    # Dims
    add_dim(fig, w_pl+20, h_pl/2, w_pl+20, h_pl/2-lv, f"{lv:.0f}", 10, "v")
    add_dim(fig, 0, -h_pl/2-20, w_pl, -h_pl/2-20, f"{w_pl:.0f}", -20, "h")

    fig.update_layout(title="<b>ELEVATION VIEW</b>", height=500, plot_bgcolor="white", margin=dict(l=80, r=80, t=60, b=60), xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

# =============================================================================
# 3. SIDE VIEW (SECTION A-A)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    conn_type = plate.get('type', 'Fin Plate')
    
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl, tp = plate['h'], plate['t']
    rows, sv, lv = bolts['rows'], bolts['s_v'], plate['lv']
    
    # 1. Column (Background)
    col_w, col_h = b + 50, h + 150
    draw_rect(fig, -col_w/2, -col_h/2, col_w/2, col_h/2, STYLE['STEEL_FACE'])
    
    if "End Plate" in conn_type:
        # End Plate: Vertical Plate at x=0
        # Beam starts at x = tp
        draw_rect(fig, -col_w/2, -h_pl/2, col_w/2, h_pl/2, dict(fillcolor="rgba(0,0,0,0)", line=dict(width=0))) # Ghost boundary
        
        # Plate (Side cut)
        # Actually in Side View, End Plate looks like a thin strip if sectioned through bolts,
        # or full width if looking from side. Assuming Section cut through center.
        # Plate is between Col Flange and Beam End.
        # Draw Plate Section
        draw_rect(fig, -col_w/2, -h_pl/2, col_w/2, h_pl/2, dict(fillcolor="white", line=dict(width=0))) # clear
        
        # Col Flange Face
        fig.add_shape(type="line", x0=-col_w/2, y0=-col_h/2, x1=col_w/2, y1=-col_h/2, line=dict(color="black"))
        
        # Since it's side view, we see the H-Beam Section profile?
        # No, Section A-A usually cuts vertically.
        # Let's draw the standard "Side View" of the assembly.
        
        # 1. Col Flange (Vertical Line)
        # 2. End Plate (Vertical Rect)
        draw_rect(fig, 0, -h_pl/2, tp, h_pl/2, STYLE['PLATE'])
        # 3. Beam (Starts after Plate)
        draw_h_beam_section(fig, tp + b/2, 0, h, b, tf, tw, STYLE['STEEL_CUT'], orientation="I")
        
        # Bolts: Go through Plate and Col Flange (assumed)
        y_start = (h_pl/2) - lv
        d = bolts['d']
        for r in range(rows):
            y = y_start - (r * sv)
            # Bolt Head inside Beam? Or outside? Usually outside.
            # Draw bolt passing through Plate
            draw_rect(fig, -15, y-d/2, tp+15, y+d/2, STYLE['BOLT'])
            
        add_leader(fig, tp/2, h_pl/2, tp/2+50, h_pl/2+50, "End Plate Side")
        
    elif "Double" in conn_type:
        # 1. Beam Section (Center)
        draw_h_beam_section(fig, 0, 0, h, b, tf, tw, STYLE['STEEL_CUT'], orientation="I")
        
        # 2. Double Angles (Left and Right of Web)
        # Angle Section
        draw_rect(fig, -tw/2-tp, -h_pl/2, -tw/2, h_pl/2, STYLE['ANGLE']) # Left Angle
        draw_rect(fig, tw/2, -h_pl/2, tw/2+tp, h_pl/2, STYLE['ANGLE'])   # Right Angle
        
        # 3. Bolts (Through all 3)
        y_start = (h_pl/2) - lv
        d = bolts['d']
        for r in range(rows):
            y = y_start - (r * sv)
            draw_rect(fig, -tw/2-tp-10, y-d/2, tw/2+tp+10, y+d/2, STYLE['BOLT'])
            
        add_leader(fig, tw/2+tp, 0, tw/2+tp+60, 20, "Double Angle")
        
    else:
        # Fin Plate
        draw_h_beam_section(fig, 0, 0, h, b, tf, tw, STYLE['STEEL_CUT'], orientation="I")
        # Plate (Right of Web usually, or Center? Fin plate replaces web or welded to it?
        # In section view, Fin plate is welded to Col, Beam Web is bolted to it.
        # So we see Beam Web (cut) and Plate (cut) overlapping?
        # Usually: Plate is welded to Col. Beam Web slides onto Plate.
        # In this view (looking from Column towards Beam), we see Beam Cross Section.
        # And the Plate is next to the web.
        
        draw_rect(fig, tw/2, -h_pl/2, tw/2+tp, h_pl/2, STYLE['PLATE'])
        
        y_start = (h_pl/2) - lv
        d = bolts['d']
        for r in range(rows):
            y = y_start - (r * sv)
            draw_rect(fig, -tw/2-10, y-d/2, tw/2+tp+10, y+d/2, STYLE['BOLT'])
            
        add_leader(fig, tw/2+tp, 0, tw/2+tp+60, 20, "Fin Plate")

    fig.update_layout(title="<b>SECTION A-A</b>", height=500, plot_bgcolor="white", margin=dict(l=80, r=80, t=60, b=60), xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

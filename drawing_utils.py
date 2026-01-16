# drawing_utils.py (V18 - Reworked Geometry)
import plotly.graph_objects as go
import numpy as np

# =============================================================================
# 🏗️ ENGINEER'S STANDARD STYLES
# =============================================================================
STYLE = {
    'STEEL_CUT':   dict(fillcolor="#D1D5DB", line=dict(color="black", width=2)),       
    'STEEL_FACE':  dict(fillcolor="#F3F4F6", line=dict(color="#9CA3AF", width=1)),     
    'PLATE':       dict(fillcolor="#BFDBFE", line=dict(color="#1E3A8A", width=2)),     
    'ANGLE':       dict(fillcolor="#C7D2FE", line=dict(color="#312E81", width=2)),
    'BOLT':        dict(fillcolor="#4B5563", line=dict(color="black", width=1)),       
    'CL':          dict(color="#DC2626", width=1, dash="dashdot"),                     
    'DIM':         dict(color="#1D4ED8", family="Arial", size=10),                     
    'WELD':        dict(fillcolor="black", line=dict(width=0))
}

SETBACK = 15

# =============================================================================
# 🛠️ HELPER FUNCTIONS (Basic Shapes & Annotations)
# =============================================================================
def add_dim(fig, x0, y0, x1, y1, text, offset=30, type="h"):
    col = STYLE['DIM']['color']
    ext = 5 * np.sign(offset)
    if type == "h": 
        y_pos = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos+ext, line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos+ext, line=dict(color=col, width=0.5))
        fig.add_annotation(x=x0, y=y_pos, ax=x1, ay=y_pos, arrowhead=2, arrowcolor=col, text="", arrowsize=1, arrowwidth=1)
        fig.add_annotation(x=x1, y=y_pos, ax=x0, ay=y_pos, arrowhead=2, arrowcolor=col, text="", arrowsize=1, arrowwidth=1)
        fig.add_annotation(x=(x0+x1)/2, y=y_pos+(8 if offset>0 else -12), text=f"<b>{text}</b>", showarrow=False, font=STYLE['DIM'])
    else: 
        x_pos = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos+ext, y1=y0, line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos+ext, y1=y1, line=dict(color=col, width=0.5))
        fig.add_annotation(x=x_pos, y=y0, ax=x_pos, ay=y1, arrowhead=2, arrowcolor=col, text="", arrowsize=1, arrowwidth=1)
        fig.add_annotation(x=x_pos, y=y1, ax=x_pos, ay=y0, arrowhead=2, arrowcolor=col, text="", arrowsize=1, arrowwidth=1)
        fig.add_annotation(x=x_pos+(12 if offset>0 else -12), y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, textangle=-90, font=STYLE['DIM'])

def add_leader(fig, x, y, ax, ay, text):
    fig.add_annotation(x=x, y=y, ax=ax, ay=ay, text=f"<b>{text}</b>", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1,
                       font=dict(size=10, color="black"), bgcolor="rgba(255,255,255,0.7)")

def draw_rect(fig, x0, y0, x1, y1, style, layer="above"):
    fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, fillcolor=style.get('fillcolor'), line=style.get('line'), layer=layer)

def draw_bolt_assy(fig, x, y, d, length, orientation="h"):
    """Draw schematic bolt assembly (Head + Nut + Shank)"""
    head_h, nut_h = d*0.6, d*0.8
    if orientation == "h":
        # Shank
        draw_rect(fig, x-length/2, y-d/2, x+length/2, y+d/2, STYLE['BOLT'])
        # Head (Left)
        draw_rect(fig, x-length/2-head_h, y-d, x-length/2, y+d, STYLE['BOLT'])
        # Nut (Right)
        draw_rect(fig, x+length/2, y-d, x+length/2+nut_h, y+d, STYLE['BOLT'])
    else: # Vertical
        # Shank
        draw_rect(fig, x-d/2, y-length/2, x+d/2, y+length/2, STYLE['BOLT'])
        # Head (Top)
        draw_rect(fig, x-d, y+length/2, x+d, y+length/2+head_h, STYLE['BOLT'])
        # Nut (Bottom)
        draw_rect(fig, x-d, y-length/2-nut_h, x+d, y-length/2, STYLE['BOLT'])

def draw_l_section(fig, x_corner, y_corner, leg_h, leg_v, t, style, mirror_x=False):
    """Draw L-shape angle section"""
    mx = -1 if mirror_x else 1
    path = f"M {x_corner} {y_corner} L {x_corner + mx*leg_h} {y_corner} L {x_corner + mx*leg_h} {y_corner+t} L {x_corner + mx*t} {y_corner+t} L {x_corner + mx*t} {y_corner+leg_v} L {x_corner} {y_corner+leg_v} Z"
    fig.add_shape(type="path", path=path, fillcolor=style['fillcolor'], line=style['line'])

def draw_i_section(fig, x, y, h, b, tf, tw, style, orient="I"):
    if orient == "I":
        draw_rect(fig, x-b/2, y+h/2-tf, x+b/2, y+h/2, style) # Top Flange
        draw_rect(fig, x-b/2, y-h/2, x+b/2, y-h/2+tf, style) # Bot Flange
        draw_rect(fig, x-tw/2, y-h/2+tf, x+tw/2, y+h/2-tf, style) # Web
    else: # H
        draw_rect(fig, x-h/2, y-b/2, x-h/2+tf, y+b/2, style) # Left Flange
        draw_rect(fig, x+h/2-tf, y-b/2, x+h/2, y+b/2, style) # Right Flange
        draw_rect(fig, x-h/2+tf, y-tw/2, x+h/2-tf, y+tw/2, style) # Web

# =============================================================================
# 1. PLAN VIEW (TOP VIEW)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    conn_type = plate.get('type', 'Fin Plate')
    
    # Beam props
    bh, bb, btf, btw = beam['h'], beam['b'], beam['tf'], beam['tw']
    # Plate/Connection props
    ph, pw, pt = plate['h'], plate['w'], plate['t']
    # Bolt props
    bd = bolts['d']
    
    # Reference Point (0,0) is center of column flange face
    col_width = max(300, bb + 100)
    
    # 1. Draw Column (Support) - H Shape viewed from top
    draw_i_section(fig, -col_width/2, 0, col_width, col_width, 20, 12, STYLE['STEEL_CUT'], orient="H")
    
    if "End Plate" in conn_type:
        # --- END PLATE PLAN ---
        # Plate is welded to beam end, bolted to column flange
        
        # 1. End Plate (seen from top as a line with thickness pt)
        # Located at x=0 (against column face)
        draw_rect(fig, 0, -bb/2, pt, bb/2, STYLE['PLATE']) # Assuming plate width ~= beam width for now
        
        # 2. Beam (Top View) starts after plate
        beam_start_x = pt
        beam_len = 300
        # Top Flange Face
        draw_rect(fig, beam_start_x, -bb/2, beam_start_x+beam_len, bb/2, STYLE['STEEL_FACE'])
        # Web Hidden line (dashed)
        fig.add_shape(type="line", x0=beam_start_x, y0=0, x1=beam_start_x+beam_len, y1=0, line=dict(color="gray", dash="dot"))
        
        # 3. Bolts (Connecting Plate to Column Flange)
        # Assuming gauge g = 100mm
        g = 100
        bolt_len = pt + 25 # Plate t + Col Flange t + extra
        draw_bolt_assy(fig, pt/2, g/2, bd, bolt_len, "h")
        draw_bolt_assy(fig, pt/2, -g/2, bd, bolt_len, "h")
        
        add_leader(fig, pt, bb/2, pt+50, bb/2+50, "End Plate welded to Beam")

    elif "Double" in conn_type:
        # --- DOUBLE ANGLE PLAN ---
        # Two angles sandwiching the beam web.
        
        # 1. Beam Web (Cut section view from top)
        beam_start_x = SETBACK
        beam_len = 300
        draw_rect(fig, beam_start_x, -btw/2, beam_start_x+beam_len, btw/2, STYLE['STEEL_CUT'])
        
        # 2. Double Angles (L-shapes)
        ang_leg = pw # Use input width as leg length
        t_ang = pt   # Use input thickness as angle thickness
        
        # Top Angle (y > 0)
        draw_l_section(fig, SETBACK, btw/2, ang_leg, 100, t_ang, STYLE['ANGLE'], mirror_x=False)
        # Bottom Angle (y < 0) - Mirror Y roughly by drawing coords
        draw_l_section(fig, SETBACK, -btw/2, ang_leg, -100, t_ang, STYLE['ANGLE'], mirror_x=False)
        # Adjust bottom angle y-coords to be correct L-shape facing out
        # Re-draw correctly:
        # Top angle
        draw_rect(fig, SETBACK, btw/2, SETBACK+ang_leg, btw/2+t_ang, STYLE['ANGLE']) # Leg on web
        draw_rect(fig, SETBACK, btw/2+t_ang, SETBACK+t_ang, btw/2+100, STYLE['ANGLE']) # Outstanding leg
        # Bot angle
        draw_rect(fig, SETBACK, -btw/2-t_ang, SETBACK+ang_leg, -btw/2, STYLE['ANGLE']) # Leg on web
        draw_rect(fig, SETBACK, -btw/2-100, SETBACK+t_ang, -btw/2-t_ang, STYLE['ANGLE']) # Outstanding leg

        # 3. Bolts (Through Angle-Web-Angle)
        bx = SETBACK + plate['e1']
        bolt_len = btw + 2*t_ang + 20
        draw_bolt_assy(fig, bx, 0, bd, bolt_len, "v") # Vertical bolt in this view
        
        add_leader(fig, bx, btw/2+t_ang, bx+50, btw/2+t_ang+50, "2L-Angles")

    else:
        # --- FIN PLATE PLAN (Default) ---
        # Plate welded to column face. Beam web laps plate.
        
        # 1. Fin Plate (Welded to Column at x=0)
        draw_rect(fig, 0, -pt/2, pw, pt/2, STYLE['PLATE'])
        
        # 2. Beam Web (Laps plate, starts at Setback)
        beam_len = pw + 100
        # Assume beam web is "below" plate in this view (y < 0)
        draw_rect(fig, SETBACK, -pt/2-btw, SETBACK+beam_len, -pt/2, STYLE['STEEL_CUT'])
        
        # 3. Weld Symbol (at x=0)
        ws = plate['weld_size']
        fig.add_shape(type="path", path=f"M 0 {pt/2} L {ws} {pt/2} L 0 {pt/2+ws} Z", fillcolor="black", line_width=0)
        fig.add_shape(type="path", path=f"M 0 {-pt/2} L {ws} {-pt/2} L 0 {-pt/2-ws} Z", fillcolor="black", line_width=0)

        # 4. Bolt (Through Plate and Web)
        bx = plate['e1']
        bolt_len = pt + btw + 20
        draw_bolt_assy(fig, bx, -pt/2, bd, bolt_len, "v")
        
        add_leader(fig, pw, pt/2, pw+50, pt/2+50, "Fin Plate")
        add_dim(fig, 0, 0, SETBACK, 0, f"Setback {SETBACK}", -40, "h")

    # Global Layout settings
    fig.update_layout(title="<b>PLAN VIEW</b>", height=450, plot_bgcolor="white", 
                      margin=dict(l=50, r=50, t=70, b=50), 
                      xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

# =============================================================================
# 2. ELEVATION VIEW (FRONT VIEW of Connection)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    conn_type = plate.get('type', 'Fin Plate')
    
    bh = beam['h']
    ph, pw = plate['h'], plate['w']
    rows, cols = bolts['rows'], bolts['cols']
    sv, sh = bolts['s_v'], bolts['s_h']
    lv, e1 = plate['lv'], plate['e1']
    bd = bolts['d']

    # Center of connection at (0,0)
    
    if "End Plate" in conn_type:
        # --- END PLATE FRONT VIEW ---
        # Looking at the face of the End Plate bolted to column.
        
        # 1. End Plate Face
        # Assuming ph is height, pw is width of end plate
        draw_rect(fig, -pw/2, -ph/2, pw/2, ph/2, STYLE['PLATE'])
        
        # 2. Beam Profile (Welded behind plate - dashed lines)
        fig.add_shape(type="rect", x0=-beam['b']/2, y0=-bh/2, x1=beam['b']/2, y1=bh/2, line=dict(color="gray", dash="dot"))
        
        # 3. Bolts Pattern
        # Assume symmetric gauge based on width if cols=2
        g = sh if cols > 1 else pw*0.6 
        start_y = (ph/2) - lv
        
        bolt_cols_x = [-g/2, g/2] if cols > 1 else [0]
        
        for bx in bolt_cols_x:
            for r in range(rows):
                by = start_y - (r * sv)
                # Draw Bolt Head
                fig.add_shape(type="circle", x0=bx-bd*0.6, y0=by-bd*0.6, x1=bx+bd*0.6, y1=by+bd*0.6, 
                              fillcolor="white", line=dict(color="black"))
                
        add_dim(fig, -pw/2, -ph/2-30, pw/2, -ph/2-30, f"PL Width {pw}", -20, "h")
        add_dim(fig, pw/2+30, ph/2, pw/2+30, -ph/2, f"PL Height {ph}", 30, "v")

    else:
        # --- FIN PLATE & DOUBLE ANGLE FRONT VIEW ---
        # Looking at the side of the beam web, seeing the plate/angle face.
        
        # 1. Beam Ghost Line
        fig.add_shape(type="line", x0=-100, y0=bh/2, x1=pw+100, y1=bh/2, line=dict(color="gray", dash="dot"))
        fig.add_shape(type="line", x0=-100, y0=-bh/2, x1=pw+100, y1=-bh/2, line=dict(color="gray", dash="dot"))
        
        # 2. Plate/Angle Face
        style = STYLE['ANGLE'] if "Double" in conn_type else STYLE['PLATE']
        # Assuming top of plate is aligned with some reference, let's center it vertically for now
        draw_rect(fig, 0, -ph/2, pw, ph/2, style)
        
        # 3. Bolts Pattern
        start_y = (ph/2) - lv
        for c in range(cols):
            bx = e1 + (c * sh)
            for r in range(rows):
                by = start_y - (r * sv)
                fig.add_shape(type="circle", x0=bx-bd/2, y0=by-bd/2, x1=bx+bd/2, y1=by+bd/2, 
                              fillcolor="white", line=dict(color="black"))
        
        desc = "Angles (Near & Far)" if "Double" in conn_type else "Fin Plate (Near side)"
        add_leader(fig, pw, ph/2, pw+50, ph/2+50, desc)
        
        # Dims
        add_dim(fig, pw+20, ph/2, pw+20, ph/2-lv, f"lv={lv}", 10, "v")
        if rows > 1:
             add_dim(fig, pw+20, ph/2-lv, pw+20, ph/2-lv-sv, f"pitch={sv}", 10, "v")

    # Global Layout
    fig.update_layout(title="<b>ELEVATION VIEW</b>", height=500, plot_bgcolor="white", 
                      margin=dict(l=80, r=80, t=70, b=60), 
                      xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

# =============================================================================
# 3. SIDE VIEW (SECTION A-A)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    conn_type = plate.get('type', 'Fin Plate')
    
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    ph, pt = plate['h'], plate['t']
    bd = bolts['d']
    
    # Reference: (0,0) center of beam web

    if "End Plate" in conn_type:
        # --- END PLATE SECTION ---
        # Cut through beam and end plate.
        
        # 1. Beam Section (I-shape)
        # Beam ends at x=0, Plate is at x>0
        draw_i_section(fig, -b/2, 0, h, b, tf, tw, STYLE['STEEL_CUT'], orient="I")
        
        # 2. End Plate (Cut section)
        # Welded to beam end.
        draw_rect(fig, 0, -ph/2, pt, ph/2, STYLE['PLATE'])
        
        # 3. Support (Column Flange Face) - Ghost
        draw_rect(fig, pt, -h/2-50, pt+20, h/2+50, STYLE['STEEL_FACE'])
        
        # 4. Bolt (Through Plate and Support)
        # Assume bolt is somewhere along the height
        by = h/2 - 100 
        bolt_len = pt + 20 + 20
        draw_bolt_assy(fig, pt, by, bd, bolt_len, "h")
        
        add_leader(fig, pt/2, ph/2, pt/2+50, ph/2+50, "End Plate (t={pt})")

    elif "Double" in conn_type:
        # --- DOUBLE ANGLE SECTION ---
        # Cut through web and two angles.
        
        # 1. Beam Web (Center)
        draw_rect(fig, -tw/2, -h/2, tw/2, h/2, STYLE['STEEL_CUT']) # Simplified web view
        # Add Flanges ghost
        draw_rect(fig, -b/2, h/2-tf, b/2, h/2, STYLE['STEEL_FACE'])
        draw_rect(fig, -b/2, -h/2, b/2, -h/2+tf, STYLE['STEEL_FACE'])
        
        # 2. Double Angles (Cut section)
        # Left Angle
        draw_rect(fig, -tw/2-pt, -ph/2, -tw/2, ph/2, STYLE['ANGLE'])
        # Right Angle
        draw_rect(fig, tw/2, -ph/2, tw/2+pt, ph/2, STYLE['ANGLE'])
        
        # 3. Bolt (Through all)
        by = ph/2 - plate['lv']
        bolt_len = tw + 2*pt + 30
        draw_bolt_assy(fig, 0, by, bd, bolt_len, "h")
        
        add_leader(fig, tw/2+pt, 0, tw/2+pt+60, 30, "2-Angles")

    else:
        # --- FIN PLATE SECTION (Default) ---
        # Cut through web and one plate.
        
        # 1. Beam Web
        draw_rect(fig, -tw/2, -h/2, tw/2, h/2, STYLE['STEEL_CUT'])
        # Flanges ghost
        draw_rect(fig, -b/2, h/2-tf, b/2, h/2, STYLE['STEEL_FACE'])
        draw_rect(fig, -b/2, -h/2, b/2, -h/2+tf, STYLE['STEEL_FACE'])
        
        # 2. Fin Plate (Lapped on one side, say Right)
        draw_rect(fig, tw/2, -ph/2, tw/2+pt, ph/2, STYLE['PLATE'])
        
        # 3. Bolt (Through Web & Plate)
        by = ph/2 - plate['lv']
        bolt_len = tw + pt + 30
        draw_bolt_assy(fig, tw/2, by, bd, bolt_len, "h")
        
        add_leader(fig, tw/2+pt, 0, tw/2+pt+60, 30, "Fin Plate (Single Shear)")

    # Global Layout
    fig.update_layout(title="<b>SECTION VIEW</b>", height=500, plot_bgcolor="white", 
                      margin=dict(l=80, r=80, t=70, b=60), 
                      xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

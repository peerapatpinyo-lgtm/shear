# drawing_utils.py (Final Fix - Smart Zoom & Pixel Offset)
import plotly.graph_objects as go
import numpy as np

# =============================================================================
# 🎨 STYLES
# =============================================================================
STYLE = {
    'STEEL_CUT':   dict(fillcolor="#D1D5DB", line=dict(color="black", width=2)),       
    'STEEL_FACE':  dict(fillcolor="#F3F4F6", line=dict(color="#9CA3AF", width=1)),     
    'PLATE':       dict(fillcolor="#BFDBFE", line=dict(color="#1E3A8A", width=2)),     
    'ANGLE':       dict(fillcolor="#C7D2FE", line=dict(color="#312E81", width=2)),
    'BOLT':        dict(fillcolor="#4B5563", line=dict(color="black", width=1)),       
    'DIM':         dict(color="#1D4ED8", family="Arial", size=11),                     
}

SETBACK = 15

# =============================================================================
# 🛠️ HELPER FUNCTIONS (FIXED SCALING)
# =============================================================================
def add_dim(fig, x0, y0, x1, y1, text, offset=30, type="h"):
    """
    Draw dimension lines. 
    offset: distance in pixels/units from the object.
    """
    col = STYLE['DIM']['color']
    # Small extension lines
    ext = 5 * np.sign(offset)
    
    if type == "h": 
        y_pos = y0 + offset
        # Extension lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos+ext, line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos+ext, line=dict(color=col, width=0.5))
        # Main Dim line
        fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=col, width=1))
        # Arrows (using annotations to simulate arrows)
        fig.add_annotation(x=x0, y=y_pos, ax=x0+10, ay=y_pos, arrowhead=2, arrowcolor=col, arrowsize=1, text="")
        fig.add_annotation(x=x1, y=y_pos, ax=x1-10, ay=y_pos, arrowhead=2, arrowcolor=col, arrowsize=1, text="")
        # Text
        fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=f"<b>{text}</b>", showarrow=False, yshift=(10 if offset>0 else -10), font=STYLE['DIM'])
        
    else: # Vertical
        x_pos = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos+ext, y1=y0, line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos+ext, y1=y1, line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x_pos, y0=y0, x1=x_pos, y1=y1, line=dict(color=col, width=1))
        fig.add_annotation(x=x_pos, y=y0, ax=x_pos, ay=y0+10, arrowhead=2, arrowcolor=col, arrowsize=1, text="")
        fig.add_annotation(x=x_pos, y=y1, ax=x_pos, ay=y1-10, arrowhead=2, arrowcolor=col, arrowsize=1, text="")
        fig.add_annotation(x=x_pos, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=(10 if offset>0 else -10), textangle=-90, font=STYLE['DIM'])

def add_leader(fig, x, y, text, ax_offset=40, ay_offset=-40):
    """
    Add a leader line pointing to (x,y).
    ax_offset, ay_offset: PIXEL distance from point (prevents scaling issues).
    """
    fig.add_annotation(
        x=x, y=y,
        ax=ax_offset, ay=ay_offset,
        axref="pixel", ayref="pixel",  # KEY FIX: Use pixels, not data coordinates
        text=f"<b>{text}</b>",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5,
        font=dict(size=11, color="black"),
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="black", borderwidth=1,
        opacity=0.9
    )

def draw_rect(fig, x0, y0, x1, y1, style):
    fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, fillcolor=style.get('fillcolor'), line=style.get('line'))

def draw_bolt_assy(fig, x, y, d, length, orientation="h"):
    head_h, nut_h = d*0.6, d*0.8
    if orientation == "h":
        draw_rect(fig, x-length/2, y-d/2, x+length/2, y+d/2, STYLE['BOLT'])
        draw_rect(fig, x-length/2-head_h, y-d, x-length/2, y+d, STYLE['BOLT'])
        draw_rect(fig, x+length/2, y-d, x+length/2+nut_h, y+d, STYLE['BOLT'])
    else:
        draw_rect(fig, x-d/2, y-length/2, x+d/2, y+length/2, STYLE['BOLT'])
        draw_rect(fig, x-d, y+length/2, x+d, y+length/2+head_h, STYLE['BOLT'])
        draw_rect(fig, x-d, y-length/2-nut_h, x+d, y-length/2, STYLE['BOLT'])

def draw_i_section(fig, x, y, h, b, tf, tw, style, orient="I"):
    if orient == "I":
        draw_rect(fig, x-b/2, y+h/2-tf, x+b/2, y+h/2, style) # Top Flange
        draw_rect(fig, x-b/2, y-h/2, x+b/2, y-h/2+tf, style) # Bot Flange
        draw_rect(fig, x-tw/2, y-h/2+tf, x+tw/2, y+h/2-tf, style) # Web
    else: # H
        draw_rect(fig, x-h/2, y-b/2, x-h/2+tf, y+b/2, style)
        draw_rect(fig, x+h/2-tf, y-b/2, x+h/2, y+b/2, style)
        draw_rect(fig, x-h/2+tf, y-tw/2, x+h/2-tf, y+tw/2, style)

def set_smart_layout(fig, title, max_dim=400):
    """Sets a fixed aspect ratio and reasonable zoom padding"""
    padding = max_dim * 0.6
    fig.update_layout(
        title=dict(text=title, y=0.95),
        height=500,
        plot_bgcolor="white",
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis=dict(visible=False, range=[-padding, padding], scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False, range=[-padding, padding]),
        showlegend=False
    )

# =============================================================================
# 1. PLAN VIEW
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    conn_type = plate.get('type', 'Fin Plate')
    
    bh, bb, btf, btw = beam['h'], beam['b'], beam['tf'], beam['tw']
    ph, pw, pt = plate['h'], plate['w'], plate['t']
    bd = bolts['d']
    
    col_size = max(250, bb+50)
    
    # 1. Column (H-Shape)
    draw_i_section(fig, -col_size/2, 0, col_size, col_size, 16, 10, STYLE['STEEL_CUT'], orient="H")

    if "End Plate" in conn_type:
        draw_rect(fig, 0, -bb/2, pt, bb/2, STYLE['PLATE']) # Plate
        draw_rect(fig, pt, -bb/2, pt+200, bb/2, STYLE['STEEL_FACE']) # Beam
        # Bolts
        g = 100
        draw_bolt_assy(fig, pt/2, g/2, bd, pt+30, "h")
        draw_bolt_assy(fig, pt/2, -g/2, bd, pt+30, "h")
        add_leader(fig, pt, bb/2, "End Plate")
        
    elif "Double" in conn_type:
        # Beam Web
        draw_rect(fig, SETBACK, -btw/2, SETBACK+200, btw/2, STYLE['STEEL_CUT'])
        # Angles
        ang_leg = pw
        draw_rect(fig, SETBACK, btw/2, SETBACK+ang_leg, btw/2+pt, STYLE['ANGLE']) # Top
        draw_rect(fig, SETBACK, btw/2, SETBACK+pt, btw/2+60, STYLE['ANGLE'])
        draw_rect(fig, SETBACK, -btw/2-pt, SETBACK+ang_leg, -btw/2, STYLE['ANGLE']) # Bot
        draw_rect(fig, SETBACK, -btw/2-pt, SETBACK+pt, -btw/2-60, STYLE['ANGLE'])
        # Bolt
        cx = SETBACK + plate['e1']
        draw_bolt_assy(fig, cx, 0, bd, btw+2*pt+20, "v")
        add_leader(fig, cx, btw/2+pt, "Double Angle")
        
    else: # Fin Plate
        draw_rect(fig, 0, -pt/2, pw, pt/2, STYLE['PLATE']) # Plate
        draw_rect(fig, SETBACK, -pt/2-btw, SETBACK+200, -pt/2, STYLE['STEEL_CUT']) # Beam
        # Bolt
        cx = plate['e1']
        draw_bolt_assy(fig, cx, -pt/2, bd, pt+btw+20, "v")
        add_leader(fig, cx, pt/2, "Fin Plate")
        add_dim(fig, 0, 0, SETBACK, 0, f"{SETBACK}", -30, "h")

    set_smart_layout(fig, "<b>PLAN VIEW</b>", max_dim=max(col_size/1.5, 200))
    return fig

# =============================================================================
# 2. FRONT VIEW
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    conn_type = plate.get('type', 'Fin Plate')
    
    ph, pw = plate['h'], plate['w']
    rows, cols = bolts['rows'], bolts['cols']
    sv, sh = bolts['s_v'], bolts['s_h']
    lv, e1 = plate['lv'], plate['e1']
    bd = bolts['d']
    
    if "End Plate" in conn_type:
        draw_rect(fig, -pw/2, -ph/2, pw/2, ph/2, STYLE['PLATE']) # Plate Face
        add_dim(fig, pw/2+20, ph/2, pw/2+20, -ph/2, f"H={ph}", 0, "v")
        # Bolts (Assume centered)
        start_y = (ph/2) - lv
        g = sh if cols > 1 else pw*0.6
        x_pos = [-g/2, g/2] if cols > 1 else [0]
        for x in x_pos:
            for r in range(rows):
                y = start_y - (r * sv)
                fig.add_shape(type="circle", x0=x-bd/2, y0=y-bd/2, x1=x+bd/2, y1=y+bd/2, fillcolor="white", line=dict(color="black"))
        
        add_leader(fig, -pw/2, ph/2, "End Plate")

    else: # Fin / Double
        draw_rect(fig, 0, -ph/2, pw, ph/2, STYLE['PLATE'])
        start_y = (ph/2) - lv
        for c in range(cols):
            cx = e1 + (c * sh)
            for r in range(rows):
                cy = start_y - (r * sv)
                fig.add_shape(type="circle", x0=cx-bd/2, y0=cy-bd/2, x1=cx+bd/2, y1=cy+bd/2, fillcolor="white", line=dict(color="black"))
        
        add_leader(fig, pw, ph/2, "Plate/Angle")
        add_dim(fig, pw+10, ph/2, pw+10, ph/2-lv, f"{lv}", 10, "v")
        if rows > 1:
            add_dim(fig, pw+10, ph/2-lv, pw+10, ph/2-lv-sv, f"s={sv}", 10, "v")

    set_smart_layout(fig, "<b>FRONT VIEW</b>", max_dim=max(ph, pw, 200))
    return fig

# =============================================================================
# 3. SIDE VIEW
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    conn_type = plate.get('type', 'Fin Plate')
    
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    ph, pt = plate['h'], plate['t']
    bd = bolts['d']
    
    if "End Plate" in conn_type:
        draw_i_section(fig, -b/2, 0, h, b, tf, tw, STYLE['STEEL_CUT']) # Beam
        draw_rect(fig, 0, -ph/2, pt, ph/2, STYLE['PLATE']) # Plate
        draw_rect(fig, pt, -h/2-20, pt+20, h/2+20, STYLE['STEEL_FACE']) # Col
        # Bolt
        draw_bolt_assy(fig, pt, h/2-80, bd, pt+40, "h")
        add_leader(fig, pt/2, ph/2, "End Plate")
        
    elif "Double" in conn_type:
        draw_rect(fig, -tw/2, -h/2, tw/2, h/2, STYLE['STEEL_CUT']) # Web
        draw_rect(fig, -tw/2-pt, -ph/2, -tw/2, ph/2, STYLE['ANGLE']) # Left Ang
        draw_rect(fig, tw/2, -ph/2, tw/2+pt, ph/2, STYLE['ANGLE']) # Right Ang
        draw_bolt_assy(fig, 0, ph/2-plate['lv'], bd, tw+2*pt+30, "h")
        add_leader(fig, tw/2+pt, 0, "Double Angle")
        
    else: # Fin
        draw_rect(fig, -tw/2, -h/2, tw/2, h/2, STYLE['STEEL_CUT']) # Web
        draw_rect(fig, tw/2, -ph/2, tw/2+pt, ph/2, STYLE['PLATE']) # Plate
        draw_bolt_assy(fig, tw/2, ph/2-plate['lv'], bd, tw+pt+30, "h")
        add_leader(fig, tw/2+pt, 0, "Fin Plate")

    set_smart_layout(fig, "<b>SECTION VIEW</b>", max_dim=max(h, 250))
    return fig

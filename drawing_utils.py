import plotly.graph_objects as go
import numpy as np

# =============================================================================
# 🎨 1. ENGINEERING STYLES (มาตรฐานก่อสร้าง)
# =============================================================================
STYLE = {
    'STEEL_CUT':   dict(fillcolor="#D1D5DB", line=dict(color="black", width=2)), # หน้าตัด (เทา)
    'STEEL_FACE':  dict(fillcolor="#F3F4F6", line=dict(color="#6B7280", width=1)), # ผิวเห็น (เทาอ่อน)
    'PLATE':       dict(fillcolor="#BFDBFE", line=dict(color="#1E3A8A", width=2)), # Plate (ฟ้า)
    'ANGLE':       dict(fillcolor="#C7D2FE", line=dict(color="#312E81", width=2)), # Angle (ม่วงอ่อน)
    'BOLT':        dict(fillcolor="#374151", line=dict(color="black", width=1)), # Bolt
    'CL':          dict(color="#DC2626", width=1, dash="dashdot"), # Center Line
    'DIM':         dict(color="#1D4ED8", family="Arial", size=11), # Dimension Color
    'WELD':        dict(fillcolor="black", line=dict(width=0)), # เชื่อม
}

SETBACK = 15 # ระยะห่างมาตรฐาน

# =============================================================================
# 🛠️ 2. UTILITY FUNCTIONS (Smart Scaling)
# =============================================================================
def add_dim(fig, x0, y0, x1, y1, text, offset=30, type="h"):
    """เขียน Dimension โดยใช้ Pixel Shift เพื่อไม่ให้กราฟระเบิด (Fix Zoom Issue)"""
    col = STYLE['DIM']['color']
    
    if type == "h": 
        y_pos = y0 + offset
        # Main Line & Extensions
        fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=col, width=1))
        ext_dir = np.sign(offset) if offset != 0 else 1
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos+(5*ext_dir), line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos+(5*ext_dir), line=dict(color=col, width=0.5))
        # Arrows (Pixel based)
        fig.add_annotation(x=x0, y=y_pos, ax=15, ay=0, axref="pixel", ayref="pixel", arrowhead=2, arrowsize=1, arrowcolor=col, text="")
        fig.add_annotation(x=x1, y=y_pos, ax=-15, ay=0, axref="pixel", ayref="pixel", arrowhead=2, arrowsize=1, arrowcolor=col, text="")
        # Text
        shift_val = 10 if offset > 0 else -15
        fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=f"<b>{text}</b>", showarrow=False, yshift=shift_val, font=dict(size=11, color=col))
    
    else: # Vertical
        x_pos = x0 + offset
        ext_dir = np.sign(offset) if offset != 0 else 1
        fig.add_shape(type="line", x0=x_pos, y0=y0, x1=x_pos, y1=y1, line=dict(color=col, width=1))
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos+(5*ext_dir), y1=y0, line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos+(5*ext_dir), y1=y1, line=dict(color=col, width=0.5))
        # Arrows
        fig.add_annotation(x=x_pos, y=y0, ax=0, ay=15, axref="pixel", ayref="pixel", arrowhead=2, arrowsize=1, arrowcolor=col, text="")
        fig.add_annotation(x=x_pos, y=y1, ax=0, ay=-15, axref="pixel", ayref="pixel", arrowhead=2, arrowsize=1, arrowcolor=col, text="")
        # Text
        shift_val = 15 if offset > 0 else -15
        fig.add_annotation(x=x_pos, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=shift_val, textangle=-90, font=dict(size=11, color=col))

def add_leader(fig, x, y, text, ax=40, ay=-40, align="left"):
    """Leader Line แบบ Pixel Reference (ไม่ทำให้กราฟเพี้ยน)"""
    fig.add_annotation(
        x=x, y=y, ax=ax, ay=ay, axref="pixel", ayref="pixel",
        text=f"<b>{text}</b>", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5,
        font=dict(size=11, color="black"), align=align, bgcolor="rgba(255,255,255,0.8)"
    )

def draw_h_section(fig, x, y, h, b, tf, tw, style, orient="I"):
    """วาดหน้าตัดเหล็ก H-Beam/I-Beam"""
    if orient == "I":
        # Web & Flanges
        fig.add_shape(type="path", path=f"M {x-tw/2} {y-h/2+tf} L {x-tw/2} {y+h/2-tf} L {x+tw/2} {y+h/2-tf} L {x+tw/2} {y-h/2+tf} Z", fillcolor=style['fillcolor'], line=dict(width=0))
        fig.add_shape(type="rect", x0=x-b/2, y0=y+h/2-tf, x1=x+b/2, y1=y+h/2, fillcolor=style['fillcolor'], line=style['line']) # Top
        fig.add_shape(type="rect", x0=x-b/2, y0=y-h/2, x1=x+b/2, y1=y-h/2+tf, fillcolor=style['fillcolor'], line=style['line']) # Bot
        fig.add_shape(type="line", x0=x-tw/2, y0=y-h/2+tf, x1=x-tw/2, y1=y+h/2-tf, line=style['line']) # Web Line L
        fig.add_shape(type="line", x0=x+tw/2, y0=y-h/2+tf, x1=x+tw/2, y1=y+h/2-tf, line=style['line']) # Web Line R
    else: # H (Column Top View)
        fig.add_shape(type="rect", x0=x-h/2, y0=y-b/2, x1=x-h/2+tf, y1=y+b/2, fillcolor=style['fillcolor'], line=style['line'])
        fig.add_shape(type="rect", x0=x+h/2-tf, y0=y-b/2, x1=x+h/2, y1=y+b/2, fillcolor=style['fillcolor'], line=style['line'])
        fig.add_shape(type="rect", x0=x-h/2+tf, y0=y-tw/2, x1=x+h/2-tf, y1=y+tw/2, fillcolor=style['fillcolor'], line=dict(width=0))
        fig.add_shape(type="line", x0=x-h/2+tf, y0=y-tw/2, x1=x+h/2-tf, y1=y-tw/2, line=style['line'])
        fig.add_shape(type="line", x0=x-h/2+tf, y0=y+tw/2, x1=x+h/2-tf, y1=y+tw/2, line=style['line'])

def set_layout(fig, title, limit):
    """ตั้งค่า Layout ให้แน่นและสเกลถูกต้อง"""
    pad = limit * 0.6
    fig.update_layout(
        title=dict(text=title, y=0.95, x=0.5, xanchor='center', font=dict(size=14)),
        height=500, margin=dict(l=40, r=40, t=60, b=40), plot_bgcolor="white",
        xaxis=dict(visible=False, range=[-pad, pad], scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False, range=[-pad, pad]), showlegend=False
    )

# =============================================================================
# 3. VIEW GENERATORS (PLAN, FRONT, SIDE)
# =============================================================================

# --- 3.1 PLAN VIEW (TOP VIEW) ---
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    conn_type = plate.get('type', 'Fin Plate')
    
    # Column (H-Shape Cut)
    col_h, col_b = max(300, beam['b']+50), max(300, beam['b']+50)
    draw_h_section(fig, -col_h/2, 0, col_h, col_b, 16, 12, STYLE['STEEL_CUT'], orient="H")
    
    tp, wp, d = plate['t'], plate['w'], bolts['d']

    # --- LOGIC: FIN PLATE ---
    if conn_type == "Fin Plate":
        # Plate & Beam
        fig.add_shape(type="rect", x0=0, y0=-tp/2, x1=wp, y1=tp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        fig.add_shape(type="rect", x0=SETBACK, y0=tp/2, x1=wp+100, y1=tp/2+beam['tw'], fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
        
        # Bolt
        bx = plate['e1']
        fig.add_shape(type="rect", x0=bx-d/2, y0=-tp/2-10, x1=bx+d/2, y1=tp/2+beam['tw']+12, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
        fig.add_shape(type="rect", x0=bx-d, y0=-tp/2-18, x1=bx+d, y1=-tp/2-10, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black",width=1)) # Head
        fig.add_shape(type="rect", x0=bx-d, y0=tp/2+beam['tw']+12, x1=bx+d, y1=tp/2+beam['tw']+20, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black",width=1)) # Nut

        # Weld (Fillet)
        ws = plate['weld_size']
        fig.add_shape(type="path", path=f"M 0 {-tp/2} L {ws} {-tp/2} L 0 {-tp/2-ws} Z", fillcolor="black", line_width=0)
        fig.add_shape(type="path", path=f"M 0 {tp/2} L {ws} {tp/2} L 0 {tp/2+ws} Z", fillcolor="black", line_width=0)

        add_leader(fig, wp, tp/2, "Fin Plate", ax=40, ay=-30)
        add_dim(fig, 0, 0, SETBACK, 0, f"{SETBACK}", -30, "h")

    # --- LOGIC: END PLATE ---
    elif conn_type == "End Plate":
        # Plate (Flat on Col)
        fig.add_shape(type="rect", x0=0, y0=-wp/2, x1=tp, y1=wp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        # Beam (Starts after Plate)
        fig.add_shape(type="rect", x0=tp, y0=-beam['b']/2, x1=tp+200, y1=beam['b']/2, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=STYLE['STEEL_FACE']['line'])
        
        # Bolt (Through Plate + Col Flange)
        g = 100 # Gauge
        for s in [-1, 1]:
            by = s * g / 2
            # Bolt Head (Right/Beam Side) & Nut (Left/Col Side)
            fig.add_shape(type="rect", x0=-20, y0=by-d/2, x1=tp+15, y1=by+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tp, y0=by-d, x1=tp+10, y1=by+d, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black",width=1)) # Head
        
        # Weld (Beam to Plate) - Web Weld
        ws = 6
        fig.add_shape(type="path", path=f"M {tp} {-beam['tw']/2} L {tp+ws} {-beam['tw']/2} L {tp} {-beam['tw']/2-ws} Z", fillcolor="black", line_width=0)

        add_leader(fig, tp, wp/2, "End Plate", ax=40, ay=-40)
        add_dim(fig, 0, -wp/2-20, tp, -wp/2-20, f"tp={tp}", -20, "h")

    # --- LOGIC: DOUBLE ANGLE ---
    elif conn_type == "Double Angle":
        # Beam Web (Center)
        fig.add_shape(type="rect", x0=SETBACK, y0=-beam['tw']/2, x1=SETBACK+wp+50, y1=beam['tw']/2, fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
        
        # Angles (L-Shape on both sides)
        ang_leg, ang_t = 75, tp
        for s in [-1, 1]:
            y_web = s * beam['tw']/2
            y_out = s * (beam['tw']/2 + ang_t)
            # Leg touching Web
            fig.add_shape(type="rect", x0=SETBACK, y0=y_web, x1=SETBACK+ang_leg, y1=y_out, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
            # Leg touching Col
            fig.add_shape(type="rect", x0=SETBACK, y0=y_web, x1=SETBACK+ang_t, y1=y_web + (s*100), fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
        
        # Bolt (Through Web)
        bx = SETBACK + plate['e1']
        full_thk = beam['tw'] + 2*ang_t
        fig.add_shape(type="rect", x0=bx-d/2, y0=-full_thk/2-10, x1=bx+d/2, y1=full_thk/2+10, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
        fig.add_shape(type="rect", x0=bx-d, y0=full_thk/2+10, x1=bx+d, y1=full_thk/2+18, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black", width=1))

        add_leader(fig, SETBACK, beam['tw']/2+ang_t, "2L-Angle", ax=40, ay=-40)
        add_dim(fig, 0, 0, SETBACK, 0, f"{SETBACK}", -30, "h")

    set_layout(fig, f"<b>PLAN VIEW</b> : {conn_type}", 250)
    return fig


# --- 3.2 FRONT VIEW (ELEVATION) ---
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    conn_type = plate.get('type', 'Fin Plate')
    
    h_b = beam['h']
    h_pl, w_pl = plate['h'], plate['w']
    lv, sv, rows = plate['lv'], bolts['s_v'], bolts['rows']
    
    # Auto Calc Height for Drawing
    req_h = lv + ((rows-1)*sv) + 1.5*bolts['d']
    draw_h = max(h_pl, req_h + 20)
    y_top, y_bot = draw_h/2, -draw_h/2

    # Ghost Beam & Col Line
    fig.add_shape(type="line", x0=0, y0=-h_b/2-50, x1=0, y1=h_b/2+50, line=dict(color="black", width=2))
    fig.add_shape(type="rect", x0=0, y0=-h_b/2, x1=w_pl+100, y1=h_b/2, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(color="gray", width=1, dash="dot"))

    # --- LOGIC SELECTION ---
    if conn_type == "End Plate":
        # Draw Plate Centered
        dw = max(beam['b'], w_pl)
        fig.add_shape(type="rect", x0=-dw/2, y0=y_bot, x1=dw/2, y1=y_top, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        # Bolts (2 Columns outside web)
        g = 100
        start_y = y_top - lv
        for s in [-1, 1]:
            bx = s * g / 2
            for r in range(rows):
                by = start_y - (r * sv)
                fig.add_shape(type="circle", x0=bx-bolts['d']/2, y0=by-bolts['d']/2, x1=bx+bolts['d']/2, y1=by+bolts['d']/2, fillcolor="white", line=dict(color="black", width=1))
        
        add_leader(fig, -dw/2, y_top, "End Plate", ax=-40, ay=-40)
        dim_x = dw/2 + 30

    else: # Fin Plate & Double Angle (Similar logic in Front View)
        # Shift start X for visual (Fin starts at 0, Angle also 0)
        style = STYLE['ANGLE'] if conn_type == "Double Angle" else STYLE['PLATE']
        fig.add_shape(type="rect", x0=0, y0=y_bot, x1=w_pl, y1=y_top, fillcolor=style['fillcolor'], line=style['line'])
        
        # Bolts Grid
        start_y = y_top - lv
        for c in range(bolts['cols']):
            cx = plate['e1'] + (c * bolts['s_h'])
            for r in range(rows):
                by = start_y - (r * sv)
                fig.add_shape(type="circle", x0=cx-bolts['d']/2, y0=by-bolts['d']/2, x1=cx+bolts['d']/2, y1=by+bolts['d']/2, fillcolor="white", line=dict(color="black", width=1))
        
        lbl = "Double Angle" if "Double" in conn_type else "Fin Plate"
        add_leader(fig, w_pl, y_top, lbl, ax=40, ay=-40)
        dim_x = w_pl + 30

    # Dims
    add_dim(fig, dim_x, y_top, dim_x, y_top-lv, f"{lv}", 10, "v")
    add_dim(fig, dim_x, y_top-lv, dim_x, y_top-lv-(rows-1)*sv, f"{rows-1}@{sv}", 10, "v")
    
    set_layout(fig, f"<b>ELEVATION VIEW</b> : {conn_type}", max(draw_h, h_b/2))
    return fig


# --- 3.3 SIDE VIEW (SECTION A-A) ---
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    conn_type = plate.get('type', 'Fin Plate')
    
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    draw_h = plate['h']
    tp, d = plate['t'], bolts['d']

    # Background Column (Hatched)
    col_w, col_h = b+50, h+100
    fig.add_shape(type="rect", x0=-col_w/2, y0=-col_h/2, x1=col_w/2, y1=col_h/2, line=dict(color="black", width=2))
    fig.add_trace(go.Scatter(x=[-col_w/2, col_w/2, col_w/2, -col_w/2], y=[-col_h/2, -col_h/2, col_h/2, col_h/2], 
                             fill='toself', fillpattern=dict(shape="/", size=10, solidity=0.2), mode='none', hoverinfo='skip'))

    y_start = draw_h/2 - plate['lv']
    
    # --- LOGIC: END PLATE ---
    if conn_type == "End Plate":
        # 1. End Plate (Side Cut)
        fig.add_shape(type="rect", x0=0, y0=-draw_h/2, x1=tp, y1=draw_h/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        # 2. Beam (Profile - Not Cut)
        fig.add_shape(type="line", x0=tp, y0=h/2, x1=tp+200, y1=h/2, line=dict(color="black", width=2)) # Top
        fig.add_shape(type="line", x0=tp, y0=-h/2, x1=tp+200, y1=-h/2, line=dict(color="black", width=2)) # Bot
        fig.add_shape(type="line", x0=tp, y0=0, x1=tp+200, y1=0, line=STYLE['CL']) # CL
        
        # 3. Bolts (Head on Plate side)
        for r in range(bolts['rows']):
            y = y_start - (r * bolts['s_v'])
            fig.add_shape(type="rect", x0=-15, y0=y-d/2, x1=tp+12, y1=y+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tp, y0=y-d, x1=tp+10, y1=y+d, fillcolor="black", line=dict(width=0)) # Head
        
        add_leader(fig, tp, draw_h/2, "End Plate (Side)", ax=40, ay=-40)

    # --- LOGIC: DOUBLE ANGLE ---
    elif conn_type == "Double Angle":
        # 1. Beam Cut
        draw_h_section(fig, 0, 0, h, b, tf, tw, STYLE['STEEL_CUT'], orient="I")
        # 2. Angles (Left & Right)
        fig.add_shape(type="rect", x0=-tw/2-tp, y0=-draw_h/2, x1=-tw/2, y1=draw_h/2, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
        fig.add_shape(type="rect", x0=tw/2, y0=-draw_h/2, x1=tw/2+tp, y1=draw_h/2, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
        # 3. Bolt
        for r in range(bolts['rows']):
            y = y_start - (r * bolts['s_v'])
            fig.add_shape(type="rect", x0=-tw/2-tp-15, y0=y-d/2, x1=tw/2+tp+15, y1=y+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tw/2+tp, y0=y-d, x1=tw/2+tp+10, y1=y+d, fillcolor="black", line=dict(width=0)) # Head
            fig.add_shape(type="rect", x0=-tw/2-tp-10, y0=y-d, x1=-tw/2-tp, y1=y+d, fillcolor="black", line=dict(width=0)) # Nut
        
        add_leader(fig, tw/2+tp, 0, "Double Angle", ax=40, ay=-40)

    # --- LOGIC: FIN PLATE ---
    else:
        # 1. Beam Cut
        draw_h_section(fig, 0, 0, h, b, tf, tw, STYLE['STEEL_CUT'], orient="I")
        # 2. Fin Plate
        fig.add_shape(type="rect", x0=tw/2, y0=-draw_h/2, x1=tw/2+tp, y1=draw_h/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        # 3. Bolt
        for r in range(bolts['rows']):
            y = y_start - (r * bolts['s_v'])
            fig.add_shape(type="rect", x0=-tw/2-15, y0=y-d/2, x1=tw/2+tp+15, y1=y+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tw/2+tp, y0=y-d, x1=tw/2+tp+10, y1=y+d, fillcolor="black", line=dict(width=0))
            fig.add_shape(type="rect", x0=-tw/2-10, y0=y-d, x1=-tw/2, y1=y+d, fillcolor="black", line=dict(width=0))
        
        add_leader(fig, tw/2+tp, 0, "Fin Plate", ax=40, ay=-40)

    set_layout(fig, f"<b>SECTION A-A</b> : {conn_type}", h)
    return fig

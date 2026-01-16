import plotly.graph_objects as go
import numpy as np

# =============================================================================
# 🏗️ ENGINEER'S STANDARD STYLES (Construction Grade)
# =============================================================================
STYLE = {
    # สีวัสดุ (เน้นความชัดเจนเมื่อพิมพ์ขาว-ดำ หรือดูในจอ)
    'STEEL_CUT':   dict(fillcolor="#D1D5DB", line=dict(color="black", width=2)),       # หน้าตัดเหล็ก (เทาเข้ม)
    'STEEL_FACE':  dict(fillcolor="#F3F4F6", line=dict(color="#6B7280", width=1)),     # ผิวเหล็ก (เทาจางๆ)
    'PLATE':       dict(fillcolor="#BFDBFE", line=dict(color="#1E3A8A", width=2)),     # Plate (ฟ้า) เน้นให้เด่น
    'BOLT':        dict(fillcolor="#374151", line=dict(color="black", width=1)),       # Bolt (สีตะกั่ว)
    'WASHER':      dict(fillcolor="#9CA3AF", line=dict(color="black", width=1)),       # Washer
    
    # เส้นบอกระยะและสัญลักษณ์
    'CL':          dict(color="#DC2626", width=1, dash="dashdot"),                     # Center Line (แดง)
    'DIM':         dict(color="#1D4ED8", family="Arial", size=11),                     # Dimension Text
    'LEADER':      dict(color="#000000", width=1.5),                                   # เส้นชี้บอก (Leader Line)
    'WELD':        dict(fillcolor="black", line=dict(width=0)),                        # สัญลักษณ์เชื่อม
    'ERROR':       dict(color="#EF4444", width=2, dash="dash")                         # เส้นเตือน Error
}

SETBACK = 15  # ระยะ Setback มาตรฐาน (mm)

# =============================================================================
# 🛠️ UTILITY FUNCTIONS (เครื่องมือวาด)
# =============================================================================
def add_dim(fig, x0, y0, x1, y1, text, offset=30, type="h", color=STYLE['DIM']['color'], is_err=False):
    """เขียนเส้นบอกระยะ Dimension Line"""
    col = "#EF4444" if is_err else color
    ext = 5 * np.sign(offset)
    
    if type == "h": # Horizontal Dim
        y_pos = y0 + offset
        # Extension Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos+ext, line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos+ext, line=dict(color=col, width=0.5))
        # Dim Line & Arrows
        fig.add_annotation(x=x0, y=y_pos, ax=x1, ay=y_pos, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=col, text="")
        fig.add_annotation(x=x1, y=y_pos, ax=x0, ay=y_pos, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=col, text="")
        # Text
        fig.add_annotation(x=(x0+x1)/2, y=y_pos+(10 if offset>0 else -15), text=f"<b>{text}</b>", 
                           showarrow=False, font=dict(size=11, color=col))
    else: # Vertical Dim
        x_pos = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos+ext, y1=y0, line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos+ext, y1=y1, line=dict(color=col, width=0.5))
        fig.add_annotation(x=x_pos, y=y0, ax=x_pos, ay=y1, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=col, text="")
        fig.add_annotation(x=x_pos, y=y1, ax=x_pos, ay=y0, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=col, text="")
        fig.add_annotation(x=x_pos+(15 if offset>0 else -15), y=(y0+y1)/2, text=f"<b>{text}</b>", 
                           showarrow=False, textangle=-90, font=dict(size=11, color=col))

def add_leader(fig, x, y, ax, ay, text, align="left"):
    """เขียนเส้นชี้บอกรายละเอียด (Leader Line)"""
    fig.add_annotation(x=x, y=y, ax=ax, ay=ay, xref="x", yref="y", axref="x", ayref="y",
                       text=f"<b>{text}</b>", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5,
                       font=dict(size=11, color="black"), align=align, bgcolor="rgba(255,255,255,0.7)")

def draw_h_beam_section(fig, x_cen, y_cen, h, b, tf, tw, style, orientation="I"):
    """วาดหน้าตัด H-Beam (ปรับปรุงเส้นขอบให้คม)"""
    if orientation == "I":
        # Flanges & Web (Filled)
        fig.add_shape(type="path", 
                      path=f"M {x_cen-tw/2} {y_cen-h/2+tf} L {x_cen-tw/2} {y_cen+h/2-tf} L {x_cen+tw/2} {y_cen+h/2-tf} L {x_cen+tw/2} {y_cen-h/2+tf} Z",
                      fillcolor=style['fillcolor'], line=dict(width=0)) # Web Fill
        fig.add_shape(type="rect", x0=x_cen-b/2, y0=y_cen+h/2-tf, x1=x_cen+b/2, y1=y_cen+h/2, 
                      fillcolor=style['fillcolor'], line=style['line']) # Top Flange
        fig.add_shape(type="rect", x0=x_cen-b/2, y0=y_cen-h/2, x1=x_cen+b/2, y1=y_cen-h/2+tf, 
                      fillcolor=style['fillcolor'], line=style['line']) # Bot Flange
        # Web Outline
        fig.add_shape(type="line", x0=x_cen-tw/2, y0=y_cen-h/2+tf, x1=x_cen-tw/2, y1=y_cen+h/2-tf, line=style['line'])
        fig.add_shape(type="line", x0=x_cen+tw/2, y0=y_cen-h/2+tf, x1=x_cen+tw/2, y1=y_cen+h/2-tf, line=style['line'])
    else: # H Shape (Top View Column)
        fig.add_shape(type="rect", x0=x_cen-h/2, y0=y_cen-b/2, x1=x_cen-h/2+tf, y1=y_cen+b/2,
                      fillcolor=style['fillcolor'], line=style['line']) # Left Flange
        fig.add_shape(type="rect", x0=x_cen+h/2-tf, y0=y_cen-b/2, x1=x_cen+h/2, y1=y_cen+b/2,
                      fillcolor=style['fillcolor'], line=style['line']) # Right Flange
        fig.add_shape(type="rect", x0=x_cen-h/2+tf, y0=y_cen-tw/2, x1=x_cen+h/2-tf, y1=y_cen+tw/2,
                      fillcolor=style['fillcolor'], line=dict(width=0)) # Web Fill
        fig.add_shape(type="line", x0=x_cen-h/2+tf, y0=y_cen-tw/2, x1=x_cen+h/2-tf, y1=y_cen-tw/2, line=style['line'])
        fig.add_shape(type="line", x0=x_cen-h/2+tf, y0=y_cen+tw/2, x1=x_cen+h/2-tf, y1=y_cen+tw/2, line=style['line'])

# =============================================================================
# 1. PLAN VIEW (TOP VIEW) - เพิ่มแนวเชื่อมและทิศทาง
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    
    # 1. Column Section (H-Shape)
    col_h, col_b = max(300, beam['b']+50), max(300, beam['b']+50)
    col_tf, col_tw = 16, 12
    draw_h_beam_section(fig, -col_h/2, 0, col_h, col_b, col_tf, col_tw, STYLE['STEEL_CUT'], orientation="H")
    
    # 2. Fin Plate
    tp, wp = plate['t'], plate['w']
    fig.add_shape(type="rect", x0=0, y0=-tp/2, x1=wp, y1=tp/2, 
                  fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
    
    # 3. Beam Web (Cut Section)
    beam_len = wp + 60
    tw = beam['tw']
    fig.add_shape(type="rect", x0=SETBACK, y0=tp/2, x1=beam_len, y1=tp/2+tw,
                  fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
    
    # 4. Bolt Assembly (ละเอียด: หัว, น็อต, แหวน)
    bolt_x = plate['e1']
    d = bolts['d']
    
    # Bolt Body
    y_head_out = -tp/2 - 8  # หัวอยู่ฝั่ง Plate
    y_nut_out = tp/2 + tw + 10 # น็อตอยู่ฝั่ง Web
    fig.add_shape(type="rect", x0=bolt_x-d/2, y0=y_head_out, x1=bolt_x+d/2, y1=y_nut_out,
                  fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
    # Head (Hex)
    fig.add_shape(type="rect", x0=bolt_x-d, y0=y_head_out-6, x1=bolt_x+d, y1=y_head_out,
                  fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black", width=1))
    # Nut (Hex)
    fig.add_shape(type="rect", x0=bolt_x-d, y0=y_nut_out, x1=bolt_x+d, y1=y_nut_out+10,
                  fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black", width=1))
    # Washers (สำคัญ!)
    fig.add_shape(type="rect", x0=bolt_x-d, y0=y_head_out, x1=bolt_x+d, y1=y_head_out+2, fillcolor="gray", line=dict(width=1))
    fig.add_shape(type="rect", x0=bolt_x-d, y0=y_nut_out-2, x1=bolt_x+d, y1=y_nut_out, fillcolor="gray", line=dict(width=1))
    # Thread Stick-out
    fig.add_shape(type="line", x0=bolt_x-d/2, y0=y_nut_out+10, x1=bolt_x-d/2, y1=y_nut_out+15, line=dict(color="black", width=0.5))
    fig.add_shape(type="line", x0=bolt_x+d/2, y0=y_nut_out+10, x1=bolt_x+d/2, y1=y_nut_out+15, line=dict(color="black", width=0.5))
    
    # Center Line
    fig.add_shape(type="line", x0=bolt_x, y0=-col_b/2, x1=bolt_x, y1=col_b/2, line=STYLE['CL'])

    # 5. Welding Detail (สำคัญมากสำหรับก่อสร้าง)
    ws = plate['weld_size']
    # Weld Triangle (Fillet)
    fig.add_shape(type="path", path=f"M 0 {-tp/2} L {ws} {-tp/2} L 0 {-tp/2-ws} Z", fillcolor="black", line_width=0)
    fig.add_shape(type="path", path=f"M 0 {tp/2} L {ws} {tp/2} L 0 {tp/2+ws} Z", fillcolor="black", line_width=0)
    # Weld Callout
    add_leader(fig, 0, -tp/2-ws, -40, -tp/2-40, f"Fillet Weld {ws}mm<br>(Shop Weld)", align="right")

    # 6. Dimensions & Annotations
    add_dim(fig, 0, -col_b/2-20, -col_h, -col_b/2-20, f"Col H={col_h}", 30, "h", color="gray")
    add_dim(fig, 0, tp/2+tw+40, bolt_x, tp/2+tw+40, f"e1={plate['e1']}", 20, "h")
    add_dim(fig, 0, 0, SETBACK, 0, f"Setback {SETBACK}", -30, "h")
    
    # Section Cut Indication
    fig.add_annotation(x=beam_len+20, y=0, text="<b>SEC A-A</b>", showarrow=False, textangle=0, font=dict(size=14, color="red"))
    fig.add_shape(type="line", x0=beam_len+10, y0=-50, x1=beam_len+10, y1=50, line=dict(color="red", width=2, dash="dashdot"))

    fig.update_layout(title="<b>PLAN VIEW</b> (Detailed Fabrication)", height=500, plot_bgcolor="white",
                      margin=dict(l=60, r=60, t=80, b=60),
                      xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

# =============================================================================
# 2. ELEVATION VIEW (PLATE DETAIL) - เหมือน Shop Drawing จริง
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    
    h_b = beam['h']
    h_pl_input, w_pl = plate['h'], plate['w']
    lv, sv, rows = plate['lv'], bolts['s_v'], bolts['rows']
    e1, cols, sh = plate['e1'], bolts['cols'], bolts['s_h']
    
    # Auto-Extend Logic (For visual correctness)
    min_edge = 1.5 * bolts['d']
    req_h = lv + ((rows-1)*sv) + min_edge
    is_short = h_pl_input < req_h
    draw_h_pl = req_h + 20 if is_short else h_pl_input
    y_top, y_bot = draw_h_pl/2, -draw_h_pl/2
    
    # 1. Column Ref
    fig.add_shape(type="line", x0=0, y0=-h_b/2-50, x1=0, y1=h_b/2+50, line=dict(color="black", width=2))
    
    # 2. Beam Ghost Line (บอกตำแหน่งคานให้รู้)
    fig.add_shape(type="rect", x0=SETBACK, y0=-h_b/2, x1=w_pl+100, y1=h_b/2, 
                  fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(color="gray", width=1, dash="dot"))
    fig.add_annotation(x=w_pl+50, y=h_b/2, text=f"Beam Top (+{h_b/2})", font=dict(size=10, color="gray"), showarrow=False, yanchor="bottom")

    # 3. Plate (Main Subject)
    fig.add_shape(type="rect", x0=0, y0=y_bot, x1=w_pl, y1=y_top, 
                  fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
    
    # Error Handling Visual
    if is_short:
        user_y_bot = y_top - h_pl_input
        fig.add_shape(type="line", x0=-10, y0=user_y_bot, x1=w_pl+10, y1=user_y_bot, line=STYLE['ERROR'])
        add_leader(fig, w_pl/2, user_y_bot, w_pl/2+50, user_y_bot-30, "Input Height too short!<br>Extend for edge dist.")

    # 4. Bolts Pattern
    start_y = y_top - lv
    bolt_count = 0
    for c in range(cols):
        cx = e1 + (c * sh)
        for r in range(rows):
            cy = start_y - (r * sv)
            # Bolt Hole Crosshair
            fig.add_shape(type="circle", x0=cx-bolts['d']/2, y0=cy-bolts['d']/2, x1=cx+bolts['d']/2, y1=cy+bolts['d']/2,
                          fillcolor="white", line=dict(color="black", width=1))
            fig.add_shape(type="line", x0=cx-bolts['d'], y0=cy, x1=cx+bolts['d'], y1=cy, line=dict(color="black", width=0.5))
            fig.add_shape(type="line", x0=cx, y0=cy-bolts['d'], x1=cx, y1=cy+bolts['d'], line=dict(color="black", width=0.5))
            bolt_count += 1
            
    # 5. Callouts (Construction Specs)
    # Plate Spec
    plate_desc = f"PL-{plate['t']}x{w_pl}x{h_pl_input} (SS400)"
    add_leader(fig, w_pl/2, y_top, w_pl/2+40, y_top+50, plate_desc)
    
    # Bolt Spec
    bolt_desc = f"{bolt_count}-M{bolts['d']} Bolts<br>(A325 / 8.8)"
    first_bolt_x, first_bolt_y = e1, start_y
    add_leader(fig, first_bolt_x, first_bolt_y, first_bolt_x-50, first_bolt_y+50, bolt_desc, align="right")

    # 6. Dimensions
    x_dim = w_pl + 30
    add_dim(fig, x_dim, y_top, x_dim, start_y, f"{lv}", 10, "v")
    if rows > 1:
        add_dim(fig, x_dim, start_y, x_dim, start_y-((rows-1)*sv), f"{rows-1}@{sv} = {(rows-1)*sv}", 10, "v")
    last_bolt_y = start_y - ((rows-1)*sv)
    add_dim(fig, x_dim, last_bolt_y, x_dim, y_bot, f"{(last_bolt_y - y_bot):.1f}", 10, "v")
    add_dim(fig, 0, y_bot-30, w_pl, y_bot-30, f"{w_pl}", -20, "h")
    
    fig.update_layout(title="<b>ELEVATION VIEW</b> (Connection Detail)", height=600, plot_bgcolor="white",
                      margin=dict(l=100, r=100, t=80, b=80),
                      xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

# =============================================================================
# 3. SECTION A-A (SIDE VIEW) - เห็นภาพการติดตั้งจริง
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl_input = plate['h']
    rows, sv, lv = bolts['rows'], bolts['s_v'], plate['lv']
    
    # Auto-Extend Logic (Sync with Front View)
    min_edge = 1.5 * bolts['d']
    req_h = lv + ((rows-1)*sv) + min_edge
    is_short = h_pl_input < req_h
    draw_h_pl = req_h + 20 if is_short else h_pl_input
    
    # 1. Column (Background)
    col_w = b + 50
    col_h = h + 150
    # Column Flange Face
    fig.add_shape(type="rect", x0=-col_w/2, y0=-col_h/2, x1=col_w/2, y1=col_h/2,
                  fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(color="black", width=2))
    # Hatching (แสดงผิววัสดุ)
    fig.add_trace(go.Scatter(x=[-col_w/2, col_w/2], y=[-col_h/2, col_h/2], 
                             mode='lines', line=dict(width=0), hoverinfo='skip',
                             fillpattern=dict(shape="/", size=10, solidity=0.2, fgcolor="#D1D5DB"), fill='toself'))

    # 2. Beam Section
    draw_h_beam_section(fig, 0, 0, h, b, tf, tw, STYLE['STEEL_CUT'], orientation="I")

    # 3. Plate (Side Cut)
    tp = plate['t']
    fig.add_shape(type="rect", x0=tw/2, y0=-draw_h_pl/2, x1=tw/2+tp, y1=draw_h_pl/2,
                  fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])

    # 4. Bolts (Side View - Assembly)
    y_start = (draw_h_pl/2) - lv
    d = bolts['d']
    
    for r in range(rows):
        y = y_start - (r * sv)
        
        # Center Line
        fig.add_shape(type="line", x0=-col_w/2, y0=y, x1=col_w/2, y1=y, line=STYLE['CL'])
        
        # Bolt Shank (Through Web & Plate)
        fig.add_shape(type="rect", x0=-tw/2-15, y0=y-d/2, x1=tw/2+tp+15, y1=y+d/2,
                      fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
        
        # Head (Left/Web side - or Right/Plate side depending on access. Standard: Plate side for fin plate)
        # Let's put Head on Plate side (Right), Nut on Web side (Left) like Plan View
        
        # Head (Right)
        fig.add_shape(type="rect", x0=tw/2+tp, y0=y-d, x1=tw/2+tp+10, y1=y+d, fillcolor="black", line=dict(width=0))
        fig.add_shape(type="rect", x0=tw/2+tp, y0=y-d, x1=tw/2+tp+2, y1=y+d, fillcolor="gray", line=dict(width=1)) # Washer
        
        # Nut (Left)
        fig.add_shape(type="rect", x0=-tw/2-12, y0=y-d, x1=-tw/2, y1=y+d, fillcolor="black", line=dict(width=0))
        fig.add_shape(type="rect", x0=-tw/2-2, y0=y-d, x1=-tw/2, y1=y+d, fillcolor="gray", line=dict(width=1)) # Washer
        
        # Thread Stickout
        fig.add_shape(type="line", x0=-tw/2-12, y0=y-d/2, x1=-tw/2-18, y1=y-d/2, line=dict(color="black", width=1))
        fig.add_shape(type="line", x0=-tw/2-12, y0=y+d/2, x1=-tw/2-18, y1=y+d/2, line=dict(color="black", width=1))

    # 5. Dimensions & Labels
    add_dim(fig, -b/2-40, h/2, -b/2-40, -h/2, f"Beam Depth {h}", 30, "v")
    add_dim(fig, b/2+40, draw_h_pl/2, b/2+40, -draw_h_pl/2, f"Plate H={draw_h_pl:.0f}", 30, "v")
    
    # Beam Label
    add_leader(fig, -tw/2, h/2-tf, -tw/2-60, h/2+40, f"Beam<br>H{h}x{b}x{tw}x{tf}")

    fig.update_layout(title="<b>SECTION A-A</b> (Assembly Detail)", height=600, plot_bgcolor="white",
                      margin=dict(l=100, r=100, t=80, b=80),
                      xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

# drawing_utils.py (V18 - Final Fix Consistency)
import plotly.graph_objects as go
import numpy as np

# =============================================================================
# 🎨 CAD STANDARD STYLES
# =============================================================================
STYLE = {
    'STEEL_CUT':   dict(fillcolor="#E5E7EB", line=dict(color="#1F2937", width=2)), 
    'STEEL_FACE':  dict(fillcolor="#F9FAFB", line=dict(color="#9CA3AF", width=1)), 
    'PLATE':       dict(fillcolor="#DBEAFE", line=dict(color="#1E40AF", width=2)), 
    'BOLT':        dict(fillcolor="#4B5563", line=dict(color="#111827", width=1.5)), 
    'WELD':        dict(fillcolor="#000000", line=dict(width=0)),
    'CL':          dict(color="#DC2626", width=1, dash="dashdot"),      
    'DIM':         dict(color="#1D4ED8", family="Sarabun", size=12),    
    'ERROR':       dict(color="#EF4444", width=2, dash="dash")          
}

SETBACK = 15 

# =============================================================================
# 🛠️ HELPER FUNCTIONS
# =============================================================================
def add_dim(fig, x0, y0, x1, y1, text, offset=30, type="h", color=STYLE['DIM']['color'], is_err=False):
    col = "#EF4444" if is_err else color
    ext = 5 * np.sign(offset)
    if type == "h": 
        y_pos = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos+ext, line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos+ext, line=dict(color=col, width=0.5))
        fig.add_annotation(x=x1, y=y_pos, ax=x0, ay=y_pos, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=col, text="")
        fig.add_annotation(x=(x0+x1)/2, y=y_pos+(10 if offset>0 else -15), text=f"<b>{text}</b>", 
                           showarrow=False, font=dict(size=11, color=col))
    else: 
        x_pos = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos+ext, y1=y0, line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos+ext, y1=y1, line=dict(color=col, width=0.5))
        fig.add_annotation(x=x_pos, y=y1, ax=x_pos, ay=y0, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=col, text="")
        fig.add_annotation(x=x_pos+(15 if offset>0 else -15), y=(y0+y1)/2, text=f"<b>{text}</b>", 
                           showarrow=False, textangle=-90, font=dict(size=11, color=col))

def draw_h_beam_section(fig, x_cen, y_cen, h, b, tf, tw, color_style, orientation="I"):
    if orientation == "I": 
        fig.add_shape(type="rect", x0=x_cen-tw/2, y0=y_cen-h/2+tf, x1=x_cen+tw/2, y1=y_cen+h/2-tf,
                      fillcolor=color_style['fillcolor'], line=dict(width=0))
        fig.add_shape(type="rect", x0=x_cen-b/2, y0=y_cen+h/2-tf, x1=x_cen+b/2, y1=y_cen+h/2,
                      fillcolor=color_style['fillcolor'], line=color_style['line'])
        fig.add_shape(type="rect", x0=x_cen-b/2, y0=y_cen-h/2, x1=x_cen+b/2, y1=y_cen-h/2+tf,
                      fillcolor=color_style['fillcolor'], line=color_style['line'])
        fig.add_shape(type="line", x0=x_cen-tw/2, y0=y_cen-h/2+tf, x1=x_cen-tw/2, y1=y_cen+h/2-tf, line=color_style['line'])
        fig.add_shape(type="line", x0=x_cen+tw/2, y0=y_cen-h/2+tf, x1=x_cen+tw/2, y1=y_cen+h/2-tf, line=color_style['line'])
    else: 
        fig.add_shape(type="rect", x0=x_cen-h/2+tf, y0=y_cen-tw/2, x1=x_cen+h/2-tf, y1=y_cen+tw/2,
                      fillcolor=color_style['fillcolor'], line=dict(width=0))
        fig.add_shape(type="rect", x0=x_cen-h/2, y0=y_cen-b/2, x1=x_cen-h/2+tf, y1=y_cen+b/2,
                      fillcolor=color_style['fillcolor'], line=color_style['line'])
        fig.add_shape(type="rect", x0=x_cen+h/2-tf, y0=y_cen-b/2, x1=x_cen+h/2, y1=y_cen+b/2,
                      fillcolor=color_style['fillcolor'], line=color_style['line'])
        fig.add_shape(type="line", x0=x_cen-h/2+tf, y0=y_cen-tw/2, x1=x_cen+h/2-tf, y1=y_cen-tw/2, line=color_style['line'])
        fig.add_shape(type="line", x0=x_cen-h/2+tf, y0=y_cen+tw/2, x1=x_cen+h/2-tf, y1=y_cen+tw/2, line=color_style['line'])

# =============================================================================
# 1. PLAN VIEW
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw = beam['tw']
    tp, wp, e1 = plate['t'], plate['w'], plate['e1']
    
    col_h, col_b = max(300, beam['b']+50), max(300, beam['b']+50)
    col_tf, col_tw = 14, 10
    draw_h_beam_section(fig, -col_h/2, 0, col_h, col_b, col_tf, col_tw, STYLE['STEEL_CUT'], orientation="H")
    
    fig.add_shape(type="rect", x0=0, y0=-tp/2, x1=wp, y1=tp/2, 
                  fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
    
    beam_len = wp + 50
    fig.add_shape(type="rect", x0=SETBACK, y0=tp/2, x1=beam_len, y1=tp/2+tw,
                  fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
    
    bolt_x = e1
    y_head = -tp/2 - 8
    y_nut = tp/2 + tw
    fig.add_shape(type="rect", x0=bolt_x-bolts['d']/2, y0=y_head, x1=bolt_x+bolts['d']/2, y1=y_nut,
                  fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
    fig.add_shape(type="rect", x0=bolt_x-bolts['d'], y0=y_head-10, x1=bolt_x+bolts['d'], y1=y_head,
                  fillcolor="black", line=dict(width=0)) 
    fig.add_shape(type="rect", x0=bolt_x-bolts['d'], y0=y_nut, x1=bolt_x+bolts['d'], y1=y_nut+12,
                  fillcolor="black", line=dict(width=0)) 
    fig.add_shape(type="line", x0=bolt_x, y0=y_head-20, x1=bolt_x, y1=y_nut+30, line=STYLE['CL'])

    ws = plate['weld_size']
    fig.add_shape(type="path", path=f"M 0 {-tp/2} L {ws} {-tp/2} L 0 {-tp/2-ws} Z", fillcolor="black", line_width=0)
    fig.add_shape(type="path", path=f"M 0 {tp/2} L {ws} {tp/2} L 0 {tp/2+ws} Z", fillcolor="black", line_width=0)

    add_dim(fig, 0, -col_b/2, -col_h, -col_b/2, f"Col={col_h}", 30, "h", color="gray")
    add_dim(fig, 0, -tp/2-50, wp, -tp/2-50, f"W_pl={wp}", 20, "h")
    add_dim(fig, 0, tp/2+tw+40, bolt_x, tp/2+tw+40, f"e1={e1}", 20, "h")
    add_dim(fig, 0, 0, SETBACK, 0, f"{SETBACK}", -30, "h")

    fig.update_layout(title="<b>PLAN VIEW</b> (Column & Connection)", height=450, plot_bgcolor="white",
                      margin=dict(l=50, r=50, t=80, b=50),
                      xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

# =============================================================================
# 2. ELEVATION VIEW
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    
    h_b = beam['h']
    h_pl_input, w_pl = plate['h'], plate['w']
    lv, sv, rows = plate['lv'], bolts['s_v'], bolts['rows']
    e1, cols, sh = plate['e1'], bolts['cols'], bolts['s_h']
    
    # --- AUTO-EXTEND LOGIC ---
    min_edge = 1.5 * bolts['d']
    req_h = lv + ((rows-1)*sv) + min_edge
    is_short = h_pl_input < req_h
    draw_h_pl = req_h + 20 if is_short else h_pl_input # ถ้าสั้นไป ยืดออก
    
    y_top, y_bot = draw_h_pl/2, -draw_h_pl/2
    
    fig.add_shape(type="line", x0=0, y0=-h_b/2-100, x1=0, y1=h_b/2+100, line=dict(color="black", width=3))
    fig.add_shape(type="rect", x0=SETBACK, y0=-h_b/2, x1=w_pl+150, y1=h_b/2, 
                  fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(color="#E5E7EB", width=1))
    fig.add_shape(type="rect", x0=0, y0=y_bot, x1=w_pl, y1=y_top, 
                  fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])

    if is_short:
        user_y_bot = y_top - h_pl_input
        fig.add_shape(type="line", x0=-10, y0=user_y_bot, x1=w_pl+10, y1=user_y_bot, line=STYLE['ERROR'])
        fig.add_annotation(x=w_pl/2, y=user_y_bot-10, text="User Input Limit", font=dict(color="red", size=10))

    start_y = y_top - lv # อ้างอิงจากขอบบนที่ถูกต้อง
    for c in range(cols):
        cx = e1 + (c * sh)
        for r in range(rows):
            cy = start_y - (r * sv)
            fig.add_shape(type="circle", x0=cx-bolts['d']/2, y0=cy-bolts['d']/2, x1=cx+bolts['d']/2, y1=cy+bolts['d']/2,
                          fillcolor="white", line=dict(color="#374151", width=1.5))
            fig.add_shape(type="line", x0=cx-5, y0=cy, x1=cx+5, y1=cy, line=dict(color="#374151", width=0.5))
            fig.add_shape(type="line", x0=cx, y0=cy-5, x1=cx, y1=cy+5, line=dict(color="#374151", width=0.5))

    x_dim = w_pl + 25
    add_dim(fig, x_dim, y_top, x_dim, start_y, f"Lv={lv}", 10, "v")
    if rows > 1:
        add_dim(fig, x_dim, start_y, x_dim, start_y-((rows-1)*sv), f"Pitch={sv}x{rows-1}", 10, "v")
    
    last_bolt_y = start_y - ((rows-1)*sv)
    add_dim(fig, x_dim, last_bolt_y, x_dim, y_bot, f"Lev={(last_bolt_y - y_bot):.1f}", 10, "v")

    if is_short:
        add_dim(fig, -30, y_top, -30, y_bot, f"Req H={draw_h_pl:.0f}", -20, "v", is_err=True)
    else:
        add_dim(fig, -30, y_top, -30, y_bot, f"H_pl={h_pl_input}", -20, "v")

    fig.update_layout(title="<b>ELEVATION VIEW</b> (Plate Geometry)", height=550, plot_bgcolor="white",
                      margin=dict(l=100, r=80, t=80, b=50),
                      xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

# =============================================================================
# 3. SECTION VIEW (FIXED)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl_input = plate['h'] # รับค่าดิบ
    rows, sv, lv = bolts['rows'], bolts['s_v'], plate['lv']
    
    # --- AUTO-EXTEND LOGIC (ใส่เพิ่มให้เหมือน Front View) ---
    min_edge = 1.5 * bolts['d']
    req_h = lv + ((rows-1)*sv) + min_edge
    is_short = h_pl_input < req_h
    draw_h_pl = req_h + 20 if is_short else h_pl_input # ใช้ค่าที่คำนวณใหม่
    
    # พื้นหลัง (เสา)
    col_w = b + 40
    col_h = h + 200
    fig.add_shape(type="rect", x0=-col_w/2, y0=-col_h/2, x1=col_w/2, y1=col_h/2,
                  fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(color="black", width=2))
    fig.add_trace(go.Scatter(x=[-col_w/2, col_w/2], y=[-col_h/2, col_h/2], 
                             mode='lines', line=dict(width=0), hoverinfo='skip',
                             fillpattern=dict(shape="/", size=10, solidity=0.1, fgcolor="#E5E7EB"), fill='toself'))

    # คาน
    draw_h_beam_section(fig, 0, 0, h, b, tf, tw, STYLE['STEEL_CUT'], orientation="I")

    # Plate (ใช้ draw_h_pl ที่คำนวณแล้ว)
    tp = plate['t']
    fig.add_shape(type="rect", x0=tw/2, y0=-draw_h_pl/2, x1=tw/2+tp, y1=draw_h_pl/2,
                  fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])

    # Bolts (คำนวณตำแหน่งอิงจากขอบบนใหม่: draw_h_pl/2)
    y_start = (draw_h_pl/2) - lv 
    
    for r in range(rows):
        y = y_start - (r * sv)
        fig.add_shape(type="line", x0=-col_w/2, y0=y, x1=col_w/2, y1=y, line=STYLE['CL'])
        fig.add_shape(type="rect", x0=-tw/2-10, y0=y-bolts['d']/2, x1=tw/2+tp, y1=y+bolts['d']/2,
                      fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
        fig.add_shape(type="rect", x0=tw/2+tp, y0=y-bolts['d']/2, x1=tw/2+tp+15, y1=y+bolts['d']/2, 
                      fillcolor="black", line=dict(width=0))

    # Dims
    add_dim(fig, -b/2-20, h/2, -b/2-20, -h/2, f"Beam={h}", 30, "v")
    
    # แสดง Dimension ตามความจริงที่วาด (ถ้า Auto-Extend ให้โชว์ค่าใหม่ หรือเตือน)
    if is_short:
         add_dim(fig, b/2+30, draw_h_pl/2, b/2+30, -draw_h_pl/2, f"Req H={draw_h_pl:.0f}", 30, "v", is_err=True)
    else:
         add_dim(fig, b/2+30, draw_h_pl/2, b/2+30, -draw_h_pl/2, f"Plate={h_pl_input}", 30, "v")

    fig.update_layout(title="<b>SECTION A-A</b> (Beam to Column Face)", height=550, plot_bgcolor="white",
                      margin=dict(l=80, r=80, t=80, b=80),
                      xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

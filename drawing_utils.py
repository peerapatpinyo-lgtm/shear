import plotly.graph_objects as go
import numpy as np

# =============================================================================
# 🏗️ ENGINEER'S STANDARD STYLES (คงเดิม 100%)
# =============================================================================
STYLE = {
    'STEEL_CUT':   dict(fillcolor="#D1D5DB", line=dict(color="black", width=2)),
    'STEEL_FACE':  dict(fillcolor="#F3F4F6", line=dict(color="#6B7280", width=1)),
    'PLATE':       dict(fillcolor="#BFDBFE", line=dict(color="#1E3A8A", width=2)),
    'ANGLE':       dict(fillcolor="#C7D2FE", line=dict(color="#312E81", width=2)),
    'BOLT':        dict(fillcolor="#374151", line=dict(color="black", width=1)),
    'WASHER':      dict(fillcolor="#9CA3AF", line=dict(color="black", width=1)),
    'CL':          dict(color="#DC2626", width=1, dash="dashdot"),
    'DIM':         dict(color="#1D4ED8", family="Arial", size=11),
    'LEADER':      dict(color="#000000", width=1.5),
    'ERROR':       dict(color="#EF4444", width=2, dash="dash")
}

SETBACK = 15

# =============================================================================
# 🛠️ UTILITY FUNCTIONS (แก้ระบบพิกัด เพื่อไม่ให้กราฟระเบิด)
# =============================================================================
def add_dim(fig, x0, y0, x1, y1, text, offset=30, type="h", color=STYLE['DIM']['color']):
    """
    เขียน Dimension แบบใช้ Pixel Shift เพื่อไม่ให้ดันกราฟ Zoom Out
    """
    col = color
    # คำนวณตำแหน่งเส้น Dim
    if type == "h": 
        y_pos = y0 + offset
        
        # 1. เส้นหลัก (Main Line)
        fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=col, width=1))
        
        # 2. เส้น Extension (ขาหยั่ง)
        ext_dir = np.sign(offset) if offset != 0 else 1
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos + (5*ext_dir), line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos + (5*ext_dir), line=dict(color=col, width=0.5))
        
        # 3. หัวลูกศร (ใช้ Annotation แปะที่ปลายเส้น)
        # ซ้าย
        fig.add_annotation(x=x0, y=y_pos, ax=15, ay=0, axref="pixel", ayref="pixel",
                           showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=col, text="")
        # ขวา
        fig.add_annotation(x=x1, y=y_pos, ax=-15, ay=0, axref="pixel", ayref="pixel",
                           showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=col, text="")
        
        # 4. ตัวหนังสือ (ใช้ yshift แทนการบวก y เพื่อไม่ให้กราฟขยาย)
        shift_val = 10 if offset > 0 else -15
        fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=f"<b>{text}</b>", 
                           showarrow=False, yshift=shift_val, font=dict(size=11, color=col))
                           
    else: # Vertical
        x_pos = x0 + offset
        ext_dir = np.sign(offset) if offset != 0 else 1
        
        # เส้นและขาหยั่ง
        fig.add_shape(type="line", x0=x_pos, y0=y0, x1=x_pos, y1=y1, line=dict(color=col, width=1))
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos + (5*ext_dir), y1=y0, line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos + (5*ext_dir), y1=y1, line=dict(color=col, width=0.5))
        
        # หัวลูกศร
        fig.add_annotation(x=x_pos, y=y0, ax=0, ay=15, axref="pixel", ayref="pixel",
                           showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=col, text="")
        fig.add_annotation(x=x_pos, y=y1, ax=0, ay=-15, axref="pixel", ayref="pixel",
                           showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=col, text="")
        
        # ตัวหนังสือ
        shift_val = 15 if offset > 0 else -15
        fig.add_annotation(x=x_pos, y=(y0+y1)/2, text=f"<b>{text}</b>", 
                           showarrow=False, xshift=shift_val, textangle=-90, font=dict(size=11, color=col))

def add_leader(fig, x, y, text, ax=40, ay=-40, align="left"):
    """
    เขียน Leader Line แบบล็อคระยะ Pixel (สำคัญมาก! แก้ปัญหารูปแตก)
    ax, ay: ระยะห่างเป็น Pixel (เช่น 40, -40) ไม่ใช่หน่วยกราฟ
    """
    fig.add_annotation(
        x=x, y=y,
        ax=ax, ay=ay, 
        axref="pixel", ayref="pixel",  # <--- ตัวแก้ปัญหา: ใช้ Pixel อ้างอิง
        text=f"<b>{text}</b>",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5,
        font=dict(size=11, color="black"),
        align=align,
        bgcolor="rgba(255,255,255,0.7)",
        borderpad=2
    )

def draw_h_beam_section(fig, x_cen, y_cen, h, b, tf, tw, style, orientation="I"):
    # ฟังก์ชันวาดรูป (คงเดิม)
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

def set_tight_layout(fig, title, max_size):
    """บังคับกล้องให้จับที่วัตถุ ไม่ใช่วิ่งตาม Text"""
    pad = max_size * 0.6
    fig.update_layout(
        title=dict(text=title, y=0.95),
        height=550,
        plot_bgcolor="white",
        margin=dict(l=50, r=50, t=80, b=50),
        # Fix Aspect Ratio & Range
        xaxis=dict(visible=False, range=[-pad, pad], scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False, range=[-pad, pad]),
        showlegend=False
    )

# =============================================================================
# 1. PLAN VIEW
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    conn_type = plate.get('type', 'Fin Plate')
    
    col_h, col_b = max(300, beam['b']+50), max(300, beam['b']+50)
    col_tf, col_tw = 16, 12
    draw_h_beam_section(fig, -col_h/2, 0, col_h, col_b, col_tf, col_tw, STYLE['STEEL_CUT'], orientation="H")
    
    tp, wp = plate['t'], plate['w']
    d = bolts['d']

    if "End Plate" in conn_type:
        fig.add_shape(type="rect", x0=0, y0=-wp/2, x1=tp, y1=wp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        beam_len = 200
        fig.add_shape(type="rect", x0=tp, y0=-beam['b']/2, x1=tp+beam_len, y1=beam['b']/2, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=STYLE['STEEL_FACE']['line'])
        g_bolt = 100 
        for sign in [-1, 1]:
            y_b = sign * g_bolt / 2
            fig.add_shape(type="rect", x0=-20, y0=y_b-d/2, x1=tp+15, y1=y_b+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tp, y0=y_b-d, x1=tp+10, y1=y_b+d, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black", width=1))
        
        # ใช้ ax=40, ay=40 (Pixel) แทนพิกัด
        add_leader(fig, tp, wp/2, "End Plate", ax=40, ay=-40)
        add_dim(fig, 0, -wp/2-20, tp, -wp/2-20, f"tp={tp}", -30, "h")

    elif "Double" in conn_type:
        beam_len = wp + 60
        fig.add_shape(type="rect", x0=SETBACK, y0=-beam['tw']/2, x1=beam_len, y1=beam['tw']/2, fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
        leg_web, leg_col, t_ang = wp, 100, tp
        for sign in [-1, 1]:
            y_web = sign * beam['tw']/2
            y_outer = sign * (beam['tw']/2 + t_ang)
            fig.add_shape(type="rect", x0=SETBACK, y0=y_web, x1=SETBACK+leg_web, y1=y_outer, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
            fig.add_shape(type="rect", x0=SETBACK, y0=y_web, x1=SETBACK+t_ang, y1=y_web + (sign*leg_col), fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])

        bx = SETBACK + plate['e1']
        full_thk = beam['tw'] + 2*t_ang
        fig.add_shape(type="rect", x0=bx-d/2, y0=-full_thk/2-10, x1=bx+d/2, y1=full_thk/2+10, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
        fig.add_shape(type="rect", x0=bx-d, y0=full_thk/2+10, x1=bx+d, y1=full_thk/2+18, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black", width=1))
        fig.add_shape(type="rect", x0=bx-d, y0=-full_thk/2-18, x1=bx+d, y1=-full_thk/2-10, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black", width=1))

        add_leader(fig, SETBACK, beam['tw']/2+t_ang, "2L-Angles", ax=40, ay=-50)

    else:
        # Fin Plate
        fig.add_shape(type="rect", x0=0, y0=-tp/2, x1=wp, y1=tp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        beam_len = wp + 60
        fig.add_shape(type="rect", x0=SETBACK, y0=tp/2, x1=beam_len, y1=tp/2+beam['tw'], fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
        bolt_x = plate['e1']
        y_head, y_nut = -tp/2 - 8, tp/2 + beam['tw'] + 10
        fig.add_shape(type="rect", x0=bolt_x-d/2, y0=y_head, x1=bolt_x+d/2, y1=y_nut, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
        fig.add_shape(type="rect", x0=bolt_x-d, y0=y_head-6, x1=bolt_x+d, y1=y_head, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black", width=1))
        fig.add_shape(type="rect", x0=bolt_x-d, y0=y_nut, x1=bolt_x+d, y1=y_nut+10, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black", width=1))
        
        ws = plate['weld_size']
        fig.add_shape(type="path", path=f"M 0 {-tp/2} L {ws} {-tp/2} L 0 {-tp/2-ws} Z", fillcolor="black", line_width=0)
        fig.add_shape(type="path", path=f"M 0 {tp/2} L {ws} {tp/2} L 0 {tp/2+ws} Z", fillcolor="black", line_width=0)
        
        # Leader & Dim Fix
        add_leader(fig, 0, -tp/2-ws, f"Weld {ws}", ax=-50, ay=30, align="right")
        add_dim(fig, 0, tp/2+beam['tw']+40, bolt_x, tp/2+beam['tw']+40, f"e1={plate['e1']}", 20, "h")
        add_leader(fig, wp, tp/2, "Fin Plate", ax=40, ay=-30)

    # Common
    if "Fin" in conn_type or "Double" in conn_type:
        add_dim(fig, 0, 0, SETBACK, 0, f"{SETBACK}", -30, "h")

    set_tight_layout(fig, "<b>PLAN VIEW</b>", max(col_b, 300))
    return fig

# =============================================================================
# 2. ELEVATION VIEW
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    conn_type = plate.get('type', 'Fin Plate')

    h_b = beam['h']
    h_pl, w_pl = plate['h'], plate['w']
    lv, sv, rows = plate['lv'], bolts['s_v'], bolts['rows']
    e1, cols, sh = plate['e1'], bolts['cols'], bolts['s_h']
    
    # Auto Scale Logic
    req_h = lv + ((rows-1)*sv) + (1.5*bolts['d'])
    draw_h = req_h + 20 if h_pl < req_h else h_pl
    y_top, y_bot = draw_h/2, -draw_h/2

    fig.add_shape(type="line", x0=0, y0=-h_b/2-50, x1=0, y1=h_b/2+50, line=dict(color="black", width=2)) # Col CL
    fig.add_shape(type="rect", x0=0, y0=-h_b/2, x1=w_pl+100, y1=h_b/2, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(color="gray", width=1, dash="dot")) # Beam

    if "End Plate" in conn_type:
        dw = max(beam['b'], w_pl)
        fig.add_shape(type="rect", x0=-dw/2, y0=y_bot, x1=dw/2, y1=y_top, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        g_bolt = 100
        start_y = y_top - lv
        for sign in [-1, 1]:
            bx = sign * g_bolt / 2
            for r in range(rows):
                by = start_y - (r * sv)
                fig.add_shape(type="circle", x0=bx-bolts['d']/2, y0=by-bolts['d']/2, x1=bx+bolts['d']/2, y1=by+bolts['d']/2, fillcolor="white", line=dict(color="black", width=1))
        
        add_leader(fig, -dw/2, y_top, "End Plate", ax=-40, ay=-40)
        add_dim(fig, -dw/2, y_bot-20, dw/2, y_bot-20, f"W={dw}", -20, "h")
        x_dim_ref = dw/2 + 30
    else:
        style = STYLE['ANGLE'] if "Double" in conn_type else STYLE['PLATE']
        fig.add_shape(type="rect", x0=0, y0=y_bot, x1=w_pl, y1=y_top, fillcolor=style['fillcolor'], line=style['line'])
        start_y = y_top - lv
        for c in range(cols):
            cx = e1 + (c * sh)
            for r in range(rows):
                cy = start_y - (r * sv)
                fig.add_shape(type="circle", x0=cx-bolts['d']/2, y0=cy-bolts['d']/2, x1=cx+bolts['d']/2, y1=cy+bolts['d']/2, fillcolor="white", line=dict(color="black", width=1))
        
        lbl = "Double Angle" if "Double" in conn_type else "Fin Plate"
        add_leader(fig, w_pl, y_top, lbl, ax=40, ay=-40)
        add_dim(fig, 0, y_bot-30, w_pl, y_bot-30, f"{w_pl}", -20, "h")
        x_dim_ref = w_pl + 30

    add_dim(fig, x_dim_ref, y_top, x_dim_ref, y_top-lv, f"{lv}", 10, "v")
    if rows > 1:
        add_dim(fig, x_dim_ref, y_top-lv, x_dim_ref, y_top-lv-((rows-1)*sv), f"s={sv}", 10, "v")

    set_tight_layout(fig, "<b>ELEVATION VIEW</b>", max(draw_h, 250))
    return fig

# =============================================================================
# 3. SECTION A-A
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    conn_type = plate.get('type', 'Fin Plate')
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl, tp, d = plate['h'], plate['t'], bolts['d']
    rows, sv, lv = bolts['rows'], bolts['s_v'], plate['lv']

    min_edge = 1.5 * d
    req_h = lv + ((rows-1)*sv) + min_edge
    draw_h_pl = req_h + 20 if h_pl < req_h else h_pl
    
    col_w, col_h = b + 50, h + 100
    fig.add_shape(type="rect", x0=-col_w/2, y0=-col_h/2, x1=col_w/2, y1=col_h/2, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(color="black", width=2))
    
    if "End Plate" in conn_type:
        fig.add_shape(type="rect", x0=0, y0=-draw_h_pl/2, x1=tp, y1=draw_h_pl/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        fig.add_shape(type="rect", x0=tp, y0=-h/2, x1=tp+200, y1=h/2, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(color="black", width=1))
        
        y_start = (draw_h_pl/2) - lv
        for r in range(rows):
            y = y_start - (r * sv)
            fig.add_shape(type="rect", x0=-20, y0=y-d/2, x1=tp+15, y1=y+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tp, y0=y-d, x1=tp+10, y1=y+d, fillcolor="black", line=dict(width=0))
        
        add_leader(fig, tp, draw_h_pl/2, "End Plate", ax=40, ay=-40)

    elif "Double" in conn_type:
        draw_h_beam_section(fig, 0, 0, h, b, tf, tw, STYLE['STEEL_CUT'], orientation="I")
        fig.add_shape(type="rect", x0=-tw/2-tp, y0=-draw_h_pl/2, x1=-tw/2, y1=draw_h_pl/2, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
        fig.add_shape(type="rect", x0=tw/2, y0=-draw_h_pl/2, x1=tw/2+tp, y1=draw_h_pl/2, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
        
        y_start = (draw_h_pl/2) - lv
        for r in range(rows):
            y = y_start - (r * sv)
            fig.add_shape(type="rect", x0=-tw/2-tp-15, y0=y-d/2, x1=tw/2+tp+15, y1=y+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tw/2+tp, y0=y-d, x1=tw/2+tp+10, y1=y+d, fillcolor="black", line=dict(width=0))
            fig.add_shape(type="rect", x0=-tw/2-tp-10, y0=y-d, x1=-tw/2-tp, y1=y+d, fillcolor="black", line=dict(width=0))

        add_leader(fig, tw/2+tp, 0, "Double Angle", ax=40, ay=-40)

    else:
        draw_h_beam_section(fig, 0, 0, h, b, tf, tw, STYLE['STEEL_CUT'], orientation="I")
        fig.add_shape(type="rect", x0=tw/2, y0=-draw_h_pl/2, x1=tw/2+tp, y1=draw_h_pl/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        y_start = (draw_h_pl/2) - lv
        for r in range(rows):
            y = y_start - (r * sv)
            fig.add_shape(type="line", x0=-col_w/2, y0=y, x1=col_w/2, y1=y, line=STYLE['CL'])
            fig.add_shape(type="rect", x0=-tw/2-15, y0=y-d/2, x1=tw/2+tp+15, y1=y+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tw/2+tp, y0=y-d, x1=tw/2+tp+10, y1=y+d, fillcolor="black", line=dict(width=0))
            fig.add_shape(type="rect", x0=-tw/2-12, y0=y-d, x1=-tw/2, y1=y+d, fillcolor="black", line=dict(width=0))

        add_leader(fig, tw/2+tp, 0, "Fin Plate", ax=40, ay=-40)

    set_tight_layout(fig, "<b>SECTION A-A</b>", max(h, 250))
    return fig

import plotly.graph_objects as go
import numpy as np

# =============================================================================
# 1. 🏗️ ENGINEERING STYLES & UTILS (เหมือนเดิม)
# =============================================================================
STYLE = {
    'STEEL_CUT':   dict(fillcolor="#D1D5DB", line=dict(color="black", width=2)),
    'STEEL_FACE':  dict(fillcolor="#F3F4F6", line=dict(color="#6B7280", width=1)),
    'PLATE':       dict(fillcolor="#BFDBFE", line=dict(color="#1E3A8A", width=2)),
    'ANGLE':       dict(fillcolor="#C7D2FE", line=dict(color="#312E81", width=2)),
    'BOLT':        dict(fillcolor="#374151", line=dict(color="black", width=1)),
    'CL':          dict(color="#DC2626", width=1, dash="dashdot"),
    'DIM':         dict(color="#1D4ED8", family="Arial", size=11),
}
SETBACK = 15

def add_dim(fig, x0, y0, x1, y1, text, offset=30, type="h"):
    col = STYLE['DIM']['color']
    if type == "h": 
        y_pos = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=col, width=1))
        dir = np.sign(offset) if offset != 0 else 1
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos+(5*dir), line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos+(5*dir), line=dict(color=col, width=0.5))
        fig.add_annotation(x=x0, y=y_pos, ax=15, ay=0, axref="pixel", ayref="pixel", arrowhead=2, arrowsize=1, arrowcolor=col, text="")
        fig.add_annotation(x=x1, y=y_pos, ax=-15, ay=0, axref="pixel", ayref="pixel", arrowhead=2, arrowsize=1, arrowcolor=col, text="")
        fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=f"<b>{text}</b>", showarrow=False, yshift=10*dir, font=dict(size=11, color=col))
    else:
        x_pos = x0 + offset
        dir = np.sign(offset) if offset != 0 else 1
        fig.add_shape(type="line", x0=x_pos, y0=y0, x1=x_pos, y1=y1, line=dict(color=col, width=1))
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos+(5*dir), y1=y0, line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos+(5*dir), y1=y1, line=dict(color=col, width=0.5))
        fig.add_annotation(x=x_pos, y=y0, ax=0, ay=15, axref="pixel", ayref="pixel", arrowhead=2, arrowsize=1, arrowcolor=col, text="")
        fig.add_annotation(x=x_pos, y=y1, ax=0, ay=-15, axref="pixel", ayref="pixel", arrowhead=2, arrowsize=1, arrowcolor=col, text="")
        fig.add_annotation(x=x_pos, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=15*dir, textangle=-90, font=dict(size=11, color=col))

def add_leader(fig, x, y, text, ax=40, ay=-40):
    fig.add_annotation(x=x, y=y, ax=ax, ay=ay, axref="pixel", ayref="pixel", text=f"<b>{text}</b>", showarrow=True, arrowhead=2, arrowsize=1, font=dict(size=11), bgcolor="rgba(255,255,255,0.8)")

def draw_h_section(fig, x, y, h, b, tf, tw, style, orient="I"):
    if orient == "I":
        fig.add_shape(type="path", path=f"M {x-tw/2} {y-h/2+tf} L {x-tw/2} {y+h/2-tf} L {x+tw/2} {y+h/2-tf} L {x+tw/2} {y-h/2+tf} Z", fillcolor=style['fillcolor'], line=dict(width=0))
        fig.add_shape(type="rect", x0=x-b/2, y0=y+h/2-tf, x1=x+b/2, y1=y+h/2, fillcolor=style['fillcolor'], line=style['line'])
        fig.add_shape(type="rect", x0=x-b/2, y0=y-h/2, x1=x+b/2, y1=y-h/2+tf, fillcolor=style['fillcolor'], line=style['line'])
        fig.add_shape(type="line", x0=x-tw/2, y0=y-h/2+tf, x1=x-tw/2, y1=y+h/2-tf, line=style['line'])
        fig.add_shape(type="line", x0=x+tw/2, y0=y-h/2+tf, x1=x+tw/2, y1=y+h/2-tf, line=style['line'])
    else: 
        fig.add_shape(type="rect", x0=x-h/2, y0=y-b/2, x1=x-h/2+tf, y1=y+b/2, fillcolor=style['fillcolor'], line=style['line'])
        fig.add_shape(type="rect", x0=x+h/2-tf, y0=y-b/2, x1=x+h/2, y1=y+b/2, fillcolor=style['fillcolor'], line=style['line'])
        fig.add_shape(type="rect", x0=x-h/2+tf, y0=y-tw/2, x1=x+h/2-tf, y1=y+tw/2, fillcolor=style['fillcolor'], line=dict(width=0))
        fig.add_shape(type="line", x0=x-h/2+tf, y0=y-tw/2, x1=x+h/2-tf, y1=y-tw/2, line=style['line'])
        fig.add_shape(type="line", x0=x-h/2+tf, y0=y+tw/2, x1=x+h/2-tf, y1=y+tw/2, line=style['line'])

def set_layout(fig, title, h_limit):
    pad = h_limit * 0.7
    fig.update_layout(title=dict(text=title, y=0.95, x=0.5, xanchor='center'), height=500, margin=dict(l=40, r=40, t=60, b=40), plot_bgcolor="white", xaxis=dict(visible=False, range=[-pad, pad], scaleanchor="y", scaleratio=1), yaxis=dict(visible=False, range=[-pad, pad]), showlegend=False)

# =============================================================================
# 2. VIEW 1: FRONT VIEW (ELEVATION)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    ctype = plate.get('type', 'Fin Plate')
    
    # Beam & Plate Dimensions
    hb, bb = beam['h'], beam['b']
    hp, wp = plate['h'], plate['w']
    tp = plate['t']
    
    # Draw Reference Lines
    fig.add_shape(type="line", x0=0, y0=-hb/2-50, x1=0, y1=hb/2+50, line=dict(color="black", width=2)) # CL Column
    
    # --- LOGIC SWITCH ---
    if ctype == "End Plate":
        # End Plate: วาด Plate เต็มหน้ากว้างกว่า Beam
        draw_w = max(bb, wp)
        fig.add_shape(type="rect", x0=-draw_w/2, y0=-hp/2, x1=draw_w/2, y1=hp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        
        # Bolts: อยู่ซ้ายขวาของ Web (Standard Gauge)
        g = 100 # Default Gauge
        for s in [-1, 1]:
            bx = s * g / 2
            start_y = (hp/2) - plate['lv']
            for r in range(bolts['rows']):
                by = start_y - (r * bolts['s_v'])
                fig.add_shape(type="circle", x0=bx-bolts['d']/2, y0=by-bolts['d']/2, x1=bx+bolts['d']/2, y1=by+bolts['d']/2, fillcolor="white", line=dict(color="black", width=1))
        
        add_leader(fig, -draw_w/2, hp/2, "End Plate", ax=-40, ay=-40)
        dim_ref_x = draw_w/2 + 20

    elif ctype == "Double Angle":
        # Double Angle: หน้าตาเหมือน Plate สองอันประกบ แต่ใน Front View เห็นเป็นสี่เหลี่ยมผืนผ้า
        fig.add_shape(type="rect", x0=0, y0=-hp/2, x1=wp, y1=hp/2, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
        # Bolts
        start_y = (hp/2) - plate['lv']
        for r in range(bolts['rows']):
            by = start_y - (r * bolts['s_v'])
            bx = plate['e1']
            fig.add_shape(type="circle", x0=bx-bolts['d']/2, y0=by-bolts['d']/2, x1=bx+bolts['d']/2, y1=by+bolts['d']/2, fillcolor="white", line=dict(color="black", width=1))
        
        add_leader(fig, wp, hp/2, "2L-Angle", ax=40, ay=-40)
        dim_ref_x = wp + 20

    else: # Fin Plate
        fig.add_shape(type="rect", x0=0, y0=-hp/2, x1=wp, y1=hp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        # Bolts
        start_y = (hp/2) - plate['lv']
        for c in range(bolts['cols']):
            bx = plate['e1'] + (c * bolts['s_h'])
            for r in range(bolts['rows']):
                by = start_y - (r * bolts['s_v'])
                fig.add_shape(type="circle", x0=bx-bolts['d']/2, y0=by-bolts['d']/2, x1=bx+bolts['d']/2, y1=by+bolts['d']/2, fillcolor="white", line=dict(color="black", width=1))
        
        add_leader(fig, wp, hp/2, "Fin Plate", ax=40, ay=-40)
        dim_ref_x = wp + 20

    # Common Dims
    add_dim(fig, dim_ref_x, hp/2, dim_ref_x, hp/2-plate['lv'], f"{plate['lv']}", 10, "v")
    if bolts['rows'] > 1:
        add_dim(fig, dim_ref_x, hp/2-plate['lv'], dim_ref_x, hp/2-plate['lv']-(bolts['rows']-1)*bolts['s_v'], f"{bolts['rows']-1}@{bolts['s_v']}", 10, "v")

    set_layout(fig, f"<b>FRONT VIEW</b> ({ctype})", max(hb, hp))
    return fig

# =============================================================================
# 3. VIEW 2: SIDE VIEW (SECTION A-A)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    ctype = plate.get('type', 'Fin Plate')
    
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    hp, tp = plate['h'], plate['t']
    d = bolts['d']

    # Draw Column Background
    col_w, col_h = b+50, h+100
    fig.add_shape(type="rect", x0=-col_w/2, y0=-col_h/2, x1=col_w/2, y1=col_h/2, line=dict(color="black", width=2))
    
    # --- LOGIC SWITCH ---
    if ctype == "End Plate":
        # End Plate: เห็น Plate เป็นแท่งบางๆ แปะ Column + Beam ยื่นออกไป
        # 1. Plate
        fig.add_shape(type="rect", x0=0, y0=-hp/2, x1=tp, y1=hp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        # 2. Beam (Profile Side View - ไม่ใช่ Cut Section)
        fig.add_shape(type="rect", x0=tp, y0=-h/2, x1=tp+200, y1=h/2, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(width=0))
        fig.add_shape(type="line", x0=tp, y0=h/2, x1=tp+200, y1=h/2, line=dict(color="black", width=2))
        fig.add_shape(type="line", x0=tp, y0=-h/2, x1=tp+200, y1=-h/2, line=dict(color="black", width=2))
        fig.add_shape(type="line", x0=tp, y0=h/2-tf, x1=tp+200, y1=h/2-tf, line=dict(color="gray", width=1))
        fig.add_shape(type="line", x0=tp, y0=-h/2+tf, x1=tp+200, y1=-h/2+tf, line=dict(color="gray", width=1))
        
        # 3. Bolts (Head visible)
        start_y = hp/2 - plate['lv']
        for r in range(bolts['rows']):
            y = start_y - (r * bolts['s_v'])
            fig.add_shape(type="rect", x0=-15, y0=y-d/2, x1=tp+12, y1=y+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tp, y0=y-d, x1=tp+10, y1=y+d, fillcolor="black", line=dict(width=0)) # Head

        add_leader(fig, tp, hp/2, "End Plate", ax=40, ay=-40)

    elif ctype == "Double Angle":
        # Double Angle: เห็น Beam Cut Section ตรงกลาง + Angle ขนาบข้าง
        draw_h_section(fig, 0, 0, h, b, tf, tw, STYLE['STEEL_CUT'], "I")
        
        # Left Angle
        fig.add_shape(type="rect", x0=-tw/2-tp, y0=-hp/2, x1=-tw/2, y1=hp/2, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
        # Right Angle
        fig.add_shape(type="rect", x0=tw/2, y0=-hp/2, x1=tw/2+tp, y1=hp/2, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
        
        # Bolts through everything
        start_y = hp/2 - plate['lv']
        for r in range(bolts['rows']):
            y = start_y - (r * bolts['s_v'])
            fig.add_shape(type="rect", x0=-tw/2-tp-15, y0=y-d/2, x1=tw/2+tp+15, y1=y+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tw/2+tp, y0=y-d, x1=tw/2+tp+10, y1=y+d, fillcolor="black", line=dict(width=0)) # Head
            fig.add_shape(type="rect", x0=-tw/2-tp-10, y0=y-d, x1=-tw/2-tp, y1=y+d, fillcolor="black", line=dict(width=0)) # Nut
            
        add_leader(fig, tw/2+tp, 0, "Double Angle", ax=40, ay=-40)

    else: # Fin Plate
        # Fin Plate: เห็น Beam Cut Section ตรงกลาง + Plate เสียบตรงกลาง
        draw_h_section(fig, 0, 0, h, b, tf, tw, STYLE['STEEL_CUT'], "I")
        
        # Plate (เชื่อมติดเสา) - ต้องวาด Plate ก่อน Beam จะได้ไม่ทับเส้น
        fig.add_shape(type="rect", x0=tw/2, y0=-hp/2, x1=tw/2+tp, y1=hp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        
        # Bolts
        start_y = hp/2 - plate['lv']
        for r in range(bolts['rows']):
            y = start_y - (r * bolts['s_v'])
            fig.add_shape(type="rect", x0=-tw/2-15, y0=y-d/2, x1=tw/2+tp+15, y1=y+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tw/2+tp, y0=y-d, x1=tw/2+tp+10, y1=y+d, fillcolor="black", line=dict(width=0))
            fig.add_shape(type="rect", x0=-tw/2-10, y0=y-d, x1=-tw/2, y1=y+d, fillcolor="black", line=dict(width=0))

        add_leader(fig, tw/2+tp, 0, "Fin Plate", ax=40, ay=-40)

    set_layout(fig, f"<b>SIDE VIEW</b> ({ctype})", h)
    return fig

# =============================================================================
# 4. VIEW 3: PLAN VIEW (TOP VIEW)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    ctype = plate.get('type', 'Fin Plate')
    
    col_h, col_b = max(300, beam['b']+50), max(300, beam['b']+50)
    draw_h_section(fig, -col_h/2, 0, col_h, col_b, 16, 12, STYLE['STEEL_CUT'], "H")
    
    tp, wp, d = plate['t'], plate['w'], bolts['d']

    # --- LOGIC SWITCH ---
    if ctype == "End Plate":
        # End Plate: เห็น Plate แปะหน้าเสา + Beam ยื่นออกมา
        fig.add_shape(type="rect", x0=0, y0=-wp/2, x1=tp, y1=wp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        fig.add_shape(type="rect", x0=tp, y0=-beam['b']/2, x1=tp+200, y1=beam['b']/2, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=STYLE['STEEL_FACE']['line'])
        
        # Bolts (เจาะผ่าน Plate เข้าปีกเสา)
        g = 100
        for s in [-1, 1]:
            y_bolt = s * g / 2
            fig.add_shape(type="rect", x0=-20, y0=y_bolt-d/2, x1=tp+15, y1=y_bolt+d/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tp, y0=y_bolt-d, x1=tp+10, y1=y_bolt+d, fillcolor="black", line=dict(width=0))

        # Weld (เชื่อมเอวคานกับ Plate)
        ws = 6
        fig.add_shape(type="path", path=f"M {tp} {-beam['tw']/2} L {tp+ws} {-beam['tw']/2} L {tp} {-beam['tw']/2-ws} Z", fillcolor="black", line_width=0)
        fig.add_shape(type="path", path=f"M {tp} {beam['tw']/2} L {tp+ws} {beam['tw']/2} L {tp} {beam['tw']/2+ws} Z", fillcolor="black", line_width=0)

        add_leader(fig, tp, wp/2, "End Plate", ax=40, ay=-40)
        add_dim(fig, 0, -wp/2-20, tp, -wp/2-20, f"t={tp}", -20, "h")

    elif ctype == "Double Angle":
        # Double Angle: เห็นเหล็กฉากตัว L สองตัวหนีบ Web
        # Beam Web
        fig.add_shape(type="rect", x0=SETBACK, y0=-beam['tw']/2, x1=SETBACK+wp+50, y1=beam['tw']/2, fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
        
        angle_leg = 75
        for s in [-1, 1]:
            # ขาที่แปะ Web
            y_inner = s * beam['tw']/2
            y_outer = s * (beam['tw']/2 + tp)
            fig.add_shape(type="rect", x0=SETBACK, y0=y_inner, x1=SETBACK+angle_leg, y1=y_outer, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
            # ขาที่แปะเสา (ยื่นออกไปทาง y)
            y_far = s * (beam['tw']/2 + 100) # สมมติขาฉากยาว 100
            fig.add_shape(type="rect", x0=SETBACK, y0=y_inner, x1=SETBACK+tp, y1=y_far, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
        
        # Bolt ผ่าน Web
        bx = SETBACK + plate['e1']
        full_t = beam['tw'] + 2*tp
        fig.add_shape(type="rect", x0=bx-d/2, y0=-full_t/2-10, x1=bx+d/2, y1=full_t/2+10, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
        fig.add_shape(type="rect", x0=bx-d, y0=full_t/2+10, x1=bx+d, y1=full_t/2+18, fillcolor="black", line=dict(width=0))
        
        add_leader(fig, SETBACK, beam['tw']/2+tp, "2L-Angle", ax=40, ay=-40)
        add_dim(fig, 0, 0, SETBACK, 0, f"{SETBACK}", -30, "h")

    else: # Fin Plate
        # Fin Plate: Plate ยื่นออกมา + Beam Web ประกบ
        fig.add_shape(type="rect", x0=0, y0=-tp/2, x1=wp, y1=tp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        fig.add_shape(type="rect", x0=SETBACK, y0=tp/2, x1=wp+100, y1=tp/2+beam['tw'], fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
        
        # Bolt
        bx = plate['e1']
        fig.add_shape(type="rect", x0=bx-d/2, y0=-tp/2-10, x1=bx+d/2, y1=tp/2+beam['tw']+12, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
        fig.add_shape(type="rect", x0=bx-d, y0=-tp/2-18, x1=bx+d, y1=-tp/2-10, fillcolor="black", line=dict(width=0))
        fig.add_shape(type="rect", x0=bx-d, y0=tp/2+beam['tw']+12, x1=bx+d, y1=tp/2+beam['tw']+20, fillcolor="black", line=dict(width=0))

        # Weld
        ws = plate['weld_size']
        fig.add_shape(type="path", path=f"M 0 {-tp/2} L {ws} {-tp/2} L 0 {-tp/2-ws} Z", fillcolor="black", line_width=0)
        fig.add_shape(type="path", path=f"M 0 {tp/2} L {ws} {tp/2} L 0 {tp/2+ws} Z", fillcolor="black", line_width=0)
        
        add_leader(fig, wp, tp/2, "Fin Plate", ax=40, ay=-30)
        add_dim(fig, 0, 0, SETBACK, 0, f"{SETBACK}", -30, "h")

    set_layout(fig, f"<b>PLAN VIEW</b> ({ctype})", 250)
    return fig

# =============================================================================
# 🚀 TEST ZONE (วิธีใช้งาน)
# =============================================================================

# 1. ข้อมูล Beam & Bolts พื้นฐาน
beam_data = {'h': 400, 'b': 200, 'tf': 13, 'tw': 8}
bolt_data = {'d': 20, 'rows': 3, 'cols': 1, 's_v': 70, 's_h': 0}

# 2. เลือก Type ที่ต้องการสร้าง (Comment/Uncomment เพื่อเลือก)

# --- Case A: Fin Plate ---
plate_data = {'type': 'Fin Plate', 'h': 280, 'w': 100, 't': 10, 'lv': 40, 'e1': 50, 'weld_size': 6}

# --- Case B: End Plate (Uncomment บรรทัดล่างเพื่อใช้) ---
# plate_data = {'type': 'End Plate', 'h': 500, 'w': 200, 't': 16, 'lv': 50, 'e1': 0, 'weld_size': 8}

# --- Case C: Double Angle (Uncomment บรรทัดล่างเพื่อใช้) ---
# plate_data = {'type': 'Double Angle', 'h': 250, 'w': 150, 't': 10, 'lv': 40, 'e1': 50, 'weld_size': 0}


# 3. สร้างรูป (Run 3 บรรทัดนี้จะได้รูปครบเลย)
fig1 = create_front_view(beam_data, plate_data, bolt_data)
fig2 = create_side_view(beam_data, plate_data, bolt_data)
fig3 = create_plan_view(beam_data, plate_data, bolt_data)

fig1.show()
fig2.show()
fig3.show()

import plotly.graph_objects as go
import numpy as np

# =============================================================================
# 1. 🏗️ ENGINEERING STYLES
# =============================================================================
STYLE = {
    'STEEL_CUT':   dict(fillcolor="#D1D5DB", line=dict(color="black", width=2)), # หน้าตัด (เทาเข้ม)
    'STEEL_FACE':  dict(fillcolor="#F3F4F6", line=dict(color="#6B7280", width=1)), # ผิวเห็น (เทาอ่อน)
    'PLATE':       dict(fillcolor="#BFDBFE", line=dict(color="#1E3A8A", width=2)), # Plate (ฟ้า)
    'ANGLE':       dict(fillcolor="#C7D2FE", line=dict(color="#312E81", width=2)), # Angle (ม่วง)
    'BOLT':        dict(fillcolor="#374151", line=dict(color="black", width=1)), # Bolt (เทาดำ)
    'CL':          dict(color="#DC2626", width=1, dash="dashdot"), # Center Line (แดง)
    'DIM':         dict(color="#1D4ED8", family="Arial", size=11), # Dimension (น้ำเงิน)
}

# =============================================================================
# 2. 🛠️ HELPER FUNCTIONS (Smart Scaling)
# =============================================================================

def add_dim(fig, x0, y0, x1, y1, text, offset=30, type="h"):
    """เขียน Dimension แบบยึดพิกัดแม่นยำ (Fix Scale Issue)"""
    c = STYLE['DIM']['color']
    
    if type == "h": 
        y_pos = y0 + offset
        # เส้นหลัก
        fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=c, width=1))
        # ขาหยั่ง
        dir = 1 if offset >= 0 else -1
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos+(5*dir), line=dict(color=c, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos+(5*dir), line=dict(color=c, width=0.5))
        # ลูกศร & ข้อความ
        fig.add_annotation(x=x0, y=y_pos, ax=15, ay=0, axref="pixel", ayref="pixel", arrowhead=2, arrowsize=1, arrowcolor=c, text="")
        fig.add_annotation(x=x1, y=y_pos, ax=-15, ay=0, axref="pixel", ayref="pixel", arrowhead=2, arrowsize=1, arrowcolor=c, text="")
        fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=f"<b>{text}</b>", showarrow=False, yshift=10*dir, font=dict(size=11, color=c))

    else: # Vertical
        x_pos = x0 + offset
        dir = 1 if offset >= 0 else -1
        # เส้นหลัก
        fig.add_shape(type="line", x0=x_pos, y0=y0, x1=x_pos, y1=y1, line=dict(color=c, width=1))
        # ขาหยั่ง
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos+(5*dir), y1=y0, line=dict(color=c, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos+(5*dir), y1=y1, line=dict(color=c, width=0.5))
        # ลูกศร & ข้อความ
        fig.add_annotation(x=x_pos, y=y0, ax=0, ay=15, axref="pixel", ayref="pixel", arrowhead=2, arrowsize=1, arrowcolor=c, text="")
        fig.add_annotation(x=x_pos, y=y1, ax=0, ay=-15, axref="pixel", ayref="pixel", arrowhead=2, arrowsize=1, arrowcolor=c, text="")
        fig.add_annotation(x=x_pos, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=15*dir, textangle=-90, font=dict(size=11, color=c))

def add_leader(fig, x, y, text, ax=40, ay=-40):
    fig.add_annotation(
        x=x, y=y, ax=ax, ay=ay, axref="pixel", ayref="pixel",
        text=f"<b>{text}</b>", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5,
        font=dict(size=11, color="black"), bgcolor="rgba(255,255,255,0.8)", bordercolor="black", borderwidth=1
    )

def draw_h_section(fig, x, y, h, b, tf, tw, style, orient="I"):
    """วาดหน้าตัดเหล็ก H-Beam/I-Beam"""
    if orient == "I":
        # Web Polygon
        fig.add_shape(type="path", path=f"M {x-tw/2} {y-h/2+tf} L {x-tw/2} {y+h/2-tf} L {x+tw/2} {y+h/2-tf} L {x+tw/2} {y-h/2+tf} Z", fillcolor=style['fillcolor'], line=dict(width=0))
        # Flanges
        fig.add_shape(type="rect", x0=x-b/2, y0=y+h/2-tf, x1=x+b/2, y1=y+h/2, fillcolor=style['fillcolor'], line=style['line']) # Top
        fig.add_shape(type="rect", x0=x-b/2, y0=y-h/2, x1=x+b/2, y1=y-h/2+tf, fillcolor=style['fillcolor'], line=style['line']) # Bot
        # Web Lines
        fig.add_shape(type="line", x0=x-tw/2, y0=y-h/2+tf, x1=x-tw/2, y1=y+h/2-tf, line=style['line'])
        fig.add_shape(type="line", x0=x+tw/2, y0=y-h/2+tf, x1=x+tw/2, y1=y+h/2-tf, line=style['line'])
    else: # H Shape
        fig.add_shape(type="rect", x0=x-h/2, y0=y-b/2, x1=x-h/2+tf, y1=y+b/2, fillcolor=style['fillcolor'], line=style['line'])
        fig.add_shape(type="rect", x0=x+h/2-tf, y0=y-b/2, x1=x+h/2, y1=y+b/2, fillcolor=style['fillcolor'], line=style['line'])
        fig.add_shape(type="rect", x0=x-h/2+tf, y0=y-tw/2, x1=x+h/2-tf, y1=y+tw/2, fillcolor=style['fillcolor'], line=dict(width=0))
        fig.add_shape(type="line", x0=x-h/2+tf, y0=y-tw/2, x1=x+h/2-tf, y1=y-tw/2, line=style['line'])
        fig.add_shape(type="line", x0=x-h/2+tf, y0=y+tw/2, x1=x+h/2-tf, y1=y+tw/2, line=style['line'])

def force_range(fig, x_range, y_range):
    """**หัวใจสำคัญ** : บังคับ Scale ไม่ให้กราฟระเบิด"""
    fig.update_layout(
        xaxis=dict(range=x_range, visible=False, scaleanchor="y", scaleratio=1, fixedrange=True),
        yaxis=dict(range=y_range, visible=False, fixedrange=True),
        height=500, margin=dict(l=20, r=20, t=50, b=20),
        plot_bgcolor="white", showlegend=False
    )

# =============================================================================
# 3. VIEW GENERATORS (FRONT, SIDE, PLAN)
# =============================================================================

# --- 3.1 FRONT VIEW (รูปด้านหน้า) ---
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    ctype = plate.get('type', 'Fin Plate')
    
    h, b = beam['h'], beam['b']
    hp, wp = plate['h'], plate['w']
    
    # เส้น Center เสา
    fig.add_shape(type="line", x0=0, y0=-h/2-50, x1=0, y1=h/2+50, line=dict(color="black", width=2, dash="dash"))
    
    # --- LOGIC SELECTION ---
    if ctype == "End Plate":
        # End Plate: สี่เหลี่ยมบังหน้าตัดคาน
        draw_w = max(b, wp) # Plate มักจะกว้างพอๆ กับคาน
        fig.add_shape(type="rect", x0=-draw_w/2, y0=-hp/2, x1=draw_w/2, y1=hp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        
        # Bolts (แยกซ้ายขวา Web)
        gauge = 100 
        for s in [-1, 1]:
            bx = s * gauge / 2
            start_y = hp/2 - plate['lv']
            for r in range(bolts['rows']):
                by = start_y - (r * bolts['s_v'])
                fig.add_shape(type="circle", x0=bx-bolts['d']/2, y0=by-bolts['d']/2, x1=bx+bolts['d']/2, y1=by+bolts['d']/2, fillcolor="white", line=dict(color="black", width=1))
        
        add_leader(fig, -draw_w/2, hp/2, "End Plate", ax=-40, ay=-40)
        dim_x = draw_w/2 + 20

    elif ctype == "Double Angle":
        # Double Angle: เหมือน Fin Plate แต่เป็นเหล็กฉาก
        fig.add_shape(type="rect", x0=0, y0=-hp/2, x1=wp, y1=hp/2, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
        start_y = hp/2 - plate['lv']
        for r in range(bolts['rows']):
            by = start_y - (r * bolts['s_v'])
            bx = plate['e1']
            fig.add_shape(type="circle", x0=bx-bolts['d']/2, y0=by-bolts['d']/2, x1=bx+bolts['d']/2, y1=by+bolts['d']/2, fillcolor="white", line=dict(color="black", width=1))
        
        add_leader(fig, wp, hp/2, "2L-Angle", ax=40, ay=-40)
        dim_x = wp + 20

    else: # Fin Plate
        fig.add_shape(type="rect", x0=0, y0=-hp/2, x1=wp, y1=hp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        start_y = hp/2 - plate['lv']
        for c in range(bolts['cols']):
            bx = plate['e1'] + (c * bolts['s_h'])
            for r in range(bolts['rows']):
                by = start_y - (r * bolts['s_v'])
                fig.add_shape(type="circle", x0=bx-bolts['d']/2, y0=by-bolts['d']/2, x1=bx+bolts['d']/2, y1=by+bolts['d']/2, fillcolor="white", line=dict(color="black", width=1))
        
        add_leader(fig, wp, hp/2, "Fin Plate", ax=40, ay=-40)
        dim_x = wp + 20

    # Dimensions
    add_dim(fig, dim_x, hp/2, dim_x, hp/2-plate['lv'], f"{plate['lv']}", 10, "v")
    add_dim(fig, dim_x, hp/2-plate['lv'], dim_x, hp/2-plate['lv']-(bolts['rows']-1)*bolts['s_v'], f"{bolts['rows']-1}@{bolts['s_v']}", 10, "v")

    force_range(fig, [-300, 300], [-300, 300]) # Lock range
    fig.update_layout(title_text=f"<b>FRONT VIEW</b> : {ctype}")
    return fig

# --- 3.2 SIDE VIEW (รูปตัด) ---
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    ctype = plate.get('type', 'Fin Plate')
    
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    hp, tp = plate['h'], plate['t']
    
    # วาดเสา (Background)
    fig.add_shape(type="rect", x0=-b/2-20, y0=-h/2-50, x1=b/2+20, y1=h/2+50, line=dict(color="black", width=2))
    fig.add_trace(go.Scatter(x=[-b/2, b/2, b/2, -b/2], y=[-h/2, -h/2, h/2, h/2], fill='toself', fillpattern=dict(shape="/", size=10, solidity=0.2), mode='none', hoverinfo='skip'))

    # --- LOGIC SELECTION ---
    if ctype == "End Plate":
        # *** KEY FIX *** : End Plate Side View เห็นคานยาวๆ ไม่ใช่หน้าตัด I
        # Plate
        fig.add_shape(type="rect", x0=0, y0=-hp/2, x1=tp, y1=hp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        # Beam (Longitudinal)
        L_beam = 250
        fig.add_shape(type="rect", x0=tp, y0=-h/2, x1=tp+L_beam, y1=h/2, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(width=0))
        fig.add_shape(type="line", x0=tp, y0=h/2, x1=tp+L_beam, y1=h/2, line=dict(color="black", width=2)) # Top Flange
        fig.add_shape(type="line", x0=tp, y0=-h/2, x1=tp+L_beam, y1=-h/2, line=dict(color="black", width=2)) # Bot Flange
        fig.add_shape(type="line", x0=tp, y0=h/2-tf, x1=tp+L_beam, y1=h/2-tf, line=dict(color="gray", width=1)) # Inner Top
        fig.add_shape(type="line", x0=tp, y0=-h/2+tf, x1=tp+L_beam, y1=-h/2+tf, line=dict(color="gray", width=1)) # Inner Bot
        
        # Bolts (Head Visible)
        start_y = hp/2 - plate['lv']
        for r in range(bolts['rows']):
            y = start_y - (r * bolts['s_v'])
            fig.add_shape(type="rect", x0=-15, y0=y-bolts['d']/2, x1=tp+12, y1=y+bolts['d']/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tp, y0=y-bolts['d'], x1=tp+8, y1=y+bolts['d'], fillcolor="black", line=dict(width=0))

        add_leader(fig, tp, hp/2, "End Plate", ax=40, ay=-40)

    else: 
        # Fin / Angle : เห็นหน้าตัด I-Shape ตรงกลาง (Cut Section)
        draw_h_section(fig, 0, 0, h, b, tf, tw, STYLE['STEEL_CUT'], "I")
        
        start_y = hp/2 - plate['lv']
        bolt_y_list = [start_y - (r*bolts['s_v']) for r in range(bolts['rows'])]

        if ctype == "Double Angle":
            # Angles L/R
            fig.add_shape(type="rect", x0=-tw/2-tp, y0=-hp/2, x1=-tw/2, y1=hp/2, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
            fig.add_shape(type="rect", x0=tw/2, y0=-hp/2, x1=tw/2+tp, y1=hp/2, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
            # Bolts through
            for y in bolt_y_list:
                fig.add_shape(type="rect", x0=-tw/2-tp-15, y0=y-bolts['d']/2, x1=tw/2+tp+15, y1=y+bolts['d']/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            add_leader(fig, tw/2+tp, 0, "Double Angle", ax=40, ay=-40)

        else: # Fin Plate
            # Plate at Center
            fig.add_shape(type="rect", x0=tw/2, y0=-hp/2, x1=tw/2+tp, y1=hp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
            # Bolts
            for y in bolt_y_list:
                fig.add_shape(type="rect", x0=-tw/2-15, y0=y-bolts['d']/2, x1=tw/2+tp+15, y1=y+bolts['d']/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            add_leader(fig, tw/2+tp, 0, "Fin Plate", ax=40, ay=-40)

    force_range(fig, [-300, 300], [-300, 300])
    fig.update_layout(title_text=f"<b>SIDE VIEW (Section)</b> : {ctype}")
    return fig

# --- 3.3 PLAN VIEW (รูปแปลน) ---
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    ctype = plate.get('type', 'Fin Plate')
    
    col_size = 300
    draw_h_section(fig, -col_size/2, 0, col_size, col_size, 16, 12, STYLE['STEEL_CUT'], "H") # เสา H-Beam
    
    tp, wp = plate['t'], plate['w']
    
    if ctype == "End Plate":
        # Plate: แปะหน้าเสา (แนวตั้งในแปลน)
        fig.add_shape(type="rect", x0=0, y0=-wp/2, x1=tp, y1=wp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        # Beam: ยื่นออกจาก Plate
        fig.add_shape(type="rect", x0=tp, y0=-beam['b']/2, x1=tp+300, y1=beam['b']/2, fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=STYLE['STEEL_FACE']['line'])
        fig.add_shape(type="line", x0=tp, y0=0, x1=tp+300, y1=0, line=STYLE['CL']) # CL Beam
        
        # Bolts (Top down)
        gauge = 100
        for s in [-1, 1]:
            by = s * gauge / 2
            fig.add_shape(type="rect", x0=-20, y0=by-bolts['d']/2, x1=tp+15, y1=by+bolts['d']/2, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
            fig.add_shape(type="rect", x0=tp, y0=by-bolts['d'], x1=tp+10, y1=by+bolts['d'], fillcolor="black", line=dict(width=0))

        add_leader(fig, tp, wp/2, "End Plate", ax=40, ay=-40)
        add_dim(fig, 0, -wp/2-30, tp, -wp/2-30, f"tp={tp}", -20, "h")

    elif ctype == "Double Angle":
        # Beam Web
        SETBACK = 15
        fig.add_shape(type="rect", x0=SETBACK, y0=-beam['tw']/2, x1=SETBACK+300, y1=beam['tw']/2, fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
        
        # Angles (L-Shape)
        leg_len = 76
        for s in [-1, 1]:
            # Leg on Web
            fig.add_shape(type="rect", x0=SETBACK, y0=s*beam['tw']/2, x1=SETBACK+leg_len, y1=s*(beam['tw']/2+tp), fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
            # Leg on Col
            y_far = s * (beam['tw']/2 + 100) # ขาฉากยื่นออกไป
            fig.add_shape(type="rect", x0=SETBACK, y0=s*beam['tw']/2, x1=SETBACK+tp, y1=y_far, fillcolor=STYLE['ANGLE']['fillcolor'], line=STYLE['ANGLE']['line'])
            
        add_leader(fig, SETBACK, beam['tw']/2+tp, "2L-Angle", ax=40, ay=-40)

    else: # Fin Plate
        SETBACK = 15
        # Plate
        fig.add_shape(type="rect", x0=0, y0=-tp/2, x1=wp, y1=tp/2, fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
        # Beam Web
        fig.add_shape(type="rect", x0=SETBACK, y0=tp/2, x1=wp+200, y1=tp/2+beam['tw'], fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
        
        # Bolt
        bx = plate['e1']
        fig.add_shape(type="rect", x0=bx-bolts['d']/2, y0=-tp/2-10, x1=bx+bolts['d']/2, y1=tp/2+beam['tw']+10, fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
        
        add_leader(fig, wp, tp/2, "Fin Plate", ax=40, ay=-30)
        add_dim(fig, 0, 0, SETBACK, 0, f"{SETBACK}", -30, "h")

    force_range(fig, [-200, 400], [-250, 250])
    fig.update_layout(title_text=f"<b>PLAN VIEW</b> : {ctype}")
    return fig

# =============================================================================
# 🚀 TEST EXECUTION (รันส่วนนี้เพื่อดูผลลัพธ์)
# =============================================================================
beam_data = {'h': 400, 'b': 200, 'tf': 13, 'tw': 8}
bolt_data = {'d': 20, 'rows': 4, 'cols': 1, 's_v': 75, 's_h': 0}

# --- 1. TEST FIN PLATE ---
plate_fin = {'type': 'Fin Plate', 'h': 300, 'w': 100, 't': 10, 'lv': 40, 'e1': 50}
fig1 = create_front_view(beam_data, plate_fin, bolt_data)
fig1.show()

# --- 2. TEST END PLATE (พระเอกของงานนี้) ---
plate_end = {'type': 'End Plate', 'h': 450, 'w': 200, 't': 16, 'lv': 40, 'e1': 0}
# ลองเปลี่ยน bolt data ให้เหมาะกับ End Plate (2 rows)
bolt_end = {'d': 20, 'rows': 4, 'cols': 2, 's_v': 75, 's_h': 100} 
fig2_front = create_front_view(beam_data, plate_end, bolt_end)
fig2_side  = create_side_view(beam_data, plate_end, bolt_end)
fig2_plan  = create_plan_view(beam_data, plate_end, bolt_end)

fig2_front.show()
fig2_side.show()
fig2_plan.show()

# --- 3. TEST DOUBLE ANGLE ---
plate_angle = {'type': 'Double Angle', 'h': 280, 'w': 80, 't': 10, 'lv': 40, 'e1': 50}
fig3 = create_side_view(beam_data, plate_angle, bolt_data)
fig3.show()

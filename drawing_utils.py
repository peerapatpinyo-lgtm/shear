# drawing_utils.py (V14 - Senior Structural Engineer Edition)
import plotly.graph_objects as go
import numpy as np

# =============================================================================
# 📐 CAD STANDARDS & CONFIG
# =============================================================================
COLOR_STEEL_CUT = "#D1D5DB"  # สีเนื้อเหล็กโดนตัด (Light Gray)
COLOR_STEEL_FACE = "#F3F4F6" # สีผิวเหล็ก (White Smoke)
COLOR_PLATE = "#BAE6FD"      # สี Plate (Light Blue)
COLOR_BOLT = "#475569"       # สี Bolt (Slate)
COLOR_DIM = "#1E40AF"        # สีเส้นบอกระยะ (Blue)
COLOR_CL = "#EF4444"         # สี Center Line (Red)
COLOR_WELD = "#000000"       # สีรอยเชื่อม

# Engineering Defaults
SETBACK = 15  # ระยะ Erection Gap มาตรฐาน (mm)

def add_dim(fig, x0, y0, x1, y1, text, offset=30, type="h", color=COLOR_DIM):
    """ฟังก์ชันเขียน Dimension แบบมืออาชีพ (Arrow + Extension Lines)"""
    # Extension Line Length
    ext_len = 5
    
    if type == "h": # Horizontal Dimension
        y_pos = y0 + offset
        # Draw Extension Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos+ext_len, line=dict(color=color, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos+ext_len, line=dict(color=color, width=0.5))
        # Draw Arrow Line
        fig.add_annotation(x=x1, y=y_pos, ax=x0, ay=y_pos, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=color, text="")
        # Text
        fig.add_annotation(x=(x0+x1)/2, y=y_pos+10, text=f"<b>{text}</b>", showarrow=False, 
                           font=dict(size=11, color=color, family="Arial"))
    
    else: # Vertical Dimension
        x_pos = x0 + offset
        # Draw Extension Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos+ext_len, y1=y0, line=dict(color=color, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos+ext_len, y1=y1, line=dict(color=color, width=0.5))
        # Draw Arrow Line
        fig.add_annotation(x=x_pos, y=y1, ax=x_pos, ay=y0, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=color, text="")
        # Text
        fig.add_annotation(x=x_pos+15, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, textangle=-90,
                           font=dict(size=11, color=color, family="Arial"))

def draw_hex_bolt_side(fig, x_center, y_center, d, length, orientation="h"):
    """วาด Bolt ด้านข้าง (Shank + Head + Nut)"""
    head_h = d * 0.6
    nut_h = d * 0.8
    head_dia = d * 1.6
    
    if orientation == "h": # แนวนอน (ใช้ใน Section, Plan)
        # Shank
        fig.add_shape(type="rect", x0=x_center-length/2, y0=y_center-d/2, x1=x_center+length/2, y1=y_center+d/2,
                      fillcolor=COLOR_BOLT, line=dict(width=0))
        # Head (Left)
        fig.add_shape(type="rect", x0=x_center-length/2-head_h, y0=y_center-head_dia/2, x1=x_center-length/2, y1=y_center+head_dia/2,
                      fillcolor=COLOR_BOLT, line=dict(color="black", width=1))
        # Nut (Right)
        fig.add_shape(type="rect", x0=x_center+length/2, y0=y_center-head_dia/2, x1=x_center+length/2+nut_h, y1=y_center+head_dia/2,
                      fillcolor=COLOR_BOLT, line=dict(color="black", width=1))
    else: # แนวตั้ง
        pass # Implement if needed

# =============================================================================
# 1. SECTIONAL PLAN VIEW (มองจากด้านบน ตัดผ่าน Web)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    
    # Dimensions
    tw = beam['tw']
    tp, wp = plate['t'], plate['w']
    col_tf = 12 # สมมติความหนาปีกเสา (ถ้าไม่มีข้อมูล)
    
    # 1. Column Flange (ตัดขวาง) - เป็นฐานยึด
    fig.add_shape(type="rect", x0=-col_tf, y0=-100, x1=0, y1=100, 
                  fillcolor=COLOR_STEEL_CUT, line=dict(color="black", width=2))
    # Hatching for Column
    fig.add_trace(go.Scatter(x=[-col_tf, 0], y=[-100, 100], mode='lines', line=dict(width=0), hoverinfo='skip',
                             fillpattern=dict(shape="/", size=5, solidity=0.3, fgcolor="black"), fill='toself'))

    # 2. Connection Plate (Fin Plate) - ยื่นออกมาจากเสา
    fig.add_shape(type="rect", x0=0, y0=-tp/2, x1=wp, y1=tp/2, 
                  fillcolor=COLOR_PLATE, line=dict(color="black", width=1))

    # 3. Beam Web (ตัดขวาง) - ประกบกับ Plate
    # ต้องมี Setback (ระยะห่างจากหน้าเสาถึงขอบคาน)
    web_start = SETBACK 
    web_len = wp + 50 # วาดเลย Plate ไปหน่อย
    
    # สมมติ Beam Web อยู่ด้านบนของ Plate (ใน Plan) หรือประกบข้าง
    # ปกติ Fin Plate อยู่ด้านข้าง Web -> วาด Web ประกบข้าง Plate
    fig.add_shape(type="rect", x0=web_start, y0=tp/2, x1=web_start+web_len, y1=tp/2+tw, 
                  fillcolor=COLOR_STEEL_CUT, line=dict(color="black", width=1))
    
    # 4. Bolt Assembly (ถูกต้องตามวิศวกรรม: Head -> Plate -> Web -> Nut)
    bolt_y_center = tp/2 + tw/2
    bolt_x = plate['e1'] # ระยะ Bolt ตัวแรกจากหน้าเสา
    
    # ความยาว Bolt = Plate + Web + Washer/Nut allowances
    bolt_grip = tp + tw + 10 
    draw_hex_bolt_side(fig, bolt_x, tp/2, bolts['d'], bolt_grip, "v") # เดี๋ยวเขียน Logic วาด Bolt แนวตั้งใน Plan ใหม่ข้างล่างนี้

    # *แก้ใหม่* วาด Bolt ใน Plan View (มองท็อปทะลุแกน)
    # Bolt ต้องเจาะผ่าน Plate(y=-tp/2 to tp/2) และ Web(y=tp/2 to tp/2+tw)
    # แกน Bolt อยู่ที่ y = 0 (Center Plate) ถึงไหน?
    # จริงๆ Web มักประกบข้าง -> Center Bolt อยู่ที่รอยต่อ
    
    # เอาใหม่ให้ Clear: 
    # y=0 คือกึ่งกลาง Plate
    # Plate: y from -tp/2 to tp/2
    # Web: y from tp/2 to tp/2+tw (ประกบด้านขวาของ Plate ในรูป)
    
    b_len = tp + tw + 15 # เผื่อเกลียว
    b_cen_y = tp/2 # กึ่งกลางรอยต่อ (ไม่ใช่ละ Bolt ต้องทะลุทั้งคู่)
    
    # วาด Bolt แนวนอนขวางแกน Y (ทะลุจากล่างขึ้นบนในรูป)
    fig.add_shape(type="rect", x0=bolt_x-bolts['d']/2, y0=-tp/2-10, x1=bolt_x+bolts['d']/2, y1=tp/2+tw+10,
                  fillcolor=COLOR_BOLT, line=dict(width=1)) # Shank
    fig.add_shape(type="rect", x0=bolt_x-bolts['d'], y0=-tp/2-18, x1=bolt_x+bolts['d'], y1=-tp/2-10,
                  fillcolor="black", line=dict(width=1)) # Head (Bottom)
    fig.add_shape(type="rect", x0=bolt_x-bolts['d'], y0=tp/2+tw+10, x1=bolt_x+bolts['d'], y1=tp/2+tw+18,
                  fillcolor="black", line=dict(width=1)) # Nut (Top)

    # 5. Weld Symbol (Fillet Weld 2 ด้านของ Plate ที่ติดเสา)
    w_size = plate['weld_size']
    # Weld ด้านล่าง
    fig.add_shape(type="path", path=f"M 0 {-tp/2} L {w_size} {-tp/2} L 0 {-tp/2-w_size} Z", fillcolor=COLOR_WELD, line_width=0)
    # Weld ด้านบน
    fig.add_shape(type="path", path=f"M 0 {tp/2} L {w_size} {tp/2} L 0 {tp/2+w_size} Z", fillcolor=COLOR_WELD, line_width=0)
    
    # 6. Dimensions
    add_dim(fig, 0, tp/2+tw+30, bolt_x, tp/2+tw+30, f"e1={plate['e1']}", 30, "h")
    add_dim(fig, SETBACK, -tp/2-30, 0, -tp/2-30, f"Gap={SETBACK}", 20, "h")
    add_dim(fig, 0, -tp/2-60, wp, -tp/2-60, f"W_plate={wp}", 20, "h")

    fig.update_layout(title="<b>SECTIONAL PLAN VIEW</b> (Top View at Beam Web)", 
                      plot_bgcolor="white", height=350, showlegend=False,
                      xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

# =============================================================================
# 2. ELEVATION VIEW (มองด้านข้าง เห็น Plate เต็มใบ)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    
    h_beam = beam['h']
    h_pl, w_pl = plate['h'], plate['w']
    lv = plate['lv']
    sv = bolts['s_v']
    rows = bolts['rows']
    e1 = plate['e1']
    cols = bolts['cols']
    sh = bolts['s_h']

    # 1. Column Reference Line
    fig.add_shape(type="line", x0=0, y0=-h_beam/2-50, x1=0, y1=h_beam/2+50, line=dict(color="black", width=3))
    
    # 2. Beam Web (Background)
    fig.add_shape(type="rect", x0=SETBACK, y0=-h_beam/2, x1=w_pl+150, y1=h_beam/2, 
                  fillcolor="white", line=dict(color=COLOR_STEEL_CUT, width=2, dash="dot")) # Beam เป็นเส้นประเพราะโดน Plate บัง? ไม่ใช่ Beam เป็น Main
    # เอาใหม่ Beam Web เป็น Solid แต่จางๆ
    fig.add_shape(type="rect", x0=SETBACK, y0=-h_beam/2, x1=w_pl+150, y1=h_beam/2, 
                  fillcolor=COLOR_STEEL_FACE, line=dict(color="gray", width=1))

    # 3. Fin Plate (Solid Line)
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, 
                  fillcolor=COLOR_PLATE, line=dict(color="black", width=2))
    
    # 4. Bolts (Circles)
    start_y = h_pl/2 - lv
    
    for c in range(cols):
        cur_x = e1 + (c * sh)
        # ตรวจสอบว่า Bolt ไม่ชิดขอบ (Visual Check)
        for r in range(rows):
            cur_y = start_y - (r * sv)
            # Bolt Shank
            fig.add_shape(type="circle", x0=cur_x-bolts['d']/2, y0=cur_y-bolts['d']/2, x1=cur_x+bolts['d']/2, y1=cur_y+bolts['d']/2,
                          fillcolor="white", line=dict(color="black", width=1))
            # Center Mark
            fig.add_shape(type="line", x0=cur_x-5, y0=cur_y, x1=cur_x+5, y1=cur_y, line=dict(color="red", width=1))
            fig.add_shape(type="line", x0=cur_x, y0=cur_y-5, x1=cur_x, y1=cur_y+5, line=dict(color="red", width=1))
    
    # 5. Dimensions (ละเอียด)
    # Vertical
    x_dim_v = w_pl + 20
    add_dim(fig, x_dim_v, h_pl/2, x_dim_v, h_pl/2-lv, f"Lv={lv}", 10, "v")
    if rows > 1:
        add_dim(fig, x_dim_v, h_pl/2-lv, x_dim_v, h_pl/2-lv-sv, f"s={sv}", 10, "v")
    add_dim(fig, 0, h_pl/2, 0, -h_pl/2, f"H_pl={h_pl}", -30, "v") # บอกด้านซ้าย
    
    # Horizontal
    y_dim_h = -h_beam/2 - 30
    add_dim(fig, 0, y_dim_h, e1, y_dim_h, f"e1={e1}", 20, "h")
    add_dim(fig, 0, y_dim_h-30, w_pl, y_dim_h-30, f"W_pl={w_pl}", 20, "h")
    
    # Erection Gap
    add_dim(fig, 0, h_beam/2+20, SETBACK, h_beam/2+20, f"{SETBACK}", 10, "h")

    fig.update_layout(title="<b>ELEVATION VIEW</b> (Connection Detail)", plot_bgcolor="white", height=450,
                      showlegend=False, xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

# =============================================================================
# 3. SECTION VIEW (มองตามแกนคาน เห็นหน้าตัด I-Beam และปีกเสา)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl = plate['h']
    
    # 1. Column Flange (ที่เป็น Backing)
    # สมมติเสาขนาด H-Beam ใหญ่กว่าหรือเท่ากัน (เช่น H300)
    col_width = b + 50 # สมมติความกว้างเสา
    col_tf = 12
    
    # วาดปีกเสา (Column Flange) เป็นแผ่นหนาด้านหลัง
    fig.add_shape(type="rect", x0=-col_width/2, y0=-h/2-50, x1=col_width/2, y1=h/2+50,
                  fillcolor="white", line=dict(color="black", width=2)) # เส้นรอบรูปเสา
    
    # Hatching (แสดงว่าเป็นผิวหน้าเสา)
    # เนื่องจากเป็น View มองเข้าหาเสา เราอาจจะไม่ Hatch แต่แสดงเป็นกรอบ
    
    # 2. I-Beam Section (Cross Section)
    # Web
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, 
                  fillcolor=COLOR_STEEL_CUT, line=dict(color="black", width=2))
    # Top Flange
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, 
                  fillcolor=COLOR_STEEL_CUT, line=dict(color="black", width=2))
    # Bottom Flange
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, 
                  fillcolor=COLOR_STEEL_CUT, line=dict(color="black", width=2))
    
    # 3. Fin Plate (Side visible)
    # Plate เชื่อมติดเสา (อยู่หลัง Web ของคาน) แต่ Web คานบัง?
    # ไม่ใช่... Fin Plate ยื่นออกมา Web คานประกบ
    # ใน View นี้เราตัดผ่านคาน -> จะเห็น Plate โผล่มาจากด้านหลัง (ถ้ามองไปที่เสา)
    # หรือถ้าตัดผ่าน Bolt เราจะเห็น Plate ซ้อนกับ Web
    
    # วาด Plate ซ้อน Web (ให้เห็นขอบ Plate เล็กน้อยถ้า Plate สูงไม่เท่า Web)
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+plate['t'], y1=h_pl/2, 
                  fillcolor=COLOR_PLATE, line=dict(color="black", width=1))

    # 4. Bolts (Shank View passing through)
    rows = bolts['rows']
    sv = bolts['s_v']
    lv = plate['lv']
    start_y = h_pl/2 - lv
    
    for r in range(rows):
        y_pos = start_y - (r * sv)
        # Bolt ยาวผ่าน Web(tw) และ Plate(t)
        # Center line
        fig.add_shape(type="line", x0=-b/2, y0=y_pos, x1=b/2, y1=y_pos, line=dict(color=COLOR_CL, dash="dashdot", width=1))
        # Head & Nut (Schematic)
        draw_hex_bolt_side(fig, tw/2 + plate['t']/2, y_pos, bolts['d'], tw+plate['t']+20, "h")

    # 5. Dimensions
    # Beam Depth
    add_dim(fig, -b/2-20, h/2, -b/2-20, -h/2, f"d={h}", 30, "v")
    # Beam Width
    add_dim(fig, -b/2, h/2+20, b/2, h/2+20, f"bf={b}", 30, "h")
    # Column Width Indication
    add_dim(fig, -col_width/2, -h/2-40, col_width/2, -h/2-40, "Column Width", 20, "h", color="gray")

    fig.update_layout(title="<b>SECTION A-A</b> (Through Beam & Connection)", plot_bgcolor="white", height=500,
                      showlegend=False, xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

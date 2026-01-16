# drawing_utils.py (V16 - Ultimate Professional Edition)
import plotly.graph_objects as go
import numpy as np

# =============================================================================
# 🎨 CAD STANDARD STYLES
# =============================================================================
STYLE = {
    'STEEL_CUT':   dict(fillcolor="#E5E7EB", line=dict(color="#1F2937", width=2)), # สีตัดเหล็ก (เทาอ่อน)
    'STEEL_FACE':  dict(fillcolor="#F9FAFB", line=dict(color="#9CA3AF", width=1)), # สีผิวเหล็ก (ขาวควันบุหรี่)
    'PLATE':       dict(fillcolor="#DBEAFE", line=dict(color="#1E40AF", width=2)), # สี Plate (ฟ้าอ่อน)
    'BOLT':        dict(fillcolor="#4B5563", line=dict(color="#111827", width=1.5)), # สี Bolt (เทาเข้ม)
    'WELD':        dict(fillcolor="#000000", line=dict(width=0)),                  # สีเชื่อม (ดำ)
    'CL':          dict(color="#DC2626", width=1, dash="dashdot"),                 # เส้น Center (แดงจุดยาว)
    'DIM':         dict(color="#1D4ED8", family="Sarabun", size=12),               # เส้นบอกระยะ (น้ำเงิน)
    'ERROR':       dict(line=dict(color="#EF4444", width=2, dash="dash"))          # เส้น Error (แดงประ)
}

SETBACK = 15  # ระยะเว้นช่องว่างติดตั้ง (mm)

# =============================================================================
# 🛠️ HELPER FUNCTIONS (CAD TOOLS)
# =============================================================================
def add_dim(fig, x0, y0, x1, y1, text, offset=30, type="h", color=STYLE['DIM']['color'], is_err=False):
    """ฟังก์ชันเขียน Dimension แบบวิศวกรรม (มีหัวลูกศร + เส้น Extension)"""
    col = "#EF4444" if is_err else color
    ext = 5 * np.sign(offset)
    
    if type == "h": # แนวนอน
        y_pos = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos+ext, line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos+ext, line=dict(color=col, width=0.5))
        fig.add_annotation(x=x1, y=y_pos, ax=x0, ay=y_pos, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=col, text="")
        fig.add_annotation(x=(x0+x1)/2, y=y_pos+(10 if offset>0 else -15), text=f"<b>{text}</b>", 
                           showarrow=False, font=dict(size=11, color=col))
    else: # แนวตั้ง
        x_pos = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos+ext, y1=y0, line=dict(color=col, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos+ext, y1=y1, line=dict(color=col, width=0.5))
        fig.add_annotation(x=x_pos, y=y1, ax=x_pos, ay=y0, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=col, text="")
        fig.add_annotation(x=x_pos+(15 if offset>0 else -15), y=(y0+y1)/2, text=f"<b>{text}</b>", 
                           showarrow=False, textangle=-90, font=dict(size=11, color=col))

def draw_h_beam_section(fig, x_cen, y_cen, h, b, tf, tw, color_style, orientation="I"):
    """วาดหน้าตัด H-Beam (I-Shape)"""
    if orientation == "I": # รูปตัว I (ปกติ)
        # Web
        fig.add_shape(type="rect", x0=x_cen-tw/2, y0=y_cen-h/2+tf, x1=x_cen+tw/2, y1=y_cen+h/2-tf,
                      fillcolor=color_style['fillcolor'], line=dict(width=0))
        # Top Flange
        fig.add_shape(type="rect", x0=x_cen-b/2, y0=y_cen+h/2-tf, x1=x_cen+b/2, y1=y_cen+h/2,
                      fillcolor=color_style['fillcolor'], line=color_style['line'])
        # Bottom Flange
        fig.add_shape(type="rect", x0=x_cen-b/2, y0=y_cen-h/2, x1=x_cen+b/2, y1=y_cen-h/2+tf,
                      fillcolor=color_style['fillcolor'], line=color_style['line'])
        # Web Outline (Left/Right)
        fig.add_shape(type="line", x0=x_cen-tw/2, y0=y_cen-h/2+tf, x1=x_cen-tw/2, y1=y_cen+h/2-tf, line=color_style['line'])
        fig.add_shape(type="line", x0=x_cen+tw/2, y0=y_cen-h/2+tf, x1=x_cen+tw/2, y1=y_cen+h/2-tf, line=color_style['line'])
        
    else: # รูปตัว H (ตะแคง หรือ Top View ของเสา)
        # Web (Horizontal)
        fig.add_shape(type="rect", x0=x_cen-h/2+tf, y0=y_cen-tw/2, x1=x_cen+h/2-tf, y1=y_cen+tw/2,
                      fillcolor=color_style['fillcolor'], line=dict(width=0))
        # Left Flange (Vertical)
        fig.add_shape(type="rect", x0=x_cen-h/2, y0=y_cen-b/2, x1=x_cen-h/2+tf, y1=y_cen+b/2,
                      fillcolor=color_style['fillcolor'], line=color_style['line'])
        # Right Flange (Vertical)
        fig.add_shape(type="rect", x0=x_cen+h/2-tf, y0=y_cen-b/2, x1=x_cen+h/2, y1=y_cen+b/2,
                      fillcolor=color_style['fillcolor'], line=color_style['line'])
        # Web Lines
        fig.add_shape(type="line", x0=x_cen-h/2+tf, y0=y_cen-tw/2, x1=x_cen+h/2-tf, y1=y_cen-tw/2, line=color_style['line'])
        fig.add_shape(type="line", x0=x_cen-h/2+tf, y0=y_cen+tw/2, x1=x_cen+h/2-tf, y1=y_cen+tw/2, line=color_style['line'])

# =============================================================================
# 1. PLAN VIEW (TOP DOWN)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    
    tw = beam['tw']
    tp, wp, e1 = plate['t'], plate['w'], plate['e1']
    
    # --- 1. Column Section (Top View = H-Shape) ---
    # สมมติขนาดเสา H300x300 (ถ้าไม่มีข้อมูล) หรือใหญ่กว่าคาน
    col_h, col_b = max(300, beam['b']+50), max(300, beam['b']+50)
    col_tf, col_tw = 14, 10
    
    # วาดเสา (Column) เป็นรูปตัว H (แกนเสาอยู่ตรงกลาง)
    # จุดเชื่อมต่ออยู่ที่ผิวปีกขวาของเสา (x=0)
    # ดังนั้น Center เสาอยู่ที่ x = -col_h/2
    draw_h_beam_section(fig, -col_h/2, 0, col_h, col_b, col_tf, col_tw, STYLE['STEEL_CUT'], orientation="H")
    
    # --- 2. Fin Plate (เชื่อมติดปีกเสา) ---
    fig.add_shape(type="rect", x0=0, y0=-tp/2, x1=wp, y1=tp/2, 
                  fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
    
    # --- 3. Beam Web (มาประกบ) ---
    beam_len = wp + 50
    # Beam Web ตัด section
    fig.add_shape(type="rect", x0=SETBACK, y0=tp/2, x1=beam_len, y1=tp/2+tw,
                  fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
    
    # --- 4. Bolt (Top View - เห็นด้านข้าง Bolt) ---
    bolt_x = e1 # ระยะจากหน้าเสา
    bolt_len = tp + tw + 15
    bolt_cen_y = tp/2 # กึ่งกลางรอยต่อ
    
    # วาด Bolt ขวาง (หัวอยู่ฝั่ง Plate, น็อตอยู่ฝั่ง Web)
    y_head = -tp/2 - 8
    y_nut = tp/2 + tw
    
    # Shank
    fig.add_shape(type="rect", x0=bolt_x-bolts['d']/2, y0=y_head, x1=bolt_x+bolts['d']/2, y1=y_nut,
                  fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
    # Head (Hex)
    fig.add_shape(type="rect", x0=bolt_x-bolts['d'], y0=y_head-10, x1=bolt_x+bolts['d'], y1=y_head,
                  fillcolor="black", line=dict(width=0))
    # Nut
    fig.add_shape(type="rect", x0=bolt_x-bolts['d'], y0=y_nut, x1=bolt_x+bolts['d'], y1=y_nut+12,
                  fillcolor="black", line=dict(width=0))
    # Center Line
    fig.add_shape(type="line", x0=bolt_x, y0=y_head-20, x1=bolt_x, y1=y_nut+30, line=STYLE['CL'])

    # --- 5. Weld Symbol ---
    ws = plate['weld_size']
    fig.add_shape(type="path", path=f"M 0 {-tp/2} L {ws} {-tp/2} L 0 {-tp/2-ws} Z", fillcolor="black", line_width=0)
    fig.add_shape(type="path", path=f"M 0 {tp/2} L {ws} {tp/2} L 0 {tp/2+ws} Z", fillcolor="black", line_width=0)

    # --- 6. Dimensions ---
    add_dim(fig, 0, -col_b/2, -col_h, -col_b/2, f"Col H={col_h}", 30, "h", color="gray")
    add_dim(fig, 0, -tp/2-50, wp, -tp/2-50, f"Plate W={wp}", 20, "h")
    add_dim(fig, 0, tp/2+tw+40, bolt_x, tp/2+tw+40, f"e1={e1}", 20, "h")
    add_dim(fig, 0, 0, SETBACK, 0, f"{SETBACK}", -30, "h")

    fig.update_layout(title="<b>PLAN VIEW</b> (Column & Connection)", 
                      plot_bgcolor="white", height=450, showlegend=False,
                      margin=dict(l=50, r=50, t=80, b=50),
                      xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

# =============================================================================
# 2. ELEVATION VIEW (FRONT) - แก้ไข Bolt ชิดขอบ
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    
    h_b = beam['h']
    h_pl_input = plate['h']
    w_pl = plate['w']
    lv = plate['lv']
    sv, rows = bolts['s_v'], bolts['rows']
    e1, cols, sh = plate['e1'], bolts['cols'], bolts['s_h']
    
    # --- 1. INTELLIGENT PLATE SIZING (Auto-Fix Visual) ---
    # คำนวณความสูงที่ต้องการจริง (Minimum Required Height)
    min_edge_dist = 1.5 * bolts['d'] # มาตรฐาน AISC
    req_h_bolt_zone = lv + ((rows-1)*sv) + min_edge_dist
    
    # ถ้า Input สั้นกว่าที่ควรจะเป็น -> วาดรูปให้ถูก (ยาวขึ้น) แต่โชว์เส้นประเตือน
    if h_pl_input < req_h_bolt_zone:
        draw_h_pl = req_h_bolt_zone + 20 # เผื่อสวยงาม
        is_short = True
    else:
        draw_h_pl = h_pl_input
        is_short = False
        
    y_top = draw_h_pl/2
    y_bot = -draw_h_pl/2
    
    # --- 2. Drawing Objects ---
    # Column Ref
    fig.add_shape(type="line", x0=0, y0=-h_b/2-100, x1=0, y1=h_b/2+100, line=dict(color="black", width=3))
    
    # Beam Web (Ghost)
    fig.add_shape(type="rect", x0=SETBACK, y0=-h_b/2, x1=w_pl+150, y1=h_b/2, 
                  fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(color="#E5E7EB", width=1))

    # Connection Plate (Solid - Corrected Size)
    fig.add_shape(type="rect", x0=0, y0=y_bot, x1=w_pl, y1=y_top, 
                  fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
    
    # User Input Line (Show where user stopped if short)
    if is_short:
        user_y_bot = y_top - h_pl_input
        fig.add_shape(type="line", x0=-10, y0=user_y_bot, x1=w_pl+10, y1=user_y_bot, line=STYLE['ERROR'])
        fig.add_annotation(x=w_pl/2, y=user_y_bot-10, text="User Input Height Limit", font=dict(color="red", size=10))

    # Bolts
    bolt_start_y = y_top - lv
    for c in range(cols):
        cx = e1 + (c * sh)
        for r in range(rows):
            cy = bolt_start_y - (r * sv)
            # Bolt Head
            fig.add_shape(type="circle", x0=cx-bolts['d']/2, y0=cy-bolts['d']/2, x1=cx+bolts['d']/2, y1=cy+bolts['d']/2,
                          fillcolor="white", line=dict(color="#374151", width=1.5))
            # Crosshair
            fig.add_shape(type="line", x0=cx-5, y0=cy, x1=cx+5, y1=cy, line=dict(color="#374151", width=0.5))
            fig.add_shape(type="line", x0=cx, y0=cy-5, x1=cx, y1=cy+5, line=dict(color="#374151", width=0.5))

    # --- 3. Dimensions ---
    x_dim = w_pl + 25
    
    # Lv
    add_dim(fig, x_dim, y_top, x_dim, bolt_start_y, f"Lv={lv}", 10, "v")
    
    # Pitch
    if rows > 1:
        last_bolt_y = bolt_start_y - ((rows-1)*sv)
        add_dim(fig, x_dim, bolt_start_y, x_dim, last_bolt_y, f"Pitch={sv}x{rows-1}", 10, "v")
        
    # Lev (Edge Distance Bottom)
    last_bolt_y = bolt_start_y - ((rows-1)*sv)
    lev_val = last_bolt_y - y_bot
    add_dim(fig, x_dim, last_bolt_y, x_dim, y_bot, f"Lev={lev_val:.1f}", 10, "v")

    # Plate Height
    if is_short:
        add_dim(fig, -30, y_top, -30, y_bot, f"Req H={draw_h_pl:.0f}", -20, "v", is_err=True)
        add_dim(fig, -60, y_top, -60, y_top-h_pl_input, f"Input={h_pl_input}", -20, "v", color="gray")
    else:
        add_dim(fig, -30, y_top, -30, y_bot, f"H_pl={h_pl_input}", -20, "v")

    fig.update_layout(title="<b>ELEVATION VIEW</b> (Plate Geometry)", 
                      height=550, plot_bgcolor="white",
                      margin=dict(l=100, r=80, t=80, b=50),
                      xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

# =============================================================================
# 3. SECTION VIEW (SIDE A-A) - แก้ไขเสาให้รับคานพอดี
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl = plate['h']
    rows, sv, lv = bolts['rows'], bolts['s_v'], plate['lv']
    
    # --- 1. Column Flange (Background) ---
    # Column Flange ปกติจะกว้างกว่า Beam Flange เล็กน้อย (เช่น Beam 200 -> Column 250/300)
    col_width = b + 40 
    col_face_h = h + 200 # สูงเลยคานไปหน่อย
    
    # วาดผิวหน้าปีกเสา (Column Face)
    fig.add_shape(type="rect", x0=-col_width/2, y0=-col_face_h/2, x1=col_width/2, y1=col_face_h/2,
                  fillcolor=STYLE['STEEL_FACE']['fillcolor'], line=dict(color="black", width=2))
    # Hatching (แสดงว่าเป็นผิววัสดุ)
    fig.add_trace(go.Scatter(x=[-col_width/2, col_width/2], y=[-col_face_h/2, col_face_h/2], 
                             mode='lines', line=dict(width=0), hoverinfo='skip',
                             fillpattern=dict(shape="/", size=10, solidity=0.1, fgcolor="#E5E7EB"), fill='toself'))

    # --- 2. Beam Section (I-Shape) ---
    draw_h_beam_section(fig, 0, 0, h, b, tf, tw, STYLE['STEEL_CUT'], orientation="I")

    # --- 3. Plate (Side Edge) ---
    # Plate ยื่นออกมาจากเสา (ด้านหลัง) มาประกบข้าง Web
    # ใน View นี้: Web อยู่ตรงกลาง (x= -tw/2 to tw/2)
    # Plate ประกบด้านขวา (x = tw/2 to tw/2 + tp)
    tp = plate['t']
    
    # ถ้า Plate สูงไม่เท่าคาน
    # ต้องคำนวณตำแหน่ง Y เริ่มต้นของ Plate เทียบกับคาน
    # ปกติ Plate อยู่กลางคาน? ถ้าใช่ -> Center เดียวกัน
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+tp, y1=h_pl/2,
                  fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])

    # --- 4. Bolts ---
    y_start = h_pl/2 - lv
    bolt_total_len = b + 40
    
    for r in range(rows):
        y_pos = y_start - (r * sv)
        # Center Line
        fig.add_shape(type="line", x0=-col_width/2, y0=y_pos, x1=col_width/2, y1=y_pos, line=STYLE['CL'])
        # Bolt Body (Head Left, Nut Right -> but visually cross section)
        # Head
        fig.add_shape(type="rect", x0=tw/2+tp, y0=y_pos-bolts['d']/2, x1=tw/2+tp+15, y1=y_pos+bolts['d']/2,
                      fillcolor="black", line=dict(width=0))
        # Shank (ทะลุ Plate & Web)
        fig.add_shape(type="rect", x0=-tw/2-10, y0=y_pos-bolts['d']/2, x1=tw/2+tp, y1=y_pos+bolts['d']/2,
                      fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))

    # --- 5. Dimensions ---
    add_dim(fig, -b/2-20, h/2, -b/2-20, -h/2, f"Beam D={h}", 30, "v")
    add_dim(fig, -col_width/2, -col_face_h/2, col_width/2, -col_face_h/2, f"Col Width={col_width}", 20, "h", color="gray")
    add_dim(fig, b/2+30, h_pl/2, b/2+30, -h_pl/2, f"Plate H={h_pl}", 30, "v")

    fig.update_layout(title="<b>SECTION A-A</b> (Beam to Column Face)", 
                      height=550, plot_bgcolor="white",
                      margin=dict(l=80, r=80, t=80, b=80),
                      xaxis=dict(visible=False, scaleanchor="y"), yaxis=dict(visible=False))
    return fig

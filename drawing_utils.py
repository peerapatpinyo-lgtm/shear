# drawing_utils.py (V15 - Professional Structural Detailing)
import plotly.graph_objects as go
import numpy as np

# =============================================================================
# 🎨 CAD STANDARD STYLES (Engineering Blueprints)
# =============================================================================
STYLE = {
    'STEEL_CUT':   dict(fillcolor="#E5E7EB", line=dict(color="#1F2937", width=2)), # เหล็กถูกตัด (Light Gray)
    'STEEL_FACE':  dict(fillcolor="#FFFFFF", line=dict(color="#9CA3AF", width=1)), # ผิวเหล็ก (White)
    'PLATE':       dict(fillcolor="#DBEAFE", line=dict(color="#1E40AF", width=2)), # แผ่นเหล็ก (Blue Tint)
    'BOLT':        dict(fillcolor="#4B5563", line=dict(color="#111827", width=1)), # น็อต (Dark Gray)
    'WELD':        dict(fillcolor="#000000", line=dict(width=0)),                  # รอยเชื่อม (Black)
    'CL':          dict(color="#EF4444", width=1, dash="dashdot"),                 # เส้น Center (Red DashDot)
    'DIM':         dict(color="#1D4ED8", family="Arial", size=12),                 # เส้นบอกระยะ (Blue)
    'WARNING':     dict(color="#DC2626", width=2)                                  # สีเตือน (Red)
}

SETBACK = 15 # ระยะห่างมาตรฐานระหว่างคานกับเสา (mm)

# =============================================================================
# 🛠️ HELPER FUNCTIONS
# =============================================================================
def add_dim(fig, x0, y0, x1, y1, text, offset=30, type="h", color=STYLE['DIM']['color'], warning=False):
    """
    ฟังก์ชันเขียน Dimension แบบวิศวกรรม (Arrowhead + Extension Lines)
    warning=True จะเปลี่ยนสีเป็นแดงเพื่อเตือนว่าระยะนี้มีปัญหา
    """
    dim_color = "#DC2626" if warning else color
    ext_len = 5
    
    if type == "h": # แนวนอน
        y_pos = y0 + offset
        # Extension Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos+ext_len*np.sign(offset), line=dict(color=dim_color, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos+ext_len*np.sign(offset), line=dict(color=dim_color, width=0.5))
        # Dimension Line
        fig.add_annotation(x=x1, y=y_pos, ax=x0, ay=y_pos, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=dim_color, text="")
        # Text
        fig.add_annotation(x=(x0+x1)/2, y=y_pos+(10 if offset>0 else -10), text=f"<b>{text}</b>", showarrow=False, 
                           font=dict(size=11, color=dim_color, family="Arial"))
    
    else: # แนวตั้ง
        x_pos = x0 + offset
        # Extension Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos+ext_len*np.sign(offset), y1=y0, line=dict(color=dim_color, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos+ext_len*np.sign(offset), y1=y1, line=dict(color=dim_color, width=0.5))
        # Dimension Line
        fig.add_annotation(x=x_pos, y=y1, ax=x_pos, ay=y0, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=dim_color, text="")
        # Text
        fig.add_annotation(x=x_pos+(15 if offset>0 else -15), y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, textangle=-90,
                           font=dict(size=11, color=dim_color, family="Arial"))

def draw_bolt_side(fig, x_cen, y_cen, d, length, orientation="h"):
    """ วาด Bolt ด้านข้าง (เห็น Shank, Head, Nut) """
    head_h = d * 0.6
    nut_h = d * 0.8
    w_head = d * 1.6
    
    if orientation == "h": # แนวนอน (ใช้ใน Plan / Section)
        # Shank (แกนกลาง)
        fig.add_shape(type="rect", x0=x_cen-length/2, y0=y_cen-d/2, x1=x_cen+length/2, y1=y_cen+d/2,
                      fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
        # Head (Left)
        fig.add_shape(type="rect", x0=x_cen-length/2-head_h, y0=y_cen-w_head/2, x1=x_cen-length/2, y1=y_cen+w_head/2,
                      fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black", width=1))
        # Nut (Right)
        fig.add_shape(type="rect", x0=x_cen+length/2, y0=y_cen-w_head/2, x1=x_cen+length/2+nut_h, y1=y_cen+w_head/2,
                      fillcolor=STYLE['BOLT']['fillcolor'], line=dict(color="black", width=1))
        # Center Line
        fig.add_shape(type="line", x0=x_cen-length/2-head_h-5, y0=y_cen, x1=x_cen+length/2+nut_h+5, y1=y_cen, 
                      line=STYLE['CL'])

# =============================================================================
# 1. PLAN VIEW (TOP SECTION) - มองจากด้านบน
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    
    tw = beam['tw']
    tp, wp, e1 = plate['t'], plate['w'], plate['e1']
    col_tf = 12 # สมมติความหนาปีกเสา (Column Flange)
    
    # 1. Column Flange (ฐานยึด)
    fig.add_shape(type="rect", x0=-col_tf, y0=-80, x1=0, y1=80, 
                  fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
    
    # 2. Shear Plate (Fin Plate)
    fig.add_shape(type="rect", x0=0, y0=-tp/2, x1=wp, y1=tp/2, 
                  fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])

    # 3. Beam Web (ประกบข้าง) - ตัด Section
    # Beam Web จะเริ่มหลังจาก Setback
    web_len = wp - SETBACK + 20
    fig.add_shape(type="rect", x0=SETBACK, y0=tp/2, x1=SETBACK+web_len, y1=tp/2+tw,
                  fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
    
    # 4. Bolt Assembly (Correct Orientation: Side View of Bolt)
    # Bolt ทะลุผ่าน Plate และ Web (แกน Y)
    # ความยาว Bolt ที่ต้องใช้ = tp + tw + เผื่อ
    bolt_len = tp + tw + 10
    bolt_x = e1 # ระยะจากหน้าเสาถึง Bolt ตัวแรก
    
    # Bolt Center Y position (กึ่งกลางระหว่าง Plate และ Web)
    bolt_cen_y = tp/2 # ทางทฤษฎี Bolt center อยู่กึ่งกลางความหนารวมไม่ได้ ต้องทะลุ
    # วาด Bolt ขวางแกน Y (Vertical in this 2D plot context? No, Horizontal visually but vertical logical)
    # ใน Plan View: แกน X คือความยาวคาน, แกน Y คือความกว้าง
    # Bolt วางขวางแกน Y
    
    # วาด Bolt เป็นแท่งแนวตั้งในรูป (เพราะมันขวาง Beam Web)
    b_y_start = -tp/2 - 5 # Head position (Plate side)
    b_y_end = tp/2 + tw + 5 # Nut position (Web side)
    
    # Shank
    fig.add_shape(type="rect", x0=bolt_x-bolts['d']/2, y0=b_y_start, x1=bolt_x+bolts['d']/2, y1=b_y_end,
                  fillcolor=STYLE['BOLT']['fillcolor'], line=dict(width=0))
    # Head (Bottom/Plate Side)
    fig.add_shape(type="rect", x0=bolt_x-bolts['d'], y0=b_y_start-8, x1=bolt_x+bolts['d'], y1=b_y_start,
                  fillcolor="black", line=dict(width=0))
    # Nut (Top/Web Side)
    fig.add_shape(type="rect", x0=bolt_x-bolts['d'], y0=b_y_end, x1=bolt_x+bolts['d'], y1=b_y_end+10,
                  fillcolor="black", line=dict(width=0))
    # Center Line Bolt
    fig.add_shape(type="line", x0=bolt_x, y0=b_y_start-15, x1=bolt_x, y1=b_y_end+15, line=STYLE['CL'])

    # 5. Weld Symbol (Fillet at Junction)
    ws = plate['weld_size']
    fig.add_shape(type="path", path=f"M 0 {-tp/2} L {ws} {-tp/2} L 0 {-tp/2-ws} Z", fillcolor="black", line_width=0)
    fig.add_shape(type="path", path=f"M 0 {tp/2} L {ws} {tp/2} L 0 {tp/2+ws} Z", fillcolor="black", line_width=0)

    # 6. Dimensions
    add_dim(fig, 0, -tp/2-40, wp, -tp/2-40, f"W_pl={wp}", 20, "h")
    add_dim(fig, 0, tp/2+tw+40, bolt_x, tp/2+tw+40, f"e1={e1}", 30, "h")
    add_dim(fig, 0, 0, SETBACK, 0, f"{SETBACK}", -60, "h") # Setback
    
    # Layout Config
    fig.update_layout(title="<b>PLAN VIEW</b> (Section at Web)", 
                      height=400, plot_bgcolor="white",
                      margin=dict(l=50, r=50, t=80, b=50),
                      xaxis=dict(visible=False, scaleanchor="y"), 
                      yaxis=dict(visible=False))
    return fig

# =============================================================================
# 2. ELEVATION VIEW (FRONT) - รูปด้านหน้า
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    
    h_b = beam['h']
    h_pl, w_pl = plate['h'], plate['w']
    lv = plate['lv']
    sv, rows = bolts['s_v'], bolts['rows']
    e1, cols, sh = plate['e1'], bolts['cols'], bolts['s_h']
    
    # --- Check Clearance (Clash Detection) ---
    # คำนวณตำแหน่ง Bolt ล่างสุด
    y_top_bolt = h_pl/2 - lv
    y_bot_bolt = y_top_bolt - ((rows-1) * sv)
    edge_bottom = -h_pl/2
    
    actual_lev = y_bot_bolt - edge_bottom
    min_lev = 1.5 * bolts['d'] # กฎเหล็ก: ระยะขอบล่างต้อง > 1.5d
    
    is_clash = actual_lev < min_lev
    
    # 1. Column Limit
    fig.add_shape(type="line", x0=0, y0=-h_b/2-50, x1=0, y1=h_b/2+50, line=dict(color="black", width=3))
    
    # 2. Beam Web (Ghost)
    fig.add_shape(type="rect", x0=SETBACK, y0=-h_b/2, x1=w_pl+100, y1=h_b/2, 
                  line=dict(color="#E5E7EB", width=1), fillcolor="rgba(255,255,255,0)")
    
    # 3. Connection Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, 
                  fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])
    
    # 4. Bolts Pattern
    for c in range(cols):
        cx = e1 + (c * sh)
        for r in range(rows):
            cy = y_top_bolt - (r * sv)
            
            # Bolt Hole/Head
            fig.add_shape(type="circle", x0=cx-bolts['d']/2, y0=cy-bolts['d']/2, x1=cx+bolts['d']/2, y1=cy+bolts['d']/2,
                          fillcolor="white", line=dict(color="black", width=1.5))
            # Crosshair
            fig.add_shape(type="line", x0=cx-6, y0=cy, x1=cx+6, y1=cy, line=dict(color="black", width=0.5))
            fig.add_shape(type="line", x0=cx, y0=cy-6, x1=cx, y1=cy+6, line=dict(color="black", width=0.5))

    # 5. Dimensions & Warnings
    x_dim = w_pl + 30
    
    # Lv (Top Edge)
    add_dim(fig, x_dim, h_pl/2, x_dim, y_top_bolt, f"Lv={lv}", 10, "v")
    
    # Spacing (Pitch)
    if rows > 1:
        add_dim(fig, x_dim, y_top_bolt, x_dim, y_bot_bolt, f"Pitch={sv}x{rows-1}", 10, "v")
        
    # Lev (Bottom Edge) - Highlight RED if clash
    label_lev = f"Lev={actual_lev:.1f}" + (" ⚠️" if is_clash else "")
    add_dim(fig, x_dim, y_bot_bolt, x_dim, edge_bottom, label_lev, 10, "v", warning=is_clash)
    
    # Plate Height
    add_dim(fig, 0, h_pl/2, 0, -h_pl/2, f"H_pl={h_pl}", -40, "v")
    
    # Widths
    add_dim(fig, 0, -h_b/2-30, w_pl, -h_b/2-30, f"W_pl={w_pl}", 30, "h")
    
    # Warning Annotation Text
    if is_clash:
        fig.add_annotation(x=w_pl/2, y=-h_pl/2 - 20, text="⚠️ PLATE TOO SHORT!", 
                           showarrow=False, font=dict(color="red", size=14, weight="bold"))

    fig.update_layout(title="<b>ELEVATION VIEW</b> (Plate Detail)", 
                      height=600, plot_bgcolor="white",
                      margin=dict(l=80, r=80, t=80, b=80), # เพิ่ม Margin ไม่ให้รูปชิดขอบ
                      xaxis=dict(visible=False, scaleanchor="y", range=[-50, w_pl+100]), 
                      yaxis=dict(visible=False))
    return fig

# =============================================================================
# 3. SECTION VIEW (SIDE A-A) - รูปตัดขวาง
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl = plate['h']
    rows, sv, lv = bolts['rows'], bolts['s_v'], plate['lv']
    
    # 1. Column Section (H-Beam Background)
    col_d = h + 50 # สมมติเสาใหญ่กว่าคานนิดหน่อย
    col_b = b + 20
    col_tf = 12
    col_tw = 10
    
    # วาดเสาเป็นโครงเส้น (Wireframe) ด้านหลัง
    # Left Flange
    fig.add_shape(type="rect", x0=-col_b/2, y0=-col_d/2, x1=-col_b/2+col_tf, y1=col_d/2, 
                  fillcolor="#F3F4F6", line=dict(color="gray", width=1))
    # Right Flange
    fig.add_shape(type="rect", x0=col_b/2-col_tf, y0=-col_d/2, x1=col_b/2, y1=col_d/2, 
                  fillcolor="#F3F4F6", line=dict(color="gray", width=1))
    # Web
    fig.add_shape(type="rect", x0=-col_b/2, y0=-col_tw/2, x1=col_b/2, y1=col_tw/2, 
                  fillcolor="#F3F4F6", line=dict(color="gray", width=0)) # Web แนวนอนในรูปตัด? 
    # แก้ไข: รูปตัดนี้เรามองเข้าด้านข้างคาน ดังนั้นเราจะเห็น "ปีกเสา" เป็นแผ่นบังหลัง
    
    # เอาใหม่: Column Face (Surface)
    fig.add_shape(type="rect", x0=-col_b/2, y0=-col_d/2, x1=col_b/2, y1=col_d/2,
                  line=dict(color="gray", width=1, dash="dot")) # แสดงแนวเสาจางๆ

    # 2. Beam Section (Main) - I-Shape
    # Web
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf,
                  fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
    # Flanges
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2,
                  fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf,
                  fillcolor=STYLE['STEEL_CUT']['fillcolor'], line=STYLE['STEEL_CUT']['line'])

    # 3. Connection Plate (Side Edge)
    # Plate ยื่นออกมาจากเสา (ซึ่งอยู่ด้านหลัง) มาประกบ Web
    # ใน View นี้เราเห็นความหนา Web + Plate
    # Plate Position (Assumed Right Side of Web)
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+plate['t'], y1=h_pl/2,
                  fillcolor=STYLE['PLATE']['fillcolor'], line=STYLE['PLATE']['line'])

    # 4. Bolts (Side View passing through)
    y_start = h_pl/2 - lv
    bolt_len = b # ยาวเท่าความกว้างปีกคาน (สมมติเพื่อความสวยงามในรูป)
    
    for r in range(rows):
        y_bolt = y_start - (r * sv)
        # Center Line
        fig.add_shape(type="line", x0=-b/2-20, y0=y_bolt, x1=b/2+20, y1=y_bolt, line=STYLE['CL'])
        # Bolt
        draw_bolt_side(fig, tw/2 + plate['t']/2, y_bolt, bolts['d'], tw+plate['t']+25, "h")

    # 5. Dimensions
    # Beam Depth
    add_dim(fig, -b/2-40, h/2, -b/2-40, -h/2, f"D={h}", 40, "v")
    # Beam Width
    add_dim(fig, -b/2, h/2+20, b/2, h/2+20, f"B={b}", 30, "h")
    # Plate Height Relative to Beam
    add_dim(fig, b/2+40, h_pl/2, b/2+40, -h_pl/2, f"Hp={h_pl}", 30, "v")

    fig.update_layout(title="<b>SECTION A-A</b> (Beam Cross Section)", 
                      height=600, plot_bgcolor="white",
                      margin=dict(l=80, r=80, t=80, b=80),
                      xaxis=dict(visible=False, scaleanchor="y"), 
                      yaxis=dict(visible=False))
    return fig

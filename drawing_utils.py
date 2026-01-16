import plotly.graph_objects as go

# =============================================================================
# 🎨 PROFESSIONAL COLOR PALETTE (Industry Standard)
# =============================================================================
C_STEEL_DARK = "#1e293b"    # ขอบเหล็กเข้ม
C_STEEL_LIGHT = "#f8fafc"   # สีผิวเหล็ก (Galvanized look)
C_PLATE = "#0284c7"         # สีเพลท (Deep Sky Blue)
C_BOLT = "#be123c"          # สีโบลท์ (Crimson)
C_WELD = "#94a3b8"          # สีรอยเชื่อม
C_DIM = "#334155"           # สีเส้น Dimension
C_YELLOW_COL = "#eab308"    # เส้นขอบเขตเสา (Yellow Line)

# =============================================================================
# 🛠️ ADVANCED HELPERS
# =============================================================================
def add_weld_symbol(fig, x, y, size=8, side="left"):
    """ วาดสัญลักษณ์รอยเชื่อม Fillet Weld """
    sign = -1 if side == "left" else 1
    fig.add_trace(go.Scatter(
        x=[x, x, x + (sign * size), x],
        y=[y - size, y, y, y - size],
        fill="toself", fillcolor=C_WELD, line=dict(color=C_STEEL_DARK, width=0.5),
        mode='lines', hoverinfo='skip', showlegend=False
    ))

def get_i_section_path(x_center, y_center, h, b, tf, tw, r=10):
    """ สร้างเส้นรอบรูป I-Section แบบมี Root Radius (ความโค้งโคนปีก) """
    # คำนวณพิกัดจุดโค้งเพื่อให้เหมือนเหล็กจริงที่สุด
    return (f"M {x_center-b/2},{y_center-h/2} L {x_center+b/2},{y_center-h/2} "
            f"L {x_center+b/2},{y_center-h/2+tf} L {x_center+tw/2+r},{y_center-h/2+tf} "
            f"Q {x_center+tw/2},{y_center-h/2+tf} {x_center+tw/2},{y_center-h/2+tf+r} "
            f"L {x_center+tw/2},{y_center+h/2-tf-r} "
            f"Q {x_center+tw/2},{y_center+h/2-tf} {x_center+tw/2+r},{y_center+h/2-tf} "
            f"L {x_center+b/2},{y_center+h/2-tf} L {x_center+b/2},{y_center+h/2} "
            f"L {x_center-b/2},{y_center+h/2} L {x_center-b/2},{y_center+h/2-tf} "
            f"L {x_center-tw/2-r},{y_center+h/2-tf} "
            f"Q {x_center-tw/2},{y_center+h/2-tf} {x_center-tw/2},{y_center+h/2-tf-r} "
            f"L {x_center-tw/2},{y_center-h/2+tf+r} "
            f"Q {x_center-tw/2},{y_center-h/2+tf} {x_center-tw/2-r},{y_center-h/2+tf} "
            f"L {x_center-b/2},{y_center-h/2+tf} Z")

# =============================================================================
# 3. SIDE VIEW (SECTION) - อัปเกรดความละเอียดสูงสุด
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl, t_pl = plate['h'], plate['t']
    lv = plate.get('lv', bolts.get('lv', 35))
    n_rows, s_v = bolts['rows'], bolts['s_v']

    # --- 1. COLUMN BOUNDARY (เส้นเหลือง - ความกว้างเสา) ---
    b_col = b + 40
    fig.add_shape(type="rect", x0=-b_col/2, y0=-h/2-60, x1=b_col/2, y1=h/2+60, 
                  line=dict(color=C_YELLOW_COL, width=2.5, dash="dash"), fillcolor="rgba(248, 250, 252, 0.5)")

    # --- 2. BEAM I-SECTION WITH ROOT RADIUS ---
    beam_path = get_i_section_path(0, 0, h, b, tf, tw, r=12)
    fig.add_shape(type="path", path=beam_path, fillcolor=C_STEEL_LIGHT, line=dict(color=C_STEEL_DARK, width=2))

    # --- 3. SHEAR PLATE & BOLTS ---
    # ระยะ Clearance ระหว่าง Web กับ Plate (สมมติ 2mm)
    p_x0 = tw/2
    p_x1 = p_x0 + t_pl
    fig.add_shape(type="rect", x0=p_x0, y0=-h_pl/2, x1=p_x1, y1=h_pl/2, 
                  fillcolor=C_PLATE, line=dict(color=C_STEEL_DARK, width=1.5))
    
    # วาด Bolt พร้อมหัวน็อตและแหวน (Hex Bolt Detail)
    for i in range(n_rows):
        y_bolt = h_pl/2 - lv - (i * s_v)
        # Shank
        fig.add_shape(type="rect", x0=p_x1, y0=y_bolt-5, x1=p_x1+15, y1=y_bolt+5, fillcolor=C_BOLT, line_width=0.5)
        # Nut
        fig.add_shape(type="rect", x0=p_x1+10, y0=y_bolt-8, x1=p_x1+18, y1=y_bolt+8, fillcolor="#4b5563", line_width=1)

    # --- 4. WELDING DETAILS ---
    # รอยเชื่อมระหว่าง Plate กับหน้าเสา (ตามที่คุณอธิบายว่า Plate เชื่อมเสา)
    add_weld_symbol(fig, p_x0, h_pl/2, size=10, side="left")
    add_weld_symbol(fig, p_x0, -h_pl/2 + 10, size=10, side="left")

    # --- 5. DIMENSIONING ---
    from drawing_utils import add_cad_dim # เรียกใช้ฟังก์ชันเดิมของคุณ
    add_cad_dim(fig, -b/2, h/2+15, b/2, h/2+15, f"BEAM B={int(b)}", offset=25)
    add_cad_dim(fig, b/2+25, h/2, b/2+25, -h/2, f"BEAM H={int(h)}", "vert", offset=40)

    fig.update_layout(
        title=dict(text="<b>DETAILED SECTION VIEW</b>", font=dict(size=16)),
        plot_bgcolor="white", height=500, width=500,
        xaxis=dict(visible=False, range=[-b_col*0.8, b_col*1.2]),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

# หมายเหตุ: สำหรับ create_plan_view และ create_front_view ให้คงโค้ดเดิมไว้ 
# เพื่อความเสถียรของแอปพลิเคชัน

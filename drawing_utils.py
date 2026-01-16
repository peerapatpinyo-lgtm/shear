# drawing_utils.py (V23 - World-Class Detailing Edition)
import plotly.graph_objects as go

# --- Global Engineering Standards ---
THEME = {
    "steel": "#263238", "plate": "#1976D2", "bolt": "#D32F2F",
    "dim": "#37474F", "bg": "#FFFFFF", "beam_fill": "#ECEFF1"
}

def add_break_line(fig, x, y_start, y_end):
    """วาดเส้น Break Line (เส้นหยัก) สัญลักษณ์สากลสำหรับชิ้นส่วนที่ยาวต่อเนื่อง"""
    mid_y = (y_start + y_end) / 2
    amp = 10
    path = f"M {x},{y_start} L {x},{mid_y+10} L {x-amp},{mid_y+5} L {x+amp},{mid_y-5} L {x},{mid_y-10} L {x},{y_end}"
    fig.add_shape(type="path", path=path, line=dict(color=THEME["steel"], width=2))

def add_running_dim(fig, x_base, y_coords, labels, axis="V", offset=80):
    """ฟังก์ชันให้ระยะแบบ Running Dimension (ระยะสะสม) ตามมาตรฐานสากล"""
    for i, y in enumerate(y_coords):
        # เส้นขีดบอกตำแหน่ง
        fig.add_shape(type="line", x0=x_base, y0=y, x1=x_base+offset+10, y1=y, line=dict(color=THEME["dim"], width=1))
        # ข้อความบอกระยะ
        fig.add_annotation(x=x_base+offset, y=y, text=f"{labels[i]}", showarrow=False, xshift=20, font=dict(size=10))
    # เส้นเชื่อมแนวดิ่ง
    fig.add_shape(type="line", x0=x_base+offset, y0=min(y_coords), x1=x_base+offset, y1=max(y_coords), line=dict(color=THEME["dim"], width=1.2))

# --- 1. FRONT VIEW (เน้นระยะขอบที่ปลอดภัยและการให้ระยะละเอียด) ---
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_pl, w_pl, s_v, rows = plate['h'], plate['w'], bolts['s_v'], bolts['rows']
    
    # 1.1 คำนวณระยะขอบที่ปลอดภัย (Safe Edge Distance)
    total_pitch = (rows - 1) * s_v
    edge_v = (h_pl - total_pitch) / 2 
    
    # 1.2 วาด Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, 
                  fillcolor="rgba(25,118,210,0.1)", line=dict(color=THEME["plate"], width=2))

    # 1.3 วาดโบลท์และให้ระยะ Running Dimension
    bolt_y_coords = [ (h_pl/2 - edge_v) - i*s_v for i in range(rows) ]
    for by in bolt_y_coords:
        fig.add_shape(type="circle", x0=plate['e1']-8, y0=by-8, x1=plate['e1']+8, y1=by+8, fillcolor=THEME["bolt"])

    # แสดง Running Dimension ข้าง Plate
    labels = [f"0", f"{edge_v:.0f}", f"{edge_v+s_v:.0f}", f"{h_pl:.0f}"]
    add_running_dim(fig, w_pl, [h_pl/2, h_pl/2-edge_v, h_pl/2-edge_v-s_v, -h_pl/2], labels)

    fig.update_layout(title="FRONT ELEVATION (DETAILED)", xaxis=dict(visible=False, range=[-50, 250]), 
                      yaxis=dict(visible=False, scaleanchor="x"), plot_bgcolor=THEME["bg"])
    return fig

# --- 2. SIDE VIEW (เพิ่ม Break Line และ Column Support) ---
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw, t_pl, h_pl = beam['h'], beam['b'], beam['tf'], beam['tw'], plate['t'], plate['h']

    # 2.1 วาดเสาด้านหลัง (Column Flange)
    col_x = -b/2 - 50
    fig.add_shape(type="line", x0=col_x, y0=-h/2-100, x1=col_x, y1=h/2+100, line=dict(color=THEME["steel"], width=3))
    fig.add_shape(type="line", x0=col_x+12, y0=-h/2-100, x1=col_x+12, y1=h/2+100, line=dict(color=THEME["steel"], width=1.5))

    # 2.2 วาด I-Beam พร้อม Break Line ด้านขวา (ตามที่คุณวาดมา)
    # วาด Flanges และ Web
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, fillcolor=THEME["beam_fill"])
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, fillcolor=THEME["beam_fill"])
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, fillcolor=THEME["beam_fill"])
    
    # วาด Plate แปะข้าง Web
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=THEME["plate"])

    # 2.3 เพิ่มสัญลักษณ์แนวเชื่อม (Welding Symbol Callout)
    fig.add_annotation(x=tw/2, y=h_pl/2, text="Fillet 6mm (E70XX)", showarrow=True, arrowhead=2, ax=-40, ay=-40)

    # 2.4 วาด Break Line (เส้นหยักบอกส่วนต่อ)
    add_break_line(fig, b/2 + 20, h/2, -h/2)

    fig.update_layout(title="SECTIONAL VIEW (WITH BREAK LINE)", xaxis=dict(visible=False, range=[col_x-50, b/2+100]), 
                      yaxis=dict(visible=False, scaleanchor="x"), plot_bgcolor=THEME["bg"])
    return fig

import plotly.graph_objects as go

# ==========================================
# 🎨 STYLES & CONSTANTS
# ==========================================
COLORS = {
    'STEEL_CUT': "#9CA3AF",    # สีเนื้อเหล็กตัด
    'STEEL_FACE': "#F3F4F6",   # สีผิวเหล็ก
    'PLATE': "#DBEAFE",        # สีแผ่นเพลท
    'BOLT': "#374151",         # สีโบลท์
    'DIM': "#1e40af",          # สีเส้นบอกระยะ
    'WELD': "#000000"          # สีงานเชื่อม
}

# ==========================================
# 🛠️ DIMENSION HELPER
# ==========================================
def draw_dim(fig, x0, y0, x1, y1, text, offset=30, type="h"):
    """
    วาดเส้นบอกระยะแบบ Construction (มีขีดหัวท้าย)
    type: 'h' (แนวนอน), 'v' (แนวตั้ง)
    """
    c = COLORS['DIM']
    tick_len = 5
    
    if type == "h":
        y_pos = y0 + offset
        # Main Line
        fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=c, width=1))
        # Ticks (Left & Right)
        fig.add_shape(type="line", x0=x0, y0=y_pos-tick_len, x1=x0, y1=y_pos+tick_len, line=dict(color=c, width=1))
        fig.add_shape(type="line", x0=x1, y0=y_pos-tick_len, x1=x1, y1=y_pos+tick_len, line=dict(color=c, width=1))
        # Extension Lines (From Object to Dim Line)
        ext_dir = 1 if offset > 0 else -1
        gap = 5 * ext_dir
        fig.add_shape(type="line", x0=x0, y0=y0+gap, x1=x0, y1=y_pos, line=dict(color=c, width=0.5, dash='dot'))
        fig.add_shape(type="line", x0=x1, y0=y1+gap, x1=x1, y1=y_pos, line=dict(color=c, width=0.5, dash='dot'))
        # Text
        fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=f"<b>{text}</b>", showarrow=False, yshift=10*ext_dir, font=dict(color=c, size=11))

    else: # Vertical
        x_pos = x0 + offset
        # Main Line
        fig.add_shape(type="line", x0=x_pos, y0=y0, x1=x_pos, y1=y1, line=dict(color=c, width=1))
        # Ticks
        fig.add_shape(type="line", x0=x_pos-tick_len, y0=y0, x1=x_pos+tick_len, y1=y0, line=dict(color=c, width=1))
        fig.add_shape(type="line", x0=x_pos-tick_len, y0=y1, x1=x_pos+tick_len, y1=y1, line=dict(color=c, width=1))
        # Extension
        ext_dir = 1 if offset > 0 else -1
        gap = 5 * ext_dir
        fig.add_shape(type="line", x0=x0+gap, y0=y0, x1=x_pos, y1=y0, line=dict(color=c, width=0.5, dash='dot'))
        fig.add_shape(type="line", x0=x1+gap, y0=y1, x1=x_pos, y1=y1, line=dict(color=c, width=0.5, dash='dot'))
        # Text
        fig.add_annotation(x=x_pos, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=10*ext_dir, textangle=-90, font=dict(color=c, size=11))

def draw_weld_symbol(fig, x, y, size, length=None, orient="right"):
    """
    วาดสัญลักษณ์การเชื่อม (Weld Symbol) ชี้ไปที่ตำแหน่ง x,y
    """
    ax = 40 if orient == "right" else -40
    text_label = f"Fillet {size}mm"
    if length: text_label += f" (L={length})"
    
    fig.add_annotation(
        x=x, y=y, ax=ax, ay=-30,
        text=f"<b>{text_label}</b>",
        showarrow=True, arrowhead=2, arrowsize=1,
        bgcolor="white", bordercolor="black", borderwidth=1
    )

def setup_canvas(fig, limit):
    fig.update_layout(
        xaxis=dict(visible=False, range=[-limit, limit], scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False, range=[-limit, limit]),
        plot_bgcolor="white",
        margin=dict(l=20, r=20, t=50, b=20),
        height=500
    )

# ==========================================
# 1. FRONT VIEW (ELEVATION)
# ==========================================
def create_front_view(beam, plate, inp):
    fig = go.Figure()
    
    # Unpack inputs
    h_pl, w_pl = plate['h'], plate['w']
    rows, cols = inp['rows'], inp['cols']
    sv, sh = inp['s_v'], inp['s_h']
    lv, leh = inp['lv'], inp['leh'] # Edge distances
    e1 = inp['e1']
    sb = inp['setback']
    weld_sz = inp['weld_size']
    
    # 1. Draw Beam Limits (Visual context)
    fig.add_shape(type="rect", x0=sb, y0=-beam['h']/2, x1=sb+w_pl+300, y1=beam['h']/2, 
                  fillcolor=COLORS['STEEL_FACE'], line=dict(width=0))
    fig.add_shape(type="line", x0=sb, y0=-beam['h']/2, x1=sb+w_pl+300, y1=-beam['h']/2, line=dict(color="black", width=1))
    fig.add_shape(type="line", x0=sb, y0=beam['h']/2, x1=sb+w_pl+300, y1=beam['h']/2, line=dict(color="black", width=1))
    
    # 2. Draw Column Line
    fig.add_shape(type="line", x0=0, y0=-beam['h']/2-100, x1=0, y1=beam['h']/2+100, 
                  line=dict(color="black", width=3)) # Column Face

    # 3. Draw Plate
    if "Fin" in plate['type']:
        # Fin Plate starts at Column Face (0)
        fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, 
                      fillcolor=COLORS['PLATE'], line=dict(color="blue", width=2))
        
        # Weld (Vertical Line at 0)
        fig.add_shape(type="line", x0=0, y0=-h_pl/2, x1=0, y1=h_pl/2, line=dict(color="black", width=4))
        draw_weld_symbol(fig, 0, h_pl/4, weld_sz, orient="left")
        
        # Bolt Holes
        start_y = h_pl/2 - lv
        start_x = e1 # For Fin, e1 is from Column Face usually? Or from Plate Edge? 
        # Standard: e1 is from Bolt to Beam End. But for Fin layout, usually define distance from Col.
        # Let's assume w_pl is calculated to cover everything.
        # Draw bolts based on w_pl - leh (Right Edge)
        
        # Let's re-calculate coordinates relative to Plate Origin (0,0)
        # Bolt Group Center X
        bg_width = (cols-1)*sh
        first_bolt_x = w_pl - leh - bg_width
        
        for c in range(cols):
            bx = first_bolt_x + (c*sh)
            for r in range(rows):
                by = start_y - (r*sv)
                fig.add_shape(type="circle", x0=bx-inp['d']/2, y0=by-inp['d']/2, x1=bx+inp['d']/2, y1=by+inp['d']/2, 
                              fillcolor="white", line=dict(color="black"))
                # Bolt Cross
                fig.add_shape(type="line", x0=bx-2, y0=by, x1=bx+2, y1=by, line=dict(color="black", width=1))
                fig.add_shape(type="line", x0=bx, y0=by-2, x1=bx, y1=by+2, line=dict(color="black", width=1))

        # Dimensions
        draw_dim(fig, 0, -h_pl/2-20, w_pl, -h_pl/2-20, f"W={w_pl}", -20, "h")
        draw_dim(fig, w_pl+20, h_pl/2, w_pl+20, -h_pl/2, f"H={h_pl}", 20, "v")
        draw_dim(fig, w_pl+50, h_pl/2, w_pl+50, start_y, f"Lv={lv}", 10, "v")
        if rows > 1:
            draw_dim(fig, w_pl+50, start_y, w_pl+50, start_y - (rows-1)*sv, f"{rows-1}@{sv}", 10, "v")

    elif "End" in plate['type']:
        # End Plate (Centered at Beam End, but Beam End is at Setback usually?)
        # Let's assume View is looking at End Plate Face
        fig.add_shape(type="rect", x0=-w_pl/2, y0=-h_pl/2, x1=w_pl/2, y1=h_pl/2, 
                      fillcolor=COLORS['PLATE'], line=dict(color="blue", width=2))
        
        # Bolts (Gauge centered)
        start_y = h_pl/2 - lv
        for s in [-1, 1]:
            bx = s * sh / 2
            for r in range(rows):
                by = start_y - (r*sv)
                fig.add_shape(type="circle", x0=bx-inp['d']/2, y0=by-inp['d']/2, x1=bx+inp['d']/2, y1=by+inp['d']/2, 
                              fillcolor="white", line=dict(color="black"))

        # Dimensions
        draw_dim(fig, -w_pl/2, -h_pl/2-20, w_pl/2, -h_pl/2-20, f"W={w_pl}", -20, "h")
        draw_dim(fig, -sh/2, -h_pl/2-50, sh/2, -h_pl/2-50, f"Gauge={sh}", -20, "h")
        draw_dim(fig, w_pl/2+20, h_pl/2, w_pl/2+20, -h_pl/2, f"H={h_pl}", 20, "v")
        
    fig.update_layout(title="<b>FRONT VIEW (ELEVATION)</b>")
    setup_canvas(fig, max(h_pl, beam['h']))
    return fig

# ==========================================
# 2. SIDE VIEW (SECTION)
# ==========================================
def create_side_view(beam, plate, inp):
    fig = go.Figure()
    
    tp = inp['t']
    h_beam = beam['h']
    
    # 1. Draw Column (Left Side)
    col_d = 300 # Mockup Column Depth
    fig.add_shape(type="rect", x0=-col_d, y0=-h_beam/2-100, x1=0, y1=h_beam/2+100, 
                  fillcolor="#E5E7EB", line=dict(width=0)) # Column Body
    fig.add_shape(type="line", x0=0, y0=-h_beam/2-100, x1=0, y1=h_beam/2+100, line=dict(width=2)) # Col Face

    if "End" in plate['type']:
        # End Plate is flush with Column
        fig.add_shape(type="rect", x0=0, y0=-plate['h']/2, x1=tp, y1=plate['h']/2, 
                      fillcolor=COLORS['PLATE'], line=dict(width=1))
        
        # Beam starts after Plate
        beam_start = tp
        fig.add_shape(type="rect", x0=beam_start, y0=-h_beam/2, x1=beam_start+400, y1=h_beam/2,
                      fillcolor=COLORS['STEEL_CUT'], line=dict(width=0))
        # Beam Flanges
        tf = beam['tf']
        fig.add_shape(type="rect", x0=beam_start, y0=h_beam/2-tf, x1=beam_start+400, y1=h_beam/2, fillcolor="black")
        fig.add_shape(type="rect", x0=beam_start, y0=-h_beam/2, x1=beam_start+400, y1=-h_beam/2+tf, fillcolor="black")

        # Weld (Beam to Plate)
        draw_weld_symbol(fig, beam_start, h_beam/2+20, inp['weld_size'], orient="right")
        
        # Bolts passing through
        start_y = plate['h']/2 - inp['lv']
        for r in range(inp['rows']):
            by = start_y - (r*inp['s_v'])
            fig.add_shape(type="rect", x0=-20, y0=by-inp['d']/2, x1=tp+20, y1=by+inp['d']/2, fillcolor=COLORS['BOLT'])

    else: # Fin Plate
        # Plate comes out of Column
        fig.add_shape(type="rect", x0=0, y0=-plate['h']/2, x1=plate['w'], y1=plate['h']/2,
                      fillcolor=COLORS['PLATE'], line=dict(color="blue", width=1))
        
        # Beam starts at Setback
        sb = inp['setback']
        beam_x = sb
        # Draw Beam Web Cut
        fig.add_shape(type="rect", x0=beam_x, y0=-h_beam/2, x1=beam_x+400, y1=h_beam/2, 
                      fillcolor=COLORS['STEEL_CUT'], opacity=0.3)
        
        # Bolts passing through
        bg_width = (inp['cols']-1)*inp['s_h']
        first_bolt = plate['w'] - inp['leh'] - bg_width
        start_y = plate['h']/2 - inp['lv']
        
        for c in range(inp['cols']):
            bx = first_bolt + (c*inp['s_h'])
            for r in range(inp['rows']):
                by = start_y - (r*inp['s_v'])
                fig.add_shape(type="rect", x0=bx-inp['d']/2, y0=by-10, x1=bx+inp['d']/2, y1=by+10, fillcolor=COLORS['BOLT'])

        # Dimensions
        draw_dim(fig, 0, -plate['h']/2-50, sb, -plate['h']/2-50, f"Gap={sb}", -20, "h")
        draw_dim(fig, sb, -plate['h']/2-50, first_bolt, -plate['h']/2-50, f"e1={inp['e1']}", -20, "h")

    fig.update_layout(title="<b>SIDE VIEW (SECTION)</b>")
    setup_canvas(fig, h_beam)
    return fig

# ==========================================
# 3. PLAN VIEW
# ==========================================
def create_plan_view(beam, plate, inp):
    fig = go.Figure()
    
    tp = inp['t']
    w_pl = plate['w']
    tw = beam['tw']
    
    # Column Top View
    col_w = 300
    fig.add_shape(type="rect", x0=-col_w/2, y0=-20, x1=col_w/2, y1=0, fillcolor="black") # Flange
    
    if "Fin" in plate['type']:
        # Fin Plate from Col center
        fig.add_shape(type="rect", x0=-tp/2, y0=0, x1=tp/2, y1=w_pl, fillcolor=COLORS['PLATE'], line=dict(color="blue"))
        
        # Beam Web (shifted by setback)
        sb = inp['setback']
        # Beam Web (Top/Bot of Fin) -> Actually Fin is usually welded to Col Flange or Web.
        # Let's assume Fin is welded to Col Flange center.
        
        # Beam Web next to Fin
        fig.add_shape(type="rect", x0=tp/2, y0=sb, x1=tp/2+tw, y1=sb+400, fillcolor=COLORS['STEEL_CUT'])
        
        # Dimensions
        draw_dim(fig, tp/2+tw+20, 0, tp/2+tw+20, sb, f"Gap={sb}", 20, "v")
        draw_dim(fig, tp/2+tw+20, sb, tp/2+tw+20, w_pl, f"Lap={w_pl-sb}", 20, "v")
        
    fig.update_layout(title="<b>PLAN VIEW</b>")
    setup_canvas(fig, w_pl+100)
    return fig

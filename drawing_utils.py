# drawing_utils.py (V16 - Global Presentation Edition)
import plotly.graph_objects as go

# --- Global Style & Colors for World-Class Presentation ---
COLOR_PALETTE = {
    "background": "#FFFFFF",      # Clean White Background
    "steel_main": "#263238",      # Dark Grey for Structural Steel (Deep)
    "steel_accent": "#ECEFF1",    # Light Grey for Beam Body (Subtle)
    "plate_highlight": "#0288D1", # Deep Sky Blue for Connection Plates
    "bolt_accent": "#D84315",     # Orange-Red for Bolts
    "dimension_line": "#607D8B",  # Slate Grey for Dimensions
    "center_line": "#E53935",     # Red for Centerlines
    "text_dark": "#212121",       # Dark text
    "text_light": "#B0BEC5",      # Light text for subtle notes
}
LINE_WEIGHTS = {
    "main_outline": 2.5,
    "secondary_outline": 1.5,
    "dimension": 1.0,
    "centerline": 1.0,
    "hidden": 1.0,
}
FONT_SETTINGS = {
    "family": "Arial, sans-serif",
    "size_title": 18,
    "size_label": 14,
    "size_dim": 12,
}

# --- Helper Function for Professional Dimensions ---
def add_dimension_line(fig, x0, y0, x1, y1, text, orientation="horizontal", offset_dist=80):
    """Adds a professional dimension line with extension lines and tick marks."""
    if orientation == "horizontal":
        y_dim_line = y0 + offset_dist
        # Extension lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_dim_line + (10 if offset_dist>0 else -10), line=dict(color=COLOR_PALETTE["dimension_line"], width=LINE_WEIGHTS["dimension"]))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_dim_line + (10 if offset_dist>0 else -10), line=dict(color=COLOR_PALETTE["dimension_line"], width=LINE_WEIGHTS["dimension"]))
        # Main dimension line
        fig.add_shape(type="line", x0=x0, y0=y_dim_line, x1=x1, y1=y_dim_line, line=dict(color=COLOR_PALETTE["dimension_line"], width=LINE_WEIGHTS["dimension"]))
        # Tick marks (Engineering style)
        for x_tick in [x0, x1]:
            fig.add_shape(type="line", x0=x_tick-5, y0=y_dim_line-5, x1=x_tick+5, y1=y_dim_line+5, line=dict(color=COLOR_PALETTE["dimension_line"], width=LINE_WEIGHTS["dimension"]+0.5))
        # Text label
        fig.add_annotation(x=(x0+x1)/2, y=y_dim_line, text=f"<b>{text}</b>", showarrow=False, yshift=15 if offset_dist>0 else -15, 
                           font=dict(size=FONT_SETTINGS["size_dim"], color=COLOR_PALETTE["text_dark"], family=FONT_SETTINGS["family"]), bgcolor=COLOR_PALETTE["background"])
    else: # vertical
        x_dim_line = x0 + offset_dist
        # Extension lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_dim_line + (10 if offset_dist>0 else -10), y1=y0, line=dict(color=COLOR_PALETTE["dimension_line"], width=LINE_WEIGHTS["dimension"]))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_dim_line + (10 if offset_dist>0 else -10), y1=y1, line=dict(color=COLOR_PALETTE["dimension_line"], width=LINE_WEIGHTS["dimension"]))
        # Main dimension line
        fig.add_shape(type="line", x0=x_dim_line, y0=y0, x1=x_dim_line, y1=y1, line=dict(color=COLOR_PALETTE["dimension_line"], width=LINE_WEIGHTS["dimension"]))
        # Tick marks
        for y_tick in [y0, y1]:
            fig.add_shape(type="line", x0=x_dim_line-5, y0=y_tick-5, x1=x_dim_line+5, y1=y_tick+5, line=dict(color=COLOR_PALETTE["dimension_line"], width=LINE_WEIGHTS["dimension"]+0.5))
        # Text label
        fig.add_annotation(x=x_dim_line, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=20 if offset_dist>0 else -20, 
                           textangle=-90, font=dict(size=FONT_SETTINGS["size_dim"], color=COLOR_PALETTE["text_dark"], family=FONT_SETTINGS["family"]), bgcolor=COLOR_PALETTE["background"])

def add_centerline(fig, x0, y0, x1, y1):
    fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color=COLOR_PALETTE["center_line"], width=LINE_WEIGHTS["centerline"], dash="dashdot"), opacity=0.7)

def add_weld_symbol(fig, x, y, size="6", orientation="left"):
    """Adds a simplified weld symbol for clarity."""
    fig.add_shape(type="line", x0=x, y0=y, x1=x+30, y1=y, line=dict(color=COLOR_PALETTE["text_dark"], width=1.5))
    if orientation == "left":
        fig.add_shape(type="path", path=f"M {x}, {y} L {x-10}, {y-10} L {x+20}, {y-10}", fillcolor=COLOR_PALETTE["text_dark"], line_width=0)
        fig.add_annotation(x=x-20, y=y-15, text=f"E70XX-F{size}", font=dict(size=10), showarrow=False)
    else: # right
        fig.add_shape(type="path", path=f"M {x}, {y} L {x+10}, {y-10} L {x-20}, {y-10}", fillcolor=COLOR_PALETTE["text_dark"], line_width=0)
        fig.add_annotation(x=x+20, y=y-15, text=f"E70XX-F{size}", font=dict(size=10), showarrow=False)


# =============================================================================
# 1. PLAN VIEW (World-Class Presentation)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf = beam['tw'], beam['b']
    w_pl, t_pl, e1, s_h, l_side = plate['w'], plate['t'], plate['e1'], bolts['s_h'], plate['l_side']
    
    # Dynamic Viewport Calculation (More intelligent padding)
    max_x = max(w_pl, 150) + 150 # Ensure enough space for dimensions
    max_y = bf/2 + 150
    
    # Column Flange (Deep Steel)
    fig.add_shape(type="rect", x0=-40, y0=-bf/2, x1=0, y1=bf/2, fillcolor=COLOR_PALETTE["steel_main"], line=dict(color=COLOR_PALETTE["steel_main"], width=LINE_WEIGHTS["main_outline"]))
    
    # Beam Web (Subtle grey)
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+100, y1=tw/2, fillcolor=COLOR_PALETTE["steel_accent"], line=dict(color=COLOR_PALETTE["steel_main"], width=LINE_WEIGHTS["secondary_outline"]))
    
    # Shear Plate (Highlight Blue)
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=COLOR_PALETTE["plate_highlight"], line=dict(color=COLOR_PALETTE["steel_main"], width=LINE_WEIGHTS["secondary_outline"]))

    # Bolts (Orange-Red, with proper head proportion)
    for i in range(bolts['cols']):
        bx = e1 + i*s_h
        # Bolt shank
        fig.add_shape(type="rect", x0=bx-bolts['d']/2, y0=-tw/2-5, x1=bx+bolts['d']/2, y1=tw/2+t_pl+5, fillcolor=COLOR_PALETTE["bolt_accent"], line_width=0)
        # Bolt head (Hexagonal approximation for Plan View)
        bolt_head_width = bolts['d'] * 1.5 # Standard hex head width
        bolt_head_thick = bolts['d'] * 0.7 # Standard hex head thickness
        fig.add_shape(type="rect", x0=bx-bolt_head_width/2, y0=tw/2+t_pl, x1=bx+bolt_head_width/2, y1=tw/2+t_pl+bolt_head_thick, 
                      fillcolor=COLOR_PALETTE["steel_main"], line=dict(color=COLOR_PALETTE["text_dark"], width=1))
        add_centerline(fig, bx, -max_y+20, bx, max_y-20) # Bolt Centerlines

    # Dimensions (Precisely placed)
    dim_y_offset = -bf/2 - 50
    add_dimension_line(fig, 0, dim_y_offset, e1, dim_y_offset, f"{e1:.0f}", "horizontal", offset_dist=0)
    if bolts['cols'] > 1:
        add_dimension_line(fig, e1, dim_y_offset, e1+s_h, dim_y_offset, f"{s_h:.0f}", "horizontal", offset_dist=0)
    add_dimension_line(fig, e1 + (bolts['cols']-1)*s_h, dim_y_offset, w_pl, dim_y_offset, f"{l_side:.0f}", "horizontal", offset_dist=0)
    add_dimension_line(fig, 0, dim_y_offset - 40, w_pl, dim_y_offset - 40, f"W_PL = {w_pl:.0f}", "horizontal", offset_dist=0)

    # Weld Symbol
    add_weld_symbol(fig, 0, tw/2+t_pl/2, "6", "left")

    fig.update_layout(
        title={"text": "<b>PLAN VIEW</b>", "x":0.05, "xanchor":"left"}, 
        plot_bgcolor=COLOR_PALETTE["background"], 
        height=500,
        xaxis=dict(visible=False, range=[-100, max_x], fixedrange=True),
        yaxis=dict(visible=False, range=[-max_y, max_y], scaleanchor="x", scaleratio=1, fixedrange=True), 
        margin=dict(l=50, r=50, t=80, b=80),
        font=dict(family=FONT_SETTINGS["family"], color=COLOR_PALETTE["text_dark"])
    )
    return fig

# =============================================================================
# 2. ELEVATION VIEW (World-Class Presentation)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_b, h_pl, w_pl, tw, tf = beam['h'], plate['h'], plate['w'], beam['tw'], beam['tf']
    e1, lv, s_v, s_h = plate['e1'], plate['lv'], bolts['s_v'], bolts['s_h']

    # Dynamic Viewport Calculation
    max_y = max(h_b, h_pl) + 150
    max_x = w_pl + 150

    # Column (Main Steel)
    fig.add_shape(type="rect", x0=-40, y0=-h_b/2-80, x1=0, y1=h_b/2+80, fillcolor=COLOR_PALETTE["steel_main"], line=dict(color=COLOR_PALETTE["steel_main"], width=LINE_WEIGHTS["main_outline"]))
    
    # Beam Profile (Hidden lines for main beam flanges)
    for y_beam_flange in [h_b/2, h_b/2-tf, -h_b/2+tf, -h_b/2]:
        fig.add_shape(type="line", x0=0, y0=y_beam_flange, x1=w_pl+100, y1=y_beam_flange, 
                      line=dict(color=COLOR_PALETTE["steel_main"], width=LINE_WEIGHTS["hidden"], dash="dot"))
    
    # Shear Plate (Highlight with slight transparency to show background grid)
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, 
                  fillcolor="rgba(2, 136, 209, 0.2)", line=dict(color=COLOR_PALETTE["plate_highlight"], width=LINE_WEIGHTS["main_outline"]))
    
    # Bolts (Orange-Red, with white center dot for clarity)
    for r in range(bolts['rows']):
        for c in range(bolts['cols']):
            bx, by = e1 + c*s_h, (h_pl/2 - lv) - r*s_v
            fig.add_shape(type="circle", x0=bx-bolts['d']/2, y0=by-bolts['d']/2, x1=bx+bolts['d']/2, y1=by+bolts['d']/2, 
                          fillcolor=COLOR_PALETTE["bolt_accent"], line=dict(color=COLOR_PALETTE["background"], width=1))
            # Center mark
            add_centerline(fig, bx-5, by, bx+5, by)
            add_centerline(fig, bx, by-5, bx, by+5)

    # Dimensions (Organized and readable)
    dim_x_offset = w_pl + 70
    add_dimension_line(fig, dim_x_offset, h_pl/2, dim_x_offset, h_pl/2-lv, f"{lv:.0f}", "vertical", offset_dist=0)
    for r_idx in range(bolts['rows'] - 1):
        y_start = h_pl/2 - lv - r_idx*s_v
        y_end = h_pl/2 - lv - (r_idx+1)*s_v
        add_dimension_line(fig, dim_x_offset, y_start, dim_x_offset, y_end, f"{s_v:.0f}", "vertical", offset_dist=0)
    add_dimension_line(fig, dim_x_offset + 50, h_pl/2, dim_x_offset + 50, -h_pl/2, f"H_PL = {h_pl:.0f}", "vertical", offset_dist=0)

    # Weld Symbol (Simplified)
    add_weld_symbol(fig, 0, h_pl/2-lv/2, "6", "left")

    fig.update_layout(
        title={"text": "<b>ELEVATION VIEW</b>", "x":0.05, "xanchor":"left"}, 
        plot_bgcolor=COLOR_PALETTE["background"], 
        height=500,
        xaxis=dict(visible=False, range=[-100, max_x], fixedrange=True),
        yaxis=dict(visible=False, range=[-max_y, max_y], scaleanchor="x", scaleratio=1, fixedrange=True), 
        margin=dict(l=50, r=50, t=80, b=80),
        font=dict(family=FONT_SETTINGS["family"], color=COLOR_PALETTE["text_dark"])
    )
    return fig

# =============================================================================
# 3. SECTION VIEW (World-Class Presentation)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl, t_pl = plate['h'], plate['t']

    # Dynamic Viewport Calculation
    max_dim = max(h, b) + 200

    # Beam Section (Precise SVG Path for I-shape)
    path_points = [
        f"M {-b/2},{-h/2}", f"L {b/2},{-h/2}", f"L {b/2},{-h/2+tf}", 
        f"L {tw/2},{-h/2+tf}", f"L {tw/2},{h/2-tf}", f"L {b/2},{h/2-tf}", 
        f"L {b/2},{h/2}", f"L {-b/2},{h/2}", f"L {-b/2},{h/2-tf}", 
        f"L {-tw/2},{h/2-tf}", f"L {-tw/2},{-h/2+tf}", f"L {-b/2},{-h/2+tf}", "Z"
    ]
    fig.add_shape(type="path", path=" ".join(path_points), fillcolor=COLOR_PALETTE["steel_accent"], 
                  line=dict(color=COLOR_PALETTE["steel_main"], width=LINE_WEIGHTS["main_outline"]))
    
    # Shear Plate (Highlight color)
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, 
                  fillcolor=COLOR_PALETTE["plate_highlight"], line=dict(color=COLOR_PALETTE["steel_main"], width=LINE_WEIGHTS["secondary_outline"]))

    # Main Dimensions (Beam overall dimensions)
    add_dimension_line(fig, -b/2 - 70, h/2, -b/2 - 70, -h/2, f"H = {h:.0f}", "vertical", offset_dist=0)
    add_dimension_line(fig, -b/2, h/2 + 70, b/2, h/2 + 70, f"B = {b:.0f}", "horizontal", offset_dist=0)
    
    # Plate thickness dimension
    add_dimension_line(fig, tw/2+t_pl/2, h_pl/2 + 60, tw/2+t_pl/2, h_pl/2, f"t_PL={t_pl:.0f}", "vertical", offset_dist=-60)
    
    # Callout for Beam Section
    fig.add_annotation(x=0, y=h/2+50, text=f"W-BEAM {h}x{b}", showarrow=True, arrowhead=2, ax=0, ay=100, 
                       font=dict(size=FONT_SETTINGS["size_label"], family=FONT_SETTINGS["family"], color=COLOR_PALETTE["text_dark"]), bgcolor=COLOR_PALETTE["background"])

    fig.update_layout(
        title={"text": "<b>SECTION VIEW</b>", "x":0.05, "xanchor":"left"}, 
        plot_bgcolor=COLOR_PALETTE["background"], 
        height=500,
        xaxis=dict(visible=False, range=[-max_dim/2, max_dim/2], fixedrange=True),
        yaxis=dict(visible=False, range=[-max_dim/2, max_dim/2], scaleanchor="x", scaleratio=1, fixedrange=True), 
        margin=dict(l=50, r=50, t=80, b=80),
        font=dict(family=FONT_SETTINGS["family"], color=COLOR_PALETTE["text_dark"])
    )
    return fig

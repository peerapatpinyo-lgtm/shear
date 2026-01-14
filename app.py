import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE (PREMIUM V13)
# ==========================================
st.set_page_config(page_title="Beam Insight V13 (Deep Connection)", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }

    /* Highlight Card */
    .highlight-card { 
        background: linear-gradient(135deg, #ebf5fb 0%, #ffffff 100%);
        padding: 25px; border-radius: 12px; border-left: 6px solid #2e86c1; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 25px; 
    }
    
    /* Metric Box */
    .metric-box { 
        text-align: center; padding: 20px; background: white; 
        border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
        border-top: 5px solid #ccc; height: 100%; transition: all 0.3s ease;
    }
    .metric-box:hover { transform: translateY(-5px); box-shadow: 0 12px 20px rgba(0,0,0,0.1); }
    .big-num { font-size: 28px; font-weight: 800; color: #17202a; margin-bottom: 5px; }
    .sub-text { font-size: 16px; font-weight: 600; color: #566573; text-transform: uppercase; }
    
    /* Calc & Report */
    .mini-calc { background-color: #f8f9fa; border: 1px dashed #bdc3c7; border-radius: 6px; padding: 10px; margin-top: 12px; font-family: 'Courier New', monospace; font-size: 13px; color: #444; text-align: left; }
    .report-paper { background-color: #ffffff; padding: 40px; border: 1px solid #e5e7e9; box-shadow: 0 10px 30px rgba(0,0,0,0.08); border-radius: 2px; max-width: 900px; margin: auto; }
    .report-header { font-size: 20px; font-weight: 800; color: #1a5276; margin-top: 25px; border-bottom: 2px solid #a9cce3; padding-bottom: 8px; }
    .report-line { font-family: 'Courier New', monospace; font-size: 16px; margin-bottom: 8px; color: #2c3e50; border-bottom: 1px dotted #eee; }
    .conn-card { background-color: #fffbf0; padding: 20px; border-radius: 10px; border-left: 6px solid #f1c40f; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }
    
    /* Status Badge */
    .pass-badge { background-color: #d5f5e3; color: #196f3d; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .fail-badge { background-color: #fadbd8; color: #943126; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE & INPUTS
# ==========================================
steel_db = {
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8},
    "H 200x100x5.5x8":  {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295},
    "H 300x150x6.5x9":  {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481},
    "H 350x175x7x11":   {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775},
    "H 400x200x8x13":   {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190},
    "H 450x200x9x14":   {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490},
    "H 500x200x10x16":  {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910},
    "H 600x200x11x17":  {"h": 600, "b": 200, "tw": 11,  "tf": 17,  "Ix": 77600,  "Zx": 2590},
}

with st.sidebar:
    st.title("Beam Insight V13")
    st.caption("Deep Connection Edition")
    st.divider()
    
    st.header("1. Design Method")
    method = st.radio("Standard", ["ASD (Allowable Stress)", "LRFD (Limit State)"])
    is_lrfd = "LRFD" in method
    
    st.divider()
    st.header("2. Beam Settings")
    sec_name = st.selectbox("Select Section", list(steel_db.keys()), index=5)
    user_span = st.number_input("Span Length (m)", min_value=1.0, value=6.0, step=0.5)
    fy = st.number_input("Fy (ksc)", 2400)
    fu = st.number_input("Fu (ksc)", 4000, help="Ultimate Tensile Strength")
    
    st.divider()
    st.header("3. Connection Detail")
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
    plate_t = st.selectbox("Plate Thickness (mm)", [6, 9, 10, 12, 16, 20], index=2)
    design_mode = st.radio("Design Load:", ["Actual Load", "75% Capacity"])
    
    E_mod = 2.04e6 
    defl_lim_val = 360 # Fixed for simplicity in this version

# ==========================================
# 3. CORE CALCULATION
# ==========================================
p = steel_db[sec_name]
h_cm, tw_cm = p['h']/10, p['tw']/10
Aw = h_cm * tw_cm
Ix, Zx = p['Ix'], p['Zx']
plate_t_cm = plate_t / 10

# --- FACTOR SETUP ---
if is_lrfd:
    phi_b, phi_v, phi_r = 0.90, 1.00, 0.75 # phi_r for block shear
    omega = 1.0
    M_cap = phi_b * fy * Zx
    V_cap = phi_v * 0.6 * fy * Aw
    bolt_factor = 1.5 
    label_load = "Wu (Factored)"
else:
    phi_r = 1.0 # For simplicity in text logic
    omega = 2.0 # Safety factor for block shear ASD
    M_cap = 0.6 * fy * Zx
    V_cap = 0.4 * fy * Aw
    bolt_factor = 1.0
    label_load = "w (Safe Load)"

# --- BEAM CAPACITIES ---
def get_capacity(L_m):
    L_cm = L_m * 100
    w_s = (2 * V_cap) / L_cm * 100
    w_m = (8 * M_cap) / (L_cm**2) * 100
    w_d = ((L_cm/defl_lim_val) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100
    return min(w_s, w_m, w_d)

user_safe_load = get_capacity(user_span)
V_actual = user_safe_load * user_span / 2
M_actual = user_safe_load * user_span**2 / 8
delta_actual = (5 * (user_safe_load/100) * ((user_span*100)**4)) / (384 * E_mod * Ix)

# --- CONNECTION DESIGN ---
if design_mode == "Actual Load": V_design = V_actual
else: V_design = V_cap * 0.75

# 1. Bolt Capacity
dia_mm = int(bolt_size[1:])
dia_cm = dia_mm/10
b_area = 3.14 if bolt_size=="M20" else (2.01 if bolt_size=="M16" else 3.8)
# Shear Strength
v_bolt_shear = 1000 * b_area * bolt_factor # Adjusted for LRFD approx
# Bearing Strength (Check Web AND Plate)
t_min_cm = min(tw_cm, plate_t_cm) # Use thinner part
v_bolt_bear = 1.2 * fu * dia_cm * t_min_cm * (1.0 if is_lrfd else 1.0/2.0) # Simplified ASD/LRFD toggle
v_bolt = min(v_bolt_shear, v_bolt_bear)

req_bolt = math.ceil(V_design / v_bolt)
if req_bolt < 2: req_bolt = 2
if req_bolt % 2 != 0: req_bolt += 1

# 2. Geometry Layout
n_rows = int(req_bolt / 2)
pitch = 3 * dia_mm
edge_dist = 40 if dia_mm <= 22 else 50 # Standard edge
req_height = (n_rows - 1) * pitch + 2 * edge_dist
avail_height = p['h'] - 2*p['tf'] - 20
layout_ok = req_height <= avail_height

# 3. Block Shear Check (New Feature!) 🚧
# Assume vertical line of bolts tearing out
# Agv = Gross area in shear (Height of block x t)
# Anv = Net area in shear (Agv - holes)
# Ant = Net area in tension (Top horizontal edge)
block_h = (n_rows - 1) * pitch + edge_dist # Length of shear plane
Agv = block_h * t_min_cm * 2 # 2 lines of bolts
hole_dia = dia_cm + 0.2
Anv = Agv - ( (n_rows - 0.5) * 2 * hole_dia * t_min_cm ) # Subtract holes
Ant = (3.5 * t_min_cm) # Assume 3.5cm horizontal edge dist * t * 2 lines (simplified)

# Formula Rn = 0.6 Fu Anv + Ubs Fu Ant
Rn_block = 0.6 * fu * Anv + 1.0 * fu * Ant 

if is_lrfd:
    block_cap = phi_r * Rn_block
else:
    block_cap = Rn_block / omega

block_pass = block_cap >= V_design

# ==========================================
# 4. UI DISPLAY
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Beam Analysis", "🔩 Advanced Connection", "📝 Report"])

with tab1:
    st.subheader(f"Analysis Result ({method})")
    # Compact Main Card
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between;">
            <div><span class="sub-text">Max Load</span><br><span class="big-num">{user_safe_load:,.0f}</span> kg/m</div>
            <div><span class="sub-text">V Design</span><br><span class="big-num">{V_design:,.0f}</span> kg</div>
            <div><span class="sub-text">M Actual</span><br><span class="big-num">{M_actual:,.0f}</span> kg.m</div>
        </div>
    </div>""", unsafe_allow_html=True)
    
    # Graph
    g_spans = np.linspace(2, 15, 50)
    g_vals = [get_capacity(l) for l in g_spans]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=g_spans, y=g_vals, fill='tozeroy', name='Capacity'))
    fig.add_trace(go.Scatter(x=[user_span], y=[user_safe_load], mode='markers', marker=dict(size=12, color='red'), name='Design Point'))
    fig.update_layout(height=350, margin=dict(t=20, b=20, l=40, r=40))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader(f"🔩 Deep Connection Analysis")
    
    c1, c2 = st.columns([1, 1.3])
    with c1:
        # --- 1. BOLT CHECK ---
        st.markdown(f"""
        <div class="conn-card" style="margin-bottom:15px;">
            <b>1. Bolt Shear & Bearing</b><br>
            • Bolt Cap: <b>{v_bolt:,.0f} kg</b><br>
            • Critical Thickness: <b>{t_min_cm*10:.1f} mm</b> ({'Web' if tw_cm <= plate_t_cm else 'Plate'})<br>
            • Required: {V_design/v_bolt:.2f} → <b>{req_bolt} Bolts</b>
        </div>
        """, unsafe_allow_html=True)
        
        # --- 2. BLOCK SHEAR CHECK (NEW) ---
        bs_color = "#27ae60" if block_pass else "#c0392b"
        st.markdown(f"""
        <div class="conn-card" style="border-left: 6px solid {bs_color}; background-color: {'#e9f7ef' if block_pass else '#fadbd8'};">
            <div style="display:flex; justify-content:space-between;">
                <b>2. Block Shear Rupture</b>
                <span class="{'pass-badge' if block_pass else 'fail-badge'}">{'PASS' if block_pass else 'FAIL'}</span>
            </div>
            <div style="font-size:13px; margin-top:5px;">
                การวิบัติแบบฉีกขาดของแผ่นเหล็ก<br>
                • Capacity ({'Phi Rn' if is_lrfd else 'Rn/Omega'}): <b>{block_cap:,.0f} kg</b><br>
                • Load (Vu): <b>{V_design:,.0f} kg</b><br>
                • Ratio: <b>{V_design/block_cap*100:.1f}%</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- 3. GEOMETRY CHECK ---
        geo_status = "OK" if layout_ok else "No Fit"
        st.markdown(f"""
        <div style="margin-top:10px; padding:10px; border:1px solid #ddd; border-radius:8px;">
            <b>3. Geometry Check (AISC)</b><br>
            <small>
            ✅ Pitch ({pitch}mm) ≥ 2.7d<br>
            ✅ Edge ({edge_dist}mm) ≥ Min<br>
            {'✅' if layout_ok else '❌'} Fit in Web: <b>{geo_status}</b>
            </small>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        # Drawing with Block Shear Path
        fig_c = go.Figure()
        # Web
        fig_c.add_shape(type="rect", x0=-p['b']/2, y0=0, x1=p['b']/2, y1=p['h'], line=dict(color="#ddd"), fillcolor="white")
        # Flanges
        fig_c.add_shape(type="rect", x0=-p['b']/2, y0=0, x1=p['b']/2, y1=p['tf'], fillcolor="#2e86c1", line_width=0)
        fig_c.add_shape(type="rect", x0=-p['b']/2, y0=p['h']-p['tf'], x1=p['b']/2, y1=p['h'], fillcolor="#2e86c1", line_width=0)
        
        # Bolts
        cy = p['h'] / 2
        start_y = cy - ((n_rows-1)*pitch)/2
        gage = 80
        bx, by = [], []
        for r in range(n_rows):
            y_pos = start_y + r*pitch
            bx.extend([-gage/2, gage/2])
            by.extend([y_pos, y_pos])
        
        fig_c.add_trace(go.Scatter(x=bx, y=by, mode='markers', marker=dict(size=12, color='#333'), name='Bolts'))
        
        # Block Shear Failure Path (Dashed Line)
        # Draw box around the bolt group simulating tear out
        path_x = [-gage/2, -gage/2, gage/2, gage/2]
        path_y = [start_y - edge_dist, start_y + (n_rows-1)*pitch + edge_dist/2, start_y + (n_rows-1)*pitch + edge_dist/2, start_y - edge_dist]
        
        # Visualizing the Block Shear "U-Shape" or "L-Shape" tear out
        # Here we simulate the block pulling down
        bs_x = [-gage/2 - 15, -gage/2 - 15, gage/2 + 15, gage/2 + 15]
        bs_y_top = start_y + (n_rows-1)*pitch + 15
        bs_y_bot = start_y - 20 # Pulling down
        
        fig_c.add_shape(type="path", path=f"M {-gage/2},{bs_y_bot} L {-gage/2},{bs_y_top} L {gage/2},{bs_y_top} L {gage/2},{bs_y_bot}", 
                        line=dict(color="#e74c3c", width=2, dash="dash"), name="Block Shear Path")
        
        fig_c.add_annotation(x=0, y=bs_y_top+10, text="Failure Path", showarrow=False, font=dict(color="#e74c3c", size=10))

        fig_c.update_layout(
            title="Connection Detail & Failure Path",
            xaxis=dict(visible=False, range=[-p['b'], p['b']]), 
            yaxis=dict(visible=False, scaleanchor="x"), 
            width=400, height=500, margin=dict(l=10, r=10, t=40, b=10), 
            plot_bgcolor='white'
        )
        st.plotly_chart(fig_c)

with tab3:
    st.markdown('<div class="report-paper">', unsafe_allow_html=True)
    st.markdown(f'<div class="report-header">Calculation Report ({method})</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="report-line"><b>Design Load (Vu):</b> {V_design:,.0f} kg</div>
    <div class="report-line"><b>Bolt Spec:</b> {bolt_size} (Fu={fu} ksc)</div>
    <div class="report-line"><b>Connection Plate:</b> t = {plate_t} mm</div>
    <br>
    <div class="report-line"><b>1. Bolt Shear Capacity:</b></div>
    <div class="report-line">Based on area {b_area} cm2 -> Cap = {v_bolt_shear:,.0f} kg</div>
    <div class="report-line"><b>2. Bearing Capacity:</b></div>
    <div class="report-line">Min Thickness = {t_min_cm*10} mm</div>
    <div class="report-line">Cap = {v_bolt_bear:,.0f} kg</div>
    <div class="report-line"><b>3. Block Shear Capacity:</b></div>
    <div class="report-line">Agv={Agv:.2f}, Anv={Anv:.2f}, Ant={Ant:.2f} cm2</div>
    <div class="report-line">Rn = {Rn_block:,.0f} kg -> <b>Design Cap = {block_cap:,.0f} kg</b></div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

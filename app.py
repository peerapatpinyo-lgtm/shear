import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots # Import เพิ่มสำหรับการทำ 2 แกนที่เสถียร
import math

# ==========================================
# 1. DATABASE & CONFIG
# ==========================================
steel_db = {
    "H 100x50x5x7":     {"h": 100, "b": 50,  "tw": 5,   "tf": 7,   "Ix": 187,    "Zx": 37.5,  "w": 9.3},
    "H 125x60x6x8":     {"h": 125, "b": 60,  "tw": 6,   "tf": 8,   "Ix": 413,    "Zx": 65.9,  "w": 13.1},
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8,  "w": 14.0},
    "H 175x90x5x8":     {"h": 175, "b": 90,  "tw": 5,   "tf": 8,   "Ix": 1210,   "Zx": 138,   "w": 18.1},
    "H 200x100x5.5x8": {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "w": 21.3},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "w": 29.6},
    "H 300x150x6.5x9": {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 350x175x7x11":  {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "w": 49.6},
    "H 400x200x8x13":  {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 450x200x9x14":  {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "w": 76.0},
    "H 500x200x10x16": {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
    "H 600x200x11x17": {"h": 600, "b": 200, "tw": 11,  "tf": 17,  "Ix": 77600,  "Zx": 2590,  "w": 106},
    "H 700x300x13x24": {"h": 700, "b": 300, "tw": 13,  "tf": 24,  "Ix": 201000, "Zx": 5760,  "w": 185},
    "H 800x300x14x26": {"h": 800, "b": 300, "tw": 14,  "tf": 26,  "Ix": 292000, "Zx": 7300,  "w": 210},
}

st.set_page_config(page_title="Pro Beam Engineer", layout="wide", page_icon="🏗️")
st.markdown("""<style>.metric-card {background-color: #f8f9fa; border: 1px solid #ddd; padding: 15px; border-radius: 8px;}</style>""", unsafe_allow_html=True)

# ==========================================
# 2. CALCULATION & PLOTTING ENGINES
# ==========================================
def analyze_beam(L_m, props, Fy, E, P_load, U_load, Lb_m):
    # Basic Props
    w_total = U_load + props['w']
    L_cm = L_m * 100
    
    # 1. Reactions
    R = (P_load / 2) + (w_total * L_m / 2)
    
    # 2. Max Forces
    V_max = R
    M_max_kgm = (P_load * L_m / 4) + (w_total * L_m**2 / 8)
    
    # 3. Deflection
    Ix = props['Ix']
    D_point = (P_load * (L_cm**3)) / (48 * E * Ix)
    D_udl = (5 * (w_total/100) * (L_cm**4)) / (384 * E * Ix)
    D_max = D_point + D_udl

    # 4. Generate SFD & BMD Data (Discretization)
    x = np.linspace(0, L_m, 100)
    V_list = []
    M_list = []
    
    for xi in x:
        # Shear V(x)
        shear = R - (w_total * xi)
        if xi > L_m/2: # Point load drop
            shear -= P_load
        V_list.append(shear)
        
        # Moment M(x)
        moment = (R * xi) - (w_total * xi**2 / 2)
        if xi > L_m/2:
            moment -= P_load * (xi - L_m/2)
        M_list.append(moment)

    return {
        "R": R, "M_max": M_max_kgm, "D_max": D_max,
        "x": x, "V_x": V_list, "M_x": M_list,
        "w_total": w_total
    }

def draw_sfd_bmd(res):
    # FIX: Use make_subplots for robust dual-axis support
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add SFD (Primary Y - Left)
    fig.add_trace(
        go.Scatter(x=res['x'], y=res['V_x'], fill='tozeroy', name='Shear (V)', line=dict(color='firebrick')),
        secondary_y=False,
    )
    
    # Add BMD (Secondary Y - Right)
    fig.add_trace(
        go.Scatter(x=res['x'], y=res['M_x'], fill='tozeroy', name='Moment (M)', line=dict(color='royalblue')),
        secondary_y=True,
    )

    # Set Titles
    fig.update_layout(
        title="Shear & Moment Diagram",
        hovermode="x unified",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Set Axis Labels
    fig.update_yaxes(title_text="Shear Force (kg)", title_font=dict(color="firebrick"), tickfont=dict(color="firebrick"), secondary_y=False)
    fig.update_yaxes(title_text="Moment (kg.m)", title_font=dict(color="royalblue"), tickfont=dict(color="royalblue"), secondary_y=True)
    fig.update_xaxes(title_text="Length (m)")

    return fig

def draw_bolt_layout(n_bolts, bolt_size, plate_width=200):
    # Logic: 2 columns if n > 3, else 1 column
    if n_bolts == 0: return go.Figure()
    
    cols = 2 if n_bolts > 3 else 1
    rows = math.ceil(n_bolts / cols)
    
    # Spacing (mm)
    s_x = 80  # horizontal spacing
    s_y = 70  # vertical spacing
    edge = 40
    
    # Calculate coords
    x_coords = []
    y_coords = []
    
    start_x = -s_x/2 if cols == 2 else 0
    start_y = (rows - 1) * s_y / 2
    
    count = 0
    for r in range(rows):
        current_y = start_y - (r * s_y)
        for c in range(cols):
            if count >= n_bolts: break
            current_x = start_x + (c * s_x)
            x_coords.append(current_x)
            y_coords.append(current_y)
            count += 1
            
    # Draw
    fig = go.Figure()
    
    # Draw Plate Outline
    p_w = (cols-1)*s_x + 2*edge + 20 # approx width
    p_h = (rows-1)*s_y + 2*edge
    
    fig.add_shape(type="rect", x0=-p_w/2, y0=-p_h/2, x1=p_w/2, y1=p_h/2, line=dict(color="Gray"), fillcolor="LightGray", opacity=0.3)
    
    # Draw Bolts
    dia = int(bolt_size[1:])
    fig.add_trace(go.Scatter(
        x=x_coords, y=y_coords, mode='markers', 
        marker=dict(size=dia*1.5, color='Black', symbol='circle'),
        name='Bolt'
    ))
    
    fig.update_layout(
        title=f"Connection Detail ({n_bolts}-{bolt_size})",
        xaxis=dict(range=[-150, 150], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[-200, 200], showgrid=False, zeroline=False, visible=False),
        height=300, width=300,
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor="white"
    )
    return fig

# ==========================================
# 3. SIDEBAR
# ==========================================
with st.sidebar:
    st.title("⚙️ Design Inputs")
    P_input = st.number_input("Point Load (kg)", 1000.0, step=100.0)
    U_input = st.number_input("Superimposed UDL (kg/m)", 500.0, step=50.0)
    L_input = st.number_input("Span (m)", 6.0, step=0.5)
    
    st.divider()
    fy = st.number_input("Fy (ksc)", 2400)
    def_lim = st.selectbox("Deflection Limit", [200, 240, 300, 400], index=2)
    
    mode = st.radio("Mode", ["Manual Check", "Optimizer"])

# ==========================================
# 4. MAIN UI
# ==========================================
st.title("🏗️ Structural Beam & Connection Pro")

if mode == "Manual Check":
    # --- SECTION SELECTION ---
    col1, col2 = st.columns([1,3])
    with col1:
        sec_name = st.selectbox("Select Section", list(steel_db.keys()), index=10)
    with col2:
        props = steel_db[sec_name]
        st.info(f"**Properties:** W = {props['w']} kg/m | Ix = {props['Ix']:,} cm4 | Zx = {props['Zx']:,} cm3")

    # --- CALCULATION ---
    # 1. Allowable
    V_allow = 0.4 * fy * (props['h']/10 * props['tw']/10)
    M_allow = 0.6 * fy * props['Zx'] # Simplified for compact
    D_allow = (L_input * 100) / def_lim
    
    # 2. Analysis
    res = analyze_beam(L_input, props, fy, 2.04e6, P_input, U_input, 0)
    
    # --- TABS ---
    tab1, tab2, tab3 = st.tabs(["📊 Analysis & Graphs", "🔩 Connection Detail", "📝 Report"])
    
    with tab1:
        # Metrics
        c1, c2, c3 = st.columns(3)
        v_rat = res['R'] / V_allow
        m_rat = (res['M_max']*100) / M_allow
        d_rat = res['D_max'] / D_allow
        
        c1.metric("Max Shear", f"{res['R']:.0f} kg", f"{v_rat*100:.0f}% Cap")
        c2.metric("Max Moment", f"{res['M_max']:.0f} kg.m", f"{m_rat*100:.0f}% Cap")
        c3.metric("Deflection", f"{res['D_max']:.2f} cm", f"Allow {D_allow:.2f}")
        
        # Traffic Light
        if max(v_rat, m_rat, d_rat) <= 1.0:
            st.success("✅ DESIGN PASS")
        else:
            st.error("❌ DESIGN FAIL")
            
        # PLOT SFD/BMD
        st.plotly_chart(draw_sfd_bmd(res), use_container_width=True)
        
    with tab2:
        col_inp, col_draw = st.columns([1, 2])
        with col_inp:
            st.subheader("Connection Inputs")
            bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
            design_v = st.radio("Design Force", ["Actual Vmax", "Typical (Span 10D)"])
            
            # Connection Calc
            if design_v == "Actual Vmax":
                V_conn = res['R']
            else:
                V_conn = (4 * (M_allow/1000) * 1000) / (10 * props['h']/1000)
            
            # Bolt Capacity (Simplified Single Shear)
            b_area = 3.14 if bolt_size=="M20" else (2.0 if bolt_size=="M16" else 3.8)
            v_bolt = 1000 * b_area # Approx 1.0t/cm2
            n_bolts = math.ceil(V_conn / v_bolt)
            
            st.write(f"Design V: **{V_conn:,.0f} kg**")
            st.write(f"Bolt Cap: **{v_bolt:,.0f} kg/ea**")
            st.metric("Required Bolts", f"{n_bolts} pcs")
            
        with col_draw:
            st.plotly_chart(draw_bolt_layout(n_bolts, bolt_size), use_container_width=True)
            
    with tab3:
        st.code(f"""
        ENGINEERING REPORT
        ------------------
        Project: Structural Check
        Section: {sec_name}
        Span: {L_input} m
        
        LOADS:
        - Point: {P_input} kg
        - UDL: {U_input} kg/m
        
        RESULTS:
        - V_act: {res['R']:.0f} kg  (Ratio: {v_rat:.2f})
        - M_act: {res['M_max']:.0f} kg.m (Ratio: {m_rat:.2f})
        - Defl : {res['D_max']:.2f} cm (Ratio: {d_rat:.2f})
        
        CONNECTION:
        - Use {n_bolts} - {bolt_size} (Design V = {V_conn:.0f} kg)
        ------------------
        Status: {"PASS" if max(v_rat, m_rat, d_rat) <= 1.0 else "FAIL"}
        """)

elif mode == "Optimizer":
    st.subheader("🚀 Find the Best Section")
    if st.button("Run Optimization"):
        results = []
        for name, p in steel_db.items():
            # Check Capacity
            r = analyze_beam(L_input, p, fy, 2.04e6, P_input, U_input, 0)
            v_al = 0.4 * fy * (p['h']/10 * p['tw']/10)
            m_al = 0.6 * fy * p['Zx']
            d_al = (L_input*100)/def_lim
            
            ratio = max(r['R']/v_al, (r['M_max']*100)/m_al, r['D_max']/d_al)
            if ratio <= 1.0:
                results.append({"Section": name, "Weight": p['w'], "Ratio": ratio})
        
        if results:
            df = pd.DataFrame(results).sort_values("Weight")
            best = df.iloc[0]
            st.success(f"Best Section: **{best['Section']}** ({best['Weight']} kg/m)")
            
            # Optimization Graph
            fig_opt = go.Figure(go.Scatter(
                x=df['Weight'], y=df['Ratio']*100,
                mode='markers+text', text=df['Section'],
                textposition='top center',
                marker=dict(size=12, color=df['Ratio'], colorscale='RdYlGn_r')
            ))
            fig_opt.update_layout(title="Efficiency Map (Weight vs Utilization)", xaxis_title="Weight (kg/m)", yaxis_title="Util %")
            st.plotly_chart(fig_opt, use_container_width=True)
        else:
            st.error("No section found!")

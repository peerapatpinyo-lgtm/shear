import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLES
# ==========================================
st.set_page_config(page_title="ProStructure: Calculation Report", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .report-box { background-color: #fdfefe; border: 1px solid #d5d8dc; padding: 20px; border-radius: 5px; font-family: 'Courier New', monospace; font-size: 14px; margin-top: 10px; }
    .header-main { color: #154360; border-bottom: 2px solid #154360; padding-bottom: 5px; margin-bottom: 15px; }
    .pass-tag { background-color: #d4efdf; color: #1e8449; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    .fail-tag { background-color: #fadbd8; color: #943126; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    .metric-card { background-color: #ebf5fb; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #a9cce3; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA & INPUTS
# ==========================================
def get_sys_data():
    data = [
        ("H 100x50x5x7", 100, 50, 5, 7, 378, 76.5),
        ("H 150x75x5x7", 150, 75, 5, 7, 666, 88.8),
        ("H 200x100x5.5x8", 200, 100, 5.5, 8, 1840, 184),
        ("H 250x125x6x9", 250, 125, 6, 9, 3690, 295),
        ("H 300x150x6.5x9", 300, 150, 6.5, 9, 7210, 481),
        ("H 350x175x7x11", 350, 175, 7, 11, 13600, 775),
        ("H 400x200x8x13", 400, 200, 8, 13, 23700, 1190),
        ("H 450x200x9x14", 450, 200, 9, 14, 33500, 1490),
        ("H 500x200x10x16", 500, 200, 10, 16, 47800, 1910),
        ("H 600x200x11x17", 600, 200, 11, 17, 77600, 2590),
        ("H 700x300x13x24", 700, 300, 13, 24, 201000, 5760),
        ("H 800x300x14x26", 800, 300, 14, 26, 292000, 7290),
        ("H 900x300x16x28", 900, 300, 16, 28, 411000, 9140)
    ]
    return pd.DataFrame(data, columns=["Section", "h", "b", "tw", "tf", "Ix", "Zx"])

with st.sidebar:
    st.title("⚙️ Parameters")
    df = get_sys_data()
    sec_name = st.selectbox("Select Section", df['Section'], index=6) # H400
    
    st.subheader("Material")
    Fy = st.number_input("Fy (ksc)", value=2400)
    Fu = st.number_input("Fu (ksc)", value=4000)
    E = 2040000

    # Props
    p = df[df['Section'] == sec_name].iloc[0]
    h, tw, tf, Ix, Zx = p['h'], p['tw'], p['tf'], p['Ix'], p['Zx']
    
    st.info(f"""
    **{sec_name}**
    h={h}, tw={tw}, tf={tf} mm
    Ix={Ix:,} cm⁴, Zx={Zx:,} cm³
    """)

# ==========================================
# 3. BEAM CALCULATION (REVERSE)
# ==========================================
st.title("🏗️ Structural Calculation Report")
st.caption("Automated Calculation Sheet based on Capacity Design")

# Inputs
c1, c2 = st.columns([1, 2])
with c1:
    span = st.number_input("Design Span Length (m)", 1.0, 20.0, 6.0, step=0.5)
with c2:
    st.markdown(f"### Target Section: **{sec_name}**")
    st.markdown("Calculating Max Allowable Reaction ($V_{max}$) based on Governing Failure Modes...")

# Calculations
L_cm = span * 100
h_cm, tw_cm = h/10, tw/10
Aw = h_cm * tw_cm

# 1. Shear
V_cap_shear = 0.6 * Fy * Aw

# 2. Moment
M_allow = 0.6 * Fy * Zx
V_cap_moment = (4 * M_allow) / L_cm

# 3. Deflection
V_cap_defl = (384 * E * Ix) / (2400 * (L_cm**2))

# Governing
V_design = min(V_cap_shear, V_cap_moment, V_cap_defl)
if V_design == V_cap_shear: gov = "Shear Yielding"
elif V_design == V_cap_moment: gov = "Bending Moment"
else: gov = "Deflection Limit (L/240)"

w_equivalent = (2 * V_design) / span

# ==========================================
# TAB 1: BEAM ANALYSIS & REPORT
# ==========================================
tab1, tab2 = st.tabs(["📊 1. Beam Analysis & Report", "🔩 2. Connection Design Report"])

with tab1:
    # --- RESULT METRICS ---
    col_res1, col_res2, col_res3 = st.columns(3)
    col_res1.markdown(f"""<div class="metric-card"><h3>{V_design:,.0f} kg</h3><p>Max Reaction (V)</p></div>""", unsafe_allow_html=True)
    col_res2.markdown(f"""<div class="metric-card"><h3>{w_equivalent:,.0f} kg/m</h3><p>Max Uniform Load (w)</p></div>""", unsafe_allow_html=True)
    col_res3.markdown(f"""<div class="metric-card"><h3>{gov}</h3><p>Controlled By</p></div>""", unsafe_allow_html=True)
    
    col_g, col_r = st.columns([1.5, 1])
    
    # --- GRAPH ---
    with col_g:
        st.subheader("📈 Capacity Envelope")
        L_vals = np.linspace(0.5, 20, 100)
        L_vals_cm = L_vals * 100
        
        v1 = np.full_like(L_vals, V_cap_shear)
        v2 = (4 * M_allow) / L_vals_cm
        v3 = (384 * E * Ix) / (2400 * (L_vals_cm**2))
        v_safe = np.minimum(np.minimum(v1, v2), v3)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=L_vals, y=v_safe, fill='tozeroy', name='Design Envelope', line=dict(color='#2980b9', width=3)))
        fig.add_trace(go.Scatter(x=L_vals, y=v1, name='Shear Limit', line=dict(dash='dot', color='green')))
        fig.add_trace(go.Scatter(x=L_vals, y=v2, name='Moment Limit', line=dict(dash='dot', color='orange')))
        fig.add_trace(go.Scatter(x=L_vals, y=v3, name='Deflection Limit', line=dict(dash='dot', color='red')))
        
        # Current Point
        fig.add_trace(go.Scatter(x=[span], y=[V_design], mode='markers', marker=dict(size=12, color='red'), name='Current Design'))
        
        # Optimal Range
        d_m = h/1000
        fig.add_vrect(x0=15*d_m, x1=20*d_m, fillcolor="green", opacity=0.1, annotation_text="Optimal Span")

        fig.update_layout(height=450, hovermode="x unified", xaxis_title="Span (m)", yaxis_title="Max V (kg)",
                          xaxis=dict(rangeslider=dict(visible=True))) # ZOOMABLE
        st.plotly_chart(fig, use_container_width=True)

    # --- CALCULATION SHEET ---
    with col_r:
        st.subheader("📝 Detailed Calculation Sheet")
        with st.container():
            st.markdown(f"""
            <div class="report-box">
            <b>1. Web Shear Capacity (อ้างอิง AISC 360)</b><br>
            A_w = d * t_w = {h_cm:.1f} * {tw_cm:.1f} = {Aw:.2f} cm²<br>
            V_n = 0.6 * F_y * A_w<br>
            &nbsp;&nbsp;&nbsp;&nbsp;= 0.6 * {Fy} * {Aw:.2f}<br>
            &nbsp;&nbsp;&nbsp;&nbsp;= <b>{V_cap_shear:,.0f} kg</b> (Constant)<br>
            <br>
            <b>2. Bending Moment Control</b><br>
            M_all = 0.6 * F_y * Z_x<br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= 0.6 * {Fy} * {Zx}<br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= {M_allow:,.0f} kg.cm<br>
            V_max = (4 * M_all) / L<br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= (4 * {M_allow:,.0f}) / {L_cm}<br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= <b>{V_cap_moment:,.0f} kg</b><br>
            <br>
            <b>3. Deflection Control (L/240)</b><br>
            Formula: V = (384 * E * I) / (2400 * L²)<br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= (384 * {E} * {Ix}) / (2400 * {L_cm}²)<br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= <b>{V_cap_defl:,.0f} kg</b><br>
            <br>
            <b>GOVERNING LOAD:</b><br>
            V_design = MIN({V_cap_shear:,.0f}, {V_cap_moment:,.0f}, {V_cap_defl:,.0f})<br>
            <span style="color:blue; font-weight:bold;">V_design = {V_design:,.0f} kg</span>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# TAB 2: CONNECTION REPORT
# ==========================================
with tab2:
    st.markdown('<h3 class="header-main">🔩 Shear Tab Connection Design</h3>', unsafe_allow_html=True)
    
    col_in, col_calc = st.columns([1, 2])
    
    with col_in:
        st.info(f"Design Load ($V_u$) from Tab 1: **{V_design:,.0f} kg**")
        
        # Config
        bolt_grade = st.selectbox("Bolt Grade", ["A325", "A307"])
        dia = st.selectbox("Diameter (mm)", [12, 16, 20, 22, 24], index=2)
        rows = st.number_input("Rows (n)", 2, 8, 3)
        tp_mm = st.selectbox("Plate Thick (mm)", [6, 9, 12, 16], index=1)
        w_size = st.selectbox("Weld Size (mm)", [4, 6, 8, 10], index=1)
        
        # Geometry
        s = 3 * dia
        lev = 1.5 * dia
        leh = 40
        st.write("---")
        st.write(f"**Geometry:** Pitch={s}, Le_v={lev}, Le_h={leh}")

    with col_calc:
        # --- CALC CODE ---
        db = dia/10
        Ab = math.pi*(db/2)**2
        Fv = 3720 if bolt_grade == "A325" else 1900
        
        # 1. Bolt Shear
        Rn_bolt = rows * Ab * Fv
        
        # 2. Bearing
        Rn_bear_w = rows * (1.2*Fu*db*(tw/10))
        Rn_bear_p = rows * (1.2*Fu*db*(tp_mm/10))
        Rn_bear = min(Rn_bear_w, Rn_bear_p)
        
        # 3. Block Shear
        Agv = ((lev + (rows-1)*s)/10) * (tp_mm/10)
        Anv = Agv - (rows-0.5)*((dia+2)/10)*(tp_mm/10)
        Ant = ((leh - 0.5*(dia+2))/10) * (tp_mm/10)
        
        bs1 = 0.6*Fy*Agv + 1.0*Fu*Ant
        bs2 = 0.6*Fu*Anv + 1.0*Fu*Ant
        Rn_block = min(bs1, bs2)
        
        # 4. Weld
        L_weld = (lev + (rows-1)*s + lev)/10
        Rn_weld = 2 * L_weld * 0.707 * (w_size/10) * (0.3 * 4900)
        
        capacities = {"Bolt Shear": Rn_bolt, "Bearing": Rn_bear, "Block Shear": Rn_block, "Weld": Rn_weld}
        min_cap = min(capacities.values())
        status = "PASSED" if min_cap >= V_design else "FAILED"
        status_color = "#d4efdf" if status == "PASSED" else "#fadbd8"
        text_color = "#1e8449" if status == "PASSED" else "#943126"

        # --- REPORT DISPLAY ---
        st.markdown(f"""
        <div style="background-color:{status_color}; padding:15px; border-radius:5px; border:1px solid {text_color}; text-align:center; margin-bottom:15px;">
            <h2 style="color:{text_color}; margin:0;">{status}</h2>
            Capacity: {min_cap:,.0f} kg (Ratio: {V_design/min_cap:.2f})
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📋 Show Detailed Calculation Steps (รายการคำนวณ)", expanded=True):
            st.markdown(f"""
            <div class="report-box">
            <b>1. Bolt Shear Capacity</b><br>
            Ab = π * ({db:.2f}/2)² = {Ab:.2f} cm²<br>
            Rn = n * Ab * Fv = {rows} * {Ab:.2f} * {Fv}<br>
            &nbsp;&nbsp;&nbsp;= <b>{Rn_bolt:,.0f} kg</b><br>
            
            <br>
            <b>2. Bearing Capacity</b><br>
            Rn_web = n * 1.2 * Fu * d * tw = {rows} * 1.2 * {Fu} * {db:.2f} * {tw/10:.2f} = {Rn_bear_w:,.0f}<br>
            Rn_plt = n * 1.2 * Fu * d * tp = {rows} * 1.2 * {Fu} * {db:.2f} * {tp_mm/10:.2f} = {Rn_bear_p:,.0f}<br>
            &nbsp;&nbsp;&nbsp;= <b>{Rn_bear:,.0f} kg</b><br>
            <br>
            <b>3. Block Shear Capacity</b><br>
            Agv={Agv:.2f}, Anv={Anv:.2f}, Ant={Ant:.2f} cm²<br>
            R1 = 0.6FyAgv + FuAnt = 0.6*{Fy}*{Agv:.2f} + {Fu}*{Ant:.2f} = {bs1:,.0f}<br>
            R2 = 0.6FuAnv + FuAnt = 0.6*{Fu}*{Anv:.2f} + {Fu}*{Ant:.2f} = {bs2:,.0f}<br>
            &nbsp;&nbsp;&nbsp;= <b>{Rn_block:,.0f} kg</b><br>
            
            <br>
            <b>4. Weld Capacity</b><br>
            L_weld = {L_weld:.2f} cm<br>
            Rn = 2 * L * 0.707 * s * 0.3Fexx<br>
            &nbsp;&nbsp;&nbsp;= 2 * {L_weld:.2f} * 0.707 * {w_size/10} * (0.3*4900)<br>
            &nbsp;&nbsp;&nbsp;= <b>{Rn_weld:,.0f} kg</b>
            </div>
            """, unsafe_allow_html=True)

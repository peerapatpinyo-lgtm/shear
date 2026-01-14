import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Beam Insight V9 (Audited)", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .highlight-card { background-color: #e8f6f3; padding: 20px; border-radius: 10px; border: 1px solid #1abc9c; }
    .conn-card { background-color: #fff9c4; padding: 15px; border-radius: 8px; border: 1px solid #fbc02d; }
    .metric-box { text-align: center; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-top: 3px solid #3498db; }
    .big-num { font-size: 24px; font-weight: bold; color: #17202a; }
    .sub-text { font-size: 14px; color: #7f8c8d; margin-top: 5px; }
    .audit-box { background-color: #fdfefe; padding: 20px; border: 1px solid #d5dbdb; border-radius: 5px; font-family: 'Sarabun', sans-serif; margin-top: 15px; }
    h5 { color: #154360; font-weight: bold; margin-top: 15px; margin-bottom: 10px; border-bottom: 2px solid #eee; padding-bottom: 5px; }
    .formula-row { display: flex; justify-content: space-between; margin-bottom: 5px; font-family: 'Courier New', monospace; font-size: 14px; color: #333; }
    .note { font-size: 12px; color: #888; font-style: italic; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE (ENGINEERING STANDARD)
# ==========================================
# 2.1 Section Properties (JIS Standard)
steel_db = {
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8,  "w": 14.0},
    "H 200x100x5.5x8":  {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "w": 21.3},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "w": 29.6},
    "H 300x150x6.5x9":  {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 350x175x7x11":   {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "w": 49.6},
    "H 400x200x8x13":   {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 450x200x9x14":   {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "w": 76.0},
    "H 500x200x10x16":  {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
    "H 600x200x11x17":  {"h": 600, "b": 200, "tw": 11,  "tf": 17,  "Ix": 77600,  "Zx": 2590,  "w": 106},
}

# 2.2 Material Properties (TIS/JIS Standard)
material_db = {
    "SS400 (General)": {"Fy": 2400, "Fu": 4100, "E": 2.04e6},
    "SM520 (High Strength)": {"Fy": 3600, "Fu": 5300, "E": 2.04e6},
    "Custom": {"Fy": 2400, "Fu": 4100, "E": 2.04e6} # Placeholder
}

# 2.3 Bolt Grades (Allowable Shear Stress - ASD)
# Note: Fv values are approximate allowable shear stresses (single shear)
bolt_grade_db = {
    "Grade 4.6 (Common)": {"Fv": 960},   # Approx 0.3 Fu (3200) -> ~960 ksc
    "Grade 8.8 (High Strength)": {"Fv": 1440}, # Approx A325 ASD
    "A325 / F10T": {"Fv": 2100} # ASD with threads excluded from shear plane
}

# ==========================================
# 3. SIDEBAR & INPUTS
# ==========================================
with st.sidebar:
    st.title("Beam Insight V9")
    st.caption("Audited Engineering Edition")
    st.divider()
    
    st.header("1. Beam Configuration")
    sec_name = st.selectbox("Section Size", list(steel_db.keys()), index=5)
    mat_name = st.selectbox("Steel Grade", list(material_db.keys()))
    
    # Material Logic
    if mat_name == "Custom":
        c1, c2 = st.columns(2)
        fy = c1.number_input("Fy (ksc)", value=2400)
        fu = c2.number_input("Fu (ksc)", value=4100)
        E_mod = 2.04e6
    else:
        mat_props = material_db[mat_name]
        fy = mat_props["Fy"]
        fu = mat_props["Fu"]
        E_mod = mat_props["E"]
        st.info(f"Properties: Fy={fy}, Fu={fu} ksc")
        
    user_span = st.number_input("Span Length (m)", min_value=1.0, value=6.0, step=0.5)
    defl_ratio = st.selectbox("Defl. Limit", ["L/300", "L/360", "L/400"], index=1)
    
    st.divider()
    st.header("2. Connection Config")
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
    bolt_grade_name = st.selectbox("Bolt Grade", list(bolt_grade_db.keys()), index=1)
    bolt_fv = bolt_grade_db[bolt_grade_name]["Fv"]
    
    design_mode = st.radio("Design Basis:", ["Actual Load (from Span)", "Fixed % Capacity"])
    if design_mode == "Fixed % Capacity":
        target_pct = st.slider("Target % Usage", 50, 100, 75, 5)
    else:
        target_pct = None

    defl_lim_val = int(defl_ratio.split("/")[1])

# ==========================================
# 4. CALCULATION ENGINE (AUDITED)
# ==========================================
# 4.1 Section Properties
p = steel_db[sec_name]
h_cm, tw_cm = p['h']/10, p['tw']/10
tf_cm = p['tf']/10
Aw = h_cm * tw_cm       # Assumption: Total Depth * tw (Standard for rolled shapes shear)
Zx = p['Zx']            # Elastic Section Modulus (S in AISC, Z in JIS/EIT often used interchangeably for elastic)
Ix = p['Ix']

# 4.2 Beam Allowable Capacities (ASD)
# Shear: 0.4 Fy
V_cap = 0.4 * fy * Aw 
# Moment: 0.6 Fy (Assumed Compact Section & Sufficient Bracing)
M_cap = 0.6 * fy * Zx 

# 4.3 Safe Load Calculation
def get_capacity(L_m):
    L_cm = L_m * 100
    
    # 1. Shear Limit: w = 2V/L
    w_s_kgcm = (2 * V_cap) / L_cm
    
    # 2. Moment Limit: w = 8M/L^2
    w_m_kgcm = (8 * M_cap) / (L_cm**2)
    
    # 3. Deflection Limit: w = (Delta * 384EI) / (5L^4)
    delta_target = L_cm / defl_lim_val
    w_d_kgcm = (delta_target * 384 * E_mod * Ix) / (5 * (L_cm**4))
    
    # Compare in kg/cm
    w_gov_kgcm = min(w_s_kgcm, w_m_kgcm, w_d_kgcm)
    
    # Convert to kg/m
    return {
        "w_safe": w_gov_kgcm * 100,
        "cause": "Shear" if w_gov_kgcm == w_s_kgcm else ("Moment" if w_gov_kgcm == w_m_kgcm else "Deflection"),
        "w_s": w_s_kgcm * 100,
        "w_m": w_m_kgcm * 100,
        "w_d": w_d_kgcm * 100
    }

res = get_capacity(user_span)
user_safe_load = res["w_safe"]
user_cause = res["cause"]

# 4.4 Actual Forces (Back Calculation)
V_actual = user_safe_load * user_span / 2
M_actual = user_safe_load * user_span**2 / 8 # kg.m
# Recalculate Delta Actual
# Formula: 5wL^4/384EI (w must be kg/cm)
w_actual_kgcm = user_safe_load / 100
delta_actual = (5 * w_actual_kgcm * ((user_span*100)**4)) / (384 * E_mod * Ix)
delta_allow = (user_span*100) / defl_lim_val

# ==========================================
# 5. UI DISPLAY
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Beam Analysis", "🔩 Connection Audit", "💾 Load Table"])

# --- TAB 1: BEAM ANALYSIS ---
with tab1:
    st.subheader(f"Structural Analysis: {sec_name} (L={user_span}m)")
    
    # Summary Card
    cause_color = "#e74c3c" if user_cause == "Shear" else ("#f39c12" if user_cause == "Moment" else "#27ae60")
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span class="sub-text">Max Allowable Uniform Load ($w_{{allow}}$)</span><br>
                <span class="big-num" style="font-size: 36px;">{user_safe_load:,.0f}</span> <span style="font-size:20px; color:#555;">kg/m</span>
            </div>
            <div style="text-align: right;">
                <span class="sub-text">Governing Criteria</span><br>
                <span style="font-size: 18px; font-weight:bold; color:{cause_color};">{user_cause}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Metrics
    c1, c2, c3 = st.columns(3)
    shear_pct = (V_actual / V_cap) * 100
    moment_pct = ((M_actual*100) / M_cap) * 100
    defl_pct = (delta_actual / delta_allow) * 100
    
    with c1: st.markdown(f"""<div class="metric-box" style="border-top-color: #e74c3c;"><div class="sub-text">Actual Shear ($V$)</div><div class="big-num">{V_actual:,.0f} kg</div><div class="sub-text">Cap: {V_cap:,.0f} | Ratio: <b>{shear_pct:.0f}%</b></div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="metric-box" style="border-top-color: #f39c12;"><div class="sub-text">Actual Moment ($M$)</div><div class="big-num">{M_actual:,.0f} kg.m</div><div class="sub-text">Cap: {M_cap/100:,.0f} | Ratio: <b>{moment_pct:.0f}%</b></div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="metric-box" style="border-top-color: #27ae60;"><div class="sub-text">Actual Deflection ($\Delta$)</div><div class="big-num">{delta_actual:.2f} cm</div><div class="sub-text">Allow: {delta_allow:.2f} | Ratio: <b>{defl_pct:.0f}%</b></div></div>""", unsafe_allow_html=True)

    # Chart
    st.markdown("#### 📈 Capacity Envelope")
    g_spans = np.linspace(2, 15, 100)
    g_data = [get_capacity(l) for l in g_spans]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=g_spans, y=[x["w_m"] for x in g_data], mode='lines', name='Moment Limit', line=dict(color='orange', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x["w_s"] for x in g_data], mode='lines', name='Shear Limit', line=dict(color='red', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x["w_d"] for x in g_data], mode='lines', name='Defl. Limit', line=dict(color='green', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x["w_safe"] for x in g_data], mode='lines', name='Safe Load Zone', line=dict(color='#2E86C1', width=3), fill='tozeroy'))
    fig.add_trace(go.Scatter(x=[user_span], y=[user_safe_load], mode='markers', marker=dict(color='black', size=12, symbol='star'), name='Current Point'))
    fig.update_layout(xaxis_title="Span Length (m)", yaxis_title="Uniform Load (kg/m)", height=400, margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # --- AUDIT REPORT (DETAILED) ---
    st.markdown("---")
    st.subheader("📋 Engineering Calculation Report")
    
    with st.expander("Show Detailed Calculation Steps (Audit Mode)", expanded=True):
        st.markdown(f"""
        <div class="audit-box">
            <h5>1. Section & Material Properties</h5>
            <ul>
                <li><b>Section:</b> {sec_name} ($A_w \approx h \cdot t_w = {h_cm} \cdot {tw_cm} = {Aw:.2f} cm^2$)</li>
                <li><b>Material:</b> {mat_name} ($F_y = {fy} ksc, F_u = {fu} ksc, E = {E_mod:,.0f} ksc$)</li>
            </ul>

            <h5>2. Allowable Capacities (ASD)</h5>
            <div class="formula-row">
                <span>Allowable Shear Stress ($F_v = 0.4F_y$):</span>
                <span>$0.4 \\times {fy} = {0.4*fy:.0f} \\text{{ ksc}}$ </span>
            </div>
            <div class="formula-row">
                <span><b>Allowable Shear Force ($V_a$):</b></span>
                <span>$F_v \\times A_w = {0.4*fy:.0f} \\times {Aw:.2f} = \\mathbf{{{V_cap:,.0f} \\text{{ kg}}}}$</span>
            </div>
            <hr style="margin: 5px 0;">
            <div class="formula-row">
                <span>Allowable Bending Stress ($F_b = 0.6F_y$):</span>
                <span>$0.6 \\times {fy} = {0.6*fy:.0f} \\text{{ ksc}}$ (Assuming Compact) </span>
            </div>
            <div class="formula-row">
                <span><b>Allowable Moment ($M_a$):</b></span>
                <span>$F_b \\times Z_x = {0.6*fy:.0f} \\times {Zx} = \\mathbf{{{M_cap:,.0f} \\text{{ kg.cm}}}}$</span>
            </div>

            <h5>3. Load Calculation @ Span {user_span} m</h5>
            <div class="note">Converting all limits to Uniform Load w (kg/m)</div>
            <br>
            <div class="formula-row">
                <span><b>Condition A (Shear):</b> $w = \\frac{{2V_a}}{{L}}$</span>
                <span>$\\frac{{2 \\times {V_cap:,.0f}}}{{{user_span*100}}} \\times 100 = \\mathbf{{{res['w_s']:,.0f}}}$ kg/m</span>
            </div>
            <div class="formula-row">
                <span><b>Condition B (Moment):</b> $w = \\frac{{8M_a}}{{L^2}}$</span>
                <span>$\\frac{{8 \\times {M_cap:,.0f}}}{{({user_span*100})^2}} \\times 100 = \\mathbf{{{res['w_m']:,.0f}}}$ kg/m</span>
            </div>
            <div class="formula-row">
                <span><b>Condition C (Deflection):</b> Limit = {delta_allow:.2f} cm</span>
                <span>$\\frac{{\\Delta \\cdot 384EI}}{{5L^4}} \\times 100 = \\mathbf{{{res['w_d']:,.0f}}}$ kg/m</span>
            </div>
            <br>
            <div style="background:#eafaf1; padding:10px; border-left:3px solid #2ecc71;">
                <b>Conclusion:</b> Max Safe Load = Min(A, B, C) = <b>{user_safe_load:,.0f} kg/m</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- TAB 2: CONNECTION ---
with tab2:
    st.subheader(f"🔩 Connection Verification: {bolt_size} ({bolt_grade_name})")
    
    # Connection Logic
    dia_mm = int(bolt_size[1:])
    dia_cm = dia_mm/10
    
    # Bolt Area
    b_area_dict = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    b_area = b_area_dict.get(bolt_size, 3.14)
    
    # 1. Bolt Shear Capacity (Based on Grade)
    v_bolt_shear = bolt_fv * b_area # Fv * Ab
    
    # 2. Bearing Capacity (Based on Beam Web & Fu of Beam)
    # Formula: 1.2 * Fu * d * t (EIT/AISC for standard holes)
    v_bolt_bear = 1.2 * fu * dia_cm * tw_cm
    
    # Governing
    v_bolt = min(v_bolt_shear, v_bolt_bear)
    gov_mode = "Shear" if v_bolt == v_bolt_shear else "Bearing"
    
    # Demand
    if design_mode == "Actual Load (from Span)":
        V_design = V_actual
        basis_txt = f"Actual Shear ($V_{{act}}$)"
    else:
        V_design = V_cap * (target_pct / 100)
        basis_txt = f"{target_pct}% of Shear Capacity"

    req_bolt = math.ceil(V_design / v_bolt)
    if req_bolt % 2 != 0: req_bolt += 1 
    if req_bolt < 2: req_bolt = 2
    
    # Layout (Same visual logic)
    col_conn1, col_conn2 = st.columns([1, 1.5])
    
    with col_conn1:
        st.markdown(f"""
        <div class="conn-card">
            <h4 style="margin:0;">Load Demand ($V_u$)</h4>
            <div class="big-num" style="color:#d35400;">{V_design:,.0f} kg</div>
            <div class="sub-text">Basis: {basis_txt}</div>
            <hr>
            <div><b>Single Bolt Capacity:</b> {v_bolt:,.0f} kg</div>
            <div class="sub-text">(Controlled by {gov_mode})</div>
            <br>
            <div><b>Required Quantity:</b></div>
            <div style="font-size:20px; font-weight:bold; color:blue;">{req_bolt} pcs</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_conn2:
        # Layout Plot
        fig_c = go.Figure()
        fig_c.add_shape(type="rect", x0=-p['b']/2, y0=0, x1=p['b']/2, y1=p['h'], line=dict(color="RoyalBlue"), fillcolor="rgba(173, 216, 230, 0.2)")
        fig_c.add_shape(type="rect", x0=-p['b']/2, y0=0, x1=p['b']/2, y1=p['tf'], fillcolor="RoyalBlue", line_width=0)
        fig_c.add_shape(type="rect", x0=-p['b']/2, y0=p['h']-p['tf'], x1=p['b']/2, y1=p['h'], fillcolor="RoyalBlue", line_width=0)
        
        n_rows = int(req_bolt / 2)
        pitch = 3 * dia_mm
        start_y = (p['h']/2) - ((n_rows-1)*pitch)/2
        bx, by = [], []
        for r in range(n_rows):
            y_pos = start_y + r*pitch
            bx.extend([-35, 35]) # Draw gauge approx
            by.extend([y_pos, y_pos])
        
        fig_c.add_trace(go.Scatter(x=bx, y=by, mode='markers', marker=dict(size=12, color='#c0392b', line=dict(width=1, color='black')), name='Bolts'))
        fig_c.update_layout(title=f"Connection Layout ({n_rows} Rows x 2 Cols)", width=350, height=450, xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"), margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_c)

    # --- BOLT AUDIT ---
    st.markdown("---")
    st.subheader("🔩 Bolt Calculation Audit")
    with st.expander("Show Bolt Check Details", expanded=True):
        st.markdown(f"""
        <div class="audit-box">
            <h5>1. Bolt Parameters</h5>
            <ul>
                <li><b>Size:</b> {bolt_size} ($d={dia_mm}$ mm), <b>Grade:</b> {bolt_grade_name}</li>
                <li><b>Area ($A_b$):</b> {b_area} cm²</li>
                <li><b>Allowable Shear Stress ($F_v$):</b> {bolt_fv} ksc (User/Standard Input)</li>
            </ul>

            <h5>2. Capacity Check</h5>
            <div class="formula-row">
                <span><b>A. Shear Capacity ($R_v$):</b> $F_v \\times A_b$ </span>
                <span>${bolt_fv} \\times {b_area} = \\mathbf{{{v_bolt_shear:,.0f}}}$ kg</span>
            </div>
            <div class="formula-row">
                <span><b>B. Bearing Capacity ($R_b$):</b> $1.2 F_u d t_w$ (on Beam Web) </span>
                <span>$1.2 \\times {fu} \\text{{(Beam)}} \\times {dia_cm} \\times {tw_cm} = \\mathbf{{{v_bolt_bear:,.0f}}}$ kg</span>
            </div>
            <div class="note" style="margin-left: 10px;">Note: Bearing uses Beam's Ultimate Strength ($F_u={fu}$), not the Bolt's.</div>
            
            <h5>3. Result</h5>
            <ul>
                <li><b>Design Capacity per Bolt:</b> Min({v_bolt_shear:,.0f}, {v_bolt_bear:,.0f}) = <b>{v_bolt:,.0f} kg</b></li>
                <li><b>Required Bolts:</b> ${V_design:,.0f} / {v_bolt:,.0f} = {V_design/v_bolt:.2f} \\rightarrow$ <b>{req_bolt} pcs</b></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# --- TAB 3: LOAD TABLE ---
with tab3:
    st.subheader("Reference Load Table")
    # Generate Data
    t_spans = np.arange(2, 12.5, 0.5)
    t_rows = []
    for l in t_spans:
        res_t = get_capacity(l)
        v_act_t = res_t["w_safe"] * l / 2
        t_rows.append({
            "Span (m)": l,
            "Max Load (kg/m)": res_t["w_safe"],
            "Gov. Case": res_t["cause"],
            "V_actual (kg)": v_act_t,
            "Shear Ratio (%)": (v_act_t/V_cap)*100
        })
    df_res = pd.DataFrame(t_rows)
    st.dataframe(df_res.style.format({
        "Span (m)": "{:.1f}",
        "Max Load (kg/m)": "{:,.0f}",
        "V_actual (kg)": "{:,.0f}",
        "Shear Ratio (%)": "{:.1f}"
    }), use_container_width=True, height=600)

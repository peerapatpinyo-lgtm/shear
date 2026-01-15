# connection_design.py (V29 - Integrated UI & Logic)
import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    # --- เพิ่มส่วนเลือก Thread Condition ที่หน้า UI ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔩 Bolt Specification")
    thread_type = st.sidebar.radio(
        "Thread Condition", 
        ["N (Included)", "X (Excluded)"], 
        help="N: เกลียวอยู่ในระนาบเฉือน | X: เกลียวนอกระนาบเฉือน (กำลังสูงกว่า)",
        index=0
    )[0] # เอาเฉพาะตัวอักษรหน้า N หรือ X

    p = section_data
    h_mm, tw_mm = p['h'], p['tw']
    tw_cm = tw_mm / 10
    Fy, Fu = 2450, 4000 # SS400 (kg/cm2)

    # 1. BOLT GEOMETRY
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    Ab = b_areas.get(bolt_size, 3.14)
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10
    dh_cm = (d_mm + 2) / 10 

    # 2. NOMINAL STRENGTHS (AISC Table J3.2)
    # อัปเดตค่า Fnv ตามเกรดและสถานะเกลียวที่เลือกจาก UI
    bolt_map = {
        "A325 (High Strength)": {"Fnv_N": 3795, "Fnv_X": 4780, "Fnt": 6325},
        "Grade 8.8 (Standard)": {"Fnv_N": 3200, "Fnv_X": 4000, "Fnt": 5300},
        "A490 (Premium)":       {"Fnv_N": 4780, "Fnv_X": 5975, "Fnt": 7940}
    }
    spec = bolt_map.get(bolt_grade, bolt_map["Grade 8.8 (Standard)"])
    Fnv = spec["Fnv_N"] if thread_type == "N" else spec["Fnv_X"]
    Fnt = spec["Fnt"]

    # 3. DESIGN PHILOSOPHY (LRFD vs ASD)
    if is_lrfd:
        phi, omega = 0.75, 1.00
        method_name = "LRFD Design"
        calc_label = r"\phi R_n = 0.75 \times"
    else:
        phi, omega = 1.00, 2.00
        method_name = "ASD Design"
        calc_label = r"R_n / \Omega = R_n / 2.00 ="

    # 4. CAPACITIES
    rn_shear_1b = Fnv * Ab
    rn_bearing_1b = 2.4 * d_cm * tw_cm * Fu
    cap_1b_shear = (phi * min(rn_shear_1b, rn_bearing_1b)) / omega
    
    n_bolts = max(2, math.ceil(V_design / cap_1b_shear))
    if n_bolts % 2 != 0: n_bolts += 1
    n_rows = n_bolts // 2

    # --- Limit States ---
    Rn_bolt_shear = n_bolts * Fnv * Ab
    
    # Combined Force Interaction (J3.7)
    frv = V_design / (n_bolts * Ab)
    if is_lrfd:
        Fnt_prime = min(1.3 * Fnt - (Fnt / (0.75 * Fnv)) * frv, Fnt)
    else:
        Fnt_prime = min(1.3 * Fnt - (2.0 * Fnt / Fnv) * frv, Fnt)
    Rn_combined = n_bolts * Fnt_prime * Ab
    
    caps = {
        "Bolt Shear": (phi * Rn_bolt_shear) / omega,
        "Combined T-V": (phi * Rn_combined) / omega,
        "Bearing Check": (phi * n_bolts * rn_bearing_1b) / omega
    }

    # --- UI RENDERING ---
    st.title(f"🔍 {method_name}")
    st.subheader(f"Bolt Grade: {bolt_grade} | Condition: Type {thread_type}")
    
    # Metrics
    cols = st.columns(3)
    for i, (name, val) in enumerate(caps.items()):
        force = V_design if name != "Combined T-V" else T_design
        ratio = force / val if val > 0 else 0
        cols[i].metric(name, f"{val:,.0f} kg", f"Ratio {ratio:.2f}", delta_color="normal" if ratio <= 1 else "inverse")

    # Sketch (คงไว้ตามที่คุณชอบ)
    st.divider()
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, y0=0, x1=10, y1=h_mm, fillcolor="rgba(37, 99, 235, 0.1)", line_color="#2563eb")
    start_y = (h_mm/2) - ((n_rows-1)*(3*d_mm))/2
    for r in range(n_rows):
        y = start_y + r*(3*d_mm)
        for x in [3, 7]: fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers', marker=dict(size=14, color='#ef4444')))
    fig.update_layout(xaxis_visible=False, yaxis_visible=False, height=300, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig, use_container_width=True)

    # Calculation Detail
    with st.expander("📖 รายการคำนวณละเอียด (AISC 360-16)", expanded=True):
        st.latex(fr"F_{{nv}} = {Fnv} \text{{ kg/cm}}^2 \quad (\text{{Type }} {thread_type})")
        st.latex(fr"R_n = F_{{nv}} A_b N_b = {Rn_bolt_shear:,.0f} \text{{ kg}}")
        st.latex(fr"{calc_label} {Rn_bolt_shear:,.0f} = {caps['Bolt Shear']:,.0f} \text{{ kg}}")

    return n_bolts, cap_1b_shear

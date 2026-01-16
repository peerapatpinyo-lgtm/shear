import streamlit as st
import pandas as pd
import math
import plotly.graph_objects as go

def render_connection_tab(V_design_from_tab1, default_bolt_size, method, is_lrfd, section_data, conn_type, default_bolt_grade, default_mat_grade):
    """
    ฟังก์ชันหลักสำหรับแสดงผล Tab 2 แบบ Professional Engineering Dashboard
    """
    
    # --- 1. SETUP STYLE ---
    st.markdown("""
    <style>
        .input-card { background-color: #f8fafc; padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 20px; }
        .result-card { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #3b82f6; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 15px; }
        .pass-card { border-left-color: #22c55e !important; }
        .fail-card { border-left-color: #ef4444 !important; }
        .metric-label { font-size: 14px; color: #64748b; font-weight: 600; text-transform: uppercase; }
        .metric-value { font-size: 24px; font-weight: 800; color: #1e293b; }
        .sub-metric { font-size: 12px; color: #94a3b8; }
        hr { margin: 15px 0; }
    </style>
    """, unsafe_allow_html=True)

    # --- 2. HEADER INFO ---
    col_head1, col_head2 = st.columns([2, 1])
    with col_head1:
        st.markdown(f"### 🔩 {conn_type} Design")
        st.caption(f"Designing for Beam: **{section_data.get('name', 'Custom Section')}** | Method: **{method}**")
    with col_head2:
        st.info(f"⚡ Design Load ($V_u$): **{V_design_from_tab1:,.0f} kg**")

    st.divider()

    # --- 3. LAYOUT: LEFT (INPUTS) | RIGHT (RESULTS) ---
    col_input, col_result = st.columns([1, 1.5], gap="large")

    # ==========================================
    # 🟠 LEFT COLUMN: INPUT CONTROLS
    # ==========================================
    with col_input:
        st.markdown("#### ⚙️ Configuration")
        
        with st.container():
            st.markdown('<div class="input-card">', unsafe_allow_html=True)
            st.markdown("**1. Bolt Settings**")
            c1, c2 = st.columns(2)
            with c1:
                # แปลง M20 -> 20 เพื่อใช้คำนวณ
                size_map = {"M12": 1.2, "M16": 1.6, "M20": 2.0, "M22": 2.2, "M24": 2.4, "M27": 2.7}
                b_size_str = st.selectbox("Bolt Size", list(size_map.keys()), index=list(size_map.keys()).index(default_bolt_size) if default_bolt_size in size_map else 2)
                d_bolt = size_map[b_size_str] # cm
            with c2:
                grades = ["A325 (High Strength)", "Grade 8.8", "A490"]
                try:
                    idx_grade = grades.index(default_bolt_grade)
                except:
                    idx_grade = 0
                b_grade = st.selectbox("Bolt Grade", grades, index=idx_grade)

            st.markdown("---")
            st.markdown("**2. Geometry (Plate)**")
            
            # Smart Default based on Section Depth
            h_beam = section_data.get('h', 400)/10 # cm
            default_rows = max(2, int(h_beam / 8))
            
            row_c1, row_c2 = st.columns(2)
            n_rows = row_c1.number_input("Rows of Bolts", min_value=1, value=default_rows)
            n_cols = row_c2.number_input("Columns", min_value=1, value=1)
            
            geo_c1, geo_c2 = st.columns(2)
            pitch = geo_c1.number_input("Pitch (cm)", min_value=3.0, value=7.5, step=0.5)
            edge_dist = geo_c2.number_input("Edge Dist (cm)", min_value=2.0, value=4.0, step=0.5)
            
            st.markdown("---")
            st.markdown("**3. Plate & Weld**")
            pl_thick = st.selectbox("Plate Thickness (mm)", [6, 9, 10, 12, 16, 20, 25], index=2)
            weld_sz = st.number_input("Weld Size (mm)", min_value=3, value=6)
            
            # Material Properties
            fy_pl = 2500 if "A36" in default_mat_grade or "SS400" in default_mat_grade else 3500
            fu_pl = 4000 if fy_pl == 2500 else 4900
            
            st.markdown('</div>', unsafe_allow_html=True)

            # Auto Calculate Properties
            h_plate = (n_rows - 1) * pitch + (2 * edge_dist)
            st.caption(f"ℹ️ Calculated Plate Height: **{h_plate:.1f} cm** (Beam Depth: {h_beam:.1f} cm)")
            if h_plate > h_beam:
                st.error("⚠️ Plate height exceeds beam depth!")

    # ==========================================
    # 🔵 CORE CALCULATION ENGINE
    # ==========================================
    # 1. Bolt Capacity
    # Shear Area
    Ab = math.pi * (d_bolt**2) / 4
    # Bolt Strength (Simplified approximation for demo)
    if "A325" in b_grade: Fnv = 3720 # kg/cm2 (approx LRFD)
    elif "A490" in b_grade: Fnv = 4690
    else: Fnv = 2800 # Gr 8.8 approx
    
    if not is_lrfd: Fnv = Fnv / 1.5 # Convert to ASD approx
    
    phi_bolt = 0.75 if is_lrfd else 1.0 # Factor already in allowable for ASD usually, but keeping structure
    Rn_bolt = Fnv * Ab 
    n_bolts = n_rows * n_cols
    cap_bolt_shear = n_bolts * Rn_bolt
    
    # 2. Bolt Bearing on Plate
    # Rn = 1.2 * Lc * t * Fu <= 2.4 * d * t * Fu
    # Simplified: 2.4 d t Fu (Upper limit)
    phi_bearing = 0.75 if is_lrfd else 1.0 # Ohm = 2.00 for ASD -> 1/2 = 0.5
    Rn_bearing_unit = 2.4 * d_bolt * (pl_thick/10) * fu_pl
    if not is_lrfd: Rn_bearing_unit = Rn_bearing_unit / 2.0
    cap_bolt_bearing = n_bolts * Rn_bearing_unit
    
    # 3. Plate Shear Yielding
    Ag_plate = h_plate * (pl_thick/10)
    phi_y = 1.00 if is_lrfd else 1.0 # Ohm = 1.50 -> 0.66
    Rn_y = 0.60 * fy_pl * Ag_plate
    if not is_lrfd: Rn_y = Rn_y / 1.50
    cap_plate_yield = Rn_y

    # 4. Plate Shear Rupture
    # An = Ag - n * (d+0.2) * t
    An_plate = Ag_plate - (n_rows * (d_bolt + 0.2) * (pl_thick/10))
    phi_r = 0.75 if is_lrfd else 1.0 # Ohm = 2.00 -> 0.5
    Rn_r = 0.60 * fu_pl * An_plate
    if not is_lrfd: Rn_r = Rn_r / 2.00
    cap_plate_rupture = Rn_r
    
    # 5. Weld Capacity
    # Fw = 0.60 * FEXX (70ksi -> 4900 ksc)
    Fexx = 4900
    Fn_weld = 0.60 * Fexx
    Aw_weld = 0.707 * (weld_sz/10) * h_plate * 2 # 2 sides
    phi_w = 0.75 if is_lrfd else 1.0 # Ohm = 2.00
    Rn_w = Fn_weld * Aw_weld
    if not is_lrfd: Rn_w = Rn_w / 2.00
    cap_weld = Rn_w

    # Summary
    capacities = {
        "Bolt Shear": cap_bolt_shear,
        "Bolt Bearing": cap_bolt_bearing,
        "Plate Yield": cap_plate_yield,
        "Plate Rupture": cap_plate_rupture,
        "Weld Shear": cap_weld
    }
    min_cap = min(capacities.values())
    gov_mode = min(capacities, key=capacities.get)
    
    # Check
    ratio = V_design_from_tab1 / min_cap if min_cap > 0 else 999
    is_pass = ratio <= 1.0
    
    status_color = "#22c55e" if is_pass else "#ef4444" # Green / Red
    status_text = "PASS" if is_pass else "FAIL"
    status_class = "pass-card" if is_pass else "fail-card"

    # ==========================================
    # 🟠 RIGHT COLUMN: DASHBOARD RESULTS
    # ==========================================
    with col_result:
        st.markdown(f"#### 📊 Analysis Results")
        
        # 1. Main Status Card
        st.markdown(f"""
        <div class="result-card {status_class}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div class="metric-label">Overall Status</div>
                    <div style="font-size: 32px; font-weight:900; color:{status_color};">{status_text}</div>
                </div>
                <div style="text-align:right;">
                    <div class="metric-label">Efficiency Ratio</div>
                    <div style="font-size: 32px; font-weight:900; color:#334155;">{ratio:.2f}</div>
                </div>
            </div>
            <div style="margin-top:15px;">
                <div class="metric-label">Capacity vs Load</div>
                <div style="font-size:16px; color:#475569;">
                    Capacity: <b>{min_cap:,.0f} kg</b> <span style="color:#cbd5e1;">|</span> Load: <b>{V_design_from_tab1:,.0f} kg</b>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. Detailed Breakdown (Progress Bars)
        st.markdown("**Critical Checks Breakdown**")
        
        for name, cap in capacities.items():
            this_ratio = V_design_from_tab1 / cap if cap > 0 else 1.5
            bar_color = "#22c55e" if this_ratio <= 1.0 else "#ef4444"
            if this_ratio > 1.0: this_ratio = 1.0 # Clip for visual
            
            c_name, c_val = st.columns([2, 1])
            c_name.markdown(f"<small>{name}</small>", unsafe_allow_html=True)
            c_val.markdown(f"<small style='float:right;'>{cap:,.0f} kg</small>", unsafe_allow_html=True)
            st.progress(this_ratio)
        
        st.info(f"💡 **Governing Failure Mode:** {gov_mode}")

        # 3. Quick Drawing (Sketch)
        with st.expander("📐 View Geometry Sketch", expanded=True):
            # Create simple scatter plot for bolts
            fig = go.Figure()
            
            # Plate outline
            fig.add_shape(type="rect",
                x0=0, y0=0, x1=15, y1=h_plate,
                line=dict(color="RoyalBlue"), fillcolor="LightSkyBlue", opacity=0.3
            )
            
            # Bolt coordinates
            bx = []
            by = []
            start_y = edge_dist
            for c in range(n_cols):
                for r in range(n_rows):
                    bx.append(5 + c*5) # Offset X
                    by.append(start_y + r*pitch)
            
            fig.add_trace(go.Scatter(
                x=bx, y=by, mode='markers',
                marker=dict(size=d_bolt*8, color='black', symbol='hexagon'),
                name='Bolts'
            ))
            
            fig.update_layout(
                width=300, height=300, 
                xaxis=dict(visible=False, range=[-2, 20]), 
                yaxis=dict(visible=False, range=[-2, h_plate+2]),
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)

    # --- 4. STEP-BY-STEP CALCULATION (Expandable) ---
    st.markdown("---")
    with st.expander("📝 Show Detailed Calculation Steps (Math)", expanded=False):
        st.markdown("#### Calculation Details")
        st.latex(r"V_{u} = " + f"{V_design_from_tab1:,.0f}" + r" \text{ kg}")
        
        st.markdown(f"**1. Bolt Shear Capacity ({'LRFD' if is_lrfd else 'ASD'})**")
        st.latex(r"\phi R_n = n \times A_b \times F_{nv} \times \phi")
        st.latex(f"= {n_bolts} \\times {Ab:.2f} \\times {Fnv:.0f} \\times 1.0 = \\mathbf{{{cap_bolt_shear:,.0f} \\text{{ kg}}}}")
        
        st.markdown("**2. Bolt Bearing Capacity**")
        st.latex(r"\phi R_n = n \times (2.4 d t F_u)")
        st.latex(f"= {n_bolts} \\times (2.4 \\times {d_bolt} \\times {pl_thick/10} \\times {fu_pl}) = \\mathbf{{{cap_bolt_bearing:,.0f} \\text{{ kg}}}}")
        
        st.markdown("**3. Plate Shear Yielding**")
        st.latex(r"\phi R_n = 0.60 F_y A_g")
        st.latex(f"= 0.60 \\times {fy_pl} \\times {Ag_plate:.2f} = \\mathbf{{{cap_plate_yield:,.0f} \\text{{ kg}}}}")
        
        st.markdown("**4. Weld Capacity**")
        st.latex(r"\phi R_n = 0.707 w L \times (0.60 F_{EXX}) \times 2")
        st.latex(f"= \\mathbf{{{cap_weld:,.0f} \\text{{ kg}}}}")

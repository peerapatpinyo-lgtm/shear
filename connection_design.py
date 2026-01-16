import streamlit as st
import math
import plotly.graph_objects as go
import drawing_utils
import calculation_report

def render_connection_tab(V_design_from_tab1, default_bolt_size, method, is_lrfd, section_data, conn_type, default_bolt_grade, default_mat_grade):
    
    # Styles
    st.markdown("""
    <style>
        .input-card { background-color: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 15px; }
        .summary-table { font-size: 13px; width: 100%; border-collapse: collapse; margin-top: 5px; }
        .summary-table th { background-color: #f1f5f9; padding: 6px; border-bottom: 2px solid #cbd5e1; font-weight: bold; color: #334155; }
        .summary-table td { padding: 6px; border-bottom: 1px solid #e2e8f0; vertical-align: middle; }
        .pass-text { color: #166534; font-weight: bold; }
        .fail-text { color: #991b1b; font-weight: bold; }
        .hl-row { background-color: #fff7ed; }
    </style>
    """, unsafe_allow_html=True)

    col_head1, col_head2 = st.columns([2, 1])
    with col_head1:
        st.markdown(f"### 🔩 {conn_type} Design (Phase 1: Advanced)")
        st.caption(f"Beam: **{section_data.get('name', 'Custom')}** | Method: **{method}**")
    with col_head2:
        st.info(f"⚡ Design Load ($V_u$): **{V_design_from_tab1:,.0f} kg**")
    st.divider()

    col_input, col_result = st.columns([1, 1.4], gap="medium")

    # --- INPUT ---
    with col_input:
        st.markdown("#### 🛠️ Configuration")
        
        with st.expander("1. Beam & Material Specs", expanded=True):
            # Extract default properties
            def_tw = section_data.get('tw', 8)
            c1, c2 = st.columns(2)
            beam_tw = c1.number_input("Beam Web t (mm)", 3.0, 30.0, float(def_tw), step=0.5, help="Crucial for Bearing Check")
            b_grade = c2.selectbox("Bolt Grade", ["A325", "Gr. 8.8", "A490"])
            
            # Bolt & Plate
            c3, c4 = st.columns(2)
            size_map = {"M12": 1.2, "M16": 1.6, "M20": 2.0, "M22": 2.2, "M24": 2.4}
            b_size_str = c3.selectbox("Bolt Size", list(size_map.keys()), index=2)
            d_bolt = size_map[b_size_str]
            pl_thick = c4.select_slider("Plate T (mm)", [6, 9, 10, 12, 16, 19, 20, 25], value=10)
            weld_sz = st.number_input("Weld Size (mm)", 3, 12, 6)

        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.markdown("**2. Geometry & Layout**")
        c_w, c_h = st.columns(2)
        w_plate = c_w.number_input("Plate W (mm)", 50, 500, 150, step=10)
        h_plate = c_h.number_input("Plate H (mm)", 50, 1000, 300, step=10)
        
        c_r, c_c = st.columns(2)
        n_rows = c_r.number_input("Rows", 1, 10, 3)
        n_cols = c_c.number_input("Cols", 1, 4, 1)
        
        st.caption("Dimensions (mm)")
        v1, v2 = st.columns(2)
        pitch_v = v1.number_input("Pitch V", 30, 200, 75)
        edge_v = v2.number_input("Edge V", 20, 100, 40)
        
        h1, h2 = st.columns(2)
        dist_weld = h1.number_input("To Weld (e1)", 20, 100, 50)
        pitch_h = h2.number_input("Pitch H", 30, 200, 60) if n_cols > 1 else 0

        # Quick Geom Check
        req_h = (n_rows - 1) * pitch_v + (2 * edge_v)
        st.markdown(f"<div style='font-size:12px; color:{'green' if h_plate >= req_h else 'red'}'>Min H required: {req_h} mm</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ==========================================
        # 3. SYNCHRONIZED CALC (Elastic Method)
        # ==========================================
        # Constants
        V_kN = V_design_from_tab1 / 101.97
        fy_ksc = 2500 if "A36" in default_mat_grade else 3500
        Fy, Fu = (250, 400) if fy_ksc == 2500 else (345, 490)
        Fnv = 372 if "A325" in b_grade else 457
        
        # Factors
        if is_lrfd:
            phi = 0.75; phi_y = 1.0
            def get_c(Rn, p=phi): return Rn * p
        else:
            om = 2.00; om_y = 1.5
            def get_c(Rn, o=om): return Rn / o

        # 1. Eccentricity Calc (Elastic)
        n_total = n_rows * n_cols
        d = d_bolt * 10
        Ab = math.pi * d**2 / 4
        
        # Centroid & Eccentricity
        x_bar = ((n_cols - 1) * pitch_h) / 2 if n_cols > 1 else 0
        e_ecc = dist_weld + x_bar
        M_u = V_kN * e_ecc # kN-mm
        
        # Polar Inertia (Sum r^2)
        sum_r2 = 0
        for c in range(n_cols):
            for r in range(n_rows):
                dx = (c * pitch_h) - x_bar
                dy = (r * pitch_v) - ((n_rows-1)*pitch_v)/2
                sum_r2 += (dx**2 + dy**2)
        
        # Forces on Critical Bolt
        # Direct
        Rv_dir = V_kN / n_total
        # Moment (Crit bolt is furthest corner)
        cx = x_bar
        cy = ((n_rows-1)*pitch_v)/2
        Rv_mom = (M_u * cx)/sum_r2 if sum_r2>0 else 0
        Rh_mom = (M_u * cy)/sum_r2 if sum_r2>0 else 0
        
        # Resultant Force per Bolt
        V_bolt_res = math.sqrt((Rv_dir + Rv_mom)**2 + Rh_mom**2)
        
        # Capacity Per Bolt
        Rn_bolt = Fnv * Ab / 1000
        cap_bolt_1 = get_c(Rn_bolt)
        
        # 2. Bearing (Min of Plate vs Web)
        Rn_br_pl = 2.4 * d * pl_thick * Fu / 1000
        Rn_br_wb = 2.4 * d * beam_tw * Fu / 1000 # Beam Web Check
        cap_br_1 = min(get_c(Rn_br_pl), get_c(Rn_br_wb))

        # 3. Plate Checks (Gross, Net, Block, Weld) -> Standard
        Ag = h_plate * pl_thick
        Rn_yld = 0.6 * Fy * Ag / 1000
        cap_yld = get_c(Rn_yld, phi_y if is_lrfd else om_y)
        
        h_hole = d + 2
        An = (h_plate - n_rows*h_hole) * pl_thick
        Rn_rup = 0.6 * Fu * An / 1000
        cap_rup = get_c(Rn_rup)
        
        # Block Shear
        l_gv = (n_rows-1)*pitch_v + edge_v
        rem_edge = w_plate - (dist_weld + (n_cols-1)*pitch_h if n_cols > 1 else dist_weld)
        Agv = l_gv * pl_thick
        Anv = (l_gv - (n_rows-0.5)*h_hole) * pl_thick
        Ant = (rem_edge - 0.5*h_hole) * pl_thick
        Rn_blk = min(0.6*Fu*Anv + Fu*Ant, 0.6*Fy*Agv + Fu*Ant) / 1000
        cap_blk = get_c(Rn_blk)
        
        # Weld
        Rn_weld = 0.6 * 480 * 0.707 * weld_sz * (h_plate*2) / 1000
        cap_weld = get_c(Rn_weld)

        # 4. Summary List
        # Note: Bolt Checks are based on Ratio, so we show Equiv Capacity
        # Equiv Cap = Load / Ratio.
        # Ratio = V_bolt_res / cap_bolt_1
        ratio_bolt = V_bolt_res / cap_bolt_1
        equiv_cap_bolt = V_kN / ratio_bolt if ratio_bolt > 0 else 999
        
        ratio_bear = V_bolt_res / cap_br_1
        equiv_cap_bear = V_kN / ratio_bear if ratio_bear > 0 else 999
        
        checks = {
            "Bolt Eccentricity": [equiv_cap_bolt, ratio_bolt],
            "Bearing (Web/Pl)": [equiv_cap_bear, ratio_bear],
            "Plate Yield": [cap_yld, V_kN/cap_yld],
            "Plate Rupture": [cap_rup, V_kN/cap_rup],
            "Block Shear": [cap_blk, V_kN/cap_blk],
            "Weld Strength": [cap_weld, V_kN/cap_weld]
        }
        
        max_r = max([v[1] for v in checks.values()])
        is_pass = max_r <= 1.0

        # --- SUMMARY TABLE ---
        st.markdown("#### 🏁 Final Status")
        st.markdown(f"<div style='background:{'#dcfce7' if is_pass else '#fee2e2'}; color:{'#166534' if is_pass else '#991b1b'}; padding:8px; border-radius:6px; text-align:center; font-weight:bold;'>{'PASS ✅' if is_pass else 'FAIL ❌'} (Ratio: {max_r:.2f})</div>", unsafe_allow_html=True)
        
        rows = ""
        for k, v in checks.items():
            cap, rat = v[0], v[1]
            cls = "pass-text" if rat <= 1.0 else "fail-text"
            rows += f"<tr><td>{k}</td><td align='center'>{cap:.1f}</td><td align='center' class='{cls}'>{rat:.2f}</td></tr>"
            
        st.markdown(f"""
        <table class="summary-table">
            <thead><tr><th>Check</th><th align='center'>Cap (kN)</th><th align='center'>Ratio</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
        """, unsafe_allow_html=True)
        
        with st.expander("ℹ️ What is Bolt Eccentricity?"):
            st.caption(f"Load is applied at {e_ecc:.1f} mm from weld. This creates Moment M = {M_u/1000:.1f} kN-m. Resultant force on bolt = {V_bolt_res:.2f} kN (vs {Rv_dir:.2f} kN pure shear).")

    # --- RIGHT SIDE ---
    with col_result:
        t1, t2 = st.tabs(["📐 Drawing", "📝 Full Report"])
        with t1:
            # Drawing Logic (Simplified for brevity, assuming drawing_utils exists)
            beam_dict = {'h': section_data.get('h', 400), 'b': section_data.get('b', 200), 'tf': section_data.get('tf', 13), 'tw': beam_tw}
            plate_dict = {'h': h_plate, 'w': w_plate, 't': pl_thick, 'e1': dist_weld, 'lv': edge_v, 'weld_size': weld_sz}
            bolt_dict = {'d': d, 'rows': n_rows, 'cols': n_cols, 's_v': pitch_v, 's_h': pitch_h}
            
            try:
                fig = drawing_utils.create_front_view(beam_dict, plate_dict, bolt_dict)
                st.plotly_chart(fig, use_container_width=True)
            except: st.error("Drawing module needed")
            
        with t2:
             # Report Logic
            beam_data_rpt = {'tw': beam_tw, 'Fu': Fu}
            plate_data_rpt = {'t': pl_thick, 'h': h_plate, 'w': w_plate, 'e1': dist_weld, 'lv': edge_v, 'l_side': rem_edge, 'weld_size': weld_sz, 'Fy': Fy, 'Fu': Fu}
            bolt_data_rpt = {'d': d, 'rows': n_rows, 'cols': n_cols, 'Fnv': Fnv, 's_v': pitch_v, 's_h': pitch_h}
            
            rpt = calculation_report.generate_report(V_kN, beam_data_rpt, plate_data_rpt, bolt_data_rpt, is_lrfd, default_mat_grade, b_grade)
            
            if "#### 🏁 Summary" in rpt:
                st.markdown(rpt.split("#### 🏁 Summary")[0] + "\n\n*(See summary on left)*", unsafe_allow_html=True)
            else:
                st.markdown(rpt, unsafe_allow_html=True)

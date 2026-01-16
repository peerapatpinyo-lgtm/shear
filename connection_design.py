import streamlit as st
import math
import drawing_utils  # เรียกใช้ไฟล์ drawing_utils.py

def render_connection_tab(V_design_from_tab1, default_bolt_size, method, is_lrfd, section_data, conn_type, default_bolt_grade, default_mat_grade):
    
    # --- STYLE & LAYOUT ---
    st.markdown("""
    <style>
        .input-card { background-color: #f8fafc; padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 20px; }
        .result-card { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #3b82f6; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 15px; }
        .metric-label { font-size: 14px; color: #64748b; font-weight: 600; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

    # --- HEADER ---
    col_head1, col_head2 = st.columns([2, 1])
    with col_head1:
        st.markdown(f"### 🔩 {conn_type} Design")
        st.caption(f"Beam: **{section_data.get('name', 'Custom Section')}** | Method: **{method}**")
    with col_head2:
        st.info(f"⚡ Design Load ($V_u$): **{V_design_from_tab1:,.0f} kg**")
    st.divider()

    # --- MAIN COLUMNS ---
    col_input, col_result = st.columns([1, 1.5], gap="large")

    # ==========================
    # 1. INPUT SECTION
    # ==========================
    with col_input:
        st.markdown("#### ⚙️ Configuration")
        with st.container():
            st.markdown('<div class="input-card">', unsafe_allow_html=True)
            
            # Bolt Params
            st.markdown("**1. Bolt Settings**")
            c1, c2 = st.columns(2)
            with c1:
                size_map = {"M12": 1.2, "M16": 1.6, "M20": 2.0, "M22": 2.2, "M24": 2.4, "M27": 2.7}
                try:
                    def_idx = list(size_map.keys()).index(default_bolt_size)
                except ValueError:
                    def_idx = 2
                b_size_str = st.selectbox("Bolt Size", list(size_map.keys()), index=def_idx)
                d_bolt = size_map[b_size_str] # cm
            with c2:
                grades = ["A325 (High Strength)", "Grade 8.8", "A490"]
                b_grade = st.selectbox("Bolt Grade", grades)

            st.markdown("---")
            
            # Plate Geometry
            st.markdown("**2. Geometry (Plate)**")
            h_beam = section_data.get('h', 400)/10 # cm
            default_rows = max(2, int(h_beam / 8))
            
            row_c1, row_c2 = st.columns(2)
            n_rows = row_c1.number_input("Rows", min_value=1, value=default_rows)
            n_cols = row_c2.number_input("Columns", min_value=1, value=1)
            
            geo_c1, geo_c2 = st.columns(2)
            pitch = geo_c1.number_input("Pitch (cm)", min_value=3.0, value=7.5, step=0.5)
            edge_dist = geo_c2.number_input("Edge Dist (cm)", min_value=3.0, value=4.0, step=0.5)
            
            st.markdown("---")
            
            # Plate & Weld Spec
            st.markdown("**3. Plate & Weld**")
            pl_thick = st.selectbox("Plate Thick (mm)", [6, 9, 10, 12, 16, 20, 25], index=2)
            weld_sz = st.number_input("Weld Size (mm)", min_value=3, value=6)
            
            # Material
            fy_pl = 2500 if "A36" in default_mat_grade or "SS400" in default_mat_grade else 3500
            fu_pl = 4000 if fy_pl == 2500 else 4900
            
            st.markdown('</div>', unsafe_allow_html=True)

            # Validation
            h_plate = (n_rows - 1) * pitch + (2 * edge_dist) # cm
            if h_plate > h_beam:
                st.error(f"⚠️ Plate height ({h_plate}cm) > Beam depth ({h_beam}cm)")

    # ==========================
    # 2. CALCULATION LOGIC
    # ==========================
    Ab = math.pi * (d_bolt**2) / 4
    Fnv = 3720 if "A325" in b_grade else (4690 if "A490" in b_grade else 2800)
    if not is_lrfd: Fnv = Fnv / 1.5
    cap_bolt_shear = (n_rows * n_cols) * (Fnv * Ab)
    
    Rn_bearing_unit = 2.4 * d_bolt * (pl_thick/10) * fu_pl
    if not is_lrfd: Rn_bearing_unit = Rn_bearing_unit / 2.0
    cap_bolt_bearing = (n_rows * n_cols) * Rn_bearing_unit
    
    Ag_plate = h_plate * (pl_thick/10)
    Rn_y = 0.60 * fy_pl * Ag_plate
    if not is_lrfd: Rn_y = Rn_y / 1.50
    cap_plate_yield = Rn_y

    An_plate = Ag_plate - (n_rows * (d_bolt + 0.2) * (pl_thick/10))
    Rn_r = 0.60 * fu_pl * An_plate
    if not is_lrfd: Rn_r = Rn_r / 2.00
    cap_plate_rupture = Rn_r
    
    Fn_weld = 0.60 * 4900 # E70XX
    Aw_weld = 0.707 * (weld_sz/10) * h_plate * 2
    Rn_w = Fn_weld * Aw_weld
    if not is_lrfd: Rn_w = Rn_w / 2.00
    cap_weld = Rn_w

    capacities = {
        "Bolt Shear": cap_bolt_shear, "Bolt Bearing": cap_bolt_bearing,
        "Plate Yield": cap_plate_yield, "Plate Rupture": cap_plate_rupture,
        "Weld Shear": cap_weld
    }
    min_cap = min(capacities.values())
    ratio = V_design_from_tab1 / min_cap if min_cap > 0 else 999
    is_pass = ratio <= 1.0

    # ==========================
    # 3. RESULT & DRAWING DASHBOARD
    # ==========================
    with col_result:
        status_color = "#22c55e" if is_pass else "#ef4444"
        status_text = "PASS" if is_pass else "FAIL"
        
        # Summary Card
        st.markdown(f"""
        <div class="result-card" style="border-left-color: {status_color}">
            <div style="display:flex; justify-content:space-between;">
                <div>
                    <span class="metric-label">Status</span><br>
                    <span style="font-size:32px; font-weight:900; color:{status_color}">{status_text}</span>
                </div>
                <div style="text-align:right;">
                    <span class="metric-label">Efficiency</span><br>
                    <span style="font-size:32px; font-weight:900;">{ratio:.2f}</span>
                </div>
            </div>
            <div style="margin-top:10px; font-size:14px; color:#64748b;">
                Governing: <b>{min(capacities, key=capacities.get)}</b> ({min_cap:,.0f} kg)
            </div>
        </div>
        """, unsafe_allow_html=True)

        for name, cap in capacities.items():
            r = V_design_from_tab1 / cap if cap > 0 else 1.5
            st.progress(min(r, 1.0), text=f"{name}: {cap:,.0f} kg (Ratio: {r:.2f})")

        st.markdown("---")
        
        # ==========================
        # 4. PLOTLY DRAWING SECTION (CORRECTED COORDINATES)
        # ==========================
        st.markdown("#### 📐 Construction Details")
        
        # Data Prep (mm)
        beam_h_mm = section_data.get('h', 400)
        beam_b_mm = section_data.get('b', 200)
        
        beam_dict = {
            'h': beam_h_mm,
            'b': beam_b_mm,
            'tf': section_data.get('tf', 13),
            'tw': section_data.get('tw', 8)
        }
        
        plate_dict = {
            'h': h_plate * 10,
            'w': 150,
            't': pl_thick,
            'e1': 50,
            'lv': edge_dist * 10,
            'weld_size': weld_sz
        }
        
        bolt_dict = {
            'd': d_bolt * 10,
            'rows': n_rows,
            'cols': n_cols,
            's_v': pitch * 10,
            's_h': 60
        }

        tab1, tab2, tab3 = st.tabs(["🖼️ Elevation (Front)", "🏗️ Plan (Top)", "✂️ Section (Side)"])
        
        # --- ฟังก์ชันจัดรูป (แก้ไขให้รองรับพิกัด Center: +/-) ---
        def fit_view(fig, x_range, y_range, height=500):
            fig.update_layout(
                height=height,
                margin=dict(l=20, r=20, t=40, b=20),
                # กำหนด Range แบบ Manual เพื่อบังคับให้มองเห็นทั้งค่าบวกและลบ
                xaxis=dict(range=x_range, visible=False, scaleanchor="y", scaleratio=1),
                yaxis=dict(range=y_range, visible=False),
                dragmode="pan",
                showlegend=False
            )
            return fig

        # ระยะขอบ (Padding)
        pad = 50 

        with tab1:
            try:
                fig_front = drawing_utils.create_front_view(beam_dict, plate_dict, bolt_dict)
                
                # [แก้ไข] Elevation View: 
                # แกน Y เป็นแบบ Center (ครึ่งบน +, ครึ่งล่าง -)
                # แกน X ส่วนใหญ่อาจจะเริ่มที่ 0 หรือ Center แต่เผื่อไว้ทั้งคู่
                
                y_max = (beam_h_mm / 2) + pad
                y_min = -(beam_h_mm / 2) - pad
                x_max = beam_b_mm + pad
                x_min = -pad # เผื่อซ้ายนิดหน่อยกรณีมีเส้นหนา
                
                st.plotly_chart(
                    fit_view(fig_front, [x_min, x_max], [y_min, y_max], height=550), 
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error: {e}")

        with tab2:
            try:
                fig_plan = drawing_utils.create_plan_view(beam_dict, plate_dict, bolt_dict)
                
                # [แก้ไข] Plan View:
                # แกน X (หน้ากว้างคาน) มักจะเป็น Center (ซ้าย -, ขวา +)
                # แกน Y (ความยาว) มักจะเป็นค่าบวก
                
                x_half = (beam_b_mm / 2) + pad
                st.plotly_chart(
                    fit_view(fig_plan, [-x_half, x_half], [-pad, 350+pad], height=400),
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error: {e}")

        with tab3:
            try:
                fig_side = drawing_utils.create_side_view(beam_dict, plate_dict, bolt_dict)
                
                # [แก้ไข] Section View:
                # แกน Y (ความสูง) เป็น Center (บน +, ล่าง -) เหมือน Front
                # แกน X (ความกว้างหน้าตัด) เป็น Center (ซ้าย -, ขวา +)
                
                y_max = (beam_h_mm / 2) + pad
                y_min = -(beam_h_mm / 2) - pad
                x_limit = 150 # กว้างพอประมาณสำหรับมองข้าง
                
                st.plotly_chart(
                    fit_view(fig_side, [-x_limit, x_limit], [y_min, y_max], height=550),
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error: {e}")

        st.caption("Interactive Drawing powered by Plotly")

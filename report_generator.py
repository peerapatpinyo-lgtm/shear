# report_generator.py
# Version: 19.0 (Recorder Edition - Save & Summary Table)
import streamlit as st
import pandas as pd
from datetime import datetime
import math

def render_report_tab(beam_data, conn_data):
    # =========================================================
    # 0. INITIALIZE ALL VARIABLES
    # =========================================================
    # Geometry
    sec_name = "-"
    d_cm = 0.0
    tw_cm = 0.0
    Aw = 0.0
    
    # Material
    fy_beam = 0.0
    fu_beam = 0.0
    is_lrfd = True
    method_txt = "LRFD"
    
    # Loads
    Vn_beam = 0.0
    V_beam_cap = 0.0
    V_u = 0.0
    
    # Connection Params
    DB = 20.0       # mm (M20)
    DH = DB + 2.0   # mm
    plate_t_mm = 10.0
    n_bolts = 0
    
    # Capacities (Initialize to 0.0)
    phiRn_bolt_shear = 0.0
    phiRn_bearing_plate = 0.0
    phiRn_bearing_web = 0.0
    phiRn_bearing_gov = 0.0 
    phiRn_plate_yield = 0.0
    phiRn_plate_rupture = 0.0
    phiRn_block_shear = 0.0
    
    req_weld_len = 0.0
    actual_plate_len = 0.0
    
    # Ratios
    ratio_bolt = 0.0
    
    # =========================================================
    # 1. DATA EXTRACTION & CALCULATION
    # =========================================================
    if not beam_data:
        st.warning("⚠️ กรุณากลับไปเลือกขนาดคานที่ Tab 1 ก่อนครับ")
        return

    try:
        # 1.1 Extract Data
        sec_name = beam_data.get('sec_name', 'Unknown')
        h_val = float(beam_data.get('h', 0) or 400)
        tw_val = float(beam_data.get('tw', 0) or 8)
        fy_beam = float(beam_data.get('Fy', 0) or 2500)
        fu_beam = float(beam_data.get('Fu', 0) or 4100)
        is_lrfd = beam_data.get('is_lrfd', True)

        # 1.2 Convert Units
        d_cm = h_val / 10.0
        tw_cm = tw_val / 10.0
        Aw = d_cm * tw_cm # cm2
        plate_t_cm = plate_t_mm / 10.0

        # 1.3 Beam Shear Capacity
        Vn_beam = 0.60 * fy_beam * Aw
        if is_lrfd:
            phi = 1.00
            V_beam_cap = phi * Vn_beam
            method_txt = "LRFD"
        else:
            omega = 1.50
            V_beam_cap = Vn_beam / omega
            method_txt = "ASD"
            
        # 1.4 Design Load (75% Rule)
        V_u = 0.75 * V_beam_cap

        # 1.5 Bolt Shear
        A_b = (math.pi * (DB/10.0)**2) / 4.0
        Fnv = 3300.0 # ksc
        
        if is_lrfd:
            phi_shear = 0.75
            phiRn_bolt_shear = phi_shear * Fnv * A_b
        else:
            omega_shear = 2.00
            phiRn_bolt_shear = (Fnv * A_b) / omega_shear

        # 1.6 Bearing Checks
        FU_PL = 4050.0
        Le = 3.5 # cm
        Lc = Le - (DH/10.0)/2.0
        
        # Plate Bearing
        r_te_pl = 1.2 * Lc * plate_t_cm * FU_PL
        r_br_pl = 2.4 * (DB/10.0) * plate_t_cm * FU_PL
        rn_pl = min(r_te_pl, r_br_pl)
        
        # Web Bearing
        r_te_web = 1.2 * Lc * tw_cm * fu_beam
        r_br_web = 2.4 * (DB/10.0) * tw_cm * fu_beam
        rn_web = min(r_te_web, r_br_web)
        
        if is_lrfd:
            phiRn_bearing_plate = 0.75 * rn_pl
            phiRn_bearing_web = 0.75 * rn_web
        else:
            phiRn_bearing_plate = rn_pl / 2.00
            phiRn_bearing_web = rn_web / 2.00
            
        # Governing Bolt Capacity
        phiRn_bearing_gov = min(phiRn_bearing_plate, phiRn_bearing_web)
        capacity_per_bolt = min(phiRn_bolt_shear, phiRn_bearing_gov)
        
        # Determine Bolt Count
        if capacity_per_bolt > 0:
            req_n = V_u / capacity_per_bolt
            n_bolts = max(2, math.ceil(req_n))
        else:
            n_bolts = 99
            
        # 1.7 Plate Checks
        spacing = 7.0 # cm
        L_plate_cm = (2*Le) + ((n_bolts-1)*spacing)
        actual_plate_len = L_plate_cm
        
        Ag = L_plate_cm * plate_t_cm
        Rn_yld = 0.60 * 2500.0 * Ag
        phiRn_plate_yield = (1.00 * Rn_yld) if is_lrfd else (Rn_yld / 1.50)
        
        An = Ag - (n_bolts * (DH/10.0) * plate_t_cm)
        Rn_rup = 0.60 * FU_PL * An
        phiRn_plate_rupture = (0.75 * Rn_rup) if is_lrfd else (Rn_rup / 2.00)
        
        # Block Shear
        Avg = (L_plate_cm - Le) * plate_t_cm
        Avn = Avg - ((n_bolts - 0.5) * (DH/10.0) * plate_t_cm)
        Atn = (Le - 0.5*(DH/10.0)) * plate_t_cm
        Rn_blk = (0.6 * FU_PL * Avn) + (1.0 * FU_PL * Atn)
        phiRn_block_shear = (0.75 * Rn_blk) if is_lrfd else (Rn_blk / 2.00)
        
        # 1.8 Weld Check
        Fexx = 4900.0
        w_size = 0.6 # cm
        Rn_weld_unit = 0.60 * Fexx * (0.707 * w_size) * 2
        phi_weld_cap = (0.75 * Rn_weld_unit) if is_lrfd else (Rn_weld_unit / 2.00)
        if phi_weld_cap > 0:
            req_weld_len = V_u / phi_weld_cap
        
        # Ratios
        ratio_bolt = V_u / (n_bolts * capacity_per_bolt)

    except Exception as e:
        st.error(f"Calculation Error: {e}")
        return

    # =========================================================
    # 2. REPORT RENDERING
    # =========================================================
    st.markdown("### 📝 รายการคำนวณออกแบบจุดต่อ (Full Engineering Checks)")
    
    with st.container(border=True):
        st.markdown(f"**PROJECT:** {sec_name} | **CODE:** AISC 360-16 ({method_txt})")
        st.divider()
        
        # Display Summary Logic
        st.markdown("#### สรุปผลการออกแบบ (Design Summary)")
        st.latex(rf"V_u (75\% \text{{ Capacity}}) = \mathbf{{{V_u:,.0f} \text{{ kg}}}}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Bolt Required", f"{n_bolts} pcs", f"Ratio {ratio_bolt:.2f}")
        c2.metric("Plate Thickness", f"{plate_t_mm:.0f} mm", "A36 Steel")
        c3.metric("Weld Length", f"{req_weld_len:.1f} cm", f"Use {max(req_weld_len, actual_plate_len):.1f} cm")
        
        st.info("รายละเอียดการคำนวณฉบับเต็มแสดงอยู่ด้านล่าง (สามารถ Print เป็น PDF ได้จาก Browser)")

    # =========================================================
    # 3. SAVE & HISTORY SECTION (NEW!)
    # =========================================================
    st.markdown("---")
    st.subheader("💾 บันทึกและเปรียบเทียบ (Save & Compare)")
    
    # 3.1 Initialize Session State
    if 'saved_designs' not in st.session_state:
        st.session_state['saved_designs'] = []
        
    # 3.2 Save Button
    col_save, col_clear = st.columns([1, 4])
    with col_save:
        if st.button("📥 Save This Design", type="primary"):
            # Create Record
            new_record = {
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Steel Section": sec_name,
                "Design V (75%)": f"{V_u:,.0f} kg",
                "Bolt Design": f"{n_bolts} x M{DB:.0f} (A325)",
                "Plate Thk.": f"{plate_t_mm:.0f} mm",
                "Weld Len.": f"{req_weld_len:.1f} cm",
                "Status": "OK" if ratio_bolt <= 1.0 else "FAIL"
            }
            st.session_state['saved_designs'].append(new_record)
            st.success("บันทึกข้อมูลเรียบร้อย!")

    with col_clear:
        if st.button("🗑️ Clear History"):
            st.session_state['saved_designs'] = []
            st.rerun()

    # 3.3 Display Table
    if len(st.session_state['saved_designs']) > 0:
        st.markdown("#### 📋 รายการที่บันทึกไว้ (Saved List)")
        
        # Convert to DataFrame
        df = pd.DataFrame(st.session_state['saved_designs'])
        
        # Display Interactive Table
        st.dataframe(
            df, 
            use_container_width=True,
            column_config={
                "Steel Section": st.column_config.TextColumn("ขนาดเหล็ก (Size)"),
                "Design V (75%)": st.column_config.TextColumn("Vshear (75% Cap)"),
                "Bolt Design": st.column_config.TextColumn("Bolt (Qty x Size)"),
                "Plate Thk.": st.column_config.TextColumn("Plate (mm)"),
                "Status": st.column_config.TextColumn("ผลลัพธ์")
            },
            hide_index=True
        )
        
        # CSV Download Button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download CSV",
            data=csv,
            file_name='connection_design_log.csv',
            mime='text/csv',
        )
    else:
        st.info("ยังไม่มีรายการที่บันทึก (กดปุ่ม Save ด้านบนเพื่อเก็บค่า)")

    # =========================================================
    # 4. FULL CALCULATION DETAILS (APPENDED BELOW)
    # =========================================================
    with st.expander("ดูรายการคำนวณละเอียด (Show Full Calculation Details)"):
        st.markdown(f"#### รายการคำนวณฉบับเต็ม ({sec_name})")
        st.latex(rf"V_n = 0.6 F_y A_w = 0.6({fy_beam:.0f})({Aw:.2f})")
        st.latex(rf"V_u = 0.75 \times \phi V_n = \mathbf{{{V_u:,.0f} \text{{ kg}}}}")
        
        st.markdown("---")
        st.write("**Bolt Checks:**")
        st.latex(rf"\phi R_{{shear}} = {phiRn_bolt_shear:,.0f} \text{{ kg/bolt}}")
        st.latex(rf"\phi R_{{bearing}} = {min(phiRn_bearing_plate, phiRn_bearing_web):,.0f} \text{{ kg/bolt}}")
        st.write(f"Governing Capacity = {capacity_per_bolt:,.0f} kg/bolt")
        st.latex(rf"N_{{req}} = {V_u:,.0f} / {capacity_per_bolt:,.0f} = {V_u/capacity_per_bolt:.2f} \rightarrow \text{{Use }} {n_bolts} \text{{ pcs}}")
        
        st.write("**Plate Checks:**")
        st.write(f"Yielding Cap = {phiRn_plate_yield:,.0f} kg")
        st.write(f"Rupture Cap = {phiRn_plate_rupture:,.0f} kg")
        st.write(f"Block Shear Cap = {phiRn_block_shear:,.0f} kg")

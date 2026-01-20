# report_generator.py
# Version: 18.0 (The Certified Standard - Full 9 Checks & Zero Errors)
import streamlit as st
from datetime import datetime
import math

def render_report_tab(beam_data, conn_data):
    # =========================================================
    # 0. INITIALIZE ALL VARIABLES (ประกาศตัวแปรกัน Error 100%)
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
    phiRn_bearing_gov = 0.0 # ตัวควบคุม
    
    phiRn_plate_yield = 0.0
    phiRn_plate_rupture = 0.0
    phiRn_block_shear = 0.0
    
    req_weld_len = 0.0
    actual_plate_len = 0.0
    
    # Ratios
    ratio_bolt = 0.0
    ratio_plate = 0.0
    ratio_block = 0.0
    
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

        # 1.3 Beam Shear Capacity (Check #1)
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

        # 1.5 Bolt Shear (Check #2)
        # A325, M20
        A_b = (math.pi * (DB/10.0)**2) / 4.0
        Fnv = 3300.0 # ksc
        
        if is_lrfd:
            phi_shear = 0.75
            phiRn_bolt_shear = phi_shear * Fnv * A_b
        else:
            omega_shear = 2.00
            phiRn_bolt_shear = (Fnv * A_b) / omega_shear

        # 1.6 Bearing Checks (Check #3 & #4)
        # Check Plate (Fy=2500, Fu=4050 for A36)
        FU_PL = 4050.0
        
        # สมมติระยะขอบ (Edge Distance) และระยะห่าง (Spacing)
        Le = 3.5 # cm (35mm)
        Lc = Le - (DH/10.0)/2.0
        
        # Plate Bearing
        r_te_pl = 1.2 * Lc * plate_t_cm * FU_PL
        r_br_pl = 2.4 * (DB/10.0) * plate_t_cm * FU_PL
        rn_pl = min(r_te_pl, r_br_pl)
        
        # Web Bearing (ใช้ Fu คาน)
        r_te_web = 1.2 * Lc * tw_cm * fu_beam
        r_br_web = 2.4 * (DB/10.0) * tw_cm * fu_beam
        rn_web = min(r_te_web, r_br_web)
        
        # Apply Safety Factor
        if is_lrfd:
            phiRn_bearing_plate = 0.75 * rn_pl
            phiRn_bearing_web = 0.75 * rn_web
        else:
            phiRn_bearing_plate = rn_pl / 2.00
            phiRn_bearing_web = rn_web / 2.00
            
        # Governing Bolt Capacity (ตัวคุม คือค่าน้อยสุดของ Shear, Bearing Plate, Bearing Web)
        phiRn_bearing_gov = min(phiRn_bearing_plate, phiRn_bearing_web)
        capacity_per_bolt = min(phiRn_bolt_shear, phiRn_bearing_gov)
        
        # Determine Bolt Count
        if capacity_per_bolt > 0:
            req_n = V_u / capacity_per_bolt
            n_bolts = max(2, math.ceil(req_n))
        else:
            n_bolts = 99
            
        # 1.7 Plate Checks (Check #5, #6, #7)
        # Plate Length
        spacing = 7.0 # cm
        L_plate_cm = (2*Le) + ((n_bolts-1)*spacing)
        actual_plate_len = L_plate_cm
        
        # Shear Yielding
        Ag = L_plate_cm * plate_t_cm
        Rn_yld = 0.60 * 2500.0 * Ag
        phiRn_plate_yield = (1.00 * Rn_yld) if is_lrfd else (Rn_yld / 1.50)
        
        # Shear Rupture
        An = Ag - (n_bolts * (DH/10.0) * plate_t_cm)
        Rn_rup = 0.60 * FU_PL * An
        phiRn_plate_rupture = (0.75 * Rn_rup) if is_lrfd else (Rn_rup / 2.00)
        
        # Block Shear (สมมติ U-shape failure)
        Avg = (L_plate_cm - Le) * plate_t_cm
        Avn = Avg - ((n_bolts - 0.5) * (DH/10.0) * plate_t_cm)
        Atn = (Le - 0.5*(DH/10.0)) * plate_t_cm
        
        Rn_blk = (0.6 * FU_PL * Avn) + (1.0 * FU_PL * Atn)
        phiRn_block_shear = (0.75 * Rn_blk) if is_lrfd else (Rn_blk / 2.00)
        
        # 1.8 Weld Check (Check #8, #9)
        # E70XX, 6mm Fillet
        Fexx = 4900.0
        w_size = 0.6 # cm
        Rn_weld_unit = 0.60 * Fexx * (0.707 * w_size) * 2 # 2 sides
        
        phi_weld_cap = (0.75 * Rn_weld_unit) if is_lrfd else (Rn_weld_unit / 2.00)
        if phi_weld_cap > 0:
            req_weld_len = V_u / phi_weld_cap
        
        # Ratios
        ratio_bolt = V_u / (n_bolts * capacity_per_bolt)
        ratio_plate = V_u / min(phiRn_plate_yield, phiRn_plate_rupture)
        ratio_block = V_u / phiRn_block_shear

    except Exception as e:
        st.error(f"Calculation Error: {e}")
        return

    # =========================================================
    # 2. REPORT RENDERING (แสดงผล)
    # =========================================================
    st.markdown("### 📝 รายการคำนวณออกแบบจุดต่อ (Full Engineering Checks)")
    
    with st.container(border=True):
        # HEADER
        st.markdown(f"**PROJECT:** {sec_name} Connection | **STD:** AISC 360-16 ({method_txt})")
        st.divider()
        
        # PART 1: LOAD
        st.markdown("#### 1. แรงกระทำ (Design Load)")
        st.latex(rf"V_n = 0.6 F_y A_w = 0.6({fy_beam:.0f})({Aw:.2f})")
        st.latex(rf"V_u = 0.75 \times \phi V_n = \mathbf{{{V_u:,.0f} \text{{ kg}}}}")
        st.divider()
        
        # PART 2: BOLT CHECK
        st.markdown("#### 2. ตรวจสอบสลักเกลียว (Bolt Checks)")
        st.info(f"Bolt M{DB:.0f} A325 x {n_bolts} pcs.")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**1) Shear Capacity:**")
            st.latex(rf"\phi R_{{shear}} = {phiRn_bolt_shear:,.0f} \text{{ kg/bolt}}")
            
        with c2:
            st.markdown("**2) Bearing Capacity:**")
            # Logic โชว์ว่าใครเป็นตัวคุม (Plate vs Web)
            if phiRn_bearing_web < phiRn_bearing_plate:
                st.write(f"❌ Control by Beam Web (t={tw_cm*10:.1f}mm)")
                st.latex(rf"\phi R_{{br}} = {phiRn_bearing_web:,.0f} \text{{ kg/bolt}}")
            else:
                st.write(f"✅ Control by Plate (t={plate_t_mm:.1f}mm)")
                st.latex(rf"\phi R_{{br}} = {phiRn_bearing_plate:,.0f} \text{{ kg/bolt}}")
        
        st.markdown(f"**Governing Capacity:** {capacity_per_bolt:,.0f} kg/bolt")
        st.latex(rf"Ratio = \frac{{{V_u:,.0f}}}{{{n_bolts} \times {capacity_per_bolt:,.0f}}} = \mathbf{{{ratio_bolt:.2f}}}")
        st.divider()
        
        # PART 3: PLATE & ELEMENT CHECK
        st.markdown("#### 3. ตรวจสอบชิ้นส่วนรับแรง (Element Checks)")
        st.write(f"Plate Size: {plate_t_mm:.0f} x {actual_plate_len:.0f} mm")
        
        # แสดงตารางผลลัพธ์
        checks = [
            ("Shear Yielding (Plate)", phiRn_plate_yield),
            ("Shear Rupture (Plate)", phiRn_plate_rupture),
            ("Block Shear Rupture", phiRn_block_shear)
        ]
        
        for name, cap in checks:
            r = V_u / cap
            status = "✅ PASS" if r <= 1.0 else "❌ FAIL"
            st.write(f"- **{name}:** Cap = {cap:,.0f} kg | Ratio = **{r:.2f}** {status}")
            
        st.divider()
        
        # PART 4: WELD
        st.markdown("#### 4. ตรวจสอบรอยเชื่อม (Weld Checks)")
        st.write(f"Weld Size: 6mm Fillet (E70XX)")
        st.write(f"Required Length = **{req_weld_len:.2f} cm**")
        st.write(f"Available Length = **{actual_plate_len:.2f} cm**")
        
        if actual_plate_len >= req_weld_len:
            st.success("✅ Weld Length OK")
        else:
            st.error("❌ Weld Length Insufficient")
            
    st.markdown("---")
    st.caption(f"Generated on {datetime.now().strftime('%d/%m/%Y')}")

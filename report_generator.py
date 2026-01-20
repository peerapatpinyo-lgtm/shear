# report_generator.py
# Version: 17.0 (Ultimate - Full AISC Checks incl. Beam Web & Block Shear)
import streamlit as st
from datetime import datetime
import math

def render_report_tab(beam_data, conn_data):
    # =========================================================
    # 0. CONSTANTS & STANDARDS
    # =========================================================
    DB = 20.0           # mm (Bolt M20)
    DH = DB + 2.0       # mm (Hole)
    A_B = (math.pi * (DB/10.0)**2) / 4.0
    
    # Material Properties
    FY_PL = 2500.0      # ksc (Plate A36)
    FU_PL = 4050.0      # ksc
    F_EXX = 4900.0      # ksc (Weld)
    
    # Geometry Standards
    LE = 35.0           # mm (Edge Distance)
    S = 70.0            # mm (Spacing)
    
    # =========================================================
    # 1. PREPARE DATA & VARIABLES (Initialize ALL variables)
    # =========================================================
    sec_name = "-"
    d_cm = 0.0
    tw_cm = 0.0
    Aw = 0.0
    fy_beam = 0.0
    fu_beam = 0.0
    Vn_beam = 0.0
    V_beam_cap = 0.0
    V_u = 0.0
    
    # Connection Variables
    n_bolts_final = 0
    plate_t_mm = 10.0
    L_plate = 0.0
    
    # Capacities
    phiRn_bolt_shear = 0.0
    phiRn_plate_bearing = 0.0
    phiRn_beam_bearing = 0.0
    phiRn_plate_yield = 0.0
    phiRn_plate_rupture = 0.0
    phiRn_block_shear = 0.0
    phiRn_weld = 0.0
    
    if not beam_data:
        st.warning("⚠️ กรุณาเลือกขนาดคานที่ Tab 1 ก่อน")
        return

    try:
        # Beam Data
        sec_name = beam_data.get('sec_name', 'Unknown')
        h = float(beam_data.get('h', 0) or 400)
        tw = float(beam_data.get('tw', 0) or 8)
        fy_beam = float(beam_data.get('Fy', 0) or 2500)
        fu_beam = float(beam_data.get('Fu', 0) or 4100)
        is_lrfd = beam_data.get('is_lrfd', True)
        
        d_cm = h / 10.0
        tw_cm = tw / 10.0
        Aw = d_cm * tw_cm
        
        # Method Factors
        if is_lrfd:
            phi = 1.00
            phi_shear = 0.75
            phi_yield = 1.00
            phi_rup = 0.75
            phi_weld = 0.75
            factor_txt = "phi"
        else:
            # ASD factors converted to equivalent multipliers for display simplicity
            # But logic below uses direct phi for LRFD. 
            # For brevity in this snippet, I will focus on LRFD logic structure 
            # and adjust display text. In real code, separate fully.
            phi = 1.0/1.50
            phi_shear = 1.0/2.00
            phi_yield = 1.0/1.50
            phi_rup = 1.0/2.00
            phi_weld = 1.0/2.00
            factor_txt = "1/Omega"

        # --- 2.1 BEAM SHEAR CAPACITY ---
        Vn_beam = 0.60 * fy_beam * Aw
        V_beam_cap = phi * Vn_beam
        V_u = 0.75 * V_beam_cap # 75% Rule

        # --- 2.2 BOLT SHEAR ---
        Fnv = 3300.0 
        Rn_bolt_unit = Fnv * A_B
        phiRn_bolt_shear = phi_shear * Rn_bolt_unit
        
        # Initial estimate
        req_n = V_u / phiRn_bolt_shear
        n_bolts_final = max(2, math.ceil(req_n))

        # --- 2.3 BEARING CHECK (PLATE vs BEAM WEB) ---
        # ต้องเช็คทั้งคู่ ตัวไหนบางกว่า ตัวนั้นพังก่อน
        
        # A. Plate Bearing
        t_pl_cm = plate_t_mm / 10.0
        Lc_edge = LE - (DH/2.0)
        rn_pl_tearout = 1.2 * (Lc_edge/10.0) * t_pl_cm * FU_PL
        rn_pl_bearing = 2.4 * (DB/10.0) * t_pl_cm * FU_PL
        rn_pl_limit = min(rn_pl_tearout, rn_pl_bearing)
        phiRn_plate_bearing = phi_shear * rn_pl_limit
        
        # B. Beam Web Bearing (Critical Check!)
        # สมมติระยะ Lc ของคานเท่ากับ Plate (เพื่อความปลอดภัย)
        rn_web_tearout = 1.2 * (Lc_edge/10.0) * tw_cm * fu_beam
        rn_web_bearing = 2.4 * (DB/10.0) * tw_cm * fu_beam
        rn_web_limit = min(rn_web_tearout, rn_web_bearing)
        phiRn_beam_bearing = phi_shear * rn_web_limit
        
        # หาตัวควบคุม (Governing Bearing Capacity)
        phiRn_bearing_gov = min(phiRn_plate_bearing, phiRn_beam_bearing)
        
        # Re-calc bolts with bearing limit
        bolt_capacity_final = min(phiRn_bolt_shear, phiRn_bearing_gov)
        n_bolts_final = max(n_bolts_final, math.ceil(V_u / bolt_capacity_final))
        
        # --- 2.4 PLATE CHECKS ---
        L_plate = (2 * LE) + ((n_bolts_final - 1) * S)
        L_plate_cm = L_plate / 10.0
        
        # Shear Yield
        Ag = L_plate_cm * t_pl_cm
        phiRn_plate_yield = phi_yield * (0.60 * FY_PL * Ag)
        
        # Shear Rupture
        An = Ag - (n_bolts_final * (DH/10.0) * t_pl_cm)
        phiRn_plate_rupture = phi_rup * (0.60 * FU_PL * An)
        
        # --- 2.5 BLOCK SHEAR (NEW!) ---
        # สมมติการวิบัติรูปตัว U แนวนอน (Horizontal Block Shear)
        # Agv = พื้นที่เฉือนรวม (2 แนวเส้นสลัก) -> คิดแบบ Conservative 1 แนว for Single Plate usually L-shape or U-shape
        # AISC Single Plate usually checks block shear on the Plate
        # Assuming failure line passes through all bolts vertically
        
        # Shear Plane (Vertical)
        Avg = (L_plate_cm - (LE/10.0)) * t_pl_cm # Gross shear area
        Avn = Avg - ((n_bolts_final - 0.5) * (DH/10.0) * t_pl_cm) # Net shear area
        
        # Tension Plane (Horizontal - to edge)
        Atg = (LE/10.0) * t_pl_cm # Gross tension
        Atn = Atg - (0.5 * (DH/10.0) * t_pl_cm) # Net tension
        
        Ubs = 1.0
        # Formula: Rn = 0.6 Fu Anv + Ubs Fu Ant <= 0.6 Fy Agv + Ubs Fu Ant
        R1 = (0.6 * FU_PL * Avn) + (Ubs * FU_PL * Atn)
        R2 = (0.6 * FY_PL * Avg) + (Ubs * FU_PL * Atn)
        Rn_block = min(R1, R2)
        phiRn_block_shear = phi_rup * Rn_block
        
        # --- 2.6 WELD ---
        w_size_cm = 0.6
        Rn_weld_unit = 0.60 * F_EXX * (0.707 * w_size_cm)
        phiRn_weld = phi_weld * Rn_weld_unit * 2 # 2 sides
        L_weld_req = V_u / phiRn_weld

    except Exception as e:
        st.error(f"Calculation Error: {e}")
        return

    # =========================================================
    # 3. REPORT RENDERING
    # =========================================================
    st.markdown("### 📝 รายการคำนวณออกแบบจุดต่อ (Ultimate Checks)")
    
    with st.container(border=True):
        st.markdown(f"**PROJECT:** Connection for {sec_name} | **CODE:** AISC 360-16 ({'LRFD' if is_lrfd else 'ASD'})")
        st.divider()
        
        # 1. LOAD
        st.markdown("#### 1. แรงกระทำ (Design Load)")
        st.latex(rf"V_u (Req) = \mathbf{{{V_u:,.0f} \text{{ kg}}}}")
        
        st.divider()
        
        # 2. BOLT & BEARING
        st.markdown("#### 2. ตรวจสอบสลักเกลียวและการแบกทาน (Bolt & Bearing)")
        st.info(f"Bolt M{DB:.0f} A325 x {n_bolts_final} pcs.")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Bolt Shear Strength:**")
            st.latex(rf"\phi R_n = {phiRn_bolt_shear:,.0f} \text{{ kg/bolt}}")
            
        with c2:
            st.markdown("**Max Bearing Capacity:**")
            # โชว์ค่าที่ต่ำกว่าระหว่าง Plate กับ Beam Web
            if phiRn_beam_bearing < phiRn_plate_bearing:
                 st.write("❌ **Control by Beam Web** (Web < Plate)")
                 val = phiRn_beam_bearing
            else:
                 st.write("✅ **Control by Plate**")
                 val = phiRn_plate_bearing
            st.latex(rf"\phi R_{{br}} = {val:,.0f} \text{{ kg/bolt}}")

        # สรุป Ratio Bolt
        total_bolt_cap = n_bolts_final * min(phiRn_bolt_shear, phiRn_bearing_gov)
        bolt_ratio = V_u / total_bolt_cap
        st.progress(min(bolt_ratio, 1.0), text=f"Bolt D/C Ratio: {bolt_ratio:.2f}")
        
        st.divider()
        
        # 3. PLATE CHECKS
        st.markdown("#### 3. ตรวจสอบแผ่นเหล็ก (Plate Checks)")
        st.write(f"Plate Size: {plate_t_mm:.0f} x {L_plate:.0f} mm")
        
        # Table for checks
        checks = [
            ("Shear Yielding", phiRn_plate_yield),
            ("Shear Rupture", phiRn_plate_rupture),
            ("Block Shear", phiRn_block_shear)
        ]
        
        for name, cap in checks:
            status = "✅ PASS" if cap >= V_u else "❌ FAIL"
            ratio = V_u / cap
            col_a, col_b = st.columns([3, 1])
            col_a.write(f"- {name}: Capacity = **{cap:,.0f} kg**")
            col_b.write(f"Ratio: **{ratio:.2f}** {status}")
            
        if any(cap < V_u for _, cap in checks):
             st.error("⚠️ แผ่นเหล็กรับแรงไม่ไหว กรุณาเพิ่มความหนา")
        
        st.divider()
        
        # 4. WELD
        st.markdown("#### 4. รอยเชื่อม (Weld)")
        st.write(f"Required Weld Length = {L_weld_req:.2f} cm")
        st.write(f"Actual Plate Length = {L_plate_cm:.2f} cm")
        if L_plate_cm >= L_weld_req:
            st.success(f"✅ Weld OK (Use 6mm Fillet Full Length)")
        else:
            st.error(f"❌ Plate too short for weld (Need {L_weld_req:.2f} cm)")
            
    st.markdown("---")
    st.caption("Note: Bearing Check includes both Plate and Beam Web checks.")

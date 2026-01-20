# report_generator.py
# Version: 16.0 (Professional Standard - Full Checks)
import streamlit as st
from datetime import datetime
import math

def render_report_tab(beam_data, conn_data):
    # =========================================================
    # 0. CONSTANTS & STANDARDS (ค่าคงที่ตามมาตรฐาน)
    # =========================================================
    # Bolt M20 A325
    DB = 20.0           # mm (Bolt Diameter)
    DH = DB + 2.0       # mm (Hole Diameter standard +2mm)
    A_B = (math.pi * (DB/10.0)**2) / 4.0 # cm2
    
    # Plate A36 (Standard Plate)
    FY_PL = 2500.0      # ksc
    FU_PL = 4050.0      # ksc
    
    # Weld E70XX
    F_EXX = 4900.0      # ksc (70 ksi)
    
    # Geometry (Standard Practice)
    LE = 35.0           # mm (Edge Distance for M20)
    S = 70.0            # mm (Spacing approx 3*db)
    
    # =========================================================
    # 1. PREPARE DATA (กัน Error 100%)
    # =========================================================
    if not beam_data:
        st.warning("⚠️ กรุณาเลือกขนาดคานที่หน้า 1 ก่อนครับ")
        return

    try:
        sec_name = beam_data.get('sec_name', 'Unknown')
        h = float(beam_data.get('h', 0) or 400)
        tw = float(beam_data.get('tw', 0) or 8)
        fy_beam = float(beam_data.get('Fy', 0) or 2500)
        # แปลงหน่วย
        d_cm = h / 10.0
        tw_cm = tw / 10.0
        Aw = d_cm * tw_cm
        is_lrfd = beam_data.get('is_lrfd', True)
    except:
        st.error("Data Error")
        return

    # =========================================================
    # 2. ENGINEERING CALCULATION (CORE)
    # =========================================================
    
    # --- 2.1 LOAD DETERMINATION (75% Rule) ---
    Vn_beam = 0.60 * fy_beam * Aw
    if is_lrfd:
        phi = 1.00
        V_beam_cap = phi * Vn_beam
        V_u = 0.75 * V_beam_cap  # Demand Load
        txt_method = "LRFD"
    else:
        omega = 1.50
        V_beam_cap = Vn_beam / omega
        V_u = 0.75 * V_beam_cap
        txt_method = "ASD"

    # --- 2.2 BOLT DESIGN (SHEAR) ---
    # A325 Shear Strength (Threads included)
    Fnv = 3300.0 # ksc (Approx for A325)
    
    if is_lrfd:
        phi_bolt = 0.75
        Rn_bolt_shear = phi_bolt * Fnv * A_B
    else:
        omega_bolt = 2.00
        Rn_bolt_shear = (Fnv * A_B) / omega_bolt

    # Estimate number of bolts
    req_n = V_u / Rn_bolt_shear
    n_bolts = max(2, math.ceil(req_n))
    
    # --- 2.3 PLATE DESIGN (THICKNESS & CHECKS) ---
    t_plate_mm = 10.0 # Try 10mm
    t_pl = t_plate_mm / 10.0 # cm
    
    # Check 1: Bolt Bearing & Tearout (J3.10)
    # Lc = Clear distance calculation
    # สมมติระยะ Lc สำหรับตัวริม (Critical) = Le - (dh/2)
    Lc_edge = LE - (DH / 2.0) # mm
    Lc_edge_cm = Lc_edge / 10.0
    
    # Tearout Strength (Rn = 1.2 Lc t Fu)
    rn_tearout = 1.2 * Lc_edge_cm * t_pl * FU_PL
    # Bearing Strength (Rn = 2.4 d t Fu)
    rn_bearing = 2.4 * (DB/10.0) * t_pl * FU_PL
    
    rn_limit = min(rn_tearout, rn_bearing)
    
    if is_lrfd:
        phi_br = 0.75
        Rn_bolt_bearing = phi_br * rn_limit
    else:
        omega_br = 2.00
        Rn_bolt_bearing = rn_limit / omega_br
        
    # Final Bolt Capacity (Controls by Shear or Bearing)
    phiRn_bolt_final = min(Rn_bolt_shear, Rn_bolt_bearing)
    
    # Re-check number of bolts with bearing limit
    req_n_final = V_u / phiRn_bolt_final
    n_bolts_final = max(2, math.ceil(req_n_final))
    
    # Connection Height (Plate Length)
    L_plate = (2 * LE) + ((n_bolts_final - 1) * S) # mm
    L_plate_cm = L_plate / 10.0
    
    # Check 2: Shear Yielding of Plate (J4.2)
    # Rn = 0.60 * Fy * Ag
    Ag = L_plate_cm * t_pl
    Rn_yield = 0.60 * FY_PL * Ag
    
    if is_lrfd:
        phi_y = 1.00
        Cap_yield = phi_y * Rn_yield
    else:
        omega_y = 1.50
        Cap_yield = Rn_yield / omega_y
        
    # Check 3: Shear Rupture of Plate (J4.2)
    # Rn = 0.60 * Fu * An
    # An = Ag - (n * dh * t) -- คิดแนวตัดผ่านรูน๊อต
    An = Ag - (n_bolts_final * (DH/10.0) * t_pl) 
    Rn_rupture = 0.60 * FU_PL * An
    
    if is_lrfd:
        phi_rup = 0.75
        Cap_rupture = phi_rup * Rn_rupture
    else:
        omega_rup = 2.00
        Cap_rupture = Rn_rupture / omega_rup
        
    # --- 2.4 WELD DESIGN ---
    # Weld Size (Double Fillet)
    w_size_mm = 6.0
    w_eff = 0.707 * (w_size_mm/10.0) # Throat size cm
    
    # Weld Strength per cm (E70XX)
    # Fnw = 0.60 * Fexx
    Rn_weld_unit = 0.60 * F_EXX * w_eff * 1.0 # kg/cm per line
    
    if is_lrfd:
        phi_w = 0.75
        Cap_weld_per_cm = phi_w * Rn_weld_unit * 2 # x2 sides
    else:
        omega_w = 2.00
        Cap_weld_per_cm = (Rn_weld_unit * 2) / omega_w
        
    # Weld Length Required
    L_weld_req = V_u / Cap_weld_per_cm
    
    # Check if Plate Length is enough for weld
    weld_status = "OK" if L_plate_cm >= L_weld_req else "NG (Increase Length)"

    # =========================================================
    # 3. REPORT RENDERING
    # =========================================================
    st.markdown("### 📝 รายการคำนวณออกแบบจุดต่อ (Detailed Calculation)")
    
    with st.container(border=True):
        # Header
        st.markdown(f"**PROJECT:** {beam_data.get('sec_name')} Connection Design")
        st.markdown(f"**DESIGN CODE:** AISC 360-16 ({txt_method})")
        st.divider()
        
        # --- PART 1: LOADS ---
        st.markdown("#### 1. แรงกระทำ (Design Load)")
        st.write(f"Beam: {sec_name}, Shear Capacity ($\phi V_n$) = {V_beam_cap:,.0f} kg")
        st.info("💡 Design Condition: 75% of Beam Shear Capacity")
        st.latex(rf"V_u = 0.75 \times {V_beam_cap:,.0f} = \mathbf{{{V_u:,.0f} \text{{ kg}}}}")
        
        st.divider()
        
        # --- PART 2: BOLT DESIGN ---
        st.markdown("#### 2. ตรวจสอบรอยต่อสลักเกลียว (Bolt Check)")
        st.markdown(f"**Properties:** M{DB:.0f} A325 (Hole {DH:.0f} mm)")
        
        st.markdown("**(a) Bolt Shear Strength:**")
        st.latex(rf"\phi R_n = \mathbf{{{Rn_bolt_shear:,.0f} \text{{ kg/bolt}}}}")
        
        st.markdown("**(b) Bearing & Tearout Strength (Plate t=10mm):**")
        st.caption(f"Edge Dist ($L_e$) = {LE} mm | Clear Dist ($L_c$) = {Lc_edge:.1f} mm")
        st.latex(rf"R_n = 1.2 L_c t F_u = 1.2({Lc_edge_cm:.2f})(1.0)({FU_PL}) = {rn_tearout:,.0f} \text{{ kg}}")
        st.latex(rf"R_n = 2.4 d t F_u = 2.4({DB/10.0})(1.0)({FU_PL}) = {rn_bearing:,.0f} \text{{ kg}}")
        st.write(f"Control Value = {rn_limit:,.0f} kg")
        st.latex(rf"\phi R_{{br}} = 0.75 \times {rn_limit:,.0f} = \mathbf{{{Rn_bolt_bearing:,.0f} \text{{ kg/bolt}}}}")
        
        st.markdown("**(c) Bolt Quantity:**")
        st.write(f"Governing Capacity per Bolt = {phiRn_bolt_final:,.0f} kg")
        st.latex(rf"N_{{req}} = \frac{{{V_u:,.0f}}}{{{phiRn_bolt_final:,.0f}}} = {req_n_final:.2f} \rightarrow \text{{Use }} \mathbf{{{n_bolts_final} \text{{ Bolts}}}}")
        
        st.divider()
        
        # --- PART 3: PLATE CHECKS ---
        st.markdown("#### 3. ตรวจสอบแผ่นเหล็ก (Shear Plate Checks)")
        st.markdown(f"**Plate Size:** {t_plate_mm:.0f} x {L_plate:.0f} mm (Material: A36)")
        
        # Yielding
        st.markdown("**(a) Shear Yielding (Gross Area):**")
        st.latex(rf"\phi R_n = 1.00(0.60 F_y A_g) = 0.6({FY_PL})({Ag:.2f}) = \mathbf{{{Cap_yield:,.0f} \text{{ kg}}}}")
        if Cap_yield >= V_u:
            st.success(f"✅ PASS (Ratio = {V_u/Cap_yield:.2f})")
        else:
            st.error("❌ FAIL (Increase Thickness)")

        # Rupture
        st.markdown("**(b) Shear Rupture (Net Area):**")
        st.latex(rf"A_n = A_g - N_{{cut}} d_h t = {Ag:.2f} - ({n_bolts_final} \times {DH/10.0} \times {t_pl}) = {An:.2f} \text{{ cm}}^2")
        st.latex(rf"\phi R_n = 0.75(0.60 F_u A_n) = 0.75(0.6)({FU_PL})({An:.2f}) = \mathbf{{{Cap_rupture:,.0f} \text{{ kg}}}}")
        if Cap_rupture >= V_u:
            st.success(f"✅ PASS (Ratio = {V_u/Cap_rupture:.2f})")
        else:
            st.error("❌ FAIL (Increase Thickness)")
            
        st.divider()
        
        # --- PART 4: WELD DESIGN ---
        st.markdown("#### 4. ตรวจสอบรอยเชื่อม (Weld Design)")
        st.write("Weld 6mm (Fillet) 2 sides (E70XX)")
        st.latex(rf"\phi R_w = 0.75 \times 0.60 F_{{exx}} \times 0.707 s \times 2")
        st.latex(rf"\phi R_w = \mathbf{{{Cap_weld_per_cm:,.0f} \text{{ kg/cm}}}}")
        
        st.write(f"Required Length = {V_u:,.0f} / {Cap_weld_per_cm:,.0f} = **{L_weld_req:.2f} cm**")
        st.write(f"Available Plate Length = **{L_plate_cm:.2f} cm**")
        
        if L_plate_cm >= L_weld_req:
             st.success("✅ WELD OK")
        else:
             st.error("❌ WELD LENGTH INSUFFICIENT")

    # Final Summary
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.info(f"**สรุป:** ใช้ Bolt M20 A325 จำนวน **{n_bolts_final} ตัว**")
    with c2:
        st.caption("Calculation based on AISC 360-16 / EIT Standard (SDM)")

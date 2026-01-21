import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

# --- Module Integrity Check ---
try:
    from report_generator import get_standard_sections, calculate_full_properties
except ImportError:
    st.error("🚨 Critical Error: Core module 'report_generator.py' is missing.")
    st.stop()

# --- Engineering Constants ---
E_STEEL_KSC = 2040000  
FY_PLATE = 2400 
FU_PLATE = 4000 
FV_BOLT = 2100  
FV_WELD = 1470  

def render_analytics_section(load_pct, bolt_dia, load_case, factor):
    """
    Renders the Structural Analytics Dashboard.
    - Version 31.0: REMOVED FS=4 from display. 
      Table now shows raw Nominal Shear Capacity (Vn = 0.6*Fy*Aw).
      Example: H-400x200 -> 47,040 kg.
    """
    
    st.markdown("## 🏗️ Structural Optimization Dashboard")
    st.divider()

    all_sections = get_standard_sections()
    if not all_sections:
        st.warning("⚠️ No sections found.")
        return

    data_list = []
    
    # --- CALCULATION LOOP ---
    for sec in all_sections:
        full_props = calculate_full_properties(sec) 
        
        # --- 1. BEAM SHEAR CAPACITY (Raw / Nominal) ---
        h_cm = sec['h'] / 10
        tw_cm = sec['tw'] / 10
        Aw = h_cm * tw_cm
        
        # Vn = 0.6 * Fy * Aw (ไม่หาร Safety Factor)
        # ตัวอย่าง: 0.6 * 2450 * 32 = 47,040 kg
        V_beam_nominal = 0.60 * sec['Fy'] * Aw 
        
        # --- 2. TARGET LOAD ---
        # คิด Load จาก % ของความสามารถสูงสุด (Vn) โดยตรง 
        # เพื่อให้เห็นภาพว่ารับแรงกี่ % ของขีดจำกัด
        V_target = V_beam_nominal * (load_pct / 100.0)

        # --- 3. ZONES (Moment / Deflection) ---
        # ใช้ Factor เฉพาะตอนคำนวณระยะ Span เพื่อความปลอดภัย แต่ค่า Shear โชว์เต็ม
        safe_factor_span = 1.67 # Standard ASD Factor for Spans
        
        try:
            M_n_kgcm = sec['Fy'] * full_props['Zx (cm3)']
            M_safe = (M_n_kgcm / safe_factor_span) / 100 
            V_safe = V_beam_nominal / safe_factor_span
        except: M_safe = 0; V_safe = 1
        
        Ix = full_props['Ix (cm4)']
        K_defl = (384 * E_STEEL_KSC * Ix) / 18000000 
        
        L_sm = (4 * M_safe) / V_safe if V_safe > 0 else 0
        L_md = K_defl / (8 * M_safe) if M_safe > 0 else 0
        
        # --- 4. AUTO-DESIGN CONNECTIONS ---
        bolt_d_cm = bolt_dia / 10
        hole_d_cm = bolt_d_cm + 0.2
        pitch_cm = 3 * bolt_d_cm
        edge_cm = 4.0 
        req_bolts = 2; t_plate_cm = 0.9
        if V_target > 30000: t_plate_cm = 1.2
        
        is_safe = False; final_info = {}
        
        while not is_safe and req_bolts <= 24:
            plate_h_cm = math.ceil(((req_bolts - 1) * pitch_cm) + (2 * edge_cm))
            
            # Capacities
            Rn_bolt = req_bolts * FV_BOLT * (3.14159 * bolt_d_cm**2 / 4)
            
            Lc_edge = edge_cm - hole_d_cm/2; Lc_inner = pitch_cm - hole_d_cm
            Rn_bear = (min(1.2*Lc_edge*t_plate_cm*FU_PLATE, 2.4*bolt_d_cm*t_plate_cm*FU_PLATE) + 
                       (req_bolts-1)*min(1.2*Lc_inner*t_plate_cm*FU_PLATE, 2.4*bolt_d_cm*t_plate_cm*FU_PLATE))
            
            Rn_yield = 0.60 * FY_PLATE * plate_h_cm * t_plate_cm
            Rn_rup = 0.50 * FU_PLATE * (plate_h_cm*t_plate_cm - req_bolts*hole_d_cm*t_plate_cm)
            
            Anv = (plate_h_cm-edge_cm)*t_plate_cm - (req_bolts-0.5)*hole_d_cm*t_plate_cm
            Ant = (4.0-0.5*hole_d_cm)*t_plate_cm
            Rn_block = (0.6 * FU_PLATE * Anv) + (1.0 * FU_PLATE * Ant)
            
            weld_sz = max(0.6, (t_plate_cm*10 - 2)/10)
            Rn_weld = 2 * 0.707 * weld_sz * plate_h_cm * FV_WELD
            
            limit_states = {"Bolt Shear": Rn_bolt, "Bearing": Rn_bear, "Yield": Rn_yield, 
                            "Rupture": Rn_rup, "Block Shear": Rn_block, "Weld": Rn_weld}
            
            min_cap = min(limit_states.values())
            ratio = V_target / min_cap
            
            if ratio <= 1.00:
                is_safe = True
                governing = min(limit_states, key=limit_states.get)
                final_info = {"Bolts": req_bolts, "Plate": f"PL-{t_plate_cm*10:.0f}x100x{plate_h_cm*10:.0f}", 
                              "Weld": f"{weld_sz*10:.0f}mm", "Ratio": ratio, "Mode": governing}
            else:
                req_bolts += 1
                if req_bolts > 12 and t_plate_cm < 1.6: t_plate_cm += 0.3; req_bolts = max(2, req_bolts - 3)

        data_list.append({
            "Section": sec['name'],
            "Moment Zone": f"{L_sm:.2f} - {L_md:.2f} m",
            "L_Start": L_sm, "L_End": L_md,
            "V_Nominal": V_beam_nominal,   # <-- ค่านี้คือ 47,040 (Pure Capacity)
            "V_Target": V_target,
            "Bolt Spec": f"{final_info.get('Bolts')} - M{int(bolt_dia)}",
            "Plate Size": final_info.get('Plate'),
            "Weld Spec": final_info.get('Weld'),
            "D/C Ratio": final_info.get('Ratio'),
            "Governing": final_info.get('Mode')
        })

    if not data_list: return
    df = pd.DataFrame(data_list)

    # --- DISPLAY TABLE ---
    st.subheader("📋 Specification Table (Nominal Capacity)")
    st.dataframe(
        df[[
            "Section", "V_Nominal", "V_Target", 
            "Bolt Spec", "Plate Size", "Weld Spec", 
            "Governing", "D/C Ratio"
        ]],
        use_container_width=True,
        column_config={
            "Section": st.column_config.TextColumn("Section", width="small"),
            
            # --- ตรงนี้คือหัวใจสำคัญ: แสดงค่าเต็ม ไม่หาร ---
            "V_Nominal": st.column_config.NumberColumn(
                "Shear Capacity (Max)", 
                format="%.0f kg", 
                help="Nominal Capacity (Vn) = 0.6*Fy*Aw (No Safety Factor)"
            ),
            # ----------------------------------------
            
            "V_Target": st.column_config.NumberColumn(f"Load ({load_pct}%)", format="%.0f kg"),
            "Bolt Spec": st.column_config.TextColumn("Bolts", width="small"),
            "Plate Size": st.column_config.TextColumn("Plate (mm)", width="medium"),
            "Weld Spec": st.column_config.TextColumn("Weld", width="small"),
            "Governing": st.column_config.TextColumn("Crit. Mode", width="medium"),
            "D/C Ratio": st.column_config.ProgressColumn("Ratio", format="%.2f", min_value=0, max_value=1.5),
        },
        height=600,
        hide_index=True
    )
    
    # Validation Box
    st.info("ℹ️ **Note:** Values shown are **Nominal Capacities (Vn)** without Safety Factor reduction. (Designed for Limit State Analysis)")

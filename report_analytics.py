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
FY_PLATE = 2400 # ksc (For connection plate)
FU_PLATE = 4000 # ksc
FV_BOLT = 2100  # ksc
FV_WELD = 1470  # ksc

def render_analytics_section(load_pct, bolt_dia, load_case, factor):
    """
    Renders the Structural Analytics Dashboard.
    - Version 23.2: Shear Capacity explicitly calculated from Beam Section (d * tw).
    """
    st.markdown("## 📊 Structural Integrity & Optimization Dashboard")
    st.markdown("Comprehensive connection design with **verified zone analysis**.")
    st.divider()
    
    all_sections = get_standard_sections()
    if not all_sections:
        st.warning("⚠️ No sections found.")
        return

    data_list = []
    
    # --- 1. CALCULATION LOOP ---
    for sec in all_sections:
        full_props = calculate_full_properties(sec) 
        
        # --- 1.1 BEAM SHEAR CAPACITY (Calculated from Section) ---
        # ดึงค่าจาก Database หน้าตัดโดยตรง
        beam_depth_cm = sec['h'] / 10      # d (Total Depth)
        beam_tw_cm = sec['tw'] / 10        # tw (Web Thickness)
        beam_fy = sec['Fy']                # Fy of Beam
        
        # คำนวณพื้นที่รับแรงเฉือน (Shear Area = d * tw)
        Aw = beam_depth_cm * beam_tw_cm 
        
        # คำนวณ Shear Capacity (Vn = 0.6 * Fy * Aw)
        V_beam_nominal = 0.60 * beam_fy * Aw
        
        # Apply Safety Factor
        safe_factor = factor if (factor and factor > 0) else 1.0
        V_beam_allow = V_beam_nominal / safe_factor

        # --- 1.2 TARGET LOAD ---
        # แรงเฉือนที่ต้องการออกแบบ (V_Target) = % Load * V_Allowable
        V_target = V_beam_allow * (load_pct / 100.0)

        # --- 1.3 MOMENT & DEFLECTION ---
        try:
            M_n_kgcm = beam_fy * full_props['Zx (cm3)']
            M_allow_kgm = (M_n_kgcm / safe_factor) / 100 
        except: M_allow_kgm = 0
        
        Ix = full_props['Ix (cm4)']
        K_defl = (384 * E_STEEL_KSC * Ix) / 18000000 
        
        # Limit Zones
        L_sm = (4 * M_allow_kgm) / V_beam_allow if V_beam_allow > 0 else 0
        L_md = K_defl / (8 * M_allow_kgm) if M_allow_kgm > 0 else 0
        
        if L_md > L_sm:
            zone_text = f"{L_sm:.2f} - {L_md:.2f}"
        else: zone_text = "Check Design"

        # --- 1.4 CONNECTION AUTO-DESIGN ---
        bolt_d_cm = bolt_dia / 10
        hole_d_cm = bolt_d_cm + 0.2
        pitch_cm = 3 * bolt_d_cm
        edge_cm = 4.0 
        
        req_bolts = 2
        t_plate_cm = 0.9
        if V_target > 30000: t_plate_cm = 1.2
        
        is_safe = False
        final_info = {}
        
        while not is_safe and req_bolts <= 24:
            plate_h_cm = math.ceil(((req_bolts - 1) * pitch_cm) + (2 * edge_cm))
            
            # Connection Capacities
            Rn_bolt_shear = req_bolts * FV_BOLT * (3.14159 * bolt_d_cm**2 / 4)
            
            Lc_edge = edge_cm - hole_d_cm/2
            Lc_inner = pitch_cm - hole_d_cm
            Rn_bear_total = (min(1.2*Lc_edge*t_plate_cm*FU_PLATE, 2.4*bolt_d_cm*t_plate_cm*FU_PLATE) + 
                             (req_bolts-1)*min(1.2*Lc_inner*t_plate_cm*FU_PLATE, 2.4*bolt_d_cm*t_plate_cm*FU_PLATE))
            
            Ag = plate_h_cm * t_plate_cm
            Rn_yield = 0.60 * FY_PLATE * Ag
            
            An = Ag - (req_bolts * hole_d_cm * t_plate_cm)
            Rn_rupture = 0.50 * FU_PLATE * An
            
            Anv = (plate_h_cm - edge_cm) * t_plate_cm - ((req_bolts - 0.5) * hole_d_cm * t_plate_cm)
            Ant = (4.0 - 0.5*hole_d_cm) * t_plate_cm
            Rn_block = (0.6 * FU_PLATE * Anv) + (1.0 * FU_PLATE * Ant)
            
            weld_sz = max(0.6, (t_plate_cm*10 - 2)/10)
            Rn_weld = 2 * 0.707 * weld_sz * plate_h_cm * FV_WELD
            
            min_cap = min(Rn_bolt_shear, Rn_bear_total, Rn_yield, Rn_rupture, Rn_block, Rn_weld)
            ratio = V_target / min_cap
            
            if ratio <= 1.00:
                is_safe = True
                final_info = {
                    "Bolts": req_bolts, 
                    "Plate": f"PL-{t_plate_cm*10:.0f}x100x{plate_h_cm*10:.0f}", 
                    "Weld": f"{weld_sz*10:.0f}mm", 
                    "Ratio": ratio, 
                    "Mode": min({k:v for k,v in locals().items() if k.startswith('Rn_')}, key={k:v for k,v in locals().items() if k.startswith('Rn_')}.get).replace('Rn_','')
                }
            else:
                req_bolts += 1
                if req_bolts > 12 and t_plate_cm < 1.6:
                    t_plate_cm += 0.3
                    req_bolts = max(2, req_bolts - 3)

        data_list.append({
            "Section": sec['name'],
            "Moment Zone": zone_text,
            "L_Start": L_sm, 
            "L_End": L_md,   
            "V_Beam_Allow": V_beam_allow, 
            "V_Target": V_target,
            "Bolt Spec": f"{final_info.get('Bolts')} - M{int(bolt_dia)}",
            "Plate Size": final_info.get('Plate'),
            "Weld Spec": final_info.get('Weld'),
            "D/C Ratio": final_info.get('Ratio'),
            "Governing": final_info.get('Mode')
        })

    if not data_list: return
    df = pd.DataFrame(data_list)

    # --- 2. GRAPH RENDERING ---
    st.subheader("🔬 Deep Dive: Critical Limit Analysis")
    
    col_sel, _ = st.columns([1, 2])
    with col_sel:
        selected_name = st.selectbox("Select Section:", df['Section'].unique())

    row = df[df['Section'] == selected_name].iloc[0]
    
    # Graph Setup
    V_allow_graph = row['V_Beam_Allow']
    L_start = row['L_Start']
    L_end = row['L_End']
    
    M_derived = (L_start * V_allow_graph) / 4 if L_start > 0 else 0
    K_derived = L_end * 8 * M_derived if M_derived > 0 else 0

    max_span = max(10, L_end * 1.5)
    spans = np.linspace(0.1, max_span, 400)
    
    ws = (2 * V_allow_graph) / spans 
    wm = (8 * M_derived) / (spans**2) 
    wd = K_derived / (spans**3) 
    w_safe = np.minimum(np.minimum(ws, wm), wd)

    # Plot
    plt.style.use('bmh')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(spans, ws, color='#9B59B6', linestyle=':', linewidth=1.5, label='Shear Limit (Web)')
    ax.plot(spans, wm, color='#E74C3C', linestyle='--', linewidth=1.5, label='Moment Limit')
    ax.plot(spans, wd, color='#2ECC71', linestyle='-.', linewidth=1.5, label='Deflection Limit')
    ax.plot(spans, w_safe, color='#2C3E50', linewidth=3, label='Safe Load Envelope')
    
    if L_start > 0.1:
        ax.axvline(x=L_start, color='#D35400', linestyle='-', linewidth=1.5)
        ax.text(L_start, max(w_safe)*0.5, f" Start: {L_start:.2f}m", 
                rotation=90, va='bottom', ha='right', color='white', fontweight='bold',
                bbox=dict(facecolor='#D35400', alpha=0.7, edgecolor='none'))

    if L_end > L_start:
        ax.axvline(x=L_end, color='#27AE60', linestyle='-', linewidth=1.5)
        ax.text(L_end, max(w_safe)*0.3, f" End: {L_end:.2f}m", 
                rotation=90, va='bottom', ha='left', color='white', fontweight='bold',
                bbox=dict(facecolor='#27AE60', alpha=0.7, edgecolor='none'))

    if L_end > L_start:
        mask = (spans >= L_start) & (spans <= L_end)
        ax.fill_between(spans, 0, w_safe, where=mask, color='#E74C3C', alpha=0.15)
        mid_point = (L_start + L_end) / 2
        safe_load_at_mid = np.interp(mid_point, spans, w_safe)
        ax.text(mid_point, safe_load_at_mid*0.5, "MOMENT\nZONE", 
                ha='center', va='center', color='#C0392B', fontweight='bold', fontsize=10)

    ax.set_ylim(0, max(w_safe)*1.2 if max(w_safe)>0 else 1000)
    ax.set_xlim(0, max_span)
    ax.set_xlabel("Span Length (m)", fontweight='bold')
    ax.set_ylabel("Safe Uniform Load (kg/m)", fontweight='bold')
    ax.legend(loc='upper right')
    st.pyplot(fig)
    
    # Verification Context
    st.info(f"""
    **Beam Capacity Check for {selected_name}:**
    * **Max Shear Capacity (V_allow):** {row['V_Beam_Allow']:,.0f} kg (Calculated from 0.6*Fy*Aw)
    * **Design Load (V_target):** {row['V_Target']:,.0f} kg (at {load_pct}%)
    """)

    st.divider()

    # --- 3. MASTER TABLE ---
    st.subheader("📋 Specification Table")
    st.dataframe(
        df[[
            "Section", "Moment Zone", "V_Beam_Allow", "V_Target", 
            "Bolt Spec", "Plate Size", 
            "D/C Ratio", "Governing"
        ]],
        use_container_width=True,
        column_config={
            "Section": st.column_config.TextColumn("Section", width="small"),
            "Moment Zone": st.column_config.TextColumn("Zone (m)", width="small"),
            "V_Beam_Allow": st.column_config.NumberColumn("Beam Shear Cap.", format="%.0f kg", help="0.6 * Fy * d * tw"),
            "V_Target": st.column_config.NumberColumn(f"Shear Demand ({load_pct}%)", format="%.0f kg"),
            "Bolt Spec": st.column_config.TextColumn("Bolts", width="small"),
            "Plate Size": st.column_config.TextColumn("Plate (mm)", width="medium"),
            "D/C Ratio": st.column_config.NumberColumn("Ratio", format="%.2f"),
            "Governing": st.column_config.TextColumn("Critical Mode", width="medium"),
        },
        height=500,
        hide_index=True
    )

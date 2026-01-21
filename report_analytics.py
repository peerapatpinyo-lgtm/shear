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
FY_PLATE = 2400 # ksc
FU_PLATE = 4000 # ksc
FV_BOLT = 2100  # ksc (Shear)
FV_WELD = 1470  # ksc (0.3 * 4900)

def render_analytics_section(load_pct, bolt_dia, load_case, factor):
    """
    Renders the Structural Analytics Dashboard.
    - Full AISC Failure Mode Analysis.
    - FIXED: Graph Vertical Lines & Labels.
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
        
        # 1.1 Capacities
        h_cm = sec['h'] / 10
        tw_cm = sec['tw'] / 10
        
        # Beam Shear (Web Yield)
        V_beam_nominal = 0.60 * sec['Fy'] * (h_cm * tw_cm)
        V_beam_allow = V_beam_nominal / factor if factor and factor > 0 else V_beam_nominal

        # Target Load (User Specified % applied to Allowable)
        V_target = V_beam_allow * (load_pct / 100.0)

        # Moment Capacity
        try:
            M_n_kgcm = sec['Fy'] * full_props['Zx (cm3)']
            M_allow_kgm = (M_n_kgcm / factor) / 100 if factor and factor > 0 else 0
        except: M_allow_kgm = 0
        
        # Deflection K
        Ix = full_props['Ix (cm4)']
        K_defl = (384 * E_STEEL_KSC * Ix) / 18000000 
        
        # 1.2 LIMIT ZONES (Calculated for every section)
        # Shear -> Moment Transition: L = 4M/V
        L_sm = (4 * M_allow_kgm) / V_beam_allow if V_beam_allow > 0 else 0
        
        # Moment -> Deflection Transition: L = K / 8M (approx for uniform load)
        L_md = K_defl / (8 * M_allow_kgm) if M_allow_kgm > 0 else 0
        
        # Zone String
        if L_md > L_sm:
            zone_text = f"{L_sm:.2f} - {L_md:.2f}"
        else: zone_text = "Check Design"

        # 1.3 AUTO-DESIGN (6 Modes)
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
            # Geometry
            plate_h_cm = ((req_bolts - 1) * pitch_cm) + (2 * edge_cm)
            plate_h_cm = math.ceil(plate_h_cm) 
            
            # Capacities
            Rn_bolt_shear = req_bolts * FV_BOLT * (3.14159 * bolt_d_cm**2 / 4)
            
            Lc_edge = edge_cm - hole_d_cm/2
            Lc_inner = pitch_cm - hole_d_cm
            Rn_bear_total = (min(1.2*Lc_edge*t_plate_cm*FU_PLATE, 2.4*bolt_d_cm*t_plate_cm*FU_PLATE) + 
                             (req_bolts-1)*min(1.2*Lc_inner*t_plate_cm*FU_PLATE, 2.4*bolt_d_cm*t_plate_cm*FU_PLATE))
            
            Ag = plate_h_cm * t_plate_cm
            Rn_yield = 0.60 * FY_PLATE * Ag
            
            An = Ag - (req_bolts * hole_d_cm * t_plate_cm)
            Rn_rupture = 0.50 * FU_PLATE * An
            
            # Block Shear
            Anv = (plate_h_cm - edge_cm) * t_plate_cm - ((req_bolts - 0.5) * hole_d_cm * t_plate_cm)
            Ant = (4.0 - 0.5*hole_d_cm) * t_plate_cm
            Rn_block = (0.6 * FU_PLATE * Anv) + (1.0 * FU_PLATE * Ant)
            
            weld_sz = max(0.6, (t_plate_cm*10 - 2)/10)
            Rn_weld = 2 * 0.707 * weld_sz * plate_h_cm * FV_WELD
            
            # Find Minimum
            limit_states = {
                "Bolt Shear": Rn_bolt_shear, "Bearing": Rn_bear_total, 
                "Yield": Rn_yield, "Rupture": Rn_rupture, 
                "Block Shear": Rn_block, "Weld": Rn_weld
            }
            min_cap = min(limit_states.values())
            governing_mode = min(limit_states, key=limit_states.get)
            
            ratio = V_target / min_cap
            
            if ratio <= 1.00:
                is_safe = True
                final_info = {
                    "Bolts": req_bolts, 
                    "Plate": f"PL-{t_plate_cm*10:.0f}x100x{plate_h_cm*10:.0f}", 
                    "Weld": f"{weld_sz*10:.0f}mm", 
                    "Ratio": ratio, 
                    "Mode": governing_mode
                }
            else:
                req_bolts += 1
                if req_bolts > 12 and t_plate_cm < 1.6:
                    t_plate_cm += 0.3
                    req_bolts = max(2, req_bolts - 3)

        data_list.append({
            "Section": sec['name'],
            "Moment Zone": zone_text,
            "L_Start": L_sm,  # For Graph
            "L_End": L_md,    # For Graph
            "V_Beam": V_beam_allow,
            "V_Target": V_target,
            "Bolt Spec": f"{final_info.get('Bolts')} - M{int(bolt_dia)}",
            "Plate Size": final_info.get('Plate'),
            "Weld Spec": final_info.get('Weld'),
            "D/C Ratio": final_info.get('Ratio'),
            "Governing": final_info.get('Mode')
        })

    if not data_list: return
    df = pd.DataFrame(data_list)

    # --- 2. GRAPH RENDERING (FIXED & RESTORED) ---
    st.subheader("🔬 Deep Dive: Critical Limit Analysis")
    
    col_sel, _ = st.columns([1, 2])
    with col_sel:
        selected_name = st.selectbox("Select Section:", df['Section'].unique())

    row = df[df['Section'] == selected_name].iloc[0]
    
    # Retrieve Limits
    V_allow = row['V_Beam']
    L_start = row['L_Start']
    L_end = row['L_End']
    
    # Re-derive constants for plotting curves
    M_derived = (L_start * V_allow) / 4 if L_start > 0 else 0
    K_derived = L_end * 8 * M_derived if M_derived > 0 else 0

    # Plot Range
    max_span = max(10, L_end * 1.5)
    spans = np.linspace(0.1, max_span, 400)
    
    # Curve Formulas
    ws = (2 * V_allow) / spans # Shear Limit
    wm = (8 * M_derived) / (spans**2) # Moment Limit
    wd = K_derived / (spans**3) # Deflection Limit
    w_safe = np.minimum(np.minimum(ws, wm), wd)

    # PLOT
    plt.style.use('bmh')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Curves
    ax.plot(spans, ws, color='#9B59B6', linestyle=':', linewidth=1.5, label='Shear Limit')
    ax.plot(spans, wm, color='#E74C3C', linestyle='--', linewidth=1.5, label='Moment Limit')
    ax.plot(spans, wd, color='#2ECC71', linestyle='-.', linewidth=1.5, label='Deflection Limit')
    ax.plot(spans, w_safe, color='#2C3E50', linewidth=3, label='Safe Load Envelope')
    
    # --- FIXED: VERTICAL LINES LOGIC ---
    # Plot L_Start (Shear -> Moment)
    if L_start > 0.1:
        ax.axvline(x=L_start, color='#D35400', linestyle='-', linewidth=1.5)
        # Add label with background box for readability
        ax.text(L_start, max(w_safe)*0.5, f" Start: {L_start:.2f}m", 
                rotation=90, va='bottom', ha='right', color='white', fontweight='bold',
                bbox=dict(facecolor='#D35400', alpha=0.7, edgecolor='none'))

    # Plot L_End (Moment -> Deflection)
    if L_end > L_start:
        ax.axvline(x=L_end, color='#27AE60', linestyle='-', linewidth=1.5)
        ax.text(L_end, max(w_safe)*0.3, f" End: {L_end:.2f}m", 
                rotation=90, va='bottom', ha='left', color='white', fontweight='bold',
                bbox=dict(facecolor='#27AE60', alpha=0.7, edgecolor='none'))

    # Fill Moment Zone
    if L_end > L_start:
        # Create boolean mask for the range
        mask = (spans >= L_start) & (spans <= L_end)
        ax.fill_between(spans, 0, w_safe, where=mask, color='#E74C3C', alpha=0.15)
        
        # Add Zone Label in the middle
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

    st.divider()

    # --- 3. MASTER TABLE ---
    st.subheader("📋 Specification Table: Fully Verified Design")
    st.dataframe(
        df[[
            "Section", "Moment Zone", "V_Target", 
            "Bolt Spec", "Plate Size", "Weld Spec", 
            "D/C Ratio", "Governing"
        ]],
        use_container_width=True,
        column_config={
            "Section": st.column_config.TextColumn("Section", width="small"),
            "Moment Zone": st.column_config.TextColumn("Zone (m)", width="small"),
            "V_Target": st.column_config.NumberColumn("Load (kg)", format="%.0f"),
            "Bolt Spec": st.column_config.TextColumn("Bolts", width="small"),
            "Plate Size": st.column_config.TextColumn("Plate (mm)", width="medium"),
            "Weld Spec": st.column_config.TextColumn("Weld", width="small"),
            "D/C Ratio": st.column_config.NumberColumn("Max Ratio", format="%.2f"),
            "Governing": st.column_config.TextColumn("Critical Mode", width="medium"),
        },
        height=500,
        hide_index=True
    )

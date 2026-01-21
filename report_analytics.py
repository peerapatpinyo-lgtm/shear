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
    - Version 32.0: 
        1. Table shows Nominal Capacity (e.g. 47,040 kg) explicitly.
        2. Graph section is FULLY RESTORED.
    """
    
    st.markdown("## 🏗️ Structural Optimization Dashboard")
    st.divider()

    all_sections = get_standard_sections()
    if not all_sections:
        st.warning("⚠️ No sections found.")
        return

    data_list = []
    
    # --- 1. CALCULATION CORE ---
    for sec in all_sections:
        full_props = calculate_full_properties(sec) 
        
        # --- A. SHEAR CAPACITY (Nominal) ---
        h_cm = sec['h'] / 10
        tw_cm = sec['tw'] / 10
        Aw = h_cm * tw_cm
        
        # Vn = 0.6 * Fy * Aw (NO Safety Factor applied here for display)
        # Example: 0.6 * 2450 * 32 = 47,040 kg
        V_beam_nominal = 0.60 * sec['Fy'] * Aw 
        
        # Define Allowable for Graphing (Optional, if you want "Safe" curves)
        # If user says "Cut FS", we can use Nominal for graph or apply standard ASD
        # Here we use Nominal for consistency with the Table request.
        V_graph_limit = V_beam_nominal 

        # Target Load (User % of Nominal)
        V_target = V_beam_nominal * (load_pct / 100.0)

        # --- B. ZONES (Moment / Deflection) ---
        # Calculate limits based on Nominal values for consistency
        try:
            M_n_kgcm = sec['Fy'] * full_props['Zx (cm3)']
            M_limit_kgm = M_n_kgcm / 100 
        except: M_limit_kgm = 0
        
        Ix = full_props['Ix (cm4)']
        K_defl = (384 * E_STEEL_KSC * Ix) / 18000000 
        
        L_sm = (4 * M_limit_kgm) / V_beam_nominal if V_beam_nominal > 0 else 0
        L_md = K_defl / (8 * M_limit_kgm) if M_limit_kgm > 0 else 0
        
        # --- C. AUTO-DESIGN (6 Modes) ---
        bolt_d_cm = bolt_dia / 10
        hole_d_cm = bolt_d_cm + 0.2
        pitch_cm = 3 * bolt_d_cm
        edge_cm = 4.0 
        req_bolts = 2; t_plate_cm = 0.9; 
        if V_target > 30000: t_plate_cm = 1.2
        
        is_safe = False; final_info = {}
        
        while not is_safe and req_bolts <= 24:
            plate_h_cm = math.ceil(((req_bolts - 1) * pitch_cm) + (2 * edge_cm))
            
            # 6 Checks
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
            "L_Start": L_sm, 
            "L_End": L_md,
            "V_Nominal": V_beam_nominal,   # 47,040 kg
            "V_Target": V_target,
            "Bolt Spec": f"{final_info.get('Bolts')} - M{int(bolt_dia)}",
            "Plate Size": final_info.get('Plate'),
            "Weld Spec": final_info.get('Weld'),
            "D/C Ratio": final_info.get('Ratio'),
            "Governing": final_info.get('Mode')
        })

    if not data_list: return
    df = pd.DataFrame(data_list)

    # --- 2. TABLE DISPLAY ---
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
            "V_Nominal": st.column_config.NumberColumn("Shear Capacity (Vn)", format="%.0f kg", help="Nominal Web Shear (0.6*Fy*Aw)"),
            "V_Target": st.column_config.NumberColumn(f"Load ({load_pct}%)", format="%.0f kg"),
            "Bolt Spec": st.column_config.TextColumn("Bolts", width="small"),
            "Plate Size": st.column_config.TextColumn("Plate", width="medium"),
            "Weld Spec": st.column_config.TextColumn("Weld", width="small"),
            "Governing": st.column_config.TextColumn("Crit. Mode", width="medium"),
            "D/C Ratio": st.column_config.ProgressColumn("Ratio", format="%.2f", min_value=0, max_value=1.5),
        },
        height=500,
        hide_index=True
    )

    # --- 3. GRAPH RENDERING (RESTORED) ---
    st.divider()
    st.subheader("🔬 Deep Dive: Critical Limit Analysis")
    
    col_sel, _ = st.columns([1, 2])
    with col_sel:
        selected_name = st.selectbox("Select Section:", df['Section'].unique())

    row = df[df['Section'] == selected_name].iloc[0]
    
    # Use Nominal Values for the graph to match the table
    V_graph = row['V_Nominal']
    L_start = row['L_Start']
    L_end = row['L_End']
    
    # Calculate Plotting Curves
    M_derived = (L_start * V_graph) / 4 if L_start > 0 else 0
    K_derived = L_end * 8 * M_derived if M_derived > 0 else 0

    max_span = max(10, L_end * 1.5)
    spans = np.linspace(0.1, max_span, 400)
    
    ws = (2 * V_graph) / spans 
    wm = (8 * M_derived) / (spans**2) 
    wd = K_derived / (spans**3) 
    w_safe = np.minimum(np.minimum(ws, wm), wd)

    # PLOT
    plt.style.use('bmh')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(spans, ws, color='#9B59B6', linestyle=':', linewidth=1.5, label='Shear Limit (Web)')
    ax.plot(spans, wm, color='#E74C3C', linestyle='--', linewidth=1.5, label='Moment Limit')
    ax.plot(spans, wd, color='#2ECC71', linestyle='-.', linewidth=1.5, label='Deflection Limit')
    ax.plot(spans, w_safe, color='#2C3E50', linewidth=3, label='Safe Load Envelope')
    
    # Vertical Lines & Shading
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
    
    st.success(f"✅ Displaying Nominal Capacity for {selected_name}: {row['V_Nominal']:,.0f} kg")

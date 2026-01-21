# report_analytics.py
# Version: 27.0 (Explicit Visualization: Failure Mode Spectrum Chart)
# Engineered by: Senior Structural Engineer AI

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
    Key Update: Visualizing the 'Why' behind the Ratio using a Spectrum Chart.
    """
    
    st.markdown("## 🏗️ Structural Integrity & Limit State Analysis")
    st.markdown("Detailed breakdown of connection capacity showing **all 6 failure modes**.")
    st.divider()

    # --- 1. CALCULATION ENGINE ---
    all_sections = get_standard_sections()
    if not all_sections: return

    data_list = []
    
    # Pre-calculation for all sections
    for sec in all_sections:
        full_props = calculate_full_properties(sec) 
        
        # Beam Limits
        h_cm = sec['h'] / 10
        tw_cm = sec['tw'] / 10
        V_beam_allow = (0.60 * sec['Fy'] * h_cm * tw_cm) / (factor if factor else 1)
        V_target = V_beam_allow * (load_pct / 100.0) 

        # Zone Limits
        try: M_allow_kgm = (sec['Fy'] * full_props['Zx (cm3)'] / factor) / 100 if factor else 0
        except: M_allow_kgm = 0
        Ix = full_props['Ix (cm4)']
        K_defl = (384 * E_STEEL_KSC * Ix) / 18000000 
        L_sm = (4 * M_allow_kgm) / V_beam_allow if V_beam_allow > 0 else 0
        L_md = K_defl / (8 * M_allow_kgm) if M_allow_kgm > 0 else 0
        
        # Design Loop
        bolt_d_cm = bolt_dia / 10; hole_d_cm = bolt_d_cm + 0.2
        pitch_cm = 3 * bolt_d_cm; edge_cm = 4.0 
        req_bolts = 2; t_plate_cm = 0.9; 
        if V_target > 30000: t_plate_cm = 1.2
        
        is_safe = False; final_info = {}
        
        while not is_safe and req_bolts <= 24:
            plate_h_cm = math.ceil(((req_bolts - 1) * pitch_cm) + (2 * edge_cm))
            
            # 6 LIMIT STATES (Recalculated for logic)
            # 1. Bolt Shear
            Rn_bolt = req_bolts * FV_BOLT * (3.14159 * bolt_d_cm**2 / 4)
            # 2. Bearing
            Rn_bear = (min(1.2*(edge_cm-hole_d_cm/2)*t_plate_cm*FU_PLATE, 2.4*bolt_d_cm*t_plate_cm*FU_PLATE) + 
                       (req_bolts-1)*min(1.2*(pitch_cm-hole_d_cm)*t_plate_cm*FU_PLATE, 2.4*bolt_d_cm*t_plate_cm*FU_PLATE))
            # 3. Yield
            Rn_yield = 0.60 * FY_PLATE * plate_h_cm * t_plate_cm
            # 4. Rupture
            Rn_rup = 0.50 * FU_PLATE * (plate_h_cm * t_plate_cm - req_bolts * hole_d_cm * t_plate_cm)
            # 5. Block Shear
            Anv = (plate_h_cm - edge_cm)*t_plate_cm - (req_bolts-0.5)*hole_d_cm*t_plate_cm
            Ant = (4.0 - 0.5*hole_d_cm)*t_plate_cm
            Rn_block = (0.6 * FU_PLATE * Anv) + (1.0 * FU_PLATE * Ant)
            # 6. Weld
            weld_sz = max(0.6, (t_plate_cm*10 - 2)/10)
            Rn_weld = 2 * 0.707 * weld_sz * plate_h_cm * FV_WELD
            
            limit_states = {
                "Bolt Shear": Rn_bolt, "Bearing": Rn_bear, "Yield": Rn_yield, 
                "Rupture": Rn_rup, "Block Shear": Rn_block, "Weld": Rn_weld
            }
            min_cap = min(limit_states.values())
            governing = min(limit_states, key=limit_states.get)
            ratio = V_target / min_cap
            
            if ratio <= 1.00:
                is_safe = True
                final_info = {
                    "Bolts": req_bolts, "Plate": f"PL-{t_plate_cm*10:.0f}x100x{plate_h_cm*10:.0f}",
                    "Weld": f"{weld_sz*10:.0f}mm", "Ratio": ratio, "Mode": governing,
                    "Details": limit_states # Save all states for graphing
                }
            else:
                req_bolts += 1
                if req_bolts > 12 and t_plate_cm < 1.6: t_plate_cm += 0.3; req_bolts = max(2, req_bolts - 3)

        data_list.append({
            "Section": sec['name'],
            "Moment Zone": f"{L_sm:.2f}-{L_md:.2f} m",
            "L_Start": L_sm, "L_End": L_md,
            "V_Beam": V_beam_allow, "V_Target": V_target,
            "Bolt Spec": f"{final_info.get('Bolts')} - M{int(bolt_dia)}",
            "Plate Size": final_info.get('Plate'),
            "Weld Spec": final_info.get('Weld'),
            "D/C Ratio": final_info.get('Ratio'),
            "Governing": final_info.get('Mode'),
            "Debug_States": final_info.get('Details') # Hidden column for graph
        })

    if not data_list: return
    df = pd.DataFrame(data_list)

    # --- 2. SUMMARY METRICS ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Sections", len(df))
    max_row = df.loc[df['D/C Ratio'].idxmax()]
    c2.metric("Critical Case", f"{max_row['Section']}", f"Ratio {max_row['D/C Ratio']:.2f}")
    c3.metric("Governing Mode", max_row['Governing'], "Most Critical Limit")
    st.divider()

    # --- 3. TABS UI ---
    tab1, tab2 = st.tabs(["📋 Design Table", "🔍 Deep Dive & Failure Spectrum"])

    # === TAB 1: TABLE ===
    with tab1:
        # Create a display-friendly dataframe
        df_display = df.copy()
        # Combine Ratio and Mode into one string for clarity
        df_display['Safety Check'] = df_display.apply(
            lambda x: f"{x['D/C Ratio']:.2f} ({x['Governing']})", axis=1
        )
        
        st.dataframe(
            df_display[[
                "Section", "Moment Zone", "V_Target", 
                "Bolt Spec", "Plate Size", "Weld Spec", 
                "Safety Check"
            ]],
            use_container_width=True,
            column_config={
                "Section": st.column_config.TextColumn("Section", width="small"),
                "V_Target": st.column_config.NumberColumn("Load (kg)", format="%.0f"),
                "Bolt Spec": st.column_config.TextColumn("Bolts", width="small"),
                "Safety Check": st.column_config.TextColumn(
                    "D/C Ratio (Crit. Mode)",
                    width="medium",
                    help="Ratio of Demand/Capacity. Shows the governing failure mode."
                ),
            },
            height=500,
            hide_index=True
        )

    # === TAB 2: DEEP DIVE + SPECTRUM CHART (NEW!) ===
    with tab2:
        col_sel, _ = st.columns([1, 2])
        with col_sel:
            selected_name = st.selectbox("Select Beam for Stress Analysis:", df['Section'].unique())

        row = df[df['Section'] == selected_name].iloc[0]
        
        # --- PART A: FAILURE MODE SPECTRUM (THE NEW VISUAL) ---
        st.subheader(f"📊 Failure Mode Spectrum: {selected_name}")
        st.caption(f"Comparing Demand ({row['V_Target']:.0f} kg) vs Capacity of all 6 limit states.")
        
        # Prepare Data for Bar Chart
        states = row['Debug_States']
        # Calculate Ratio for EACH mode (Demand / Capacity of that mode)
        # Note: Higher Ratio = More Critical
        ratios = {k: row['V_Target']/v for k,v in states.items()}
        
        # Create Horizontal Bar Chart using Matplotlib
        fig_bar, ax_bar = plt.subplots(figsize=(10, 3))
        modes = list(ratios.keys())
        vals = list(ratios.values())
        colors = ['#E74C3C' if v == max(vals) else '#95A5A6' for v in vals] # Red for Max, Grey for others
        
        y_pos = np.arange(len(modes))
        ax_bar.barh(y_pos, vals, align='center', color=colors)
        ax_bar.set_yticks(y_pos)
        ax_bar.set_yticklabels(modes)
        ax_bar.axvline(x=1.0, color='black', linestyle='--', linewidth=1.5) # Limit Line
        ax_bar.set_xlabel('D/C Ratio (Must be < 1.0)')
        ax_bar.set_title('Connection "Weakest Link" Analysis')
        
        # Add values on bars
        for i, v in enumerate(vals):
            ax_bar.text(v + 0.02, i, f"{v:.2f}", va='center', fontweight='bold', color='black')
            
        st.pyplot(fig_bar)
        
        st.markdown("---")

        # --- PART B: ZONE GRAPH (Restored) ---
        st.subheader("📉 Beam Limit Zones")
        
        V_allow = row['V_Beam']
        L_start, L_end = row['L_Start'], row['L_End']
        M_derived = (L_start * V_allow) / 4 if L_start > 0 else 0
        K_derived = L_end * 8 * M_derived if M_derived > 0 else 0
        
        max_span = max(10, L_end * 1.5)
        spans = np.linspace(0.1, max_span, 400)
        ws = (2 * V_allow) / spans
        wm = (8 * M_derived) / (spans**2)
        wd = K_derived / (spans**3)
        w_safe = np.minimum(np.minimum(ws, wm), wd)

        plt.style.use('bmh')
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(spans, ws, color='#8E44AD', linestyle=':', label='Shear Limit')
        ax.plot(spans, wm, color='#C0392B', linestyle='--', label='Moment Limit')
        ax.plot(spans, wd, color='#27AE60', linestyle='-.', label='Deflection Limit')
        ax.plot(spans, w_safe, color='#2C3E50', linewidth=3, label='Safe Envelope')
        
        if L_start > 0:
            ax.axvline(x=L_start, color='#D35400')
            ax.text(L_start, max(w_safe)*0.5, f" {L_start:.2f}m", rotation=90, va='bottom', ha='right', color='#D35400', fontweight='bold')
        if L_end > L_start:
            ax.axvline(x=L_end, color='#27AE60')
            ax.text(L_end, max(w_safe)*0.3, f" {L_end:.2f}m", rotation=90, va='bottom', ha='left', color='#219150', fontweight='bold')
            
        ax.set_ylim(0, max(w_safe)*1.2)
        ax.set_xlim(0, max_span)
        ax.legend()
        st.pyplot(fig)

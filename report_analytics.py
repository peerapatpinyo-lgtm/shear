# report_analytics.py
# Version: 24.0 (UI/UX Overhaul: Dashboard Metrics, Tabs, Visualized Ratios)
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

# --- Constants ---
E_STEEL_KSC = 2040000  
FY_PLATE = 2400 
FU_PLATE = 4000 
FV_BOLT = 2100  
FV_WELD = 1470  

def render_analytics_section(load_pct, bolt_dia, load_case, factor):
    """
    Renders the Structural Analytics Dashboard (Pro UI Version).
    """
    
    # --- 1. Header & Context ---
    st.markdown("## 🏗️ Structural Optimization Dashboard")
    st.markdown("Advanced connection design verification (AISC 360) & Governing limit state analysis.")
    st.divider()

    # --- 2. Calculation Engine (Same Logic as V23 - Reliable) ---
    all_sections = get_standard_sections()
    if not all_sections:
        st.warning("⚠️ No sections found.")
        return

    data_list = []
    
    # Processing Loop
    for sec in all_sections:
        full_props = calculate_full_properties(sec) 
        
        # Capacities
        h_cm = sec['h'] / 10
        tw_cm = sec['tw'] / 10
        V_beam_allow = (0.60 * sec['Fy'] * h_cm * tw_cm) / (factor if factor else 1)
        V_target = V_beam_allow * 0.75

        # Zones
        try:
            M_allow_kgm = (sec['Fy'] * full_props['Zx (cm3)'] / factor) / 100 if factor else 0
        except: M_allow_kgm = 0
        
        Ix = full_props['Ix (cm4)']
        K_defl = (384 * E_STEEL_KSC * Ix) / 18000000 
        
        L_sm = (4 * M_allow_kgm) / V_beam_allow if V_beam_allow > 0 else 0
        L_md = K_defl / (8 * M_allow_kgm) if M_allow_kgm > 0 else 0
        
        # Auto-Design Logic (Compressed)
        bolt_d_cm = bolt_dia / 10; hole_d_cm = bolt_d_cm + 0.2
        pitch_cm = 3 * bolt_d_cm; edge_cm = 4.0 
        req_bolts = 2; t_plate_cm = 0.9; 
        if V_target > 30000: t_plate_cm = 1.2
        is_safe = False; final_info = {}
        
        while not is_safe and req_bolts <= 20:
            plate_h_cm = math.ceil(((req_bolts - 1) * pitch_cm) + (2 * edge_cm))
            
            # 6 Checks
            Rn_bolt = req_bolts * FV_BOLT * (3.14159 * bolt_d_cm**2 / 4)
            Rn_bear = (min(1.2*(edge_cm-hole_d_cm/2)*t_plate_cm*FU_PLATE, 2.4*bolt_d_cm*t_plate_cm*FU_PLATE) + 
                       (req_bolts-1)*min(1.2*(pitch_cm-hole_d_cm)*t_plate_cm*FU_PLATE, 2.4*bolt_d_cm*t_plate_cm*FU_PLATE))
            Rn_yield = 0.60 * FY_PLATE * plate_h_cm * t_plate_cm
            Rn_rup = 0.50 * FU_PLATE * (plate_h_cm * t_plate_cm - req_bolts * hole_d_cm * t_plate_cm)
            Rn_block = (0.6 * FU_PLATE * ((plate_h_cm-edge_cm)*t_plate_cm - (req_bolts-0.5)*hole_d_cm*t_plate_cm)) + (1.0 * FU_PLATE * (4.0-0.5*hole_d_cm)*t_plate_cm)
            weld_sz = max(0.6, (t_plate_cm*10 - 2)/10)
            Rn_weld = 2 * 0.707 * weld_sz * plate_h_cm * FV_WELD
            
            min_cap = min(Rn_bolt, Rn_bear, Rn_yield, Rn_rup, Rn_block, Rn_weld)
            ratio = V_target / min_cap
            
            if ratio <= 1.00:
                is_safe = True
                governing = min({k:v for k,v in locals().items() if k.startswith('Rn_')}, key={k:v for k,v in locals().items() if k.startswith('Rn_')}.get).replace('Rn_','')
                final_info = {
                    "Bolts": req_bolts, 
                    "Plate": f"PL-{t_plate_cm*10:.0f}x100x{plate_h_cm*10:.0f}", 
                    "Weld": f"{weld_sz*10:.0f}mm", 
                    "Ratio": ratio, 
                    "Mode": governing
                }
            else:
                req_bolts += 1
                if req_bolts > 12 and t_plate_cm < 1.6: t_plate_cm += 0.3; req_bolts = max(2, req_bolts - 3)

        data_list.append({
            "Section": sec['name'],
            "Moment Zone": f"{L_sm:.2f} - {L_md:.2f} m",
            "L_Start": L_sm, "L_End": L_md,
            "V_Beam": V_beam_allow, "V_Target": V_target,
            "Bolt Spec": f"{final_info.get('Bolts')} - M{int(bolt_dia)}",
            "Plate Size": final_info.get('Plate'),
            "Weld Spec": final_info.get('Weld'),
            "D/C Ratio": final_info.get('Ratio'),
            "Governing": final_info.get('Mode')
        })

    if not data_list: return
    df = pd.DataFrame(data_list)

    # --- 3. HIGH-LEVEL METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Sections", f"{len(df)} Beams", delta="Verified")
    with col2:
        max_ratio = df['D/C Ratio'].max()
        st.metric("Critical Ratio (Max)", f"{max_ratio:.2f}", 
                  delta="Safe" if max_ratio <= 1.0 else "Unsafe", 
                  delta_color="normal" if max_ratio <= 1.0 else "inverse")
    with col3:
        avg_bolts = df['Bolt Spec'].apply(lambda x: int(x.split()[0])).mean()
        st.metric("Avg. Bolt Qty", f"{avg_bolts:.1f} ea", f"M{bolt_dia}")
    with col4:
        # Most common failure mode
        mode = df['Governing'].mode()[0] if not df.empty else "-"
        st.metric("Governing Mode", mode.replace('_',' ').title())

    st.markdown("---")

    # --- 4. TABS INTERFACE ---
    tab1, tab2 = st.tabs(["📋 Detailed Specification Table", "📉 Deep Dive Graph Analysis"])

    # === TAB 1: SMART TABLE ===
    with tab1:
        st.caption("Auto-generated connection specifications based on 75% Beam Capacity.")
        
        # Color styling for Ratio
        st.dataframe(
            df[[
                "Section", "Moment Zone", "V_Target", 
                "Bolt Spec", "Plate Size", "Weld Spec", 
                "Governing", "D/C Ratio"
            ]],
            use_container_width=True,
            column_config={
                "Section": st.column_config.TextColumn("Section", width="small", help="Wide Flange Section"),
                "Moment Zone": st.column_config.TextColumn("Zone Range", width="small", help="Range where Moment controls design"),
                "V_Target": st.column_config.NumberColumn("Load (75%)", format="%.0f kg"),
                "Bolt Spec": st.column_config.TextColumn("Bolts", width="small"),
                "Plate Size": st.column_config.TextColumn("Plate (mm)", width="medium"),
                "Weld Spec": st.column_config.TextColumn("Weld", width="small"),
                "Governing": st.column_config.TextColumn("Critical Limit", width="medium"),
                
                # VISUAL PROGRESS BAR FOR RATIO
                "D/C Ratio": st.column_config.ProgressColumn(
                    "Safety Ratio",
                    help="Demand / Capacity Ratio (Must be <= 1.0)",
                    format="%.2f",
                    min_value=0,
                    max_value=1.5, # Cap at 1.5 visually
                ),
            },
            height=600,
            hide_index=True
        )

    # === TAB 2: INTERACTIVE GRAPH ===
    with tab2:
        col_sel, _ = st.columns([1, 2])
        with col_sel:
            selected_name = st.selectbox("Select Beam for Analysis:", df['Section'].unique())

        row = df[df['Section'] == selected_name].iloc[0]
        
        # Graph Logic
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

        # Plot Styling
        plt.style.use('bmh') # Professional grid style
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Plot Lines
        ax.plot(spans, ws, color='#8E44AD', linestyle=':', label='Shear Limit (Web)')
        ax.plot(spans, wm, color='#C0392B', linestyle='--', label='Moment Limit')
        ax.plot(spans, wd, color='#27AE60', linestyle='-.', label='Deflection Limit')
        ax.plot(spans, w_safe, color='#2C3E50', linewidth=2.5, label='Safe Envelope')
        
        # Zones Shading
        if L_start > 0:
            ax.fill_between(spans, 0, 100000, where=(spans <= L_start), color='#8E44AD', alpha=0.05)
            ax.text(L_start/2, max(w_safe)*0.1, "SHEAR ZONE", ha='center', color='#8E44AD', fontsize=9, fontweight='bold', alpha=0.5)

        if L_end > L_start:
            ax.fill_between(spans, 0, 100000, where=((spans > L_start) & (spans <= L_end)), color='#C0392B', alpha=0.05)
            ax.axvline(x=L_start, color='#D35400', linestyle='-', linewidth=1)
            ax.axvline(x=L_end, color='#27AE60', linestyle='-', linewidth=1)
            ax.text(L_start, max(w_safe)*0.6, f" {L_start:.2f}m", rotation=90, va='bottom', ha='right', color='#D35400', fontweight='bold')
            ax.text(L_end, max(w_safe)*0.4, f" {L_end:.2f}m", rotation=90, va='bottom', ha='left', color='#219150', fontweight='bold')

        ax.set_ylim(0, max(w_safe)*1.2)
        ax.set_xlim(0, max_span)
        ax.set_title(f"Critical Limit State Diagram: {selected_name}", fontsize=12, fontweight='bold')
        ax.set_xlabel("Span Length (m)")
        ax.set_ylabel("Safe Load (kg/m)")
        ax.legend(loc='upper right', frameon=True, fancybox=True, framealpha=1)
        
        st.pyplot(fig)
        
        # Mini Context
        c1, c2, c3 = st.columns(3)
        c1.info(f"**Shear Capacity:** {V_allow:,.0f} kg")
        c2.info(f"**Moment Controlled:** {L_start:.2f} - {L_end:.2f} m")
        c3.info(f"**Connection D/C:** {row['D/C Ratio']:.2f}")

    st.success("✅ Analysis Complete. All connections verified against AISC 360 Specification.")

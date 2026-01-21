# report_analytics.py
# Version: 26.0 (Restored V24 UI + Rigorous V25 Math)
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
    Restored UI: Tabs + Deep Dive Graph.
    Logic: Full 6-Mode Failure Analysis.
    """
    
    st.markdown("## 🏗️ Structural Optimization Dashboard")
    st.markdown("Detailed verification of connection capacity against Beam Limit States (Shear/Moment/Deflection).")
    st.divider()

    # --- 1. CALCULATION ENGINE (Rigorous) ---
    all_sections = get_standard_sections()
    if not all_sections: return

    data_list = []
    
    for sec in all_sections:
        full_props = calculate_full_properties(sec) 
        
        # A. Beam Limits
        h_cm = sec['h'] / 10
        tw_cm = sec['tw'] / 10
        V_beam_allow = (0.60 * sec['Fy'] * h_cm * tw_cm) / (factor if factor else 1)
        V_target = V_beam_allow * (load_pct / 100.0) # User Defined Load

        # Zones Calculation
        try:
            M_allow_kgm = (sec['Fy'] * full_props['Zx (cm3)'] / factor) / 100 if factor else 0
        except: M_allow_kgm = 0
        
        Ix = full_props['Ix (cm4)']
        K_defl = (384 * E_STEEL_KSC * Ix) / 18000000 
        
        # Transition Points
        L_sm = (4 * M_allow_kgm) / V_beam_allow if V_beam_allow > 0 else 0
        L_md = K_defl / (8 * M_allow_kgm) if M_allow_kgm > 0 else 0
        
        # B. Connection Auto-Design (6 Modes Check)
        bolt_d_cm = bolt_dia / 10; hole_d_cm = bolt_d_cm + 0.2
        pitch_cm = 3 * bolt_d_cm; edge_cm = 4.0 
        req_bolts = 2; t_plate_cm = 0.9; 
        if V_target > 30000: t_plate_cm = 1.2
        
        is_safe = False; final_info = {}
        
        while not is_safe and req_bolts <= 24:
            plate_h_cm = math.ceil(((req_bolts - 1) * pitch_cm) + (2 * edge_cm))
            
            # 6 Limit States
            Rn_bolt = req_bolts * FV_BOLT * (3.14159 * bolt_d_cm**2 / 4)
            
            Lc_edge = edge_cm - hole_d_cm/2
            Lc_inner = pitch_cm - hole_d_cm
            Rn_bear = (min(1.2*Lc_edge*t_plate_cm*FU_PLATE, 2.4*bolt_d_cm*t_plate_cm*FU_PLATE) + 
                       (req_bolts-1)*min(1.2*Lc_inner*t_plate_cm*FU_PLATE, 2.4*bolt_d_cm*t_plate_cm*FU_PLATE))
            
            Rn_yield = 0.60 * FY_PLATE * plate_h_cm * t_plate_cm
            Rn_rup = 0.50 * FU_PLATE * (plate_h_cm * t_plate_cm - req_bolts * hole_d_cm * t_plate_cm)
            
            Anv = (plate_h_cm - edge_cm)*t_plate_cm - (req_bolts-0.5)*hole_d_cm*t_plate_cm
            Ant = (4.0 - 0.5*hole_d_cm)*t_plate_cm
            Rn_block = (0.6 * FU_PLATE * Anv) + (1.0 * FU_PLATE * Ant)
            
            weld_sz = max(0.6, (t_plate_cm*10 - 2)/10)
            Rn_weld = 2 * 0.707 * weld_sz * plate_h_cm * FV_WELD
            
            # Evaluate
            limit_states = {"Bolt Shear": Rn_bolt, "Bearing": Rn_bear, "Yield": Rn_yield, 
                            "Rupture": Rn_rup, "Block Shear": Rn_block, "Weld": Rn_weld}
            min_cap = min(limit_states.values())
            governing = min(limit_states, key=limit_states.get)
            
            ratio = V_target / min_cap
            
            if ratio <= 1.00:
                is_safe = True
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

    # --- 2. DISPLAY LAYOUT (Restored V24 Style) ---
    
    # Summary Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Beams", len(df))
    max_r = df['D/C Ratio'].max()
    c2.metric("Max Safety Ratio", f"{max_r:.2f}", delta="OK" if max_r<=1.0 else "Check", delta_color="inverse")
    c3.metric("Critical Limit State", df['Governing'].mode()[0])

    st.markdown("---")

    # TABS SYSTEM
    tab1, tab2 = st.tabs(["📋 Specification Table", "📉 Deep Dive Graph"])

    # === TAB 1: DATA TABLE ===
    with tab1:
        st.dataframe(
            df[[
                "Section", "Moment Zone", "V_Target", 
                "Bolt Spec", "Plate Size", "Weld Spec", 
                "Governing", "D/C Ratio"
            ]],
            use_container_width=True,
            column_config={
                "Section": st.column_config.TextColumn("Section", width="small"),
                "V_Target": st.column_config.NumberColumn("Load (kg)", format="%.0f"),
                "Bolt Spec": st.column_config.TextColumn("Bolts", width="small"),
                "Plate Size": st.column_config.TextColumn("Plate (mm)", width="medium"),
                "Weld Spec": st.column_config.TextColumn("Weld", width="small"),
                "Governing": st.column_config.TextColumn("Critical Mode", width="medium"),
                "D/C Ratio": st.column_config.ProgressColumn(
                    "Safety Ratio",
                    format="%.2f",
                    min_value=0, max_value=1.2,
                    help="Values > 1.0 indicate failure."
                ),
            },
            height=600,
            hide_index=True
        )

    # === TAB 2: DEEP DIVE GRAPH (The One You Liked) ===
    with tab2:
        col_sel, _ = st.columns([1, 2])
        with col_sel:
            selected_name = st.selectbox("Select Beam:", df['Section'].unique())

        row = df[df['Section'] == selected_name].iloc[0]
        
        # Prepare Data for Plotting
        V_allow = row['V_Beam']
        L_start, L_end = row['L_Start'], row['L_End']
        
        # Re-derive Moment/Deflection curves based on transitions
        M_derived = (L_start * V_allow) / 4 if L_start > 0 else 0
        K_derived = L_end * 8 * M_derived if M_derived > 0 else 0
        
        max_span = max(10, L_end * 1.5)
        spans = np.linspace(0.1, max_span, 400)
        
        ws = (2 * V_allow) / spans
        wm = (8 * M_derived) / (spans**2)
        wd = K_derived / (spans**3)
        w_safe = np.minimum(np.minimum(ws, wm), wd)

        # Plot
        plt.style.use('bmh')
        fig, ax = plt.subplots(figsize=(10, 5))
        
        ax.plot(spans, ws, color='#8E44AD', linestyle=':', label='Shear Limit')
        ax.plot(spans, wm, color='#C0392B', linestyle='--', label='Moment Limit')
        ax.plot(spans, wd, color='#27AE60', linestyle='-.', label='Deflection Limit')
        ax.plot(spans, w_safe, color='#2C3E50', linewidth=3, label='Safe Envelope')
        
        # Vertical Lines & Shading (Restored)
        if L_start > 0:
            ax.axvline(x=L_start, color='#D35400', linestyle='-')
            ax.text(L_start, max(w_safe)*0.5, f" Start: {L_start:.2f}m", rotation=90, va='bottom', ha='right', color='#D35400', fontweight='bold')
            
        if L_end > L_start:
            ax.axvline(x=L_end, color='#27AE60', linestyle='-')
            ax.text(L_end, max(w_safe)*0.3, f" End: {L_end:.2f}m", rotation=90, va='bottom', ha='left', color='#219150', fontweight='bold')
            
            # Shading Moment Zone
            ax.fill_between(spans, 0, max(w_safe)*1.5, where=((spans >= L_start) & (spans <= L_end)), color='#C0392B', alpha=0.05)
            ax.text((L_start+L_end)/2, max(w_safe)*0.1, "MOMENT CONTROL", ha='center', color='#C0392B', alpha=0.6, fontweight='bold')

        ax.set_ylim(0, max(w_safe)*1.2)
        ax.set_xlim(0, max_span)
        ax.set_xlabel("Span Length (m)")
        ax.set_ylabel("Safe Load (kg/m)")
        ax.legend()
        
        st.pyplot(fig)
        
        # Mini Stats below graph
        c1, c2, c3 = st.columns(3)
        c1.info(f"**Web Shear Cap:** {V_allow:,.0f} kg")
        c2.info(f"**Connection D/C:** {row['D/C Ratio']:.2f}")
        c3.warning(f"**Governing:** {row['Governing']}")

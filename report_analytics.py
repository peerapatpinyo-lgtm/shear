# report_analytics.py
# Version: 18.0 (Full Plate Sizing: PL-TxWxL | Fabrication Ready)
# Engineered by: Senior Structural Engineer AI

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- Module Integrity Check ---
try:
    from report_generator import get_standard_sections, calculate_connection, calculate_full_properties
except ImportError:
    st.error("🚨 Critical Error: Core module 'report_generator.py' is missing. System cannot proceed.")
    st.stop()

# --- Constants ---
E_STEEL_KSC = 2040000  
DEFLECTION_RATIO = 360 

def render_analytics_section(load_pct, bolt_dia, load_case, factor):
    """
    Renders the Structural Analytics Dashboard.
    - Deep Dive Graph (Critical Limits)
    - Detailed Specification Table with FULL PLATE SIZING.
    """
    st.markdown("## 📊 Structural Integrity & Optimization Dashboard")
    st.markdown("Analysis of governing failure modes and fabrication specifications.")
    
    # --- 1. Data Processing ---
    all_sections = get_standard_sections()
    if not all_sections:
        st.warning("⚠️ System Notice: No structural sections found.")
        return

    data_list = []
    
    for sec in all_sections:
        full_props = calculate_full_properties(sec) 
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        
        # 1.1 Allowable Capacities
        try:
            V_n = r.get('Vn_beam', 0)
            V_allow = V_n / factor if factor and factor > 0 else V_n
        except: V_allow = 0
            
        try:
            M_n_kgcm = sec['Fy'] * full_props['Zx (cm3)']
            M_allow_kgm = (M_n_kgcm / factor) / 100 if factor and factor > 0 else 0
        except: M_allow_kgm = 0

        # 1.2 Calculate 75% Shear Capacity
        V_75_pct = V_allow * 0.75

        # 1.3 Critical Intersection Analysis (Moment Zone)
        Ix = full_props['Ix (cm4)']
        K_defl = (384 * E_STEEL_KSC * Ix) / 18000000 
        
        L_shear_moment_limit = (4 * M_allow_kgm) / V_allow if V_allow > 0 else 0
        L_moment_defl_limit = K_defl / (8 * M_allow_kgm) if M_allow_kgm > 0 else 0
        
        # Moment Zone Text
        if L_moment_defl_limit > L_shear_moment_limit:
            zone_text = f"{L_shear_moment_limit:.2f} - {L_moment_defl_limit:.2f}"
        else:
            zone_text = "Check Design"

        # 1.4 Connection & Plate Sizing (Fabrication Ready)
        bolt_qty = r.get('Bolt Qty', 0)
        t_plate = r.get('t_plate', 0)
        
        # --- Logic: Generate Exact Plate Size (PL-T x W x L) ---
        # Height (L): Based on Bolt Pitch (3d) and Edge (e.g. 35-40mm)
        # Width (W): Standard 100mm for single shear tab (or 120mm for larger bolts)
        
        pitch = 3 * bolt_dia * 10 # convert cm to mm
        edge_dist = 40 # mm (Standard edge distance)
        
        if bolt_qty > 0:
            # Height = (rows-1)*pitch + 2*edge
            plate_h_mm = ((bolt_qty - 1) * pitch) + (2 * edge_dist)
            
            # Round up height to nearest 10mm
            plate_h_mm = math.ceil(plate_h_mm / 10.0) * 10
            
            plate_w_mm = 100 # Standard Width
            
            # Format: PL-9x100x190
            plate_str = f"PL-{t_plate:.0f}x{plate_w_mm}x{plate_h_mm:.0f}"
        else:
            plate_str = "-"

        # 1.5 Compiling Data
        data_list.append({
            "Name": sec['name'].replace("H-", ""), 
            "Section": sec['name'],
            "Weight (kg/m)": full_props['Area (cm2)']*0.785,
            # Limits for Graph
            "L_Start": L_shear_moment_limit, 
            "L_End": L_moment_defl_limit,
            # Table Data
            "Moment Zone Range": zone_text,
            "V_75": V_75_pct,
            "Bolts": bolt_qty,
            "Plate Size": plate_str, # The Full Size String
            # Deep Dive Context
            "V_allow": V_allow,         
            "M_allow_kgm": M_allow_kgm, 
            "K_defl": K_defl
        })

    if not data_list: return
    df = pd.DataFrame(data_list)

    # ==========================================
    # 🔬 GRAPH: DEEP DIVE CRITICAL LIMIT ANALYSIS
    # ==========================================
    st.subheader("🔬 Deep Dive: Critical Limit Analysis")
    
    if 'Section' not in df.columns or df.empty: return

    col_sel, col_empty = st.columns([1, 2])
    with col_sel:
        selected_name = st.selectbox("Select Section:", df['Section'].unique())

    # --- Prepare Data for Deep Dive ---
    row = df[df['Section'] == selected_name].iloc[0]
    V_allow = row['V_allow']
    M_allow_kgm = row['M_allow_kgm']
    K_defl = row['K_defl']
    L_start = row['L_Start']
    L_end = row['L_End']

    max_span_plot = max(8, L_end * 1.4)
    spans = np.linspace(0.5, max_span_plot, 300)
    
    # Calculate Curves
    ws = (2 * V_allow) / spans
    wm = (8 * M_allow_kgm) / (spans**2)
    wd = K_defl / (spans**3)
    w_safe_envelope = np.minimum(np.minimum(ws, wm), wd)

    # --- PLOTTING ---
    fig_d, ax_d = plt.subplots(figsize=(10, 6))
    ax_d.grid(True, which='both', linestyle='--', alpha=0.4)
    
    ax_d.plot(spans, ws, color='#9B59B6', linestyle=':', linewidth=1.5, alpha=0.6, label='Shear Limit')
    ax_d.plot(spans, wd, color='#2ECC71', linestyle='-.', linewidth=1.5, alpha=0.6, label='Deflection Limit')
    ax_d.plot(spans, wm, color='#E74C3C', linestyle='--', linewidth=1.5, alpha=0.6, label='Moment Limit')
    ax_d.plot(spans, w_safe_envelope, color='#2C3E50', linewidth=3, label='Safe Envelope')
    
    # Fill Moment Zone
    if L_end > L_start:
        idx_start = np.searchsorted(spans, L_start)
        idx_end = np.searchsorted(spans, L_end)
        ax_d.fill_between(spans[idx_start:idx_end], 0, w_safe_envelope[idx_start:idx_end], 
                          color='#E74C3C', alpha=0.15, label='Moment Zone')

    # Vertical Lines
    if 0.5 < L_start < max_span_plot:
        ax_d.axvline(x=L_start, color='#E67E22', linestyle='-', linewidth=1)
        ax_d.text(L_start, max(w_safe_envelope)*0.8, f" Start: {L_start:.2f} m", 
                  rotation=90, va='bottom', ha='right', color='#D35400', fontweight='bold')

    if 0.5 < L_end < max_span_plot:
        ax_d.axvline(x=L_end, color='#27AE60', linestyle='-', linewidth=1)
        ax_d.text(L_end, max(w_safe_envelope)*0.6, f" End: {L_end:.2f} m", 
                  rotation=90, va='bottom', ha='left', color='#219150', fontweight='bold')

    ax_d.set_ylim(0, max(w_safe_envelope)*1.2 if max(w_safe_envelope)>0 else 1000)
    ax_d.set_xlim(0.5, max_span_plot)
    ax_d.set_xlabel("Span Length (m)", fontweight='bold')
    ax_d.set_ylabel("Safe Load (kg/m)", fontweight='bold')
    ax_d.legend(loc='upper right')
    st.pyplot(fig_d)
    
    col1, col2, col3 = st.columns(3)
    with col1: st.markdown(f"🟣 **Shear Zone:** <br>0.00 - {L_start:.2f} m", unsafe_allow_html=True)
    with col2: st.markdown(f"🔴 **Moment Zone:** <br><span style='color:#C0392B'><b>{L_start:.2f} - {L_end:.2f} m</b></span>", unsafe_allow_html=True)
    with col3: st.markdown(f"🟢 **Deflection Zone:** <br>> {L_end:.2f} m", unsafe_allow_html=True)

    st.divider()

    # --- TABLE ---
    st.subheader("📋 Specification Table: Moment Controlled Ranges")
    
    st.dataframe(
        df[["Section", "Moment Zone Range", "V_75", "Bolts", "Plate Size"]],
        use_container_width=True,
        column_config={
            "Section": st.column_config.TextColumn("Section", width="small"),
            "Moment Zone Range": st.column_config.TextColumn("✅ Moment Zone (m)", width="medium"),
            "V_75": st.column_config.NumberColumn("75% Shear (kg)", format="%.0f"),
            "Bolts": st.column_config.NumberColumn("Bolts", format="%d pcs"),
            "Plate Size": st.column_config.TextColumn("Plate Size (PL-TxWxL)", width="medium", help="Calculated for Fabrication"),
        },
        height=500,
        hide_index=True
    )
    
import math # Ensure math is imported for plate sizing

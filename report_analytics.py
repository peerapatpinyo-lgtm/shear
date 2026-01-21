# report_analytics.py
# Version: Final Masterpiece
# Engineered by: Senior Structural Engineer AI
# Description: Advanced structural dashboard focusing on Governing Failure Modes and Safe Span Ranges.

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import math

# --- Module Integrity Check ---
try:
    from report_generator import get_standard_sections, calculate_connection, calculate_full_properties
except ImportError:
    st.error("🚨 Critical Error: Core module 'report_generator.py' is missing. System cannot proceed.")
    st.stop()

# --- Constants & Engineering Parameters ---
E_STEEL_KSC = 2040000  # Modulus of Elasticity (ksc)
DEFLECTION_RATIO = 360 # L/360 Standard Limit

def render_analytics_section(load_pct, bolt_dia, load_case, factor):
    """
    Renders the Advanced Structural Analytics Dashboard.
    Focus: Identifying the 'Moment Controlled Zone' for each section.
    """
    st.markdown("## 📊 Structural Integrity & Optimization Dashboard")
    st.markdown("This module analyzes the governing failure modes (Shear vs. Moment vs. Deflection) to determine the effective safe span range.")
    
    # --- 1. Data Acquisition & Processing ---
    all_sections = get_standard_sections()
    if not all_sections:
        st.warning("⚠️ System Notice: No structural sections found in the database.")
        return

    data_list = []
    
    for sec in all_sections:
        # 1.1 Structural Properties
        full_props = calculate_full_properties(sec) 
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        
        # 1.2 Capacity Retrieval (With Safety Factors)
        try:
            V_n = r.get('Vn_beam', 0)
            V_allow = V_n / factor if factor and factor > 0 else V_n
        except: V_allow = 0
            
        try:
            M_n_kgcm = sec['Fy'] * full_props['Zx (cm3)']
            M_allow_kgm = (M_n_kgcm / factor) / 100 if factor and factor > 0 else 0
        except: M_allow_kgm = 0

        # 1.3 Critical Intersection Analysis (The Heart of the Logic)
        Ix = full_props['Ix (cm4)']
        
        # Constant K for Deflection (Derived from Delta = 5wL^4/384EI and Delta_allow = L/360)
        # Resulting simplified K for w(kg/m) and L(m) equation structure
        K_defl = (384 * E_STEEL_KSC * Ix) / 18000000 
        
        # A. Start of Moment Zone (Shear Dominance ends, Moment Dominance begins)
        # Intersection: 2V/L = 8M/L^2  => L = 4M/V
        L_shear_moment_limit = (4 * M_allow_kgm) / V_allow if V_allow > 0 else 0
        
        # B. End of Moment Zone (Moment Dominance ends, Deflection Dominance begins)
        # Intersection: 8M/L^2 = K/L^3 => L = K/8M
        L_moment_defl_limit = K_defl / (8 * M_allow_kgm) if M_allow_kgm > 0 else 0
        
        # C. Valid Range Check
        if L_moment_defl_limit > L_shear_moment_limit:
            zone_text = f"{L_shear_moment_limit:.2f} - {L_moment_defl_limit:.2f}"
            status = "Optimal"
        else:
            zone_text = "N/A (Shear->Defl)" # Rare case where moment never governs
            status = "Inefficient"

        # 1.4 Representative Load Calculation (at Mid-Moment Zone)
        L_mid = (L_shear_moment_limit + L_moment_defl_limit) / 2
        safe_w_mid = (8 * M_allow_kgm) / (L_mid**2) if L_mid > 0 else 0

        # 1.5 Compiling the Dataset
        data_list.append({
            "Name": sec['name'].replace("H-", ""), 
            "Section": sec['name'],
            "Weight (kg/m)": full_props['Area (cm2)']*0.785,
            "Safe W (kg/m)": safe_w_mid,
            "L_Start": L_shear_moment_limit, 
            "L_End": L_moment_defl_limit,
            "Moment Zone Range": zone_text,
            "Status": status,
            # Deep Dive Context
            "V_allow": V_allow,         
            "M_allow_kgm": M_allow_kgm, 
            "K_defl": K_defl,
            "Raw_Sec": sec
        })

    if not data_list: return
    df = pd.DataFrame(data_list)
    names = df['Name']
    x = np.arange(len(names))

    # ==========================================
    # 📉 GRAPH 1: GOVERNING ZONES (GANTT STYLE)
    # ==========================================
    st.subheader("1️⃣ Governing Failure Mode: Moment Controlled Zone")
    st.caption("The bars represent the span range where the **Moment Capacity** is the limiting factor (Safe Zone).")
    
    fig1, ax1 = plt.subplots(figsize=(12, 4.5))
    ax1.grid(which='major', axis='x', linestyle='--', alpha=0.3)
    ax1.grid(which='major', axis='y', linestyle=':', alpha=0.3)
    
    # Logic: Bar starts at L_Start (Shear Limit) and has height of (L_End - L_Start)
    ax1.bar(x, df['L_End'] - df['L_Start'], bottom=df['L_Start'], 
            color='#E74C3C', alpha=0.75, edgecolor='#C0392B', linewidth=1, label='Moment Controlled Range')
    
    # Annotate Top Values
    for i, val in enumerate(df['L_End']):
        ax1.text(i, val + 0.1, f"{val:.2f}", ha='center', va='bottom', fontsize=7, color='#555')

    ax1.set_ylabel('Span Length (m)', fontweight='bold')
    ax1.set_xlabel('Section Size', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=90)
    ax1.set_xlim(-0.6, len(names)-0.4)
    ax1.legend(loc='upper left')
    
    st.pyplot(fig1)
    st.divider()

    # ==========================================
    # 📉 GRAPH 2: STRUCTURAL EFFICIENCY
    # ==========================================
    st.subheader("2️⃣ Structural Efficiency (Load/Weight Ratio)")
    
    fig2, ax2 = plt.subplots(figsize=(12, 4))
    # Load Bar
    ax2.bar(x, df['Safe W (kg/m)'], color='#3498DB', alpha=0.6, label='Design Load Capacity')
    ax2.set_ylabel('Safe Load W (kg/m)', color='#2980B9', fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='#2980B9')
    
    # Weight Line
    ax3 = ax2.twinx()
    ax3.plot(x, df['Weight (kg/m)'], color='#E67E22', marker='D', markersize=4, linestyle='-', linewidth=2, label='Steel Weight')
    ax3.set_ylabel('Self Weight (kg/m)', color='#D35400', fontweight='bold')
    ax3.tick_params(axis='y', labelcolor='#D35400')
    
    ax2.set_xticks(x)
    ax2.set_xticklabels(names, rotation=90)
    ax2.set_xlim(-0.6, len(names)-0.4)
    
    # Combined Legend
    lines, labels = ax2.get_legend_handles_labels()
    lines2, labels2 = ax3.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper right')
    
    st.pyplot(fig2)
    st.divider()

    # ==========================================
    # 🔬 DEEP DIVE: CRITICAL LIMIT ANALYSIS
    # ==========================================
    st.markdown("## 🔬 Deep Dive: Critical Limit Analysis")
    st.info("Analyze the interaction between Shear, Moment, and Deflection limits for a specific section.")

    if 'Section' not in df.columns or df.empty: return

    col_sel, col_empty = st.columns([1, 2])
    with col_sel:
        selected_name = st.selectbox("Select Section for Detailed Analysis:", df['Section'].unique())

    # --- Prepare Data for Deep Dive ---
    row = df[df['Section'] == selected_name].iloc[0]
    V_allow = row['V_allow']
    M_allow_kgm = row['M_allow_kgm']
    K_defl = row['K_defl']
    
    L_start = row['L_Start']
    L_end = row['L_End']

    # Span Generation for smooth curves
    max_span_plot = max(8, L_end * 1.4)
    spans = np.linspace(0.5, max_span_plot, 300)
    
    # Calculate Curves
    # 1. Shear Limit: w = 2V/L
    ws = (2 * V_allow) / spans
    # 2. Moment Limit: w = 8M/L^2
    wm = (8 * M_allow_kgm) / (spans**2)
    # 3. Deflection Limit: w = K/L^3
    wd = K_defl / (spans**3)
    
    # Envelope (Governing Capacity)
    w_safe_envelope = np.minimum(np.minimum(ws, wm), wd)

    # --- PLOTTING DEEP DIVE ---
    fig_d, ax_d = plt.subplots(figsize=(10, 6))
    
    # Background Grid
    ax_d.grid(True, which='both', linestyle='--', alpha=0.4)
    
    # Plot Limit Lines
    ax_d.plot(spans, ws, color='#9B59B6', linestyle=':', linewidth=1.5, alpha=0.6, label='Shear Limit (Failure)')
    ax_d.plot(spans, wd, color='#2ECC71', linestyle='-.', linewidth=1.5, alpha=0.6, label='Deflection Limit (Service)')
    ax_d.plot(spans, wm, color='#E74C3C', linestyle='--', linewidth=1.5, alpha=0.6, label='Moment Limit (Failure)')
    
    # Plot Governing Envelope
    ax_d.plot(spans, w_safe_envelope, color='#2C3E50', linewidth=3, label='Safe Working Load (Envelope)')
    
    # Fill Moment Zone
    if L_end > L_start:
        idx_start = np.searchsorted(spans, L_start)
        idx_end = np.searchsorted(spans, L_end)
        ax_d.fill_between(spans[idx_start:idx_end], 0, w_safe_envelope[idx_start:idx_end], 
                          color='#E74C3C', alpha=0.15, label='Moment Controlled Zone')

    # Add Vertical Transition Lines & Text
    # Transition 1: Shear -> Moment
    if 0.5 < L_start < max_span_plot:
        ax_d.axvline(x=L_start, color='#E67E22', linestyle='-', linewidth=1)
        ax_d.text(L_start, max(w_safe_envelope)*0.8, f" Start: {L_start:.2f} m", 
                  rotation=90, va='bottom', ha='right', color='#D35400', fontweight='bold')

    # Transition 2: Moment -> Deflection
    if 0.5 < L_end < max_span_plot:
        ax_d.axvline(x=L_end, color='#27AE60', linestyle='-', linewidth=1)
        ax_d.text(L_end, max(w_safe_envelope)*0.6, f" End: {L_end:.2f} m", 
                  rotation=90, va='bottom', ha='left', color='#219150', fontweight='bold')

    # Formatting
    ax_d.set_ylim(0, max(w_safe_envelope)*1.2 if max(w_safe_envelope)>0 else 1000)
    ax_d.set_xlim(0.5, max_span_plot)
    ax_d.set_title(f"Governing Capacity Analysis: {selected_name}", fontweight='bold', fontsize=12)
    ax_d.set_xlabel("Span Length (m)", fontweight='bold')
    ax_d.set_ylabel("Allowable Uniform Load (kg/m)", fontweight='bold')
    
    # Custom Legend
    ax_d.legend(loc='upper right', frameon=True, shadow=True)
    
    st.pyplot(fig_d)
    
    # Zone Summary
    col1, col2, col3 = st.columns(3)
    with col1: 
        st.markdown(f"🟣 **Shear Zone:** <br>0.00 - {L_start:.2f} m", unsafe_allow_html=True)
    with col2: 
        st.markdown(f"🔴 **Moment Zone (Safe):** <br><span style='font-size:1.2em; color:#C0392B'><b>{L_start:.2f} - {L_end:.2f} m</b></span>", unsafe_allow_html=True)
    with col3: 
        st.markdown(f"🟢 **Deflection Zone:** <br>> {L_end:.2f} m", unsafe_allow_html=True)

    st.divider()

    # --- FINAL SPECIFICATION TABLE ---
    st.subheader("📋 Specification Table: Moment Controlled Ranges")
    
    # Select & Rename Columns for Presentation
    table_df = df[["Section", "Weight (kg/m)", "L_Start", "L_End", "Moment Zone Range"]]
    
    st.dataframe(
        table_df,
        use_container_width=True,
        column_config={
            "Section": st.column_config.TextColumn("Section Size", width="small", help="JIS Standard H-Beam"),
            "Weight (kg/m)": st.column_config.NumberColumn("Weight", format="%.1f kg/m"),
            "L_Start": st.column_config.NumberColumn("Zone Start", format="%.2f m", help="Transition from Shear to Moment"),
            "L_End": st.column_config.NumberColumn("Zone End", format="%.2f m", help="Transition from Moment to Deflection"),
            "Moment Zone Range": st.column_config.TextColumn(
                "✅ Moment Controlled Zone", 
                width="medium",
                help="The effective span range where Moment Capacity governs design."
            ),
        },
        height=500,
        hide_index=True
    )

# report_analytics.py
# Version: 15.0 (Safe Span = Moment Zone Range "Start - End")
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

try:
    from report_generator import get_standard_sections, calculate_connection, calculate_full_properties
except ImportError:
    st.error("⚠️ Error: Missing report_generator.py")
    st.stop()

def render_analytics_section(load_pct, bolt_dia, load_case, factor):
    """
    Dashboard V.15.0:
    - Safe Span is now a TEXT RANGE (e.g., "0.56 - 3.69").
    - Represents the 'Moment Zone' calculated from intersections.
    """
    st.markdown("## 📊 Structural Analysis Dashboard")
    
    all_sections = get_standard_sections()
    if not all_sections:
        st.warning("⚠️ No section data found.")
        return

    data_list = []
    E_ksc = 2040000 
    
    for sec in all_sections:
        full_props = calculate_full_properties(sec) 
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        
        # --- 1. Get Capacities ---
        try:
            V_n = r.get('Vn_beam', 0)
            V_allow = V_n / factor if factor else V_n
        except: V_allow = 0
            
        try:
            M_n_kgcm = sec['Fy'] * full_props['Zx (cm3)']
            M_allow_kgm = (M_n_kgcm / factor) / 100 if factor else 0
        except: M_allow_kgm = 0

        # --- 2. Calculate Moment Zone Range (Start - End) ---
        Ix = full_props['Ix (cm4)']
        K_defl = (384 * E_ksc * Ix) / 18000000 
        
        # A. Start of Moment Zone (Intersection: Shear vs Moment)
        # 2V/L = 8M/L^2  => L = 4M/V
        L_start = (4 * M_allow_kgm) / V_allow if V_allow > 0 else 0
        
        # B. End of Moment Zone (Intersection: Moment vs Deflection)
        # 8M/L^2 = K/L^3 => L = K/8M
        L_end = K_defl / (8 * M_allow_kgm) if M_allow_kgm > 0 else 0
        
        # Format as String Range
        moment_zone_str = f"{L_start:.2f} - {L_end:.2f}"

        # --- 3. Calculate Safe W (at Middle of Zone for Reference) ---
        # Just for graphing purpose, we pick a representative W
        L_mid = (L_start + L_end) / 2
        safe_w = (8 * M_allow_kgm) / (L_mid**2) if L_mid > 0 else 0

        # --- 4. Append Data ---
        data_list.append({
            "Name": sec['name'].replace("H-", ""), 
            "Section": sec['name'],
            "Weight (kg/m)": full_props['Area (cm2)']*0.785,
            "Safe W (kg/m)": safe_w,
            # Limits (Numeric for Graphs)
            "L_Shear_End": L_start, 
            "L_Moment_End": L_end,
            # ✅ Table Requirement: Safe Span = Moment Zone Range
            "Safe Span Range": moment_zone_str, 
            # Deep Dive Data
            "V_allow": V_allow,         
            "M_allow_kgm": M_allow_kgm, 
            "Raw_Sec": sec,
            "Full_Props": full_props
        })

    if not data_list: return
    df = pd.DataFrame(data_list)
    names = df['Name']
    x = np.arange(len(names))

    # ==========================================
    # 📉 GRAPH 1: OPTIMIZATION OVERVIEW (Zone Bar)
    # ==========================================
    st.subheader("1️⃣ Optimization Overview (Moment Zone)")
    fig1, ax1 = plt.subplots(figsize=(12, 4))
    ax1.grid(which='major', axis='y', linestyle='--', alpha=0.3)
    
    # Plot bars covering the Moment Zone
    # Bottom = L_Shear_End, Top = L_Moment_End
    ax1.bar(x, df['L_Moment_End'] - df['L_Shear_End'], bottom=df['L_Shear_End'], 
            color='#E74C3C', alpha=0.6, label='Moment Controlled Zone')
    
    ax1.set_ylabel('Span (m)'); ax1.set_xticks(x); ax1.set_xticklabels(names, rotation=90)
    ax1.set_xlim(-0.5, len(names)-0.5)
    ax1.legend(loc='upper left', fontsize=8)
    st.pyplot(fig1)
    st.caption("Bar represents the span range where Moment is the governing factor.")
    st.divider()

    # ==========================================
    # 📉 GRAPH 2: EFFICIENCY
    # ==========================================
    st.subheader("2️⃣ Efficiency (Ref W vs Weight)")
    fig2, ax3 = plt.subplots(figsize=(12, 4))
    ax3.bar(x, df['Safe W (kg/m)'], color='#3498DB', alpha=0.7, label='Avg Safe W')
    ax4 = ax3.twinx()
    ax4.plot(x, df['Weight (kg/m)'], color='#E67E22', marker='o', markersize=4, label='Weight')
    ax3.set_ylabel('Safe W (kg/m)'); ax4.set_ylabel('Weight (kg/m)')
    ax3.set_xticks(x); ax3.set_xticklabels(names, rotation=90)
    ax3.set_xlim(-0.5, len(names)-0.5)
    st.pyplot(fig2)
    st.divider()

    # ==========================================
    # 🔬 DEEP DIVE: CRITICAL LIMIT ZONES
    # ==========================================
    st.markdown("## 🔬 Deep Dive: Critical Limit Zones")
    if 'Section' not in df.columns or df.empty: return

    col_sel, col_info = st.columns([1, 2])
    with col_sel:
        selected_name = st.selectbox("Select Section:", df['Section'].unique())

    selected_row = df[df['Section'] == selected_name].iloc[0]
    V_allow = selected_row['V_allow']
    M_allow_kgm = selected_row['M_allow_kgm']
    Ix = selected_row['Full_Props']['Ix (cm4)']
    E = 2040000; K_defl = (384 * E * Ix) / 18000000 

    # Retrieve Values
    L_shear_moment = selected_row['L_Shear_End']
    L_moment_defl = selected_row['L_Moment_End']

    max_span_plot = max(10, L_moment_defl * 1.5)
    if max_span_plot > 30: max_span_plot = 30
    if max_span_plot <= 1: max_span_plot = 10
    
    spans = np.linspace(0.5, max_span_plot, 200)
    ws = (2 * V_allow) / spans
    wm = (8 * M_allow_kgm) / (spans**2)
    wd = K_defl / (spans**3)
    w_safe_curve = np.minimum(np.minimum(ws, wm), wd)

    # --- PLOTTING ---
    fig_d, ax_d = plt.subplots(figsize=(10, 6))
    
    ax_d.plot(spans, ws, color='#9B59B6', linestyle=':', label='Shear Limit')
    ax_d.plot(spans, wm, color='#E74C3C', linestyle='--', label='Moment Limit')
    ax_d.plot(spans, wd, color='#2ECC71', linestyle='-.', label='Deflection Limit')
    ax_d.plot(spans, w_safe_curve, color='#34495E', linewidth=3, label='Governing Capacity')

    # Vertical Lines
    if 0.5 < L_shear_moment < max_span_plot:
        ax_d.axvline(x=L_shear_moment, color='#E67E22', linestyle='--', linewidth=1.5)
        ax_d.text(L_shear_moment, max(w_safe_curve)*0.9, f" Start: {L_shear_moment:.2f} m", 
                  rotation=90, verticalalignment='top', color='white', fontweight='bold',
                  bbox=dict(facecolor='#E67E22', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2'))

    if 0.5 < L_moment_defl < max_span_plot:
        ax_d.axvline(x=L_moment_defl, color='#27AE60', linestyle='--', linewidth=1.5)
        ax_d.text(L_moment_defl, max(w_safe_curve)*0.7, f" End: {L_moment_defl:.2f} m", 
                  rotation=90, verticalalignment='top', color='white', fontweight='bold',
                  bbox=dict(facecolor='#27AE60', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2'))

    ax_d.set_ylim(0, max(w_safe_curve)*1.3 if max(w_safe_curve)>0 else 1000)
    ax_d.set_xlim(0.5, max_span_plot)
    ax_d.set_title(f"Critical Span Limits: {selected_name}", fontweight='bold')
    ax_d.set_xlabel("Span Length (m)", fontweight='bold')
    ax_d.set_ylabel("Safe Load (kg/m)", fontweight='bold')
    ax_d.grid(True, alpha=0.3)
    ax_d.legend(loc='upper right')
    st.pyplot(fig_d)
    
    st.markdown(f"### 🔴 Moment Zone: **{L_shear_moment:.2f} - {L_moment_defl:.2f} m**")
    st.divider()

    # --- TABLE (UPDATED: SAFE SPAN RANGE) ---
    st.subheader("📋 Specification Table")
    st.dataframe(
        df[["Section", "Weight (kg/m)", "L_Shear_End", "L_Moment_End", "Safe Span Range"]],
        use_container_width=True,
        column_config={
            "Section": st.column_config.TextColumn("Section", width="small"),
            "Weight (kg/m)": st.column_config.NumberColumn("Weight", format="%.1f"),
            "L_Shear_End": st.column_config.NumberColumn("Start(m)", format="%.2f", help="Shear ends here"),
            "L_Moment_End": st.column_config.NumberColumn("End(m)", format="%.2f", help="Deflection starts here"),
            "Safe Span Range": st.column_config.TextColumn("✅ Moment Zone (m)", width="medium"),
        },
        height=400,
        hide_index=True
    )

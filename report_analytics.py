# report_analytics.py
# Version: 13.0 (Logic Update: Safe Span is governed by Moment Limit)
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
    Dashboard V.13.0:
    - Safe Span in Table is now EXPLICITLY the Moment Limit.
    """
    st.markdown("## 📊 Structural Analysis Dashboard")
    
    # --- 1. Main Data Loop ---
    all_sections = get_standard_sections()
    if not all_sections:
        st.warning("⚠️ No section data found.")
        return

    data_list = []
    E_ksc = 2040000 
    
    for sec in all_sections:
        full_props = calculate_full_properties(sec) 
        # Calculate Limits (L_crit_moment comes from report_generator logic)
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        
        # --- Allowable Capacities (For Deep Dive) ---
        try:
            V_n = r.get('Vn_beam', 0)
            V_allow = V_n / factor if factor else V_n
        except: V_allow = 0
        try:
            M_n_kgcm = sec['Fy'] * full_props['Zx (cm3)']
            M_allow_kgm = (M_n_kgcm / factor) / 100 if factor else 0
        except: M_allow_kgm = 0

        # --- Calculate Safe W (Based on Moment Limit Span) ---
        # User defined: Safe Span = Moment Limit
        L_moment_limit = r.get('L_crit_moment', 0)
        
        safe_w = 0
        if L_moment_limit > 0:
            # Calculate W based on Moment Capacity at this length
            # w = 8 * M / L^2
            safe_w = (8 * M_allow_kgm) / (L_moment_limit**2)

        # --- Theoretical Limits ---
        # L_Shear Limit
        try: l_shear = (2 * V_allow) / safe_w if safe_w > 0 else 0
        except: l_shear = 0
        
        # L_Deflection Limit
        try:
             w_cm = safe_w/100
             l_cube = (384 * E_ksc * full_props['Ix (cm4)']) / (1800 * w_cm) if w_cm > 0 else 0
             l_defl = (l_cube**(1/3)) / 100 
        except: l_defl = 0
        
        data_list.append({
            "Name": sec['name'].replace("H-", ""), 
            "Section": sec['name'],
            "Weight (kg/m)": full_props['Area (cm2)']*0.785,
            "Safe W (kg/m)": safe_w,
            # Limits
            "L_Shear": l_shear, 
            "L_Moment": L_moment_limit, # ใช้ค่าจริงจาก Solver
            "L_Defl": l_defl,
            "Safe Span": L_moment_limit, # ✅ Set Safe Span = Moment Limit ตามที่ขอ
            # Deep Dive Data
            "V_allow": V_allow,         
            "M_allow_kgm": M_allow_kgm, 
            "Raw_Sec": sec,
            "Full_Props": full_props,
            "Moment Limit": L_moment_limit, # For Graph 1
            "Deflection Limit": r.get('L_crit_defl', 0) # For Graph 1
        })

    if not data_list: return
    df = pd.DataFrame(data_list)
    names = df['Name']
    x = np.arange(len(names))

    # ==========================================
    # 📉 GRAPH 1: OPTIMIZATION OVERVIEW
    # ==========================================
    st.subheader("1️⃣ Optimization Overview")
    fig1, ax1 = plt.subplots(figsize=(12, 4))
    ax1.grid(which='major', axis='y', linestyle='--', alpha=0.3)
    ax1.plot(x, df['Moment Limit'], color='#E74C3C', linestyle='-', linewidth=2, label='Safe Span (Moment Limit)')
    ax1.plot(x, df['Deflection Limit'], color='#2980B9', linestyle='--', label='Deflection Check')
    
    ax1.fill_between(x, 0, df['Moment Limit'], color='#E74C3C', alpha=0.1, label='Moment Capacity Zone')
    
    ax1.set_ylabel('Span (m)'); ax1.set_xticks(x); ax1.set_xticklabels(names, rotation=90)
    ax1.set_xlim(-0.5, len(names)-0.5)
    ax1.legend(loc='upper left', fontsize=8)
    st.pyplot(fig1)
    st.divider()

    # ==========================================
    # 📉 GRAPH 2: EFFICIENCY
    # ==========================================
    st.subheader("2️⃣ Efficiency (Load vs Weight)")
    fig2, ax3 = plt.subplots(figsize=(12, 4))
    ax3.bar(x, df['Safe W (kg/m)'], color='#3498DB', alpha=0.7, label='Safe W (at Moment Limit)')
    ax4 = ax3.twinx()
    ax4.plot(x, df['Weight (kg/m)'], color='#E67E22', marker='o', markersize=4, label='Weight')
    ax3.set_ylabel('Safe W (kg/m)'); ax4.set_ylabel('Weight (kg/m)')
    ax3.set_xticks(x); ax3.set_xticklabels(names, rotation=90)
    ax3.set_xlim(-0.5, len(names)-0.5)
    st.pyplot(fig2)
    st.divider()

    # ==========================================
    # 🔬 DEEP DIVE: INTERSECTION ANALYSIS
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

    # Calc Intersections
    L_shear_moment = (4 * M_allow_kgm) / V_allow if V_allow > 0 else 0
    L_moment_defl = K_defl / (8 * M_allow_kgm) if M_allow_kgm > 0 else 0

    max_span_plot = max(10, L_moment_defl * 1.5)
    if max_span_plot > 30: max_span_plot = 30
    if max_span_plot <= 1: max_span_plot = 10
    
    spans = np.linspace(0.5, max_span_plot, 200)
    ws = (2 * V_allow) / spans
    wm = (8 * M_allow_kgm) / (spans**2)
    wd = K_defl / (spans**3)
    w_safe_curve = np.minimum(np.minimum(ws, wm), wd)

    fig_d, ax_d = plt.subplots(figsize=(10, 6))
    ax_d.plot(spans, ws, color='#9B59B6', linestyle=':', alpha=0.5, label='Shear Limit')
    ax_d.plot(spans, wm, color='#E74C3C', linestyle='--', alpha=0.5, label='Moment Limit')
    ax_d.plot(spans, wd, color='#2ECC71', linestyle='-.', alpha=0.5, label='Deflection Limit')
    ax_d.plot(spans, w_safe_curve, color='#34495E', linewidth=3, label='Governing Capacity')

    # Vertical Lines
    if 0.5 < L_shear_moment < max_span_plot:
        ax_d.axvline(x=L_shear_moment, color='#E67E22', linestyle='--', linewidth=1.5)
        ax_d.text(L_shear_moment, max(w_safe_curve)*0.9, f" Shear Ends\n {L_shear_moment:.2f} m", 
                  rotation=90, verticalalignment='top', color='white', fontweight='bold', bbox=dict(facecolor='#E67E22', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2'))

    if 0.5 < L_moment_defl < max_span_plot:
        ax_d.axvline(x=L_moment_defl, color='#27AE60', linestyle='--', linewidth=1.5)
        ax_d.text(L_moment_defl, max(w_safe_curve)*0.7, f" Deflection Starts\n {L_moment_defl:.2f} m", 
                  rotation=90, verticalalignment='top', color='white', fontweight='bold', bbox=dict(facecolor='#27AE60', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2'))

    ax_d.set_ylim(0, max(w_safe_curve)*1.3 if max(w_safe_curve)>0 else 1000)
    ax_d.set_xlim(0.5, max_span_plot)
    ax_d.set_title(f"Critical Span Limits: {selected_name}", fontweight='bold')
    ax_d.grid(True, alpha=0.3)
    ax_d.legend(loc='upper right')
    st.pyplot(fig_d)
    
    col1, col2, col3 = st.columns(3)
    with col1: st.caption(f"🟣 **Shear:** 0.00 - {L_shear_moment:.2f} m")
    with col2: st.caption(f"🔴 **Moment:** {L_shear_moment:.2f} - {L_moment_defl:.2f} m")
    with col3: st.caption(f"🟢 **Deflection:** > {L_moment_defl:.2f} m")

    st.divider()

    # --- TABLE (UPDATED) ---
    st.subheader("📋 Specification Table (Moment Controlled)")
    st.dataframe(
        df[["Section", "Safe W (kg/m)", "Weight (kg/m)", "L_Shear", "L_Defl", "Safe Span"]],
        use_container_width=True,
        column_config={
            "Section": st.column_config.TextColumn("Section", width="small"),
            "Safe W (kg/m)": st.column_config.NumberColumn("Load W", format="%.0f"),
            "Weight (kg/m)": st.column_config.NumberColumn("Weight", format="%.1f"),
            "L_Shear": st.column_config.NumberColumn("Lim(Shr)", format="%.2f m"),
            "L_Defl": st.column_config.NumberColumn("Lim(Def)", format="%.2f m"),
            "Safe Span": st.column_config.NumberColumn("✅ Span(Mom)", format="%.2f m", help="Max Span based on Moment Capacity"),
        },
        height=400,
        hide_index=True
    )

# report_analytics.py
# Version: 11.1 (Fix KeyError & Safety Factor Sync)
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
    Update V.11.1:
    - Fix KeyError by ensuring all keys exist in dictionary
    - Added empty dataframe check
    - Synchronized Safety Factors
    """
    st.markdown("## 📊 Structural Analysis Dashboard")
    
    # --- 1. Main Data Loop ---
    all_sections = get_standard_sections()
    
    if not all_sections:
        st.warning("⚠️ No section data found.")
        return

    data_list = []
    
    # Constants
    E_ksc = 2040000 
    
    for sec in all_sections:
        full_props = calculate_full_properties(sec) 
        
        # Calculate Connection (Nominal)
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        
        # --- RE-CALCULATE CAPACITIES (ALLOWABLE / DESIGN) ---
        # 1. Shear Capacity (Allowable)
        try:
            V_n = r.get('Vn_beam', 0)
            V_allow = V_n / factor if factor else V_n
        except: V_allow = 0
            
        # 2. Moment Capacity (Allowable)
        try:
            M_n_kgcm = sec['Fy'] * full_props['Zx (cm3)']
            M_allow_kgm = (M_n_kgcm / factor) / 100 if factor else 0
        except: M_allow_kgm = 0

        # --- Calculate Safe W for Table ---
        L_m = r.get('L_safe', 0)
        safe_w = 0
        w_shear, w_moment, w_defl = 0, 0, 0
        
        if L_m > 0:
            # Shear Control: w = 2 * V_allow / L
            w_shear = (2 * V_allow) / L_m
            
            # Moment Control: w = 8 * M_allow / L^2
            w_moment = (8 * M_allow_kgm) / (L_m**2)
            
            # Deflection Control
            L_cm = L_m * 100
            delta_allow = L_cm / 360
            w_defl_kg_cm = (384 * E_ksc * full_props['Ix (cm4)'] * delta_allow) / (5 * (L_cm**4))
            w_defl = w_defl_kg_cm * 100
            
            safe_w = min(w_shear, w_moment, w_defl)

        # --- Reverse Limits (Theoretical Spans) ---
        try: l_shear = (2 * V_allow) / safe_w if safe_w > 0 else 0
        except: l_shear = 0
        try: l_moment = math.sqrt((8 * M_allow_kgm) / safe_w) if safe_w > 0 else 0
        except: l_moment = 0
        try:
             w_cm = safe_w/100
             l_cube = (384 * E_ksc * full_props['Ix (cm4)']) / (1800 * w_cm) if w_cm > 0 else 0
             l_defl = (l_cube**(1/3)) / 100 
        except: l_defl = 0

        # --- APPEND TO LIST (KEY FIX IS HERE) ---
        data_list.append({
            "Name": sec['name'].replace("H-", ""), 
            "Section": sec['name'],
            "Moment Limit": r.get('L_crit_moment', 0),
            "Deflection Limit": r.get('L_crit_defl', 0),
            "Shear Cap": V_allow, 
            "Max Span": L_m,
            "Weight (kg/m)": full_props['Area (cm2)']*0.785,
            "Safe W (kg/m)": safe_w,
            # Critical Keys for Graphs
            "L_Shear": l_shear, 
            "L_Moment": l_moment, 
            "L_Defl": l_defl,
            # Store for Deep Dive
            "V_allow": V_allow,         
            "M_allow_kgm": M_allow_kgm, 
            "Raw_Sec": sec,
            "Full_Props": full_props
        })

    if not data_list:
        st.warning("⚠️ No valid calculation results.")
        return

    df = pd.DataFrame(data_list)
    
    # Verify Columns Exist before Plotting
    required_cols = ['L_Shear', 'L_Moment', 'L_Defl', 'Moment Limit', 'Deflection Limit']
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0.0

    names = df['Name']
    x = np.arange(len(names))

    # ==========================================
    # 📉 GRAPH 1: OPTIMIZATION OVERVIEW
    # ==========================================
    st.subheader("1️⃣ Optimization Overview")
    fig1, ax1 = plt.subplots(figsize=(12, 4))
    ax1.grid(which='major', axis='y', linestyle='--', alpha=0.3)
    ax1.plot(x, df['Moment Limit'], color='#E74C3C', linestyle='--', label='Limit: Moment')
    ax1.plot(x, df['Deflection Limit'], color='#2980B9', linestyle='-', label='Limit: Deflection')
    upper = np.minimum(df['Moment Limit'], df['Deflection Limit'])
    ax1.fill_between(x, 0, upper, color='#2ECC71', alpha=0.2, label='Safe Zone')
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
    ax3.bar(x, df['Safe W (kg/m)'], color='#3498DB', alpha=0.7, label='Safe W')
    ax4 = ax3.twinx()
    ax4.plot(x, df['Weight (kg/m)'], color='#E67E22', marker='o', markersize=4, label='Weight')
    ax3.set_ylabel('Safe W (kg/m)'); ax4.set_ylabel('Weight (kg/m)')
    ax3.set_xticks(x); ax3.set_xticklabels(names, rotation=90)
    ax3.set_xlim(-0.5, len(names)-0.5)
    st.pyplot(fig2)
    st.divider()

    # ==========================================
    # 📉 GRAPH 3: THEORETICAL LIMITS (Fix KeyError Here)
    # ==========================================
    st.subheader("3️⃣ Theoretical Limits (3 Lines)")
    fig3, ax5 = plt.subplots(figsize=(12, 4))
    ax5.grid(True, linestyle='--', alpha=0.3)
    
    # Safe plotting
    ax5.plot(x, df['L_Shear'], color='#9B59B6', linestyle=':', label='Shear')
    ax5.plot(x, df['L_Moment'], color='#E74C3C', linestyle='-', label='Moment')
    ax5.plot(x, df['L_Defl'], color='#2ECC71', linestyle='-', label='Deflection')
    
    ax5.set_ylabel('Span (m)'); ax5.set_xticks(x); ax5.set_xticklabels(names, rotation=90)
    ax5.set_xlim(-0.5, len(names)-0.5)
    
    # Auto Scale Y
    max_val = max(df['L_Moment'].max(), df['L_Defl'].max()) if not df.empty else 10
    ax5.set_ylim(0, max_val * 1.5)
    ax5.legend(loc='upper left', fontsize=8)
    st.pyplot(fig3)
    st.divider()

    # ==========================================
    # 🔬 DEEP DIVE: INTERSECTION ANALYSIS
    # ==========================================
    st.markdown("## 🔬 Deep Dive: Critical Limit Zones")
    
    # Safety Check for Dropdown
    if 'Section' not in df.columns or df.empty:
        st.error("No section data available for Deep Dive.")
        return

    col_sel, col_info = st.columns([1, 2])
    with col_sel:
        selected_name = st.selectbox("Select Section:", df['Section'].unique())

    # Get Data
    selected_row = df[df['Section'] == selected_name].iloc[0]
    
    V_allow = selected_row['V_allow']
    M_allow_kgm = selected_row['M_allow_kgm']
    Ix = selected_row['Full_Props']['Ix (cm4)']
    E = 2040000

    # Constant K for Deflection
    K_defl = (384 * E * Ix) / 18000000 

    # --- CALCULATE INTERSECTIONS ---
    L_shear_moment = (4 * M_allow_kgm) / V_allow if V_allow > 0 else 0
    L_moment_defl = K_defl / (8 * M_allow_kgm) if M_allow_kgm > 0 else 0

    # Plot Range
    max_span_plot = max(10, L_moment_defl * 1.5)
    if max_span_plot > 30: max_span_plot = 30
    if max_span_plot <= 1: max_span_plot = 10 # Default fallback
    
    spans = np.linspace(0.5, max_span_plot, 200)
    
    ws = (2 * V_allow) / spans
    wm = (8 * M_allow_kgm) / (spans**2)
    wd = K_defl / (spans**3)
    
    w_safe_curve = np.minimum(np.minimum(ws, wm), wd)

    # --- PLOT ---
    fig_d, ax_d = plt.subplots(figsize=(10, 6))
    
    ax_d.plot(spans, ws, color='#9B59B6', linestyle=':', alpha=0.5, label='Shear Limit (Allowable)')
    ax_d.plot(spans, wm, color='#E74C3C', linestyle='--', alpha=0.5, label='Moment Limit (Allowable)')
    ax_d.plot(spans, wd, color='#2ECC71', linestyle='-.', alpha=0.5, label='Deflection Limit (L/360)')
    ax_d.plot(spans, w_safe_curve, color='#34495E', linewidth=3, label='Governing Capacity')

    # --- VERTICAL LINES ---
    # Shear -> Moment
    if 0.5 < L_shear_moment < max_span_plot:
        ax_d.axvline(x=L_shear_moment, color='#E67E22', linestyle='--', linewidth=1.5)
        ax_d.text(L_shear_moment, max(w_safe_curve)*0.9, f" Shear Ends\n {L_shear_moment:.2f} m", 
                  rotation=90, verticalalignment='top', color='white', fontweight='bold',
                  bbox=dict(facecolor='#E67E22', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2'))

    # Moment -> Deflection
    if 0.5 < L_moment_defl < max_span_plot:
        ax_d.axvline(x=L_moment_defl, color='#27AE60', linestyle='--', linewidth=1.5)
        ax_d.text(L_moment_defl, max(w_safe_curve)*0.7, f" Deflection Starts\n {L_moment_defl:.2f} m", 
                  rotation=90, verticalalignment='top', color='white', fontweight='bold',
                  bbox=dict(facecolor='#27AE60', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2'))

    # Styling
    ax_d.set_ylim(0, max(w_safe_curve)*1.3 if max(w_safe_curve) > 0 else 1000)
    ax_d.set_xlim(0.5, max_span_plot)
    ax_d.set_xlabel("Span Length (m)", fontweight='bold')
    ax_d.set_ylabel("Safe Load Capacity (kg/m)", fontweight='bold')
    ax_d.set_title(f"Critical Span Limits for {selected_name} (SF={factor})", fontweight='bold')
    ax_d.grid(True, which='both', alpha=0.3)
    ax_d.legend(loc='upper right')
    
    st.pyplot(fig_d)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"🟣 **Shear:** 0.00 - {L_shear_moment:.2f} m")
    with col2:
        st.caption(f"🔴 **Moment:** {L_shear_moment:.2f} - {L_moment_defl:.2f} m")
    with col3:
        st.caption(f"🟢 **Deflection:** > {L_moment_defl:.2f} m")

    st.divider()

    # --- TABLE ---
    st.subheader("📋 Specification Table")
    st.dataframe(
        df[["Section", "Safe W (kg/m)", "Weight (kg/m)", "L_Moment", "L_Defl", "Max Span"]],
        use_container_width=True,
        column_config={
            "Section": st.column_config.TextColumn("Section", width="small"),
            "Safe W (kg/m)": st.column_config.NumberColumn("Capacity W", format="%.0f"),
            "Weight (kg/m)": st.column_config.NumberColumn("Weight", format="%.1f"),
            "L_Moment": st.column_config.NumberColumn("Lim(Mom)", format="%.2f m"),
            "L_Defl": st.column_config.NumberColumn("Lim(Defl)", format="%.2f m"),
            "Max Span": st.column_config.NumberColumn("✅ Safe Span", format="%.2f m"),
        },
        height=400,
        hide_index=True
    )

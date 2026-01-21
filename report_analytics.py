# report_analytics.py
# Version: 10.0 (Fix: Deflection Unit Scale & Vertical Line Limits)
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
    st.markdown("## 📊 Structural Analysis Dashboard")
    
    # --- 1. Main Data Loop ---
    all_sections = get_standard_sections()
    data_list = []
    
    for sec in all_sections:
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        full_props = calculate_full_properties(sec) 
        
        # Calculate Safe W (Governing Load)
        L_m = r['L_safe']
        L_cm = L_m * 100
        safe_w = 0
        if L_m > 0:
            # Shear (w = 2V/L)
            w_shear = (2 * r['Vn_beam']) / L_m
            
            # Moment (w = 8M/L^2)
            phi_Mn_kgm = (0.90 * sec['Fy'] * full_props['Zx (cm3)']) / 100
            w_moment = (8 * phi_Mn_kgm) / (L_m**2)
            
            # Deflection (w from delta=L/360)
            E=2040000; Ix=full_props['Ix (cm4)']; delta=L_cm/360
            # Formula: w_kg_cm = 384EI delta / 5 L^4
            w_defl_kg_cm = (384 * E * Ix * delta) / (5 * (L_cm**4))
            w_defl = w_defl_kg_cm * 100 # Convert to kg/m
            
            safe_w = min(w_shear, w_moment, w_defl)

        # Reverse Calculate Limits (Span)
        try: l_shear = (2 * r['Vn_beam']) / safe_w if safe_w > 0 else 0
        except: l_shear = 0
        try: 
            phi_Mn_kgm = (0.90 * sec['Fy'] * full_props['Zx (cm3)']) / 100
            l_moment = math.sqrt((8 * phi_Mn_kgm) / safe_w) if safe_w > 0 else 0
        except: l_moment = 0
        try:
             E=2040000; Ix=full_props['Ix (cm4)']; w_cm = safe_w/100
             # L^3 = 384EI / 1800 w_cm
             l_cube = (384*E*Ix)/(1800*w_cm) if w_cm > 0 else 0
             l_defl = (l_cube**(1/3)) / 100 
        except: l_defl = 0

        data_list.append({
            "Name": sec['name'].replace("H-", ""), 
            "Section": sec['name'],
            "Moment Limit": r['L_crit_moment'],
            "Deflection Limit": r['L_crit_defl'],
            "Shear Cap": r['Vn_beam'],
            "Max Span": r['L_safe'],
            "Weight (kg/m)": full_props['Area (cm2)']*0.785,
            "Safe W (kg/m)": safe_w,
            "L_Shear": l_shear, "L_Moment": l_moment, "L_Defl": l_defl,
            "Raw_Sec": sec
        })

    df = pd.DataFrame(data_list)
    names = df['Name']
    x = np.arange(len(names))

    # ==========================================
    # 📉 GRAPH 1-3 (Overview)
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

    st.subheader("3️⃣ Theoretical Limits (3 Lines)")
    fig3, ax5 = plt.subplots(figsize=(12, 4))
    ax5.grid(True, linestyle='--', alpha=0.3)
    ax5.plot(x, df['L_Shear'], color='#9B59B6', linestyle=':', label='Shear')
    ax5.plot(x, df['L_Moment'], color='#E74C3C', linestyle='-', label='Moment')
    ax5.plot(x, df['L_Defl'], color='#2ECC71', linestyle='-', label='Deflection')
    ax5.set_ylabel('Span (m)'); ax5.set_xticks(x); ax5.set_xticklabels(names, rotation=90)
    ax5.set_xlim(-0.5, len(names)-0.5)
    # Clamp extreme shear values for readability
    max_y = max(df['L_Moment'].max(), df['L_Defl'].max()) * 1.5
    ax5.set_ylim(0, max_y)
    ax5.legend(loc='upper left', fontsize=8)
    st.pyplot(fig3)
    st.divider()

    # ==========================================
    # 🔬 DEEP DIVE: INTERSECTION ANALYSIS (FIXED)
    # ==========================================
    st.markdown("## 🔬 Deep Dive: Critical Limit Zones")
    col_sel, col_info = st.columns([1, 2])
    with col_sel:
        selected_name = st.selectbox("Select Section:", df['Section'].unique())

    # Get Data
    selected_row = df[df['Section'] == selected_name].iloc[0]
    sec_data = selected_row['Raw_Sec']
    full_props = calculate_full_properties(sec_data)
    
    # Constants
    Fy = sec_data['Fy']; h = sec_data['h']; tw = sec_data['tw']
    Zx = full_props['Zx (cm3)']; Ix = full_props['Ix (cm4)']
    E = 2040000
    
    Vn = 0.60 * Fy * h * tw 
    phiMn_kgm = (0.90 * Fy * Zx) / 100 

    # --- FIX K FACTOR ---
    # From L^3 = 384EI / 1800 w_cm  => w_kg_m = (384 EI * 100) / (1800 * 100^3 L^3)
    # Constant K where w = K / L^3 for L in meters
    # K = 384 * E * Ix / 18,000,000  (Previously was 180,000 -> Error 100x)
    K_defl = (384 * E * Ix) / 18000000 

    # --- CALCULATE INTERSECTIONS ---
    # 1. Shear vs Moment: 2Vn/L = 8Mn/L^2 -> L = 4Mn/Vn
    L_shear_moment = (4 * phiMn_kgm) / Vn
    
    # 2. Moment vs Deflection: 8Mn/L^2 = K_defl/L^3 -> L = K_defl / 8Mn
    L_moment_defl = K_defl / (8 * phiMn_kgm)

    # Plot Range logic
    max_span_plot = max(10, L_moment_defl * 1.5)
    if max_span_plot > 30: max_span_plot = 30 # Cap at 30m to prevent insane zoom out
    
    spans = np.linspace(0.5, max_span_plot, 200)
    
    ws = (2 * Vn) / spans
    wm = (8 * phiMn_kgm) / (spans**2)
    wd = K_defl / (spans**3)
    w_safe_curve = np.minimum(np.minimum(ws, wm), wd)

    # --- PLOT ---
    fig_d, ax_d = plt.subplots(figsize=(10, 6))
    
    # Curves
    ax_d.plot(spans, ws, color='#9B59B6', linestyle=':', alpha=0.5, label='Shear Limit')
    ax_d.plot(spans, wm, color='#E74C3C', linestyle='--', alpha=0.5, label='Moment Limit')
    ax_d.plot(spans, wd, color='#2ECC71', linestyle='-.', alpha=0.5, label='Deflection Limit')
    ax_d.plot(spans, w_safe_curve, color='#34495E', linewidth=3, label='Governing Capacity')

    # --- PLOT VERTICAL LINES ---
    # Shear -> Moment
    if 0.5 < L_shear_moment < max_span_plot:
        ax_d.axvline(x=L_shear_moment, color='#E67E22', linestyle='--', linewidth=1.5)
        # Add text with background
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
    ax_d.set_ylim(0, max(w_safe_curve)*1.3)
    ax_d.set_xlim(0.5, max_span_plot)
    ax_d.set_xlabel("Span Length (m)", fontweight='bold')
    ax_d.set_ylabel("Load Capacity (kg/m)", fontweight='bold')
    ax_d.set_title(f"Critical Span Limits for {selected_name}", fontweight='bold')
    ax_d.grid(True, which='both', alpha=0.3)
    ax_d.legend(loc='upper right')
    
    st.pyplot(fig_d)
    
    # Explanation Text
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"🟣 **Shear Control:** 0.00 - {L_shear_moment:.2f} m")
    with col2:
        st.caption(f"🔴 **Moment Control:** {L_shear_moment:.2f} - {L_moment_defl:.2f} m")
    with col3:
        st.caption(f"🟢 **Deflection Control:** > {L_moment_defl:.2f} m")

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

# report_analytics.py
# Version: 8.1 (Fix: Restore Graph 1 Full Details + All New Graphs)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

# Import Logic
try:
    from report_generator import get_standard_sections, calculate_connection, calculate_full_properties
except ImportError:
    st.error("⚠️ Error: Missing report_generator.py")
    st.stop()

def render_analytics_section(load_pct, bolt_dia, load_case, factor):
    """
    Dashboard V.8.1 Fixed:
    1. Graph 1: Optimization Gap (RESTORED Dual Axis: Span vs Shear)
    2. Graph 2: Efficiency (W vs Weight)
    3. Graph 3: 3-Lines Limits (Shear/Moment/Defl vs Span)
    """
    st.markdown("## 📊 Structural Analysis Dashboard")
    
    # --- 1. Data Processing ---
    all_sections = get_standard_sections()
    data_list = []
    
    for sec in all_sections:
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        full_props = calculate_full_properties(sec) 
        
        # Calculate Safe W (Governing Load)
        L_m = r['L_safe']
        L_cm = L_m * 100
        safe_w_load = 0
        
        w_shear_cap, w_moment_cap, w_defl_cap = 0, 0, 0
        
        if L_m > 0:
            # Shear
            w_shear_cap = (2 * r['Vn_beam']) / L_m
            # Moment
            phi_Mn_kgm = (0.90 * sec['Fy'] * full_props['Zx (cm3)']) / 100
            w_moment_cap = (8 * phi_Mn_kgm) / (L_m**2)
            # Deflection
            E_ksc = 2040000; Ix = full_props['Ix (cm4)']; delta_allow_cm = L_cm / 360
            w_defl_kg_cm = (384 * E_ksc * Ix * delta_allow_cm) / (5 * (L_cm**4))
            w_defl_cap = w_defl_kg_cm * 100
            
            safe_w_load = min(w_shear_cap, w_moment_cap, w_defl_cap)

        # Reverse Calculate Span Limits
        try: l_limit_shear = (2 * r['Vn_beam']) / safe_w_load if safe_w_load > 0 else 0
        except: l_limit_shear = 0

        try:
            phi_Mn_kgm = (0.90 * sec['Fy'] * full_props['Zx (cm3)']) / 100
            l_limit_moment = math.sqrt((8 * phi_Mn_kgm) / safe_w_load) if safe_w_load > 0 else 0
        except: l_limit_moment = 0

        try:
            E = 2040000; Ix = full_props['Ix (cm4)']; w_cm = safe_w_load / 100
            l_cube_cm = (384 * E * Ix) / (1800 * w_cm) if w_cm > 0 else 0
            l_limit_defl = (l_cube_cm**(1/3)) / 100 
        except: l_limit_defl = 0

        weight_kg_m = full_props['Area (cm2)'] * 0.785 
        
        data_list.append({
            "Name": sec['name'].replace("H-", ""), 
            "Section": sec['name'],
            "Moment Limit": r['L_crit_moment'],
            "Deflection Limit": r['L_crit_defl'],
            "Shear Cap": r['Vn_beam'],
            "Max Span": r['L_safe'],
            "Weight (kg/m)": weight_kg_m,     
            "Safe W (kg/m)": safe_w_load,
            "L_Shear": l_limit_shear,
            "L_Moment": l_limit_moment,
            "L_Defl": l_limit_defl
        })

    df = pd.DataFrame(data_list)
    names = df['Name']
    x = np.arange(len(names))

    # ==================================================
    # 📈 GRAPH 1: OPTIMIZATION OVERVIEW (Fixed Full Version)
    # ==================================================
    st.subheader("1️⃣ Optimization Overview (Span vs Shear)")
    
    # Scale Calculation for Aesthetics
    max_moment_defl = max(df['Moment Limit'].max(), df['Deflection Limit'].max())
    max_span_val = max_moment_defl * 1.10
    max_shear_val = df['Shear Cap'].max() * 1.10
    scale_factor = max_span_val / max_shear_val # Used to align visual fill

    fig1, ax1 = plt.subplots(figsize=(12, 5.5))
    ax1.grid(which='major', axis='y', linestyle='--', linewidth=0.5, alpha=0.3)
    
    # Plot Span Limits (Axis 1 - Left)
    ax1.plot(x, df['Moment Limit'], color='#E74C3C', linestyle='--', label='Moment Limit')
    ax1.plot(x, df['Deflection Limit'], color='#2980B9', linestyle='-', label='Deflection Limit')
    
    # Safe Zone Fill
    # Note: Shear visual is scaled just for the fill intersection
    shears_visual = df['Shear Cap'] * scale_factor
    upper_bound = np.minimum(df['Moment Limit'], df['Deflection Limit'])
    lower_bound = shears_visual
    # Fill only where Span Limits > Scaled Shear (Visual logic)
    ax1.fill_between(x, 0, upper_bound, color='#2ECC71', alpha=0.2, label='Safe Zone')

    ax1.set_ylabel('Span Range (m)', fontweight='bold', color='#333333')
    ax1.set_ylim(0, max_span_val)
    ax1.set_xlim(-0.5, len(names)-0.5)
    ax1.set_xticks(x); ax1.set_xticklabels(names, rotation=90, fontsize=9)
    
    # Plot Shear Capacity (Axis 2 - Right) <-- RESTORED
    ax2 = ax1.twinx()
    ax2.plot(x, df['Shear Cap'], color='#663399', linestyle=':', linewidth=2, label='Shear Capacity ($V_n$)')
    ax2.set_ylabel('Shear Capacity (kg)', fontweight='bold', color='#663399')
    ax2.set_ylim(0, max_shear_val)

    # Combine Legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=9)
    
    st.pyplot(fig1)
    
    st.divider()

    # ==================================================
    # ⚖️ GRAPH 2: EFFICIENCY (W vs Weight)
    # ==================================================
    st.subheader("2️⃣ Load Efficiency (Capacity $W$ vs Weight)")
    st.caption("ความคุ้มค่า: กราฟแท่ง (W) ยิ่งสูงยิ่งดี / กราฟเส้น (นน.) ยิ่งต่ำยิ่งดี")

    fig2, ax3 = plt.subplots(figsize=(12, 5))
    ax3.grid(which='major', axis='y', linestyle='--', linewidth=0.5, color='gray', alpha=0.3)
    
    # Bar: Safe Load W
    ax3.bar(x, df['Safe W (kg/m)'], color='#3498DB', alpha=0.7, label='Safe Uniform Load W')
    ax3.set_ylabel('Safe W (kg/m)', fontweight='bold', color='#2980B9')
    
    # Line: Weight
    ax4 = ax3.twinx()
    ax4.plot(x, df['Weight (kg/m)'], color='#E67E22', marker='o', markersize=4, linewidth=2, label='Steel Weight')
    ax4.set_ylabel('Weight (kg/m)', fontweight='bold', color='#D35400')
    
    ax3.set_xticks(x); ax3.set_xticklabels(names, rotation=90, fontsize=8)
    ax3.set_xlim(-0.5, len(names)-0.5)
    
    # Limits
    ax3.set_ylim(0, df['Safe W (kg/m)'].max() * 1.25)
    ax4.set_ylim(0, df['Weight (kg/m)'].max() * 1.5) 
    
    # Legend
    lines3, labels3 = ax3.get_legend_handles_labels()
    lines4, labels4 = ax4.get_legend_handles_labels()
    ax3.legend(lines3 + lines4, labels3 + labels4, loc='upper left', fontsize=8)
    
    st.pyplot(fig2)

    st.divider()

    # ==================================================
    # 📉 GRAPH 3: THEORETICAL LIMITS (3 Lines)
    # ==================================================
    st.subheader("3️⃣ Theoretical Limits (Shear/Moment/Deflection)")
    st.caption("เจาะลึก: เปรียบเทียบขีดจำกัดของแต่ละแรง (แปลงเป็นระยะ Span) เส้นต่ำสุดคือ Governing")

    fig3, ax5 = plt.subplots(figsize=(12, 6))
    ax5.grid(which='major', axis='y', linestyle='--', linewidth=0.5, color='gray', alpha=0.3)

    # Plot 3 Lines
    ax5.plot(x, df['L_Shear'], color='#9B59B6', linestyle=':', linewidth=1.5, label='Limit: Shear')
    ax5.plot(x, df['L_Moment'], color='#E74C3C', linestyle='-', marker='o', markersize=3, linewidth=2, label='Limit: Moment')
    ax5.plot(x, df['L_Defl'], color='#2ECC71', linestyle='-', marker='s', markersize=3, linewidth=2, label='Limit: Deflection')

    ax5.set_ylabel('Max Theoretical Span (m)', fontweight='bold', color='#333333')
    ax5.set_xticks(x); ax5.set_xticklabels(names, rotation=90, fontsize=8)
    ax5.set_xlim(-0.5, len(names)-0.5)

    # Auto Y-Limit
    max_reasonable = max(df['L_Moment'].max(), df['L_Defl'].max()) * 1.4
    ax5.set_ylim(0, max_reasonable)
    
    # Add Weight Reference (Gray dashed)
    ax6 = ax5.twinx()
    ax6.plot(x, df['Weight (kg/m)'], color='gray', linestyle='--', alpha=0.4, linewidth=1, label='Weight (Ref)')
    ax6.set_ylabel('Weight Ref (kg/m)', color='gray', fontsize=8)
    ax6.set_ylim(0, df['Weight (kg/m)'].max() * 2)

    # Legend
    lines5, labels5 = ax5.get_legend_handles_labels()
    lines6, labels6 = ax6.get_legend_handles_labels()
    ax5.legend(lines5 + lines6, labels5 + labels6, loc='upper left', fontsize=8, ncol=2)

    st.pyplot(fig3)
    
    st.divider()

    # --- Table ---
    st.subheader("📋 Summary Table")
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

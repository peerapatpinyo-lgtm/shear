# report_analytics.py
# Version: 7.0 (Dual Graphs: Optimization Gap + Efficiency Load W)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Import Logic
try:
    from report_generator import get_standard_sections, calculate_connection
except ImportError:
    st.error("⚠️ Error: Missing report_generator.py")
    st.stop()

def render_analytics_section(load_pct, bolt_dia, load_case, factor):
    """
    Dashboard Updated:
    1. Graph 1: Optimization Gap (Span vs Shear)
    2. Graph 2: Load Efficiency (Safe Load w vs Steel Weight) - NEW! 🚀
    """
    st.markdown("## 📊 Structural Analysis Dashboard")
    
    # --- 1. Data Processing ---
    all_sections = get_standard_sections()
    data_list = []
    
    for sec in all_sections:
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        actual_cap = r['Bolt Qty'] * r['phiRn_bolt']
        util = (r['V_target'] / actual_cap) * 100 if actual_cap > 0 else 0
        
        # Calculate Weight of Steel (kg/m) roughly: Area * 7850 kg/m3
        # Area (cm2) approx = (2*b*tf + (h-2*tf)*tw) / 100
        h, b, tw, tf = sec['h'], sec['b'], sec['tw'], sec['tf']
        area_cm2 = (2 * b * tf + (h - 2*tf) * tw) / 100
        weight_kg_m = area_cm2 * 0.785 # Density of steel
        
        # Calculate Safe Uniform Load (w) at Safe Span (kg/m)
        # Based on V_target (Load input) distributed over the Safe Span
        # w = 2 * V / L (Simplified for estimation)
        safe_span_m = r['L_safe']
        safe_w_load = (r['V_target'] * 2) / safe_span_m if safe_span_m > 0 else 0
        
        data_list.append({
            "Name": sec['name'].replace("H-", ""), 
            "Section": sec['name'], 
            "Moment Limit": r['L_crit_moment'],
            "Deflection Limit": r['L_crit_defl'],
            "Shear Cap": r['Vn_beam'],
            "Max Span": r['L_safe'],
            "Bolts": r['Bolt Qty'],
            "Load (kg)": r['V_target'],
            "Util": util,
            "Weight (kg/m)": weight_kg_m,     # แกนขวากราฟใหม่
            "Safe Load w (kg/m)": safe_w_load # แกนซ้ายกราฟใหม่
        })

    df = pd.DataFrame(data_list)

    # --- 2. Scale Factors ---
    max_moment_defl = max(df['Moment Limit'].max(), df['Deflection Limit'].max())
    max_span_val = max_moment_defl * 1.10
    max_shear_val = df['Shear Cap'].max() * 1.10
    scale_factor = max_span_val / max_shear_val

    # Range String
    def create_range_string(row):
        start_m = row['Shear Cap'] * scale_factor
        end_m = row['Max Span']                 
        if start_m >= end_m:
            return f"N/A (Shear > Span)"
        return f"{start_m:.2f} - {end_m:.2f}"

    df['Safe Range'] = df.apply(create_range_string, axis=1)

    # Prepare Data for Plotting
    names = df['Name']
    x = np.arange(len(names))

    # ==================================================
    # 📈 GRAPH 1: OPTIMIZATION GAP (SPAN vs SHEAR)
    # ==================================================
    st.subheader("1️⃣ Optimization Gap (Span vs Shear)")
    
    plt.style.use('default') 
    fig1, ax1 = plt.subplots(figsize=(12, 5.5))
    
    # Grid & Limits
    ax1.grid(which='major', axis='y', linestyle='--', linewidth=0.5, color='gray', alpha=0.3)
    ax1.plot(x, df['Moment Limit'], color='#E74C3C', linestyle='--', linewidth=1.2, label='Moment Limit', alpha=0.8)
    ax1.plot(x, df['Deflection Limit'], color='#2980B9', linestyle='-', linewidth=1.2, label='Deflection Limit', alpha=0.8)
    
    # Green Zone
    shears_visual = df['Shear Cap'] * scale_factor
    upper_bound = np.minimum(df['Moment Limit'], df['Deflection Limit'])
    lower_bound = shears_visual
    ax1.fill_between(x, lower_bound, upper_bound, where=(upper_bound > lower_bound), color='#2ECC71', alpha=0.3, label='Safe Operating Zone')
    
    # Axis 1 Settings
    ax1.set_ylabel('Span Range (m)', fontweight='bold', color='#333333')
    ax1.set_ylim(0, max_span_val)
    ax1.set_xlim(-0.5, len(names)-0.5)
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=90, fontsize=9)
    
    # Axis 2 (Shear)
    ax2 = ax1.twinx()
    ax2.plot(x, df['Shear Cap'], color='#663399', linestyle=':', linewidth=2, label='Shear Capacity ($V_n$)')
    ax2.set_ylabel('Shear Capacity (kg)', fontweight='bold', color='#663399')
    ax2.set_ylim(0, max_shear_val) 

    # Legend
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left', fontsize=9)
    
    st.pyplot(fig1)

    st.divider()

    # ==================================================
    # ⚖️ GRAPH 2: LOAD EFFICIENCY (W vs Weight) - NEW!
    # ==================================================
    st.subheader("2️⃣ Load Efficiency (Capacity $w$ vs Steel Weight)")
    st.caption("กราฟนี้ช่วยเลือกความคุ้มค่า: แท่งกราฟสูง (รับแรงได้เยอะ) แต่เส้นกราฟต่ำ (น้ำหนักเหล็กเบา/ราคาถูก) คือดีที่สุด")

    fig2, ax3 = plt.subplots(figsize=(12, 5.5))
    
    # Grid
    ax3.grid(which='major', axis='y', linestyle='--', linewidth=0.5, color='gray', alpha=0.3)
    
    # Plot 1: Safe Load w (Bar Chart) - Left Axis
    # ใช้ Bar Chart เพื่อให้ดูถึง "ปริมาณ" การรับน้ำหนัก
    bars = ax3.bar(x, df['Safe Load w (kg/m)'], color='#3498DB', alpha=0.6, label='Safe Load Capacity ($w_{safe}$)')
    
    # Plot 2: Steel Weight (Line Chart) - Right Axis
    ax4 = ax3.twinx()
    line = ax4.plot(x, df['Weight (kg/m)'], color='#E67E22', marker='o', markersize=4, linewidth=2, label='Steel Weight (kg/m)')
    
    # Axis Settings
    ax3.set_ylabel('Safe Load Capacity $w$ (kg/m)', fontweight='bold', color='#2980B9')
    ax4.set_ylabel('Steel Weight (kg/m)', fontweight='bold', color='#D35400')
    
    ax3.set_xticks(x)
    ax3.set_xticklabels(names, rotation=90, fontsize=9)
    ax3.set_xlim(-0.5, len(names)-0.5)
    
    # Setting Limits to make it look nice
    ax3.set_ylim(0, df['Safe Load w (kg/m)'].max() * 1.2)
    ax4.set_ylim(0, df['Weight (kg/m)'].max() * 1.5) # เผื่อที่ด้านบนให้เส้นไม่ทับแท่งกราฟมากเกินไป

    # Combine Legends
    lines_3, labels_3 = ax3.get_legend_handles_labels()
    lines_4, labels_4 = ax4.get_legend_handles_labels()
    ax3.legend(lines_3 + lines_4, labels_3 + labels_4, loc='upper left', fontsize=9)

    st.pyplot(fig2)
    
    st.divider()

    # --- 3. Table Summary ---
    st.subheader("📋 Specification Table (Optimization Range)")
    
    st.dataframe(
        df[["Section", "Safe Load w (kg/m)", "Weight (kg/m)", "Safe Range", "Bolts", "Util"]],
        use_container_width=True,
        column_config={
            "Section": st.column_config.TextColumn("Section Size", width="medium"),
            "Safe Load w (kg/m)": st.column_config.NumberColumn("Capacity $w$ (kg/m)", format="%.0f"),
            "Weight (kg/m)": st.column_config.NumberColumn("Steel Wt. (kg/m)", format="%.1f"),
            "Safe Range": st.column_config.TextColumn("Opt. Span Range (m)", width="medium"),
            "Bolts": st.column_config.NumberColumn("Bolts", format="%d"),
            "Util": st.column_config.ProgressColumn("Utilization", format="%.0f%%", min_value=0, max_value=100)
        },
        height=500,
        hide_index=True
    )

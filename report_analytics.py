# report_analytics.py
# Version: 7.2 (Correct W Logic: Min of Shear, Moment, Deflection)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Import Logic
try:
    # เพิ่ม calculate_full_properties เข้ามาด้วย เพื่อดึงค่า Ix, Zx
    from report_generator import get_standard_sections, calculate_connection, calculate_full_properties
except ImportError:
    st.error("⚠️ Error: Missing report_generator.py")
    st.stop()

def render_analytics_section(load_pct, bolt_dia, load_case, factor):
    """
    Dashboard Updated:
    Graph 2: W (Uniform Load Capacity) calculated strictly from Min(Shear, Moment, Deflection)
    """
    st.markdown("## 📊 Structural Analysis Dashboard")
    
    # --- 1. Data Processing ---
    all_sections = get_standard_sections()
    data_list = []
    
    for sec in all_sections:
        # 1. ดึงค่าพื้นฐาน
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        full_props = calculate_full_properties(sec) # ดึงค่า Ix, Zx, Area

        # 2. คำนวณ Utilization
        actual_cap = r['Bolt Qty'] * r['phiRn_bolt']
        util = (r['V_target'] / actual_cap) * 100 if actual_cap > 0 else 0
        
        # 3. คำนวณ W (Uniform Load Capacity) ตามนิยาม Moment, Shear, Deflection
        # ใช้ระยะ Safe Span (r['L_safe']) เป็นตัวตั้งในการหา W ที่ระยะนั้น
        L_m = r['L_safe']
        L_cm = L_m * 100
        
        safe_w_load = 0
        w_shear, w_moment, w_defl = 0, 0, 0
        
        if L_m > 0:
            # A. Shear Limit (V = wL/2 -> w = 2V/L)
            # Vn_beam คือ Shear Capacity (0.6FyAw)
            w_shear = (2 * r['Vn_beam']) / L_m
            
            # B. Moment Limit (M = wL^2/8 -> w = 8M/L^2)
            # phiMn = 0.90 * Fy * Zx
            phi_Mn_kgcm = 0.90 * sec['Fy'] * full_props['Zx (cm3)']
            phi_Mn_kgm = phi_Mn_kgcm / 100
            w_moment = (8 * phi_Mn_kgm) / (L_m**2)
            
            # C. Deflection Limit (delta = 5wL^4 / 384EI -> w = 384EI delta / 5L^4)
            # Limit = L/360
            delta_allow_cm = L_cm / 360
            E_ksc = 2040000
            Ix = full_props['Ix (cm4)']
            
            # คำนวณ w หน่วย kg/cm ก่อน
            w_defl_kg_cm = (384 * E_ksc * Ix * delta_allow_cm) / (5 * (L_cm**4))
            w_defl = w_defl_kg_cm * 100 # แปลงเป็น kg/m
            
            # *** Governing W ***
            safe_w_load = min(w_shear, w_moment, w_defl)
            
        # 4. คำนวณน้ำหนักเหล็ก (kg/m)
        weight_kg_m = full_props['Area (cm2)'] * 0.785 
        
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
            "Weight (kg/m)": weight_kg_m,     
            "Safe Load w (kg/m)": safe_w_load # ค่า W ที่ถูกต้อง
        })

    df = pd.DataFrame(data_list)

    # --- 2. Scale Factors ---
    max_moment_defl = max(df['Moment Limit'].max(), df['Deflection Limit'].max())
    max_span_val = max_moment_defl * 1.10
    max_shear_val = df['Shear Cap'].max() * 1.10
    scale_factor = max_span_val / max_shear_val

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
    
    # Axis Settings
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
    # ⚖️ GRAPH 2: LOAD EFFICIENCY (Corrected W Logic)
    # ==================================================
    st.subheader("2️⃣ Load Efficiency (Safe Uniform Load $w$ vs Weight)")
    st.caption("กราฟนี้แสดงค่า $W_{safe} = \\min(w_{shear}, w_{moment}, w_{defl})$ เทียบกับน้ำหนักเหล็ก")

    fig2, ax3 = plt.subplots(figsize=(12, 5.5))
    ax3.grid(which='major', axis='y', linestyle='--', linewidth=0.5, color='gray', alpha=0.3)
    
    # Plot 1: Safe Load W (Bar Chart) - Left Axis
    bars = ax3.bar(x, df['Safe Load w (kg/m)'], color='#3498DB', alpha=0.65, label='Safe Uniform Load ($w_{safe}$)')
    
    # Plot 2: Steel Weight (Line Chart) - Right Axis
    ax4 = ax3.twinx()
    line = ax4.plot(x, df['Weight (kg/m)'], color='#E67E22', marker='o', markersize=4, linewidth=2, label='Steel Weight (kg/m)')
    
    # Axis Settings
    ax3.set_ylabel('Safe Uniform Load $w$ (kg/m)', fontweight='bold', color='#2980B9')
    ax4.set_ylabel('Steel Weight (kg/m)', fontweight='bold', color='#D35400')
    
    ax3.set_xticks(x)
    ax3.set_xticklabels(names, rotation=90, fontsize=9)
    ax3.set_xlim(-0.5, len(names)-0.5)
    
    # Auto Scale Limits
    w_max = df['Safe Load w (kg/m)'].max()
    wt_max = df['Weight (kg/m)'].max()
    ax3.set_ylim(0, w_max * 1.2 if w_max > 0 else 100)
    ax4.set_ylim(0, wt_max * 1.4) 

    # Combine Legends
    lines_3, labels_3 = ax3.get_legend_handles_labels()
    lines_4, labels_4 = ax4.get_legend_handles_labels()
    ax3.legend(lines_3 + lines_4, labels_3 + labels_4, loc='upper left', fontsize=9)

    st.pyplot(fig2)
    
    st.divider()

    # --- 3. Table Summary ---
    st.subheader("📋 Specification Table")
    # เพิ่มคอลัมน์ Safe W เพื่อให้ user เช็คตัวเลขได้
    st.dataframe(
        df[["Section", "Safe Load w (kg/m)", "Weight (kg/m)", "Max Span", "Bolts", "Util"]],
        use_container_width=True,
        column_config={
            "Section": st.column_config.TextColumn("Section Size", width="medium"),
            "Safe Load w (kg/m)": st.column_config.NumberColumn("Safe W (kg/m)", format="%.0f"),
            "Weight (kg/m)": st.column_config.NumberColumn("Weight (kg/m)", format="%.1f"),
            "Max Span": st.column_config.NumberColumn("Safe Span (m)", format="%.2f"),
            "Bolts": st.column_config.NumberColumn("Bolts", format="%d"),
            "Util": st.column_config.ProgressColumn("Utilization", format="%.0f%%", min_value=0, max_value=100)
        },
        height=500,
        hide_index=True
    )

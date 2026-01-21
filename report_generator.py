# report_analytics.py
# Version: 6.1 (Synced with new report_generator logic)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Import Logic จากไฟล์ report_generator (สมองของระบบ)
try:
    from report_generator import get_standard_sections, calculate_connection
except ImportError:
    st.error("⚠️ Error: Missing report_generator.py. Please make sure both files exist.")
    st.stop()

def render_analytics_section(load_pct, bolt_dia, load_case, factor):
    """
    Dashboard Updated:
    - เชื่อมต่อกับ report_generator ตัวใหม่
    - แสดงกราฟ Green Zone และ ตารางช่วงระยะ (Range)
    """
    st.markdown("## 📊 Structural Analysis")
    
    # --- 1. Data Processing ---
    # ดึงข้อมูลหน้าตัดทั้งหมดจาก Database กลาง
    all_sections = get_standard_sections()
    data_list = []
    
    for sec in all_sections:
        # ส่งข้อมูลไปคำนวณ (ใช้ฟังก์ชันกลางจาก report_generator)
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        
        # คำนวณ % Usage
        actual_cap = r['Bolt Qty'] * r['phiRn_bolt']
        util = (r['V_target'] / actual_cap) * 100 if actual_cap > 0 else 0
        
        data_list.append({
            "Name": r['Section'].replace("H-", ""), 
            "Section": r['Section'], 
            "Moment Limit": r['L_crit_moment'],
            "Deflection Limit": r['L_crit_defl'],
            "Shear Cap": r['Vn_beam'],
            "Max Span": r['L_safe'],
            "Bolts": r['Bolt Qty'],
            "Load (kg)": r['V_target'],
            "Util": util
        })

    df = pd.DataFrame(data_list)

    # --- 2. Calculate Scaling Factor (Global) ---
    # แปลง Shear (kg) -> Visual Span (m) สำหรับกราฟ
    if not df.empty:
        max_moment_defl = max(df['Moment Limit'].max(), df['Deflection Limit'].max())
        max_span_val = max_moment_defl * 1.10
        max_shear_val = df['Shear Cap'].max() * 1.10
        
        # Scale Factor
        scale_factor = max_span_val / max_shear_val if max_shear_val > 0 else 0
    else:
        st.warning("No data available.")
        return

    # --- 3. Add Range Column ---
    def create_range_string(row):
        start_m = row['Shear Cap'] * scale_factor # จุดเริ่ม (Shear Baseline)
        end_m = row['Max Span']                   # จุดจบ (Safe Limit)
        if start_m >= end_m:
            return f"N/A (Shear > Span)"
        return f"{start_m:.2f} - {end_m:.2f}"

    df['Safe Range'] = df.apply(create_range_string, axis=1)

    # Prepare Data for Plotting
    names = df['Name']
    moments = df['Moment Limit']
    defls = df['Deflection Limit']
    shears = df['Shear Cap']
    shears_visual = shears * scale_factor 

    # --- 4. The Graph (Green Zone) ---
    st.subheader("📈 Optimization Gap (Span vs Shear Trend)")
    
    plt.style.use('default') 
    fig, ax1 = plt.subplots(figsize=(12, 5.5))
    
    # Grid
    ax1.grid(which='major', axis='y', linestyle='--', linewidth=0.5, color='gray', alpha=0.3)
    ax1.grid(which='major', axis='x', linestyle=':', linewidth=0.5, color='gray', alpha=0.2)

    x = np.arange(len(names))

    # 4.1 Plot Limits
    ax1.plot(x, moments, color='#E74C3C', linestyle='--', linewidth=1.2, label='Moment Limit', alpha=0.8)
    ax1.plot(x, defls, color='#2980B9', linestyle='-', linewidth=1.2, label='Deflection Limit', alpha=0.8)
    
    # 4.2 The "Green Zone" (Gap)
    upper_bound = np.minimum(moments, defls)
    lower_bound = shears_visual
    
    ax1.fill_between(
        x, lower_bound, upper_bound, 
        where=(upper_bound > lower_bound),
        color='#2ECC71', alpha=0.3, label='Safe Operating Zone'
    )
    
    # Axes Setup
    ax1.set_ylabel('Span Range (m)', fontweight='bold', color='#333333')
    ax1.set_ylim(0, max_span_val)
    ax1.set_xlim(-0.5, len(names)-0.5)
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=90, fontsize=9)
    ax1.tick_params(axis='x', which='both', bottom=False)

    # 4.3 Shear (Floor) - Right Axis
    ax2 = ax1.twinx()
    ax2.plot(x, shears, color='#663399', linestyle=':', linewidth=2, label='Shear Capacity ($V_n$)')
    ax2.set_ylabel('Shear Capacity (kg)', fontweight='bold', color='#663399')
    ax2.set_ylim(0, max_shear_val) 

    # Legend
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left', frameon=True, framealpha=0.9, fontsize=9)

    st.pyplot(fig)

    st.divider()

    # --- 5. Table with Synced Range ---
    st.subheader("📋 Specification Table (Optimization Range)")
    
    st.dataframe(
        df[["Section", "Load (kg)", "Shear Cap", "Safe Range", "Bolts", "Util"]],
        use_container_width=True,
        column_config={
            "Section": st.column_config.TextColumn("Section Size", width="medium"),
            "Load (kg)": st.column_config.NumberColumn("Load ($V_u$)", format="%.0f"),
            "Shear Cap": st.column_config.NumberColumn("Capacity ($V_n$)", format="%.0f kg"),
            "Safe Range": st.column_config.TextColumn("Opt. Span Range (m)", width="medium"),
            "Bolts": st.column_config.NumberColumn("Bolts", format="%d"),
            "Util": st.column_config.ProgressColumn("Utilization", format="%.0f%%", min_value=0, max_value=100)
        },
        height=500,
        hide_index=True
    )

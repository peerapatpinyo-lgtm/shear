# report_analytics.py
# Version: 4.0 (Clean & Minimalist - Focus on Clarity)
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
    Dashboard แบบ Clean Design
    เน้นกราฟที่อ่านง่าย สบายตา และตารางที่กระชับ
    """
    st.markdown("## 📊 Structural Analysis")
    
    # --- 1. Data Processing ---
    all_sections = get_standard_sections()
    data_list = []
    
    # Loop คำนวณ
    for sec in all_sections:
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        
        # คำนวณ % Usage เพื่อใช้ในการทำสีในตาราง
        actual_cap = r['Bolt Qty'] * r['phiRn_bolt']
        util = (r['V_target'] / actual_cap) * 100 if actual_cap > 0 else 0
        
        data_list.append({
            "Name": sec['name'].replace("H-", ""), # ชื่อย่อในกราฟ
            "Section": sec['name'], # ชื่อเต็มในตาราง
            "Moment Limit": r['L_crit_moment'],
            "Deflection Limit": r['L_crit_defl'],
            "Shear Cap": r['Vn_beam'],
            "Max Span": r['L_safe'],
            "Bolts": r['Bolt Qty'],
            "Load (kg)": r['V_target'],
            "Util": util
        })

    df = pd.DataFrame(data_list)
    names = df['Name']
    moments = df['Moment Limit']
    defls = df['Deflection Limit']
    shears = df['Shear Cap']

    # --- 2. The Clean Graph ---
    st.subheader("📈 Optimization Gap (Span vs Shear Trend)")
    
    # ตั้งค่า Style กราฟให้ดูคลีน (ใช้ Style ของ Matplotlib)
    plt.style.use('default') 
    fig, ax1 = plt.subplots(figsize=(12, 5.5))
    
    # ปรับ Grid ให้บางและจางลง
    ax1.grid(which='major', axis='y', linestyle='--', linewidth=0.5, color='gray', alpha=0.3)
    ax1.grid(which='major', axis='x', linestyle=':', linewidth=0.5, color='gray', alpha=0.2)

    x = np.arange(len(names))

    # 2.1 Scale Logic (Visual Normalization)
    # เพิ่ม Headroom 10% เพื่อความสวยงาม
    max_span_val = max(max(moments), max(defls)) * 1.10
    max_shear_val = max(shears) * 1.10
    scale_factor = max_span_val / max_shear_val
    shears_visual = shears * scale_factor

    # 2.2 Plot Limits (Span - Left Axis)
    # ใช้เส้นทึบที่บางลง เพื่อความเนี๊ยบ
    ax1.plot(x, moments, color='#E74C3C', linestyle='--', linewidth=1.2, label='Moment Limit', alpha=0.8)
    ax1.plot(x, defls, color='#2980B9', linestyle='-', linewidth=1.2, label='Deflection Limit', alpha=0.8)
    
    # 2.3 The "Green Gap" (Highlight Area)
    # พื้นที่ระหว่าง Shear (Scaled) กับ Min Limit
    upper_bound = np.minimum(moments, defls)
    lower_bound = shears_visual
    
    ax1.fill_between(
        x, lower_bound, upper_bound, 
        where=(upper_bound > lower_bound),
        color='#2ECC71', # สีเขียวมาตรฐาน
        alpha=0.3,       # ความโปร่งใส 30% กำลังดี ไม่แยงตา
        label='Optimization Zone'
    )
    
    # Format Left Axis
    ax1.set_ylabel('Max Span (m)', fontweight='bold', color='#333333')
    ax1.set_ylim(0, max_span_val)
    ax1.set_xlim(-0.5, len(names)-0.5)
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=90, fontsize=9)
    ax1.tick_params(axis='x', which='both', bottom=False) # ซ่อนขีดแกน X เพื่อความคลีน

    # 2.4 Plot Shear (Shear - Right Axis)
    ax2 = ax1.twinx()
    # ใช้สีม่วงเข้ม (Rebeccapurple) ดูแพงกว่าม่วงปกติ
    ax2.plot(x, shears, color='#663399', linestyle=':', linewidth=2, label='Shear Capacity ($V_n$)')
    ax2.set_ylabel('Shear Capacity (kg)', fontweight='bold', color='#663399')
    ax2.set_ylim(0, max_shear_val) # Sync Scale

    # Legend รวมกันไว้ข้างบน (กรอบใส)
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left', frameon=True, framealpha=0.9, fontsize=9)

    st.pyplot(fig)

    st.divider()

    # --- 3. Clean Table ---
    st.subheader("📋 Specification Table")
    
    # แสดงตารางแบบเรียบง่าย เรียงตาม Catalog
    st.dataframe(
        df[["Section", "Load (kg)", "Shear Cap", "Max Span", "Bolts", "Util"]],
        use_container_width=True,
        column_config={
            "Section": st.column_config.TextColumn("Section Size", width="medium"),
            "Load (kg)": st.column_config.NumberColumn("Load ($V_u$)", format="%.0f"),
            "Shear Cap": st.column_config.NumberColumn("Capacity ($V_n$)", format="%.0f kg"),
            "Max Span": st.column_config.NumberColumn("Safe Span", format="%.2f m"),
            "Bolts": st.column_config.NumberColumn("Bolts", format="%d"),
            "Util": st.column_config.ProgressColumn("Utilization", format="%.0f%%", min_value=0, max_value=100)
        },
        height=500,
        hide_index=True
    )

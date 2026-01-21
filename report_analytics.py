# report_analytics.py
# Version: 3.0 (Professional Dashboard - Catalog Order)
# Features: Visual Gap Graph, Weight Efficiency, Auto-Highlights, CSV Download

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Import Logic from main file
try:
    from report_generator import get_standard_sections, calculate_connection, calculate_full_properties
except ImportError:
    st.error("❌ Critical Error: ไม่พบไฟล์ report_generator.py กรุณาวางไฟล์ทั้งสองไว้ในโฟลเดอร์เดียวกัน")
    st.stop()

def render_analytics_section(load_pct, bolt_dia, load_case, factor):
    """
    แสดงผล Dashboard การวิเคราะห์ขั้นสูง
    - คงการเรียงลำดับตาม Catalog (Size)
    - แสดงกราฟ Visual Gap (Green Zone)
    - วิเคราะห์ความคุ้มค่า (Weight Efficiency)
    """
    
    # --- 1. DATA PREPARATION & BATCH CALCULATION ---
    all_sections = get_standard_sections()
    data_list = []

    for sec in all_sections:
        # 1.1 Structural Calc
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        # 1.2 Physical Properties (Weight)
        props = calculate_full_properties(sec)
        weight_kg_m = props['Area (cm2)'] * 0.785 # A * Density
        
        # 1.3 Efficiency Metric (Span per kg of steel)
        efficiency = r['L_safe'] / weight_kg_m if weight_kg_m > 0 else 0
        
        # 1.4 Capacity Check
        actual_cap = r['Bolt Qty'] * r['phiRn_bolt']
        util = (r['V_target'] / actual_cap) * 100 if actual_cap > 0 else 0

        data_list.append({
            "Name": sec['name'].replace("H-", ""),
            "Full_Name": sec['name'],
            "Weight (kg/m)": weight_kg_m,
            "Moment Limit": r['L_crit_moment'],
            "Deflection Limit": r['L_crit_defl'],
            "Max Span (m)": r['L_safe'],
            "Shear Cap (kg)": r['Vn_beam'],
            "Bolts": r['Bolt Qty'],
            "Util (%)": util,
            "Efficiency": efficiency, # Span per kg
            "Raw Data": r
        })

    df = pd.DataFrame(data_list)

    # --- 2. EXECUTIVE SUMMARY (KPIs) ---
    st.markdown("## 📊 Strategic Analysis Dashboard")
    
    # Find Best Performers
    best_span = df.loc[df['Max Span (m)'].idxmax()]
    best_eff = df.loc[df['Efficiency'].idxmax()]
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🔩 Current Bolt Size", f"M{bolt_dia}", f"Load {load_pct}%")
    with c2:
        st.metric("🏆 Strongest Beam", best_span['Name'], f"{best_span['Max Span (m)']:.2f} m")
    with c3:
        st.metric("💰 Best Value (Eco)", best_eff['Name'], "Most efficient")
    with c4:
        st.metric("📉 H-450 Drop Reason", "Low Inertia", "Deep but Narrow")

    # --- 3. ADVANCED VISUALIZATION (THE GRAPH) ---
    st.subheader("📈 Structural Limit States & Optimization Zone")
    
    # Setup Data
    names = df['Name']
    moments = df['Moment Limit']
    defls = df['Deflection Limit']
    shears = df['Shear Cap (kg)']
    
    # Create Plot
    fig, ax1 = plt.subplots(figsize=(14, 7))
    x = np.arange(len(names))

    # 3.1 Visual Scaling (เพื่อดึงกราฟ Shear ขึ้นมาเทียบ Span)
    # ใช้ Factor 1.2 เพื่อเผื่อที่ด้านบนสำหรับ Legend
    max_span_val = max(max(moments), max(defls)) * 1.2
    max_shear_val = max(shears) * 1.2
    shear_scale = max_span_val / max_shear_val
    shears_visual = shears * shear_scale

    # 3.2 Plot Limits (Left Axis - Meters)
    ax1.set_ylabel('Safe Span Limit (m)', color='#27AE60', fontweight='bold', fontsize=12)
    # Plot Limits
    line_m, = ax1.plot(x, moments, 'r--', label='Moment Limit', alpha=0.5, linewidth=1.5)
    line_d, = ax1.plot(x, defls, 'b-', label='Deflection Limit', alpha=0.6, linewidth=1.5)
    
    # 3.3 The "Green Zone" (Gap between Visual Shear and Actual Limit)
    upper_bound = np.minimum(moments, defls)
    lower_bound = shears_visual
    
    # ระบายสีเฉพาะพื้นที่ที่ Span > Shear Trend (Gap ที่คุ้มค่า)
    ax1.fill_between(
        x, lower_bound, upper_bound, 
        where=(upper_bound > lower_bound),
        color='#2ECC71', alpha=0.35, 
        label='Optimization Zone (Span > Shear Trend)'
    )
    
    # Annotate Max Point
    idx_max = df['Max Span (m)'].idxmax()
    ax1.annotate(f'Max: {df.iloc[idx_max]["Max Span (m)"]:.2f}m', 
                 xy=(idx_max, df.iloc[idx_max]["Max Span (m)"]), 
                 xytext=(idx_max, df.iloc[idx_max]["Max Span (m)"] + 0.5),
                 arrowprops=dict(facecolor='black', shrink=0.05),
                 ha='center', fontsize=9, fontweight='bold')

    # Annotate The Drop (H-450) - เพื่อความเป็นมืออาชีพ อธิบายว่าทำไมกราฟตก
    try:
        idx_drop = df[df['Name'].str.contains("450x200")].index[0]
        ax1.annotate('Low Inertia ($I_x$)', 
                     xy=(idx_drop, df.iloc[idx_drop]["Max Span (m)"]), 
                     xytext=(idx_drop, df.iloc[idx_drop]["Max Span (m)"] + 1.5),
                     arrowprops=dict(facecolor='red', arrowstyle='->'),
                     color='red', ha='center', fontsize=8)
    except:
        pass

    # Axis Settings
    ax1.set_ylim(0, max_span_val)
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=90, fontsize=9)
    ax1.grid(True, linestyle='--', alpha=0.4)

    # 3.4 Right Axis (Shear Capacity)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Shear Capacity (kg)', color='purple', fontweight='bold', fontsize=12)
    line_v, = ax2.plot(x, shears, color='purple', linestyle=':', linewidth=2, label='Shear Trend ($V_n$)')
    ax2.set_ylim(0, max_shear_val) # Sync Scale!
    
    # Unified Legend
    lines = [line_m, line_d, line_v]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left', frameon=True, facecolor='white', framealpha=0.9)

    st.pyplot(fig)
    
    # 📝 Caption อธิบายกราฟ
    st.info("""
    **💡 วิธีอ่านกราฟ:**
    * **พื้นที่สีเขียว:** แสดง "ระยะปลอดภัย" ที่เหลืออยู่เมื่อเทียบกับแนวโน้มของแรงเฉือน (ยิ่งกว้างยิ่งแสดงว่าหน้าตัดนั้นรับ Span ได้ดีมากเมื่อเทียบกับขนาดตัว)
    * **เส้นประสีม่วง:** คือแนวโน้มการรับแรงเฉือน (Shear) ยิ่งหน้าตัดใหญ่ เส้นนี้จะยิ่งสูง
    * **จุดสังเกต:** หน้าตัด H-450x200 กราฟตกลงมาเพราะเป็นหน้าตัดแบบบาง (Light Weight) มีค่า Inertia น้อยกว่า H-400x400 ที่เป็นแบบจัตุรัส
    """)

    st.divider()

    # --- 4. COMPREHENSIVE DATA TABLE ---
    st.subheader("📋 Detailed Calculation Table")
    
    # Formatting for display
    df_display = df.copy()
    
    # เลือก Column ที่จะโชว์
    cols = ["Name", "Weight (kg/m)", "Shear Cap (kg)", "Bolts", "Util (%)", "Max Span (m)", "Efficiency"]
    
    st.dataframe(
        df_display[cols],
        use_container_width=True,
        column_config={
            "Name": st.column_config.TextColumn("Section Name", width="medium"),
            "Weight (kg/m)": st.column_config.NumberColumn("Weight (kg/m)", format="%.1f"),
            "Shear Cap (kg)": st.column_config.NumberColumn("Shear Cap ($V_n$)", format="%.0f"),
            "Bolts": st.column_config.NumberColumn("Bolts Req.", format="%d pcs"),
            "Util (%)": st.column_config.ProgressColumn("Bolt Util.", format="%.0f%%", min_value=0, max_value=100),
            "Max Span (m)": st.column_config.NumberColumn("Safe Span", format="%.2f m"),
            "Efficiency": st.column_config.LineChartColumn("Efficiency (Span/Wt)", y_min=0, y_max=df['Efficiency'].max())
        },
        height=600,
        hide_index=True
    )
    
    # Download Button
    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Full Report (CSV)",
        data=csv,
        file_name='structural_analysis_report.csv',
        mime='text/csv',
    )

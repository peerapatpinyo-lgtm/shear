# report_analytics.py
# Version: 1.1 (Custom Green Zone: Shear to Min-Limit)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Import Logic from main file
# (ตรวจสอบให้แน่ใจว่าไฟล์ report_generator.py อยู่ในโฟลเดอร์เดียวกัน)
try:
    from report_generator import get_standard_sections, calculate_connection
except ImportError:
    st.error("ไม่พบไฟล์ report_generator.py กรุณาวางไฟล์ทั้งสองไว้ในโฟลเดอร์เดียวกัน")
    st.stop()

def render_analytics_section(load_pct, bolt_dia, load_case, factor):
    """
    แสดงผลกราฟและตารางเปรียบเทียบ
    Updated: ปรับการระบายสีเขียวให้อยู่ระหว่างเส้น Shear (Scaled) กับ Min(Limit)
    """
    st.markdown("## 📊 Analytics Dashboard")
    
    all_sections = get_standard_sections()
    names, moments, defls, shears = [], [], [], []
    batch_results = []

    # --- 1. Batch Calculation ---
    for sec in all_sections:
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        
        # Data for Graph
        names.append(sec['name'].replace("H-", "")) 
        moments.append(r['L_crit_moment'])
        defls.append(r['L_crit_defl'])
        shears.append(r['Vn_beam']) 
        
        # Data for Table
        actual_cap = r['Bolt Qty'] * r['phiRn_bolt']
        util = (r['V_target'] / actual_cap) * 100 if actual_cap > 0 else 0
        
        batch_results.append({
            "Section": r['Section'],
            "Design Vu (kg)": r['V_target'],
            "Max Span (m)": r['L_safe'],
            "Limit State": "Moment" if r['L_crit_moment'] < r['L_crit_defl'] else "Deflection",
            "Bolt Qty": r['Bolt Qty'],
            "Plate H (mm)": int(r['Plate Len']*10),
            "Util. (%)": util
        })

    # --- 2. Structural Limit States Diagram (Updated Zone) ---
    st.subheader("📈 Structural Limit States Diagram")
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    x = np.arange(len(names))
    
    # 2.1 Calculate Axis Limits to Normalize Data visually
    # หาสเกลสูงสุดของแต่ละแกนเพื่อเทียบอัตราส่วน
    max_span_val = max(max(moments), max(defls)) * 1.1
    max_shear_val = max(shears) * 1.1
    
    # สร้างเส้น Shear จำลอง (Scaled) เพื่อใช้ระบายสีบนแกนซ้าย (เมตร)
    # สูตร: ค่า Shear เดิม * (Max Span / Max Shear)
    shear_scale_factor = max_span_val / max_shear_val
    shears_visual = np.array(shears) * shear_scale_factor

    # 2.2 Plot Limits (Left Axis - Meters)
    ax1.set_ylabel('Max Span (m)', color='#27AE60', fontweight='bold')
    ax1.plot(x, moments, 'r--', label='Moment Limit', alpha=0.6, linewidth=1.5)
    ax1.plot(x, defls, 'b-', label='Deflection Limit', alpha=0.6, linewidth=1.5)
    
    # 2.3 Custom Fill Between (Green Zone)
    # พื้นที่: ด้านล่างคือ Shear (Visual), ด้านบนคือ Min(Moment, Deflect)
    upper_bound = np.minimum(moments, defls)
    lower_bound = shears_visual
    
    # ระบายสีเฉพาะส่วนที่ Upper > Lower (เพื่อความสวยงาม)
    ax1.fill_between(
        x, 
        lower_bound, 
        upper_bound, 
        where=(upper_bound > lower_bound),
        color='#2ECC71', 
        alpha=0.4, 
        label='Optimal Zone (Above Shear Trend)'
    )
    
    # ตั้งค่าแกนซ้าย
    ax1.set_ylim(0, max_span_val)
    ax1.legend(loc='upper left')
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=90, fontsize=8)
    ax1.grid(True, linestyle=':', alpha=0.5)
    
    # 2.4 Plot Shear Capacity (Right Axis - kg)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Shear Capacity (kg)', color='purple', fontweight='bold')
    # Plot เส้นจริง (หน่วย kg) ทับลงไปที่ตำแหน่งเดียวกับเส้น Visual
    ax2.plot(x, shears, color='purple', linestyle=':', linewidth=2, label='Shear Capacity ($V_n$)')
    ax2.set_ylim(0, max_shear_val) # Sync scale with the visual factor
    ax2.legend(loc='upper right')
    
    st.pyplot(fig)

    st.divider()

    # --- 3. Comparative Analysis Table ---
    st.subheader("📋 Comparative Analysis Table")
    
    col_sort, col_filter = st.columns(2)
    with col_sort:
        sort_by = st.selectbox("Sort By", ["Section", "Max Span (m)", "Util. (%)"], index=1)
        
    df_compare = pd.DataFrame(batch_results)
    
    if sort_by == "Max Span (m)":
        df_compare = df_compare.sort_values(by="Max Span (m)", ascending=False)
    elif sort_by == "Util. (%)":
        df_compare = df_compare.sort_values(by="Util. (%)", ascending=False)
        
    st.dataframe(
        df_compare,
        use_container_width=True,
        column_config={
            "Design Vu (kg)": st.column_config.NumberColumn("Load (kg)", format="%.0f"),
            "Max Span (m)": st.column_config.NumberColumn("Safe Span (m)", format="%.2f"),
            "Bolt Qty": st.column_config.NumberColumn("Bolts", format="%d"),
            "Util. (%)": st.column_config.ProgressColumn("Capacity Usage", format="%.0f%%", min_value=0, max_value=100),
        },
        hide_index=True, height=600
    )

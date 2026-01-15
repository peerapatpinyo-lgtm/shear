import streamlit as st
import drawing_utils as du
import calculation_report as calc  # <--- 1. Import ไฟล์ใหม่

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    # ... (ส่วน Inputs และ Drawing เดิมเหมือนที่ทำไปแล้ว) ...
    # ... (โค้ดช่วงบนคงเดิมทุกอย่าง จนถึงบรรทัดที่ plot รูปเสร็จ) ...

    # --- ส่วนเดิมที่ plot กราฟ 3 รูป ---
    col1, col2, col3 = st.columns(3)
    with col1:
        fig1 = du.create_plan_view(beam_data, plate_data, bolt_data)
        st.plotly_chart(fig1, use_container_width=True, config=plotly_config)
    with col2:
        fig2 = du.create_front_view(beam_data, plate_data, bolt_data)
        st.plotly_chart(fig2, use_container_width=True, config=plotly_config)
    with col3:
        fig3 = du.create_side_view(beam_data, plate_data, bolt_data)
        st.plotly_chart(fig3, use_container_width=True, config=plotly_config)

    # st.info(...) # อันเก่าอาจจะเอาออกหรือเก็บไว้ก็ได้

    st.divider() # เส้นคั่นสวยๆ

    # ==========================================================
    # 🆕 ส่วนแสดงรายการคำนวณ (เรียกใช้จาก calculation_report.py)
    # ==========================================================
    st.markdown("### 🧮 Calculation Results")
    
    # เรียกฟังก์ชัน generate_report และรับข้อความ Markdown กลับมา
    # (V_design คือแรงที่เราใส่เข้ามาในฟังก์ชันหลักอยู่แล้ว)
    report_markdown = calc.generate_report(
        V_load=V_design,
        beam=beam_data,
        plate=plate_data,
        bolts=bolt_data,
        material_grade="A36", # ส่งค่าเพิ่มได้ถ้าต้องการ
        bolt_grade=bolt_grade
    )
    
    # แสดงผล Markdown
    with st.expander("📄 Click to view full calculation details", expanded=True):
        st.markdown(report_markdown)

    return n_rows*n_cols, 10000

import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    # ดึงค่าหน้าตัดเหล็ก (mm)
    h, b = res_ctx['h'], res_ctx['b']
    
    # ส่วนรับข้อมูล Bolt
    with st.container(border=True):
        st.markdown("##### 🔩 Bolt Placement & Clearance Check")
        c1, c2, c3 = st.columns(3)
        bolt_d = c1.selectbox("ขนาด Bolt (mm)", [16, 20, 24, 30], index=1)
        # ระยะจากกึ่งกลาง Bolt ถึงกึ่งกลางเสา (cm)
        dist_x = c2.number_input("ระยะห่างระหว่าง Bolt แนวแกน X (cm)", value=(b/10)+10.0)
        dist_y = c3.number_input("ระยะห่างระหว่าง Bolt แนวแกน Y (cm)", value=(h/10)+10.0)

    # คำนวณ Clearance (ระยะห่างจากขอบปีกเสาถึงกึ่งกลาง Bolt)
    # Clearance_X = (ระยะห่าง Bolt - ความกว้างปีกเสา) / 2
    clearance_mm = ((dist_x * 10) - b) / 2
    
    # เกณฑ์การตรวจสอบ (Min Wrench Clearance)
    min_req = 40 if bolt_d <= 20 else 50
    is_safe = clearance_mm >= min_req

    # --- SVG Drawing (Blueprint Style) ---
    sc = 1.5 # Scale
    svg = f"""
    <div style="display:flex; justify-content:center; background:#f8fafc; padding:20px; border-radius:8px; border:1px solid #cbd5e1;">
    <svg width="600" height="400" viewBox="0 0 600 400">
        <rect x="150" y="50" width="300" height="300" fill="none" stroke="#1e293b" stroke-width="2"/>
        
        <g transform="translate(300, 200)" fill="#cbd5e1" stroke="#000">
            <rect x="{-b/2*sc}" y="{-h/2*sc}" width="{b*sc}" height="10"/> <rect x="{-b/2*sc}" y="{(h/2-10)*sc}" width="{b*sc}" height="10"/> </g>

        <g stroke-width="2">
            <circle cx="{300 - (dist_x*10/2)*sc}" cy="{200 - (dist_y*10/2)*sc}" r="8" fill="none" stroke="{"#16a34a" if is_safe else "#dc2626"}"/>
            <circle cx="{300 + (dist_x*10/2)*sc}" cy="{200 - (dist_y*10/2)*sc}" r="8" fill="none" stroke="{"#16a34a" if is_safe else "#dc2626"}"/>
        </g>

        <line x1="{300 + b/2*sc}" y1="200" x2="{300 + (dist_x*10/2)*sc}" y2="200" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="4"/>
        <text x="{300 + (b/2 + dist_x*10/4)*sc}" y="195" fill="#ef4444" font-size="12" text-anchor="middle">Gap: {clearance_mm:.1f} mm</text>
        
        <text x="300" y="380" text-anchor="middle" font-size="14" font-weight="bold" fill="{"#16a34a" if is_safe else "#dc2626"}">
            Verdict: {"ผ่าน (ติดตั้งง่าย)" if is_safe else "ระวัง! ใกล้เหล็กเกินไปจะขันน็อตลำบาก"}
        </text>
    </svg>
    </div>
    """
    components.html(svg, height=420)

    # แสดงผลทางเทคนิค
    if not is_safe:
        st.error(f"⚠️ **Warning:** ระยะ Clearance ปัจจุบัน ({clearance_mm:.1f} mm) น้อยกว่าระยะแนะนำ ({min_req} mm) สำหรับ Bolt M{bolt_d}")
        st.info("💡 **ข้อแนะนำ:** ให้ขยายระยะห่างระหว่าง Bolt (Spacing) หรือลดขนาด Bolt หากแรงดึงเพียงพอ")
    else:
        st.success(f"✅ **ระยะติดตั้งเหมาะสม:** มีพื้นที่เหลือ {clearance_mm:.1f} mm เพียงพอสำหรับประแจขัน")

# report_generator.py
# Version: 22.0 (Documentation Edition - Clear Explanations)
import streamlit as st
import pandas as pd
from datetime import datetime
import math

# =========================================================
# 🏗️ 1. MOCK DATABASE
# =========================================================
def get_standard_sections():
    # Standard TIS H-Beam
    return [
        {"name": "H-100x50x5x7",    "h": 100, "b": 50,  "tw": 5,  "tf": 7,  "Fy": 2500, "Fu": 4100},
        {"name": "H-125x60x6x8",    "h": 125, "b": 60,  "tw": 6,  "tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-150x75x5x7",    "h": 150, "b": 75,  "tw": 5,  "tf": 7,  "Fy": 2500, "Fu": 4100},
        {"name": "H-175x90x5x8",    "h": 175, "b": 90,  "tw": 5,  "tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-200x100x5.5x8", "h": 200, "b": 100, "tw": 5.5,"tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-250x125x6x9",    "h": 250, "b": 125, "tw": 6,  "tf": 9,  "Fy": 2500, "Fu": 4100},
        {"name": "H-300x150x6.5x9",  "h": 300, "b": 150, "tw": 6.5,"tf": 9,  "Fy": 2500, "Fu": 4100},
        {"name": "H-350x175x7x11",   "h": 350, "b": 175, "tw": 7,  "tf": 11, "Fy": 2500, "Fu": 4100},
        {"name": "H-400x200x8x13",   "h": 400, "b": 200, "tw": 8,  "tf": 13, "Fy": 2500, "Fu": 4100},
        {"name": "H-450x200x9x14",   "h": 450, "b": 200, "tw": 9,  "tf": 14, "Fy": 2500, "Fu": 4100},
        {"name": "H-500x200x10x16",  "h": 500, "b": 200, "tw": 10, "tf": 16, "Fy": 2500, "Fu": 4100},
        {"name": "H-600x200x11x17",  "h": 600, "b": 200, "tw": 11, "tf": 17, "Fy": 2500, "Fu": 4100},
        {"name": "H-700x300x13x24",  "h": 700, "b": 300, "tw": 13, "tf": 24, "Fy": 2500, "Fu": 4100},
        {"name": "H-800x300x14x26",  "h": 800, "b": 300, "tw": 14, "tf": 26, "Fy": 2500, "Fu": 4100},
        {"name": "H-900x300x16x28",  "h": 900, "b": 300, "tw": 16, "tf": 28, "Fy": 2500, "Fu": 4100},
    ]

# =========================================================
# 🧠 2. CALCULATION LOGIC
# =========================================================
def calculate_zx(h, b, tw, tf):
    h_cm, b_cm = h/10.0, b/10.0
    tw_cm, tf_cm = tw/10.0, tf/10.0
    return (b_cm * tf_cm * (h_cm - tf_cm)) + (tw_cm * (h_cm - 2*tf_cm)**2 / 4.0)

def calculate_connection(props):
    # Unpack
    h, tw, fy, fu = props['h'], props['tw'], props['Fy'], props['Fu']
    b, tf = props.get('b', h/2.0), props.get('tf', tw*1.5)
    
    # Constants
    DB = 20.0
    plate_t_mm = 10.0
    
    # Shear Cap
    Aw = (h/10.0) * (tw/10.0)
    V_cap = 1.00 * (0.60 * fy * Aw)
    V_u = 0.75 * V_cap
    
    # Moment Cap & Critical Span
    Zx = calculate_zx(h, b, tw, tf)
    phiMn = 0.90 * (fy * Zx)
    L_critical_m = ((4 * phiMn) / V_u) / 100.0 if V_u > 0 else 0
    
    # Bolt Design
    Ab = (math.pi * (DB/10.0)**2) / 4.0
    Rn_shear = 0.75 * 3300 * Ab
    
    Le = 3.5
    Lc = Le - ((DB+2)/10.0)/2.0
    t_pl, t_web = plate_t_mm/10.0, tw/10.0
    
    phiRn_pl = 0.75 * min(1.2*Lc*t_pl*4050, 2.4*(DB/10.0)*t_pl*4050)
    phiRn_web = 0.75 * min(1.2*Lc*t_web*fu, 2.4*(DB/10.0)*t_web*fu)
    
    cap_per_bolt = min(Rn_shear, phiRn_pl, phiRn_web)
    n_bolts = max(2, math.ceil(V_u / cap_per_bolt)) if cap_per_bolt > 0 else 99

    return {
        "Steel Section": props['name'],
        "Design Vu (Ton)": V_u/1000.0,
        "Max Span @75%V (m)": L_critical_m,
        "Bolt Qty": n_bolts,
        "Bolt Spec": f"M{int(DB)}",
        "Control By": "Web Bear" if phiRn_web < phiRn_pl else "Bolt/Plt",
    }

# =========================================================
# 🖥️ 3. RENDER FUNCTION WITH EXPLANATION
# =========================================================
def render_report_tab(beam_data, conn_data):
    
    st.markdown("### 🖨️ Engineering Report & Analysis")

    # --- 📖 ส่วนคำอธิบาย (EXPLANATION SECTION) ---
    with st.expander("📖 คู่มือ: อ่านหน้านี้อย่างไรให้เข้าใจ (How to read this report)", expanded=False):
        st.markdown("""
        **หน้านี้ทำหน้าที่อะไร?** หน้านี้จะทำการออกแบบจุดต่อ (Connection Design) แบบอัตโนมัติ โดยใช้สมมติฐานความปลอดภัยสูงสุด คือออกแบบให้รับแรงได้ **75% ของกำลังรับแรงเฉือนคาน** เพื่อให้มั่นใจว่าจุดต่อจะแข็งแรงเพียงพอเสมอ ไม่ว่าแรงจริงจะมาเท่าไหร่
        
        ---
        #### 1. แรงออกแบบมาจากไหน? (Design Load)
        เราใช้หลักการ **Capacity Design** คือการออกแบบให้จุดต่อแข็งแรงกว่าคาน
        $$
        V_{design} = 0.75 \times \phi V_{n(Beam)}
        $$
        * ค่านี้คือแรงเฉือน "เกือบสูงสุด" ที่หน้าตัดคานนั้นจะรับไหว
        * ถ้าออกแบบผ่านจุดนี้ได้ แสดงว่าจุดต่อปลอดภัยหายห่วง
        
        #### 2. ค่า "Max Span" คืออะไร? (สำคัญมาก 💡)
        ค่าในช่อง **Max Span @75%V** บอกขีดจำกัดทางฟิสิกส์ของคานตัวนั้น
        $$
        L_{critical} = \\frac{4 \times \phi M_n}{V_{design}}
        $$
        * **ถ้าคานยาวกว่าค่านี้:** คานจะพังด้วยการแอ่นตัว (Moment) ก่อนที่แรงเฉือนจะขึ้นไปถึง 75% -> **จุดต่อรับแรงน้อยลง (ปลอดภัย)**
        * **ถ้าคานสั้นกว่าค่านี้:** คานมีความเสี่ยงที่จะเกิดแรงเฉือนสูงถึง 75% จริงๆ -> **ต้องใช้จำนวน Bolt ตามตารางนี้**
        
        > **สรุปง่ายๆ:** ถ้าคานในแบบของคุณ **"ยาว"** กว่าเลขในตาราง แสดงว่า Bolt ที่คำนวณให้นี้ **Over Design (เผื่อไว้เยอะมาก)** สบายใจได้เลย
        
        #### 3. Bolt Spec & Control
        * **Bolt Qty:** จำนวนน๊อตขั้นต่ำที่ต้องใช้ (เรียงแถวเดี่ยว)
        * **Control By:** บอกจุดอ่อนที่สุดของจุดต่อ
            * *Web Bear:* เอวคานบางเกินไป (รูเจาะจะฉีก)
            * *Bolt/Plt:* น๊อตจะขาด หรือแผ่นเหล็กจะฉีก
        """)
        
    st.markdown("---")
    
    # --- TAB A: SINGLE BEAM ---
    with st.expander("📌 Single Beam Detail (ดูรายละเอียดทีละตัว)", expanded=True):
        if beam_data:
            try:
                res = calculate_connection({
                    "name": beam_data.get('sec_name', 'Custom'),
                    "h": float(beam_data.get('h', 400)),
                    "b": float(beam_data.get('h', 400))/2,
                    "tw": float(beam_data.get('tw', 8)),
                    "tf": float(beam_data.get('tw', 8))*1.5,
                    "Fy": float(beam_data.get('Fy', 2500)),
                    "Fu": float(beam_data.get('Fu', 4100))
                })
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Design Load (Vu)", f"{res['Design Vu (Ton)']*1000:,.0f} kg")
                c2.metric("Critical Span", f"{res['Max Span @75%V (m)']:.2f} m", "Max Length")
                c3.metric("Bolts Required", f"{res['Bolt Qty']} pcs", res['Bolt Spec'])
                
                # Dynamic Explanation for Single Beam
                span_val = res['Max Span @75%V (m)']
                st.info(f"""
                **แปลผล:** คาน **{res['Steel Section']}** จะรับแรงเฉือนมหาศาลขนาดนี้ได้ ก็ต่อเมื่อคานมีความยาว **ไม่เกิน {span_val:.2f} เมตร**
                *(หากคานจริงยาวกว่า {span_val:.2f} ม. แรงเฉือนจะลดลง และจำนวนน๊อตนี้ถือว่าเผื่อไว้ปลอดภัยมาก)*
                """)
            except Exception as e:
                st.error(f"Error: {e}")
        else:
             st.warning("Please select a beam first.")

    st.markdown("---")

    # --- TAB B: BATCH ANALYSIS ---
    st.subheader("🚀 Standard Sections Analysis Table")
    st.write("ตารางสรุปการออกแบบสำหรับหน้าตัดมาตรฐาน (ไล่จากเล็กไปใหญ่)")
    
    if st.button("⚡ Run Full Analysis", type="primary"):
        all_beams = get_standard_sections()
        results = []
        progress_bar = st.progress(0)
        
        for i, beam in enumerate(all_beams):
            progress_bar.progress((i + 1) / len(all_beams))
            results.append(calculate_connection(beam))
            
        df_res = pd.DataFrame(results)
        
        st.dataframe(
            df_res,
            use_container_width=True,
            column_config={
                "Steel Section": st.column_config.TextColumn("Section"),
                "Design Vu (Ton)": st.column_config.NumberColumn("Load (Ton)", format="%.2f", help="75% of Shear Capacity"),
                "Max Span @75%V (m)": st.column_config.NumberColumn("Critical Span (m)", format="%.2f", help="ความยาวคานที่ทำให้เกิดแรงเฉือนนี้พอดี"),
                "Bolt Qty": st.column_config.NumberColumn("Bolts (Pcs)", format="%d"),
                "Control By": st.column_config.TextColumn("Failure Mode")
            },
            hide_index=True
        )

# report_generator.py
# Version: 21.0 (Physics Engine - Critical Span Calculation)
import streamlit as st
import pandas as pd
from datetime import datetime
import math

# =========================================================
# 🏗️ 1. MOCK DATABASE (ฐานข้อมูลเหล็กมาตรฐาน TIS)
# =========================================================
def get_standard_sections():
    # Format: Name, h, b, tw, tf, Fy, Fu
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
# 🧠 2. CORE CALCULATION LOGIC
# =========================================================
def calculate_zx(h, b, tw, tf):
    """
    Calculate Plastic Modulus (Zx) for I-Shape
    Zx = (b*tf)*(h-tf) + (tw*(h-2*tf)^2)/4
    All units in cm
    """
    h_cm = h/10.0
    b_cm = b/10.0
    tw_cm = tw/10.0
    tf_cm = tf/10.0
    
    # Plastic Modulus Formula
    Zx = (b_cm * tf_cm * (h_cm - tf_cm)) + (tw_cm * (h_cm - 2*tf_cm)**2 / 4.0)
    return Zx

def calculate_connection(props):
    # 1. Unpack properties
    h = props['h']
    tw = props['tw']
    fy = props['Fy']
    fu = props['Fu']
    
    # Try to get b and tf, if not exist use approximation
    b = props.get('b', h/2.0) 
    tf = props.get('tf', tw*1.5)
    
    # Constants
    DB = 20.0
    DH = DB + 2.0
    plate_t_mm = 10.0
    
    # 2. Geometry Conversion
    d_cm = h / 10.0
    tw_cm = tw / 10.0
    Aw = d_cm * tw_cm
    
    # 3. Beam Capacity (Shear)
    Vn_beam = 0.60 * fy * Aw
    V_cap = 1.00 * Vn_beam # Phi=1.00
    V_u = 0.75 * V_cap     # 75% Rule
    
    # 4. Beam Capacity (Moment) - To find Critical Length
    Zx = calculate_zx(h, b, tw, tf)
    Mn_beam = fy * Zx # Plastic Moment (kg.cm)
    phiMn = 0.90 * Mn_beam
    
    # 5. Critical Length Calculation (L = 4*M / V)
    # ความยาวที่ทำให้เกิด V_u พร้อมกับ M_max พอดี
    # ถ้าคานยาวกว่านี้ -> จะพังด้วยโมเมนต์ก่อน (Shear จะไม่ถึง 75%)
    # ถ้าคานสั้นกว่านี้ -> Shear จะถึง 75% ได้
    if V_u > 0:
        L_critical_cm = (4 * phiMn) / V_u
        L_critical_m = L_critical_cm / 100.0
    else:
        L_critical_m = 0
        
    # 6. Bolt Capacity
    Ab = (math.pi * (DB/10.0)**2) / 4.0
    Rn_shear = 0.75 * 3300 * Ab
    
    Le = 3.5
    Lc = Le - (DH/10.0)/2.0
    plate_t_cm = plate_t_mm / 10.0
    
    rn_pl = min(1.2*Lc*plate_t_cm*4050, 2.4*(DB/10.0)*plate_t_cm*4050)
    phiRn_pl = 0.75 * rn_pl
    
    rn_web = min(1.2*Lc*tw_cm*fu, 2.4*(DB/10.0)*tw_cm*fu)
    phiRn_web = 0.75 * rn_web
    
    phiRn_bearing = min(phiRn_pl, phiRn_web)
    cap_per_bolt = min(Rn_shear, phiRn_bearing)
    
    if cap_per_bolt > 0:
        n_req = V_u / cap_per_bolt
        n_bolts = max(2, math.ceil(n_req))
    else:
        n_bolts = 99
        
    # Weld
    spacing = 7.0
    L_plate_cm = (2*Le) + ((n_bolts-1)*spacing)
    w_size = 0.6
    phiRn_weld = 0.75 * (0.6 * 4900 * 0.707 * w_size) * 2
    req_weld_len = V_u / phiRn_weld
    weld_status = "OK" if L_plate_cm >= req_weld_len else "Short Plate"
    
    return {
        "Steel Section": props['name'],
        "Design Vu (Ton)": V_u/1000.0,
        "Max Span @75%V (m)": L_critical_m, # <--- NEW FIELD
        "Bolt Qty": n_bolts,
        "Bolt Spec": f"M{int(DB)}",
        "Control By": "Web Bear" if phiRn_web < phiRn_pl else "Bolt/Plt",
    }

# =========================================================
# 🖥️ 3. RENDER FUNCTION
# =========================================================
def render_report_tab(beam_data, conn_data):
    st.markdown("### 🖨️ Engineering Report & Analysis")
    
    # --- TAB A: SINGLE ---
    with st.expander("📌 Single Beam Detail", expanded=True):
        if beam_data:
            try:
                # พยายาม Parse ค่า b, tf จากชื่อ ถ้าไม่มีให้เดา
                # (กรณี User กรอกเอง อาจจะไม่แม่นเรื่อง Moment แต่ Shear แม่น)
                res = calculate_connection({
                    "name": beam_data.get('sec_name', 'Custom'),
                    "h": float(beam_data.get('h', 400)),
                    "b": float(beam_data.get('h', 400))/2, # Estimate
                    "tw": float(beam_data.get('tw', 8)),
                    "tf": float(beam_data.get('tw', 8))*1.5, # Estimate
                    "Fy": float(beam_data.get('Fy', 2500)),
                    "Fu": float(beam_data.get('Fu', 4100))
                })
                
                c1, c2, c3 = st.columns(3)
                design_load_kg = res['Design Vu (Ton)'] * 1000 
                c1.metric("Design Load (Vu)", f"{design_load_kg:,.0f} kg")
                c2.metric("Critical Span", f"{res['Max Span @75%V (m)']:.2f} m", "Max Length for Shear")
                c3.metric("Bolts", f"{res['Bolt Qty']} pcs", res['Control By'])
                
                st.info(f"💡 หมายความว่า: คานตัวนี้ต้องสั้นกว่า **{res['Max Span @75%V (m)']:.2f} เมตร** จึงจะเกิดแรงเฉือนระดับนี้ได้ (ถ้าคานยาวกว่านี้ จะพังด้วยโมเมนต์ดัดก่อน)")
                
            except Exception as e:
                st.error(f"Single Calc Error: {e}")
        else:
             st.warning("Please select a beam first.")

    st.markdown("---")

    # --- TAB B: BATCH ---
    st.subheader("🚀 Standard Sections Analysis")
    if st.button("⚡ Run Analysis (With Critical Span)", type="primary"):
        
        all_beams = get_standard_sections()
        results = []
        
        progress_bar = st.progress(0)
        
        for i, beam in enumerate(all_beams):
            progress_bar.progress((i + 1) / len(all_beams))
            res = calculate_connection(beam)
            results.append(res)
            
        df_res = pd.DataFrame(results)
        
        st.dataframe(
            df_res,
            use_container_width=True,
            column_config={
                "Steel Section": st.column_config.TextColumn("Section"),
                "Design Vu (Ton)": st.column_config.NumberColumn("V (Ton)", format="%.2f"),
                "Max Span @75%V (m)": st.column_config.NumberColumn("Max Span (m)", format="%.2f"),
                "Bolt Qty": st.column_config.NumberColumn("Bolts", format="%d"),
            },
            hide_index=True
        )
        st.caption("Note: 'Max Span' คือความยาวคานสูงสุดที่แรงเฉือนจะถึง 75% Capacity ได้ (คำนวณจาก Simple Beam UDL)")

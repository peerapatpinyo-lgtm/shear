# report_generator.py
# Version: 20.1 (Bug Fixed & Stable)
import streamlit as st
import pandas as pd
from datetime import datetime
import math

# =========================================================
# 🏗️ 1. MOCK DATABASE (ฐานข้อมูลเหล็กมาตรฐาน TIS)
# =========================================================
def get_standard_sections():
    return [
        {"name": "H-100x50x5x7",    "h": 100, "tw": 5,  "Fy": 2500, "Fu": 4100},
        {"name": "H-125x60x6x8",    "h": 125, "tw": 6,  "Fy": 2500, "Fu": 4100},
        {"name": "H-150x75x5x7",    "h": 150, "tw": 5,  "Fy": 2500, "Fu": 4100},
        {"name": "H-175x90x5x8",    "h": 175, "tw": 5,  "Fy": 2500, "Fu": 4100},
        {"name": "H-200x100x5.5x8", "h": 200, "tw": 5.5,"Fy": 2500, "Fu": 4100},
        {"name": "H-250x125x6x9",    "h": 250, "tw": 6,  "Fy": 2500, "Fu": 4100},
        {"name": "H-300x150x6.5x9",  "h": 300, "tw": 6.5,"Fy": 2500, "Fu": 4100},
        {"name": "H-350x175x7x11",   "h": 350, "tw": 7,  "Fy": 2500, "Fu": 4100},
        {"name": "H-400x200x8x13",   "h": 400, "tw": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-450x200x9x14",   "h": 450, "tw": 9,  "Fy": 2500, "Fu": 4100},
        {"name": "H-500x200x10x16",  "h": 500, "tw": 10, "Fy": 2500, "Fu": 4100},
        {"name": "H-600x200x11x17",  "h": 600, "tw": 11, "Fy": 2500, "Fu": 4100},
        {"name": "H-700x300x13x24",  "h": 700, "tw": 13, "Fy": 2500, "Fu": 4100},
        {"name": "H-800x300x14x26",  "h": 800, "tw": 14, "Fy": 2500, "Fu": 4100},
        {"name": "H-900x300x16x28",  "h": 900, "tw": 16, "Fy": 2500, "Fu": 4100},
    ]

# =========================================================
# 🧠 2. CORE CALCULATION LOGIC
# =========================================================
def calculate_connection(props):
    """
    Core Logic: Input Dict -> Output Dict
    """
    # 1. Unpack properties
    h = props['h']
    tw = props['tw']
    fy = props['Fy']
    fu = props['Fu']
    
    # Constants
    DB = 20.0
    DH = DB + 2.0
    plate_t_mm = 10.0
    
    # 2. Geometry Conversion
    d_cm = h / 10.0
    tw_cm = tw / 10.0
    Aw = d_cm * tw_cm
    
    # 3. Beam Capacity & Load
    Vn_beam = 0.60 * fy * Aw
    phi = 1.00
    V_cap = phi * Vn_beam
    V_u = 0.75 * V_cap # 75% Rule
    
    # 4. Bolt Capacity (Shear)
    Ab = (math.pi * (DB/10.0)**2) / 4.0
    phi_shear = 0.75
    Rn_shear = phi_shear * 3300 * Ab # Fnv=3300 ksc
    
    # 5. Bearing Capacity (Web vs Plate)
    Le = 3.5 # cm
    Lc = Le - (DH/10.0)/2.0
    plate_t_cm = plate_t_mm / 10.0
    
    # Plate Bearing
    rn_pl = min(1.2*Lc*plate_t_cm*4050, 2.4*(DB/10.0)*plate_t_cm*4050)
    phiRn_pl = 0.75 * rn_pl
    
    # Web Bearing
    rn_web = min(1.2*Lc*tw_cm*fu, 2.4*(DB/10.0)*tw_cm*fu)
    phiRn_web = 0.75 * rn_web
    
    # Governing
    phiRn_bearing = min(phiRn_pl, phiRn_web)
    cap_per_bolt = min(Rn_shear, phiRn_bearing)
    
    # 6. Determine Bolts
    if cap_per_bolt > 0:
        n_req = V_u / cap_per_bolt
        n_bolts = max(2, math.ceil(n_req))
    else:
        n_bolts = 99
        
    # 7. Check Plate Length vs Weld
    spacing = 7.0 # cm
    L_plate_cm = (2*Le) + ((n_bolts-1)*spacing)
    
    # Weld Req
    w_size = 0.6 # cm
    phiRn_weld = 0.75 * (0.6 * 4900 * 0.707 * w_size) * 2
    req_weld_len = V_u / phiRn_weld
    
    weld_status = "OK" if L_plate_cm >= req_weld_len else "Short Plate"
    
    # Return Result Dictionary (KEY NAMES FIXED HERE)
    return {
        "Steel Section": props['name'],
        "h (mm)": h,
        "Beam Cap (Ton)": V_cap/1000.0,
        "Design Vu (Ton)": V_u/1000.0, 
        "Bolt Qty": n_bolts,
        "Bolt Spec": f"M{int(DB)} A325",
        "Plate (mm)": int(plate_t_mm),
        "Control By": "Web Bearing" if phiRn_web < phiRn_pl else "Plate/Shear",
        "Weld Check": weld_status
    }

# =========================================================
# 🖥️ 3. RENDER FUNCTION
# =========================================================
def render_report_tab(beam_data, conn_data):
    
    st.markdown("### 🖨️ Engineering Report & Batch Analysis")
    
    # --- TAB A: SINGLE CALCULATION ---
    with st.expander("📌 Single Beam Detail (ดูรายละเอียดทีละตัว)", expanded=True):
        if not beam_data:
            st.warning("Please select a beam in Tab 1")
        else:
            # ใช้ฟังก์ชันคำนวณ
            try:
                res = calculate_connection({
                    "name": beam_data.get('sec_name', 'Custom'),
                    "h": float(beam_data.get('h', 400)),
                    "tw": float(beam_data.get('tw', 8)),
                    "Fy": float(beam_data.get('Fy', 2500)),
                    "Fu": float(beam_data.get('Fu', 4100))
                })
                
                # Show Result Pretty
                c1, c2, c3 = st.columns(3)
                
                # FIX: ใช้ key ให้ตรงกับที่ return มา (Design Vu (Ton))
                design_load_kg = res['Design Vu (Ton)'] * 1000 
                
                c1.metric("Design Load (Vu)", f"{design_load_kg:,.0f} kg")
                c2.metric("Required Bolts", f"{res['Bolt Qty']} pcs", res['Bolt Spec'])
                c3.metric("Plate Thickness", f"{res['Plate (mm)']} mm", res['Control By'])
                
                st.info(f"Summary: Use {res['Bolt Qty']} bolts for {res['Steel Section']} (Weld Status: {res['Weld Check']})")
            except Exception as e:
                st.error(f"Error processing single beam: {e}")

    st.markdown("---")

    # --- TAB B: BATCH PROCESSOR ---
    st.subheader("🚀 Batch Analysis (คำนวณรวดเดียวทั้งตาราง)")
    st.write("กดปุ่มด้านล่างเพื่อไล่คำนวณหน้าตัดเหล็กมาตรฐานทั้งหมด (TIS Standard)")
    
    if st.button("⚡ Run Calculation for All Sections", type="primary"):
        
        all_beams = get_standard_sections()
        results = []
        
        # Progress Bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Loop Calculate
        for i, beam in enumerate(all_beams):
            progress = (i + 1) / len(all_beams)
            progress_bar.progress(progress)
            status_text.text(f"Calculating: {beam['name']}...")
            
            res = calculate_connection(beam)
            results.append(res)
            
        status_text.text("✅ Calculation Complete!")
        
        # Display DataFrame
        df_res = pd.DataFrame(results)
        
        st.dataframe(
            df_res,
            use_container_width=True,
            column_config={
                "Steel Section": st.column_config.TextColumn("Section Size"),
                "Design Vu (Ton)": st.column_config.NumberColumn("V_design (Ton)", format="%.2f"),
                "Bolt Qty": st.column_config.NumberColumn("Bolts (Pcs)", format="%d"),
                "Control By": st.column_config.TextColumn("Critical Limit"),
                "Weld Check": st.column_config.TextColumn("Weld Status")
            },
            hide_index=True
        )
        
        # Download CSV
        csv = df_res.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Excel/CSV",
            data=csv,
            file_name='Standard_Connection_Table.csv',
            mime='text/csv'
        )

    else:
        st.info("Waiting for command... (Click button above)")

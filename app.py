import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE (กระดาษคำนวณ)
# ==========================================
st.set_page_config(page_title="Professional Structural Report", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    /* จำลองกระดาษ A4 หรือ Engineering Report */
    .calc-paper {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 5px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        font-family: 'Sarabun', sans-serif;
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
    }
    .header-topic {
        color: #1a5276;
        border-bottom: 2px solid #1a5276;
        padding-bottom: 10px;
        margin-bottom: 20px;
        font-weight: bold;
        font-size: 22px;
    }
    .sub-topic {
        color: #2e86c1;
        font-weight: bold;
        margin-top: 20px;
        font-size: 18px;
    }
    .governing-box {
        background-color: #d4efdf;
        padding: 20px;
        border: 2px solid #27ae60;
        border-radius: 10px;
        text-align: center;
        color: #145a32;
        margin-top: 20px;
    }
    .warning-box {
        background-color: #fdedec;
        padding: 10px;
        border: 1px solid #e74c3c;
        border-radius: 5px;
        color: #922b21;
    }
    /* ปรับแต่ง Table ให้ดูดีขึ้น */
    div[data-testid="stTable"] {
        font-family: 'Courier New', monospace;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA & INPUTS
# ==========================================
def get_sys_data():
    data = [
        ("H 100x50x5x7", 100, 50, 5, 7, 378, 76.5),
        ("H 150x75x5x7", 150, 75, 5, 7, 666, 88.8),
        ("H 200x100x5.5x8", 200, 100, 5.5, 8, 1840, 184),
        ("H 250x125x6x9", 250, 125, 6, 9, 3690, 295),
        ("H 300x150x6.5x9", 300, 150, 6.5, 9, 7210, 481),
        ("H 350x175x7x11", 350, 175, 7, 11, 13600, 775),
        ("H 400x200x8x13", 400, 200, 8, 13, 23700, 1190),
        ("H 450x200x9x14", 450, 200, 9, 14, 33500, 1490),
        ("H 500x200x10x16", 500, 200, 10, 16, 47800, 1910),
        ("H 600x200x11x17", 600, 200, 11, 17, 77600, 2590),
        ("H 700x300x13x24", 700, 300, 13, 24, 201000, 5760),
        ("H 800x300x14x26", 800, 300, 14, 26, 292000, 7290),
        ("H 900x300x16x28", 900, 300, 16, 28, 411000, 9140)
    ]
    return pd.DataFrame(data, columns=["Section", "h", "b", "tw", "tf", "Ix", "Zx"])

# SIDEBAR
with st.sidebar:
    st.header("1. Input Parameters")
    df = get_sys_data()
    sec_name = st.selectbox("Select Section", df['Section'], index=6) # H400
    
    st.subheader("Material Properties")
    Fy = st.number_input("Yield Strength (Fy)", value=2400)
    Fu = st.number_input("Ultimate Strength (Fu)", value=4000)
    E_val = 2.04e6 
    
    st.subheader("Geometry")
    span = st.number_input("Span Length (m)", 1.0, 20.0, 6.0, step=0.5)

    # Get Props
    p = df[df['Section'] == sec_name].iloc[0]
    h, tw, tf, Ix, Zx = p['h'], p['tw'], p['tf'], p['Ix'], p['Zx']
    
    st.markdown("---")
    st.markdown("**Section Properties:**")
    st.latex(rf"h = {h} \ mm, \ t_w = {tw} \ mm")
    st.latex(rf"I_x = {Ix:,} \ cm^4")
    st.latex(rf"Z_x = {Zx:,} \ cm^3")

# ==========================================
# 3. LOGIC & CALCULATION
# ==========================================
# Units: kg, cm
L_cm = span * 100
h_cm = h/10
tw_cm = tw/10
Aw = h_cm * tw_cm

# CASE 1: Shear Yielding
V_case1 = 0.6 * Fy * Aw
w_case1 = (2 * V_case1) / L_cm * 100 

# CASE 2: Bending Moment
M_all = 0.6 * Fy * Zx
V_case2 = (4 * M_all) / L_cm
w_case2 = (8 * M_all) / (L_cm**2) * 100 

# CASE 3: Deflection (L/240)
V_case3 = (384 * E_val * Ix) / (2400 * (L_cm**2))
w_case3 = (384 * E_val * Ix) / (1200 * (L_cm**3)) * 100 

# Compare
results = {
    "Shear Capacity": V_case1,
    "Moment Capacity": V_case2,
    "Deflection Limit": V_case3
}
V_governing = min(results.values())
Control_case = min(results, key=results.get)

# ==========================================
# 4. MAIN REPORT
# ==========================================
st.title("🏗️ Structural Calculation Report")
st.write("รายการคำนวณความสามารถในการรับน้ำหนักและออกแบบจุดต่อ (Automated Calculation Sheet)")

tab_beam, tab_conn = st.tabs(["📄 1. Beam Capacity Calculation", "🔩 2. Connection Design"])

# -------------------------------------------------------------------
# TAB 1: BEAM REPORT
# -------------------------------------------------------------------
with tab_beam:
    col_sheet, col_vis = st.columns([1.3, 1])
    
    with col_sheet:
        st.markdown('<div class="calc-paper">', unsafe_allow_html=True)
        st.markdown('<div class="header-topic">PART A: Beam Capacity Analysis</div>', unsafe_allow_html=True)
        
        st.write(f"**Section:** {sec_name} | **Span:** {span:.2f} m")
        st.markdown("")
        
        # --- CASE 1 ---
        st.markdown('<div class="sub-topic">1. Check Web Shear Capacity (แรงเฉือน)</div>', unsafe_allow_html=True)
        st.write("ความต้านทานแรงเฉือนของหน้าตัด (Shear Yielding):")
        st.latex(r"A_w = d \times t_w")
        st.latex(rf"A_w = {h/10:.1f} \times {tw/10:.1f} = {Aw:.2f} \ cm^2")
        
        st.write("Allowable Shear ($V_n$):")
        st.latex(r"V_1 = 0.6 \cdot F_y \cdot A_w")
        st.latex(rf"V_1 = 0.6 \cdot {Fy} \cdot {Aw:.2f} = \mathbf{{{V_case1:,.0f}}} \ kg")

        # --- CASE 2 ---
        st.markdown('<div class="sub-topic">2. Check Bending Moment (โมเมนต์ดัด)</div>', unsafe_allow_html=True)
        st.write("โมเมนต์ดัดที่ยอมให้ ($M_{allow}$):")
        st.latex(r"M_{all} = 0.6 \cdot F_y \cdot Z_x")
        st.latex(rf"M_{{all}} = 0.6 \cdot {Fy} \cdot {Zx} = {M_all:,.0f} \ kg \cdot cm")
        
        st.write("แรงปฏิกิริยาสูงสุดที่รับได้ (แปลงจากโมเมนต์):")
        st.latex(r"V_2 = \frac{4 \cdot M_{all}}{L}")
        st.latex(rf"V_2 = \frac{{4 \cdot {M_all:,.0f}}}{{{L_cm}}} = \mathbf{{{V_case2:,.0f}}} \ kg")

        # --- CASE 3 ---
        st.markdown('<div class="sub-topic">3. Check Deflection (ระยะแอ่น L/240)</div>', unsafe_allow_html=True)
        st.write("แรงปฏิกิริยาที่ทำให้เกิดระยะแอ่นตัวสูงสุดที่ยอมให้:")
        st.latex(r"V_3 = \frac{384 \cdot E \cdot I_x}{2400 \cdot L^2}")
        st.latex(rf"V_3 = \frac{{384 \cdot {E_val:.0f} \cdot {Ix}}}{{2400 \cdot {L_cm}^2}} = \mathbf{{{V_case3:,.0f}}} \ kg")

        # --- SUMMARY ---
        st.markdown("---")
        st.markdown('<div class="header-topic">CONCLUSION (สรุปผล)</div>', unsafe_allow_html=True)
        st.write("เปรียบเทียบค่าทั้ง 3 กรณี (Compare Cases):")
        
        # --- FIX: ปรับปรุงการแสดงผล Table เพื่อไม่ให้ Error ---
        comp_data = pd.DataFrame({
            "Criteria": ["1. Shear", "2. Moment", "3. Deflection"],
            "Max Reaction (V)": [V_case1, V_case2, V_case3],
            "Max Uniform Load (w)": [w_case1, w_case2, w_case3]
        })
        
        # ใช้ Dictionary ระบุว่า column ไหนจัด Format อย่างไร (ป้องกัน Error กับ column ที่เป็น string)
        st.table(comp_data.style.format({
            "Max Reaction (V)": "{:,.0f}",
            "Max Uniform Load (w)": "{:,.0f}"
        }))
        # ----------------------------------------------------
        
        st.markdown(f"""
        <div class="governing-box">
            <h3>DESIGN REACTION ($V_{{design}}$) = {V_governing:,.0f} kg</h3>
            Controlled by: <b>{Control_case}</b>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    with col_vis:
        st.subheader("📊 Visual Analysis")
        
        # Plot Logic
        L_vals = np.linspace(1, 20, 100)
        L_vals_cm = L_vals * 100
        
        v1_line = np.full_like(L_vals, V_case1)
        v2_line = (4 * M_all) / L_vals_cm
        v3_line = (384 * E_val * Ix) / (2400 * (L_vals_cm**2))
        v_env = np.minimum(np.minimum(v1_line, v2_line), v3_line)
        
        fig = go.Figure()
        # Limits
        fig.add_trace(go.Scatter(x=L_vals, y=v1_line, name='1. Shear Limit', line=dict(dash='dot', color='green')))
        fig.add_trace(go.Scatter(x=L_vals, y=v2_line, name='2. Moment Limit', line=dict(dash='dot', color='orange')))
        fig.add_trace(go.Scatter(x=L_vals, y=v3_line, name='3. Deflection Limit', line=dict(dash='dot', color='red')))
        
        # Envelope
        fig.add_trace(go.Scatter(x=L_vals, y=v_env, name='Design Capacity', fill='tozeroy', line=dict(color='#1a5276', width=3)))
        
        # Current Point
        fig.add_trace(go.Scatter(x=[span], y=[V_governing], mode='markers+text', 
                                 marker=dict(size=15, color='#c0392b'),
                                 text=[f"{V_governing/1000:.1f}T"], textposition="top right",
                                 name='Current Design'))
        
        # Optimal
        d_m = h/1000
        fig.add_vrect(x0=15*d_m, x1=20*d_m, fillcolor="green", opacity=0.1, annotation_text="Optimal Span")
        
        fig.update_layout(xaxis_title="Span Length (m)", yaxis_title="Reaction Force (kg)", height=500,
                          hovermode="x unified", title="Load Capacity Envelope",
                          xaxis=dict(rangeslider=dict(visible=True)))
        st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------------------------
# TAB 2: CONNECTION DESIGN REPORT
# -------------------------------------------------------------------
with tab_conn:
    st.markdown('<div class="calc-paper">', unsafe_allow_html=True)
    st.markdown('<div class="header-topic">PART B: Connection Design Report</div>', unsafe_allow_html=True)
    
    col_in, col_cal = st.columns([1, 2])
    
    with col_in:
        st.markdown("**1. Design Load ($V_u$)**")
        st.write(f"From Part A: **{V_governing:,.0f} kg**")
        
        st.markdown("**2. Connection Config**")
        bolt_gr = st.selectbox("Bolt Grade", ["A325", "A307"])
        dia = st.selectbox("Diameter (mm)", [12, 16, 20, 22, 24], index=2)
        n_rows = st.number_input("No. of Rows", 2, 8, 3)
        plt_t = st.selectbox("Plate Thick (mm)", [6, 9, 12, 16], index=1)
        w_leg = st.selectbox("Weld Leg (mm)", [4, 6, 8, 10], index=1)
        
        st.markdown("**3. Geometry Check**")
        pitch = 3 * dia
        lev = 1.5 * dia
        st.write(f"Pitch = {pitch} mm")
        st.write(f"Edge Dist = {lev} mm")

    with col_cal:
        # Pre-calc
        db = dia/10
        Ab = math.pi * (db/2)**2
        Fv = 3720 if bolt_gr == "A325" else 1900
        
        # --- CALCULATION STEPS ---
        
        # 1. BOLT SHEAR
        st.markdown('<div class="sub-topic">1. Bolt Shear Strength</div>', unsafe_allow_html=True)
        Rn_bolt = n_rows * Ab * Fv
        st.latex(rf"R_n = n \times A_b \times F_v")
        st.latex(rf"R_n = {n_rows} \times {Ab:.2f} \times {Fv} = \mathbf{{{Rn_bolt:,.0f}}} \ kg")
        st.markdown("")
        
        # 2. BEARING
        st.markdown('<div class="sub-topic">2. Bearing Strength</div>', unsafe_allow_html=True)
        st.write("ตรวจสอบทั้งที่เอวคาน (Web) และแผ่นเหล็ก (Plate) เลือกค่าน้อยกว่า")
        
        Rn_w = n_rows * 1.2 * Fu * db * (tw/10)
        Rn_p = n_rows * 1.2 * Fu * db * (plt_t/10)
        Rn_bear = min(Rn_w, Rn_p)
        
        st.latex(rf"R_{{web}} = {n_rows} \times 1.2 \times {Fu} \times {db} \times {tw/10} = {Rn_w:,.0f} \ kg")
        st.latex(rf"R_{{plate}} = {n_rows} \times 1.2 \times {Fu} \times {db} \times {plt_t/10} = {Rn_p:,.0f} \ kg")
        st.write(f"**Control Bearing = {Rn_bear:,.0f} kg**")
        
        # 3. BLOCK SHEAR
        st.markdown('<div class="sub-topic">3. Block Shear Rupture</div>', unsafe_allow_html=True)
        st.markdown("")
        st.write("การวิบัติแบบฉีกขาดผ่านรูเจาะ (Shear Yield + Tension Rupture)")
        
        # Geo
        Agv = ((lev + (n_rows-1)*pitch)/10) * (plt_t/10)
        Anv = Agv - (n_rows-0.5)*((dia+2)/10)*(plt_t/10)
        Ant = ((40 - 0.5*(dia+2))/10) * (plt_t/10) # Assume Leh=40mm
        
        R1 = 0.6*Fy*Agv + 1.0*Fu*Ant
        R2 = 0.6*Fu*Anv + 1.0*Fu*Ant
        Rn_block = min(R1, R2)
        
        st.latex(rf"A_{{gv}}={Agv:.2f}, \ A_{{nv}}={Anv:.2f}, \ A_{{nt}}={Ant:.2f} \ cm^2")
        st.latex(rf"R_1 = 0.6({Fy})({Agv:.2f}) + {Fu}({Ant:.2f}) = {R1:,.0f} \ kg")
        st.latex(rf"R_2 = 0.6({Fu})({Anv:.2f}) + {Fu}({Ant:.2f}) = {R2:,.0f} \ kg")
        st.write(f"**Block Shear Capacity = {Rn_block:,.0f} kg**")
        
        # 4. WELD
        st.markdown('<div class="sub-topic">4. Weld Strength (Double Fillet)</div>', unsafe_allow_html=True)
        L_weld = (lev + (n_rows-1)*pitch + lev)/10
        Rn_weld = 2 * L_weld * 0.707 * (w_leg/10) * (0.3 * 4900)
        st.latex(rf"L_{{weld}} = {L_weld:.2f} \ cm")
        st.latex(rf"R_{{weld}} = 2 \times {L_weld:.2f} \times 0.707 \times {w_leg/10} \times (0.3 \times 4900)")
        st.write(f"**Weld Capacity = {Rn_weld:,.0f} kg**")
        
        # --- FINAL CHECK ---
        st.markdown("---")
        min_conn_cap = min(Rn_bolt, Rn_bear, Rn_block, Rn_weld)
        
        if min_conn_cap >= V_governing:
            st.markdown(f"""
            <div class="governing-box">
                <h3>✅ CONNECTION PASSED</h3>
                Capacity ({min_conn_cap:,.0f} kg) > Load ({V_governing:,.0f} kg)<br>
                Ratio = {V_governing/min_conn_cap:.2f}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="warning-box">
                <h3>❌ CONNECTION FAILED</h3>
                Capacity ({min_conn_cap:,.0f} kg) < Load ({V_governing:,.0f} kg)<br>
                Please increase Bolt Rows, Diameter, or Plate Thickness.
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown('</div>', unsafe_allow_html=True)

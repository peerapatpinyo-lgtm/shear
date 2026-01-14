import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLING
# ==========================================
st.set_page_config(page_title="Safe Load Table Generator", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .report-header {
        background-color: #1a5276;
        color: white;
        padding: 15px;
        border-radius: 5px;
        text-align: center;
        margin-bottom: 20px;
    }
    .highlight-row {
        background-color: #d4efdf !important;
    }
    .metric-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        background-color: #f8f9f9;
    }
    .optimal-badge {
        background-color: #28a745;
        color: white;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 12px;
    }
    .calc-box {
        font-family: 'Courier New', monospace;
        background-color: #fff;
        border: 1px solid #ddd;
        padding: 15px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA & LOGIC
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

def calculate_capacity(span_m, h, tw, Ix, Zx, Fy, E_val):
    L_cm = span_m * 100
    
    # 1. Shear Limit (Constant)
    Aw = (h/10) * (tw/10)
    V_shear = 0.6 * Fy * Aw
    
    # 2. Moment Limit (Assuming Simple Beam, Uniform Load) -> Converted to Max Reaction V
    # M = wL^2/8, V = wL/2 => M = V(L/2)/2 = VL/4 => V = 4M/L
    M_allow = 0.6 * Fy * Zx
    V_moment = (4 * M_allow) / L_cm
    
    # 3. Deflection Limit (L/360) -> Converted to Max Reaction V
    # Delta = 5wL^4/384EI. V = wL/2.
    # Delta = 5(2V/L)L^4 / 384EI = 10VL^3 / 384EI
    # Limit = L/360
    # L/360 = 10VL^3 / 384EI => V = (384EI)/(3600 L^2)
    V_defl = (384 * E_val * Ix) / (3600 * (L_cm**2))
    
    # Governor
    V_max = min(V_shear, V_moment, V_defl)
    
    if V_max == V_shear: gov = "Shear"
    elif V_max == V_moment: gov = "Moment"
    else: gov = "Deflection"
    
    return V_max, gov

# ==========================================
# 3. SIDEBAR SELECTION
# ==========================================
with st.sidebar:
    st.header("⚙️ Specification")
    df = get_sys_data()
    sec_name = st.selectbox("Select Section", df['Section'], index=6) # Default H400
    
    # Params
    Fy = 2400
    E_val = 2.04e6
    
    # Props
    p = df[df['Section'] == sec_name].iloc[0]
    h, tw, tf, Ix, Zx = p['h'], p['tw'], p['tf'], p['Ix'], p['Zx']
    
    st.info(f"""
    **{sec_name}**
    Depth: {h} mm
    Weight: ~{h*0.1:.1f} kg/m
    """)

# ==========================================
# 4. GENERATE LOAD TABLE (CORE LOGIC)
# ==========================================
st.title("🏗️ Typical Detail: Safe Load Table Generator")
st.markdown("ตารางแนะนำพิกัดรับน้ำหนักปลอดภัย (Safe Working Load) ที่ช่วง 50-70% Efficiency")

# Generate Data for Spans 2m - 15m
table_rows = []
spans = np.arange(2.0, 16.0, 0.5)
d_m = h / 1000

optimal_range_text = ""
opt_min_s, opt_max_s = 0, 0

for s in spans:
    v_max, gov = calculate_capacity(s, h, tw, Ix, Zx, Fy, E_val)
    
    # Optimal Span Check (L/d = 15-20)
    ratio = s / d_m
    is_optimal = 15 <= ratio <= 24 # ยืดหยุ่นนิดหน่อยให้ครอบคลุม
    
    if is_optimal:
        if opt_min_s == 0: opt_min_s = s
        opt_max_s = s
    
    table_rows.append({
        "Span (m)": s,
        "Max Capacity (kg)": v_max,
        "Gov. Mode": gov,
        "Target 50% (kg)": v_max * 0.50,
        "Target 70% (kg)": v_max * 0.70,
        "L/d": ratio,
        "Optimal": "✅" if is_optimal else "-"
    })

df_table = pd.DataFrame(table_rows)

# ==========================================
# 5. DISPLAY MAIN CONTENT
# ==========================================
col_chart, col_table = st.columns([1.5, 1])

with col_chart:
    st.subheader("📈 Load Specification Chart")
    
    # Create Band Chart
    fig = go.Figure()
    
    # 70% Limit Line
    fig.add_trace(go.Scatter(
        x=df_table['Span (m)'], 
        y=df_table['Target 70% (kg)'],
        mode='lines',
        line=dict(width=0),
        showlegend=False,
        name='70% Limit'
    ))
    
    # 50% Limit Line (Filled to 70%)
    fig.add_trace(go.Scatter(
        x=df_table['Span (m)'], 
        y=df_table['Target 50% (kg)'],
        mode='lines',
        fill='tonexty', # Fill area between 50% and 70%
        fillcolor='rgba(40, 167, 69, 0.3)', # Green transparent
        line=dict(width=0),
        name='Effective Zone (50-70%)'
    ))
    
    # Max Capacity Line (Reference)
    fig.add_trace(go.Scatter(
        x=df_table['Span (m)'], 
        y=df_table['Max Capacity (kg)'],
        mode='lines',
        line=dict(color='gray', dash='dash'),
        name='Max Capacity (100%)'
    ))
    
    # Highlight Optimal Span Range
    if opt_max_s > 0:
        fig.add_vrect(
            x0=opt_min_s, x1=opt_max_s,
            fillcolor="yellow", opacity=0.1,
            annotation_text="Optimal Span", annotation_position="top"
        )

    fig.update_layout(
        title=f"Recommended Load Range for {sec_name}",
        xaxis_title="Span Length (m)",
        yaxis_title="Total Reaction Force (kg)",
        hovermode="x unified",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # --- Typical Detail Specification ---
    st.markdown("### 📝 Typical Detail Specification")
    st.info(f"""
    **Section:** {sec_name}
    **Recommended Span:** {opt_min_s} - {opt_max_s} m
    **Design Criteria:** Load Efficiency 50-70% of Capacity
    """)
    st.write("ใช้ข้อมูลในตารางด้านขวาเพื่อระบุลงในแบบก่อสร้าง (Typical Drawing)")

with col_table:
    st.subheader("📋 Safe Load Table")
    
    # Display Format
    st.dataframe(
        df_table.style.format({
            "Span (m)": "{:.1f}",
            "Max Capacity (kg)": "{:,.0f}",
            "Target 50% (kg)": "{:,.0f}",
            "Target 70% (kg)": "{:,.0f}",
            "L/d": "{:.1f}"
        }).apply(lambda x: ['background-color: #d4efdf' if v == "✅" else '' for v in x], subset=["Optimal"]),
        height=600,
        use_container_width=True
    )
    
    st.caption("**Target 50-70%:** ช่วงน้ำหนักบรรทุกแนะนำ (Reaction) ที่ทำให้หน้าตัดทำงานได้คุ้มค่าและปลอดภัยที่สุด")

# ==========================================
# 6. DETAILED CALCULATION (FOR VERIFICATION)
# ==========================================
st.markdown("---")
with st.expander("🔎 เจาะลึกรายการคำนวณที่ระยะ Span (เลือกดูได้)"):
    sel_span = st.slider("Select Span to Check (m)", 2.0, 15.0, 6.0, 0.5)
    
    # Recalculate for display
    L_cm = sel_span * 100
    Aw = (h/10)*(tw/10)
    V_s = 0.6*Fy*Aw
    V_m = (4 * (0.6*Fy*Zx)) / L_cm
    V_d = (384*E_val*Ix) / (3600 * (L_cm**2))
    
    v_final = min(V_s, V_m, V_d)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Calculation Breakdown:**")
        st.write(f"Span: {sel_span} m | L/d: {sel_span*1000/h:.1f}")
        st.latex(rf"V_{{shear}} = {V_s:,.0f} \ kg")
        st.latex(rf"V_{{moment}} = {V_m:,.0f} \ kg")
        st.latex(rf"V_{{defl}} = {V_d:,.0f} \ kg")
        st.markdown(f"**Max Capacity (100%): {v_final:,.0f} kg**")
    
    with c2:
        st.markdown("**Load Recommendation:**")
        st.write(f"50% Utilization: **{v_final*0.5:,.0f} kg**")
        st.write(f"70% Utilization: **{v_final*0.7:,.0f} kg**")
        st.success(f"ช่วง Load ที่ควรระบุในแบบ: **{v_final*0.5:,.0f} - {v_final*0.7:,.0f} kg**")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Section Efficiency Analyzer", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 15px;
        border-radius: 5px;
        text-align: center;
    }
    .explanation-text {
        font-size: 14px;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA
# ==========================================
def get_sys_data():
    data = [
        ("H 150x75x5x7", 150, 75, 5, 7, 666, 88.8),
        ("H 200x100x5.5x8", 200, 100, 5.5, 8, 1840, 184),
        ("H 250x125x6x9", 250, 125, 6, 9, 3690, 295),
        ("H 300x150x6.5x9", 300, 150, 6.5, 9, 7210, 481),
        ("H 350x175x7x11", 350, 175, 7, 11, 13600, 775),
        ("H 400x200x8x13", 400, 200, 8, 13, 23700, 1190),
        ("H 450x200x9x14", 450, 200, 9, 14, 33500, 1490),
        ("H 500x200x10x16", 500, 200, 10, 16, 47800, 1910),
        ("H 600x200x11x17", 600, 200, 11, 17, 77600, 2590),
    ]
    return pd.DataFrame(data, columns=["Section", "h", "b", "tw", "tf", "Ix", "Zx"])

def get_capacity_details(span_m, h, tw, Ix, Zx, Fy=2400, E=2.04e6):
    L_cm = span_m * 100
    
    # 1. Shear (Constant)
    Aw = (h/10)*(tw/10)
    V_shear = 0.6*Fy*Aw
    
    # 2. Moment (Curve 1/L)
    M_allow = 0.6*Fy*Zx
    V_moment = (4*M_allow)/L_cm
    
    # 3. Deflection (Curve 1/L^2)
    V_defl = (384*E*Ix)/(3600*(L_cm**2)) # Based on L/360 limit
    
    # Check Governor
    vals = {'Shear': V_shear, 'Moment': V_moment, 'Deflection': V_defl}
    gov_mode = min(vals, key=vals.get)
    capacity = vals[gov_mode]
    
    return capacity, gov_mode

# ==========================================
# 3. INPUTS
# ==========================================
with st.sidebar:
    st.header("⚙️ Analysis Setup")
    df = get_sys_data()
    sec_name = st.selectbox("Select Section", df['Section'], index=5)
    
    # Get props
    p = df[df['Section'] == sec_name].iloc[0]
    h = p['h']
    
    st.info(f"""
    **{sec_name}**
    Depth (d): {h} mm
    Optimal Span (L/d ≈ 20): {h*20/1000:.1f} m
    """)

# ==========================================
# 4. VISUALIZATION - THE "GOVERNING ZONES"
# ==========================================
st.title("🎯 Structural Efficiency Analysis")
st.write("กราฟนี้แสดงให้เห็นว่าทำไมช่วงความยาว (Span) บางช่วงถึงเหมาะสมที่สุด โดยดูจาก **พฤติกรรมการวิบัติ (Failure Mode)**")

# Calculate data points
spans = np.linspace(1, 15, 100)
results = []
for s in spans:
    cap, mode = get_capacity_details(s, p['h'], p['tw'], p['Ix'], p['Zx'])
    results.append({'span': s, 'cap': cap, 'mode': mode})

df_res = pd.DataFrame(results)

# Create Chart
fig = go.Figure()

# Plot Capacity Line
fig.add_trace(go.Scatter(
    x=df_res['span'], y=df_res['cap'],
    mode='lines', line=dict(color='black', width=3),
    name='Safe Load Limit'
))

# Add Background Zones (Color Coded by Mode)
# เราจะหาจุดเปลี่ยน (Transition Points) ของ Mode
modes = df_res['mode'].values
changes = np.where(modes[:-1] != modes[1:])[0]
boundaries = [df_res['span'].iloc[0]] + df_res['span'].iloc[changes].tolist() + [df_res['span'].iloc[-1]]
zone_colors = {'Shear': 'rgba(255, 0, 0, 0.1)', 'Moment': 'rgba(0, 255, 0, 0.2)', 'Deflection': 'rgba(0, 0, 255, 0.1)'}
zone_labels = {'Shear': 'Short Span (Shear Controls)', 'Moment': 'Optimal Span (Moment Controls)', 'Deflection': 'Long Span (Deflection Controls)'}

last_x = df_res['span'].iloc[0]
for i, change_idx in enumerate(changes):
    mode = modes[change_idx]
    next_x = df_res['span'].iloc[change_idx]
    
    fig.add_vrect(
        x0=last_x, x1=next_x,
        fillcolor=zone_colors.get(mode, 'white'), opacity=1,
        layer="below", line_width=0,
        annotation_text=mode, annotation_position="top left"
    )
    last_x = next_x

# Add last zone
last_mode = modes[-1]
fig.add_vrect(
    x0=last_x, x1=df_res['span'].iloc[-1],
    fillcolor=zone_colors.get(last_mode, 'white'), opacity=1,
    layer="below", line_width=0,
    annotation_text=last_mode, annotation_position="top left"
)

# Add L/d markers
L_d_15 = (15 * h) / 1000
L_d_20 = (20 * h) / 1000

fig.add_vline(x=L_d_15, line_dash="dot", annotation_text="L/d=15", annotation_position="bottom right")
fig.add_vline(x=L_d_20, line_dash="dot", annotation_text="L/d=20", annotation_position="bottom right")

fig.update_layout(
    title=f"Efficiency Zones for {sec_name}",
    xaxis_title="Span Length (m)",
    yaxis_title="Max Load Capacity (kg)",
    height=500,
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 5. EXPLANATION
# ==========================================
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("### 🔴 Shear Zone")
    st.caption("ช่วงสั้นมาก (Short Span)")
    st.write("รับแรงได้มหาศาล แต่พังด้วยแรงเฉือน เหมือนคานลึก (Deep Beam) เป็นช่วงที่ **สิ้นเปลืองเหล็ก**")

with c2:
    st.markdown("### 🟢 Moment Zone (Optimal)")
    st.caption("ช่วงที่เหมาะสม")
    st.write("เป็นช่วงที่หน้าตัดได้ทำงานต้านทานการดัดตัวเต็มที่ (Fully Yield) คุ้มค่าที่สุด มักตรงกับช่วง **L/d 15-20**")

with c3:
    st.markdown("### 🔵 Deflection Zone")
    st.caption("ช่วงยาว (Long Span)")
    st.write("รับแรงได้น้อยลงมาก เพราะถูกจำกัดด้วยระยะแอ่น (Stiffness) คานจะย้วย **ไม่แนะนำ**")

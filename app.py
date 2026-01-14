import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. CONFIG & STYLE
# ==========================================
st.set_page_config(page_title="H-Beam Connection Master", layout="wide", page_icon="🏗️")

# Custom CSS for better cards
st.markdown("""
<style>
    .big-card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #2e86c1; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    .rec-card { background-color: #e8f8f5; padding: 15px; border-radius: 10px; border: 1px solid #a2d9ce; color: #0e6655; }
    .metric-value { font-size: 24px; font-weight: bold; color: #17202a; }
    .metric-label { font-size: 14px; color: #566573; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE (JIS STANDARD)
# ==========================================
steel_db = {
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8,  "w": 14.0},
    "H 175x90x5x8":     {"h": 175, "b": 90,  "tw": 5,   "tf": 8,   "Ix": 1210,   "Zx": 138,   "w": 18.1},
    "H 200x100x5.5x8": {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "w": 21.3},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "w": 29.6},
    "H 300x150x6.5x9": {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 350x175x7x11":  {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "w": 49.6},
    "H 400x200x8x13":  {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 450x200x9x14":  {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "w": 76.0},
    "H 500x200x10x16": {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
    "H 600x200x11x17": {"h": 600, "b": 200, "tw": 11,  "tf": 17,  "Ix": 77600,  "Zx": 2590,  "w": 106},
    "H 700x300x13x24": {"h": 700, "b": 300, "tw": 13,  "tf": 24,  "Ix": 201000, "Zx": 5760,  "w": 185},
    "H 800x300x14x26": {"h": 800, "b": 300, "tw": 14,  "tf": 26,  "Ix": 292000, "Zx": 7300,  "w": 210},
}

# ==========================================
# 3. SIDEBAR (CONTROLS)
# ==========================================
with st.sidebar:
    st.header("🎛️ Design Controls")
    
    # Section Selector
    section_name = st.selectbox("1. เลือกหน้าตัด (Section)", list(steel_db.keys()), index=8) # Default H500
    props = steel_db[section_name]
    
    st.info(f"""
    **{section_name}**
    🔹 Depth (d): {props['h']} mm
    🔹 Web (tw): {props['tw']} mm
    🔹 Zx: {props['Zx']:,} cm³
    """)
    
    # Bolt Selector
    bolt_size = st.selectbox("2. ขนาด Bolt", ["M16", "M20", "M22", "M24"], index=1)
    
    # Material Props
    fy = st.number_input("Fy (ksc)", value=2400)
    st.caption("Standard SS400 (Fy=2400 ksc)")

# ==========================================
# 4. CALCULATION LOGIC
# ==========================================
# A. Capacities
h_cm = props['h']/10
tw_cm = props['tw']/10
Aw = h_cm * tw_cm

# Max Web Shear (Limit สูงสุดของเหล็ก)
V_max_web = 0.4 * fy * Aw 

# Moment Capacity
M_allow = 0.6 * fy * props['Zx'] # kg.cm

# Bolt Capacity (Single Shear vs Bearing)
bolt_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
dia_cm = int(bolt_size[1:]) / 10

# 1. Shear Strength (Approx 1.0 ton/cm2 per leg)
phi_shear = 1000 * bolt_areas[bolt_size] 
# 2. Bearing Strength (1.2 Fu d t)
phi_bearing = 1.2 * 4000 * dia_cm * tw_cm # SS400 Fu=4000

bolt_cap = min(phi_shear, phi_bearing)
gov_mode = "Shear" if phi_shear < phi_bearing else "Bearing"

# ==========================================
# 5. GENERATE DATA FOR GRAPH
# ==========================================
# สร้างช่วง Span จากสั้นมาก (2D) ไปยาวมาก (30D)
depth_m = props['h'] / 1000
spans = np.linspace(depth_m*2, depth_m*30, 100) # meter

v_list = []
limit_type = []

for L in spans:
    # V from Moment Control: V = 4*M / L
    V_from_M = (4 * (M_allow/100)) / (L * 100) * 1000 # kg
    
    if V_from_M > V_max_web:
        v_list.append(V_max_web)
        limit_type.append("Shear Limit (Web)")
    else:
        v_list.append(V_from_M)
        limit_type.append("Moment Limit (Span)")

df_chart = pd.DataFrame({"Span": spans, "V_design": v_list, "Limit": limit_type})

# จุด Typical 10D
L_10d = depth_m * 10
V_10d = (4 * M_allow) / (L_10d * 100) # kg
if V_10d > V_max_web: V_10d = V_max_web

# ==========================================
# 6. MAIN DISPLAY
# ==========================================
st.title("🔩 Typical Connection Designer")
st.markdown("### วิเคราะห์หาจุดคุ้มค่าสำหรับการทำแบบมาตรฐาน (Typical Detail)")

# --- Top Cards: The Answer ---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="big-card">
        <div class="metric-label">🚧 Max Web Capacity</div>
        <div class="metric-value" style="color:#e74c3c;">{V_max_web/1000:,.1f} Tons</div>
        <div class="metric-label">ขีดจำกัดสูงสุดของเอวคาน</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="big-card" style="border-left: 5px solid #27ae60;">
        <div class="metric-label">✅ Recommended Design Load</div>
        <div class="metric-value" style="color:#27ae60;">{V_10d/1000:,.1f} Tons</div>
        <div class="metric-label">ที่ Span {L_10d:.1f} ม. (10D)</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    req_bolts = math.ceil(V_10d / bolt_cap)
    st.markdown(f"""
    <div class="big-card" style="border-left: 5px solid #f39c12;">
        <div class="metric-label">🔩 Standard Bolt Qty</div>
        <div class="metric-value" style="color:#d35400;">{req_bolts} x {bolt_size}</div>
        <div class="metric-label">Gov: {gov_mode} ({bolt_cap:,.0f} kg/ตัว)</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- Middle: The "Efficiency Curve" (ไฮไลท์ของรอบนี้) ---
c_graph, c_table = st.columns([2, 1])

with c_graph:
    st.subheader("📈 กราฟความสัมพันธ์ Span vs Design Shear")
    
    fig = go.Figure()
    
    # 1. เส้นหลัก (V Design)
    fig.add_trace(go.Scatter(
        x=df_chart['Span'], y=df_chart['V_design']/1000,
        mode='lines', name='Design Shear Capacity',
        line=dict(color='#2E86C1', width=4),
        fill='tozeroy', fillcolor='rgba(46, 134, 193, 0.1)'
    ))
    
    # 2. เส้น Web Limit (สีแดงประ)
    fig.add_trace(go.Scatter(
        x=[spans[0], spans[-1]], y=[V_max_web/1000, V_max_web/1000],
        mode='lines', name='Max Web Limit',
        line=dict(color='red', dash='dash', width=2)
    ))
    
    # 3. จุด Typical 10D
    fig.add_trace(go.Scatter(
        x=[L_10d], y=[V_10d/1000],
        mode='markers+text', name='Recommended Point (10D)',
        marker=dict(size=15, color='#27ae60', symbol='diamond', line=dict(color='white', width=2)),
        text=[f"{V_10d/1000:.1f}T"], textposition="top right"
    ))
    
    # Annotations Zones (FIXED: Changed 'top center' to 'top' or 'inside top')
    fig.add_vrect(x0=spans[0], x1=depth_m*8, fillcolor="red", opacity=0.05, annotation_text="Deep Beam Zone", annotation_position="top left")
    fig.add_vrect(x0=depth_m*8, x1=depth_m*15, fillcolor="green", opacity=0.05, annotation_text="Typical Zone", annotation_position="top")
    fig.add_vrect(x0=depth_m*15, x1=spans[-1], fillcolor="blue", opacity=0.05, annotation_text="Economical Zone", annotation_position="top right")

    fig.update_layout(
        xaxis_title="Beam Span Length (m)",
        yaxis_title="Design Shear Force (Ton)",
        hovermode="x unified",
        height=450,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
    )
    st.plotly_chart(fig, use_container_width=True)

with c_table:
    st.subheader("📋 Bolt Quantity Matrix")
    st.caption(f"จำนวนน็อต {bolt_size} ที่ต้องใช้ตามระดับแรงเฉือน")
    
    # สร้างตาราง Bolt Steps
    steps = []
    # สร้าง Step จาก 100% ลงไป 20% ของ Web Cap
    percentages = [1.0, 0.8, 0.6, 0.5, 0.4, 0.3]
    
    for p in percentages:
        load = V_max_web * p
        nb = math.ceil(load / bolt_cap)
        remark = ""
        if p == 1.0: remark = "Max Cap"
        elif 0.45 <= p <= 0.55: remark = "⭐ Typical (10D)"
        elif p <= 0.3: remark = "Long Span"
        
        steps.append({
            "% Web": f"{p*100:.0f}%",
            "Load (Ton)": f"{load/1000:.1f}",
            "Bolts": f"{nb}",
            "Note": remark
        })
        
    df_steps = pd.DataFrame(steps)
    
    # Stylize Table
    st.dataframe(
        df_steps,
        column_config={
            "% Web": st.column_config.TextColumn("Web Use"),
            "Load (Ton)": st.column_config.NumberColumn("Load Limit", format="%.1f T"),
            "Bolts": st.column_config.TextColumn("Qty Used", help="จำนวนน็อตขั้นต่ำ"),
        },
        hide_index=True,
        use_container_width=True
    )
    
    st.markdown("""
    <div class="rec-card">
    <b>💡 Design Insight:</b><br>
    ไม่ต้องทำ Detail รองรับ 100% Web Capacity ก็ได้! <br>
    สังเกตที่ <b>50% (⭐ Typical)</b> คือจุดที่คุ้มค่าที่สุด ครอบคลุม Span ส่วนใหญ่แล้ว
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 7. TYPICAL DETAIL DRAWING (Simple Concept)
# ==========================================
st.markdown("### 📐 Typical Detail Visualization")
st.caption(f"แสดงการจัดเรียงน็อตสำหรับแรง Typical Load ({req_bolts} bolts)")

def draw_layout_simple(n):
    if n == 0: return go.Figure()
    cols = 2 if n > 3 else 1
    rows = math.ceil(n / cols)
    
    fig = go.Figure()
    
    # Plate
    w = 160 if cols==2 else 80
    h = rows * 70 + 20
    fig.add_shape(type="rect", x0=0, y0=0, x1=w, y1=h, line=dict(color="black"), fillcolor="#D5D8DC")
    
    # Bolts
    for r in range(rows):
        y = h - 40 - (r*70)
        if cols == 1:
            fig.add_trace(go.Scatter(x=[w/2], y=[y], mode='markers', marker=dict(size=12, color='black')))
        else:
            # 2 cols
            idx = r * 2
            if idx < n: # Left
                fig.add_trace(go.Scatter(x=[40], y=[y], mode='markers', marker=dict(size=12, color='black')))
            if idx + 1 < n: # Right
                fig.add_trace(go.Scatter(x=[120], y=[y], mode='markers', marker=dict(size=12, color='black')))
                
    fig.update_layout(
        showlegend=False, xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"),
        height=300, margin=dict(l=0,r=0,t=0,b=0), plot_bgcolor="white"
    )
    return fig

col_draw1, col_draw2 = st.columns([1, 3])
with col_draw1:
    st.plotly_chart(draw_layout_simple(req_bolts), use_container_width=True)
with col_draw2:
    st.markdown(f"""
    **Standard Detail Specification:**
    * **Beam:** {section_name}
    * **Design Load:** {V_10d/1000:.1f} Tons
    * **Connection:** {req_bolts} - {bolt_size} (Grade A325/F10T)
    * **Plate:** Min Thickness {max(9, math.ceil(props['tw']))} mm (SS400)
    * **Notes:** ใช้สำหรับคานที่มีความยาวตั้งแต่ **{L_10d:.1f} ม.** ขึ้นไป (ถ้าคานสั้นกว่านี้ ต้องคำนวณแยก)
    """)

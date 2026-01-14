import streamlit as st
import pandas as pd

# ==========================================
# 1. SETUP
# ==========================================
st.set_page_config(page_title="Typical Detail Spec", layout="centered")

# CSS สำหรับกรอบข้อความผลลัพธ์แบบชัดเจน
st.markdown("""
<style>
    .spec-card {
        background-color: #e8f8f5;
        border: 2px solid #1abc9c;
        border-radius: 10px;
        padding: 30px;
        text-align: center;
        margin-top: 20px;
    }
    .spec-title {
        color: #148f77;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .spec-value {
        font-size: 36px;
        font-weight: bold;
        color: #000;
        margin: 10px 0;
    }
    .spec-desc {
        font-size: 16px;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA & LOGIC
# ==========================================
def get_data():
    # Section, h(mm), Ix(cm4), Zx(cm3)
    return pd.DataFrame([
        ("H 150x75x5x7", 150, 666, 88.8),
        ("H 200x100x5.5x8", 200, 1840, 184),
        ("H 250x125x6x9", 250, 3690, 295),
        ("H 300x150x6.5x9", 300, 7210, 481),
        ("H 350x175x7x11", 350, 13600, 775),
        ("H 400x200x8x13", 400, 23700, 1190),
        ("H 500x200x10x16", 500, 47800, 1910),
        ("H 600x200x11x17", 600, 77600, 2590),
    ], columns=["Section", "h", "Ix", "Zx"])

def calculate_spec(h, Ix, Zx):
    # 1. หา Optimal Span Range (L/d = 15 ถึง 20)
    # นี่คือ Engineering Standard ที่ดีที่สุดสำหรับ typical detail
    min_span_m = (15 * h) / 1000
    max_span_m = (20 * h) / 1000
    
    # 2. หา Capacity ที่ระยะที่ "แย่ที่สุด" ในช่วงนั้น (คือระยะ max_span_m)
    # เพื่อความปลอดภัย เราจะใช้ความยาวมากสุดในการหา Load
    span_check = max_span_m 
    L_cm = span_check * 100
    Fy = 2400
    E = 2.04e6
    
    # Check Moment (Reaction form point load approximation: V = 4M/L)
    M_allow = 0.6 * Fy * Zx
    V_mom = (4 * M_allow) / L_cm
    
    # Check Deflection (L/360 limit: V = 48EI / 360L^2)
    V_defl = (48 * E * Ix) / (360 * (L_cm**2))
    
    # Max Capacity (100%)
    V_max = min(V_mom, V_defl)
    
    # 3. Target 50-70%
    load_50 = V_max * 0.50
    load_70 = V_max * 0.70
    
    return min_span_m, max_span_m, load_50, load_70

# ==========================================
# 3. INTERFACE
# ==========================================
st.title("🏗️ Typical Detail Generator")
st.write("เลือกหน้าตัด $\\to$ รับค่าสเปคสำหรับทำแบบ")

# Input
df = get_data()
sec_name = st.selectbox("เลือกหน้าตัด (Section):", df['Section'], index=5)

# Process
row = df[df['Section'] == sec_name].iloc[0]
s_min, s_max, l_50, l_70 = calculate_spec(row['h'], row['Ix'], row['Zx'])

# Output (The Answer)
st.markdown("---")

# สร้าง HTML String อย่างระมัดระวังเพื่อป้องกัน Syntax Error
html_content = f"""
<div class="spec-card">
    <div class="spec-title">SPECIFICATION FOR: {sec_name}</div>
    <div style="display:flex; justify-content:space-around; margin-top:20px;">
        <div>
            <div class="spec-desc">ความยาวช่วงที่เหมาะสม (Optimal Span)</div>
            <div class="spec-value">{s_min:.1f} - {s_max:.1f} <span style="font-size:20px">m</span></div>
            <div class="spec-desc">(Calculated from L/d 15-20)</div>
        </div>
        <div style="border-left: 2px solid #ccc;"></div>
        <div>
            <div class="spec-desc">น้ำหนักบรรทุกปลอดภัย (Safe Load)</div>
            <div class="spec-value">{l_50:,.0f} - {l_70:,.0f} <span style="font-size:20px">kg</span></div>
            <div class="spec-desc">(Target 50-70% Capacity)</div>
        </div>
    </div>
</div>
"""

st.markdown(html_content, unsafe_allow_html=True)

st.warning(f"""
**หมายเหตุสำหรับ Typical Detail:**
ข้อมูลด้านบนคือค่าที่แนะนำสำหรับหน้าตัด **{sec_name}** เมื่อระบุในแบบ ให้ใช้ช่วงความยาว **{s_min:.1f}-{s_max:.1f} ม.** และระบุพิกัดรับน้ำหนัก (Reaction) ไม่เกิน **{l_70:,.0f} กก.** เพื่อความคุ้มค่าและความปลอดภัย
""")

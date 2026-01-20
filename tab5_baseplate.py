import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    # --- 1. DATA SOURCE (H-Beam Properties) ---
    h, b = res_ctx['h'], res_ctx['b']
    tw, tf = res_ctx['tw'], res_ctx['tf']
    
    # --- 2. INPUT INTERFACE ---
    with st.container(border=True):
        st.markdown("##### 🛠️ Full Base Plate Configuration")
        c1, c2, c3 = st.columns(3)
        N = c1.number_input("Plate Length N (mm)", value=float(math.ceil(h + 200)))
        B = c2.number_input("Plate Width B (mm)", value=float(math.ceil(b + 200)))
        tp = c3.number_input("Plate Thick (mm)", value=25.0)
        
        c4, c5, c6 = st.columns(3)
        sx = c4.number_input("Bolt Spacing X (mm)", value=b+100)
        sy = c5.number_input("Bolt Spacing Y (mm)", value=h+100)
        bolt_dia = c6.selectbox("Bolt Size (mm)", [16, 20, 24, 30], index=1)

    # --- 3. ENGINEERING ANALYSIS ---
    # ระยะขอบ (Edge Distance)
    ex = (B - sx) / 2
    ey = (N - sy) / 2
    
    # ระยะห่างจากหน้าตัดเสา (Clearance for Wrench)
    clr_x = (sx - b) / 2
    clr_y = (sy - tw) / 2
    
    # ความปลอดภัย (Min Edge Distance AISC = 1.5d)
    min_e_req = bolt_dia * 1.5
    is_safe = ex >= min_e_req and ey >= min_e_req

    # --- 4. MASTER BLUEPRINT (SVG) ---
    sc = 320 / max(N, B)  # Scaling factor
    cv_w, cv_h = 900, 900 # Canvas size
    cx, cy = 450, 420     # Drawing Center
    
    svg = f"""
    <div style="display:flex; justify-content:center; background:#ffffff; padding:25px; border:2px solid #0f172a; border-radius:12px;">
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <text x="30" y="40" font-family="sans-serif" font-size="22" font-weight="bold" fill="#0f172a">MASTER BASE PLATE SETTING-OUT PLAN</text>
        <line x1="30" y1="55" x2="650" y2="55" stroke="#0f172a" stroke-width="3"/>
        <text x="30" y="75" font-family="sans-serif" font-size="12" fill="#64748b">SCALE: NTS. | UNIT: MILLIMETERS (mm)</text>

        <g stroke="#94a3b8" stroke-width="1" stroke-dasharray="15,5,2,5">
            <line x1="{cx - B*sc/2 - 50}" y1="{cy}" x2="{cx + B*sc/2 + 50}" y2="{cy}"/> 
            <line x1="{cx}" y1="{cy - N*sc/2 - 50}" x2="{cx}" y2="{cy + N*sc/2 + 50}"/>
        </g>

        <rect x="{cx - B*sc/2}" y="{cy - N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#f1f5f9" stroke="#000" stroke-width="3"/>
        
        <g transform="translate({cx}, {cy})" fill="#cbd5e1" stroke="#000" stroke-width="2">
            <rect x="{-b/2*sc}" y="{-h/2*sc}" width="{b*sc}" height="{tf*sc}"/> <rect x="{-b/2*sc}" y="{(h/2-tf)*sc}" width="{b*sc}" height="{tf*sc}"/> <rect x="{-tw/2*sc}" y="{-h/2*sc + tf*sc}" width="{tw*sc}" height="{(h-2*tf)*sc}"/> </g>

        <g stroke="#3b82f6" stroke-width="2.5">
            <circle cx="{cx - sx/2*sc}" cy="{cy - sy/2*sc}" r="12" fill="white"/>
            <circle cx="{cx + sx/2*sc}" cy="{cy - sy/2*sc}" r="12" fill="white"/>
            <circle cx="{cx - sx/2*sc}" cy="{cy + sy/2*sc}" r="12" fill="white"/>
            <circle cx="{cx + sx/2*sc}" cy="{cy + sy/2*sc}" r="12" fill="white"/>
            <path d="M{cx - sx/2*sc - 15} {cy - sy/2*sc} h30 M{cx - sx/2*sc} {cy - sy/2*sc - 15} v30" stroke-width="1"/>
            <path d="M{cx + sx/2*sc - 15} {cy - sy/2*sc} h30 M{cx + sx/2*sc} {cy - sy/2*sc - 15} v30" stroke-width="1"/>
            <path d="M{cx - sx/2*sc - 15} {cy + sy/2*sc} h30 M{cx - sx/2*sc} {cy + sy/2*sc - 15} v30" stroke-width="1"/>
            <path d="M{cx + sx/2*sc - 15} {cy + sy/2*sc} h30 M{cx + sx/2*sc} {cy + sy/2*sc - 15} v30" stroke-width="1"/>
        </g>

        <g stroke="#1e293b" stroke-width="1.2" font-family="monospace" font-size="13">
            <line x1="{cx - B*sc/2}" y1="{cy - N*sc/2 - 80}" x2="{cx + B*sc/2}" y2="{cy - N*sc/2 - 80}"/>
            <text x="{cx}" y="{cy - N*sc/2 - 90}" text-anchor="middle" font-weight="bold">B = {B}</text>
            
            <line x1="{cx - sx/2*sc}" y1="{cy - N*sc/2 - 45}" x2="{cx + sx/2*sc}" y2="{cy - N*sc/2 - 45}"/>
            <text x="{cx}" y="{cy - N*sc/2 - 55}" text-anchor="middle" fill="#3b82f6">Sx = {sx}</text>

            <line x1="{cx - B*sc/2}" y1="{cy - N*sc/2 - 20}" x2="{cx - sx/2*sc}" y2="{cy - N*sc/2 - 20}" stroke="#16a34a"/>
            <text x="{cx - (B/2 + sx/2)/2*sc}" y="{cy - N*sc/2 - 25}" text-anchor="middle" fill="#16a34a">ex:{ex}</text>
            <line x1="{cx + sx/2*sc}" y1="{cy - N*sc/2 - 20}" x2="{cx + B*sc/2}" y2="{cy - N*sc/2 - 20}" stroke="#16a34a"/>
            <text x="{cx + (B/2 + sx/2)/2*sc}" y="{cy - N*sc/2 - 25}" text-anchor="middle" fill="#16a34a">ex:{ex}</text>
        </g>

        <g stroke="#1e293b" stroke-width="1.2" font-family="monospace" font-size="13">
            <line x1="{cx - B*sc/2 - 80}" y1="{cy - N*sc/2}" x2="{cx - B*sc/2 - 80}" y2="{cy + N*sc/2}"/>
            <text x="{cx - B*sc/2 - 90}" y="{cy}" transform="rotate(-90 {cx-B*sc/2-90} {cy})" text-anchor="middle" font-weight="bold">N = {N}</text>

            <line x1="{cx - B*sc/2 - 50}" y1="{cy - sy/2*sc}" x2="{cx - B*sc/2 - 50}" y2="{cy + sy/2*sc}"/>
            <text x="{cx - B*sc/2 - 60}" y="{cy}" transform="rotate(-90 {cx-B*sc/2-60} {cy})" text-anchor="middle" fill="#3b82f6">Sy = {sy}</text>

            <line x1="{cx - B*sc/2 - 20}" y1="{cy - N*sc/2}" x2="{cx - B*sc/2 - 20}" y2="{cy - sy/2*sc}" stroke="#16a34a"/>
            <text x="{cx - B*sc/2 - 25}" y="{cy - (N/2+sy/2)/2*sc}" text-anchor="middle" transform="rotate(-90 {cx-B*sc/2-25} {cy - (N/2+sy/2)/2*sc})" fill="#16a34a">ey:{ey}</text>
            <line x1="{cx - B*sc/2 - 20}" y1="{cy + sy/2*sc}" x2="{cx - B*sc/2 - 20}" y2="{cy + N*sc/2}" stroke="#16a34a"/>
            <text x="{cx - B*sc/2 - 25}" y="{cy + (N/2+sy/2)/2*sc}" text-anchor="middle" transform="rotate(-90 {cx-B*sc/2-25} {cy + (N/2+sy/2)/2*sc})" fill="#16a34a">ey:{ey}</text>
        </g>

        <g stroke="#ef4444" stroke-width="1" stroke-dasharray="4,2" font-size="11">
            <line x1="{cx + b/2*sc}" y1="{cy + 30}" x2="{cx + sx/2*sc}" y2="{cy + 30}"/>
            <text x="{cx + (b/2+sx/2)/2*sc}" y="{cy + 25}" text-anchor="middle" fill="#ef4444">Clr:{clr_x}mm</text>
        </g>

        <g transform="translate(580, 680)">
            <rect x="0" y="0" width="280" height="180" fill="#f8fafc" stroke="#0f172a" stroke-width="2"/>
            <text x="15" y="30" font-family="sans-serif" font-weight="bold" font-size="14">FABRICATION SCHEDULE</text>
            <line x1="15" y1="40" x2="265" y2="40" stroke="#cbd5e1" stroke-width="1"/>
            <text x="15" y="65" font-family="monospace" font-size="12">PLATE : {B}x{N}x{tp} mm</text>
            <text x="15" y="85" font-family="monospace" font-size="12">HOLES : 4-Ø{bolt_dia+6} (Oversized)</text>
            <text x="15" y="105" font-family="monospace" font-size="12">MIN_E : {min_e_req} mm (AISC)</text>
            <text x="15" y="135" font-family="sans-serif" font-weight="bold" fill="{"#16a34a" if is_safe else "#dc2626"}">
                {"VERDICT: OK" if is_safe else "VERDICT: EDGE TOO THIN!"}
            </text>
        </g>
        
        <g transform="translate(30, 830)" font-family="sans-serif" font-size="11" fill="#475569">
            <rect x="0" y="0" r="3" width="10" height="10" fill="#3b82f6"/> <text x="15" y="9">Bolt Spacing</text>
            <rect x="100" y="0" r="3" width="10" height="10" fill="#16a34a"/> <text x="115" y="9">Edge Distance</text>
            <rect x="210" y="0" r="3" width="10" height="10" fill="#ef4444"/> <text x="225" y="9">Clearance</text>
        </g>
    </svg>
    </div>
    """
    components.html(svg, height=920)

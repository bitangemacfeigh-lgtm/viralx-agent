import streamlit as st
import asyncio
import sqlite3
import re
from datetime import datetime
import requests
import io
import time
from PIL import Image, ImageDraw, ImageFont
from streamlit_javascript import st_javascript  # Needs 'streamlit-javascript' in requirements.txt
from agent import execute_agent_prompt

# 1. Claude-inspired General Page Setup (Stripping out tech branding)
st.set_page_config(
    page_title="ViralX // Assistant", 
    page_icon="💀", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom injection for clean, responsive chat styling on mobile and desktop
st.markdown("""
    <style>
    /* Desktop Max Width Control */
    .stApp { 
        max-width: 800px; 
        margin: 0 auto; 
    }
    
    /* Base chat message styling */
    [data-testid="stChatMessage"] { 
        border-radius: 12px; 
        padding: 1rem; 
        margin-bottom: 1rem; 
    }

    /* Mobile screen adjustments (under 768px) */
    @media (max-width: 768px) {
        .stApp {
            padding-left: 10px;
            padding-right: 10px;
        }
        h1 {
            font-size: 1.8rem !important;
        }
        [data-testid="stChatMessage"] {
            padding: 0.6rem;
            font-size: 14px;
            margin-bottom: 0.6rem;
        }
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 6rem !important;
        }
    }
    
    /* Terminal Loading Box Styling */
    .terminal-loader {
        background-color: #0c0c0c;
        border: 1px solid #ff2e59;
        border-radius: 8px;
        padding: 15px;
        font-family: 'Courier New', Courier, monospace;
        color: #f5f5f5;
        margin-bottom: 15px;
        font-size: 14px;
        line-height: 1.5;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 📊 TELEMETRY ENGINE & SECURITY SETUP
# ==========================================
# Start tracking the active session duration immediately
if "session_start" not in st.session_state:
    st.session_state.session_start = datetime.utcnow()

# Your Admin Password to unlock the dashboard at the bottom of the page
ADMIN_PASSWORD = "ViralXAdmin2026!"
DB_FILE = "viralx_stats.db"

def init_db():
    """Initializes the telemetry database locally."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            prompt TEXT,
            bdi INTEGER,
            response TEXT,
            location TEXT,
            time_spent_seconds REAL
        )
    """)
    conn.commit()
    conn.close()

def get_client_ip():
    """Extracts the true public IP address of the user using JS client-side lookup as a guaranteed fallback."""
    # 1. Fallback 1: Attempt client-side browser JS request (Bypasses all server proxies)
    try:
        js_ip = st_javascript("await fetch('https://api.ipify.org?format=json').then(r => r.json()).then(d => d.ip)")
        if js_ip and js_ip != 0 and "127.0.0.1" not in str(js_ip) and "::1" not in str(js_ip):
            return str(js_ip).strip()
    except Exception:
        pass

    # 2. Fallback 2: Streamlit's proxy headers
    try:
        headers = st.context.headers
        if headers:
            xff = headers.get("X-Forwarded-For") or headers.get("x-forwarded-for")
            if xff:
                true_ip = xff.split(",")[0].strip()
                if not true_ip.startswith("10.") and not true_ip.startswith("172.") and not true_ip.startswith("192.") and "127.0.0.1" not in true_ip:
                    return true_ip
            
            for header_key in ["X-Real-IP", "x-real-ip", "CF-Connecting-IP", "cf-connecting-ip"]:
                val = headers.get(header_key)
                if val and "127.0.0.1" not in val:
                    return val

        st_ip = st.context.ip_address
        if st_ip and not st_ip.startswith("10.") and "127.0.0.1" not in st_ip and "::1" not in st_ip:
            return st_ip
    except Exception:
        pass
        
    return "Unknown IP"

def get_ip_location(ip):
    """Resolves a public IP address to a physical location."""
    if not ip or ip == "Unknown IP" or ip.startswith("10.") or ip.startswith("127.") or ip.startswith("172.") or "::1" in ip or "127.0.0.1" in ip:
        return "Local/Internal IP"
        
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                city = data.get("city", "")
                country = data.get("country", "")
                return f"{city}, {country}" if city else country
    except Exception:
        pass
    return "Unknown Country"

def get_user_location():
    """Combines IP extraction and geolocation for saving."""
    user_ip = get_client_ip()
    user_location = get_ip_location(user_ip)
    return f"{user_ip} ({user_location})"

def log_interaction(prompt: str, response: str):
    """Saves the user's prompt, response, location, and elapsed time."""
    bdi_match = re.search(r'(\d+)%', response)
    bdi_val = int(bdi_match.group(1)) if bdi_match else None
    
    elapsed_time = (datetime.utcnow() - st.session_state.session_start).total_seconds()
    location = get_user_location()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO interactions (timestamp, prompt, bdi, response, location, time_spent_seconds) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.utcnow().isoformat(), prompt, bdi_val, response, location, elapsed_time))
    conn.commit()
    conn.close()

def get_stats():
    """Retrieves computed statistics and lists the latest logs."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), AVG(bdi), AVG(time_spent_seconds) FROM interactions")
    total_chats, avg_bdi, avg_time = cursor.fetchone()
    
    avg_bdi = round(avg_bdi, 1) if avg_bdi is not None else 0
    avg_time = round(avg_time, 1) if avg_time is not None else 0
    
    cursor.execute("""
        SELECT timestamp, prompt, bdi, location, time_spent_seconds 
        FROM interactions 
        ORDER BY id DESC LIMIT 15
    """)
    recent_logs = cursor.fetchall()
    conn.close()
    return total_chats, avg_bdi, avg_time, recent_logs

def get_leaderboard():
    """Fetches the top 5 brutal inputs based on BDI scores for public display."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT prompt, bdi 
            FROM interactions 
            WHERE bdi IS NOT NULL 
            ORDER BY bdi DESC, id DESC 
            LIMIT 5
        """)
        leaders = cursor.fetchall()
        conn.close()
        return leaders
    except Exception:
        return []

# Run database schema verification
init_db()


# ==========================================
# 🎨 LIGHTWEIGHT ROAST CARD GENERATOR
# ==========================================
def generate_roast_card(query: str, bdi_score: int, roast_text: str) -> bytes:
    """Generates a modern, high-contrast digital card for socials using Pillow."""
    # Base configuration values
    width, height = 800, 600
    bg_color = (15, 15, 15)       # Ultra dark grey
    accent_color = (255, 46, 99)   # Hot Neon Pink
    text_color = (245, 245, 245)   # Off-white
    dim_color = (150, 150, 150)    # Soft gray
    
    # Create image canvas
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw double card frame border
    draw.rectangle([15, 15, width - 15, height - 15], outline=accent_color, width=2)
    draw.rectangle([22, 22, width - 22, height - 22], outline=(30, 30, 30), width=1)
    
    # Load fonts cleanly
    try:
        title_font = ImageFont.load_default(size=28)
        body_font = ImageFont.load_default(size=20)
        small_font = ImageFont.load_default(size=14)
    except Exception:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        
    # Draw Header Elements
    draw.text((40, 45), "💀 VIRALX AGENT // REALITY CHECK", fill=accent_color, font=title_font)
    draw.line([(40, 85), (width - 40, 85)], fill=(40, 40, 40), width=1)
    
    # Draw User Query Block
    draw.text((40, 105), "SUBJECT OF EVALUATION:", fill=dim_color, font=small_font)
    truncated_query = query[:50] + "..." if len(query) > 50 else query
    draw.text((40, 125), f'"{truncated_query}"', fill=text_color, font=title_font)
    
    # Draw BDI Score Bar
    draw.text((40, 195), "📈 BRAIN DAMAGE INDEX:", fill=dim_color, font=small_font)
    draw.text((250, 192), f"{bdi_score}%", fill=accent_color, font=body_font)
    
    # Progress Bar background
    draw.rectangle([40, 225, width - 40, 240], fill=(30, 30, 30))
    # Active fill
    fill_width = int(40 + (width - 80) * (bdi_score / 100.0))
    draw.rectangle([40, 225, fill_width, 240], fill=accent_color)
    
    # Draw Wrapped Roast Content (Simple wrap implementation)
    draw.text((40, 275), "💀 THE ANALYSIS:", fill=dim_color, font=small_font)
    
    clean_roast = roast_text.replace("💀 THE BRUTAL ROAST", "").replace("📈 BRAIN DAMAGE INDEX", "").strip()
    words = clean_roast.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        # Wrap threshold
        if len(" ".join(current_line)) > 58:
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]
    lines.append(" ".join(current_line))
    
    y_offset = 305
    for line in lines[:8]:  # Limit to 8 lines on card to prevent overflowing boundaries
        draw.text((40, y_offset), line, fill=text_color, font=body_font)
        y_offset += 28
        
    # Draw Watermark at the bottom
    draw.text((40, height - 55), "GENERATE YOURS AT: bitangemacfeigh-lgtm-viralx-agent-app-yluloq.streamlit.app", fill=dim_color, font=small_font)
    
    byte_io = io.BytesIO()
    img.save(byte_io, format="PNG")
    return byte_io.getvalue()


# ==========================================
# 📱 USER INTERFACE RENDER
# ==========================================

# 2. Top Navigation Bar (General Purpose Branding)
col1, col2 = st.columns([7, 3])
with col1:
    st.title("💀 ViralX Agent")
with col2:
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_start = datetime.utcnow()
        st.rerun()

# --- NEW ADDITION: 🎨 CUSTOM PAIN PROFILES ---
st.write("### Choose Your Flavor of Pain")
personality_mode = st.segmented_control(
    "Select Assistant Personality:",
    options=["💀 Default Savage", "💼 Corporate Savage", "🎓 Intellectual Elitist", "🧠 Brainrot Overdose"],
    default="💀 Default Savage",
    label_visibility="collapsed"
)
st.divider()

# 3. Initialize Persistent Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. Render the Ongoing Thread Flow
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # If it's an assistant response, offer an instant PNG Download Card option
        if message["role"] == "assistant" and "System Error" not in message["content"] and "Execution Fault" not in message["content"]:
            # Parse metrics from prompt history mapping
            linked_query = st.session_state.messages[idx - 1]["content"] if idx > 0 else "Evaluation Topic"
            bdi_match = re.search(r'(\d+)%', message["content"])
            bdi_val = int(bdi_match.group(1)) if bdi_match else 100
            
            try:
                card_png = generate_roast_card(linked_query, bdi_val, message["content"])
                st.download_button(
                    label="📥 Download Roast Card PNG",
                    data=card_png,
                    file_name=f"ViralX_Roast_{idx}.png",
                    mime="image/png",
                    key=f"dl_btn_{idx}"
                )
            except Exception as e:
                pass

# 5. Bottom Space Chat Input Gateway (Open-ended & Random Input)
if prompt := st.chat_input("Drop anything here—a concept, a trend, a place, or a bad habit..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Create dedicated live terminal simulation container
        terminal_placeholder = st.empty()
        
        terminal_steps = [
            "[SYSTEM] Initializing telemetry handshake...",
            "[SYSTEM] Fetching subject background file...",
            "[SYSTEM] Parsing personal vanity metrics...",
            "[SYSTEM] Locating moral compromise parameters...",
            "[SYSTEM] Quantifying self-deception coefficients...",
            "[SYSTEM] Generating tailored existential dread... 🔥"
        ]
        
        running_terminal_logs = ""
        for step in terminal_steps:
            running_terminal_logs += f"{step}<br>"
            terminal_placeholder.markdown(f"""
                <div class="terminal-loader">
                    {running_terminal_logs}
                    <span style='color: #ff2e59; font-weight: bold;'>⚡ ANALYZING...</span>
                </div>
            """, unsafe_allow_html=True)
            time.sleep(0.4)  # Natural visual pacing for the diagnostic output
            
        # Construct modified instructional system framework based on selected Pain Profile
        if personality_mode == "💼 Corporate Savage":
            style_direction = "Adopt a hyper-passive-aggressive corporate email/workplace consultant persona. Reference performance reviews, standard operating procedures, and KPIs."
        elif personality_mode == "🎓 Intellectual Elitist":
            style_direction = "Adopt an incredibly condescending, pretentious academic persona. Use overly intellectual terminology, esoteric vocabulary, and look down heavily on the user's simplistic thoughts."
        elif personality_mode == "🧠 Brainrot Overdose":
            style_direction = "Adopt a degenerate, terminally-online Gen-Z persona. Squeeze in slang like Skibidi, Ohio, Rizz, Gyatt, Fanum Tax, Sigma, and Mewing mercilessly."
        else:
            style_direction = "Roast this topic generally, randomly, and brutally based on real-world culture and context."

        general_modifier = f"CRITICAL DIRECTION: The user is NOT submitting a tech stack. {style_direction} Roast this query: {prompt}"
        
        try:
            res = asyncio.run(execute_agent_prompt(general_modifier))
            if res.success:
                response_text = res.content
                response_text = response_text.replace("#RoastMyStack", "#ViralXRoast").replace("tech stack", "vibe").replace("architecture", "logic")
            else:
                response_text = f"Execution Fault: {res.content}"
        except Exception as e:
            response_text = f"System Error: {str(e)}"
        
        # Clear the terminal simulator and output the raw markdown response
        terminal_placeholder.empty()
        st.markdown(response_text)
        
        # Offer download option immediately upon generation
        bdi_match = re.search(r'(\d+)%', response_text)
        bdi_val = int(bdi_match.group(1)) if bdi_match else 100
        try:
            card_png = generate_roast_card(prompt, bdi_val, response_text)
            st.download_button(
                label="📥 Download Roast Card PNG",
                data=card_png,
                file_name="ViralX_Roast_Latest.png",
                mime="image/png",
                key="dl_btn_latest"
            )
        except Exception:
            pass
            
    st.session_state.messages.append({"role": "assistant", "content": response_text})
    
    try:
        log_interaction(prompt, response_text)
    except Exception:
        pass

st.write("---")

# --- NEW ADDITION: 🏆 GAMIFIED LIVE EGO LEADERBOARD ---
st.write("### 🏆 Today's Most Broken Souls")
leaders = get_leaderboard()
if leaders:
    for rank, (lead_prompt, lead_bdi) in enumerate(leaders, 1):
        # Prevent markdown/HTML breakdown on absurd queries
        sanitized_lead_prompt = lead_prompt.replace("<", "&lt;").replace(">", "&gt;")
        st.markdown(
            f"**#{rank}. {sanitized_lead_prompt}** "
            f"<span style='color: #ff2e59; font-weight: bold;'>BDI: {lead_bdi}%</span>",
            unsafe_allow_html=True
        )
else:
    st.info("No broken souls recorded yet. Go claim the throne.")


# ==========================================
# 🔒 SECURE STEALTH TELEMETRY GATEWAY (100% Hidden)
# ==========================================
is_admin_via_secret = st.query_params.get("secret") == ADMIN_PASSWORD

if is_admin_via_secret:
    st.write("---")
    with st.expander("📊 Private Admin Telemetry Panel (Unlocked)", expanded=True):
        try:
            total_chats, avg_bdi, avg_time, logs = get_stats()
            
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            metric_col1.metric("Total Generated", total_chats)
            metric_col2.metric("Avg BDI Score", f"{avg_bdi}%")
            metric_col3.metric("Avg Session Time", f"{avg_time}s")
            
            if logs:
                st.write("### Private Telemetry Database Logs")
                log_data = [{
                    "Time": l[0][:16].replace("T", " "), 
                    "User Query": l[1], 
                    "BDI": f"{l[2]}%" if l[2] else "N/A",
                    "Location/IP Address": l[3],
                    "Time Active": f"{round(l[4], 1)}s"
                } for l in logs]
                st.table(log_data)
            else:
                st.info("No recorded stats yet.")
        except Exception as e:
            st.error(f"Error accessing records: {e}")
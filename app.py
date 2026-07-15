import streamlit as st
import asyncio
import sqlite3
import re
from datetime import datetime
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

def get_user_location():
    """Extracts IP address and Country from Streamlit deployment headers."""
    try:
        headers = st.context.headers
        ip = headers.get("X-Forwarded-For", "Unknown IP").split(",")[0].strip()
        country = headers.get("Cf-Ipcountry", "Unknown Country")
        return f"{ip} ({country})"
    except Exception:
        return "Localhost/Unknown"

def log_interaction(prompt: str, response: str):
    """Saves the user's prompt, response, location, and elapsed time."""
    # Try to capture the BDI percentage from the generated text
    bdi_match = re.search(r'(\d+)%', response)
    bdi_val = int(bdi_match.group(1)) if bdi_match else None
    
    # Measure the elapsed active time since the chat loaded or was reset
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

# Run database schema verification
init_db()


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
        # Reset the session clock for a fresh start
        st.session_state.session_start = datetime.utcnow()
        st.rerun()

st.divider()

# 3. Initialize Persistent Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. Render the Ongoing Thread Flow
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Bottom Space Chat Input Gateway (Open-ended & Random Input)
if prompt := st.chat_input("Drop anything here—a concept, a trend, a place, or a bad habit..."):
    
    # Render user query instantly in the thread flow
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Compute execution streaming placeholder
    with st.chat_message("assistant"):
        with st.spinner("THINKING..."):
            # Inject a clear framing instruction so the agent knows to treat this as a general topic, not tech
            general_modifier = f"CRITICAL DIRECTION: The user is NOT submitting a tech stack. Roast this topic generally, randomly, and brutally based on real-world culture and context: {prompt}"
            
            try:
                res = asyncio.run(execute_agent_prompt(general_modifier))
                if res.success:
                    response_text = res.content
                    
                    # Post-processing patch to clean out legacy technical hashtags if the engine leaks them
                    response_text = response_text.replace("#RoastMyStack", "#ViralXRoast").replace("tech stack", "vibe").replace("architecture", "logic")
                else:
                    response_text = f"Execution Fault: {res.content}"
            except Exception as e:
                response_text = f"System Error: {str(e)}"
            
            st.markdown(response_text)
            
    # Append assistant execution response directly to continue thread
    st.session_state.messages.append({"role": "assistant", "content": response_text})
    
    # Log the interaction variables silently to SQL database
    try:
        log_interaction(prompt, response_text)
    except Exception:
        pass


# ==========================================
# 🔒 HIDDEN PRIVATE ADMIN CONTROLS
# ==========================================
st.write("---")

# Verify if URL contains the administrative flag (e.g. ?admin=true)
is_admin_via_url = st.query_params.get("admin") == "true"

if is_admin_via_url:
    # Direct access to the admin metrics via custom secret link
    with st.expander("📊 Private Admin Telemetry Panel (Unlocked via URL)"):
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
else:
    # Discrete password option at the bottom of the page
    with st.expander("🔑 Access System Panel"):
        entered_pass = st.text_input("Enter Master Key", type="password")
        if entered_pass == ADMIN_PASSWORD:
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
        elif entered_pass:
            st.error("Invalid access key.")
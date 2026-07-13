import streamlit as st
import asyncio
from agent import execute_agent_prompt

# 1. Claude-inspired Page Setup (Minimal Stark/Dark aesthetic)
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
            font-size: 1.8rem !important; /* Scale down heading to prevent wrapping */
        }
        [data-testid="stChatMessage"] {
            padding: 0.6rem;
            font-size: 14px; /* Compact text size for mobile viewing */
            margin-bottom: 0.6rem;
        }
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 6rem !important; /* Safety padding so input box doesn't overlap text */
        }
    }
    </style>
""", unsafe_allow_html=True)

# 2. Top Navigation Bar (New Chat Control - adjusted ratio for mobile balance)
col1, col2 = st.columns([7, 3])
with col1:
    st.title("💀 ViralX Agent")
with col2:
    # Clicking this completely resets the persistent session history
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.divider()

# 3. Initialize Persistent Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. Render the Ongoing Thread Flow
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Bottom Space Chat Input Gateway
if prompt := st.chat_input("Ask ViralX to analyze your architecture, iterate, or proceed..."):
    
    # Render user query instantly in the thread flow
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Compute execution streaming placeholder
    with st.chat_message("assistant"):
        with st.spinner("THINKING..."):
            # Execute context prompt matching the engine architecture
            try:
                res = asyncio.run(execute_agent_prompt(prompt))
                if res.success:
                    response_text = res.content
                else:
                    response_text = f"Execution Fault: {res.content}"
            except Exception as e:
                response_text = f"System Error: {str(e)}"
            
            st.markdown(response_text)
            
    # Append assistant execution response directly to continue thread
    st.session_state.messages.append({"role": "assistant", "content": response_text})
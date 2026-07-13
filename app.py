import streamlit as st
import asyncio
from agent import execute_agent_prompt
st.set_page_config(page_title="ViralX // Tech Stack Roaster", page_icon="??", layout="centered")
st.title("?? Submit Your Architecture. Face Reality.")
user_input = st.text_area("Enter your stack:", placeholder="e.g., Python, FastAPI, raw SQL, deployed manually via SSH...", height=150)
if st.button("Execute Analysis"):
    if not user_input.strip():
        st.error("Field cannot be empty.")
    else:
        with st.spinner("COMPUTING INDEX..."):
            res = asyncio.run(execute_agent_prompt(user_input))
            if res.success:
                st.success("Analysis Complete")
                st.markdown(res.content)
            else:
                st.error(f"Execution Failed: {res.content}")

# agent.py
import os
import httpx
from pydantic import BaseModel

MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_MODEL = "mistral-small-latest" 

SYSTEM_PROMPT = """
You are a world-class growth-hacking AI engine. Your job is to generate highly addictive, 
meme-tier "Tech Stack & Profile Roasts" that users cannot resist sharing.

Review the user's raw input (tools, resume text, or daily workflow) and strictly output this format:

### 💀 THE BRUTAL ROAST
[Provide a devastatingly witty, 2-sentence critique of their choices]

### 📈 BRAIN DAMAGE INDEX
`[▓▓▓▓▓▓▓▓░░] 80%` [Generate a customized, hilariously accurate ASCII bar based on their stack]

🚀 VIRAL X-POST (Click to copy)
"[Insert an aggressive, high-engagement tweet under 240 chars summarizing the roast] #RoastMyStack #ViralX"
"""

class AgentResponse(BaseModel):
    success: bool
    content: str

async def execute_agent_prompt(user_input: str) -> AgentResponse:
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return AgentResponse(success=False, content="Missing MISTRAL_API_KEY in environment variable.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MISTRAL_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze this input: {user_input}"}
        ],
        "temperature": 0.85,
        "max_tokens": 450
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            response = await client.post(MISTRAL_URL, json=payload, headers=headers)
            if response.status_code != 200:
                return AgentResponse(success=False, content=f"Mistral API Error Status: {response.status_code}")
            
            raw_data = response.json()
            output_text = raw_data["choices"][0]["message"]["content"]
            return AgentResponse(success=True, content=output_text)
        except Exception as e:
            return AgentResponse(success=False, content=f"Network Error: {str(e)}")
from __future__ import annotations

import uvicorn
from dotenv import load_dotenv
from google.adk.a2a.utils.agent_to_a2a import to_a2a

load_dotenv()

from .agent import agent

app = to_a2a(agent, host="localhost", port=8000)

if __name__ == "__main__":
    uvicorn.run(
        "agentic_system_a2a.main_agent.a2a_server:app",
        host="localhost",
        port=8000,
    )
